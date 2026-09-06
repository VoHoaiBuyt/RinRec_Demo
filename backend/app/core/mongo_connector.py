# -*- coding: utf-8 -*-
"""
backend/app/core/mongo_connector.py
Quản lý kết nối và truy xuất dữ liệu từ MongoDB Atlas (Database: RinRec_DB).
Refactored: imports config từ backend.app.core.config (centralized).
"""
import os
import sys
import pandas as pd
from pymongo import MongoClient

# ─── Path bootstrap (để chạy standalone hoặc qua import) ─────────────────────
_root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
if _root_dir not in sys.path:
    sys.path.insert(0, _root_dir)

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# ─── Import centralized config ────────────────────────────────────────────────
try:
    from backend.app.core.config import MONGO_URI, DB_NAME
except ImportError:
    # Fallback: load trực tiếp (chạy standalone)
    from app.core.config import MONGO_URI, DB_NAME  # type: ignore

# ─── Singleton MongoClient ────────────────────────────────────────────────────
_client: MongoClient = None  # type: ignore


def get_mongo_client() -> MongoClient:
    """Khởi tạo hoặc tái sử dụng MongoClient singleton."""
    global _client
    if _client is None:
        _client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=8000)
    return _client


def get_database():
    """Lấy database RinRec_DB từ MongoDB Atlas."""
    return get_mongo_client()[DB_NAME]


# ─── Generic CRUD Helpers ─────────────────────────────────────────────────────

def get_collection_df(collection_name: str, query: dict = None, projection: dict = None) -> pd.DataFrame:
    """Truy vấn MongoDB collection → Pandas DataFrame (không bao gồm _id)."""
    try:
        db = get_database()
        if projection is None:
            projection = {"_id": 0}
        else:
            projection["_id"] = 0
        cursor = db[collection_name].find(query or {}, projection)
        data = list(cursor)
        return pd.DataFrame(data) if data else pd.DataFrame()
    except Exception as e:
        print(f"⚠️ Lỗi khi tải collection '{collection_name}': {e}")
        return pd.DataFrame()


def save_df_to_collection(collection_name: str, df: pd.DataFrame, drop_existing: bool = True):
    """Lưu DataFrame vào MongoDB collection."""
    if df.empty:
        print(f"⚠️ DataFrame rỗng, bỏ qua '{collection_name}'.")
        return
    try:
        db = get_database()
        col = db[collection_name]
        if drop_existing:
            col.delete_many({})
        col.insert_many(df.to_dict(orient="records"))
        print(f"✅ Đã lưu {len(df)} bản ghi vào '{collection_name}'.")
    except Exception as e:
        print(f"⚠️ Lỗi khi ghi vào '{collection_name}': {e}")


# ─── Face / eKYC Operations ───────────────────────────────────────────────────

def upsert_customer_face(cif_number: str, data: dict) -> bool:
    """Lưu hoặc cập nhật vector khuôn mặt khách hàng (collection: customer_faces)."""
    try:
        db = get_database()
        cif_clean = str(cif_number).strip().upper()
        data["cif_number"] = cif_clean
        db["customer_faces"].update_one({"cif_number": cif_clean}, {"$set": data}, upsert=True)
        return True
    except Exception as e:
        print(f"⚠️ Lỗi upsert_customer_face '{cif_number}': {e}")
        return False


def get_customer_faces(query: dict = None) -> list:
    """Lấy danh sách thông tin khuôn mặt từ collection customer_faces."""
    try:
        return list(get_database()["customer_faces"].find(query or {}, {"_id": 0}))
    except Exception as e:
        print(f"⚠️ Lỗi get_customer_faces: {e}")
        return []


def get_customer_face(cif_number: str) -> dict:
    """Lấy thông tin khuôn mặt một khách hàng theo CIF."""
    try:
        cif_clean = str(cif_number).strip().upper()
        return get_database()["customer_faces"].find_one({"cif_number": cif_clean}, {"_id": 0}) or {}
    except Exception as e:
        print(f"⚠️ Lỗi get_customer_face '{cif_number}': {e}")
        return {}


def delete_customer_face(cif_number: str) -> bool:
    """Xóa dữ liệu khuôn mặt của một khách hàng."""
    try:
        cif_clean = str(cif_number).strip().upper()
        get_database()["customer_faces"].delete_one({"cif_number": cif_clean})
        return True
    except Exception as e:
        print(f"⚠️ Lỗi delete_customer_face '{cif_number}': {e}")
        return False


