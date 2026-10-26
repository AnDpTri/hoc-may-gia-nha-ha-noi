"""Thực nghiệm KT2/KT3, toàn pipeline được fit lại trong mỗi fold thời gian.

Chạy: python -m src.experiments. Test chỉ được mở để chấm sau khi khóa lựa chọn.
"""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import time
import sys
import warnings
import joblib
import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.dummy import DummyRegressor
from sklearn.linear_model import LinearRegression, Ridge, Lasso, ElasticNet, RidgeCV, LassoCV
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, root_mean_squared_error, r2_score, make_scorer
from sklearn.model_selection import GridSearchCV
from sklearn.inspection import permutation_importance
from sklearn.exceptions import ConvergenceWarning
from threadpoolctl import threadpool_limits
from .preprocessing import load_raw, clean_features, make_preprocessor, SEED
from .modeling import make_model, predict_nonnegative, FeatureBuilder

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'reports/experiments'
RIDGE_ALPHAS = [.1, 1., 3., 10., 30., 100., 300., 1000.]
LASSO_ALPHAS = [.0001, .0003, .001, .003, .01, .03]

def rmse_log(y, pred):
    return float(root_mean_squared_error(np.log1p(y), np.log1p(np.maximum(0,pred))))

SCORER = make_scorer(rmse_log, greater_is_better=False)

def metrics(y, pred):
    p=np.maximum(0,pred)
    return {'rmse_log':rmse_log(y,p), 'mae_usd':float(mean_absolute_error(y,p)),
            'rmse_usd':float(root_mean_squared_error(y,p)), 'r2_usd':float(r2_score(y,p))}

def temporal_folds(raw):
    years=raw['Yr Sold'].to_numpy()
    return [(np.flatnonzero(years < y), np.flatnonzero(years == y)) for y in [2007,2008,2009]]

def evaluate_cv(name, model, train, folds):
    y=train.SalePrice.to_numpy(); rows=[]; predictions=[]
    for k,(a,b) in enumerate(folds,1):
        m=clone(model); t=time.perf_counter(); m.fit(train.iloc[a],y[a])
        pa=predict_nonnegative(m,train.iloc[a]); pb=predict_nonnegative(m,train.iloc[b])
        row={'model':name,'fold':k,'validation_year':int(train.iloc[b]['Yr Sold'].min()),
             'n_train':len(a),'n_validation':len(b),'fit_seconds':time.perf_counter()-t}
        row.update({'train_'+s:v for s,v in metrics(y[a],pa).items()})
        row.update(metrics(y[b],pb)); rows.append(row)
        predictions.append(pd.DataFrame({'Order':train.iloc[b].Order.to_numpy(),
                                         'fold':k,'actual':y[b],'predicted':pb}))
    frame=pd.DataFrame(rows)
    summary={'model':name,'cv_rmse_log_mean':float(frame.rmse_log.mean()),
             'cv_rmse_log_std':float(frame.rmse_log.std(ddof=1)),
             'cv_train_rmse_log_mean':float(frame.train_rmse_log.mean()),
             'cv_mae_usd_mean':float(frame.mae_usd.mean()),
             'cv_rmse_usd_mean':float(frame.rmse_usd.mean()),
             'cv_r2_usd_mean':float(frame.r2_usd.mean()),
             'fit_seconds_mean':float(frame.fit_seconds.mean())}
    return summary,frame,pd.concat(predictions,ignore_index=True)

def tune(name, model, grid, train, folds):
    print('Tuning',name,flush=True)
    # n_jobs=1 + giới hạn BLAS tránh nhân số luồng trên máy cá nhân.
    search=GridSearchCV(model,grid,cv=folds,scoring=SCORER,n_jobs=1,
                        error_score='raise',return_train_score=True,refit=True)
    search.fit(train,train.SalePrice)
    results=pd.DataFrame(search.cv_results_)
    results['rmse_log_mean']=-results['mean_test_score']
    results['params']=results.params.map(lambda p:json.dumps(p,ensure_ascii=False))
    results.to_csv(OUT/f'grid_{name}.csv',index=False)
    params={k.replace('regressor__model__',''):v for k,v in search.best_params_.items()}
    return search.best_estimator_,params

