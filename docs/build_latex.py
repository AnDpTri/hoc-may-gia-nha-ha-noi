"""Chuyển báo cáo đã xác minh sang dự án LaTeX độc lập, sẵn sàng cho Overleaf."""
from pathlib import Path
import re
import shutil
import zipfile

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / 'reports/latex'

def escape(s):
    replacements = {'\\':r'\textbackslash{}', '&':r'\&', '%':r'\%', '$':r'\$',
                    '#':r'\#', '_':r'\_', '{':r'\{', '}':r'\}', '~':r'\textasciitilde{}',
                    '^':r'\textasciicircum{}', 'α':r'\ensuremath{\alpha}',
                    'ρ':r'\ensuremath{\rho}', '≤':r'\ensuremath{\leq}', '≥':r'\ensuremath{\geq}',
                    '−':r'\ensuremath{-}', '×':r'\ensuremath{\times}', '²':r'\textsuperscript{2}',
                    'ᵀ':r'\textsuperscript{T}', 'ⱼ':r'\textsubscript{j}', 'ŷ':r'\ensuremath{\hat{y}}',
                    '’':"'"}
    # URL được đưa vào url để có thể ngắt dòng; không escape toàn bộ lệnh.
    parts = re.split(r'(https?://\S+|[\w./]+\.(?:csv|npz|py|md|json|txt|ipynb|joblib))', s)
    return ''.join(r'\url{'+p.rstrip('.')+'}'+('.' if p.endswith('.') else '')
                   if p.startswith(('http://','https://')) else
                   r'\path{'+p+'}' if re.fullmatch(r'[\w./]+\.(?:csv|npz|py|md|json|txt|ipynb|joblib)',p) else
                   ''.join(replacements.get(c,c) for c in p) for p in parts)

PREAMBLE = r'''% !TeX program = pdflatex
% Báo cáo KT1 Ames Housing. Biên dịch pdfLaTeX hai lần.
\documentclass[12pt,a4paper]{article}
\usepackage{iftex}
\ifPDFTeX
\usepackage[T5]{fontenc}
\usepackage[utf8]{inputenc}
\usepackage{lmodern}
\else
\usepackage{fontspec}
\setmainfont{lmroman10-regular.otf}[BoldFont=lmroman10-bold.otf,ItalicFont=lmroman10-italic.otf,BoldItalicFont=lmroman10-bolditalic.otf]
\fi
\usepackage[vietnamese]{babel}
\usepackage[margin=2cm,headheight=15pt]{geometry}
\usepackage{amsmath,amssymb,bm}
\usepackage{graphicx,booktabs,tabularx,array,float,caption}
\usepackage{setspace,microtype,xurl}
\usepackage[unicode,hidelinks,pdftitle={Báo cáo KT1 Dự đoán giá nhà Ames},pdfauthor={Sinh viên bổ sung thông tin}]{hyperref}
\graphicspath{{images/}}
\setstretch{1.09}
\setlength{\parindent}{0pt}
\setlength{\parskip}{6pt}
\setlength{\emergencystretch}{2em}
\renewcommand{\arraystretch}{1.17}
\captionsetup{font=small,labelfont=bf,skip=5pt}
\newcolumntype{Y}{>{\raggedright\arraybackslash}X}
\newcommand{\R}{\mathbb{R}}
\hypersetup{pageanchor=false}
\begin{document}
\begin{titlepage}
\centering
{\LARGE\bfseries BÁO CÁO BÀI KIỂM TRA 1\par}
\vspace{0.6cm}
{\Large\bfseries Dự đoán giá bất động sản\\dựa trên đặc điểm nhà ở\par}
\vspace{0.5cm}
{\large Học phần Học máy\par}
{\large Học kỳ 1 năm học 2026--2027\par}
\vspace{0.9cm}
\begin{tabular}{ll}
Sinh viên: & \makebox[9cm]{\dotfill}\\[0.3cm]
Mã sinh viên: & \dotfill\\[0.3cm]
Lớp: & \dotfill\\[0.3cm]
Giảng viên: & \dotfill
\end{tabular}
\vspace{0.7cm}
\par Ngày 26 tháng 10 năm 2026
\vspace{0.7cm}
\begin{flushleft}
\textbf{Tóm tắt}
'''

