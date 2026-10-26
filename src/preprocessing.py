"""Tiền xử lý Ames: quy tắc cố định + thống kê chỉ học trên train."""
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

SEED = 42
DROP_COLUMNS = ['Order', 'PID', 'SalePrice', 'Sale Type', 'Sale Condition']
STRUCTURAL = ['Alley', 'Bsmt Qual', 'Bsmt Cond', 'Bsmt Exposure',
              'BsmtFin Type 1', 'BsmtFin Type 2', 'Fireplace Qu', 'Garage Type',
              'Garage Finish', 'Garage Qual', 'Garage Cond', 'Pool QC', 'Fence', 'Misc Feature']
AREA_COLUMNS = ['Lot Frontage', 'Lot Area', 'Mas Vnr Area', 'BsmtFin SF 1',
                'BsmtFin SF 2', 'Bsmt Unf SF', 'Total Bsmt SF', '1st Flr SF',
                '2nd Flr SF', 'Low Qual Fin SF', 'Gr Liv Area', 'Garage Area',
                'Wood Deck SF', 'Open Porch SF', 'Enclosed Porch', '3Ssn Porch',
                'Screen Porch', 'Pool Area', 'Misc Val']

def load_raw(path):
    # Giữ literal NA và None: NA có thể nghĩa là không có tiện ích.
    return pd.read_csv(path, sep='\t', keep_default_na=False,
                       dtype={'PID': str, 'MS SubClass': str})

def clean_features(raw):
    """Không học thống kê; có thể dùng độc lập cho từng fold và test."""
    x = raw.drop(columns=DROP_COLUMNS, errors='ignore').copy()
    for c in x.columns:
        if pd.api.types.is_string_dtype(x[c]) or x[c].dtype == object:
            x[c] = x[c].astype(object).map(lambda v: v.strip() if isinstance(v, str) else v)
            x[c] = x[c].replace('', np.nan)
            if c in STRUCTURAL:
                x[c] = x[c].replace('NA', '__ABSENT__')
            else:
                x[c] = x[c].replace('NA', np.nan)
    # Khôi phục cột số có literal NA, không ép mã loại nhà thành số.
    categorical = set(STRUCTURAL + ['MS SubClass', 'Mo Sold'])
    numeric_candidates = ['Lot Frontage', 'Mas Vnr Area', 'BsmtFin SF 1',
                          'BsmtFin SF 2', 'Bsmt Unf SF', 'Total Bsmt SF',
                          'Bsmt Full Bath', 'Bsmt Half Bath', 'Garage Yr Blt',
                          'Garage Cars', 'Garage Area']
    for c in numeric_candidates:
        x[c] = pd.to_numeric(x[c], errors='coerce')
    for c in ['Year Built', 'Year Remod/Add', 'Garage Yr Blt']:
        # Năm sau năm bán hoặc trước 1800 là bất hợp lệ theo ngữ nghĩa dự án.
        x.loc[(x[c] > x['Yr Sold']) | (x[c] < 1800), c] = np.nan
    for c in categorical:
        x[c] = x[c].map(lambda v: str(v) if pd.notna(v) else np.nan).astype(object)
    return x

class QuantileClipper(BaseEstimator, TransformerMixin):
    """Winsorize các cột diện tích/giá trị về [0, phân vị 99% của train]."""
    def __init__(self, quantile=0.99, enabled=True):
        self.quantile = quantile
        self.enabled = enabled

    def fit(self, X, y=None):
        self.feature_names_in_ = np.asarray(X.columns, dtype=object)
        self.columns_ = [c for c in AREA_COLUMNS if c in X.columns]
        self.upper_ = X[self.columns_].quantile(self.quantile)
        return self

    def transform(self, X):
        z = X.copy()
        if self.enabled:
            z[self.columns_] = z[self.columns_].clip(lower=0, upper=self.upper_, axis=1)
        return z

def make_preprocessor(x_train):
    numeric = x_train.select_dtypes(include='number').columns.tolist()
    categorical = [c for c in x_train if c not in numeric]
    encoder = ColumnTransformer([
        ('num', Pipeline([('impute', SimpleImputer(strategy='median', add_indicator=True)),
                          ('scale', StandardScaler())]), numeric),
        ('cat', Pipeline([('impute', SimpleImputer(strategy='constant', fill_value='__MISSING__')),
                          ('onehot', OneHotEncoder(handle_unknown='ignore', sparse_output=False))]), categorical),
    ], verbose_feature_names_out=True)
    return Pipeline([('clip', QuantileClipper()), ('encode', encoder)])
