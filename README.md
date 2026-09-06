# 🏦 RinRec - SmartAdvisor 360 (Monorepo)
### Financial & Banking Product Recommendation System with UltraGCN & FastAPI Architecture

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.30+-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io/)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.0+-EE4C2C?logo=pytorch&logoColor=white)](https://pytorch.org/)
[![MongoDB](https://img.shields.io/badge/MongoDB-Atlas-47A248?logo=mongodb&logoColor=white)](https://www.mongodb.com/atlas)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)](https://www.docker.com/)

> **RinRec SmartAdvisor 360**: Nền tảng tư vấn tài chính và gợi ý sản phẩm ngân hàng cá nhân hóa theo kiến trúc Monorepo phân tầng. Hệ thống kết hợp mô hình học sâu đồ thị (**UltraGCN - Ultra Simplification Graph Convolutional Networks**), động cơ luật chuyên gia (**Hybrid Rule-based Re-ranking**), nhận diện sinh trắc học eKYC và hệ thống sinh kịch bản tư vấn thời gian thực (Explainable AI) cho Giao dịch viên (GDV).

> 📋 **BÁO CÁO GIẢI TRÌNH BAN GIÁM KHẢO VÒNG 2 (ĐỘI FEB):** Chi tiết xem tại [FEB Round 2 Judge Response & Business Case](file:///Users/vothanhtong/RinRec_Demo/docs/FEB_Round2_Judge_Response_and_Business_Case.md):
> 1. **Số liệu Pilot Thực tế:** eKYC 99.4%, Latency 320ms, NPS 88/100, GDV Usability 4.8/5.0.
> 2. **Lượng hóa Tài chính & ROI:** AHT giảm 76.7% (15 phút ➔ 3.5 phút), OPEX giảm 82.8% (35.000đ ➔ 6.000đ/giao dịch), ROI 478.5% (Hòa vốn trong 2.1 tháng).
> 3. **Kiến trúc Công nghệ:** Sơ đồ End-to-End từ Biometric ➔ MongoDB ➔ UltraGCN ➔ Hybrid Rules ➔ XAI Script.
> 4. **Thương mại hóa B2B:** Mô hình SaaS Licensing per Teller/Branch & FEB Kiosk Enterprise.

---

## 👥 Ban Dự Án & Cố Vấn Chuyên Môn

| Vai trò | Họ và Tên | Đơn vị / Nhiệm vụ |
| :--- | :--- | :--- |
| **Cố Vấn Khoa Học** | TS. Trần Anh Tuấn | Giảng viên hướng dẫn & Thẩm định kiến trúc |
| **Trưởng Nhóm & ML/DL** | Nhóm Phát Triển RinRec | Thiết kế mô hình UltraGCN, Data Pipeline, FastAPI & Web Client |

---

## 🏛️ 1. Kiến Trúc Monorepo (System Architecture)

Hệ thống được tổ chức theo cấu trúc Monorepo phân tách rõ ràng trách nhiệm giữa Core Engine, REST API Backend, User Web Client, Admin Dashboard và Edge Module:

```
                  ┌────────────────────────────────────────┐
                  │          Client Applications           │
                  ├───────────────────┬────────────────────┤
                  │  Streamlit Client │   Admin Dashboard  │
                  │   (:8501 / Web)   │    (:8502 / Adm)   │
                  └─────────▲─────────┴──────────▲─────────┘
                            │                    │
                            │  HTTP / REST API   │
                            ▼                    ▼
                  ┌────────────────────────────────────────┐
                  │       Backend REST API (FastAPI)       │
                  │              Port :8000                │
                  ├────────────────────────────────────────┤
                  │  • /api/v1/customers                   │
                  │  • /api/v1/transactions                │
                  │  • /api/v1/products                    │
                  │  • /api/v1/consultations               │
                  └───────────┬────────────────┬───────────┘
                              │                │
            ┌─────────────────┴─┐            ┌─┴─────────────────┐
            │   AI & Analytics  │            │   Database Layer  │
            ├───────────────────┤            ├───────────────────┤
            │  • Financial      │            │  • MongoDB Atlas  │
            │    UltraGCN       │            │    (RinRec_DB)    │
            │  • Hybrid Rules   │            │  • Fallback JSON  │
            │  • Face eKYC      │            │  • RBAC Auth      │
            └───────────────────┘            └───────────────────┘
```

* **`backend/`**: Cung cấp RESTful API với FastAPI, quản lý kết nối CSDL MongoDB Atlas, xác thực RBAC và dịch vụ AI models.
* **`frontend/`**: Giao diện chính cho Giao dịch viên (Streamlit Web Client) với Glassmorphism UI, eKYC WebRTC, Dynamic Tabs và XAI Recommendation.
* **`dashboard/`**: Bảng điều khiển quản trị viên theo dõi trạng thái hệ thống, phân quyền người dùng và nhật ký tư vấn.
* **`shared/`**: Chứa Schemas và Contracts dùng chung (Pydantic models, DTOs).
* **`face_engine/`**: Module nhận diện khuôn mặt sinh trắc học eKYC và đồng bộ phiên di động qua QR Code.
* **`core/` & `Product_Demo/`**: Được giữ nguyên nhằm đảm bảo tương thích ngược (Backward Compatibility) hoàn toàn.

---

## 📌 2. Tổng Quan Tính Năng Chính

* **Xử lý dữ liệu & Bipartite Graph**: Chuẩn hóa dữ liệu theo chuẩn Data Warehouse 10 bảng của ngân hàng.
* **Huấn luyện & So sánh 5 thuật toán**: Matrix Factorization (MF), Neural Collaborative Filtering (NCF), Deep MLP, LightGCN, và Financial-UltraGCN.
* **Top-K Đề xuất Cá nhân hóa**: Đề xuất Top-5 sản phẩm tài chính kèm điểm số **Match Score (%)** và hạn mức an toàn theo phân khúc (MASS, PRIME, DIAMOND).
* **Tính Khả giải (Explainable AI - XAI)**: Tự động sinh kịch bản tư vấn nghiệp vụ hiển thị trực tiếp lên màn hình giao dịch viên tại quầy.
* **Tích hợp eKYC Sinh Trắc Học**: Nhận diện khuôn mặt khách hàng qua webcam hoặc kết nối di động bằng QR Code.

---

## 📊 3. Nguồn Dữ Liệu Cloud (MongoDB Atlas - RinRec_DB)

Toàn bộ dữ liệu nghiệp vụ được lưu trữ và đồng bộ hóa qua **MongoDB Atlas (RinRec_DB)**:

* **`DanhMucDichVu`** (78 docs): Dịch vụ quầy và số hóa kèm nhãn tín hiệu nghiệp vụ (`MATURITY_EVENT`, `TRAVEL_STUDY_ABROAD`, `HIGH_CASA_INFLOW`...).
* **`DanhMucSanPham`** (25 docs): 25 sản phẩm tài chính mục tiêu (Tiết kiệm, Thẻ tín dụng, Vay tiêu dùng, Bảo hiểm, Ngoại tệ, Đầu tư).
* **`RuleGoiY`** (20 docs): 20 luật chuyên gia tài chính với trọng số và lý do nghiệp vụ cho re-ranking.
* **`dim_customer`** (120 docs): Hồ sơ khách hàng 360° (CIF, tên, phân khúc, thu nhập, rủi ro, thông tin eKYC).
* **`factTransaction`** (3.000 docs): Lịch sử giao dịch tài chính đa kênh.
* **`factCustomerProduct`** (299 docs): Danh mục sản phẩm khách hàng đang sở hữu thực tế.
* **`recommendations`** & **`purchase_history`**: Kết quả dự đoán Top-5 từ UltraGCN và lịch sử giao dịch được đồng bộ thời gian thực.
* **`consultation_logs`**: Nhật ký tư vấn và phản hồi khách hàng (Accept/Reject/Pending) dùng để tinh chỉnh mô hình.

---

## 🧠 4. Các Mô Hình AI & Đánh Giá Hiệu Năng

Hệ thống cài đặt và đánh giá 5 mô hình Recommendation System trên tập kiểm thử (Test Set 20%):

| Thuật toán (Model) | Precision@10 | Recall@10 | NDCG@10 | RMSE ↓ | MAE ↓ | Đặc điểm kiến trúc |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **Matrix Factorization (MF)** | 0.1523 | 0.7696 | 0.3293 | 3.3274 | 3.2639 | Phân rã ma trận tương tác tiềm ẩn |
| **Neural Collaborative Filtering (NCF)** | 0.0748 | 0.3558 | 0.1806 | **0.3329** | **0.2622** | Kết hợp Embeddings và mạng MLP |
| **Deep Multi-Layer Perceptron (Deep MLP)** | 0.0748 | 0.3651 | 0.2134 | **0.3068** | **0.2468** | Mạng đa tầng với Dropout & BatchNorm |
| **LightGCN** | 0.1692 | **0.8483** | **0.5088** | 4.2120 | 4.1921 | Truyền tin đa tầng qua đồ thị tương tác |
| **Financial-UltraGCN (Đề xuất)** | **0.1692** | 0.8421 | 0.4946 | 4.2407 | 4.2216 | **Bỏ qua lan truyền, tối ưu trực tiếp bậc node** |

> **Ưu thế của UltraGCN:** Xếp hạng tương đương LightGCN (**NDCG@10 ~ 0.50**, **Recall@10 ~ 84.8%**) nhưng tốc độ huấn luyện **nhanh hơn 10-15 lần** do loại bỏ hoàn toàn các bước Message Passing phức tạp.

---

## 📁 5. Cấu Trúc Thư Mục Dự Án (Monorepo Layout)

```
RinRec_Demo/
├── backend/                             # 🚀 Backend FastAPI REST API
│   ├── app/
│   │   ├── api/routes/                  # Các Router Endpoints
│   │   │   ├── customers.py             # CRUD & 360° View khách hàng
│   │   │   ├── transactions.py          # Quản lý & ghi nhận giao dịch
│   │   │   ├── products.py              # Danh mục sản phẩm ngân hàng
│   │   │   └── consultations.py         # Ghi nhận kết quả tư vấn GDV
│   │   ├── core/
│   │   │   ├── config.py                # Cấu hình tập trung (.env)
│   │   │   ├── mongo_connector.py       # Kết nối CSDL MongoDB Atlas
│   │   │   ├── auth.py                  # Xác thực PBKDF2 & Phân quyền RBAC
│   │   │   └── users_fallback.json      # Dữ liệu người dùng dự phòng
│   │   ├── models/                      # AI Pipelines & Model Training
│   │   │   ├── fintech_data_pipeline.py
│   │   │   └── fintech_models_comparison.py
│   │   ├── services/                    # Business Logic Layer
│   │   └── main.py                      # FastAPI App Entrypoint
│   ├── requirements.txt                 # Dependencies riêng cho Backend
│   └── Dockerfile                       # Image Docker FastAPI
│
├── frontend/                            # 💻 User Web Client (Streamlit)
│   ├── app/
│   │   ├── main.py                      # Ứng dụng chính cho Giao dịch viên
│   │   ├── components/                  # UI Components (Glassmorphism, Cards)
│   │   └── pages/                       # Multi-page views
│   ├── .streamlit/                      # Theme & UI configuration
│   ├── requirements.txt                 # Dependencies riêng cho Frontend
│   └── Dockerfile                       # Image Docker Streamlit
│
├── dashboard/                           # 📊 Admin Dashboard
│   └── app/
│       └── admin_dashboard.py           # Quản trị hệ thống, users & logs
│
├── shared/                              # 🔄 Shared Contracts & Schemas
│   └── schemas/
│       └── customer.py                  # Pydantic models dùng chung
│
├── face_engine/                         # 👤 Biometric eKYC Engine
│   ├── customer_faces/                  # Ảnh chuẩn hóa khuôn mặt
│   ├── face_recognizer.py               # Engine nhận diện khuôn mặt
│   ├── session_manager.py               # Quản lý phiên QR / Mobile
│   ├── setup_sample_faces.py            # Tạo dữ liệu mẫu
│   └── test_pipeline.py                 # Test nhận diện eKYC
│
├── notebooks/                           # 📓 Jupyter Notebooks Nghiên Cứu
│   ├── 01_Financial_Data_Processing.ipynb
│   ├── 02_Financial_Recommendation_System.ipynb
│   └── 03_Recommend_Using_UltraGCN.ipynb
│
├── mobile_client/                       # 📱 Mobile Web Client quét QR
│   └── index.html
│
├── core/                                # 🛡️ Legacy Core (Giữ nguyên tương thích)
├── Product_Demo/                        # 🛡️ Legacy Demo (Giữ nguyên tương thích)
│
├── docker-compose.yml                   # 🐳 Orchestration Backend + Frontend
├── Makefile                             # 🛠️ Bộ lệnh tự động hóa phát triển
├── .env.example                         # 📋 Mẫu biến môi trường
├── requirements.txt                     # 📦 Tổng hợp dependencies
└── README.md                            # 📖 Tài liệu dự án
```

---

## 🌐 6. Danh Sách REST API Endpoints (FastAPI)

FastAPI tự động cung cấp tài liệu Swagger UI trực quan tại `http://localhost:8000/docs`:

| Method | Endpoint | Mô Tả | Tham Số Chính |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/health` | Kiểm tra trạng thái hệ thống | - |
| `GET` | `/api/v1/customers/` | Lấy danh sách khách hàng | `skip`, `limit`, `search` |
| `GET` | `/api/v1/customers/{cif}` | Xem chi tiết hồ sơ 360° khách hàng | `cif` (e.g. `CUST001`) |
| `POST` | `/api/v1/customers/` | Tạo hồ sơ khách hàng mới | Customer JSON Payload |
| `GET` | `/api/v1/transactions/` | Lịch sử giao dịch toàn hệ thống | `cif`, `limit` |
| `POST` | `/api/v1/transactions/` | Ghi nhận giao dịch tài chính mới | Transaction JSON Payload |
| `GET` | `/api/v1/products/` | Lấy danh mục sản phẩm ngân hàng | `category` |
| `POST` | `/api/v1/products/` | Thêm sản phẩm tài chính mới | Product JSON Payload |
| `GET` | `/api/v1/consultations/` | Lịch sử nhật ký tư vấn của GDV | `cif`, `teller_id` |
| `POST` | `/api/v1/consultations/` | Ghi nhận phản hồi kết quả tư vấn | Consultation JSON Payload |

---

## 🏗️ 7. Tech Stack

* **Ngôn ngữ lõi**: Python 3.10+
* **Backend API**: FastAPI, Uvicorn, Pydantic v2
* **Frontend & Dashboard**: Streamlit, HTML5/CSS3 Glassmorphism UI
* **Cơ sở dữ liệu**: MongoDB Atlas (PyMongo, Dnspython) với Local Fallback
* **Machine Learning & Graph**: PyTorch, Scikit-learn, Pandas, NumPy, UltraGCN
* **eKYC & Computer Vision**: OpenCV, Pillow, QRCode
* **DevOps & Container**: Docker, Docker Compose, GNU Make

---

## ▶️ 8. Hướng Dẫn Cài Đặt & Khởi Chạy (Getting Started)

### 1. Chuẩn Bị Môi Trường

Sao chép file cấu hình môi trường và điền thông tin kết nối CSDL:

```bash
cp .env.example .env
```

Cập nhật các tham số chính trong [.env](file:///Users/vothanhtong/RinRec_Demo/.env):
```ini
MONGO_URI="mongodb+srv://<username>:<password>@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority"
DB_NAME="RinRec_DB"
ADMIN_USERNAME="admin"
ADMIN_PASSWORD="YourSecurePassword"
```

Cài đặt các gói thư viện:
```bash
# Cài đặt qua Makefile
make install

# Hoặc cài trực tiếp bằng pip
pip install -r requirements.txt
pip install fastapi uvicorn
```

---

### 2. Khởi Chạy Qua Makefile (Khuyến nghị)

Dự án cung cấp [Makefile](file:///Users/vothanhtong/RinRec_Demo/Makefile) với đầy đủ lệnh tự động hóa:

```bash
# 🖥️ Chạy Frontend Streamlit (Port 8501)
make run-frontend

# 🚀 Chạy Backend FastAPI REST API (Port 8000)
make run-backend

# 📊 Chạy Admin Dashboard (Port 8502)
make run-dashboard

# 🔍 Kiểm tra kết nối cơ sở dữ liệu MongoDB
make test-db

# 🧪 Chạy syntax check toàn bộ source code
make test

# 🔁 Chạy bản cũ (Backward compatibility)
make run-legacy
```

Truy cập các địa chỉ:
* **User Web Client (Streamlit)**: [http://localhost:8501](http://localhost:8501)
* **Backend API Docs (Swagger UI)**: [http://localhost:8000/docs](http://localhost:8000/docs)
* **Backend ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)
* **Admin Dashboard**: [http://localhost:8502](http://localhost:8502)

---

### 3. Khởi Chạy Bằng Docker Compose (Production Ready)

Khởi động toàn bộ cụm dịch vụ (Backend + Frontend) chỉ với một câu lệnh:

```bash
# Khởi động cụm dịch vụ nền
make docker-up
# Hoặc: docker-compose up -d --build

# Xem log thời gian thực
make docker-logs

# Dừng cụm dịch vụ
make docker-down
```

---

### 4. Huấn Luyện Lại Mô Hình (Retrain AI Model)

Để chạy lại pipeline tiền xử lý, tái tạo đồ thị và huấn luyện 5 thuật toán so sánh:

```bash
# Huấn luyện mô hình từ backend
python -m backend.app.models.fintech_models_comparison

# Hoặc từ legacy core
python -m core.fintech_models_comparison
```

Các file kết quả đề xuất và biểu đồ so sánh [model_comparison.png](file:///Users/vothanhtong/RinRec_Demo/docs/images/model_comparison.png) sẽ tự động được cập nhật.

---

## 🔐 9. Cơ Chế Xác Thực & Phân Quyền (RBAC)

Hệ thống bảo mật đa tầng với cơ chế **Role-Based Access Control (RBAC)**:

1. **Mật khẩu & Băm an toàn**: Sử dụng thuật toán `PBKDF2-HMAC-SHA256` với salt ngẫu nhiên cho mỗi tài khoản.
2. **Các vai trò được hỗ trợ**:
   * **Admin**: Quản trị toàn hệ thống, tạo tài khoản và phân quyền cho nhân viên.
   * **Manager**: Xem báo cáo chi nhánh, thống kê hiệu quả tư vấn và giám sát giao dịch.
   * **Teller (GDV)**: Quét eKYC khách hàng, tra cứu hồ sơ 360°, nhận đề xuất Top-5 và ghi nhận kết quả tư vấn.
3. **Cơ chế Fallback High-Availability**: Tự động chuyển sang xác thực file nội bộ an toàn nếu kết nối MongoDB Atlas gặp sự cố gián đoạn.