def update_customer_ekyc_status(cif_number: str, status: str = "ENROLLED",
                                 full_name: str = None, segment: str = None) -> bool:
    """Cập nhật trạng thái eKYC sinh trắc học trong dim_customer."""
    try:
        from datetime import datetime
        db = get_database()
        cif_clean = str(cif_number).strip().upper()
        digits = "".join(filter(str.isdigit, cif_clean))
        num_id = int(digits) if digits else None

        filters = [{"cif_number": cif_clean}]
        if num_id is not None:
            filters += [{"customer_id": num_id}, {"cif_number": f"CIF{num_id:07d}"}]

        update_fields: dict = {"kyc_biometric_status": status, "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
        if full_name:
            update_fields["full_name"] = full_name
        if segment:
            update_fields["segment"] = segment

        db["dim_customer"].update_many({"$or": filters}, {"$set": update_fields})
        return True
    except Exception as e:
        print(f"⚠️ Lỗi update_customer_ekyc_status: {e}")
        return False


# ─── Business CRUD Operations ─────────────────────────────────────────────────

def add_transaction(txn_data: dict) -> dict:
    """Thêm giao dịch mới vào factTransaction và purchase_history."""
    try:
        from datetime import datetime
        db = get_database()

        cif_raw = str(txn_data.get("cif_number", "")).strip()
        digits = "".join(filter(str.isdigit, cif_raw))
        cid = int(digits) if digits else 1
        cif_formatted = f"CUST_{cid:04d}"
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        amt = float(txn_data.get("amount", 0.0))
        service_name = txn_data.get("service_name", "Giao dịch tại quầy")
        service_group = txn_data.get("service_group", "Dịch vụ ngân hàng")
        channel = txn_data.get("channel", "QUẦY")
        cust_name = txn_data.get("customer_name", f"Khách hàng {cif_formatted}")
        segment = txn_data.get("segment", "MASS")

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
            "status": "SUCCESS",
        }
        db["factTransaction"].insert_one(fact_doc)

        ph_doc = {
            "reviewerID": cif_formatted,
            "reviewerName": cust_name,
            "segment": segment,
            "category": service_group,
            "title": service_name,
            "brand": "VPBank Financial",
            "price": f"{amt:,.0f} VND",
            "channel": channel,
            "transaction_time": now_str,
        }
        db["purchase_history"].insert_one(ph_doc)

        if any(k in service_name.lower() for k in ["nộp tiền", "tiết kiệm", "tiền gửi"]):
            db["dim_customer"].update_one(
                {"$or": [{"customer_id": cid}, {"cif_number": cif_formatted}]},
                {"$inc": {"casa_balance": amt}, "$set": {"updated_at": now_str}},
            )

        return {"success": True, "message": f"Đã ghi nhận thành công giao dịch #{next_tid}!", "data": ph_doc}
    except Exception as e:
        print(f"⚠️ Lỗi add_transaction: {e}")
        return {"success": False, "message": f"Lỗi: {str(e)}"}


def create_customer(cust_data: dict) -> dict:
    """Tạo mới hồ sơ khách hàng vào dim_customer và khởi tạo dữ liệu ban đầu."""
    try:
        from datetime import datetime
        db = get_database()

        last_cust = db["dim_customer"].find_one({}, sort=[("customer_id", -1)])
        next_cid = (last_cust.get("customer_id", 0) + 1) if last_cust else 121
        cif_formatted = f"CUST_{next_cid:04d}"
        cif_standard = f"CIF{next_cid:07d}"
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        full_name = cust_data.get("full_name", "").strip()
        segment = cust_data.get("segment", "MASS").upper()
        casa = float(cust_data.get("casa_balance", 1_000_000.0))

        new_doc = {
            "customer_id": next_cid,
            "cif_number": cif_standard,
            "cif_code": cif_formatted,
            "full_name": full_name,
            "date_of_birth": cust_data.get("date_of_birth", "1995-01-01"),
            "gender": cust_data.get("gender", "M"),
            "id_number": cust_data.get("id_number", "001099000000"),
            "phone_number": cust_data.get("phone_number", "0900000000"),
            "email": cust_data.get("email", f"cust_{next_cid}@rinrec.fintech.vn"),
            "address": cust_data.get("address", "Hà Nội"),
            "occupation": cust_data.get("occupation", "Nhân viên văn phòng"),
            "income_range": cust_data.get("income_range", "20-40tr"),
            "marital_status": cust_data.get("marital_status", "Độc thân"),
            "segment": segment,
            "customer_since": datetime.now().strftime("%Y-%m-%d"),
            "home_branch_code": cust_data.get("branch_code", "CN001"),
            "kyc_biometric_status": cust_data.get("kyc_biometric_status", "PENDING"),
            "casa_balance": casa,
            "total_asset_value": casa,
            "churn_risk_score": 0.15,
            "updated_at": now_str,
        }
        db["dim_customer"].insert_one(new_doc)

        # Giao dịch kích hoạt tài khoản đầu tiên
        db["purchase_history"].insert_one({
            "reviewerID": cif_formatted,
            "reviewerName": full_name,
            "segment": segment,
            "category": "A. Tài khoản & Thông tin KH",
            "title": "Mở mới tài khoản thanh toán CASA & Kích hoạt eKYC",
            "brand": "VPBank Financial",
            "price": f"{casa:,.0f} VND",
            "channel": "QUẦY",
            "transaction_time": now_str,
        })

        # Gợi ý sản phẩm mặc định theo phân khúc
        _seed_default_recommendations(db, cif_formatted, full_name, segment)

        return {
            "success": True,
            "message": f"Tạo khách hàng thành công! Mã CIF: {cif_formatted}",
            "cif": cif_formatted,
            "customer_id": next_cid,
        }
    except Exception as e:
        print(f"⚠️ Lỗi create_customer: {e}")
        return {"success": False, "message": f"Lỗi: {str(e)}", "cif": None}


