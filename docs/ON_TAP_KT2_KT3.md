# Ôn tập KT2 KT3 và bảo vệ dự án

## KT2

1. **Vì sao DummyMeanLog?** Mất mát chính là bình phương sai số trên log, nên trung bình log của train là baseline hợp lý. Không lấy trung bình từ test.
2. **OLS và regularization khác nhau thế nào?** OLS tối thiểu SSE; Ridge thêm phạt L2, Lasso thêm L1, Elastic Net kết hợp hai loại. Intercept không bị phạt trong triển khai này.
3. **Vì sao scale?** Hệ số phụ thuộc đơn vị. Scale số giúp giảm việc cùng mức phạt xử lý khác nhau chỉ vì một biến đo ft² và một biến đo năm. One-hot vẫn 0/1, nên không diễn giải độ lớn mọi hệ số như hoàn toàn tương đương.
4. **Mô hình nhìn nhãn/ID trong X không?** Mô hình nhận raw nhưng FeatureBuilder bỏ SalePrice, Order, PID, Sale Type và Sale Condition ngay trong pipeline. Tests thay nhãn/ID xác nhận đặc trưng không thay đổi.
5. **Vì sao log?** Giảm độ lệch và trọng số tương đối của nhà rất đắt. Hoàn nguyên bằng expm1; clip dự đoán về không âm. Có thể có độ chệch trên trung bình giá USD sau hoàn nguyên.
6. **Nhận diện quá khớp thế nào?** Đối chiếu train–validation và ổn định theo năm. OLS có train log khoảng 0.078 nhưng CV khoảng 0.143; các mô hình chính quy hóa giảm lỗi CV.
7. **Chỉ số nào chính?** RMSE log; MAE/RMSE USD giúp hiểu số tiền; R² bổ trợ. Không dùng Accuracy cho hồi quy.
8. **Cần gì để chạy lại?** Dữ liệu raw có sẵn, Python 3.11, requirements, `python -m src.run_all`. Mã không phụ thuộc đường dẫn máy cá nhân.

## KT3

1. **Đã cải tiến gì?** Bảy đặc trưng tổng hợp, clipping/log diện tích, tìm alpha/l1_ratio và thử boosting. Có bảng ablation đo từng thay đổi, kể cả kết quả không tăng.
2. **Vì sao không giữ feature engineering?** Trên cùng alpha Ridge và fold, RMSE log tăng từ khoảng 0.12772 lên 0.12982. Kết luận chỉ áp dụng bộ biến mới đã thử.
3. **Vì sao không chọn mô hình có test thấp nhất?** Lựa chọn dựa trên CV và khóa trước test. Đổi sang mô hình khác sau nhìn test làm test trở thành dữ liệu phát triển.
4. **Lasso cuối tốt hơn KT2 nhiều không?** Không. CV khoảng 0.12719 so với Elastic Net KT2 0.12749; chênh lệch ~0.23%, nhỏ hơn std giữa năm. Không tuyên bố cải thiện có ý nghĩa thống kê chắc chắn.
5. **Alpha tối ưu là bao nhiêu?** Lasso 0.0003; Ridge 10; Elastic Net alpha 0.0003, l1_ratio 0.9. Đây là tối ưu trong lưới đã thử, không phải tối ưu tuyệt đối.
6. **LassoCV/RidgeCV có dùng thật không?** Có, thí nghiệm phụ fit preprocessing năm 2006 rồi đóng băng. Cách này không nhìn validation 2007–2009; khác preprocessing với bảng chính nên không so kết quả như chỉ khác lớp API.
7. **Vì sao không đặt preprocessing toàn train rồi LassoCV?** Khi CV nội bộ chia, preprocessing đã nhìn fold validation. Bảng chính dùng GridSearchCV bên ngoài toàn pipeline để tránh lỗi đó.
8. **Boosting hoạt động thế nào?** Cộng nhiều cây theo từng bước để sửa phần lỗi còn lại của mô hình trước. Số vòng, learning_rate, số lá và phạt L2 kiểm soát độ phức tạp.
9. **Permutation importance chứng minh nhân quả không?** Không. Đo mức tăng lỗi khi phá quan hệ của một đầu vào trên validation 2009; các đặc trưng liên quan có thể chia sẻ tầm quan trọng.
10. **Hash lựa chọn chứng minh không gian lận không?** Không tự chứng minh. Hash chỉ kiểm tra nhất quán giữa tệp; quy trình code ghi lựa chọn trước phần chấm test và có thể kiểm tra. Nhật ký/thời gian do chương trình tạo không là chứng thực độc lập.
11. **Nhóm nào khó?** Nhà >250k có MAE USD cao hơn; một số nhà đắt bị dự đoán thấp. Không tự xóa những mẫu test này.
12. **Hạn chế quan trọng?** Ames lịch sử, test 2010 một phần năm, ba fold ít, CV lạc quan do tìm kiếm, chưa có dữ liệu mới để xác nhận thêm và chất lượng một số biến đánh giá có thể chủ quan.

## Thực hành 10–15 phút

Chạy các đoạn dưới trong notebook KT2, nơi đã có `train`, `make_model`, `temporal_folds`, `metrics`, `predict_nonnegative`.

```python
from sklearn.linear_model import Ridge, Lasso
from sklearn.model_selection import GridSearchCV
from src.experiments import SCORER

# Đổi alpha trên fold đầu, đọc đủ bốn chỉ số.
a, b = temporal_folds(train)[0]
model = make_model(train, Ridge(alpha=100))
model.fit(train.iloc[a], train.iloc[a].SalePrice)
metrics(train.iloc[b].SalePrice,
        predict_nonnegative(model, train.iloc[b]))

# Tìm kiếm nhỏ trên train, không chấm test.
search = GridSearchCV(
    make_model(train, Ridge()),
    {'regressor__model__alpha': [1, 10, 100]},
    cv=temporal_folds(train), scoring=SCORER)
search.fit(train, train.SalePrice)
print(search.best_params_)

# Đổi thuật toán để tự luyện, giữ nguyên pipeline và fold.
lasso = make_model(train, Lasso(alpha=0.001, max_iter=50000))
lasso.fit(train.iloc[a], train.iloc[a].SalePrice)
```

Tự thực hành trước khi nộp. AI đã hỗ trợ tạo mã/tài liệu; không dùng kết quả vấn đáp mẫu thay cho việc hiểu mã.
