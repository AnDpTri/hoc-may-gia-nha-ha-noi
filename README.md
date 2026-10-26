# Dự đoán giá bất động sản dựa trên đặc điểm nhà ở

**Bài kiểm tra 1 — Học máy, học kỳ 1 năm học 2026–2027.**

Bộ nộp gồm báo cáo Word tiếng Việt, notebook đã chạy, dữ liệu Ames gốc, từ điển đủ 82 cột, mã tiền xử lý và bảng kiểm tra chất lượng. Mốc này chưa huấn luyện Linear Regression/Ridge/Lasso/Elastic Net; phần lý thuyết và kế hoạch đánh giá được chuẩn bị cho mốc sau.

## Mở bài

- [Báo cáo Word](reports/Bao_cao_KT1_Du_doan_gia_nha.docx)
- [Notebook đã chạy](notebooks/01_KT1_Ames_Housing.ipynb)
- [Ôn vấn đáp và thực hành](docs/ON_TAP_VAN_DAP.md)
- [Đối chiếu 10 tiêu chí](docs/DOI_CHIEU_TIEU_CHI.md)
- [Từ điển 82 cột](docs/data_dictionary.csv)
- [Nguồn và điều kiện sử dụng](data/SOURCES.md)
- [Nhật ký và thông tin cần bổ sung](docs/NHAT_KY_DONG_GOP.md)

## Kết quả KT1

| Nội dung | Kết quả |
|---|---:|
| Dữ liệu gốc | 2.930 dòng × 82 cột |
| Đầu vào sau bỏ định danh/thông tin chốt giao dịch | 77 biến |
| Train 2006–2009 | 2.589 dòng |
| Test năm 2010 | 341 dòng |
| Ma trận sau tiền xử lý | 350 cột |
| Ô trống thật / mã NA chỉ không có tiện ích | 719 / 13.278 |
| Ô năm vi phạm giả định | 6 |
| Dòng trùng / PID trùng | 0 / 0 |

Fit clipping, điền khuyết, chuẩn hóa và one-hot chỉ trên train. Giá được biến đổi `log1p`, giữ mọi dòng và không clip nhãn. Chỉ EDA train; test chỉ audit/transform. `data/processed/ames_ready.npz` dùng cho kiểm tra dữ liệu và fit cuối train, **không dùng để tính CV** vì imputer/scaler đã học toàn bộ train. Khi CV phải fit pipeline từ đặc trưng gốc trong từng fold.

## Chạy lại bằng Python 3.11

Từ thư mục gốc của repo, trong PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m src.kt1
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe docs\build_notebook.py
```

Notebook có thể mở bằng VS Code (Python + Jupyter) hoặc Jupyter cài thêm. Chọn interpreter `.venv` rồi Run All. Mã tìm thư mục tương đối, không cần sửa đường dẫn theo máy. Dữ liệu raw đã đi kèm, nên các bước phân tích chạy được khi không có mạng.

`requirements.txt` khóa phiên bản môi trường đã thực chạy. Tái tạo báo cáo Word là tùy chọn: cài `python-docx`, rồi chạy `python docs/build_report.py`. Word đã tạo sẵn nên không bắt buộc cài thư viện này để chạy EDA.

## Phạm vi và tính trung thực

Đây là dữ liệu giao dịch Ames, Iowa 2006–2010, đơn vị USD và ft²; không phải dữ liệu rao bán Việt Nam. Chưa có kết quả mô hình; mục tiêu RMSE log ≤ 0,18 là mục tiêu đề xuất. AI hỗ trợ chuẩn bị mã và tài liệu, được khai báo trong báo cáo. Sinh viên tự bổ sung họ tên/MSSV/lớp, kiểm tra, hiểu mã và ghi nhận đóng góp thực tế trước khi nộp. Không tự tạo lịch sử đóng góp của sinh viên.
