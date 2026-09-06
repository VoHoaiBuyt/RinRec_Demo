"""
mongo_connector.py
Quản lý kết nối và truy xuất dữ liệu từ MongoDB Atlas (Database: RinRec_DB) cho hệ thống RinRec Fintech Recommendation System.
"""
import os
import sys
import urllib.parse
import pandas as pd
from pymongo import MongoClient

if sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Tự động nạp cấu hình từ file .env nếu có (tìm ở thư mục hiện tại hoặc thư mục cha)
for env_path in [
    os.path.join(os.path.dirname(__file__), ".env"),
    os.path.join(os.path.dirname(__file__), "..", ".env")
]:
    if os.path.exists(env_path):
        try:
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        os.environ.setdefault(k.strip(), v.strip())
            break
        except Exception:
            pass

# Nạp cấu hình từ Streamlit Cloud Secrets nếu có
try:
    import streamlit as _st
    if hasattr(_st, "secrets"):
        for _k in ["MONGO_USER", "MONGO_PASS", "MONGO_HOST", "MONGO_DB_NAME", "MONGO_URI"]:
            if _k in _st.secrets and _k not in os.environ:
                os.environ[_k] = str(_st.secrets[_k])
except Exception:
    pass

# Cấu hình kết nối MongoDB Atlas
MONGO_USER = os.getenv("MONGO_USER", "rinrec_ad")
MONGO_PASS = os.getenv("MONGO_PASS", "Hoaibuyt05@")
MONGO_HOST = os.getenv("MONGO_HOST", "cluster0.t52ffqx.mongodb.net")
DB_NAME = os.getenv("MONGO_DB_NAME", "RinRec_DB")

# URL Encode mật khẩu để xử lý ký tự đặc biệt như '@'
encoded_pass = urllib.parse.quote_plus(MONGO_PASS)
DEFAULT_URI = f"mongodb+srv://{MONGO_USER}:{encoded_pass}@{MONGO_HOST}/?retryWrites=true&w=majority"
MONGO_URI = os.getenv("MONGO_URI", DEFAULT_URI)

_client = None

def get_mongo_client():
    """Khởi tạo hoặc tái sử dụng MongoClient singleton"""
    global _client
    if _client is None:
        _client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=8000)
    return _client

def get_database():
    """Lấy database RinRec_DB từ MongoDB Atlas"""
    client = get_mongo_client()
    return client[DB_NAME]

def get_collection_df(collection_name: str, query: dict = None, projection: dict = None) -> pd.DataFrame:
    """
    Truy vấn dữ liệu từ MongoDB collection và trả về Pandas DataFrame.
    Tự động loại bỏ trường '_id' của MongoDB.
    """
    try:
        db = get_database()
        if projection is None:
            projection = {"_id": 0}
        else:
            projection["_id"] = 0
            
        cursor = db[collection_name].find(query or {}, projection)
        data = list(cursor)
        if not data:
            return pd.DataFrame()
        return pd.DataFrame(data)
    except Exception as e:
        print(f"⚠️ Lỗi khi tải collection '{collection_name}' từ MongoDB: {e}")
        return pd.DataFrame()

def save_df_to_collection(collection_name: str, df: pd.DataFrame, drop_existing: bool = True):
    """
    Lưu DataFrame vào MongoDB collection.
    """
    if df.empty:
        print(f"⚠️ DataFrame rỗng, bỏ qua lưu vào '{collection_name}'.")
        return
    try:
        db = get_database()
        col = db[collection_name]
        if drop_existing:
            col.delete_many({})
        records = df.to_dict(orient="records")
        col.insert_many(records)
        print(f"✅ Đã lưu {len(records)} bản ghi vào collection '{collection_name}' trên MongoDB.")
    except Exception as e:
        print(f"⚠️ Lỗi khi ghi vào collection '{collection_name}': {e}")

def upsert_customer_face(cif_number: str, data: dict) -> bool:
    """
    Lưu hoặc cập nhật thông tin và vector khuôn mặt khách hàng vào MongoDB (collection 'customer_faces').
    """
    try:
        db = get_database()
        col = db["customer_faces"]
        cif_clean = str(cif_number).strip().upper()
        data["cif_number"] = cif_clean
        col.update_one({"cif_number": cif_clean}, {"$set": data}, upsert=True)
        print(f"✅ Đã lưu dữ liệu khuôn mặt của CIF '{cif_clean}' vào MongoDB collection 'customer_faces'.")
        return True
    except Exception as e:
        print(f"⚠️ Lỗi khi lưu dữ liệu khuôn mặt vào MongoDB: {e}")
        return False