MATH = r'''
\begin{equation}
J(w,b)=\frac{1}{2n}\lVert z-b\bm 1-Xw\rVert_2^2
+\alpha\left[\rho\lVert w\rVert_1+\frac{1-\rho}{2}\lVert w\rVert_2^2\right].
\label{eq:elastic}
\end{equation}
\begin{equation}
\widehat{w}_{\mathrm{L2}}=
\left(\frac{X^{\mathsf T}X}{n}+\alpha I\right)^{-1}
\frac{X^{\mathsf T}z}{n}.
\label{eq:ridge}
\end{equation}
'''

METRICS = r'''
\begin{align}
\mathrm{RMSE}_{\log}&=\sqrt{\frac{1}{m}\sum_{i=1}^{m}
 \left[\ln(1+y_i)-\ln(1+\widehat y_i)\right]^2},\\
\mathrm{MAE}_{\mathrm{USD}}&=\frac{1}{m}\sum_{i=1}^{m}|y_i-\widehat y_i|.
\end{align}
Với dự đoán không âm, RMSE log tương đương RMSLE. Chỉ số nhấn mạnh sai số
tương đối trong phạm vi giá rộng; không thể chuyển trực tiếp 0,18 thành một
tỷ lệ lỗi cố định cho mọi căn nhà. MAE có đơn vị USD, dễ diễn giải.
RMSE USD nhạy hơn với sai số lớn. $R^2$ so với phương án dự đoán trung bình
trên tập đang đánh giá.
'''

