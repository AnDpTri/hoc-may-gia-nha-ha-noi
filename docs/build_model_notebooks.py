"""Tạo và chạy notebook KT2/KT3 từ thực nghiệm đã lưu; không chấm lại test."""
from pathlib import Path
import nbformat as nbf
from nbclient import NotebookClient

ROOT=Path(__file__).resolve().parents[1]
md=nbf.v4.new_markdown_cell; code=nbf.v4.new_code_cell
setup="""from pathlib import Path
import sys, json
import pandas as pd
from IPython.display import Image, display
ROOT=Path.cwd()
if not (ROOT/'src').exists(): ROOT=ROOT.parent
sys.path.insert(0,str(ROOT))
DATA=ROOT/'reports/experiments'
assert (DATA/'results.json').exists(), 'Chạy python -m src.experiments trước'
result=json.loads((DATA/'results.json').read_text(encoding='utf-8'))
def table(name): return pd.read_csv(DATA/name)
def figure(name): display(Image(filename=str(ROOT/'reports/figures'/name)))
"""

def build(name,cells):
    nb=nbf.v4.new_notebook(cells=cells)
    nb.metadata={'kernelspec':{'display_name':'Python 3','language':'python','name':'python3'},'language_info':{'name':'python','version':'3.11'}}
    path=ROOT/'notebooks'/name
    nbf.write(nb,path)
    NotebookClient(nb,timeout=180,kernel_name='python3',resources={'metadata':{'path':str(ROOT)}}).execute()
    nbf.write(nb,path); print(path)

build('02_KT2_Train_Evaluate.ipynb',[
md('# Bài kiểm tra 2 · Huấn luyện và đánh giá\n\nSo sánh baseline dự đoán trung bình log giá, Linear Regression, Ridge, Lasso và Elastic Net. Dùng đúng train/test đã chốt ở KT1. Không tự chạy lại tìm kiếm khi mở notebook này; số liệu được đọc từ lần thực nghiệm đã lưu. Toàn bộ lệnh huấn luyện nằm ở `src/experiments.py`, tái tạo bằng `python -m src.experiments`.'),
code(setup),
md('## 1 Lựa chọn thuật toán và baseline\n\nOLS là tham chiếu tuyến tính không phạt. Ridge ổn định hệ số khi đa cộng tuyến. Lasso tạo nghiệm thưa. Elastic Net kết hợp cả hai. Baseline DummyRegressor học mean của log1p giá trên từng train fold, tránh lấy hằng số từ test.'),
code("from src.preprocessing import load_raw\nfrom src.experiments import temporal_folds\nraw=load_raw(ROOT/'data/raw/AmesHousing.tsv')\ntrain=raw[raw['Yr Sold']<2010].reset_index(drop=True)\nfor a,b in temporal_folds(train):\n    print('Train years:',sorted(train.iloc[a]['Yr Sold'].unique()), 'validation:',train.iloc[b]['Yr Sold'].unique(), 'sizes:',len(a),len(b))"),
md('## 2 Pipeline đầy đủ và cấu hình KT2\n\nFeatureBuilder tự bỏ nhãn/ID và làm sạch raw; preprocessing clip p99, điền thiếu, chuẩn hóa số, one-hot. TransformedTargetRegressor học log1p và hoàn nguyên expm1. Mỗi fold fit lại toàn bộ. KT2 dùng alpha Ridge=10, Lasso=0.001, Elastic Net=0.001 với l1_ratio=0.5, cố định trước tìm kiếm KT3.'),
code("from sklearn.linear_model import Ridge\nfrom src.modeling import make_model\ndisplay(make_model(train,Ridge(alpha=10)))"),
md('## 3 Kết quả kiểm định\n\nRMSE log là chỉ số chính, mean/std mẫu qua 3 năm kiểm định. Các cột train cho thấy chênh lệch mức khớp. Thời gian phụ thuộc máy; không dùng để khẳng định chênh lệch tốc độ tuyệt đối.'),
code("display(table('kt2_cv_summary.csv'))\ndisplay(table('all_cv_folds.csv').query('model in [\"DummyMeanLog\",\"LinearRegression\",\"Ridge_default\",\"Lasso_default\",\"ElasticNet_default\"]'))\nfigure('09_kt2_cv.png')"),
md('OLS có khoảng cách train–validation lớn hơn các mô hình chính quy hóa. Ridge/Lasso/Elastic Net đều vượt baseline rõ rệt trên CV. Elastic Net cấu hình ban đầu có RMSE log trung bình tốt nhất trong KT2, nhưng chênh lệch với Ridge rất nhỏ so với biến động giữa năm. Chưa thể nói mô hình đó ưu thế chắc chắn.'),
md('## 4 Kết quả test đã khóa sau KT3\n\nĐể giữ test độc lập, bảng test KT2 được tính sau khi toàn bộ lựa chọn KT3 đã khóa. Không dùng bảng này để đổi alpha hoặc chọn lại mô hình cuối.'),
code("display(table('final_test_comparison.csv').query('model in [\"DummyMeanLog\",\"LinearRegression\",\"Ridge_default\",\"Lasso_default\",\"ElasticNet_default\"]'))\nfigure('16_cv_vs_test.png')"),
md('## 5 Phân tích lỗi và giải thích\n\nPhân tích phần dư mô hình cuối được dùng cho cả KT2/KT3; các lỗi này chỉ được mô tả sau khi lựa chọn đã khóa. Nhóm nhà giá cao có MAE USD lớn hơn; sai số tuyệt đối tăng theo thang giá là lý do cần báo cáo cả log và USD.'),
code("figure('11_predictions_residuals.png')\ndisplay(table('errors_by_price_band.csv'))\ndisplay(table('largest_errors.csv').head(8))"),
md('## 6 Thực hành cá nhân\n\nThử một thay đổi trên CV, không đụng test: đổi alpha, đổi chỉ số sang MAE, hoặc thay Ridge bằng Lasso. Ô dưới chỉ chạy một fold với dữ liệu train, dùng để thực hành tại chỗ.'),
code("from sklearn.base import clone\nfrom src.experiments import metrics\nfrom src.modeling import predict_nonnegative\na,b=temporal_folds(train)[0]\ndemo=make_model(train,Ridge(alpha=30))\ndemo.fit(train.iloc[a],train.iloc[a].SalePrice)\nprint(metrics(train.iloc[b].SalePrice,predict_nonnegative(demo,train.iloc[b])))"),
md('Đọc `docs/ON_TAP_KT2_KT3.md` để giải thích hàm mục tiêu, tham số và các cột kết quả. AI hỗ trợ xây dựng mã/tài liệu; sinh viên tự kiểm tra, hiểu và ghi nhận phần việc thực tế trước khi nộp.')])

