"""Kiểm tra các lỗi có thể làm sai đánh giá mô hình ở mốc sau."""
import unittest
from pathlib import Path
import numpy as np
import pandas as pd
from src.preprocessing import load_raw, clean_features, make_preprocessor

class TestPreprocessing(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        r = load_raw(Path(__file__).resolve().parents[1]/'data/raw/AmesHousing.tsv')
        cls.tr = clean_features(r[r['Yr Sold'] < 2010])
        cls.te = clean_features(r[r['Yr Sold'] == 2010])

    def test_schema_and_absence(self):
        self.assertFalse(set(['PID','Order','SalePrice','Sale Type','Sale Condition']) & set(self.tr))
        self.assertIn('__ABSENT__', set(self.tr['Alley']))
        self.assertIn('None', set(self.tr['Mas Vnr Type']))
        self.assertEqual(self.tr.shape[1], 77)

    def test_fit_only_train_and_transform_is_stable(self):
        p = make_preprocessor(self.tr)
        a = p.fit_transform(self.tr)
        saved = p.named_steps['clip'].upper_.copy()
        altered = self.te.copy()
        altered['Lot Area'] = 10**9
        altered['Neighborhood'] = 'UNSEEN_NEIGHBORHOOD'
        b = p.transform(altered)
        pd.testing.assert_series_equal(saved, p.named_steps['clip'].upper_)
        self.assertAlmostEqual(saved['Lot Area'], self.tr['Lot Area'].quantile(.99))
        self.assertEqual(a.shape[1], b.shape[1])
        self.assertTrue(np.isfinite(a).all() and np.isfinite(b).all())
        scaler = p.named_steps['encode'].named_transformers_['num'].named_steps['scale']
        self.assertEqual(scaler.n_samples_seen_, len(self.tr))

    def test_log_round_trip(self):
        values = np.array([13100, 161500, 755000], dtype=float)
        np.testing.assert_allclose(np.expm1(np.log1p(values)), values)

if __name__ == '__main__':
    unittest.main()
