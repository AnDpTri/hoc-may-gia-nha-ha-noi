# Mô hình dự đoán giá nhà Ames

- Mục đích: demo học phần hồi quy và regularization, bối cảnh Ames 2006–2010.
- Model: pipeline Lasso, alpha=0.0003; imputer/scaler/one-hot và clip p99 được học trên train.
- Nhãn học: log1p giá; trả USD bằng expm1 và chặn về không âm trong CLI.
- Train: 2.589 giao dịch 2006–2009; test: 341 giao dịch năm 2010.
- CV: ba fold mở rộng theo năm; RMSE log trung bình khoảng 0.12719, std mẫu 0.00977.
- Test: RMSE log khoảng 0.15095, MAE khoảng 14.840 USD, R² khoảng 0.91893.
- Chọn mô hình bằng CV, giữ Lasso dù một số mô hình có test RMSE log thấp hơn đôi chút.
- Giới hạn: nhà đắt có sai số tiền lớn; dữ liệu một thành phố và lịch sử; không đánh giá thị trường Việt Nam hoặc hiện tại.

Kết quả chính xác nằm trong reports/experiments/results.json; cấu hình khóa trong selection_frozen_before_test.json.

`final_model.joblib` được tải bởi `python -m src.predict`. Không cần fit lại khi dùng demo.
