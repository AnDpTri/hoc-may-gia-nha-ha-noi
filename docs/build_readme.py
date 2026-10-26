from pathlib import Path
import json

root=Path(__file__).resolve().parents[1]
r=json.loads((root/'reports/experiments/results.json').read_text(encoding='utf-8'))
text=f'''# Dự đoán giá bất động sản dựa trên đặc điểm nhà ở

Dự án môn Học máy, học kỳ 1 năm học 2026–2027. Bộ nộp **KT1, KT2 và KT3** gồm dữ liệu, mã nguồn, ba notebook đã chạy, báo cáo LaTeX/PDF, mô hình và demo CLI.

## Mở kết quả

- [Báo cáo tổng hợp PDF](reports/Bao_cao_KT1_KT2_KT3.pdf)
- [Bộ nguồn LaTeX để tải lên Overleaf](reports/Bao_cao_KT1_KT2_KT3_LaTeX.zip)
- [Nguồn LaTeX chỉnh sửa được](reports/latex_full/main.tex)
- [KT1 khảo sát và tiền xử lý](notebooks/01_KT1_Ames_Housing.ipynb)
- [KT2 huấn luyện và đánh giá](notebooks/02_KT2_Train_Evaluate.ipynb)
- [KT3 tối ưu và cải tiến](notebooks/03_KT3_Tuning_Improvement.ipynb)
- [Bản Word riêng KT1](reports/Bao_cao_KT1_Du_doan_gia_nha.docx)

## Kết quả thực nghiệm

Ames gốc có 2.930 dòng × 82 cột; dùng 77 đầu vào, sau mã hóa có 350 cột. Train 2006–2009 gồm 2.589 mẫu; test 2010 gồm 341 mẫu. Ba fold CV mở rộng theo năm, **fit lại toàn pipeline trong mỗi fold**.

| Nội dung | Kết quả |
|---|---:|
| Mô hình cuối chọn theo CV | {r['selected_model']} alpha=0.0003 |
| RMSE log CV mean ± std mẫu | {r['selected_cv']['cv_rmse_log_mean']:.5f} ± {r['selected_cv']['cv_rmse_log_std']:.5f} |
| RMSE log test | {r['test_metrics']['rmse_log']:.5f} |
| MAE test USD | {r['test_metrics']['mae_usd']:,.2f} |
| R² test | {r['test_metrics']['r2_usd']:.5f} |
| Giảm RMSE log test so với baseline | {r['test_rmse_log_improvement_vs_dummy_pct']:.2f}% |

KT2 so sánh DummyMeanLog, OLS, Ridge, Lasso và Elastic Net. KT3 có grid search, bảy đặc trưng mới, ablation clip/log và đối chứng HistGradientBoosting. Đặc trưng mới chưa vượt cấu hình gốc; bỏ clipping làm kết quả kém ổn định. Không chọn lại theo test: Lasso được giữ dù một số cấu hình khác có test log thấp hơn đôi chút. Chênh lệch giữa các mô hình regularization nhỏ so với biến động theo năm.

[Kết quả đầy đủ](reports/experiments) gồm từng fold, mọi ứng viên grid, lựa chọn khóa trước test, lỗi từng mẫu và tầm quan trọng hoán vị. Ví dụ RidgeCV/LassoCV dùng preprocessing đóng băng năm 2006 để không nhìn các fold validation; bảng chính dùng GridSearchCV trên toàn pipeline.

## Cài và chạy

Dùng Python 3.11, mở PowerShell từ gốc repo:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt

# Tái tạo KT1 KT2 KT3, notebook, nguồn LaTeX và kiểm tra
.\.venv\Scripts\python.exe -m src.run_all

# Demo từ model đã lưu, không huấn luyện lại
.\.venv\Scripts\python.exe -m src.predict --example
.\.venv\Scripts\python.exe -m src.predict --input examples\house.json --output work\predictions.csv

# Kiểm tra
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Chạy toàn bộ mất vài phút tùy máy. Dữ liệu raw đi kèm nên huấn luyện không cần mạng. Mở notebook bằng VS Code + Python/Jupyter và chọn `.venv`. Notebook KT2/KT3 đọc bảng đã lưu và có ô demo trên train, không tự chấm lại test mỗi lần mở.

Chạy riêng: `python -m src.kt1`, `python -m src.experiments`, `python -m src.plots`. Word KT1 có sẵn; muốn tạo lại cần cài thêm `python-docx` rồi chạy `python docs/build_report.py`.

## LaTeX

Trên Overleaf chọn **New project → Existing project (.zip)**, tải `reports/Bao_cao_KT1_KT2_KT3_LaTeX.zip`, mở `main.tex` và Recompile. Có đủ ảnh, hỗ trợ pdfLaTeX/T5 hoặc XeLaTeX/fontspec. Không cần tải dataset/Python lên Overleaf.

Nếu có TeX cục bộ:

```powershell
Set-Location reports\latex_full
xelatex main.tex
xelatex main.tex
```

Nguồn được kiểm tra bằng Tectonic 0.17.0; engine không kèm repo. `run_all` tạo nguồn LaTeX, không tự cài TeX hoặc biên dịch PDF. PDF đã biên dịch được lưu sẵn.

## Cấu trúc

| Thư mục | Nội dung |
|---|---|
| data/raw | TSV và tài liệu gốc giữ nguyên bytes |
| data/processed | Split và ma trận KT1; không dùng ma trận đã fit cả train để CV |
| src | Tiền xử lý, mô hình, thực nghiệm, hình và CLI |
| notebooks | Ba notebook đã chạy |
| reports/experiments | Kết quả chi tiết, dự đoán, grid, lỗi |
| reports/latex_full | Nguồn báo cáo tổng hợp và ảnh |
| models | Model cuối, model card |
| tests | Kiểm tra leakage, fold, schema, inference và hash |
| docs | Ôn vấn đáp, đối chiếu tiêu chí và các builder |

## Trước khi nộp

- [Nguồn và điều kiện dữ liệu](data/SOURCES.md), [từ điển 82 cột](docs/data_dictionary.csv).
- [Đối chiếu KT1](docs/DOI_CHIEU_TIEU_CHI.md), [KT2 KT3](docs/DOI_CHIEU_KT2_KT3.md).
- [Ôn KT1](docs/ON_TAP_VAN_DAP.md), [ôn KT2 KT3](docs/ON_TAP_KT2_KT3.md).
- [Thông tin và nhật ký](docs/NHAT_KY_DONG_GOP.md).

AI hỗ trợ tạo mã/tài liệu, đã khai báo trong báo cáo. Sinh viên điền họ tên, MSSV, lớp, giảng viên; tự kiểm tra, hiểu và ghi phần việc thực sự. Không tự tạo lịch sử đóng góp nhiều tuần. Phần vấn đáp và thực hành cá nhân phải do sinh viên thực hiện.

Dữ liệu thuộc Ames, Iowa 2006–2010, đơn vị USD và ft²; không đại diện thị trường Việt Nam hoặc hiện tại. Repo private mặc định; khi nộp cần cấp quyền phù hợp cho giảng viên.
'''
(root/'README.md').write_text(text,encoding='utf-8')
print('README updated')
