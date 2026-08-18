"""
Cross-Device eKYC Session Manager & Mobile HTTP Server for RinRec / VPBank SmartAdvisor 360.
Bridges Mobile Smartphone Camera -> AI Model -> Desktop Smart Counter in Realtime.
"""

import os
import io
import time
import json
import uuid
import socket
import base64
import threading
import logging
from typing import Dict, Any, Optional
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs, quote
import urllib.request
from PIL import Image, ImageDraw, ImageFont

try:
    import qrcode
    HAS_QRCODE = True
except ImportError:
    qrcode = None
    HAS_QRCODE = False

from .face_recognizer import get_face_engine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("SessionManager")

def get_local_ip() -> str:
    """Tự động phát hiện địa chỉ IP mạng nội bộ (LAN) của máy chủ"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        try:
            return socket.gethostbyname(socket.gethostname())
        except Exception:
            return "127.0.0.1"

class CrossDeviceHTTPHandler(BaseHTTPRequestHandler):
    """HTTP Request Handler phục vụ giao diện Web Mobile và API nhận diện"""

    def log_message(self, format, *args):
        # Ẩn bớt log truy cập bình thường để console sạch sẽ
        pass

    def do_OPTIONS(self):
        """Xử lý CORS preflight requests"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_GET(self):
        """Phục vụ file HTML Mobile Client hoặc API kiểm tra trạng thái session"""
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)
        manager = get_session_manager()

        if parsed.path == "/api/status":
            # API kiểm tra trạng thái
            sid = params.get("sid", [""])[0]
            session = manager.get_session(sid)
            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            if session:
                self.wfile.write(json.dumps(session).encode('utf-8'))
            else:
                self.wfile.write(json.dumps({"status": "NOT_FOUND"}).encode('utf-8'))
            return

        # Phục vụ trang Mobile Camera HTML
        html_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "mobile_client", "index.html")
        if os.path.exists(html_path):
            with open(html_path, "r", encoding="utf-8") as f:
                content = f.read()
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(content.encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"Mobile Client HTML Not Found")

    def do_POST(self):
        """API nhận ảnh khuôn mặt tải lên từ điện thoại di động"""
        parsed = urlparse(self.path)
        manager = get_session_manager()

        if parsed.path == "/api/submit_face":
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            
            try:
                data = json.loads(post_data.decode('utf-8'))
                session_id = data.get("session_id", "")
                image_base64 = data.get("image", "")

                result = manager.submit_face(session_id, image_base64)
                
                self.send_response(200)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps(result).encode('utf-8'))
            except Exception as e:
                logger.error(f"Lỗi tiếp nhận ảnh từ Mobile: {e}")
                self.send_response(400)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "error": str(e)}).encode('utf-8'))
            return

        self.send_response(404)
        self.end_headers()


