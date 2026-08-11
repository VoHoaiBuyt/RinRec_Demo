"""
fintech_data_pipeline.py
Pipeline tiền xử lý dữ liệu, làm sạch và xây dựng đồ thị tương tác chuẩn UltraGCN cho bài toán Gợi ý Sản phẩm Tài chính.
Tương thích với kiến trúc Amazon Recommendation System (MF, NCF, MLP, LightGCN, UltraGCN).
"""
import os
import sys
import json
import numpy as np
import pandas as pd
from collections import defaultdict
from sklearn.preprocessing import LabelEncoder
from datetime import datetime

if sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

from mongo_connector import get_collection_df, save_df_to_collection

def run_data_pipeline():
    print("=" * 70)
    print("🚀 BƯỚC 1: TIỀN XỬ LÝ DỮ LIỆU & XÂY DỰNG ĐỒ THỊ TƯƠNG TÁC FINTECH (MONGODB ATLAS)")
    print("=" * 70)
    
    # 1. Đọc các bảng dữ liệu trực tiếp từ MongoDB Atlas
    print("📡 Đang tải dữ liệu từ MongoDB Atlas (RinRec_DB)...")
    df_customers = get_collection_df("dim_customer")
    df_products = get_collection_df("DanhMucSanPham")
    df_services = get_collection_df("DanhMucDichVu")
    df_transactions = get_collection_df("factTransaction")
    df_holdings = get_collection_df("factCustomerProduct")
    df_rules = get_collection_df("RuleGoiY")
    
    if df_customers.empty or df_transactions.empty:
        raise RuntimeError("❌ Không thể tải dữ liệu từ MongoDB Atlas. Vui lòng kiểm tra kết nối mạng và tài khoản Atlas trong mongo_connector.py.")
    
    print(f"✅ Khách hàng: {len(df_customers)} | Sản phẩm: {len(df_products)} | Dịch vụ: {len(df_services)} | Giao dịch: {len(df_transactions)}")
    
    # 2. Xây dựng bảng Customer Interaction History (tương đương purchase_history.csv)
    history_records = []
    for _, row in df_transactions.iterrows():
        c_id = row["customer_id"]
        cust = df_customers[df_customers["customer_id"] == c_id].iloc[0]
        cif_str = f"CUST_{int(c_id):04d}" if isinstance(c_id, (int, np.integer)) or str(c_id).isdigit() else str(c_id)
        history_records.append({
            "customer_id": c_id,
            "reviewerID": cif_str,
            "customer_name": cust["full_name"],
            "reviewerName": cust["full_name"],
            "segment": cust["segment"],
            "phone_number": cust["phone_number"],
            "service_code": row["service_code"],
            "service_name": row["service_name"],
            "title": row["service_name"],
            "service_group": row["service_group"],
            "category": row["service_group"],
            "brand": "VPBank Financial",
            "amount": f"{row['amount']:,.0f} VND",
            "price": f"{row['amount']:,.0f} VND",
            "raw_amount": float(row["amount"]),
            "channel": row["channel"],
            "transaction_time": row["transaction_datetime"]
        })
        
    df_history = pd.DataFrame(history_records)
    
    # 3. Mapping tương tác User - Product
    # Mapping từ Nhóm Dịch vụ sang Sản phẩm mục tiêu
    service_group_to_product = {
        "A. Tài khoản & Thông tin KH": "SP024",
        "B. Giao dịch tiền mặt": "SP004",
        "C. Tiết kiệm & Tiền gửi": "SP001",
        "D. Thẻ": "SP004",
        "E. Chuyển tiền & Thanh toán": "SP021",
        "F. Ngoại tệ": "SP018",
        "G. Tín dụng": "SP008",
        "H. Bảo hiểm & Đầu tư": "SP013",
        "I. Ngân hàng số & Hỗ trợ": "SP021",
        "J. Khách hàng doanh nghiệp": "SP025"
    }
    
    interactions = []
    # Từ Holdings (sở hữu thực tế)
    for _, row in df_holdings.iterrows():
        c_id = row["customer_id"]
        p_id = row["product_id"]
        bal = float(row.get("current_balance", 10_000_000))
        rating = 4.5 + min(0.5, np.log10(max(1, bal)) / 10.0)
        interactions.append({
            "customer_id": c_id,
            "product_id": p_id,
            "rating": rating,
            "amount": bal,
            "source": "HOLDING"
        })
        
    # Từ Transactions (hành vi chi tiêu)
    for _, row in df_transactions.iterrows():
        c_id = row["customer_id"]
        s_grp = str(row["service_group"])
        p_id = service_group_to_product.get(s_grp, "SP001")
        amt = float(row.get("amount", 1_000_000))
        rating = min(4.5, 1.0 + (np.log1p(amt) / 18.0) * 3.5)
        interactions.append({
            "customer_id": c_id,
            "product_id": p_id,
            "rating": rating,
            "amount": amt,
            "source": "TRANSACTION"
        })
        
    df_inter = pd.DataFrame(interactions)
    df_grouped = df_inter.groupby(["customer_id", "product_id"]).agg({
        "rating": "mean",
        "amount": "sum"
    }).reset_index()
    
    # 4. Label Encoding
    user_encoder = LabelEncoder()
    item_encoder = LabelEncoder()
    
    df_grouped["user_idx"] = user_encoder.fit_transform(df_grouped["customer_id"])
    df_grouped["item_idx"] = item_encoder.fit_transform(df_grouped["product_id"])
    
    num_users = len(user_encoder.classes_)
    num_items = len(item_encoder.classes_)
    print(f"👥 Số lượng Khách hàng (User nodes): {num_users} | Sản phẩm (Item nodes): {num_items}")
    
    # 5. Tính bậc node và Trọng số cạnh UltraGCN
    user_freq = defaultdict(int)
    item_freq = defaultdict(int)
    
    for row in df_grouped.itertuples():
        user_freq[row.user_idx] += 1
        item_freq[row.item_idx] += 1
        
    df_grouped["edge_weight"] = df_grouped.apply(
        lambda r: 1.0 / ((user_freq[r.user_idx]**0.5) * (item_freq[r.item_idx]**0.5)), axis=1
    )
    
    # Lưu bảng tương tác và lịch sử vào MongoDB
    save_df_to_collection("processed_interactions", df_grouped)
    save_df_to_collection("purchase_history", df_history)
    print(f"✅ Đã lưu {len(df_grouped)} cạnh tương tác vào MongoDB collection 'processed_interactions'.")
    print(f"✅ Đã lưu {len(df_history)} lịch sử tương tác vào MongoDB collection 'purchase_history'.")
    
    print("🎉 Hoàn tất Pipeline tiền xử lý dữ liệu!")
    return df_grouped, df_history, df_products, df_customers

if __name__ == "__main__":
    run_data_pipeline()
