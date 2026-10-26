# Minh chứng KT2 KT3

| Mốc | Tiêu chí | Minh chứng |
|---|---|---|
| KT2 | 1 Thuật toán | modeling.py, experiments.py; 4 mô hình tuyến tính và baseline |
| KT2 | 2 Baseline | DummyMeanLog; kt2_cv_summary.csv, final_test_comparison.csv |
| KT2 | 3 Pipeline | FeatureBuilder → preprocessing → estimator; TransformedTargetRegressor |
| KT2 | 4 Mã nguồn | src/run_all.py; requirements.txt; notebook 02 đã chạy |
| KT2 | 5 Huấn luyện/kiểm thử | all_cv_folds.csv; selection_frozen_before_test.json |
| KT2 | 6 Chỉ số và hình | RMSE log, MAE/RMSE USD, R²; hình 09,11,16 |
| KT2 | 7 Phân tích lỗi | errors_by_price_band.csv; largest_errors.csv |
| KT2 | 8 Nguyên lý cá nhân | LaTeX lý thuyết, ON_TAP_KT2_KT3.md |
| KT2 | 9 Giải thích dữ liệu | Hệ số, sparsity.csv, permutation importance |
| KT2 | 10 Thực hành | Ô cuối notebook 02 và bài tập đổi alpha/chỉ số |
| KT3 | 1 Hạn chế | Train–CV gap, nhóm giá cao, đa cộng tuyến |
| KT3 | 2 Giải pháp | Đặc trưng, clip/log, tuning và boosting |
| KT3 | 3 Cải tiến dữ liệu | FeatureBuilder engineered=True; ablation.csv |
| KT3 | 4 Thuật toán/cấu hình mới | HistGradientBoosting; tuned regularization |
| KT3 | 5 Tối ưu | grid_*.csv, lưới trong experiments.py |
| KT3 | 6 Trước/sau | kt2/kt3_cv_summary.csv; ablation.csv |
| KT3 | 7 Tổng quát hóa | final_test_comparison.csv; cv_vs_test.csv |
| KT3 | 8 Biểu đồ | Hình 10–16; tất cả có diễn giải trong LaTeX/notebook |
| KT3 | 9 Lựa chọn cá nhân | Lasso_tuned theo CV; không chọn lại theo test |
| KT3 | 10 Thực hành | Notebook 03, ON_TAP_KT2_KT3.md |

Điểm cá nhân phải được giảng viên chấm qua vấn đáp và thao tác. Các tệp và checklist không tự bảo đảm điểm.
