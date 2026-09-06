# -*- coding: utf-8 -*-
"""
frontend/app/main_5tabs.py
RinRec SmartAdvisor 360 - Giao diện 5 tabs theo thiết kế FELIX.

Tabs:
  1. TỔNG QUAN KHÁCH HÀNG (Customer 360)
  2. LỊCH SỬ GIAO DỊCH
  3. VAY VỐN & THÔNG TIN CIC
  4. ĐỀ XUẤT SẢN PHẨM (AI Recommendation)
  5. GHI NHẬN TƯ VẤN (CRM)
"""
import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIG & SETUP
# ═══════════════════════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="VPBank SmartAdvisor 360",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded"
)

API_BASE = "http://localhost:8000/api/v1"

# CSS Responsive + Glassmorphism
st.markdown("""
<style>
/* Global responsive container */
.main .block-container {
    max-width: 100%;
    padding: 1rem 2rem;
}

/* KPI Banner */
.kpi-banner {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 1rem;
    margin-bottom: 1.5rem;
}
.kpi-card {
    background: linear-gradient(135deg, rgba(99, 102, 241, 0.1), rgba(168, 85, 247, 0.1));
    border-radius: 12px;
    padding: 1rem;
    border: 1px solid rgba(99, 102, 241, 0.2);
}
.kpi-value {
    font-size: 1.8rem;
    font-weight: 700;
    color: #6366f1;
}
.kpi-label {
    font-size: 0.85rem;
    color: #64748b;
    margin-top: 0.25rem;
}

/* Badge */
.badge {
    display: inline-block;
    padding: 0.25rem 0.75rem;
    border-radius: 12px;
    font-size: 0.75rem;
    font-weight: 600;
}
.badge-mass { background: #dbeafe; color: #1e40af; }
.badge-prime { background: #fef3c7; color: #92400e; }
.badge-diamond { background: #f3e8ff; color: #6b21a8; }
.badge-success { background: #d1fae5; color: #065f46; }
.badge-danger { background: #fee2e2; color: #991b1b; }

/* Product Card */
.product-card {
    background: white;
    border: 1px solid #e5e7eb;
    border-radius: 12px;
    padding: 1.25rem;
    margin-bottom: 1rem;
    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    transition: transform 0.2s;
}
.product-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 8px rgba(0,0,0,0.15);
}
.product-title {
    font-size: 1.1rem;
    font-weight: 600;
    color: #1f2937;
    margin-bottom: 0.5rem;
}
.match-score {
    font-size: 1.5rem;
    font-weight: 700;
    color: #10b981;
}
.script-box {
    background: #f9fafb;
    border-left: 3px solid #6366f1;
    padding: 0.75rem;
    margin: 0.75rem 0;
    font-style: italic;
    color: #374151;
}

/* Responsive: mobile */
@media (max-width: 768px) {
    .main .block-container { padding: 0.5rem 1rem; }
    .kpi-banner { grid-template-columns: 1fr 1fr; gap: 0.75rem; }
    .kpi-value { font-size: 1.4rem; }
    .product-card { padding: 1rem; }
}
</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def api_get(endpoint: str, params: Optional[Dict] = None) -> Optional[Dict]:
    """Call API GET with token."""
    token = st.session_state.get("access_token")
    if not token:
        st.error("Vui lòng đăng nhập")
        return None
    
    headers = {"Authorization": f"Bearer {token}"}
    try:
        resp = requests.get(f"{API_BASE}{endpoint}", headers=headers, params=params, timeout=10)
        if resp.status_code == 200:
            return resp.json()
        elif resp.status_code == 401:
            st.error("Token hết hạn, vui lòng đăng nhập lại")
            return None
        else:
            st.error(f"API Error: {resp.status_code}")
            return None
    except Exception as e:
        st.error(f"Lỗi kết nối API: {e}")
        return None

def api_post(endpoint: str, data: Dict) -> Optional[Dict]:
    """Call API POST with token."""
    token = st.session_state.get("access_token")
    if not token:
        st.error("Vui lòng đăng nhập")
        return None
    
    headers = {"Authorization": f"Bearer {token}"}
    try:
        resp = requests.post(f"{API_BASE}{endpoint}", headers=headers, json=data, timeout=10)
        if resp.status_code in (200, 201):
            return resp.json()
        else:
            st.error(f"API Error: {resp.status_code} - {resp.text}")
            return None
    except Exception as e:
        st.error(f"Lỗi kết nối API: {e}")
        return None

def format_currency(amount: float) -> str:
    """Format number as VND currency."""
    return f"{amount:,.0f} ₫".replace(",", ".")

def segment_badge(segment: str) -> str:
    """Return HTML badge for customer segment."""
    badge_class = {
        "MASS": "badge-mass",
        "PRIME": "badge-prime",
        "DIAMOND": "badge-diamond"
    }.get(segment, "badge-mass")
    return f'<span class="badge {badge_class}">{segment}</span>'

# ═══════════════════════════════════════════════════════════════════════════════
# SIDEBAR - LOGIN & CIF SELECTOR
# ═══════════════════════════════════════════════════════════════════════════════

with st.sidebar:
    st.image("https://via.placeholder.com/200x60/6366f1/ffffff?text=VPBank", width=200)
    st.title("SmartAdvisor 360")
    
    # Login form
    if "access_token" not in st.session_state:
        st.subheader("Đăng nhập")
        username = st.text_input("Tên đăng nhập")
        password = st.text_input("Mật khẩu", type="password")
        if st.button("Đăng nhập", use_container_width=True):
            resp = requests.post(f"{API_BASE}/auth/login", json={"username": username, "password": password})
            if resp.status_code == 200:
                data = resp.json()
                st.session_state["access_token"] = data["access_token"]
                st.session_state["user"] = data["user"]
                st.success("Đăng nhập thành công!")
                st.rerun()
            else:
                st.error("Đăng nhập thất bại")
        st.stop()
    
    # User info
    user = st.session_state.get("user", {})
    st.success(f"👤 {user.get('full_name', 'User')}")
    st.caption(f"Vai trò: {user.get('role', 'N/A')}")
    
    if st.button("Đăng xuất", use_container_width=True):
        st.session_state.clear()
        st.rerun()
    
    st.divider()
    
    # CIF Selector
    st.subheader("Chọn khách hàng")
    cif = st.text_input("Nhập CIF", value="CUST_0001")
    st.session_state["selected_cif"] = cif
    
    # Quick search
    st.caption("Hoặc tìm nhanh:")
    search_name = st.text_input("Tên khách hàng", key="search_customer")
    if search_name:
        # TODO: search API
        st.info(f"Tìm kiếm: {search_name}")

# ═══════════════════════════════════════════════════════════════════════════════
# MAIN CONTENT - 5 TABS
# ═══════════════════════════════════════════════════════════════════════════════

cif = st.session_state.get("selected_cif", "CUST_0001")

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Tổng quan KH",
    "💳 Lịch sử GD",
    "💰 Vay vốn & CIC",
    "🎯 Đề xuất SP",
    "📝 Ghi nhận tư vấn"
])

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 1: TỔNG QUAN KHÁCH HÀNG (Customer 360)
# ═══════════════════════════════════════════════════════════════════════════════

with tab1:
    st.header("📊 Tổng quan Khách hàng")
    
    customer_data = api_get(f"/customers/{cif}")
    
    if customer_data:
        # KPI Banner
        st.markdown('<div class="kpi-banner">', unsafe_allow_html=True)
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-value">{format_currency(customer_data.get('aum', 0))}</div>
                <div class="kpi-label">Tổng tài sản (AUM)</div>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-value">{format_currency(customer_data.get('total_debt', 0))}</div>
                <div class="kpi-label">Tổng dư nợ</div>
            </div>
            """, unsafe_allow_html=True)
        with col3:
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-value">{format_currency(customer_data.get('pre_approved_limit', 0))}</div>
                <div class="kpi-label">Hạn mức pre-approved</div>
            </div>
            """, unsafe_allow_html=True)
        with col4:
            credit_score = customer_data.get('credit_score', 'N/A')
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-value">{credit_score}</div>
                <div class="kpi-label">Điểm tín nhiệm</div>
            </div>
            """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Customer info
        st.subheader("Thông tin định danh")
        col1, col2 = st.columns([2, 1])
        with col1:
            st.markdown(f"**Họ tên:** {customer_data.get('full_name', 'N/A')}")
            st.markdown(f"**CIF:** {cif}")
            segment = customer_data.get('segment', 'MASS')
            st.markdown(f"**Phân khúc:** {segment_badge(segment)}", unsafe_allow_html=True)
        with col2:
            ekyc_status = customer_data.get('ekyc_verified', False)
            badge_class = "badge-success" if ekyc_status else "badge-danger"
            badge_text = "Đã xác thực" if ekyc_status else "Chưa xác thực"
            st.markdown(f'**eKYC:** <span class="badge {badge_class}">{badge_text}</span>', unsafe_allow_html=True)
        
        # Behavior & needs
        st.subheader("Hành vi & Nhu cầu")
        fav_channel = customer_data.get('favorite_channel', 'Mobile Banking')
        st.markdown(f"**Kênh ưa chuộng:** {fav_channel}")
        
        # Channel usage (simple progress bars)
        channels = customer_data.get('channel_usage', {
            'Mobile': 65, 'ATM': 25, 'Branch': 10
        })
        for ch, pct in channels.items():
            st.progress(pct / 100, text=f"{ch}: {pct}%")
        
        st.markdown(f"**Trọng tâm nhu cầu:** {customer_data.get('primary_need', 'Tiết kiệm & Đầu tư')}")
        st.caption(f"Ghi chú gần nhất: {customer_data.get('recent_note', 'Khách hàng quan tâm đến thẻ tín dụng')}")
    else:
        st.warning(f"Không tìm thấy thông tin khách hàng {cif}")

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 2: LỊCH SỬ GIAO DỊCH
# ═══════════════════════════════════════════════════════════════════════════════