build('03_KT3_Tuning_Improvement.ipynb',[
md('# Bài kiểm tra 3 · Tối ưu và so sánh cải tiến\n\nKhông giả định cải tiến bắt buộc tốt hơn. Khóa lựa chọn bằng CV trước khi chấm test. Xem `selection_frozen_before_test.json` và hash trong `results.json`.'),code(setup),
md('## 1 Hạn chế ban đầu và giải pháp\n\nĐa cộng tuyến và khoảng cách train–CV dẫn đến tìm alpha. Đuôi diện tích và lỗi nhóm giá cao dẫn đến so sánh clipping/log. Quan hệ phi tuyến dẫn đến thử boosting. Thêm tuổi nhà, tổng diện tích, tổng số phòng tắm và cờ tiện ích để kiểm tra tín hiệu tổng hợp; không coi đó là cải tiến đã có hiệu quả trước khi đo.'),
code("from src.modeling import FeatureBuilder\nfrom src.preprocessing import load_raw\nraw=load_raw(ROOT/'data/raw/AmesHousing.tsv')\ntrain=raw[raw['Yr Sold']<2010].reset_index(drop=True)\ndisplay(FeatureBuilder(engineered=True).fit_transform(train).filter(items=['HouseAge','RemodAge','TotalSF','TotalBath','HasGarage','HasBasement','TotalPorch']).head())"),
md('## 2 Ablation cùng alpha Ridge\n\nAlpha Ridge được chọn trên cấu hình gốc, sau đó giữ nguyên alpha khi đo lần lượt thêm đặc trưng, bỏ clipping và log diện tích. Các dòng dùng cùng fold, nhãn và chỉ số. Đây là tác động của thay đổi trong cấu hình alpha cố định, không phải bằng chứng mọi khả năng feature engineering đều không hiệu quả.'),
code("display(table('ablation.csv'))\nfigure('12_ablation.png')"),
md('Các biến tổng hợp chưa giảm RMSE log; bỏ clipping làm kết quả kém ổn định hơn. Log diện tích phục hồi phần lớn chất lượng so với không clip, nhưng vẫn chưa vượt cấu hình gốc. Giữ cấu hình gốc theo CV, không sửa quyết định dựa trên test.'),
md('## 3 Tìm kiếm siêu tham số\n\nGridSearchCV fit lại toàn bộ pipeline theo fold năm. Ridge tìm alpha 0.1–1000; Lasso 0.0001–0.03; Elastic Net kết hợp alpha và l1_ratio; HistGradientBoosting thử số lá tối đa và phạt L2, early_stopping=False để không trộn một tập kiểm định ngẫu nhiên vào quy trình thời gian.'),
code("print(json.dumps(result['best_params'],indent=2))\ndisplay(table('kt3_cv_summary.csv'))\nfigure('10_kt3_cv.png')\nfigure('13_alpha_validation.png')"),
md('## 4 RidgeCV và LassoCV không rò rỉ preprocessing\n\nVí dụ bổ sung đóng băng imputer/scaler/encoder bằng dữ liệu năm 2006 trước mọi validation. Do đó, các lớp RidgeCV/LassoCV không nhìn thống kê tương lai. Đây là thí nghiệm khác preprocessing với bảng chính; không dùng để khẳng định khác biệt chỉ do thuật toán CV. Bảng chính vẫn dùng refit toàn pipeline trong mỗi fold.'),
code("print((DATA/'ridgecv_lassocv.json').read_text(encoding='utf-8'))"),
md('## 5 Độ thưa và giải thích mô hình\n\nLasso tạo nhiều hệ số 0 hơn Ridge. Hệ số sau chuẩn hóa không phải tác động nhân quả và độ lớn số so với biến one-hot chưa scale không hoàn toàn tương đương. Dùng permutation importance trên validation 2009 để bổ sung bằng chứng.'),
code("display(table('sparsity.csv'))\nfigure('15_permutation_importance.png')\nfigure('14_learning_curve.png')"),
md('Khi tăng dữ liệu quá khứ trước validation 2009, sai số validation giảm; đường train và validation tiến gần hơn. Kết quả chỉ có ba kích thước và cùng một năm validation, không phải bảo đảm cho mọi thời kỳ. Diện tích ở, chất lượng, tầng hầm và năm xây dựng có vai trò lớn theo phép hoán vị, nhưng đặc trưng tương quan có thể chia sẻ tầm quan trọng.'),
md('## 6 Lựa chọn cuối và đánh giá test\n\nLasso alpha=0.0003 thắng theo CV và được giữ nguyên. Một số cấu hình khác có test RMSE log thấp hơn đôi chút; không chọn lại vì điều đó sẽ biến test thành tập chọn mô hình. Mức cải thiện so với cấu hình KT2 tốt nhất nhỏ hơn độ lệch chuẩn giữa fold, nên không tuyên bố ưu thế thống kê chắc chắn.'),
code("print('Selected:',result['selected_model'])\nprint('CV:',result['selected_cv'])\nprint('Test:',result['test_metrics'])\ndisplay(table('cv_vs_test.csv'))\nfigure('11_predictions_residuals.png')"),
md('## 7 Thực hành và hạn chế\n\nXem ô thực hành của KT2 để đổi alpha trong train fold. Xem `src/experiments.py` để đổi lưới và chạy lại một phiên bản thực nghiệm, không tuyên bố test mới độc lập sau khi đã nhìn nhiều phiên bản. Giới hạn: ba năm validation, test 2010 một phần năm, miền Ames lịch sử, cấu hình cải tiến hữu hạn và CV có độ lạc quan do tìm kiếm. Phần cá nhân và lịch sử đóng góp cần sinh viên bổ sung thật.')])