def _seed_default_recommendations(db, cif_formatted: str, full_name: str, segment: str):
    """Khởi tạo danh sách đề xuất mặc định theo phân khúc."""
    seg = segment.upper()
    if seg == "DIAMOND":
        recs = [
            ("SP010", "Gói Tài Khoản VPBank Diamond VIP", "Phân khúc", "0 VND", "Miễn phí quản lý", "Đặc quyền phòng chờ VIP, RM riêng", "98%"),
            ("SP008", "Tiết Kiệm Tích Lũy Bậc Thang VIP", "Tiết kiệm", "500,000,000 VND", "6.8%/năm", "Tối đa hóa lợi nhuận", "95%"),
            ("SP006", "Bảo Hiểm Liên Kết Đầu Tư Diamond", "Bảo hiểm", "50,000,000 VND", "Phí định kỳ", "Bảo vệ & sinh lời kép", "92%"),
            ("SP001", "Thẻ Tín Dụng VPBank Priority World", "Thẻ", "Hạn mức 500tr", "45 ngày 0%", "Hoàn tiền quốc tế & sân golf", "90%"),
            ("SP009", "Dịch Vụ Ngoại Tệ & Kiều Hối VIP", "Ngoại tệ", "Theo nhu cầu", "Ưu đãi 20 điểm", "Chuyển tiền 24/7 ưu tiên", "88%"),
        ]
    elif seg == "PRIME":
        recs = [
            ("SP010", "Gói Hội Viên VPBank Prime Priority", "Phân khúc", "0 VND", "Miễn phí", "Miễn phí chuyển khoản, hoàn tiền thẻ", "97%"),
            ("SP001", "Thẻ Tín Dụng VPBank Step Up Cashback", "Thẻ", "Hạn mức 100tr", "45 ngày 0%", "Hoàn 15% mua sắm online", "94%"),
            ("SP008", "Tiết Kiệm Trực Tuyến Prime Rate", "Tiết kiệm", "20,000,000 VND", "6.2%/năm", "+0.3% lãi suất trên VPBank NEO", "91%"),
            ("SP002", "Gói Vay Tiêu Dùng Tín Chấp Prime", "Vay", "Hạn mức 200tr", "Từ 9.9%/năm", "Giải ngân 5 phút qua app", "89%"),
            ("SP006", "Bảo Hiểm Sức Khỏe CarePlus", "Bảo hiểm", "5,000,000 VND", "Phí năm", "Bảo lãnh 300+ bệnh viện quốc tế", "86%"),
        ]
    else:  # MASS
        recs = [
            ("SP001", "Thẻ Thanh Toán VPBank NEO Mastercard", "Thẻ", "0 VND", "Miễn phí trọn đời", "Rút tiền miễn phí mọi ATM", "96%"),
            ("SP008", "Tiết Kiệm Gửi Góp EasySave", "Tiết kiệm", "1,000,000 VND", "5.8%/năm", "Tự động trích tiền gửi mỗi tháng", "93%"),
            ("SP002", "Thấu Chi Tài Khoản Online", "Vay", "Hạn mức 30tr", "Theo dư nợ", "Dự phòng chi tiêu cấp bách", "89%"),
            ("SP001", "Thẻ Tín Dụng VPBank Shopee Platinum", "Thẻ", "Hạn mức 50tr", "45 ngày 0%", "Tích điểm Shopee gấp 4 lần", "87%"),
            ("SP006", "Bảo Hiểm Daily Care", "Bảo hiểm", "1,200,000 VND", "Phí năm", "Hỗ trợ 500k/ngày nằm viện", "85%"),
        ]

    docs = [
        {
            "reviewerID": cif_formatted, "reviewerName": full_name, "segment": seg,
            "category": grp, "title": name, "brand": "VPBank Financial",
            "price": lim, "rate_or_fee": rate, "value_proposition": val, "match_score": sc,
        }
        for _, (code, name, grp, lim, rate, val, sc) in enumerate(recs)
    ]
    if docs:
        db["recommendations"].insert_many(docs)