def get_customer_faces(query: dict = None) -> list:
    """
    Lấy danh sách thông tin khuôn mặt khách hàng từ MongoDB collection 'customer_faces'.
    """
    try:
        db = get_database()
        col = db["customer_faces"]
        cursor = col.find(query or {}, {"_id": 0})
        return list(cursor)
    except Exception as e:
        print(f"⚠️ Lỗi khi truy vấn danh sách khuôn mặt từ MongoDB: {e}")
        return []

def get_customer_face(cif_number: str) -> dict:
    """
    Lấy thông tin khuôn mặt của một khách hàng theo CIF từ MongoDB.
    """
    try:
        db = get_database()
        col = db["customer_faces"]
        cif_clean = str(cif_number).strip().upper()
        res = col.find_one({"cif_number": cif_clean}, {"_id": 0})
        return res or {}
    except Exception as e:
        print(f"⚠️ Lỗi khi truy vấn khuôn mặt CIF '{cif_number}' từ MongoDB: {e}")
        return {}

def delete_customer_face(cif_number: str) -> bool:
    """
    Xóa dữ liệu khuôn mặt của một khách hàng khỏi MongoDB.
    """
    try:
        db = get_database()
        col = db["customer_faces"]
        cif_clean = str(cif_number).strip().upper()
        col.delete_one({"cif_number": cif_clean})
        print(f"✅ Đã xóa dữ liệu khuôn mặt CIF '{cif_clean}' khỏi MongoDB.")
        return True
    except Exception as e:
        print(f"⚠️ Lỗi khi xóa dữ liệu khuôn mặt từ MongoDB: {e}")
        return False

def update_customer_ekyc_status(cif_number: str, status: str = "ENROLLED", full_name: str = None, segment: str = None) -> bool:
    """
    Cập nhật trạng thái sinh trắc học eKYC trong bảng dim_customer trên MongoDB.
    """
    try:
        db = get_database()
        col = db["dim_customer"]
        cif_clean = str(cif_number).strip().upper()
        
        # Trích xuất số nguyên ID nếu có định dạng CUST_0093 -> 93
        num_id = None
        digits = "".join(filter(str.isdigit, cif_clean))
        if digits:
            num_id = int(digits)
            
        filters = [{"cif_number": cif_clean}]
        if num_id is not None:
            filters.append({"customer_id": num_id})
            filters.append({"cif_number": f"CIF{num_id:07d}"})
            
        update_fields = {"kyc_biometric_status": status}
        if full_name:
            update_fields["full_name"] = full_name
        if segment:
            update_fields["segment"] = segment
            
        col.update_many({"$or": filters}, {"$set": update_fields})
        return True
    except Exception as e:
        print(f"⚠️ Lỗi khi cập nhật trạng thái eKYC vào dim_customer: {e}")
        return False

def add_transaction(txn_data: dict) -> dict:
    """
    Thêm giao dịch mới vào factTransaction và purchase_history trên MongoDB Atlas (kèm fallback).
    """
    try:
        from datetime import datetime
        db = get_database()
        
        # 1. Chuẩn hóa dữ liệu đầu vào
        cif_raw = str(txn_data.get("cif_number", "")).strip()
        digits = "".join(filter(str.isdigit, cif_raw))
        cid = int(digits) if digits else 1
        cif_formatted = f"CUST_{cid:04d}"
        
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        amt = float(txn_data.get("amount", 0.0))
        amt_str = f"{amt:,.0f} VND" if amt > 0 else "0 VND"
        service_name = txn_data.get("service_name", "Giao dịch tại quầy")
        service_group = txn_data.get("service_group", "Dịch vụ ngân hàng")
        channel = txn_data.get("channel", "QUẦY")
        cust_name = txn_data.get("customer_name", f"Khách hàng {cif_formatted}")
        segment = txn_data.get("segment", "MASS")
        
        # 2. Sinh transaction_id mới
        last_txn = db["factTransaction"].find_one({}, sort=[("transaction_id", -1)])
        next_tid = (last_txn.get("transaction_id", 0) + 1) if last_txn else int(datetime.now().timestamp())
        
        fact_doc = {
            "transaction_id": next_tid,
            "customer_id": cid,
            "service_code": txn_data.get("service_code", f"DV{next_tid % 1000:03d}"),
            "service_name": service_name,
            "service_group": service_group,
            "signal_tag": txn_data.get("signal_tag", "TRANSACTION_NEW"),
            "branch_code": txn_data.get("branch_code", "CN001"),
            "teller_id": txn_data.get("teller_id", "GDV001"),
            "transaction_datetime": now_str,
            "amount": amt,
            "currency": "VND",
            "channel": channel,
            "status": "SUCCESS"
        }
        db["factTransaction"].insert_one(fact_doc)
        
        # 3. Đồng bộ vào purchase_history collection
        ph_doc = {
            "reviewerID": cif_formatted,
            "reviewerName": cust_name,
            "segment": segment,
            "category": service_group,
            "title": service_name,
            "brand": "VPBank Financial",
            "price": amt_str,
            "channel": channel,
            "transaction_time": now_str
        }
        db["purchase_history"].insert_one(ph_doc)
        
        # Cập nhật số dư CASA nếu là nộp tiền/tiết kiệm
        if any(k in service_name.lower() for k in ["nộp tiền", "tiết kiệm", "tiền gửi"]):
            db["dim_customer"].update_one(
                {"$or": [{"customer_id": cid}, {"cif_number": cif_formatted}]},
                {"$inc": {"casa_balance": amt}, "$set": {"updated_at": now_str}}
            )
            
        print(f"✅ Đã thêm giao dịch #{next_tid} cho CIF {cif_formatted} vào MongoDB Atlas.")
        return {"success": True, "message": f"Đã ghi nhận thành công giao dịch #{next_tid}!", "data": ph_doc}
    except Exception as e:
        print(f"⚠️ Lỗi khi thêm giao dịch vào MongoDB: {e}")
        return {"success": False, "message": f"Lỗi: {str(e)}"}