with tab2:
    st.header("💳 Lịch sử Giao dịch")
    
    # Filter bar
    col1, col2, col3 = st.columns(3)
    with col1:
        date_range = st.selectbox("Khoảng thời gian", ["7 ngày", "30 ngày", "90 ngày", "Tùy chọn"])
        if date_range == "Tùy chọn":
            from_date = st.date_input("Từ ngày")
            to_date = st.date_input("Đến ngày")
        else:
            days = int(date_range.split()[0])
            from_date = datetime.now() - timedelta(days=days)
            to_date = datetime.now()
    with col2:
        service_type = st.selectbox("Phân loại dịch vụ", ["Tất cả", "Tiết kiệm", "Chuyển tiền", "Thanh toán", "Ngoại tệ"])
    with col3:
        cash_flow = st.selectbox("Trạng thái", ["Tất cả", "Tiền vào", "Tiền ra"])
    
    # Fetch transactions
    params = {
        "cif": cif,
        "from": from_date.strftime("%Y-%m-%d") if isinstance(from_date, datetime) else str(from_date),
        "to": to_date.strftime("%Y-%m-%d") if isinstance(to_date, datetime) else str(to_date),
        "type": service_type if service_type != "Tất cả" else None
    }
    txn_data = api_get("/transactions", params=params)
    
    if txn_data and isinstance(txn_data, list):
        # Convert to DataFrame
        df = pd.DataFrame(txn_data)
        if not df.empty:
            # Format columns
            df['Số tiền'] = df['amount'].apply(lambda x: format_currency(x) if pd.notna(x) else "")
            df['Thời gian'] = pd.to_datetime(df['transaction_date']).dt.strftime("%d/%m/%Y %H:%M")
            
            # Display table
            st.dataframe(df[['Thời gian', 'transaction_type', 'Số tiền', 'status']], use_container_width=True)
        else:
            st.info("Không có giao dịch trong khoảng thời gian này")
    else:
        st.info("Không có dữ liệu giao dịch")

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 3: VAY VỐN & THÔNG TIN CIC
# ═══════════════════════════════════════════════════════════════════════════════