def build():
    DEST.mkdir(parents=True, exist_ok=True)
    (DEST/'images').mkdir(exist_ok=True)
    for f in (ROOT/'reports/figures').glob('*.png'):
        if f.name != '08_equations.png': shutil.copy2(f, DEST/'images'/f.name)
    lines=(ROOT/'reports/Bao_cao_KT1.md').read_text(encoding='utf-8').splitlines()
    start=lines.index('## Tóm tắt')+1
    i=start; out=[PREAMBLE]; cover=True; first_section=True
    while i<len(lines):
        line=lines[i].strip(); i+=1
        if not line: continue
        line=line.replace('DOI: 10.1080/10691898.2011.11889627.',
                          'DOI: https://doi.org/10.1080/10691898.2011.11889627.')
        if line=='<!-- PAGE -->':
            if cover:
                out.append(r'\end{flushleft}\end{titlepage}'+'\n'+r'\hypersetup{pageanchor=true}\tableofcontents\clearpage')
                cover=False
            elif not first_section: out.append(r'\clearpage')
            continue
        if line.startswith('# '):
            title=re.sub(r'^\d+\s+', '', line[2:])
            out.append(r'\section{'+escape(title)+'}')
            first_section=False; continue
        if line.startswith('## '):
            title=re.sub(r'^\d+\s+\d+\s+', '', line[3:])
            out.append((r'\subsection*{' if title=='Tài liệu tham khảo' else r'\subsection{')+escape(title)+'}')
            continue
        if line.startswith('|'):
            rows=[]
            i-=1
            while i<len(lines) and lines[i].strip().startswith('|'):
                cells=[x.strip() for x in lines[i].strip().strip('|').split('|')]
                if not all(re.fullmatch(r'[-:]+', x or '-') for x in cells): rows.append(cells)
                i+=1
            n=len(rows[0]); fmt={2:'YY',3:'YYY',4:'Yrrr',5:'cYYrr'}[n]
            out.append(r'\begingroup\small\setlength{\tabcolsep}{5pt}'+'\n'+
                       r'\begin{tabularx}{\linewidth}{@{}'+fmt+r'@{}}\toprule')
            for ri,row in enumerate(rows):
                out.append(' & '.join((r'\textbf{'+escape(v)+'}') if ri==0 else escape(v) for v in row)+r'\\')
                if ri==0: out.append(r'\midrule')
            out.append(r'\bottomrule\end{tabularx}\endgroup\par')
            continue
        im=re.fullmatch(r'!\[(.*?)\]\((.*?)\)',line)
        if im:
            if im.group(2).endswith('08_equations.png'):
                out.append(MATH); continue
            cap=re.sub(r'^Hình\s+\d+\s+', '', im.group(1))
            name=Path(im.group(2)).name
            width='.93' if name=='04_correlations.png' else '1'
            out.append(r'\begin{figure}[H]\centering'+'\n'+r'\includegraphics[width='+width+r'\linewidth]{'+name+'}\n'+r'\caption{'+escape(cap)+r'}\end{figure}')
            continue
        if line.startswith('RMSE log = sqrt('):
            out.append(METRICS); continue
        if line.startswith('Với L2, đặt gradient'):
            out.append(r'''Với L2, đặt gradient theo $w$ bằng 0 sau khi tâm hóa $X$ và $z$ thu được
\[
\left(\frac{X^{\mathsf T}X}{n}+\alpha I\right)w=\frac{X^{\mathsf T}z}{n}.
\]
Khi $\alpha>0$, phần $\alpha I$ làm các hướng có trị riêng nhỏ ổn định hơn.
Hệ số thường co liên tục và không thành đúng 0. Điều này phù hợp khi nhiều
biến có tín hiệu nhỏ hoặc các biến garage và diện tích liên quan mạnh.'''); continue
        if line.startswith('Với L1, chuẩn trị tuyệt đối'):
            out.append(r'''Với L1, chuẩn trị tuyệt đối không khả vi tại 0. Điều kiện tối ưu dùng
dưới gradient, cho phép một số hệ số bằng đúng 0. Trong trường hợp đặc biệt
$X^{\mathsf T}X/n=I$, nghiệm là soft-threshold:
\begin{equation}
w_j=\operatorname{sign}(c_j)\max(|c_j|-\alpha,0),\qquad
c=\frac{X^{\mathsf T}z}{n}.
\end{equation}
Công thức giải thích cơ chế chọn biến nhưng không phải nghiệm đóng cho
dữ liệu Ames tổng quát.'''); continue
        if line.startswith('Đầu ra gốc là y ='):
            out.append(r'''Đầu ra gốc là $y=\mathrm{SalePrice}>0$. Giá trị dùng để tối ưu mô hình
dự kiến là $z=\ln(1+y)$; khôi phục giá bằng $y=\exp(z)-1$.
Dữ liệu không phải giá rao bán Việt Nam và không đại diện cho thị trường hiện nay.'''); continue
        if line.startswith('Phần này chuẩn bị lý thuyết'):
            out.append(r'''Phần này chuẩn bị lý thuyết cho đề tài; KT1 chưa tối ưu hệ số hay chọn
$\alpha$. Gọi $X\in\R^{n\times p}$ là ma trận đặc trưng sau biến đổi,
$w\in\R^p$ là hệ số, $b$ là intercept và $z=\ln(1+y)$.
Intercept thường không bị phạt. Sử dụng quy ước mất mát chuẩn hóa theo $1/(2n)$.'''); continue
        line=line.replace('SimpleImputer(strategy=median, add_indicator=True)',
                          'SimpleImputer với median và cờ thiếu')
        line=line.replace('OneHotEncoder(handle_unknown=ignore)',
                          'OneHotEncoder với quy tắc ignore cho mức mới')
        out.append(escape(line)+'\n')
    out.append(r'\end{document}')
    (DEST/'main.tex').write_text('\n\n'.join(out), encoding='utf-8')
    (DEST/'README.md').write_text('''# Báo cáo KT1 bản LaTeX

Mở `main.tex`, dùng **pdfLaTeX**, biên dịch hai lần để cập nhật mục lục.
Nguồn UTF-8; hỗ trợ pdfLaTeX/T5 và XeLaTeX/fontspec. Công thức là LaTeX gốc.
Thư mục `images/` chứa 7 biểu đồ đi kèm. Điền thông tin sinh viên ở đầu main.tex.

Trên Overleaf: New project → Upload project → chọn ZIP bộ nguồn → Recompile.
Không cần tải dataset hoặc chạy Python để biên dịch bộ nguồn này.

Bản Word, notebook và mã phân tích nằm ở thư mục cha của repository.
''', encoding='utf-8')
    target=ROOT/'reports/KT1_LaTeX_Overleaf.zip'
    with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED) as z:
        for f in sorted(DEST.rglob('*')):
            if f.is_file() and (f.suffix in ['.tex','.png','.md']):
                z.write(f, f.relative_to(DEST).as_posix())
    print(target)

if __name__=='__main__':
    build()
