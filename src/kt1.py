"""Chạy python -m src.kt1 từ gốc dự án để tái tạo toàn bộ số liệu KT1."""
from pathlib import Path
import hashlib
import json
import re
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter, MaxNLocator
import seaborn as sns
from .preprocessing import load_raw, clean_features, make_preprocessor

ROOT = Path(__file__).resolve().parents[1]
FIG = ROOT / 'reports/figures'
TABLE = ROOT / 'reports/tables'

def savefig(name):
    plt.tight_layout()
    plt.savefig(FIG / name, dpi=170, bbox_inches='tight')
    plt.close()

def run():
    FIG.mkdir(parents=True, exist_ok=True)
    TABLE.mkdir(parents=True, exist_ok=True)
    raw = load_raw(ROOT / 'data/raw/AmesHousing.tsv')
    assert raw.shape == (2930, 82)
    assert raw['PID'].is_unique, 'Có lặp bất động sản: cần chia theo nhóm PID.'
    assert (raw.SalePrice > 0).all()
    train = raw.loc[raw['Yr Sold'] < 2010].copy()
    test = raw.loc[raw['Yr Sold'] == 2010].copy()
    xtr, xte = clean_features(train), clean_features(test)
    prep = make_preprocessor(xtr)
    a = prep.fit_transform(xtr)
    b = prep.transform(xte)
    assert np.isfinite(a).all() and np.isfinite(b).all()
    names = prep.named_steps['encode'].get_feature_names_out()
    np.savez_compressed(ROOT / 'data/processed/ames_ready.npz',
                        X_train=a, X_test=b, y_train_log=np.log1p(train.SalePrice),
                        y_test_log=np.log1p(test.SalePrice),
                        train_order=train.Order.to_numpy(), test_order=test.Order.to_numpy(),
                        feature_names=names.astype(str))
    pd.DataFrame({'Order': raw.Order, 'PID': raw.PID,
                  'split': np.where(raw['Yr Sold'] < 2010, 'train', 'test')}).to_csv(
                      ROOT / 'data/processed/split_manifest.csv', index=False)
    # Bảng chất lượng raw đầy đủ, EDA và ngưỡng chỉ lấy train.
    na = raw.eq('NA').sum()
    quality = pd.DataFrame({'column': raw.columns, 'dtype_raw': raw.dtypes.astype(str).values,
                            'NA_literal': na.values, 'empty': raw.eq('').sum().values,
                            'unique': raw.nunique().values})
    quality['NA_pct'] = quality.NA_literal / len(raw) * 100
    quality.to_csv(TABLE / 'quality_all_columns.csv', index=False)
    xtr.describe().T.to_csv(TABLE / 'numeric_summary_train.csv')
    xtr.describe(include=['object', 'str']).T.to_csv(TABLE / 'categorical_summary_train.csv')
    before = pd.DataFrame({'stage': ['Train sau quy tắc ngữ nghĩa', 'Test sau quy tắc ngữ nghĩa',
                                    'Train sau pipeline', 'Test sau pipeline'],
                           'rows': [len(xtr), len(xte), len(a), len(b)],
                           'columns': [xtr.shape[1], xte.shape[1], a.shape[1], b.shape[1]],
                           'missing_cells': [int(xtr.isna().sum().sum()), int(xte.isna().sum().sum()), 0, 0]})
    before.to_csv(TABLE / 'before_after.csv', index=False)
    numeric = xtr.select_dtypes(include='number')
    iqr_rows = []
    for c in numeric:
        q1, q3 = numeric[c].quantile([.25, .75]); iqr = q3-q1
        n = int(((numeric[c] < q1-1.5*iqr) | (numeric[c] > q3+1.5*iqr)).sum())
        iqr_rows.append({'feature': c, 'q1': q1, 'q3': q3, 'iqr_flag_count': n})
    pd.DataFrame(iqr_rows).to_csv(TABLE / 'outliers_iqr_train.csv', index=False)
    clipped = prep.named_steps['clip'].transform(xtr)
    clip_rows = [{'feature': c, 'upper_train_p99': float(prep.named_steps['clip'].upper_[c]),
                  'changed_train': int((xtr[c].notna() & xtr[c].ne(clipped[c])).sum()),
                  'changed_test': int((xte[c].notna() & xte[c].ne(prep.named_steps['clip'].transform(xte)[c])).sum())}
                 for c in prep.named_steps['clip'].columns_]
    pd.DataFrame(clip_rows).to_csv(TABLE / 'clipping_audit.csv', index=False)
    corr = numeric.assign(SalePrice=train.SalePrice).corr()['SalePrice'].drop('SalePrice').sort_values(ascending=False)
    corr.to_csv(TABLE / 'target_correlations_train.csv')
    sns.set_theme(style='whitegrid', font='DejaVu Sans', font_scale=.9)
    fig, ax = plt.subplots(1, 2, figsize=(10, 3.5))
    sns.histplot(train.SalePrice, bins=40, ax=ax[0], color='#28677b')
    ax[0].set(xlabel='Giá bán (USD)', ylabel='Số nhà', title='Giá gốc trên tập huấn luyện')
    ax[0].xaxis.set_major_locator(MaxNLocator(5))
    ax[0].xaxis.set_major_formatter(FuncFormatter(lambda v, pos: f'{v/1000:g}k' if v else '0'))
    sns.histplot(np.log1p(train.SalePrice), bins=40, ax=ax[1], color='#aa653e')
    ax[1].set(xlabel='ln(1 + giá bán)', ylabel='Số nhà', title='Giá sau biến đổi log1p')
    savefig('01_target.png')
    fig, ax = plt.subplots(1, 3, figsize=(11, 3.4))
    for axis, c, lab in zip(ax, ['Gr Liv Area', 'Lot Area', 'Year Built'], ['Diện tích ở (ft²)', 'Diện tích đất (ft²)', 'Năm xây dựng']):
        sns.histplot(xtr[c], bins=35, ax=axis, color='#28677b'); axis.set(xlabel=lab, ylabel='Số nhà')
        axis.xaxis.set_major_locator(MaxNLocator(4))
        if c == 'Lot Area':
            axis.xaxis.set_major_formatter(FuncFormatter(lambda v, pos: f'{v/1000:g}k' if v else '0'))
    savefig('02_features.png')
    fig, ax = plt.subplots(1, 2, figsize=(10, 3.5))
    sns.scatterplot(data=train, x='Gr Liv Area', y='SalePrice', alpha=.35, s=12, ax=ax[0])
    ax[0].set(xlabel='Diện tích ở (ft²)', ylabel='Giá bán (USD)')
    sns.boxplot(data=train, x='Overall Qual', y='SalePrice', ax=ax[1], color='#b8d4dc', showfliers=False)
    ax[1].set(xlabel='Chất lượng tổng thể (1–10)', ylabel='Giá bán (USD)')
    savefig('03_relationships.png')
    cols = ['SalePrice', 'Overall Qual', 'Gr Liv Area', 'Garage Cars', 'Garage Area', 'Total Bsmt SF', '1st Flr SF', 'Year Built']
    plt.figure(figsize=(8, 5.5))
    sns.heatmap(train[cols].apply(pd.to_numeric, errors='coerce').corr(), annot=True, fmt='.2f', cmap='vlag', vmin=-1, vmax=1)
    savefig('04_correlations.png')
    plt.figure(figsize=(9, 3.8))
    missing = quality.loc[quality.NA_literal > 0].set_index('column').NA_pct.sort_values(ascending=False)
    missing.plot.bar(color='#28677b'); plt.ylabel('Literal NA (% toàn bộ dữ liệu)'); plt.xlabel('Đặc trưng')
    savefig('05_na_tokens.png')
    fig, ax = plt.subplots(1, 2, figsize=(10, 3.3))
    for axis, data, title in [(ax[0], xtr, 'Trước clipping'), (ax[1], clipped, 'Sau clipping bằng ngưỡng train')]:
        sns.histplot(data['Lot Area'], bins=40, ax=axis, color='#28677b')
        axis.set(xlabel='Diện tích đất (ft²)', ylabel='Số nhà', title=title)
    savefig('06_before_after.png')
    plt.figure(figsize=(9, 3.7))
    top = train.groupby('Neighborhood').SalePrice.median().sort_values().tail(12)
    top.plot.barh(color='#28677b'); plt.xlabel('Trung vị giá bán (USD)'); plt.ylabel('Khu vực')
    savefig('07_neighborhood.png')
    fig = plt.figure(figsize=(11, 1.8))
    fig.text(.02, .65, r'$J(w,b)=\frac{1}{2n}\|z-b-Xw\|_2^2+\alpha[\rho\|w\|_1+\frac{1-\rho}{2}\|w\|_2^2]$', fontsize=19)
    fig.text(.02, .13, r'$\hat{w}_{L2}=(X^TX/n+\alpha I)^{-1}X^Tz/n$', fontsize=19)
    plt.axis('off')
    plt.savefig(FIG / '08_equations.png', dpi=200, bbox_inches='tight')
    plt.close()
    # Từ điển đầy đủ: nối tên thực tế với định nghĩa nguồn, không tự sinh từ tên.
    documentation = (ROOT / 'data/raw/DataDocumentation.txt').read_text(encoding='cp1252')
    defs = {}
    for line in documentation.splitlines():
        m = re.match(r'^(.+?)\s*\((Nominal|Ordinal|Discrete|Continuous)\):?\s*(.*)', line)
        if m:
            defs[m.group(1).strip()] = (m.group(2), m.group(3).strip())
    dictionary = []
    for c in raw:
        lookup = {'Bedroom AbvGr': 'Bedroom', 'Kitchen AbvGr': 'Kitchen',
                  'Exterior 1st': 'Exterior 1', 'Exterior 2nd': 'Exterior 2',
                  'BsmtFin Type 2': 'BsmtFinType 2', 'Heating QC': 'HeatingQC',
                  'Kitchen Qual': 'KitchenQual', 'TotRms AbvGrd': 'TotRmsAbvGrd',
                  'Fireplace Qu': 'FireplaceQu', '3Ssn Porch': '3-Ssn Porch'}.get(c, c)
        typ, meaning = defs.get(lookup, ('', ''))
        dictionary.append({'column': c, 'raw_dtype': str(raw[c].dtype), 'measurement': typ,
                           'meaning_original': meaning, 'NA_count': int(na[c]),
                           'role': 'target' if c=='SalePrice' else 'excluded' if c in ['Order','PID','Sale Type','Sale Condition'] else 'predictor',
                           'treatment': 'NA = absence, one-hot' if c in __import__('src.preprocessing', fromlist=['STRUCTURAL']).STRUCTURAL else
                           'log1p target' if c=='SalePrice' else 'excluded' if c in ['Order','PID','Sale Type','Sale Condition'] else
                           'median + missing indicator + scale; area p99 clip' if c in numeric else 'one-hot; unknown NA imputed separately'})
    pd.DataFrame(dictionary).to_csv(ROOT / 'docs/data_dictionary.csv', index=False, encoding='utf-8-sig')
    missing_defs = [d['column'] for d in dictionary if not d['meaning_original']]
    # Audit lỗi năm, mã có khoảng trắng, bản ghi trùng, nhãn ngoại lai.
    year_errors = {c: int(((pd.to_numeric(raw[c], errors='coerce') > raw['Yr Sold']) |
                           (pd.to_numeric(raw[c], errors='coerce') < 1800)).sum())
                   for c in ['Year Built', 'Year Remod/Add', 'Garage Yr Blt']}
    whitespace = sum(int(raw[c].map(lambda v: isinstance(v,str) and v != v.strip()).sum()) for c in raw)
    payload = raw.drop(columns=['Order', 'PID'])
    report = dict(rows=len(raw), columns=raw.shape[1], predictors=xtr.shape[1],
                  train_rows=len(train), test_rows=len(test), encoded_features=a.shape[1],
                  numeric_features=len(numeric.columns), categorical_features=xtr.shape[1]-len(numeric.columns),
                  duplicate_rows=int(raw.duplicated().sum()), duplicate_payload=int(payload.duplicated().sum()),
                  duplicate_pid=int(raw.PID.duplicated().sum()), raw_NA_tokens=int(na.sum()),
                  raw_NA_columns=int((na>0).sum()), raw_empty_cells=int(raw.eq('').sum().sum()),
                  whitespace_cells=whitespace, invalid_years=year_errors,
                  train_missing=int(xtr.isna().sum().sum()), test_missing=int(xte.isna().sum().sum()),
                  target_min=int(train.SalePrice.min()), target_max=int(train.SalePrice.max()),
                  target_mean=float(train.SalePrice.mean()), target_median=float(train.SalePrice.median()),
                  skew_raw=float(train.SalePrice.skew()), skew_log=float(np.log1p(train.SalePrice).skew()),
                  large_houses_train=int((train['Gr Liv Area'] > 4000).sum()),
                  correlations={c: float(corr[c]) for c in ['Overall Qual','Gr Liv Area','Garage Cars','Year Built']},
                  garage_correlation=float(numeric['Garage Area'].corr(numeric['Garage Cars'])),
                  yearly_counts={str(k): int(v) for k,v in raw['Yr Sold'].value_counts().sort_index().items()},
                  missing_dictionary_definitions=missing_defs,
                  sha256=hashlib.sha256((ROOT/'data/raw/AmesHousing.tsv').read_bytes()).hexdigest())
    (ROOT / 'reports/summary.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return report

if __name__ == '__main__':
    run()