def add_product(prod_data: dict) -> dict:
    """Thêm sản phẩm tài chính mới vào DanhMucSanPham."""
    try:
        db = get_database()
        col = db["DanhMucSanPham"]

        p_code = str(prod_data.get("Ma_SP", "")).strip().upper()
        if not p_code:
            cnt = col.count_documents({}) + 1
            p_code = f"SP{cnt:03d}"

        doc = {
            "Ma_SP": p_code,
            "Nhom": prod_data.get("Nhom", "Tài chính").strip(),
            "Ten_san_pham": prod_data.get("Ten_san_pham", "").strip(),
            "Gia_tri_cot_loi": prod_data.get("Gia_tri_cot_loi", "Giải pháp tài chính tối ưu").strip(),
            "Phan_khuc": prod_data.get("Phan_khuc", "ALL").strip(),
            "So_tien_toi_thieu": float(prod_data.get("So_tien_toi_thieu", 0.0)),
            "Lai_suat_Phi": prod_data.get("Lai_suat_Phi", "Theo biểu phí chuẩn").strip(),
            "Uu_tien": int(prod_data.get("Uu_tien", 5)),
        }
        col.update_one({"Ma_SP": p_code}, {"$set": doc}, upsert=True)
        return {"success": True, "message": f"Đã lưu sản phẩm {doc['Ten_san_pham']} ({p_code})!", "data": doc}
    except Exception as e:
        print(f"⚠️ Lỗi add_product: {e}")
        return {"success": False, "message": f"Lỗi: {str(e)}"}


def log_consultation(log_data: dict) -> dict:
    """Ghi nhật ký tư vấn & chốt hợp đồng vào consultation_logs."""
    try:
        from datetime import datetime
        doc = {
            "cif_number": str(log_data.get("cif_number", "")).strip(),
            "customer_name": log_data.get("customer_name", "Khách hàng"),
            "product_name": log_data.get("product_name", "Sản phẩm tài chính"),
            "category": log_data.get("category", "Tài chính"),
            "status": log_data.get("status", "CHỐT THÀNH CÔNG"),
            "deal_amount": log_data.get("deal_amount", "0 VND"),
            "notes": log_data.get("notes", ""),
            "teller_name": log_data.get("teller_name", "Giao dịch viên"),
            "teller_code": log_data.get("teller_code", "GDV001"),
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        get_database()["consultation_logs"].insert_one(doc)
        return {"success": True, "message": "Đã lưu nhật ký tư vấn thành công!", "data": doc}
    except Exception as e:
        print(f"⚠️ Lỗi log_consultation: {e}")
        return {"success": False, "message": f"Lỗi: {str(e)}"}


def get_consultation_logs(cif_number: str = None) -> list:
    """Lấy danh sách nhật ký tư vấn, lọc theo CIF nếu có."""
    try:
        q = {"cif_number": str(cif_number).strip()} if cif_number else {}
        return list(get_database()["consultation_logs"].find(q, {"_id": 0}).sort("created_at", -1))
    except Exception as e:
        print(f"⚠️ Lỗi get_consultation_logs: {e}")
        return []


def test_connection() -> bool:
    """Kiểm tra kết nối và in danh sách collection."""
    try:
        db = get_database()
        cols = db.list_collection_names()
        print(f"✅ Kết nối MongoDB Atlas thành công! DB: '{DB_NAME}'")
        for c in sorted(cols):
            print(f"  - {c}: {db[c].count_documents({})} documents")
        return True
    except Exception as e:
        print(f"❌ Kết nối MongoDB Atlas thất bại: {e}")
        return False


if __name__ == "__main__":
    test_connection()