def create_customer(cust_data: dict) -> dict:
    """
    Tạo mới hồ sơ khách hàng vào dim_customer và khởi tạo dữ liệu ban đầu trên MongoDB Atlas.
    """
    try:
        from datetime import datetime
        db = get_database()
        
        # Lấy customer_id lớn nhất để sinh ID tự tăng
        last_cust = db["dim_customer"].find_one({}, sort=[("customer_id", -1)])
        next_cid = (last_cust.get("customer_id", 0) + 1) if last_cust else 121
        
        cif_formatted = f"CUST_{next_cid:04d}"
        cif_standard = f"CIF{next_cid:07d}"
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        full_name = cust_data.get("full_name", "").strip()
        segment = cust_data.get("segment", "MASS").upper()
        casa = float(cust_data.get("casa_balance", 1000000.0))
        phone = cust_data.get("phone_number", "0900000000")
        id_num = cust_data.get("id_number", "001099000000")
        address = cust_data.get("address", "Hà Nội")
        occupation = cust_data.get("occupation", "Nhân viên văn phòng")
        
        new_doc = {
            "customer_id": next_cid,
            "cif_number": cif_standard,
            "cif_code": cif_formatted,
            "full_name": full_name,
            "date_of_birth": cust_data.get("date_of_birth", "1995-01-01"),
            "gender": cust_data.get("gender", "M"),
            "id_number": id_num,
            "phone_number": phone,
            "email": cust_data.get("email", f"cust_{next_cid}@rinrec.fintech.vn"),
            "address": address,
            "occupation": occupation,
            "income_range": cust_data.get("income_range", "20-40tr"),
            "marital_status": cust_data.get("marital_status", "Độc thân"),
            "segment": segment,
            "customer_since": datetime.now().strftime("%Y-%m-%d"),
            "home_branch_code": cust_data.get("branch_code", "CN001"),
            "kyc_biometric_status": cust_data.get("kyc_biometric_status", "PENDING"),
            "casa_balance": casa,
            "total_asset_value": casa,
            "churn_risk_score": 0.15,
            "updated_at": now_str
        }
        db["dim_customer"].insert_one(new_doc)
        
        # Tạo giao dịch kích hoạt tài khoản đầu tiên trong purchase_history
        init_ph = {
            "reviewerID": cif_formatted,
            "reviewerName": full_name,
            "segment": segment,
            "category": "A. Tài khoản & Thông tin KH",
            "title": "Mở mới tài khoản thanh toán CASA & Kích hoạt eKYC",
            "brand": "VPBank Financial",
            "price": f"{casa:,.0f} VND",
            "channel": "QUẦY",
            "transaction_time": now_str
        }
        db["purchase_history"].insert_one(init_ph)
        
        # Khởi tạo Top 5 sản phẩm khuyến nghị mặc định theo phân khúc
        default_recs = []
        if segment == "DIAMOND":
            recs_to_add = [
                ("SP010", "Gói Tài Khoản VPBank Diamond VIP", "Phân khúc", "0 VND", "Miễn phí quản lý", "Đặc quyền phòng chờ VIP, RM chăm sóc riêng", "98%"),
                ("SP008", "Tiết Kiệm Tích Lũy Bậc Thang VIP", "Tiết kiệm", "500,000,000 VND", "6.8%/năm", "Tối đa hóa lợi nhuận dòng tiền nhàn rỗi lớn", "95%"),
                ("SP006", "Bảo Hiểm Liên Kết Đầu Tư Diamond", "Bảo hiểm", "50,000,000 VND", "Phí định kỳ năm", "Bảo vệ toàn diện & sinh lời kép an toàn", "92%"),
                ("SP001", "Thẻ Tín Dụng VPBank Priority World", "Thẻ", "Hạn mức 500tr", "45 ngày 0% lãi", "Hoàn tiền chi tiêu quốc tế & sân golf", "90%"),
                ("SP009", "Dịch Vụ Ngoại Tệ & Kiều Hối VIP", "Ngoại tệ", "Theo nhu cầu", "Ưu đãi tỷ giá 20 điểm", "Chuyển tiền quốc tế ưu tiên 24/7", "88%")
            ]
        elif segment == "PRIME":
            recs_to_add = [
                ("SP010", "Gói Hội Viên VPBank Prime Priority", "Phân khúc", "0 VND", "Miễn phí", "Miễn toàn bộ phí chuyển khoản, thẻ ghi nợ hoàn tiền", "97%"),
                ("SP001", "Thẻ Tín Dụng VPBank Step Up Cashback", "Thẻ", "Hạn mức 100tr", "45 ngày 0% lãi", "Hoàn tiền tới 15% khi mua sắm online, Grab, Shopee", "94%"),
                ("SP008", "Tiết Kiệm Trực Tuyến Prime Rate", "Tiết kiệm", "20,000,000 VND", "6.2%/năm", "Cộng thêm 0.3% lãi suất trên VPBank NEO", "91%"),
                ("SP002", "Gói Vay Tiêu Dùng Tín Chấp Prime", "Vay", "Hạn mức 200tr", "Từ 9.9%/năm", "Giải ngân nhanh 5 phút qua ứng dụng", "89%"),
                ("SP006", "Bảo Hiểm Sức Khỏe & Tai Nạn CarePlus", "Bảo hiểm", "5,000,000 VND", "Phí năm", "Bảo lãnh viện phí tại hơn 300 bệnh viện quốc tế", "86%")
            ]
        else: # MASS
            recs_to_add = [
                ("SP001", "Thẻ Thanh Toán Quốc Tế VPBank NEO Mastercard", "Thẻ", "0 VND", "Miễn phí trọn đời", "Rút tiền miễn phí tại mọi ATM và thanh toán tiện lợi", "96%"),
                ("SP008", "Tiết Kiệm Gửi Góp Định Kỳ EasySave", "Tiết kiệm", "1,000,000 VND", "5.8%/năm", "Tự động trích tiền gửi góp sinh lời mỗi tháng", "93%"),
                ("SP002", "Thấu Chi Tài Khoản Thanh Toán Online", "Vay", "Hạn mức 30tr", "Theo dư nợ thực tế", "Dự phòng tiền mặt chi tiêu cấp bách tức thì", "89%"),
                ("SP001", "Thẻ Tín Dụng VPBank Shopee Platinum", "Thẻ", "Hạn mức 50tr", "45 ngày 0% lãi", "Tích điểm Shopee Xu gấp 4 lần khi chi tiêu", "87%"),
                ("SP006", "Bảo Hiểm An Tâm Viện Phí Daily Care", "Bảo hiểm", "1,200,000 VND", "Phí năm", "Hỗ trợ 500k/ngày nằm viện không cần hóa đơn", "85%")
            ]
            
        for rank, (p_code, p_name, p_grp, p_lim, p_rate, p_val, p_sc) in enumerate(recs_to_add, 1):
            default_recs.append({
                "reviewerID": cif_formatted,
                "reviewerName": full_name,
                "segment": segment,
                "category": p_grp,
                "title": p_name,
                "brand": "VPBank Financial",
                "price": p_lim,
                "rate_or_fee": p_rate,
                "value_proposition": p_val,
                "match_score": p_sc,
                "gdv_script": f"Khách hàng mới gia nhập hệ thống. Tư vấn {p_name} để tối ưu hóa giải pháp tài chính cá nhân."
            })
        db["recommendations"].insert_many(default_recs)
        
        print(f"✅ Đã tạo mới khách hàng {full_name} với CIF {cif_formatted} (ID: {next_cid}) trên MongoDB.")
        return {"success": True, "message": f"Tạo khách hàng thành công! Mã CIF: {cif_formatted}", "cif": cif_formatted, "customer_id": next_cid}
    except Exception as e:
        print(f"⚠️ Lỗi khi tạo mới khách hàng: {e}")
        return {"success": False, "message": f"Lỗi: {str(e)}", "cif": None}