with tab3:
    st.header("💰 Vay vốn & Thông tin CIC")
    
    # Loans
    st.subheader("Lịch sử vay nội bộ")
    loan_data = api_get(f"/customers/{cif}/loans")
    
    if loan_data and isinstance(loan_data, list):
        for loan in loan_data:
            with st.expander(f"📄 {loan.get('loan_type', 'Vay tiêu dùng')} - {loan.get('loan_id', 'N/A')}"):
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Số tiền", format_currency(loan.get('amount', 0)))
                with col2:
                    st.metric("Dư nợ", format_currency(loan.get('outstanding', 0)))
                with col3:
                    st.metric("Lãi suất", f"{loan.get('interest_rate', 0)}%/năm")
                
                st.markdown(f"**Kỳ hạn:** {loan.get('term', 'N/A')} tháng")
                st.markdown(f"**Giải ngân:** {loan.get('disbursement_date', 'N/A')}")
                status = loan.get('status', 'ACTIVE')
                badge = "badge-success" if status == "ACTIVE" else "badge-danger"
                st.markdown(f'**Trạng thái:** <span class="badge {badge}">{status}</span>', unsafe_allow_html=True)
    else:
        st.info("Không có khoản vay nội bộ")
    
    st.divider()
    
    # CIC
    st.subheader("Thông tin CIC")
    cic_data = api_get(f"/customers/{cif}/cic")
    
    if cic_data:
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"**Ngày cập nhật:** {cic_data.get('updated_date', 'N/A')}")
            st.markdown(f"**Số TCTD cấp tín dụng:** {cic_data.get('num_institutions', 0)}")
            st.markdown(f"**Tổng dư nợ:** {format_currency(cic_data.get('total_debt', 0))}")
        with col2:
            debt_group = cic_data.get('debt_group', 1)
            badge = "badge-success" if debt_group <= 2 else "badge-danger"
            st.markdown(f'**Nhóm nợ:** <span class="badge {badge}">Nhóm {debt_group}</span>', unsafe_allow_html=True)
            if debt_group >= 3:
                st.warning("⚠️ Cảnh báo: Nhóm nợ >= 3")
            
            bad_debt_history = cic_data.get('bad_debt_history', [])
            if bad_debt_history:
                st.markdown("**Lịch sử nợ xấu:**")
                for bd in bad_debt_history:
                    st.caption(f"- {bd}")
    else:
        st.info("Chưa có thông tin CIC")

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 4: ĐỀ XUẤT SẢN PHẨM (AI RECOMMENDATION)
# ═══════════════════════════════════════════════════════════════════════════════

