# Đối chiếu tiêu chí Bài kiểm tra 1

| STT | Tiêu chí | Minh chứng |
|---:|---|---|
| 1 | Phát biểu bài toán | Báo cáo mục 1; notebook mục 1 |
| 2 | Mục tiêu và tiêu chí thành công | Báo cáo mục 2; RMSE log, MAE USD, baseline dự kiến |
| 3 | Nguồn và mô tả dữ liệu | data/SOURCES.md; docs/data_dictionary.csv đủ 82 cột; DataDocumentation.txt |
| 4 | Thống kê và phân bố | Notebook mục 3; numeric_summary_train.csv, categorical_summary_train.csv; hình 01–02 |
| 5 | Quan hệ và ít nhất 3 nhận xét | Notebook mục 4; hình 03–04,07; target_correlations_train.csv |
| 6 | Phát hiện vấn đề có số lượng | quality_all_columns.csv; outliers_iqr_train.csv; summary.json |
| 7 | Xử lý có lý do và trước sau | src/preprocessing.py; before_after.csv, clipping_audit.csv; hình 06 |
| 8 | Mã hóa, chuẩn hóa, chia tập | Pipeline/ColumnTransformer; split_manifest.csv; notebook mục 6 |
| 9 | Cá nhân giải thích đánh giá | Báo cáo chiến lược theo năm; notebook mục 7; tài liệu ôn tập |
| 10 | Cá nhân thực hành | docs/ON_TAP_VAN_DAP.md; thao tác trực tiếp trên notebook |

Tiêu chí 9–10 phải được giảng viên đánh giá qua sinh viên. Việc có tài liệu không bảo đảm điểm vấn đáp. Các tiêu chí nhóm cũng có thể được hỏi lại trên chính dữ liệu/mã.
