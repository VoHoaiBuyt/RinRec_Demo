# 🏦 RinRec - Financial & Banking Product Recommendation System with UltraGCN

> **Dự án RinRec**: Nền tảng gợi ý sản phẩm tài chính và dịch vụ ngân hàng cá nhân hóa dựa trên học sâu đồ thị (**UltraGCN - Ultra Simplification Graph Convolutional Networks**) kết hợp động cơ luật chuyên gia (**Hybrid Rule-based Re-ranking**) và hệ thống kịch bản tư vấn thời gian thực cho Giao dịch viên (GDV).

---

## 👥 Ban Dự Án & Cố Vấn Chuyên Môn

| Vai trò | Họ và Tên | Đơn vị / Nhiệm vụ |
| :--- | :--- | :--- |
| **Cố Vấn Khoa Học** | TS. Trần Anh Tuấn | Giảng viên hướng dẫn & Thẩm định kiến trúc |
| **Trưởng Nhóm & ML/DL** | Nhóm Phát Triển RinRec | Thiết kế mô hình UltraGCN, Data Pipeline & Web Demo |

---

## 📌 1. Tổng Quan Dự Án (Overview)

Dự án tập trung xây dựng quy trình xử lý dữ liệu và huấn luyện hệ thống gợi ý đa mô hình dựa trên hành vi giao dịch thực tế của khách hàng tại quầy và ứng dụng số:

* **Xử lý dữ liệu & Đồ thị Bipartite**: Chuẩn hóa dữ liệu theo chuẩn Data Warehouse 10 bảng của ngân hàng.
* **Huấn luyện & So sánh 5 thuật toán**: Matrix Factorization (MF), Neural Collaborative Filtering (NCF), Deep MLP, LightGCN, và Financial-UltraGCN.
* **Top-K Đề xuất Cá nhân hóa**: Đề xuất Top-5 sản phẩm tài chính kèm điểm số **Match Score (%)** và hạn mức an toàn theo phân khúc (`MASS`, `PRIME`, `DIAMOND`).
* **Tính Khả giải (Explainable AI - XAI)**: Tự động sinh kịch bản tư vấn nghiệp vụ hiển thị trực tiếp lên màn hình giao dịch viên tại quầy.

---

## 📊 2. Nguồn Dữ Liệu Cloud (MongoDB Atlas - RinRec_DB)

Toàn bộ dữ liệu được lưu trữ và truy vấn trực tiếp từ cơ sở dữ liệu đám mây **MongoDB Atlas (`RinRec_DB`)**:
* **`DanhMucDichVu`** (78 docs): 78 dịch vụ quầy và số hóa kèm nhãn tín hiệu nghiệp vụ (`MATURITY_EVENT`, `TRAVEL_STUDY_ABROAD`, `HIGH_CASA_INFLOW`...).
* **`DanhMucSanPham`** (25 docs): 25 sản phẩm tài chính mục tiêu (Tiết kiệm, Thẻ, Vay, Bảo hiểm, Ngoại tệ, Đầu tư).
* **`RuleGoiY`** (20 docs): 20 luật chuyên gia tài chính với trọng số và câu giải thích lý do nghiệp vụ.
* **`dim_customer`** (120 docs) & **`factTransaction`** (3.000 docs): 120 hồ sơ khách hàng 360° và 3.000 giao dịch thực tế.
* **`factCustomerProduct`** (299 docs): Danh mục sản phẩm khách hàng đang sở hữu.
* **`recommendations`** & **`purchase_history`**: Kết quả dự đoán Top-5 từ mô hình UltraGCN và lịch sử giao dịch được đồng bộ theo thời gian thực.

---

## 🔍 3. Quy Trình Xử Lý Dữ Liệu (Data Pipeline)

$$\text{Data Extraction} \longrightarrow \text{Feature Engineering \& RFM} \longrightarrow \text{Bipartite Graph} \longrightarrow \text{Model Training} \longrightarrow \text{Hybrid Re-ranking} \longrightarrow \text{Streamlit Deployment}$$

1. **Làm sạch & Gán nhãn**: Chuẩn hóa trường tiền tệ, phân tích RFM theo thời gian.
2. **Xây dựng Bipartite Graph**: Tạo các cạnh tương tác User - Product/Service và tính bậc node $\deg(u), \deg(i)$.
3. **Chuẩn hóa bậc UltraGCN**: Trọng số cạnh chuẩn hóa $\beta_{ui} = \frac{1}{\sqrt{\deg(u) \cdot \deg(i)}}$.

---

## 🧠 4. Các Mô Hình Được Cài Đặt (Models Implemented)

1. **Matrix Factorization (MF)**: Phân rã ma trận tương tác người dùng - sản phẩm thành các vector tiềm ẩn (Latent Factors).
2. **Neural Collaborative Filtering (NCF)**: Kết hợp biểu diễn Embeddings với mạng MLP để học quan hệ phi tuyến phức tạp.
3. **Deep Multi-Layer Perceptron (Deep MLP)**: Mạng neural nhiều tầng kết hợp Dropout và BatchNorm.
4. **LightGCN**: Mô hình GCN chuẩn truyền tin qua đồ thị tương tác người dùng - sản phẩm.
5. **Financial-UltraGCN (Mô hình đề xuất tối ưu)**: Loại bỏ Message Passing đa tầng tốn kém, tối ưu trực tiếp hàm mất mát liên kết và ràng buộc an toàn tài chính.

