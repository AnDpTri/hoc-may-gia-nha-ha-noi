import hashlib
import json
from pathlib import Path
import unittest
import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from src.preprocessing import load_raw
from src.modeling import FeatureBuilder, make_model, predict_nonnegative
from src.experiments import temporal_folds

ROOT=Path(__file__).resolve().parents[1]

class TestModeling(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw=load_raw(ROOT/'data/raw/AmesHousing.tsv')
        cls.train=cls.raw[cls.raw['Yr Sold']<2010].reset_index(drop=True)

    def test_temporal_folds_disjoint_and_ordered(self):
        for fit,val in temporal_folds(self.train):
            self.assertFalse(set(fit)&set(val))
            self.assertLess(self.train.iloc[fit]['Yr Sold'].max(),self.train.iloc[val]['Yr Sold'].min())
            self.assertNotIn(2010,self.train.iloc[val]['Yr Sold'].unique())

    def test_features_do_not_depend_on_label_or_identifier(self):
        x=self.train.head(8); changed=x.copy()
        changed['SalePrice']=10**9; changed['PID']='ID_CHANGED'; changed['Order']=-1
        f=FeatureBuilder(engineered=True,log_areas=True)
        pd.testing.assert_frame_equal(f.transform(x),f.transform(changed))

    def test_complete_pipeline_can_predict_raw_unseen_categories(self):
        x=self.train.head(80); m=make_model(x,Ridge(alpha=10),engineered=True)
        m.fit(x,x.SalePrice)
        new=x.head(3).drop(columns='SalePrice').copy(); new['Neighborhood']='UNSEEN_AREA'
        p=predict_nonnegative(m,new)
        self.assertTrue(np.isfinite(p).all() and (p>=0).all())
        scaler=m.regressor_.named_steps['preprocess'].named_steps['encode'].named_transformers_['num'].named_steps['scale']
        self.assertEqual(scaler.n_samples_seen_,80)

    def test_final_selection_matches_recorded_hash(self):
        path=ROOT/'reports/experiments/results.json'
        if not path.exists():self.skipTest('Chưa chạy thực nghiệm đầy đủ')
        result=json.loads(path.read_text(encoding='utf-8'))
        frozen=(ROOT/'reports/experiments/selection_frozen_before_test.json').read_bytes()
        self.assertEqual(result['selection_sha256'],hashlib.sha256(frozen).hexdigest())
        self.assertFalse(json.loads(frozen)['test_used_for_selection'])

if __name__=='__main__':unittest.main()