def add_product(prod_data: dict) -> dict:
    """
    Thêm sản phẩm tài chính mới vào DanhMucSanPham trên MongoDB Atlas.
    """
    try:
        db = get_database()
        col = db["DanhMucSanPham"]
        
        p_code = str(prod_data.get("Ma_SP", "")).strip().upper()
        if not p_code:
            # Tự sinh mã sản phẩm tiếp theo
            cnt = col.count_documents({}) + 1
            p_code = f"SP{cnt:03d}"
            
        p_name = prod_data.get("Ten_san_pham", "").strip()
        p_group = prod_data.get("Nhom", "Tài chính").strip()
        p_val = prod_data.get("Gia_tri_cot_loi", "Giải pháp tài chính tối ưu").strip()
        p_seg = prod_data.get("Phan_khuc", "ALL").strip()
        p_min = float(prod_data.get("So_tien_toi_thieu", 0.0))
        p_fee = prod_data.get("Lai_suat_Phi", "Theo biểu phí chuẩn").strip()
        p_priority = int(prod_data.get("Uu_tien", 5))
        
        doc = {
            "Ma_SP": p_code,
            "Nhom": p_group,
            "Ten_san_pham": p_name,
            "Gia_tri_cot_loi": p_val,
            "Phan_khuc": p_seg,
            "So_tien_toi_thieu": p_min,
            "Lai_suat_Phi": p_fee,
            "Uu_tien": p_priority
        }
        
        col.update_one({"Ma_SP": p_code}, {"$set": doc}, upsert=True)
        print(f"✅ Đã thêm/cập nhật sản phẩm {p_code} ({p_name}) vào MongoDB.")
        return {"success": True, "message": f"Đã lưu sản phẩm {p_name} ({p_code}) vào Danh mục!", "data": doc}
    except Exception as e:
        print(f"⚠️ Lỗi khi thêm sản phẩm: {e}")
        return {"success": False, "message": f"Lỗi: {str(e)}"}

