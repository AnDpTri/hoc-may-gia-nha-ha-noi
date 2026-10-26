"""Tạo báo cáo tổng hợp LaTeX KT1–KT3 từ CSV/JSON kết quả thực nghiệm."""
from pathlib import Path
import json
import shutil
import zipfile
import pandas as pd
from build_latex import escape

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'reports/experiments'; DEST=ROOT/'reports/latex_full'

def run():
    DEST.mkdir(parents=True,exist_ok=True); (DEST/'images').mkdir(exist_ok=True)
    for f in (ROOT/'reports/figures').glob('*.png'):
        if f.name!='08_equations.png':shutil.copy2(f,DEST/'images'/f.name)
    r=json.loads((DATA/'results.json').read_text(encoding='utf-8'))
    cv2=pd.read_csv(DATA/'kt2_cv_summary.csv'); cv3=pd.read_csv(DATA/'kt3_cv_summary.csv')
    test=pd.read_csv(DATA/'final_test_comparison.csv')
    base=(ROOT/'reports/latex/main.tex').read_text(encoding='utf-8')
    base=base.replace('BÁO CÁO BÀI KIỂM TRA 1','BÁO CÁO DỰ ÁN HỌC MÁY',1)
    base=base.replace('Học phần Học máy\\par','Học phần Học máy\\par Bài kiểm tra 1, 2 và 3\\par',1)
    start=base.index(r'\textbf{Tóm tắt}')+len(r'\textbf{Tóm tắt}')
    end=base.index(r'\end{flushleft}',start)
    abstract=f'''Dự án khảo sát và dự đoán giá nhà Ames từ 2.930 giao dịch lịch sử. KT1 xây dựng
bộ dữ liệu và pipeline; KT2 so sánh baseline, OLS, Ridge, Lasso và Elastic Net;
KT3 đo tác động của đặc trưng mới, clipping, log diện tích và tối ưu siêu tham số,
đồng thời thử HistGradientBoosting. Mọi lựa chọn dựa trên ba fold thời gian
trong train 2006–2009; test 2010 được giữ để chấm sau khi khóa cấu hình.

Lasso alpha=0.0003 được chọn theo CV. RMSE log CV là {r['selected_cv']['cv_rmse_log_mean']:.4f},
test là {r['test_metrics']['rmse_log']:.4f}; MAE test {r['test_metrics']['mae_usd']:,.0f} USD,
R² test {r['test_metrics']['r2_usd']:.4f}. So với baseline, RMSE log test giảm
{r['test_rmse_log_improvement_vs_dummy_pct']:.2f}%. Một số thử nghiệm cải tiến không tốt hơn
cấu hình gốc; báo cáo giữ nguyên kết quả và phân tích giới hạn. Mức cải thiện
CV giữa các mô hình chính quy hóa rất nhỏ so với biến động giữa năm.

Bộ nộp gồm dữ liệu, ba notebook đã chạy, mã nguồn, mô hình đã lưu, demo CLI,
báo cáo và bộ nguồn LaTeX độc lập. Phần KT1 dưới đây ghi nhận trạng thái ở mốc
đầu; các mục KT2 và KT3 bổ sung kết quả thực nghiệm hoàn chỉnh.
'''
    base=base[:start]+'\n\n'+escape(abstract)+'\n\n'+base[end:]
    base=base.rsplit(r'\end{document}',1)[0]
    out=[base]
    def section(title):out.append(r'\clearpage\section{'+escape(title)+'}')
    def sub(title):out.append(r'\subsection{'+escape(title)+'}')
    def p(text):out.append(escape(text)+'\n')
    def fig(name,caption,width='.94'):
        out.append(r'\begin{figure}[H]\centering\includegraphics[width='+width+r'\linewidth]{'+name+r'}\caption{'+escape(caption)+r'}\end{figure}')
    def table(df,headings=None):
        df=df.copy()
        if headings:df.columns=headings
        n=len(df.columns)
        fmt='Y'+'r'*(n-1)
        out.append(r'\begingroup\small\setlength{\tabcolsep}{4pt}\begin{tabularx}{\linewidth}{@{}'+fmt+r'@{}}\toprule')
        out.append(' & '.join(r'\textbf{'+escape(str(x))+'}' for x in df.columns)+r'\\\midrule')
        for row in df.itertuples(index=False,name=None):
            cells=[]
            for v in row:
                value=f'{v:.4f}' if isinstance(v,float) else str(v)
                cells.append(escape(value))
            out.append(' & '.join(cells)+r'\\')
        out.append(r'\bottomrule\end{tabularx}\endgroup\par')
    section('Bài kiểm tra 2 Quy trình huấn luyện')
    sub('Thuật toán và cấu hình ban đầu')
    p('Baseline DummyMeanLog dự đoán trung bình log giá học từ từng train fold. OLS là hồi quy tuyến tính không phạt. Ridge dùng alpha=10; Lasso dùng alpha=0.001; Elastic Net dùng alpha=0.001 và l1_ratio=0.5. Các cấu hình này được xác định trước tìm kiếm KT3. Không chọn cấu hình theo năm 2010.')
    p('Các mô hình tuyến tính phù hợp với dữ liệu bảng, dễ khảo sát hệ số và thể hiện trực tiếp vai trò của L1/L2. Dữ liệu có các nhóm diện tích và garage tương quan mạnh nên chính quy hóa là một lựa chọn có cơ sở. Baseline cần thiết để biết mô hình có học được thông tin vượt dự đoán hằng số hay không.')
    sub('Quy trình thống nhất')
    p('TransformedTargetRegressor bao một Pipeline gồm FeatureBuilder, preprocessing và estimator. Pipeline nhận DataFrame raw, tự bỏ nhãn và định danh, làm sạch, clip, điền thiếu, scale và one-hot. Biến đổi mục tiêu là log1p, hoàn nguyên bằng expm1; đầu ra khi đánh giá được chặn không âm. Mọi fold đều clone và fit toàn bộ quy trình. Bộ ma trận đã chuẩn hóa ở KT1 không được tái sử dụng để tính CV.')
    p('Ba fold dùng các năm kiểm định 2007, 2008 và 2009. Giá trị mean lấy trung bình không trọng số giữa ba năm; std trong các bảng so sánh là độ lệch chuẩn mẫu, ddof=1. Khoảng mean ± std không phải khoảng tin cậy 95%. Các bảng grid của sklearn dùng std quần thể, ddof=0; biểu đồ alpha ghi rõ khác biệt này.')
    p('Mã nằm ở src/modeling.py và src/experiments.py. random_state=42 được dùng cho các thuật toán có ngẫu nhiên. Các phép chia theo năm là tất định. Chạy lại toàn bộ bằng python -m src.run_all; mô hình cuối nhận raw nên demo không cần tự chuẩn hóa dữ liệu.')
    section('Bài kiểm tra 2 Kết quả và nhận diện quá khớp')
    table(cv2[['model','cv_train_rmse_log_mean','cv_rmse_log_mean','cv_rmse_log_std']],['Mô hình','Train log','CV log','Std'])
    fig('09_kt2_cv.png','So sánh các mô hình KT2 theo ba fold thời gian')
    ols=cv2.set_index('model').loc['LinearRegression']; en=cv2.set_index('model').loc['ElasticNet_default']
    p(f'OLS có RMSE log train trung bình {ols.cv_train_rmse_log_mean:.4f} và validation {ols.cv_rmse_log_mean:.4f}, cho thấy khoảng cách khớp đáng kể. Chính quy hóa làm giảm khoảng cách và giảm lỗi validation. Elastic Net ban đầu đạt CV {en.cv_rmse_log_mean:.4f}; chênh lệch với Ridge nhỏ hơn nhiều biến động giữa fold, vì vậy chưa có bằng chứng ưu thế chắc chắn.')
    p('Không kết luận quá khớp chỉ từ một giá trị train nhỏ. Bằng chứng ở đây kết hợp chênh lệch train–validation, độ ổn định theo năm và phân tích phần dư. Tất cả thuật toán đều dùng cùng nhãn, cùng hold-out và cùng chiến lược xử lý thiếu.')
    section('Bài kiểm tra 3 Cải tiến dữ liệu và ablation')
    p('Từ hạn chế của KT2, dự án thử ba hướng: bổ sung đặc trưng để mô tả quan hệ tổng hợp; thay đổi xử lý đuôi diện tích để giảm tác động điểm có đòn bẩy; tối ưu chính quy hóa và thử boosting để mô tả quan hệ phi tuyến. Mỗi hướng được gắn với một vấn đề quan sát được, không giả định trước sẽ làm tăng chất lượng.')
    p('Các đặc trưng mới gồm HouseAge, RemodAge, TotalSF, TotalBath, HasGarage, HasBasement và TotalPorch. Chúng chỉ tính từ đầu vào, không dùng giá. TotalSF bằng tổng tầng hầm và diện tích tầng 1, tầng 2; TotalBath có trọng số 0.5 cho half bath. Log diện tích dùng log1p sau khi chặn giá trị âm về 0, là biến đổi cố định không học nhãn.')
    ab=pd.read_csv(DATA/'ablation.csv')
    names=['Gốc có clip','Thêm đặc trưng có clip','Thêm đặc trưng bỏ clip','Thêm đặc trưng log bỏ clip']
    ab['Thử nghiệm']=names
    table(ab[['Thử nghiệm','cv_rmse_log_mean','cv_rmse_log_std']],['Thử nghiệm','CV log','Std'])
    fig('12_ablation.png','Ablation Ridge với cùng alpha và cùng các fold thời gian',width='.88')
    p('Alpha Ridge được chọn trên cấu hình gốc rồi giữ cố định ở bốn hàng để tách tác động của biến đổi dữ liệu. Thêm đặc trưng chưa vượt cấu hình gốc; bỏ clipping tăng lỗi và độ biến động. Log diện tích phục hồi phần lớn chất lượng nhưng chưa vượt gốc. Vì vậy cấu hình cuối giữ các biến ban đầu và clipping. Kết quả không chứng minh mọi cách tạo đặc trưng đều kém, vì thử nghiệm chỉ bao phủ tập biến đổi hữu hạn.')
    section('Bài kiểm tra 3 Tìm kiếm siêu tham số')
    p('GridSearchCV tìm kiếm bằng RMSE log trên ba fold thời gian. Mỗi ứng viên fit lại FeatureBuilder, imputer, scaler và encoder trong fold. Các bảng grid lưu mọi ứng viên, thứ hạng, lỗi train/validation và thời gian; không chỉ lưu cấu hình thắng. Không có tham số nào được sửa sau khi nhìn kết quả test.')
    p('Lưới Ridge: alpha thuộc 0.1, 1, 3, 10, 30, 100, 300, 1000. Lasso: alpha thuộc 0.0001, 0.0003, 0.001, 0.003, 0.01, 0.03. Elastic Net: alpha thuộc 0.0003, 0.001, 0.003, 0.01 và l1_ratio thuộc 0.1, 0.5, 0.9. Lasso và Elastic Net dùng max_iter=50000, tol=1e-5.')
    p('Thuật toán mới HistGradientBoosting xây các cây liên tiếp để sửa sai số của tổng mô hình trước đó, học tương tác và phi tuyến. Cấu hình có max_iter=250, learning_rate=0.05; tìm max_leaf_nodes trong 15,31 và l2_regularization trong 1,10. early_stopping=False để tránh thêm một validation ngẫu nhiên vào thiết kế thời gian. Thuật toán cây là đối chứng, không thay thế nhiệm vụ nghiên cứu mô hình tuyến tính của đề tài.')
    for name,params in r['best_params'].items():p(name+': '+', '.join(f'{k}={v}' for k,v in params.items()))
    fig('13_alpha_validation.png','Ảnh hưởng của alpha Ridge trên lỗi kiểm định',width='.88')
    p('Alpha quá nhỏ ít hạn chế đa cộng tuyến; quá lớn làm tăng độ chệch. Điểm tốt nhất chỉ là tốt nhất trong lưới đã thử. Chọn preprocessing trước rồi tối ưu thuật toán trên cùng các fold tạo độ lạc quan do tìm kiếm; test giữ lại là bằng chứng tổng quát hóa bổ sung.')
    section('Bài kiểm tra 3 Kết quả CV và ví dụ RidgeCV LassoCV')
    table(cv3[['model','cv_rmse_log_mean','cv_rmse_log_std','cv_mae_usd_mean']],['Mô hình','CV log','Std','MAE USD'])
    fig('10_kt3_cv.png','Các thuật toán sau tối ưu trên cùng cấu hình dữ liệu',width='.9')
    p('Lasso có lỗi CV trung bình nhỏ nhất trong tập ứng viên, nhưng mức chênh lệch giữa các mô hình chính quy hóa rất nhỏ so với std giữa năm. Boosting không vượt các mô hình tuyến tính chính quy hóa trong thiết kế này. Không suy rộng kết luận đó sang các lưới, đặc trưng hoặc bộ dữ liệu khác.')
    sub('Đáp ứng yêu cầu RidgeCV và LassoCV')
    q=r['supplementary_cv']
    p(f'Ví dụ bổ sung dùng đúng RidgeCV và LassoCV, nhưng preprocessing được fit và đóng băng bằng {q["calibration_rows"]} mẫu năm 2006 trước mọi fold validation. Cách này tránh để imputer/scaler nhìn dữ liệu năm 2007–2009. RidgeCV chọn alpha={q["ridgecv_alpha"]:g}; LassoCV chọn alpha={q["lassocv_alpha"]:g}. Kết quả khác Ridge grid chính là hợp lý vì chiến lược preprocessing và mục tiêu gộp fold không hoàn toàn giống nhau.')
    p('Đặt một RidgeCV/LassoCV vào sau preprocessing đã fit trên toàn bộ train sẽ làm các fold nội bộ nhìn thống kê validation. Vì vậy ví dụ lớp CV được trình bày riêng, còn bảng chính dùng refit toàn pipeline. Không trộn hai bảng thành một so sánh chỉ khác thuật toán lựa chọn alpha.')
    section('Lựa chọn cuối và đánh giá độc lập')
    p(f'Mô hình được khóa trước chấm test là {r["selected_model"]}, alpha=0.0003. RMSE log CV trung bình {r["selected_cv"]["cv_rmse_log_mean"]:.4f} ± {r["selected_cv"]["cv_rmse_log_std"]:.4f}. RMSE log test năm 2010 là {r["test_metrics"]["rmse_log"]:.4f}; MAE {r["test_metrics"]["mae_usd"]:,.2f} USD; RMSE {r["test_metrics"]["rmse_usd"]:,.2f} USD; R² {r["test_metrics"]["r2_usd"]:.4f}.')
    table(test[['model','rmse_log','mae_usd','r2_usd']],['Mô hình','Test log','MAE USD','R²'])
    p(f'So với DummyMeanLog, RMSE log test giảm {r["test_rmse_log_improvement_vs_dummy_pct"]:.2f}%. Mục tiêu KT1 là RMSE log ≤ 0.18 và giảm ít nhất 10% so với baseline được đáp ứng. Tuy nhiên, cải thiện CV so với Elastic Net KT2 chỉ khoảng {(en.cv_rmse_log_mean-r["selected_cv"]["cv_rmse_log_mean"])/en.cv_rmse_log_mean*100:.2f}%, chưa đủ để tuyên bố ưu thế thống kê chắc chắn.')
    p('Một số cấu hình có test RMSE log thấp hơn Lasso đôi chút. Dự án vẫn giữ lựa chọn theo CV; chọn lại theo bảng test sẽ làm mất ý nghĩa đánh giá cuối. File selection_frozen_before_test.json được ghi trước bước chấm, có hash trong results.json. Hash là kiểm tra tính nhất quán tệp, không phải chứng thực độc lập về lịch sử thời gian.')
    fig('16_cv_vs_test.png','So sánh CV và test cho các cấu hình đã khóa',width='.92')
    section('Phân tích lỗi và giới hạn dự đoán')
    fig('11_predictions_residuals.png','Giá dự đoán và phần dư của Lasso trên test năm 2010')
    groups=pd.read_csv(DATA/'errors_by_price_band.csv')
    table(groups,['Nhóm giá','Số mẫu','MAE USD','MAE log'])
    p('Nhóm giá trên 250.000 USD có MAE USD lớn hơn rõ rệt, nhưng sai số log không lớn nhất. Điều này cho thấy cần tách ý nghĩa sai số tiền và sai số theo tỷ lệ. Phần dư dương ở một số căn đắt tiền thể hiện dự đoán thấp hơn giá thực. Không chỉnh đặc trưng hoặc tham số để sửa riêng các mẫu test này trong cùng báo cáo.')
    largest=pd.read_csv(DATA/'largest_errors.csv').head(3)
    table(largest[['Order','SalePrice','prediction_usd','absolute_error_usd']],['Order','Thực USD','Dự đoán USD','Lỗi tuyệt đối'])
    p('Ba mẫu lỗi lớn ở trên là minh chứng để mô tả hạn chế, không phải căn cứ xóa dữ liệu test. Mô hình dự báo giá trung bình theo cấu trúc đã học và không nắm hết chất lượng nội thất, thương lượng, tình trạng thị trường hoặc tiện ích hiếm. Giá được học trên thang log nên hoàn nguyên không bảo đảm dự đoán trung bình USD không chệch.')
    section('Giải thích mô hình và độ ổn định')
    sparse=pd.read_csv(DATA/'sparsity.csv')
    table(sparse,['Mô hình','Số hệ số','Khác 0'])
    p('Ngưỡng đếm hệ số khác 0 là 1e-8. Lasso có nghiệm thưa hơn Ridge, phù hợp vai trò phạt L1. Các cột gồm biến số đã scale, one-hot và cờ thiếu; không diễn giải độ lớn hệ số như tác động nhân quả. Việc một mức phân loại có hệ số 0 không đồng nghĩa yếu tố đó hoàn toàn không liên quan giá.')
    fig('15_permutation_importance.png','Tầm quan trọng hoán vị trên validation năm 2009',width='.9')
    p('Diện tích ở, chất lượng tổng thể, tầng hầm và năm xây dựng nổi bật. Phép hoán vị dùng mô hình học 2006–2008 và nhãn 2009, không dùng test. Mỗi biến được hoán vị ba lần; thanh sai số thể hiện độ biến động của phép hoán vị, không phải bất định tổng quát của mô hình. Các biến tương quan có thể chia sẻ hoặc che bớt tầm quan trọng của nhau.')
    section('Đường cong học tập và hướng phát triển')
    fig('14_learning_curve.png','Thêm dữ liệu quá khứ trước năm validation 2009',width='.92')
    learn=pd.read_csv(DATA/'learning_curve.csv')
    table(learn[['n_train','train_rmse_log','validation_2009_rmse_log']],['Mẫu học','Train log','Validation log'])
    p('Khi thêm các năm quá khứ, lỗi validation 2009 giảm và khoảng cách với train thu hẹp. Ba điểm cùng một năm validation chỉ cung cấp bằng chứng cục bộ, không bảo đảm tăng dữ liệu luôn làm chất lượng tốt hơn. Đường cong giữ nguyên siêu tham số đã chọn; validation 2009 đã tham gia tìm kiếm nên đây là phân tích phát triển, không là đánh giá ngoài mẫu mới.')
    p('Hướng phát triển gồm mở rộng dữ liệu theo thời gian, xác minh thời điểm thu thập đánh giá chất lượng, mô hình hóa nhóm nhà giá cao và thử mã hóa thứ bậc có kiểm soát. Muốn đánh giá các thay đổi sau báo cáo này cần một giai đoạn dữ liệu mới chưa được nhìn, thay vì tiếp tục dùng lại test 2010 như một test độc lập.')
    section('Tái lập dự án và trình diễn')
    p('Python 3.11 và requirements.txt khóa môi trường thực chạy. Ba notebook đã lưu kết quả: 01_KT1_Ames_Housing.ipynb, 02_KT2_Train_Evaluate.ipynb và 03_KT3_Tuning_Improvement.ipynb. Các lệnh dưới chạy từ gốc repo; dữ liệu raw đi kèm nên việc huấn luyện không cần mạng. Biên dịch LaTeX lần đầu có thể cần tải gói nếu máy chưa có TeX.')
    out.append(r'''\begin{verbatim}
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe -m src.run_all
.venv\Scripts\python.exe -m src.predict --example
.venv\Scripts\python.exe -m unittest discover -s tests -v
\end{verbatim}''')
    p('Mô hình trong models/final_model.joblib bao toàn bộ preprocessing và biến đổi nhãn. CLI nhận --input với CSV/JSON đủ các cột đặc trưng và --output để lưu giá dự đoán USD. Không cần tự one-hot hoặc chuẩn hóa. README giải thích cấu trúc thư mục, ý nghĩa các tệp kết quả và cách biên dịch báo cáo.')
    p('Các kiểm tra tự động bao gồm thứ tự và không giao nhau của fold; loại nhãn/ID khỏi đặc trưng; dự đoán raw có mức khu vực chưa gặp; scaler chỉ học số dòng train; xử lý thiếu/NA; log round-trip; và hash tệp lựa chọn. Notebook không tự chấm lại test mỗi khi mở. Kết quả có thể sai khác nhỏ do BLAS/hệ điều hành; thời gian chạy không cố định.')
    section('Đối chiếu tiêu chí Bài kiểm tra 2')
    criteria2=[('1 Thuật toán phù hợp','OLS, Ridge, Lasso, Elastic Net và baseline'),('2 Baseline','DummyMeanLog, bảng CV và test'),('3 Quy trình','Pipeline và TransformedTargetRegressor'),('4 Mã nguồn chạy được','src/run_all.py, requirements, ba notebook'),('5 Huấn luyện và kiểm thử','Ba fold theo năm, test khóa riêng'),('6 Chỉ số và công cụ bổ trợ','RMSE log, MAE/RMSE USD, R², phần dư'),('7 Phân tích lỗi','Theo nhóm giá và các mẫu lỗi lớn'),('8 Nguyên lý cá nhân','Hàm mục tiêu L1/L2/Elastic Net, tài liệu ôn'),('9 Giải thích dữ liệu dự án','Sparsity, permutation importance, đa cộng tuyến'),('10 Thực hành cá nhân','Đổi alpha hoặc chỉ số trong notebook KT2')]
    # Hai cột văn bản cần cùng kiểu Y để tự ngắt dòng.
    out.append(r'\begingroup\small\begin{tabularx}{\linewidth}{YY}\toprule\textbf{Tiêu chí}&\textbf{Minh chứng}\\\midrule')
    out.extend(escape(a)+' & '+escape(b)+r'\\' for a,b in criteria2)
    out.append(r'\bottomrule\end{tabularx}\endgroup')
    p('Các tiêu chí cá nhân cần sinh viên giải thích và thao tác thật trước giảng viên. Bộ mã và tài liệu không thay thế đánh giá vấn đáp. Các tiêu chí nhóm cũng có thể được hỏi lại trên chính dữ liệu này.')
    section('Đối chiếu tiêu chí Bài kiểm tra 3 và khai báo đóng góp')
    criteria3=[('1 Hạn chế ban đầu','Khoảng cách train–CV, đuôi giá và đa cộng tuyến'),('2 Giải pháp cải tiến','Đặc trưng mới, clip/log, tuning, boosting'),('3 Dữ liệu và đặc trưng','Bảy đặc trưng mới và ablation cùng alpha'),('4 Thuật toán hoặc cấu hình khác','HistGradientBoosting và cấu hình tuyến tính mới'),('5 Tối ưu siêu tham số','GridSearchCV, lưới và mọi ứng viên đã lưu'),('6 So sánh trước sau','Cùng dữ liệu, fold, chỉ số; ablation riêng'),('7 Tổng quát hóa','Test 2010 sau khóa lựa chọn; mean/std CV'),('8 Trực quan thực nghiệm','Biểu đồ CV, alpha, learning, phần dư'),('9 Lựa chọn mô hình cá nhân','Lasso theo CV, không chọn lại theo test'),('10 Thực hành cá nhân','Đổi khoảng alpha, xem lại đường cong validation')]
    out.append(r'\begingroup\small\begin{tabularx}{\linewidth}{YY}\toprule\textbf{Tiêu chí}&\textbf{Minh chứng}\\\midrule')
    out.extend(escape(a)+' & '+escape(b)+r'\\' for a,b in criteria3)
    out.append(r'\bottomrule\end{tabularx}\endgroup')
    p('Codex AI hỗ trợ tìm dữ liệu, triển khai pipeline, chạy thực nghiệm và soạn tài liệu cho cả ba mốc. Không tạo lịch sử đóng góp giả trong nhiều tuần; nhật ký ghi đúng thời điểm chuẩn bị. Sinh viên cần bổ sung họ tên, MSSV, lớp, giảng viên, phân công và những lần tự kiểm tra/sửa thật. Mẫu bìa của bộ môn chưa được cung cấp nên phần thông tin để trống.')
    p('Tài liệu phương pháp bổ sung: HistGradientBoostingRegressor, RidgeCV và LassoCV trong tài liệu chính thức scikit-learn: https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.HistGradientBoostingRegressor.html ; https://scikit-learn.org/stable/modules/generated/sklearn.linear_model.RidgeCV.html ; https://scikit-learn.org/stable/modules/generated/sklearn.linear_model.LassoCV.html . Các nguồn dữ liệu và lý thuyết đã được liệt kê trong phần KT1.')
    out.append(r'\end{document}')
    (DEST/'main.tex').write_text('\n\n'.join(out),encoding='utf-8')
    (DEST/'README.md').write_text('''# Báo cáo tổng hợp KT1 KT2 KT3

Mở main.tex; biên dịch bằng pdfLaTeX hoặc XeLaTeX hai lần để có mục lục.
Nguồn và images/ độc lập với đường dẫn máy. Trên Overleaf chọn Upload project
và tải ZIP Bao_cao_KT1_KT2_KT3_LaTeX.zip. Thông tin sinh viên ở đầu main.tex.

Số liệu được sinh từ reports/experiments của repo. Công thức toán là LaTeX gốc.
''',encoding='utf-8')
    target=ROOT/'reports/Bao_cao_KT1_KT2_KT3_LaTeX.zip'
    with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED) as z:
        for f in sorted(DEST.rglob('*')):
            if f.is_file() and f.suffix in ['.tex','.png','.md']:z.write(f,f.relative_to(DEST).as_posix())
    print(target)

if __name__=='__main__':run()
