# Kế Hoạch Tích Hợp Nhận Diện Khuôn Mặt Liên Thiết Bị (Cross-Device eKYC) Vào RinRec

Dự án này tích hợp giải pháp **Xác thực Sinh trắc học Liên thiết bị (Cross-Device Face Verification)** vào hệ thống **VPBank SmartAdvisor 360 / RinRec Financial Recommendation System** (`e:\RinRec_Demo`). 

Luồng vận hành: Giao dịch viên (GDV) tại máy quầy/Desktop khởi tạo phiên eKYC ➔ Hệ thống sinh mã QR Động ➔ Khách hàng quét QR bằng Smartphone để chụp ảnh selfie ➔ Ảnh gửi về Backend đưa vào Model AI nhận diện (128D Face Embeddings) ➔ Kết quả tự động đồng bộ Realtime về màn hình quầy và kích hoạt toàn bộ Hồ sơ 360° & Đề xuất sản phẩm tài chính (UltraGCN).

---

## 👥 User Review Required

> [!IMPORTANT]
> **1. Phương thức kết nối giữa Mobile và Desktop:**
> - Hệ thống sẽ tích hợp một máy chủ phiên nhẹ (`Session Server`) chạy song song hoặc nhúng trực tiếp trong project, cho phép:
>   - Điện thoại trong cùng mạng Wi-Fi/LAN quét mã QR (truy cập theo IP LAN của máy tính, ví dụ `http://192.168.x.x:8501/...` hoặc cổng phụ `http://192.168.x.x:8000`).
>   - Khách hàng không cần cài đặt app, chỉ cần mở trình duyệt web mặc định trên điện thoại (Safari/Chrome).
>
> **2. Cơ chế nhận diện khuôn mặt (Dual-Engine AI):**
> - **Engine A (Ưu tiên)**: `face_recognition` (ResNet 128D Embeddings) nếu máy có sẵn dlib.
> - **Engine B (Fallback)**: Bộ so khớp vector thông minh / OpenCV để đảm bảo bản demo luôn hoạt động mượt mà 100% không lo lỗi thiếu thư viện C++.

---

## ❓ Open Questions

* Không có câu hỏi chặn. Hệ thống được thiết kế theo dạng mô-đun hóa độc lập (pluggable), không gây ảnh hưởng đến dữ liệu đề xuất UltraGCN hiện tại.

---

## 🏗️ Proposed Changes

### Component 1: Face Recognition Engine (`face_engine/`)

Xây dựng module xử lý nhận diện vector khuôn mặt và quản lý kho dữ liệu khuôn mặt khách hàng.

#### [NEW] [face_engine/__init__.py](file:///e:/RinRec_Demo/face_engine/__init__.py)
* Xuất các hàm giao tiếp cốt lõi của module nhận diện.

#### [NEW] [face_engine/face_recognizer.py](file:///e:/RinRec_Demo/face_engine/face_recognizer.py)
* Class `FaceRecognizerEngine`:
  * Tải và mã hóa vector 128D từ thư mục `customer_faces/` vào RAM với bộ đệm cache.
  * Hàm `recognize_face(image_input)`: Trả về mã CIF (`cif_number`), tên khách hàng (`customer_name`), độ khớp (`confidence` %), và khung mặt.
  * Hàm `enroll_customer_face(cif_number, image_bytes)`: Lưu ảnh và đăng ký khuôn mặt khách hàng mới.
  * Tích hợp Dual-Engine (chuyển đổi an toàn nếu không có dlib).

#### [NEW] Thư mục lưu ảnh mẫu [face_engine/customer_faces/](file:///e:/RinRec_Demo/face_engine/customer_faces/)
* Đồng bộ các ảnh chân dung khách hàng tương ứng với CSDL `dim_customer`:
  * `CUST_0093.jpg` (Vũ Quang Tuấn - Hạng MASS)
  * `CUST_0015.jpg` (Trần Thị Mai - Hạng PRIME)
  * `CUST_0009.jpg` (Nguyễn Văn An - Hạng DIAMOND)

---

### Component 2: Cross-Device Bridge & Mobile Client (`face_engine/session_manager.py` & `mobile_client/`)

Xây dựng cầu nối truyền nhận ảnh giữa Smartphone của khách hàng và Máy tính quầy của GDV.

