# Dự đoán giá nhà Hà Nội — Học máy, Nhóm 02

Đề tài: **Dự báo bất động sản dựa trên đặc điểm nhà ở** — hồi quy tuyến tính có chính quy hoá (Ridge, Lasso, Elastic Net), đối chiếu Random Forest và Gradient Boosting.
Thành viên: Trần Văn Dưỡng, Đặng Hoàng An. Báo cáo: [`Nhóm 2.docx`](Nhóm%202.docx) (bản PDF: [`Nhóm 2.pdf`](Nhóm%202.pdf)). Mã nguồn: <https://github.com/AnDpTri/hoc-may-gia-nha-ha-noi>.

## Dữ liệu
- Nguồn: [`tinixai/vietnam-real-estates`](https://huggingface.co/datasets/tinixai/vietnam-real-estates) (Hugging Face, giấy phép CC BY-NC 4.0 — chỉ dùng phi thương mại, ghi công TiniX AI).
- Phạm vi: tin **bán nhà riêng / nhà phố tại Hà Nội**, đăng 6/2025 – 3/2026.
- Sau làm sạch: **390.169 tin** — train 312.092 / test 78.077 (chia ngẫu nhiên 80/20, seed 42, gán ngay sau bước khử trùng lặp; thống kê lọc ngoại lai theo phường chỉ học từ tập train).
- Biến mục tiêu: `log(giá)`; 17 đặc trưng gốc (6 số, 7 cờ văn bản, 4 phân loại) — xem `data_processed/feature_config.json` và từ điển dữ liệu `survey/10_tu_dien_du_lieu.csv`.

## Cấu trúc thư mục
| Đường dẫn | Nội dung |
|---|---|
| `01_tien_xu_ly_gia_nha_ha_noi(last).ipynb` | Tải dữ liệu, lọc Hà Nội + loại hình, parse giá, khử trùng lặp, lọc ngoại lai, tạo đặc trưng, chia train/test |
| `01b_bo_sung_khao_sat_chat_luong_du_lieu.ipynb` | Bảng chất lượng dữ liệu, so sánh trước – sau, phân bố và quan hệ đặc trưng – giá |
| `02_huan_luyen_mo_hinh.ipynb` | Huấn luyện 4 mô hình tuyến tính + Random Forest, chọn α, đường đi hệ số, thí nghiệm kích thước dữ liệu |
| `04_danh_gia_bo_sung_va_cai_tien.ipynb` | Baseline, kiểm định chéo 5-fold, phần dư, so sánh cách chia, Target Encoding, Gradient Boosting, tối ưu siêu tham số, ablation |
| `03_demo_dinh_gia_nha.ipynb` | Demo Gradio |
| `data_processed/` | Dữ liệu thô đã lọc, dữ liệu sạch, `train.parquet`, `test.parquet`, cấu hình đặc trưng |
| `models/` | Các mô hình đã huấn luyện (`.joblib`) và `demo_meta.json` |
| `results/`, `survey/`, `figures/` | Bảng kết quả, bảng khảo sát, hình vẽ dùng trong báo cáo |

## Cài đặt (chạy trên máy)
Yêu cầu Python 3.11 – 3.13.

```bash
python -m venv .venv
```

```bash
.venv\Scripts\activate
```

```bash
pip install -r requirements.txt
```

`scikit-learn` phải đúng **1.6.1** — các mô hình trong `models/` được lưu bằng phiên bản này.

Mở notebook bằng Jupyter (hoặc VS Code) **tại thư mục gốc dự án**:

```bash
jupyter notebook
```

Notebook tự nhận thư mục dự án: biến môi trường `ML_PROJECT_DIR` (nếu đặt) → Google Drive khi chạy trên Colab (`MyDrive/ML_house_price`) → thư mục gốc dự án khi chạy trên máy (nơi có `requirements.txt`). Không cần sửa đường dẫn.

## Thứ tự chạy
Thời gian đo khi chạy lại trên máy CPU 12 luồng, RAM 16 GB (Colab CPU chậm hơn khoảng 2–3 lần):

| Bước | Notebook | Thời gian | Ghi chú |
|---|---|---|---|
| 1 | 01 | ~3 phút (+ tải ~1,7 GB lần đầu) | Tải dữ liệu từ Hugging Face vào `raw_parquet/`. Có thể **bỏ qua** vì `data_processed/` đã có sẵn kết quả |
| 2 | 01b | ~1 phút | Đọc `data_processed/`, kiểm tra tái lập đúng số dòng của 01 |
| 3 | 02 | ~8–10 phút | Tạo các mô hình tuyến tính, Random Forest và `demo_meta.json` |
| 4 | 04 | ~12 phút | Đọc α từ mô hình của 02; ghi `results/04/`, `figures/04/`, `models/gradient_boosting.joblib`; kiểm tra tin gần trùng train–test |
| 5 | 03 | ~1 phút | Mở demo; ô cuối in đường dẫn web (trên Colab tạo thêm link công khai) |

Nên đóng các chương trình nặng khác khi chạy 02 (cần khoảng 4–6 GB RAM trống).

Mọi bước ngẫu nhiên cố định `SEED = 42`.

## Kết quả chính (tập kiểm tra)
| Mô hình | MAPE CV 5-fold (%) | MAPE test (%) | MdAPE test (%) | MAE test (tỷ) |
|---|---|---|---|---|
| Baseline: đơn giá quận × diện tích | 28,40 ± 0,14 | 28,45 | 22,88 | 5,74 |
| Lasso | 22,43 ± 0,08 | 22,44 | 17,20 | 4,46 |
| Random Forest (tối ưu) | 20,99 ± 0,19 | 20,97 | 15,03 | 4,14 |
| **Gradient Boosting (tối ưu)** | **18,49 ± 0,11** | **18,39** | **13,44** | **3,64** |

Bảng đầy đủ: `results/04/bang_so_sanh_cuoi.csv`.

## Ghi chú
- Notebook 01 ghi thêm bản CSV `data_processed/02_hanoi_nhapho_clean.csv` (137 MB, vượt giới hạn GitHub) — không đưa vào kho; bản `.parquet` cùng nội dung có sẵn. Dữ liệu gốc (~1,7 GB) cũng không đưa vào kho, notebook 01 tự tải lại từ Hugging Face.
- `requirements_runtime.txt` là danh sách phiên bản được notebook 04 tự ghi lại trong môi trường đã tạo kết quả hiện tại.