class CrossDeviceSessionManager:
    """
    Quản lý các phiên xác thực eKYC giữa Thiết bị Di Động và Màn Hình Quầy GDV.
    Tích hợp Mini HTTP Server chạy ngầm (Port 8088) để Mobile quét QR truy cập trực tiếp.
    """

    def __init__(self, port: int = 8088):
        self.port = port
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.server: Optional[HTTPServer] = None
        self.server_thread: Optional[threading.Thread] = None
        self.local_ip = get_local_ip()
        self.start_server()

    def start_server(self):
        """Khởi chạy HTTP Server chạy ngầm nếu chưa hoạt động"""
        if self.server is not None:
            return

        try:
            self.server = HTTPServer(('0.0.0.0', self.port), CrossDeviceHTTPHandler)
            self.server_thread = threading.Thread(target=self.server.serve_forever, daemon=True)
            self.server_thread.start()
            logger.info(f"Cross-Device eKYC Server đã khởi động tại: http://{self.local_ip}:{self.port}")
        except Exception as e:
            logger.warning(f"Không thể khởi động cổng {self.port} (có thể cổng đang dùng): {e}")

    def generate_qr_base64(self, data_url: str) -> str:
        """Tạo ảnh QR Code định dạng PNG Base64 (Hỗ trợ cả qrcode library và Online/PIL Fallback)"""
        if HAS_QRCODE and qrcode is not None:
            try:
                qr = qrcode.QRCode(
                    version=1,
                    error_correction=qrcode.constants.ERROR_CORRECT_M,
                    box_size=8,
                    border=2,
                )
                qr.add_data(data_url)
                qr.make(fit=True)
                img = qr.make_image(fill_color="#0A2540", back_color="#FFFFFF")
                
                buffered = io.BytesIO()
                img.save(buffered, format="PNG")
                return base64.b64encode(buffered.getvalue()).decode("utf-8")
            except Exception as e:
                logger.warning(f"Lỗi tạo QR qua thư viện qrcode: {e}")

        # Fallback 1: Lấy mã QR nét cao từ QR API
        try:
            api_url = f"https://api.qrserver.com/v1/create-qr-code/?size=250x250&data={quote(data_url)}&color=0A2540"
            req = urllib.request.Request(api_url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=2.5) as response:
                png_bytes = response.read()
                return base64.b64encode(png_bytes).decode("utf-8")
        except Exception as e:
            logger.warning(f"Lỗi tải QR từ API fallback: {e}")

        # Fallback 2: Tự tạo ảnh PNG mô phỏng QR Code bằng PIL (Hoạt động Offline 100%)
        img = Image.new("RGB", (250, 250), "#0A2540")
        draw = ImageDraw.Draw(img)
        # Vẽ khung viền và họa tiết
        draw.rectangle([10, 10, 240, 240], fill="#FFFFFF", outline="#00B14F", width=4)
        draw.rectangle([25, 25, 75, 75], fill="#0A2540")
        draw.rectangle([35, 35, 65, 65], fill="#FFFFFF")
        draw.rectangle([45, 45, 55, 55], fill="#0A2540")
        
        draw.rectangle([175, 25, 225, 75], fill="#0A2540")
        draw.rectangle([185, 35, 215, 65], fill="#FFFFFF")
        draw.rectangle([195, 45, 205, 55], fill="#0A2540")
        
        draw.rectangle([25, 175, 75, 225], fill="#0A2540")
        draw.rectangle([35, 185, 65, 215], fill="#FFFFFF")
        draw.rectangle([45, 195, 55, 205], fill="#0A2540")
        
        # Thêm text hướng dẫn
        draw.text((85, 115), "QUET QR CODE", fill="#0A2540")
        draw.text((70, 135), "XAC THUC eKYC", fill="#00B14F")
        
        buffered = io.BytesIO()
        img.save(buffered, format="PNG")
        return base64.b64encode(buffered.getvalue()).decode("utf-8")

    def create_session(self, duration_sec: int = 180) -> Dict[str, Any]:
        """Tạo một phiên xác thực eKYC mới kèm mã QR và URL kết nối di động"""
        self.cleanup_expired_sessions()
        session_id = f"EKYC_{uuid.uuid4().hex[:8].upper()}"
        now = time.time()
        
        mobile_url = f"http://{self.local_ip}:{self.port}/?sid={session_id}"
        local_url = f"http://localhost:{self.port}/?sid={session_id}"
        qr_base64 = self.generate_qr_base64(mobile_url)

        session_data = {
            "session_id": session_id,
            "created_at": now,
            "expires_at": now + duration_sec,
            "status": "PENDING", # PENDING | PROCESSING | VERIFIED | FAILED | EXPIRED
            "mobile_url": mobile_url,
            "local_url": local_url,
            "qr_base64": qr_base64,
            "result": None,
            "client_ip": None,
            "captured_image_base64": None
        }

        self.sessions[session_id] = session_data
        return session_data

    def submit_face(self, session_id: str, image_base64: str) -> Dict[str, Any]:
        """Tiếp nhận ảnh từ Mobile, kích hoạt Model AI nhận diện và lưu kết quả vào Session"""
        session = self.sessions.get(session_id)
        if not session:
            return {"success": False, "message": "Phiên xác thực không tồn tại hoặc đã hết hạn"}

        if time.time() > session["expires_at"]:
            session["status"] = "EXPIRED"
            return {"success": False, "message": "Phiên xác thực đã hết hạn"}

        session["status"] = "PROCESSING"
        session["captured_image_base64"] = image_base64

        # Kích hoạt Model AI nhận diện khuôn mặt
        engine = get_face_engine()
        result = engine.recognize_face(image_base64)

        if result["is_identified"]:
            session["status"] = "VERIFIED"
            session["result"] = result
            return {
                "success": True,
                "status": "VERIFIED",
                "customer_name": result["customer_name"],
                "cif_number": result["cif_number"],
                "confidence": result["confidence"],
                "segment": result["segment"],
                "message": f"Xác thực thành công khách hàng {result['customer_name']}!"
            }
        else:
            session["status"] = "FAILED"
            session["result"] = result
            return {
                "success": False,
                "status": "FAILED",
                "message": result.get("message", "Không nhận diện được danh tính khách hàng trong hệ thống")
            }

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Lấy thông tin và trạng thái hiện tại của phiên"""
        session = self.sessions.get(session_id)
        if session and time.time() > session["expires_at"] and session["status"] == "PENDING":
            session["status"] = "EXPIRED"
        return session

    def reset_session(self, session_id: str):
        """Đặt lại phiên để khách hàng quét/chụp lại"""
        session = self.sessions.get(session_id)
        if session:
            session["status"] = "PENDING"
            session["result"] = None
            session["captured_image_base64"] = None

    def cleanup_expired_sessions(self):
        """Dọn dẹp các phiên đã hết hạn quá 10 phút"""
        now = time.time()
        expired_keys = [
            k for k, v in self.sessions.items() 
            if now > v["expires_at"] + 600
        ]
        for k in expired_keys:
            del self.sessions[k]


# Singleton instance
_session_manager_instance: Optional[CrossDeviceSessionManager] = None

def get_session_manager() -> CrossDeviceSessionManager:
    """Lấy singleton instance của CrossDeviceSessionManager"""
    global _session_manager_instance
    if _session_manager_instance is None:
        _session_manager_instance = CrossDeviceSessionManager()
    return _session_manager_instance