def log_consultation(log_data: dict) -> dict:
    """
    Ghi nhật ký tư vấn & chốt hợp đồng bán chéo vào collection consultation_logs.
    """
    try:
        from datetime import datetime
        db = get_database()
        col = db["consultation_logs"]
        
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cif_raw = str(log_data.get("cif_number", "")).strip()
        
        log_doc = {
            "cif_number": cif_raw,
            "customer_name": log_data.get("customer_name", "Khách hàng"),
            "product_name": log_data.get("product_name", "Sản phẩm tài chính"),
            "category": log_data.get("category", "Tài chính"),
            "status": log_data.get("status", "CHỐT THÀNH CÔNG"),
            "deal_amount": log_data.get("deal_amount", "0 VND"),
            "notes": log_data.get("notes", ""),
            "teller_name": log_data.get("teller_name", "Giao dịch viên"),
            "teller_code": log_data.get("teller_code", "GDV001"),
            "created_at": now_str
        }
        col.insert_one(log_doc)
        print(f"✅ Đã lưu nhật ký tư vấn cho CIF {cif_raw} (Trạng thái: {log_doc['status']}).")
        return {"success": True, "message": "Đã lưu nhật ký tư vấn thành công!", "data": log_doc}
    except Exception as e:
        print(f"⚠️ Lỗi khi lưu nhật ký tư vấn: {e}")
        return {"success": False, "message": f"Lỗi: {str(e)}"}

def get_consultation_logs(cif_number: str = None) -> list:
    """
    Lấy danh sách nhật ký tư vấn từ collection consultation_logs.
    """
    try:
        db = get_database()
        col = db["consultation_logs"]
        q = {}
        if cif_number:
            cif_clean = str(cif_number).strip()
            q = {"cif_number": cif_clean}
        cursor = col.find(q, {"_id": 0}).sort("created_at", -1)
        return list(cursor)
    except Exception as e:
        print(f"⚠️ Lỗi khi lấy nhật ký tư vấn: {e}")
        return []

def test_connection():
    """Kiểm tra kết nối và in danh sách collection hiện có"""
    try:
        db = get_database()
        cols = db.list_collection_names()
        print(f"✅ Kết nối MongoDB Atlas thành công! Danh sách collections trong '{DB_NAME}':")
        for c in cols:
            cnt = db[c].count_documents({})
            print(f"  - {c}: {cnt} documents")
        return True
    except Exception as e:
        print(f"❌ Kết nối MongoDB Atlas thất bại: {e}")
        return False

if __name__ == "__main__":
    test_connection()

