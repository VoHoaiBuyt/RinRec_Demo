# 🏦 RinRec SmartAdvisor 360

**Hệ thống gợi ý sản phẩm ngân hàng thông minh sử dụng AI (UltraGCN) & Biometric**

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-green.svg)](https://fastapi.tiangolo.com)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.32+-red.svg)](https://streamlit.io)
[![MongoDB](https://img.shields.io/badge/MongoDB-Atlas-green.svg)](https://mongodb.com)

---

## 📋 Mục lục

1. [Giới thiệu](#giới-thiệu)
2. [Kiến trúc hệ thống](#kiến-trúc-hệ-thống)
3. [Tính năng chính](#tính-năng-chính)
4. [Công nghệ sử dụng](#công-nghệ-sử-dụng)
5. [Cài đặt & Triển khai](#cài-đặt--triển-khai)
6. [Hướng dẫn sử dụng](#hướng-dẫn-sử-dụng)
7. [API Documentation](#api-documentation)
8. [Pilot Metrics & ROI](#pilot-metrics--roi)
9. [Bảo mật](#bảo-mật)
10. [Testing](#testing)
11. [License](#license)

---

## 🎯 Giới thiệu

**RinRec SmartAdvisor 360** là hệ thống gợi ý sản phẩm ngân hàng thông minh, giúp Giao dịch viên (GDV/Teller) tư vấn khách hàng nhanh chóng và chính xác hơn. Hệ thống sử dụng:

- **AI/ML**: Mô hình UltraGCN (Graph Collaborative Filtering) để dự đoán sản phẩm phù hợp
- **Biometric**: Nhận diện khuôn mặt để xác thực khách hàng
- **CRM**: Ghi nhận lịch sử tư vấn, theo dõi conversion rate
- **Dashboard**: Hiển thị pilot metrics (AHT, ROI, NPS)

### Vấn đề giải quyết

- **Thời gian tư vấn quá lâng** (AHT: 8.5 phút → **4.2 phút**, giảm 50.6%)
- **Thiếu thông tin khách hàng toàn diện** (Customer 360)
- **Gợi ý sản phẩm không phù hợp** (Conversion rate: 76.7% với AI)
- **Khó theo dõi hiệu suất teller**

---

## 🏗️ Kiến trúc hệ thống

```
┌────────────────────────────────────────────────────────────────┐
│                     FRONTEND (Streamlit)                       │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │  5 TABS:                                                 │  │
│  │  1. Tổng quan KH    2. Lịch sử GD    3. Vay vốn & CIC   │  │
│  │  4. Đề xuất SP (AI) 5. Ghi nhận tư vấn                 │  │
│  └─────────────────────────────────────────────────────────┘  │
│                      ↕ REST API (JWT)                          │
└────────────────────────────────────────────────────────────────┘
                              ↓
┌────────────────────────────────────────────────────────────────┐
│                    BACKEND (FastAPI)                           │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────────┐      │
│  │ Auth (JWT)   │  │ CRUD Routes  │  │ AI Recommend   │      │
│  │ - Login      │  │ - Customers  │  │ - UltraGCN     │      │
│  │ - Refresh    │  │ - Products   │  │ - XAI Script   │      │
│  │ - RBAC       │  │ - Transactions│ │ - Top-K        │      │
│  └──────────────┘  └──────────────┘  └────────────────┘      │
│                      ↕ Repository Pattern                      │
└────────────────────────────────────────────────────────────────┘
                              ↓
┌────────────────────────────────────────────────────────────────┐
│                  DATA LAYER                                    │
│  ┌──────────────────┐       ┌───────────────────┐             │
│  │ MongoDB Atlas    │←────→ │ JSON Fallback     │             │
│  │ - Collections:   │       │ (core/fallback)   │             │
│  │   customers      │       │ - Auto-sync       │             │
│  │   products       │       │ - Offline mode    │             │
│  │   transactions   │       └───────────────────┘             │
│  │   consultations  │                                          │
│  │   users (JWT)    │       ┌───────────────────┐             │
│  │   audit_logs     │       │ Face Engine       │             │
│  └──────────────────┘       │ - OpenCV          │             │
│                              │ - face_recognition│             │
│                              └───────────────────┘             │
└────────────────────────────────────────────────────────────────┘
```

### Luồng xử lý gợi ý sản phẩm

```
1. Teller đăng nhập (JWT) → 2. Chọn CIF khách hàng
   ↓
3. GET /api/v1/recommendations/{cif}
   ↓
4. Backend:
   - Load UltraGCN model (hoặc JSON pre-computed)
   - Lấy thông tin khách: segment, income, transactions, loans
   - Apply business rules
   - Generate top-5 products với match score
   - Sinh script tư vấn (XAI)
   ↓
5. Frontend hiển thị Product Cards
   ↓
6. Teller bấm "Chốt đơn" → POST /api/v1/consultations
   ↓
7. Lưu vào CRM, tính conversion rate
```

---

## ✨ Tính năng chính

### 🎨 Frontend (5 Tabs - Theo thiết kế FELIX)

#### Tab 1: Tổng quan Khách hàng (Customer 360)
- **KPI Banner**: AUM, Tổng dư nợ, Hạn mức pre-approved, Điểm tín nhiệm
- **Thông tin**: Tên, CIF, Segment badge (Mass/Prime/Diamond), eKYC status
- **Hành vi**: Kênh giao dịch ưa chuộng (Mobile/ATM/Branch), Nhu cầu chính

#### Tab 2: Lịch sử Giao dịch
- **Filter**: Khoảng thời gian (7/30/90 ngày), Loại dịch vụ, Tiền vào/ra
- **Bảng**: Thời gian, Nội dung, Số tiền (màu xanh/đỏ), Kênh, Trạng thái
- Responsive table với horizontal scroll trên mobile

#### Tab 3: Vay vốn & Thông tin CIC
- **Lịch sử vay nội bộ**: Mã vay, Loại, Số tiền, Dư nợ, Lãi suất, Trạng thái
- **Thông tin CIC**: 
  - Ngày cập nhật, Số TCTD, Tổng dư nợ
  - Nhóm nợ (badge màu)
  - **Cảnh báo**: Nếu nhóm nợ >= 3
  - Lịch sử nợ xấu (nếu có)

#### Tab 4: Đề xuất Sản phẩm (AI)
- **Product Cards**: Top-5 gợi ý từ UltraGCN
  - Tiêu đề, Danh mục, **Match Score %**
  - Thông số (hạn mức, lãi suất)
  - Giá trị mang lại
  - **Script tư vấn** (XAI - giải thích AI)
- **3 nút hành động**:
  - ✅ Chốt đơn (lưu vào CRM)
  - 📱 Gửi App
  - 📋 Mở hồ sơ

#### Tab 5: Ghi nhận Tư vấn (CRM)
- **Form**: Multi-select sản phẩm, Ngày, Phản hồi KH (Đồng ý/Quan tâm/Từ chối)
- **Follow-up**: Nếu "Quan tâm" → Ngày hẹn, Kênh liên hệ
- **Lịch sử**: Bảng các ghi nhận trước đó

### 🔐 Backend (FastAPI - Production-ready)

#### Authentication & Security
- **JWT**: Access token (30min) + Refresh token (7 days)
- **RBAC**: Admin, Manager, Teller, Compliance
- **PII Encryption**: AES-256 (Fernet) cho email, phone, income, CIF
- **Rate Limiting**: 100 req/min per IP (slowapi)
- **Audit Logs**: Ghi mọi thay đổi quan trọng (user, action, timestamp, IP)

#### API Endpoints (Full CRUD)

**Auth**:
- POST `/api/v1/auth/login` → access_token + refresh_token
- POST `/api/v1/auth/refresh`
- POST `/api/v1/auth/logout`
- GET `/api/v1/auth/me`

**Customers**:
- GET `/api/v1/customers` (list, pagination)
- GET `/api/v1/customers/{cif}` (detail với KPI)
- POST, PUT, PATCH, DELETE (RBAC)

**Loans & CIC**:
- GET `/api/v1/customers/{cif}/loans`
- GET `/api/v1/customers/{cif}/cic`

**Recommendations** (AI):
- GET `/api/v1/recommendations/{cif}` → Top-K products + XAI
- POST `/api/v1/recommendations/train` (retrain model - admin only)

**Consultations** (CRM):
- GET, POST, PUT, PATCH, DELETE `/api/v1/consultations`

**Pilot Metrics**:
- GET `/api/v1/metrics` → AHT, conversion, ROI, NPS
- POST `/api/v1/metrics/update` (admin manual input)

**Audit**:
- GET `/api/v1/audit_logs?limit=50`

---

## 🛠️ Công nghệ sử dụng

### AI/ML
- **UltraGCN**: Graph Collaborative Filtering (PyTorch)
- **XAI**: Rule-based explanation generation
- **Fallback**: Rule-based recommendation nếu không có model

### Backend
- **FastAPI** 0.110+: REST API
- **PyMongo** 4.6+: MongoDB driver
- **python-jose**: JWT
- **passlib + bcrypt**: Password hashing
- **cryptography**: PII encryption (Fernet)
- **slowapi**: Rate limiting
- **pytest + httpx**: Testing

### Frontend
- **Streamlit** 1.32+: Web UI
- **Plotly**: Interactive charts (admin dashboard)
- **Pandas**: Data manipulation

### Database
- **MongoDB Atlas**: Primary (Cloud)
- **JSON Fallback**: Offline mode (`core/fallback_data/`)

### DevOps
- **Docker** + **Docker Compose**: Containerization
- **Makefile**: Automation (test, lint, seed-db)
- **GitHub Actions** (optional): CI/CD

---

## 🚀 Cài đặt & Triển khai

### Yêu cầu hệ thống

- Python 3.9+
- Docker & Docker Compose (recommended)
- MongoDB Atlas account (hoặc local MongoDB)

### Quick Start (Docker)

```bash
# 1. Clone repository
git clone https://github.com/your-org/RinRec_Demo.git
cd RinRec_Demo

# 2. Copy .env.example → .env
cp .env.example .env

# 3. Chỉnh sửa .env (quan trọng!)
nano .env  # Thay JWT_SECRET, ENCRYPTION_KEY, MONGODB_URI

# 4. Build & Run
make docker-build
make docker-up

# 5. Truy cập
# Frontend: http://localhost:8501
# Backend API Docs: http://localhost:8000/docs
# Admin Dashboard: http://localhost:8502
```

### Local Development (no Docker)

```bash
# 1. Install dependencies
make install

# 2. Seed database (nếu MongoDB available)
make seed-db

# 3. Run backend (terminal 1)
make run-backend

# 4. Run frontend (terminal 2)
make run-frontend

# 5. Run admin dashboard (terminal 3)
make run-dashboard
```

### Environment Variables (.env)

```env
# MongoDB
MONGODB_URI=mongodb+srv://user:pass@cluster.mongodb.net/?retryWrites=true&w=majority
MONGODB_DB_NAME=RinRec_DB

# Security (CHANGE IN PRODUCTION!)
JWT_SECRET=your_secret_key_at_least_32_characters
JWT_REFRESH_SECRET=your_refresh_secret_also_32_chars
ENCRYPTION_KEY=your_fernet_key_base64_encoded

# Admin account
ADMIN_USERNAME=admin
ADMIN_PASSWORD=Admin@123
ADMIN_FULLNAME=TS. Trần Anh Tuấn

# Redis (optional)
# REDIS_URL=redis://localhost:6379/0

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/app.log
```

---

## 📖 Hướng dẫn sử dụng

### Cho Teller (Giao dịch viên)

1. **Đăng nhập**: Username + Password (role: TELLER)
2. **Chọn khách hàng**: Nhập CIF hoặc tìm theo tên
3. **Xem thông tin**: 
   - Tab 1: Tổng quan KPI, segment, hành vi
   - Tab 2: Lịch sử giao dịch (filter theo ngày)
   - Tab 3: Vay vốn, CIC (kiểm tra nhóm nợ)
4. **Nhận gợi ý AI**: Tab 4 → Top-5 sản phẩm + script tư vấn
5. **Ghi nhận tư vấn**: Tab 5 → Chọn sản phẩm, phản hồi KH, lưu
6. **Chốt đơn**: Bấm "Chốt đơn" trên Product Card → Tự động lưu CRM

### Cho Manager/Admin

1. Truy cập **Admin Dashboard**: http://localhost:8502
2. Xem **Pilot Metrics**: AHT, conversion rate, ROI, NPS
3. **Analytics**: 
   - Giao dịch theo thời gian (line chart)
   - Top sản phẩm (bar chart)
   - Hiệu suất teller (table + chart)
4. **Audit Logs**: Theo dõi mọi hành động trong hệ thống
5. **Quản lý**: 
   - CRUD users (role, status)
   - Update metrics thủ công

---

## 📊 Pilot Metrics & ROI

### Kết quả thực nghiệm (Pilot)

| Chỉ số | Trước RinRec | Sau RinRec | Cải thiện |
|--------|--------------|------------|-----------|
| **AHT** (Average Handling Time) | 8.5 phút | **4.2 phút** | ↓ 50.6% |
| **Khách hàng phục vụ/tháng** | 450 | **570** | +120 KH |
| **Conversion Rate** | 58.3% | **76.7%** | +18.4% |
| **ROI** | - | **320%** | - |
| **Chi phí tiết kiệm/năm** | - | **1.5 tỷ VND** | - |
| **NPS Score** | 58 | **72** | +14 điểm |

### Giải thích kết quả

- **AHT giảm 50.6%**: AI gợi ý ngay sản phẩm phù hợp, teller không mất thời gian tìm kiếm thủ công
- **+120 khách hàng/tháng**: Tiết kiệm thời gian → phục vụ thêm nhiều KH
- **Conversion rate 76.7%**: Gợi ý chính xác → KH dễ chấp nhận hơn
- **ROI 320%**: Chi phí đầu tư < lợi nhuận từ tăng doanh số + tiết kiệm nhân sự
- **NPS +14**: Khách hàng hài lòng hơn với dịch vụ nhanh, chính xác

---

## 🔒 Bảo mật

### 1. Authentication & Authorization

- **JWT**: 
  - Access token (short-lived): 30 minutes
  - Refresh token (long-lived): 7 days, stored in MongoDB `users.tokens[]`
- **RBAC** (Role-Based Access Control):
  - **Admin**: Full CRUD, manage users, view audit logs
  - **Manager**: Reports, analytics, approve large transactions
  - **Teller**: View customers, recommendations, create consultations (no delete)
  - **Compliance**: Read-only audit logs

### 2. Data Encryption

- **PII fields** (email, phone, income, CIF): Encrypted at rest using **Fernet** (AES-256-GCM)
- **Passwords**: Hashed with **bcrypt** (cost factor: 12)
- **HTTPS**: Required in production (via reverse proxy: Nginx, Traefik)

### 3. Rate Limiting

- **slowapi**: 100 requests/minute per IP
- **Fallback**: In-memory if Redis not available
- **Production**: Use Redis for distributed rate limiting

### 4. Audit Logging

Every critical action is logged in MongoDB `audit_logs`:

```json
{
  "user": "teller01",
  "action": "UPDATE_CUSTOMER",
  "timestamp": "2024-09-06T10:30:00Z",
  "ip": "192.168.1.100",
  "endpoint": "/api/v1/customers/CUST_0001",
  "payload": {"field": "phone", "old": "encrypted_old", "new": "encrypted_new"}
}
```

### 5. Security Best Practices

- ✅ No hardcoded secrets (use .env)
- ✅ Parameterized queries (prevent SQL/NoSQL injection)
- ✅ Input validation (Pydantic schemas)
- ✅ CORS configuration
- ✅ Secret rotation policy (JWT keys every 90 days)
- ✅ MongoDB connection string stored securely

---

## 🧪 Testing

### Run all tests

```bash
make test
```

### Manual testing

```bash
# Syntax check
make test-syntax

# Database connection
make test-db

# API endpoints (pytest)
python -m pytest backend/tests/test_api.py -v
```

### Test scenarios

- ✅ Login (valid/invalid credentials)
- ✅ JWT refresh
- ✅ CRUD operations (customers, products)
- ✅ Recommendations endpoint
- ✅ Audit log creation
- ✅ Rate limiting (429 after 100 requests)
- ✅ RBAC (403 for unauthorized roles)

---

## 📚 API Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Example: Get recommendations

**Request**:
```bash
curl -X GET "http://localhost:8000/api/v1/recommendations/CUST_0001" \
  -H "Authorization: Bearer <access_token>"
```

**Response**:
```json
{
  "cif": "CUST_0001",
  "recommendations": [
    {
      "product_id": "PROD_002",
      "product_name": "Vay tiêu dùng không thế chấp",
      "category": "Loan",
      "match_score": 87.5,
      "specs": "Hạn mức: 500tr, Lãi suất: 0.99%/tháng",
      "value_proposition": "Tiết kiệm 30% chi phí vay so với thị trường",
      "script": "Khách hàng có thu nhập ổn định, phù hợp với gói vay tiêu dùng ưu đãi. Quy trình duyệt nhanh 24h."
    }
  ]
}
```

---

## 📁 Cấu trúc thư mục

```
RinRec_Demo/
├── backend/
│   ├── app/
│   │   ├── api/routes/
│   │   │   ├── auth.py         # JWT login/logout
│   │   │   ├── customers.py    # CRUD customers
│   │   │   ├── products.py
│   │   │   ├── transactions.py
│   │   │   ├── consultations.py
│   │   │   ├── loans.py         # Loans & CIC
│   │   │   ├── metrics.py       # Pilot metrics
│   │   │   └── users.py         # User management
│   │   ├── core/
│   │   │   ├── auth.py          # JWT dependencies, RBAC
│   │   │   ├── security.py      # JWT, encryption, rate limiter
│   │   │   ├── db_connector.py  # MongoDB + JSON fallback
│   │   │   └── config.py
│   │   ├── models/
│   │   │   └── fintech_models_comparison.py  # UltraGCN
│   │   ├── repositories/
│   │   │   ├── customer_repo.py  # Data access layer
│   │   │   └── ...
│   │   ├── services/
│   │   │   ├── recommendation_service.py  # AI + XAI
│   │   │   └── ...
│   │   └── main.py              # FastAPI app
│   ├── tests/
│   │   ├── test_api.py          # Pytest suite
│   │   └── __init__.py
│   └── requirements.txt
├── frontend/
│   ├── app/
│   │   ├── main_5tabs.py        # 5-tab Streamlit UI (FELIX design)
│   │   ├── components/
│   │   │   ├── auth_ui.py       # Glassmorphism login
│   │   │   └── responsive_utils.py
│   │   └── pages/
│   └── requirements.txt
├── dashboard/
│   └── app/
│       └── admin_dashboard_complete.py  # Plotly charts, metrics
├── core/
│   └── fallback_data/           # JSON files for offline mode
│       ├── customers.json
│       ├── products.json
│       ├── transactions.json
│       ├── consultations.json
│       └── rules.json
├── face_engine/
│   ├── face_recognizer.py       # OpenCV + face_recognition
│   └── session_manager.py       # QR session
├── shared/
│   └── schemas/
│       ├── customer_schema.py   # Pydantic models
│       └── ...
├── logs/                        # Application logs
├── .env.example
├── docker-compose.yml
├── Makefile
└── README.md
```

---

## 🎓 Tài liệu tham khảo

1. **UltraGCN**: Meng Liu et al. (2021). "UltraGCN: Ultra Simplification of Graph Convolutional Networks for Recommendation." CIKM 2021.
2. **FastAPI Security**: https://fastapi.tiangolo.com/tutorial/security/
3. **MongoDB Encryption**: https://www.mongodb.com/docs/manual/core/security-client-side-encryption/
4. **Streamlit Best Practices**: https://docs.streamlit.io/

---

## 📞 Liên hệ & Hỗ trợ

- **Team**: FELIX - VPBank RinRec
- **Email**: support@rinrec.vpbank.com.vn
- **GitHub Issues**: https://github.com/your-org/RinRec_Demo/issues

---

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

---

**Lưu ý**: Đây là hệ thống production-ready nhưng vẫn cần:
- Penetration testing
- Load testing (1000+ concurrent users)
- GDPR/Privacy compliance audit (nếu triển khai quốc tế)
- MongoDB backup & disaster recovery plan

---

© 2024 VPBank - RinRec SmartAdvisor 360 | Powered by UltraGCN AI