#### [NEW] [face_engine/session_manager.py](file:///e:/RinRec_Demo/face_engine/session_manager.py)
* Quản lý vòng đời phiên xác thực eKYC:
  * `create_session() -> session_id, qr_image_base64, mobile_url`: Tạo phiên mới kèm mã QR và link truy cập di động.
  * `submit_face_capture(session_id, image_base64)`: Tiếp nhận ảnh từ Smartphone, gọi `FaceRecognizerEngine` xử lý và lưu kết quả vào session.
  * `get_session_status(session_id)`: Trả về trạng thái phiên (`PENDING`, `PROCESSING`, `VERIFIED`, `EXPIRED`) và thông tin khách hàng nhận diện được.

#### [NEW] [mobile_client/index.html](file:///e:/RinRec_Demo/mobile_client/index.html)
* Trang Web Mobile eKYC chuyên dụng:
  * Giao diện chuẩn ngân hàng (VPBank Green & Dark Navy), tối ưu cho màn hình cảm ứng di động.
  * Khung oval hướng dẫn khách hàng căn chỉnh khuôn mặt.
  * Sử dụng `navigator.mediaDevices.getUserMedia` (HTML5 Camera) chụp ảnh chất lượng cao.
  * Nút bấm *"Xác nhận & Gửi nhận diện"* kèm hiệu ứng quét sinh trắc học AI.

---

### Component 3: Nâng Cấp Giao Diện Streamlit (`Product_Demo/demo_web.py`)

Tích hợp tính năng eKYC liên thiết bị vào giao diện chính của GDV.

#### [MODIFY] [Product_Demo/demo_web.py](file:///e:/RinRec_Demo/Product_Demo/demo_web.py)
* **Thêm khu vực Quầy eKYC Thông Minh (Smart Counter eKYC Modal / Expander)**:
  * **Tab 1: 📱 Xác thực qua Di động (Cross-Device QR)**:
    * Hiển thị mã QR Động và URL kết nối di động.
    * Cơ chế tự động lắng nghe (Polling / Streamlit Rerun) trạng thái phiên.
    * Khi phát hiện có ảnh gửi về từ điện thoại ➔ Tự động hiển thị popup chúc mừng và load ngay Hồ sơ Khách hàng tương ứng.
  * **Tab 2: 📷 Chụp trực tiếp tại quầy (Webcam fallback)**:
    * Dùng `st.camera_input` cho trường hợp khách hàng muốn quét trực tiếp tại máy GDV.
  * **Tab 3: 📁 Tải ảnh đối soát / Đăng ký mới (Face Enrollment)**:
    * Upload ảnh CCCD/chân dung để đăng ký mã CIF mới.
* **Cập nhật Thẻ Hồ Sơ Khách Hàng**:
  * Thêm Huy hiệu: `🛡️ eKYC: ĐÃ XÁC THỰC SINH TRẮC HỌC (FaceID Verified via Mobile)`.
  * Tự động hiển thị phân tích nhu cầu tài chính và Top-5 sản phẩm đề xuất (UltraGCN) kèm kịch bản tư vấn GDV.

---

### Component 4: Cập Nhật Cấu Hình Thư Viện (`requirements.txt`)

#### [MODIFY] [requirements.txt](file:///e:/RinRec_Demo/requirements.txt)
* Bổ sung các thư viện hỗ trợ xử lý ảnh và sinh mã QR:
  * `opencv-python-headless>=4.8.0`
  * `Pillow>=9.0.0`
  * `qrcode>=7.4.2`

---

## 🧪 Verification Plan

### 1. Kiểm tra Lõi AI Cục bộ (Unit Test)
* Chạy test `python -m face_engine.face_recognizer`:
  * Xác nhận trích xuất vector 128D thành công và nhận diện chính xác các ảnh mẫu trong `customer_faces/`.
  * Đảm bảo cơ chế fallback hoạt động trơn tru không bị crash.

### 2. Kiểm tra Vòng đời Phiên Liên thiết bị (Cross-Device End-to-End)
* Chạy ứng dụng web:
  ```powershell
  streamlit run Product_Demo/demo_web.py
  ```
* **Kịch bản kiểm thử**:
  1. GDV bấm mở tab *"Xác thực qua Di động"* ➔ Màn hình hiển thị mã QR.
  2. Mở trình duyệt điện thoại (hoặc tab trình duyệt phụ) quét mã QR / truy cập link di động.
  3. Bật camera trên điện thoại, chụp ảnh mặt và bấm *"Xác nhận & Gửi nhận diện"*.
  4. Màn hình máy tính GDV tự động nhận tín hiệu, hiển thị popup *"✅ Nhận diện thành công: Khách hàng [Tên KH]"* và tự động chuyển sang Hồ sơ 360° tương ứng.
  5. Kiểm tra Top-5 sản phẩm UltraGCN và Kịch bản tư vấn hiển thị chuẩn xác.
