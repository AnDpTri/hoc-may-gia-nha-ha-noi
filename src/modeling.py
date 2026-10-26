"""Quy trình dự đoán nhận raw DataFrame, tự làm sạch và trả giá USD."""
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.compose import TransformedTargetRegressor
from sklearn.pipeline import Pipeline
from .preprocessing import clean_features, make_preprocessor, AREA_COLUMNS

class FeatureBuilder(BaseEstimator, TransformerMixin):
    def __init__(self, engineered=False, log_areas=False):
        self.engineered = engineered
        self.log_areas = log_areas

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        z = clean_features(X)
        if self.engineered:
            z['HouseAge'] = z['Yr Sold'] - z['Year Built']
            z['RemodAge'] = z['Yr Sold'] - z['Year Remod/Add']
            z['TotalSF'] = z[['Total Bsmt SF','1st Flr SF','2nd Flr SF']].sum(axis=1, min_count=3)
            z['TotalBath'] = z['Full Bath'] + .5*z['Half Bath'] + z['Bsmt Full Bath'] + .5*z['Bsmt Half Bath']
            z['HasGarage'] = (z['Garage Cars'].fillna(0) > 0).astype(int)
            z['HasBasement'] = (z['Total Bsmt SF'].fillna(0) > 0).astype(int)
            z['TotalPorch'] = z[['Open Porch SF','Enclosed Porch','3Ssn Porch','Screen Porch']].sum(axis=1)
        if self.log_areas:
            for c in AREA_COLUMNS + ['TotalSF','TotalPorch']:
                if c in z:
                    z[c] = np.log1p(z[c].clip(lower=0))
        return z

def make_model(raw_schema, estimator, engineered=False, clipping=True, log_areas=False):
    builder = FeatureBuilder(engineered=engineered, log_areas=log_areas)
    # Chỉ xem schema, không học trung bình/phân vị hoặc dùng nhãn.
    schema = builder.transform(raw_schema.iloc[:1])
    prep = make_preprocessor(schema)
    prep.set_params(clip__enabled=clipping)
    pipeline = Pipeline([('features', builder), ('preprocess', prep), ('model', estimator)])
    return TransformedTargetRegressor(regressor=pipeline, func=np.log1p,
                                      inverse_func=np.expm1, check_inverse=True)

def predict_nonnegative(model, X):
    return np.maximum(0, model.predict(X))