with tab4:
    st.header("🎯 Đề xuất Sản phẩm (AI)")
    
    # Search & filter
    col1, col2 = st.columns([3, 1])
    with col1:
        search_product = st.text_input("🔍 Tìm kiếm sản phẩm", key="search_product")
    with col2:
        filter_category = st.selectbox("Danh mục", ["Tất cả", "Credit Card", "Loan", "Savings", "Insurance"])
    
    # Fetch recommendations
    rec_data = api_get(f"/recommendations/{cif}")
    
    if rec_data and isinstance(rec_data.get('recommendations'), list):
        recs = rec_data['recommendations']
        
        for idx, rec in enumerate(recs[:5]):  # Top 5
            st.markdown(f"""
            <div class="product-card">
                <div class="product-title">{rec.get('product_name', 'Sản phẩm')}</div>
                <span class="badge badge-mass">{rec.get('category', 'N/A')}</span>
                <div style="margin-top:0.75rem;">
                    <span class="match-score">{rec.get('match_score', 0):.1f}%</span>
                    <span style="color:#6b7280; font-size:0.85rem;"> độ phù hợp</span>
                </div>
                <div style="margin-top:0.5rem; color:#374151;">
                    <strong>Thông số:</strong> {rec.get('specs', 'Hạn mức: 500tr, Lãi suất: 0.99%/tháng')}
                </div>
                <div style="margin-top:0.5rem; color:#374151;">
                    <strong>Giá trị:</strong> {rec.get('value_proposition', 'Tiết kiệm lên đến 30% chi phí vay')}
                </div>
                <div class="script-box">
                    <strong>💬 Script tư vấn:</strong><br>
                    {rec.get('script', 'Khách hàng có thể vay nhanh chóng với lãi suất ưu đãi, phù hợp với nhu cầu hiện tại.')}
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Action buttons
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("✅ Chốt đơn", key=f"close_{idx}"):
                    # Save consultation
                    consult_data = {
                        "cif": cif,
                        "teller_id": user.get('username'),
                        "recommended_products": [rec.get('product_id')],
                        "consultation_date": datetime.now().isoformat(),
                        "result": "PENDING",
                        "notes": f"Gợi ý từ AI: {rec.get('product_name')}"
                    }
                    result = api_post("/consultations", consult_data)
                    if result:
                        st.success("Đã ghi nhận tư vấn!")
            with col2:
                if st.button("📱 Gửi App", key=f"send_{idx}"):
                    st.info("Đã gửi thông tin sản phẩm qua App khách hàng")
            with col3:
                if st.button("📋 Mở hồ sơ", key=f"open_{idx}"):
                    st.info("Chuyển đến form nhập hồ sơ sản phẩm")
            
            st.divider()
    else:
        st.warning("Không có gợi ý sản phẩm cho khách hàng này")

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 5: GHI NHẬN TƯ VẤN (CRM)
# ═══════════════════════════════════════════════════════════════════════════════

with tab5:
    st.header("📝 Ghi nhận Tư vấn")
    
    with st.form("consultation_form"):
        st.subheader("Tạo ghi nhận mới")
        
        # Products (multi-select)
        products_list = ["PROD_001 - Thẻ tín dụng", "PROD_002 - Vay tiêu dùng", "PROD_003 - Tiết kiệm", "PROD_004 - Bảo hiểm"]
        selected_products = st.multiselect("Sản phẩm đã tư vấn", products_list)
        
        # Date
        consultation_date = st.date_input("Ngày tư vấn", datetime.now())
        
        # Customer response
        customer_response = st.radio(
            "Phản hồi khách hàng",
            ["Đồng ý", "Quan tâm cần suy nghĩ", "Từ chối"]
        )
        
        # Follow-up (if interested)
        if customer_response == "Quan tâm cần suy nghĩ":
            followup_date = st.date_input("Ngày hẹn tái tư vấn")
            followup_channel = st.selectbox("Kênh liên hệ lại", ["Điện thoại", "Email", "SMS", "Zalo"])
        
        # Notes
        notes = st.text_area("Ghi chú nội dung trao đổi", height=100)
        
        # Submit
        col1, col2 = st.columns(2)
        with col1:
            submitted = st.form_submit_button("💾 Lưu ghi nhận", use_container_width=True)
        with col2:
            add_calendar = st.form_submit_button("📅 Thêm vào lịch", use_container_width=True)
        
        if submitted:
            # Prepare data
            result_map = {
                "Đồng ý": "ACCEPTED",
                "Quan tâm cần suy nghĩ": "PENDING",
                "Từ chối": "REJECTED"
            }
            
            consult_data = {
                "cif": cif,
                "teller_id": user.get('username'),
                "recommended_products": [p.split(" - ")[0] for p in selected_products],
                "consultation_date": consultation_date.isoformat(),
                "result": result_map[customer_response],
                "notes": notes
            }
            
            result = api_post("/consultations", consult_data)
            if result:
                st.success("✅ Đã lưu ghi nhận tư vấn!")
            else:
                st.error("Lỗi khi lưu ghi nhận")
        
        if add_calendar:
            st.info("📅 Đã thêm sự kiện vào lịch (tính năng đang phát triển)")
    
    st.divider()
    
    # Consultation history
    st.subheader("Lịch sử tư vấn")
    consult_history = api_get("/consultations", params={"cif": cif})
    
    if consult_history and isinstance(consult_history, list):
        for cons in consult_history[:10]:  # Show latest 10
            with st.expander(f"📅 {cons.get('consultation_date', 'N/A')} - {cons.get('result', 'N/A')}"):
                st.markdown(f"**Teller:** {cons.get('teller_id', 'N/A')}")
                st.markdown(f"**Sản phẩm:** {', '.join(cons.get('recommended_products', []))}")
                st.markdown(f"**Kết quả:** {cons.get('result', 'N/A')}")
                st.caption(f"Ghi chú: {cons.get('notes', 'Không có')}")
    else:
        st.info("Chưa có lịch sử tư vấn")

st.caption("© 2024 VPBank RinRec SmartAdvisor 360 | Powered by UltraGCN AI")
