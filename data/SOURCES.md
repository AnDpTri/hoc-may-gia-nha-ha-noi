# Nguồn dữ liệu và điều kiện sử dụng

- Tác giả: Dean De Cock; nguồn ban đầu: Ames City Assessor’s Office.
- Bộ dữ liệu: Ames Housing, 2.930 giao dịch nhà ở tại Ames, Iowa, 2006–2010.
- Tệp TSV gốc: https://jse.amstat.org/v19n3/decock/AmesHousing.txt
- Từ điển gốc: https://jse.amstat.org/v19n3/decock/DataDocumentation.txt
- Bài báo: De Cock, D. (2011). *Ames, Iowa: Alternative to the Boston Housing Data as an End of Semester Regression Project*. Journal of Statistics Education, 19(3). https://doi.org/10.1080/10691898.2011.11889627
- Bản bài báo trên JSE: https://jse.amstat.org/v19n3/decock.pdf
- Ngày tải: 26/10/2026. Bản TSV được giữ nguyên bytes; SHA-256: `6cfe6cb525ba437de428653a1040e2aed7d696640bf75203786a6d7a0e67cfcc`.

## Điều kiện sử dụng

Nguồn công khai cung cấp dữ liệu phục vụ giảng dạy hồi quy. Trang/tệp gốc đã đọc không nêu giấy phép dữ liệu riêng một cách rõ ràng; dự án không tuyên bố dữ liệu là CC0/MIT hoặc tự cấp lại giấy phép. Lưu nguồn và trích dẫn tác giả, sử dụng bản sao này cho bài tập học phần. Cần kiểm tra quyền với chủ sở hữu trước khi tái phân phối rộng rãi hoặc sử dụng thương mại. Không suy diễn giấy phép GPL của một gói R thành giấy phép của tệp gốc.

Không đính kèm toàn văn bài báo vào repo. Giữ liên kết để đọc tài liệu từ nơi xuất bản. Repo được tạo private mặc định để chia sẻ theo nhu cầu học phần.

## Tài liệu phương pháp

- Scikit-learn, Linear models: https://scikit-learn.org/stable/modules/linear_model.html
- Common pitfalls: https://scikit-learn.org/stable/common_pitfalls.html
- ColumnTransformer: https://scikit-learn.org/stable/modules/generated/sklearn.compose.ColumnTransformer.html

Lưu ý: cách định nghĩa alpha của Ridge khác hệ số trước L2 trong mất mát chuẩn hóa theo 1/(2n). Mốc sau phải chọn alpha riêng cho từng thuật toán và fit preprocessing theo từng fold.