---

## 📈 5. Bảng So Sánh Hiệu Năng (Evaluation Metrics)

Thực nghiệm đo lường trên tập kiểm thử (Test Set 20%) với 5 chỉ số tiêu chuẩn:

| Thuật toán (Model) | Precision@10 | Recall@10 | NDCG@10 | RMSE ↓ | MAE ↓ |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Matrix Factorization (MF)** | 0.1523 | 0.7696 | 0.3293 | 3.3274 | 3.2639 |
| **Neural Collaborative Filtering (NCF)** | 0.0748 | 0.3558 | 0.1806 | **0.3329** | **0.2622** |
| **Deep Multi-Layer Perceptron (Deep MLP)** | 0.0748 | 0.3651 | 0.2134 | **0.3068** | **0.2468** |
| **LightGCN** | 0.1692 | **0.8483** | **0.5088** | 4.2120 | 4.1921 |
| **Financial-UltraGCN (Đề xuất)** | **0.1692** | 0.8421 | 0.4946 | 4.2407 | 4.2216 |

> **Kết luận:** **UltraGCN** và **LightGCN** vượt trội về khả năng xếp hạng thực thể (**NDCG@10 đạt ~0.50**, **Recall@10 đạt ~84.8%**) so với các mô hình truyền thống nhờ khai thác triệt để cấu trúc đồ thị tương tác. UltraGCN có ưu thế vượt trội về tốc độ huấn luyện do không phải tính toán lan truyền tin đa tầng.

---

## 📋 6. So Sánh Kiến Trúc: LightGCN vs UltraGCN

| Đặc điểm | LightGCN | UltraGCN |
| :--- | :--- | :--- |
| **Cơ chế lan truyền (Message Passing)** | Lan truyền đa tầng qua các lớp (Tốn kém tài nguyên) | **Bỏ qua lan truyền** (Tối ưu hóa trực tiếp trên bậc node) |
| **Tương đồng toàn cục (Global Similarity)** | Không xét trực tiếp | **Tích hợp ma trận tương đồng Item-Item** |
| **Tốc độ huấn luyện (Efficiency)** | Chậm hơn khi đồ thị lớn | **Nhanh gấp 5-10 lần**, chi phí bộ nhớ thấp |
| **Khả năng ứng dụng thực tế** | Phức tạp khi scale hệ thống lớn | **Dễ dàng triển khai thực tế & Real-time Inference** |

---

## 🚀 7. Tính Năng Của Ứng Dụng (Features)

* **Chọn khách hàng mẫu**: Chọn khách hàng từ dropdown để xem hồ sơ và phân khúc (`MASS`, `PRIME`, `DIAMOND`).
* **Lịch sử giao dịch quầy & digital**: Hiển thị bảng chi tiết các dịch vụ khách hàng đã sử dụng.
* **Top 5 Đề xuất Cá nhân hóa UltraGCN**:
  * Tên sản phẩm, nhóm sản phẩm (Tiết kiệm, Thẻ, Vay, Bảo hiểm...).
  * Hạn mức tối thiểu, biểu phí / lãi suất.
  * Điểm tương đồng **Match Score (%)**.
  * **Kịch bản tư vấn GDV**: Lời thoại gợi ý giúp giao dịch viên chốt hợp đồng ngay tại quầy.

---

## 🏗️ 8. Tech Stack

* **Ngôn ngữ & Thư viện lõi**: Python 3.10+, PyTorch, Pandas, NumPy, Scikit-learn
* **Cơ sở dữ liệu đám mây**: MongoDB Atlas (PyMongo, Dnspython)
* **Trực quan hóa**: Matplotlib, Seaborn
* **Giao diện người dùng & Demo**: Streamlit, HTML5/CSS3 Glassmorphism UI
* **Kiến trúc mô hình**: Graph Neural Networks (Financial-UltraGCN, LightGCN), NCF, Deep MLP, MF

---

## ▶️ 9. Hướng Dẫn Khởi Chạy Demo (Usage)

### 1. Khởi chạy Streamlit Web App (Khuyến nghị)
1. Mở Terminal / PowerShell và di chuyển vào thư mục `Product_Demo`:
   ```bash
   cd Product_Demo
   ```
2. Chạy ứng dụng Streamlit:
   ```bash
   streamlit run demo_web.py
   ```
3. Truy cập trình duyệt tại địa chỉ: **`http://localhost:8501`**

### 2. Huấn luyện lại mô hình và tái tạo file kết quả
```bash
python fintech_models_comparison.py
```
Hai file `purchase_history.csv` và `recommendations.csv` trong `Product_Demo/` sẽ tự động được cập nhật.