def supplementary_cv(train, folds):
    # Cố định preprocessing bằng năm 2006: không fit trên năm validation nào.
    x=clean_features(train); calibration=train['Yr Sold'].eq(2006)
    p=make_preprocessor(x); p.fit(x.loc[calibration]); matrix=p.transform(x)
    y=np.log1p(train.SalePrice)
    r=RidgeCV(alphas=RIDGE_ALPHAS,cv=folds,scoring='neg_mean_squared_error').fit(matrix,y)
    l=LassoCV(alphas=LASSO_ALPHAS,cv=folds,max_iter=50000,tol=1e-5,n_jobs=1,random_state=SEED).fit(matrix,y)
    result={'preprocessing_fit_year':2006,'calibration_rows':int(calibration.sum()),
            'ridgecv_alpha':float(r.alpha_),'lassocv_alpha':float(l.alpha_),
            'note':'Minh họa đúng lớp RidgeCV/LassoCV với preprocessing đóng băng năm 2006; không thay thế CV refit pipeline chính.'}
    (OUT/'ridgecv_lassocv.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    return result

def run():
    OUT.mkdir(parents=True,exist_ok=True); (ROOT/'models').mkdir(exist_ok=True)
    raw=load_raw(ROOT/'data/raw/AmesHousing.tsv')
    train=raw.loc[raw['Yr Sold']<2010].reset_index(drop=True)
    test=raw.loc[raw['Yr Sold']==2010].reset_index(drop=True)
    assert set(train.PID).isdisjoint(set(test.PID))
    folds=temporal_folds(train)
    # KT2: cấu hình xác định trước, chưa tối ưu bằng test.
    base_estimators={'DummyMeanLog':DummyRegressor(strategy='mean'),
                     'LinearRegression':LinearRegression(),
                     'Ridge_default':Ridge(alpha=10.),
                     'Lasso_default':Lasso(alpha=.001,max_iter=50000,tol=1e-5),
                     'ElasticNet_default':ElasticNet(alpha=.001,l1_ratio=.5,max_iter=50000,tol=1e-5)}
    baseline_models={k:make_model(train,v) for k,v in base_estimators.items()}
    summaries=[]; fold_tables=[]; oof={}
    for name,model in baseline_models.items():
        print('KT2',name,flush=True)
        s,f,p=evaluate_cv(name,model,train,folds); summaries.append(s); fold_tables.append(f); oof[name]=p
    kt2=pd.DataFrame(summaries); kt2.to_csv(OUT/'kt2_cv_summary.csv',index=False)
    # KT3: chọn alpha Ridge, sau đó ablation với cùng alpha để tách tác động dữ liệu.
    ridge, rparams=tune('ridge_original',make_model(train,Ridge()),
                       {'regressor__model__alpha':RIDGE_ALPHAS},train,folds)
    alpha=rparams['alpha']; ablations=[]; policy_models={}
    policies=[('Original_clip',False,True,False),('Features_clip',True,True,False),
              ('Features_no_clip',True,False,False),('Features_log_no_clip',True,False,True)]
    for name,eng,clip,log in policies:
        model=make_model(train,Ridge(alpha=alpha),engineered=eng,clipping=clip,log_areas=log)
        s,f,p=evaluate_cv('Ablation_'+name,model,train,folds)
        s.update(engineered=eng,clipping=clip,log_areas=log,alpha=alpha)
        ablations.append(s); policy_models[name]=model; fold_tables.append(f)
    ablation=pd.DataFrame(ablations); ablation.to_csv(OUT/'ablation.csv',index=False)
    selected_policy=ablation.sort_values('cv_rmse_log_mean').iloc[0]
    flags={k:bool(selected_policy[k]) for k in ['engineered','clipping','log_areas']}
    print('Selected preprocessing:',flags,flush=True)
    searches={
        'Ridge_tuned':(Ridge(),{'regressor__model__alpha':RIDGE_ALPHAS}),
        'Lasso_tuned':(Lasso(max_iter=50000,tol=1e-5),{'regressor__model__alpha':LASSO_ALPHAS}),
        'ElasticNet_tuned':(ElasticNet(max_iter=50000,tol=1e-5),
                            {'regressor__model__alpha':[.0003,.001,.003,.01],
                             'regressor__model__l1_ratio':[.1,.5,.9]}),
        'HistGradientBoosting':(HistGradientBoostingRegressor(max_iter=250,learning_rate=.05,
                                 early_stopping=False,random_state=SEED),
                                {'regressor__model__max_leaf_nodes':[15,31],
                                 'regressor__model__l2_regularization':[1.,10.]})}
    models=dict(baseline_models); params={}; tuned_summaries=[]
    for name,(estimator,grid) in searches.items():
        best,bp=tune(name,make_model(train,estimator,**flags),grid,train,folds)
        models[name]=best; params[name]=bp
        s,f,p=evaluate_cv(name,best,train,folds)
        tuned_summaries.append(s); fold_tables.append(f); oof[name]=p
    kt3=pd.DataFrame(tuned_summaries); kt3.to_csv(OUT/'kt3_cv_summary.csv',index=False)
    final_name=kt3.sort_values('cv_rmse_log_mean').iloc[0]['model']
    # Mô hình KT2 tốt nhất cũng đủ điều kiện; không ép cải tiến phải thắng.
    candidates=pd.concat([kt2,kt3],ignore_index=True).sort_values('cv_rmse_log_mean')
    final_name=str(candidates.iloc[0]['model'])
    supplement=supplementary_cv(train,folds)
    frozen={'selected_model':final_name,'selected_preprocessing':flags,'best_params':params,
            'ridge_ablation_alpha':alpha,'selection_metric':'mean 3 yearly-fold RMSE log, equal fold weights',
            'selected_at_utc':datetime.now(timezone.utc).isoformat(),
            'test_used_for_selection':False,'test_year':2010,
            'grids':{name:grid for name,(_,grid) in searches.items()}}
    # Lưu lựa chọn TRƯỚC khi tính bất kỳ chỉ số test.
    frozen_text=json.dumps(frozen,ensure_ascii=False,indent=2)
    (OUT/'selection_frozen_before_test.json').write_bytes(frozen_text.encode('utf-8'))
    frozen_hash=hashlib.sha256(frozen_text.encode()).hexdigest()
    print('Frozen choice before test:',final_name,flush=True)
    pd.concat(fold_tables).to_csv(OUT/'all_cv_folds.csv',index=False)
    oof[final_name].to_csv(OUT/'final_oof_predictions.csv',index=False)
    # Đường cong học theo năm; học/validation không trộn tương lai.
    learning=[]
    for n_years in [1,2,3]:
        fit=train[train['Yr Sold'] < 2009].copy()
        available=sorted(fit['Yr Sold'].unique())[-n_years:]
        fit=fit[fit['Yr Sold'].isin(available)]
        val=train[train['Yr Sold']==2009]
        m=clone(models[final_name]).fit(fit,fit.SalePrice)
        learning.append({'n_train':len(fit),'train_years':','.join(map(str,available)),
                         'train_rmse_log':rmse_log(fit.SalePrice,predict_nonnegative(m,fit)),
                         'validation_2009_rmse_log':rmse_log(val.SalePrice,predict_nonnegative(m,val))})
    pd.DataFrame(learning).to_csv(OUT/'learning_curve.csv',index=False)
    # Tầm quan trọng hoán vị chỉ dùng fold validation 2009, không nhìn test.
    devfit=train[train['Yr Sold']<2009]; devval=train[train['Yr Sold']==2009]
    devmodel=clone(models[final_name]).fit(devfit,devfit.SalePrice)
    perm=permutation_importance(devmodel,devval,devval.SalePrice,scoring=SCORER,
                                n_repeats=3,random_state=SEED,n_jobs=1)
    pd.DataFrame({'feature':train.columns,'importance_mean':perm.importances_mean,
                  'importance_std':perm.importances_std}).sort_values('importance_mean',ascending=False).to_csv(
                      OUT/'permutation_importance_validation2009.csv',index=False)
    # Chấm tất cả cấu hình đã khóa cùng một lần; không chọn lại theo test.
    test_rows=[]; fitted={}
    for name,model in models.items():
        m=clone(model); t=time.perf_counter(); m.fit(train,train.SalePrice)
        elapsed=time.perf_counter()-t; fitted[name]=m
        row={'model':name,'fit_full_seconds':elapsed}
        row.update({'train_'+k:v for k,v in metrics(train.SalePrice,predict_nonnegative(m,train)).items()})
        row.update(metrics(test.SalePrice,predict_nonnegative(m,test)))
        test_rows.append(row)
    test_table=pd.DataFrame(test_rows); test_table.to_csv(OUT/'final_test_comparison.csv',index=False)
    final=fitted[final_name]; pred=predict_nonnegative(final,test)
    errors=test[['Order','PID','Gr Liv Area','Overall Qual','Neighborhood','SalePrice']].copy()
    errors['prediction_usd']=pred; errors['residual_usd']=test.SalePrice-pred
    errors['absolute_error_usd']=np.abs(errors.residual_usd)
    errors['absolute_log_error']=np.abs(np.log1p(test.SalePrice)-np.log1p(pred))
    errors['price_band']=pd.cut(test.SalePrice,[0,150000,250000,np.inf],labels=['<150k','150k-250k','>250k'])
    errors.to_csv(OUT/'final_test_predictions.csv',index=False)
    errors.sort_values('absolute_error_usd',ascending=False).head(15).to_csv(OUT/'largest_errors.csv',index=False)
    errors.groupby('price_band',observed=True).agg(n=('SalePrice','size'),
                         mae_usd=('absolute_error_usd','mean'),mean_abs_log_error=('absolute_log_error','mean')).to_csv(OUT/'errors_by_price_band.csv')
    joblib.dump(final,ROOT/'models/final_model.joblib',compress=3)
    # Hệ số tuyến tính mang ý nghĩa theo không gian đã scale, không phải nhân quả.
    for name in ['Ridge_tuned','Lasso_tuned','ElasticNet_tuned']:
        pipe=fitted[name].regressor_; coef=pipe.named_steps['model'].coef_
        feature_names=pipe.named_steps['preprocess'].named_steps['encode'].get_feature_names_out()
        pd.DataFrame({'feature':feature_names,'coefficient_log_price':coef,
                       'abs_coefficient':np.abs(coef)}).sort_values('abs_coefficient',ascending=False).to_csv(OUT/f'coefficients_{name}.csv',index=False)
    chosen=test_table.set_index('model').loc[final_name].to_dict()
    dummy=float(test_table.set_index('model').loc['DummyMeanLog','rmse_log'])
    result={'selected_model':final_name,'selected_flags':flags,'best_params':params,
            'selected_cv':candidates.iloc[0].to_dict(),'test_metrics':chosen,
            'test_rmse_log_improvement_vs_dummy_pct':100*(1-chosen['rmse_log']/dummy),
            'selection_sha256':frozen_hash,'n_train':len(train),'n_test':len(test),
            'seed':SEED,'supplementary_cv':supplement,
            'warning':'CV dùng chọn cấu hình nên hơi lạc quan; test giữ lại là đánh giá cuối. Không chọn lại theo test.'}
    (OUT/'results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False,indent=2),flush=True)
    return result

if __name__=='__main__':
    if hasattr(sys.stdout,'reconfigure'):sys.stdout.reconfigure(encoding='utf-8')
    with threadpool_limits(limits=1), warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter('always',ConvergenceWarning)
        result=run()
    convergence=[str(w.message) for w in caught if issubclass(w.category,ConvergenceWarning)]
    (OUT/'convergence_warnings.json').write_text(json.dumps(convergence,ensure_ascii=False,indent=2),encoding='utf-8')
    print('Convergence warnings:',len(convergence),flush=True)
