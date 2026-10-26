"""Tạo hình KT2/KT3 từ kết quả đã lưu, không huấn luyện/chọn lại theo test."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'reports/experiments'; FIG=ROOT/'reports/figures'

def save(name):
    plt.tight_layout(); plt.savefig(FIG/name,dpi=180,bbox_inches='tight'); plt.close()

def run():
    sns.set_theme(style='whitegrid',font='DejaVu Sans',font_scale=.85)
    kt2=pd.read_csv(DATA/'kt2_cv_summary.csv'); kt3=pd.read_csv(DATA/'kt3_cv_summary.csv')
    test=pd.read_csv(DATA/'final_test_comparison.csv')
    for df,name,title in [(kt2,'09_kt2_cv.png','KT2: kiểm định theo năm'),(kt3,'10_kt3_cv.png','KT3: cấu hình đã tối ưu')]:
        df=df.sort_values('cv_rmse_log_mean',ascending=False)
        plt.figure(figsize=(9,3.6))
        plt.barh(df.model,df.cv_rmse_log_mean,xerr=df.cv_rmse_log_std,color='#28677b',capsize=4)
        plt.xlabel('RMSE log trung bình ± độ lệch chuẩn mẫu qua 3 fold'); plt.title(title)
        save(name)
    errors=pd.read_csv(DATA/'final_test_predictions.csv')
    fig,ax=plt.subplots(1,2,figsize=(10,4))
    ax[0].scatter(errors.SalePrice/1000,errors.prediction_usd/1000,alpha=.5,s=17)
    bounds=[0,max(errors.SalePrice.max(),errors.prediction_usd.max())/1000]
    ax[0].plot(bounds,bounds,'--',color='#aa653e')
    ax[0].set(xlabel='Giá thực (nghìn USD)',ylabel='Giá dự đoán (nghìn USD)')
    ax[1].scatter(errors.prediction_usd/1000,errors.residual_usd/1000,alpha=.5,s=17)
    ax[1].axhline(0,color='#aa653e',linestyle='--')
    ax[1].set(xlabel='Giá dự đoán (nghìn USD)',ylabel='Thực − dự đoán (nghìn USD)')
    save('11_predictions_residuals.png')
    ab=pd.read_csv(DATA/'ablation.csv')
    plt.figure(figsize=(9,3.6)); plt.barh(ab.model.str.replace('Ablation_',''),ab.cv_rmse_log_mean,color='#28677b')
    plt.xlabel('RMSE log CV · cùng alpha Ridge'); save('12_ablation.png')
    grid=pd.read_csv(DATA/'grid_Ridge_tuned.csv')
    grid['alpha']=grid.params.map(lambda p:json.loads(p)['regressor__model__alpha'])
    grid=grid.sort_values('alpha')
    plt.figure(figsize=(8,3.6)); plt.errorbar(grid.alpha,grid.rmse_log_mean,yerr=grid.std_test_score,marker='o',capsize=3)
    plt.xscale('log'); plt.xlabel('Alpha của Ridge (thang log)'); plt.ylabel('RMSE log CV ± std quần thể của sklearn')
    save('13_alpha_validation.png')
    learn=pd.read_csv(DATA/'learning_curve.csv')
    plt.figure(figsize=(8,3.6))
    plt.plot(learn.n_train,learn.train_rmse_log,'o-',label='Train')
    plt.plot(learn.n_train,learn.validation_2009_rmse_log,'o-',label='Validation năm 2009')
    plt.xlabel('Số mẫu huấn luyện từ các năm gần 2009'); plt.ylabel('RMSE log'); plt.legend()
    save('14_learning_curve.png')
    perm=pd.read_csv(DATA/'permutation_importance_validation2009.csv').head(12).iloc[::-1]
    plt.figure(figsize=(8,4.3)); plt.barh(perm.feature,perm.importance_mean,xerr=perm.importance_std,color='#28677b')
    plt.xlabel('Tăng RMSE log khi hoán vị · validation 2009'); save('15_permutation_importance.png')
    sparse=[]
    for n in ['Ridge_tuned','Lasso_tuned','ElasticNet_tuned']:
        c=pd.read_csv(DATA/f'coefficients_{n}.csv')
        sparse.append({'model':n,'coefficients':len(c),'nonzero':int((c.abs_coefficient>1e-8).sum())})
    pd.DataFrame(sparse).to_csv(DATA/'sparsity.csv',index=False)
    combined=pd.concat([kt2,kt3]).merge(test[['model','rmse_log']],on='model')
    combined.to_csv(DATA/'cv_vs_test.csv',index=False)
    df=combined[~combined.model.eq('DummyMeanLog')].set_index('model')
    ax=df[['cv_rmse_log_mean','rmse_log']].plot.barh(figsize=(9,5),color=['#28677b','#aa653e'])
    ax.set_xlabel('RMSE log'); ax.legend(['CV trung bình','Test 2010 · sau khi khóa lựa chọn'])
    save('16_cv_vs_test.png')
    print('Created 8 KT2/KT3 figures')

if __name__=='__main__':run()
