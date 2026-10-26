# Ôn tập vấn đáp và thực hành KT1

Đọc notebook và tự chạy từng ô trước khi nộp. Bài viết và mã được hỗ trợ bởi AI; câu trả lời cá nhân phải dựa trên hiểu biết của sinh viên.

1. **Một mẫu là gì?** Một giao dịch nhà ở tại Ames; `PID` chỉ định danh thửa đất, không phải đầu vào dự đoán.
2. **Vì sao là hồi quy?** Nhãn `SalePrice` là giá trị USD liên tục, không phải nhãn lớp.
3. **Có 82 đặc trưng không?** Có 82 cột: một nhãn, hai định danh và 79 biến còn lại. Bỏ thêm Sale Type và Sale Condition vì thời điểm dự báo là trước khi chốt giao dịch, còn 77 đầu vào.
4. **NA có luôn là thiếu?** Không. `Alley=NA` là không có hẻm, `Pool QC=NA` là không có bể bơi theo tài liệu nguồn. Ô trống vẫn được giữ là thiếu. `Mas Vnr Type=None` là một giá trị hợp lệ.
5. **Vì sao giữ năm 2010 làm test?** Mô phỏng dự báo ở thời điểm sau các năm học. Chia ngẫu nhiên có thể trộn tín hiệu quá khứ và tương lai. Năm 2010 chỉ có một phần năm; đây là hạn chế cần nêu.
6. **Median học ở đâu?** Chỉ trên train; khi kiểm định chéo phải fit lại cả pipeline trong từng fold.
7. **Vì sao log?** Giá lệch phải, log làm giảm ảnh hưởng thang giá rất lớn; hoàn nguyên bằng `np.expm1`. Tối ưu trên log không bảo đảm dự đoán trung bình USD không chệch.
8. **Tại sao không xóa nhà trên 4000 ft²?** Nhà lớn không tự động là sai. KT1 giữ mọi dòng, clip một số đặc trưng theo p99 của train. Tác động clip cần ablation ở KT2/3.
9. **Vì sao chuẩn hóa?** L1/L2 phạt hệ số; đơn vị ft² và năm chênh lệch sẽ làm mức phạt không công bằng nếu không scale. One-hot giữ 0/1, chuẩn hóa các cột số.
10. **Đa cộng tuyến là gì?** Garage Cars và Garage Area tương quan mạnh; hệ số OLS có thể kém ổn định, là động cơ thử Ridge/Elastic Net.
11. **Alpha tăng thì sao?** Hệ số bị co mạnh hơn, thường giảm phương sai và tăng độ chệch; quá lớn gây thiếu khớp. Không dùng test để chọn alpha.
12. **RidgeCV/LassoCV bên trong Pipeline có đủ tránh rò rỉ?** Chưa chắc. Nếu tiền xử lý fit toàn bộ train rồi bộ CV nội bộ mới chia fold, thống kê preprocessing đã nhìn fold validation. Mốc sau cần vòng CV ngoài fit lại pipeline cho từng cấu hình, hoặc triển khai từng fold rõ ràng. Với thời gian, dùng các fold theo năm.
13. **Ba nhận xét quan hệ?** Chất lượng, diện tích ở và sức chứa garage tương quan dương với giá; diện tích garage với sức chứa garage tương quan cao; tương quan không chứng minh nhân quả.
14. **Đã đạt RMSE mục tiêu chưa?** Chưa huấn luyện ở KT1; 0,18 trên log là mục tiêu dự kiến, không phải kết quả đã đo.

## Bài tập thực hành

```python
# 1. Thống kê một đặc trưng
train['Lot Area'].describe()

# 2. Đếm thiếu sau khi làm sạch và đổi biến để thực hành
x_train['Lot Frontage'].isna().sum()

# 3. Đổi median sang mean rồi fit trên train
from sklearn.base import clone
alternative = clone(preprocessor)
alternative.set_params(encode__num__impute__strategy='mean')
alternative.fit_transform(x_train)

# 4. Vẽ lại quan hệ, giải thích điểm ngoại lai
train.plot.scatter(x='Gr Liv Area', y='SalePrice', alpha=0.3)

# 5. Đổi mức clipping và so sánh số ô bị thay đổi, không chọn theo test
alternative = clone(preprocessor).set_params(clip__quantile=0.995)
alternative.fit_transform(x_train)
```

Các biến `train`, `x_train`, `preprocessor` có trong notebook được giao.
