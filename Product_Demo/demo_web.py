import streamlit as st
import pandas as pd
import numpy as np
import os
import sys
import textwrap

# Đảm bảo root directory luôn có trong sys.path
_root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _root_dir not in sys.path:
    sys.path.insert(0, _root_dir)

# ==============================================================================
# CẤU HÌNH TRANG WEB & THEME GIAO DIỆN CHUẨN DOANH NGHIỆP (ENTERPRISE BANKING)
# ==============================================================================
st.set_page_config(
    page_title="VPBank SmartAdvisor 360 - Trợ Lý Tư Vấn & Bán Chéo Thông Minh",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS giao diện ngân hàng cao cấp
st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

.top-brand-bar {
    background: linear-gradient(135deg, #0A2540 0%, #0D3866 50%, #00B14F 100%);
    padding: 1.2rem 1.8rem;
    border-radius: 14px;
    color: white !important;
    margin-bottom: 1.5rem;
    box-shadow: 0 10px 25px -5px rgba(10, 37, 64, 0.25);
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
}
.top-brand-bar * {
    color: white !important;
}
.top-brand-title {
    font-size: 1.6rem;
    font-weight: 800;
    letter-spacing: -0.5px;
    display: flex;
    align-items: center;
    gap: 10px;
}
.top-brand-sub {
    font-size: 0.95rem;
    color: #E2E8F0 !important;
    margin-top: 4px;
    font-weight: 500;
}
.top-badge-live {
    background: rgba(0, 177, 79, 0.2);
    border: 1px solid #00B14F;
    color: #34D399 !important;
    padding: 0.35rem 0.8rem;
    border-radius: 20px;
    font-size: 0.85rem;
    font-weight: 600;
    display: inline-flex;
    align-items: center;
    gap: 6px;
}

.metric-card {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 12px;
    padding: 1.2rem;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
}
.metric-label {
    font-size: 0.82rem;
    font-weight: 600;
    color: #64748B;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}
.metric-value {
    font-size: 1.6rem;
    font-weight: 800;
    color: #0F172A;
    margin-top: 4px;
}
.metric-note {
    font-size: 0.82rem;
    color: #00B14F;
    font-weight: 600;
    margin-top: 4px;
}

.cust-profile-card {
    background: linear-gradient(135deg, #FFFFFF 0%, #F8FAFC 100%);
    border: 1px solid #CBD5E1;
    border-radius: 14px;
    padding: 1.4rem 1.6rem;
    margin-bottom: 1.2rem;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.03);
}

.badge-diamond {
    background: linear-gradient(135deg, #F59E0B 0%, #D97706 100%);
    color: #FFFFFF !important;
    padding: 0.3rem 0.8rem;
    border-radius: 20px;
    font-size: 0.82rem;
    font-weight: 700;
    letter-spacing: 0.5px;
    display: inline-block;
}
.badge-prime {
    background: linear-gradient(135deg, #6366F1 0%, #4F46E5 100%);
    color: #FFFFFF !important;
    padding: 0.3rem 0.8rem;
    border-radius: 20px;
    font-size: 0.82rem;
    font-weight: 700;
    letter-spacing: 0.5px;
    display: inline-block;
}
.badge-mass {
    background: linear-gradient(135deg, #0EA5E9 0%, #0284C7 100%);
    color: #FFFFFF !important;
    padding: 0.3rem 0.8rem;
    border-radius: 20px;
    font-size: 0.82rem;
    font-weight: 700;
    letter-spacing: 0.5px;
    display: inline-block;
}

.nba-card {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-left: 6px solid #00B14F;
    border-radius: 12px;
    padding: 1.2rem 1.4rem;
    margin-bottom: 1rem;
    box-shadow: 0 4px 10px rgba(0, 0, 0, 0.04);
}
.nba-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 0.6rem;
}
.nba-title {
    font-size: 1.15rem;
    font-weight: 700;
    color: #0A2540;
}
.nba-match {
    background: #ECFDF5;
    border: 1px solid #A7F3D0;
    color: #047857;
    padding: 0.25rem 0.65rem;
    border-radius: 20px;
    font-weight: 700;
    font-size: 0.85rem;
    display: inline-flex;
    align-items: center;
    gap: 4px;
}
.nba-details {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    gap: 8px;
    margin: 0.6rem 0;
    background: #F8FAFC;
    padding: 0.6rem 0.8rem;
    border-radius: 8px;
    font-size: 0.86rem;
    color: #334155;
}
.nba-value {
    color: #1E293B;
    font-size: 0.9rem;
    margin: 0.5rem 0;
    line-height: 1.45;
}
.nba-script {
    background: #EFF6FF;
    border-left: 3px solid #3B82F6;
    border-radius: 6px;
    padding: 0.7rem 0.9rem;
    color: #1E40AF;
    font-size: 0.88rem;
    margin-top: 0.6rem;
}
.nba-script-tag {
    font-weight: 700;
    color: #1D4ED8;
    font-size: 0.8rem;
    text-transform: uppercase;
    display: block;
    margin-bottom: 3px;
}

.signal-pill {
    font-size: 0.82rem;
    font-weight: 600;
    padding: 0.3rem 0.75rem;
    border-radius: 20px;
    display: inline-block;
    margin-right: 6px;
    margin-bottom: 6px;
}
.signal-pill-vip {
    background: #FEF3C7;
    border: 1px solid #FCD34D;
    color: #92400E;
}
.signal-pill-need {
    background: #EFF6FF;
    border: 1px solid #BFDBFE;
    color: #1E40AF;
}
.signal-pill-opp {
    background: #ECFDF5;
    border: 1px solid #A7F3D0;
    color: #065F46;
}
.signal-pill-chan {
    background: #F3E8FF;
    border: 1px solid #DDD6FE;
    color: #6B21A8;
}
.signal-pill-recent {
    background: #F1F5F9;
    border: 1px solid #CBD5E1;
    color: #334155;
}

/* AI Smart Counter & Cross-Device eKYC CSS */
.ekyc-card-box {
    background: linear-gradient(135deg, #0A2540 0%, #0F3862 100%);
    border: 1px solid #00B14F;
    border-radius: 16px;
    padding: 1.4rem 1.6rem;
    color: white !important;
    margin-bottom: 1.2rem;
    box-shadow: 0 10px 25px -5px rgba(0, 177, 79, 0.2);
}
.ekyc-card-box * {
    color: white !important;
}
.ekyc-qr-container {
    background: #FFFFFF;
    padding: 1rem;
    border-radius: 14px;
    display: inline-flex;
    flex-direction: column;
    align-items: center;
    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
}
.cust-face-portrait {
    width: 100px;
    height: 120px;
    border-radius: 12px;
    object-fit: cover;
    border: 2.5px solid #00B14F;
    box-shadow: 0 4px 12px rgba(0, 177, 79, 0.25);
}
.ekyc-verified-badge {
    background: rgba(0, 177, 79, 0.2);
    border: 1px solid #00B14F;
    color: #34D399 !important;
    padding: 0.25rem 0.65rem;
    border-radius: 20px;
    font-size: 0.8rem;
    font-weight: 700;
    display: inline-flex;
    align-items: center;
    gap: 4px;
}
</style>""", unsafe_allow_html=True)

# Helper render HTML an toàn không bị dính thụt dòng Markdown
def render_html(html_str: str):
    if hasattr(st, 'html'):
        st.html(html_str)
    else:
        cleaned = "\n".join(line.strip() for line in html_str.split("\n") if line.strip())
        st.markdown(cleaned, unsafe_allow_html=True)

def generate_personalized_signals(user_records, user_recs):
    """Trích xuất tín hiệu nhu cầu cá nhân hóa thực tế cho từng khách hàng (Tiếng Việt chuẩn, không emoji rườm rà)"""
    signals = []
    
    # 1. Phân khúc khách hàng
    seg = user_records['segment'].iloc[0] if 'segment' in user_records.columns else 'MASS'
    if seg == 'DIAMOND':
        signals.append(('signal-pill-vip', 'PHÂN KHÚC: DIAMOND VIP (Hạn mức cao & Chăm sóc bởi RM)'))
    elif seg == 'PRIME':
        signals.append(('signal-pill-vip', 'PHÂN KHÚC: PRIME PRIORITY (Tiềm năng mở rộng gói giải pháp tài chính)'))
    else:
        signals.append(('signal-pill-vip', 'PHÂN KHÚC: MASS (Mục tiêu kích hoạt sản phẩm thẻ & số hóa)'))
        
    # 2. Nhóm dịch vụ chiếm tỷ trọng cao nhất
    cat_counts = user_records['category'].value_counts()
    if not cat_counts.empty:
        top_cat = str(cat_counts.index[0])
        top_cat_pct = int(round((cat_counts.iloc[0] / len(user_records)) * 100))
        clean_cat = top_cat.split('.')[-1].strip() if '.' in top_cat else top_cat
        
        if any(k in top_cat.lower() for k in ['doanh nghiệp', 'l/c', 'tài trợ']):
            signals.append(('signal-pill-need', f'TRỌNG TÂM: Doanh nghiệp ({top_cat_pct}% GD) - Nhu cầu tài trợ thương mại'))
        elif any(k in top_cat.lower() for k in ['ngoại tệ', 'quốc tế', 'kiều hối']):
            signals.append(('signal-pill-need', f'TRỌNG TÂM: Ngoại tệ ({top_cat_pct}% GD) - Nhu cầu chi tiêu quốc tế'))
        elif any(k in top_cat.lower() for k in ['tiết kiệm', 'tiền gửi']):
            signals.append(('signal-pill-need', f'TRỌNG TÂM: Tiết kiệm ({top_cat_pct}% GD) - Tích lũy dòng tiền định kỳ'))
        elif any(k in top_cat.lower() for k in ['thẻ', 'pos']):
            signals.append(('signal-pill-need', f'TRỌNG TÂM: Thẻ ({top_cat_pct}% GD) - Nhu cầu hoàn tiền chi tiêu'))
        elif any(k in top_cat.lower() for k in ['chuyển tiền', 'thanh toán']):
            signals.append(('signal-pill-need', f'TRỌNG TÂM: Thanh toán ({top_cat_pct}% GD) - Dòng tiền luân chuyển cao'))
        elif any(k in top_cat.lower() for k in ['bảo hiểm', 'đầu tư']):
            signals.append(('signal-pill-need', f'TRỌNG TÂM: Bảo hiểm & Đầu tư ({top_cat_pct}% GD) - Bảo toàn tài sản'))
        elif any(k in top_cat.lower() for k in ['tín dụng', 'vay']):
            signals.append(('signal-pill-need', f'TRỌNG TÂM: Tín dụng ({top_cat_pct}% GD) - Bổ sung vốn lưu động'))
        else:
            signals.append(('signal-pill-need', f'TRỌNG TÂM: {clean_cat} ({top_cat_pct}% GD)'))

    # 3. Kênh giao dịch chủ đạo
    if 'channel' in user_records.columns:
        chans = user_records['channel'].value_counts()
        if not chans.empty:
            primary_chan = chans.index[0]
            chan_pct = int(round((chans.iloc[0] / len(user_records)) * 100))
            if primary_chan == 'APP' and chan_pct >= 60:
                signals.append(('signal-pill-chan', f'KÊNH: VPBank NEO ({chan_pct}% qua App)'))
            elif primary_chan == 'QUẦY' and chan_pct >= 50:
                signals.append(('signal-pill-chan', f'KÊNH: Tại Quầy ({chan_pct}% qua PGD)'))
            else:
                signals.append(('signal-pill-chan', f'KÊNH: Đa kênh ({primary_chan}: {chan_pct}%)'))

    # 4. Cơ hội bán chéo số 1
    if not user_recs.empty:
        top_rec = user_recs.iloc[0]
        rec_title = top_rec.get('title', 'Sản phẩm tài chính')
        rec_score = top_rec.get('match_score', '90%')
        signals.append(('signal-pill-opp', f'GỢI Ý SỐ 1: {rec_title} (Độ khớp {rec_score})'))

    # 5. Sự kiện giao dịch gần nhất
    if 'transaction_time' in user_records.columns and not user_records.empty:
        last_tx = user_records.sort_values(by='transaction_time', ascending=False).iloc[0]
        tx_title = last_tx.get('title', 'Giao dịch')
        tx_amt = last_tx.get('price', '')
        signals.append(('signal-pill-recent', f'GD GẦN NHẤT: {tx_title} ({tx_amt})'))
        
    return signals

# ==============================================================================
# HÀM TẢI & CACHE DỮ LIỆU SẢN PHẨM / KHÁCH HÀNG TỪ MONGODB ATLAS
# ==============================================================================
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
try:
    from mongo_connector import get_collection_df
except Exception:
    get_collection_df = None

# Tích hợp Module Nhận Diện Khuôn Mặt & Cross-Device Session
face_engine_error = None
try:
    from face_engine import get_face_engine, get_session_manager
    face_engine = get_face_engine()
    session_manager = get_session_manager()
except Exception as e:
    face_engine = None
    session_manager = None
    face_engine_error = str(e)

def standardize_df(df, col_type="purchase_history"):
    if df is None or df.empty:
        return pd.DataFrame()
    df = df.copy()
    
    if col_type == "purchase_history":
        col_mapping = {
            'customer_id': 'reviewerID',
            'customer_name': 'reviewerName',
            'service_name': 'title',
            'service_group': 'category',
            'amount': 'price'
        }
        for old_col, new_col in col_mapping.items():
            if old_col in df.columns and new_col not in df.columns:
                df[new_col] = df[old_col]
                
        if 'reviewerID' in df.columns:
            def format_cif(val):
                try:
                    val_str = str(val).strip()
                    if val_str.isdigit():
                        return f"CUST_{int(val_str):04d}"
                    if val_str.startswith("CUST_"):
                        return val_str
                    val_f = float(val_str)
                    if val_f.is_integer():
                        return f"CUST_{int(val_f):04d}"
                    return val_str
                except Exception:
                    return str(val)
            df['reviewerID'] = df['reviewerID'].apply(format_cif)
            
        if 'brand' not in df.columns:
            df['brand'] = 'VPBank Financial'
            
        # Đảm bảo các cột tối thiểu luôn tồn tại tránh KeyError
        required_ph_cols = {
            'reviewerID': 'CUST_0001',
            'reviewerName': 'Khách hàng',
            'segment': 'MASS',
            'category': 'Dịch vụ ngân hàng',
            'title': 'Giao dịch tại quầy',
            'price': '0 VND',
            'channel': 'QUẦY',
            'transaction_time': '2026-01-01 00:00:00'
        }
        for col, default_val in required_ph_cols.items():
            if col not in df.columns:
                df[col] = default_val
                
    elif col_type == "recommendations":
        col_mapping = {
            'customer_id': 'reviewerID',
            'customer_name': 'reviewerName',
            'product_name': 'title',
            'product_group': 'category'
        }
        for old_col, new_col in col_mapping.items():
            if old_col in df.columns and new_col not in df.columns:
                df[new_col] = df[old_col]
                
        if 'reviewerID' in df.columns:
            def format_cif(val):
                try:
                    val_str = str(val).strip()
                    if val_str.isdigit():
                        return f"CUST_{int(val_str):04d}"
                    if val_str.startswith("CUST_"):
                        return val_str
                    val_f = float(val_str)
                    if val_f.is_integer():
                        return f"CUST_{int(val_f):04d}"
                    return val_str
                except Exception:
                    return str(val)
            df['reviewerID'] = df['reviewerID'].apply(format_cif)
            
        required_rc_cols = {
            'reviewerID': 'CUST_0001',
            'reviewerName': 'Khách hàng',
            'segment': 'MASS',
            'category': 'Tài chính',
            'title': 'Sản phẩm tài chính',
            'price': '0 VND',
            'rate_or_fee': 'Theo biểu phí',
            'value_proposition': 'Giải pháp tài chính',
            'match_score': '90%',
            'gdv_script': 'Tư vấn sản phẩm phù hợp.'
        }
        for col, default_val in required_rc_cols.items():
            if col not in df.columns:
                df[col] = default_val
                
    return df

@st.cache_data(ttl=60)
def load_app_data():
    base_dir = os.path.dirname(__file__)
    is_mongo_connected = False
    
    # 1. Purchase History (Lịch sử giao dịch)
    ph = pd.DataFrame()
    if get_collection_df is not None:
        try:
            ph = get_collection_df('purchase_history')
            if not ph.empty:
                is_mongo_connected = True
        except Exception:
            ph = pd.DataFrame()
            
    if ph.empty:
        try:
            ph = pd.read_csv(os.path.join(base_dir, 'purchase_history.csv'), encoding='utf-8')
        except Exception:
            ph = pd.read_csv('purchase_history.csv')
            
    ph = standardize_df(ph, "purchase_history")
        
    # 2. Recommendations (Top-5 Gợi ý UltraGCN)
    rc = pd.DataFrame()
    if get_collection_df is not None:
        try:
            rc = get_collection_df('recommendations')
        except Exception:
            rc = pd.DataFrame()
            
    if rc.empty:
        try:
            rc = pd.read_csv(os.path.join(base_dir, 'recommendations.csv'), encoding='utf-8')
        except Exception:
            rc = pd.read_csv('recommendations.csv')
            
    rc = standardize_df(rc, "recommendations")
        
    # 3. Product Catalog (Danh mục Sản phẩm)
    catalog = pd.DataFrame()
    if get_collection_df is not None:
        try:
            catalog = get_collection_df('DanhMucSanPham')
        except Exception:
            catalog = pd.DataFrame()
            
    if catalog.empty:
        catalog = None
        
    return ph, rc, catalog, is_mongo_connected

purchase_history, recommendations, product_catalog, is_mongo = load_app_data()

# ==============================================================================
# THANH HEADER TRUNG TÂM VẬN HÀNH (TOP BRAND BAR)
# ==============================================================================
mongo_status_badge = "MONGODB ATLAS: ĐÃ KẾT NỐI (RinRec_DB)" if is_mongo else "VẬN HÀNH: BỘ NHỚ ĐỆM CỤC BỘ"

render_html(f"""
<div class="top-brand-bar">
    <div>
        <div class="top-brand-title">
            <span>VPBank SmartAdvisor 360°</span>
        </div>
        <div class="top-brand-sub">
            Hệ thống Trợ lý Tư vấn Bán chéo & Đề xuất Sản phẩm Tài chính Cá nhân hóa tại Quầy
        </div>
    </div>
    <div style="text-align: right;">
        <div class="top-badge-live">{mongo_status_badge}</div>
        <div style="font-size: 0.8rem; color: #CBD5E1; margin-top: 5px;">
            Chi nhánh Hội Sở | Giao dịch viên: <b>Nguyễn Thu Hà (VP8832)</b>
        </div>
    </div>
</div>
""")

# ==============================================================================
# SIDEBAR: BỘ LỌC KHÁCH HÀNG & TRUY VẤN HỒ SƠ
# ==============================================================================
# ==============================================================================
# KHỞI TẠO SESSION STATE CHO EKYC & CHỌN KHÁCH HÀNG
# ==============================================================================
if "selected_cif" not in st.session_state:
    st.session_state.selected_cif = None
if "ekyc_verified" not in st.session_state:
    st.session_state.ekyc_verified = False
if "ekyc_info" not in st.session_state:
    st.session_state.ekyc_info = None
if "current_ekyc_sid" not in st.session_state:
    if session_manager:
        new_sess = session_manager.create_session()
        st.session_state.current_ekyc_sid = new_sess["session_id"]
    else:
        st.session_state.current_ekyc_sid = None

# ==============================================================================
# SIDEBAR: BỘ LỌC KHÁCH HÀNG & TRUY VẤN HỒ SƠ
# ==============================================================================
with st.sidebar:
    st.markdown("### Tra Cứu Khách Hàng")
    
    # Lọc theo Phân khúc
    segment_options = ["Tất cả phân khúc", "DIAMOND (Ưu tiên cao cấp)", "PRIME (Khách hàng ưu tiên)", "MASS (Đại chúng)"]
    selected_seg_filter = st.selectbox("Lọc theo phân khúc:", segment_options, index=0)
    
    filtered_df = purchase_history.copy()
    if selected_seg_filter.startswith("DIAMOND"):
        filtered_df = filtered_df[filtered_df['segment'] == 'DIAMOND']
    elif selected_seg_filter.startswith("PRIME"):
        filtered_df = filtered_df[filtered_df['segment'] == 'PRIME']
    elif selected_seg_filter.startswith("MASS"):
        filtered_df = filtered_df[filtered_df['segment'] == 'MASS']
        
    # Danh sách khách hàng kèm CIF và Phân khúc
    user_unique = filtered_df[['reviewerID', 'reviewerName', 'segment']].drop_duplicates()
    user_unique['display'] = user_unique.apply(
        lambda r: f"[{r['segment']}] {r['reviewerName']} ({r['reviewerID']})", axis=1
    )
    
    customer_list = ['-- Chọn hoặc tìm kiếm khách hàng --'] + sorted(user_unique['display'].tolist())
    
    # Đồng bộ với session_state khi được nhận diện qua eKYC
    default_idx = 0
    if st.session_state.selected_cif:
        for idx, item in enumerate(customer_list):
            if f"({st.session_state.selected_cif})" in item:
                default_idx = idx
                break

    selected_customer_str = st.selectbox("Danh sách Khách hàng tại quầy:", customer_list, index=default_idx, key="sb_cust_select")
    
    if selected_customer_str and selected_customer_str != '-- Chọn hoặc tìm kiếm khách hàng --':
        try:
            curr_cif = selected_customer_str.split('(')[-1].replace(')', '').strip()
            if st.session_state.selected_cif != curr_cif:
                st.session_state.selected_cif = curr_cif
                st.session_state.ekyc_verified = False
                st.session_state.ekyc_info = None
        except Exception:
            pass
    elif selected_customer_str == '-- Chọn hoặc tìm kiếm khách hàng --' and st.session_state.selected_cif is not None and not st.session_state.ekyc_verified:
        st.session_state.selected_cif = None
    
    st.markdown("---")
    
    # Thống kê nhanh danh mục
    st.markdown("### Tổng Quan Chi Nhánh")
    total_cust = purchase_history['reviewerName'].nunique()
    diamond_count = purchase_history[purchase_history['segment'] == 'DIAMOND']['reviewerName'].nunique()
    prime_count = purchase_history[purchase_history['segment'] == 'PRIME']['reviewerName'].nunique()
    mass_count = purchase_history[purchase_history['segment'] == 'MASS']['reviewerName'].nunique()
    
    st.markdown(f"""
    - **Tổng số KH đang quản lý:** `{total_cust}` khách hàng
    - **Diamond VIP:** `{diamond_count}` khách hàng
    - **Prime Priority:** `{prime_count}` khách hàng
    - **Mass Standard:** `{mass_count}` khách hàng
    """)
    
    st.markdown("---")
    st.caption("Phiên bản sản phẩm SmartBanking Hub v3.5.0\nBảo mật chuẩn ISO/IEC 27001")

# ==============================================================================
# LOGIC TRÍCH XUẤT THÔNG TIN KHÁCH HÀNG ĐƯỢC CHỌN
# ==============================================================================
selected_cif = st.session_state.get("selected_cif")
selected_name = None

if selected_cif:
    user_records = purchase_history[purchase_history['reviewerID'] == selected_cif]
    if not user_records.empty:
        selected_name = user_records['reviewerName'].iloc[0]

# ==============================================================================
# ĐIỀU HƯỚNG TABS SẢN PHẨM
# ==============================================================================
tab1, tab2, tab3 = st.tabs([
    "Hồ Sơ Khách Hàng 360° & Đề Xuất Bán Chéo",
    "Báo Cáo Cơ Hội Bán Chéo Chi Nhánh",
    "Danh Mục Sản Phẩm & Biểu Phí Ưu Đãi"
])

# ==============================================================================
# TAB 1: HỒ SƠ KHÁCH HÀNG 360° & GỢI Ý NEXT-BEST-ACTION
# ==============================================================================
with tab1:
    # --------------------------------------------------------------------------
    # KHU VỰC QUẦY GIAO DỊCH SỐ: EKYC LIÊN THIẾT BỊ (CROSS-DEVICE QR & CAMERA)
    # --------------------------------------------------------------------------
    with st.expander("🛡️ **QUẦY GIAO DỊCH SỐ: NHẬN DIỆN KHUÔN MẶT KHÁCH HÀNG (AI Smart Counter & Mobile eKYC)**", expanded=(selected_cif is None)):
        ekyc_tab1, ekyc_tab2, ekyc_tab3 = st.tabs([
            "📱 Xác Thực Qua Di Động (Cross-Device QR)",
            "📷 Quét Khuôn Mặt Tại Quầy (Webcam)",
            "📁 Tải Ảnh Đối Soát / Đăng Ký Mới"
        ])
        
        # TAB A: XÁC THỰC QUA DI ĐỘNG (CROSS-DEVICE QR)
        with ekyc_tab1:
            if session_manager:
                from face_engine.session_manager import get_local_ip
                detected_ip = get_local_ip()
                
                # Cấu hình IP tùy chọn
                with st.expander("⚙️ **Cài Đặt Mạng & Địa Chỉ IP Máy Chủ**", expanded=False):
                    custom_ip = st.text_input("Địa chỉ IP máy tính (Wi-Fi LAN IP):", value=detected_ip, key="custom_ip_input", help="Đảm bảo điện thoại và máy tính kết nối cùng 1 mạng Wi-Fi.")
                    if st.button("Áp Dụng IP Mới & Tạo Lại Mã QR", key="btn_apply_ip"):
                        new_sess = session_manager.create_session(host_override=custom_ip)
                        st.session_state.current_ekyc_sid = new_sess["session_id"]
                        st.session_state.ekyc_verified = False
                        st.session_state.ekyc_info = None
                        st.rerun()

                sid = st.session_state.get("current_ekyc_sid")
                sess = session_manager.get_session(sid) if sid else None
                
                # Tự động tạo lại session nếu phiên hết hạn hoặc IP thay đổi
                if not sess or sess.get("status") == "EXPIRED" or (detected_ip not in sess.get("mobile_url", "") and "custom_ip_input" not in st.session_state):
                    sess = session_manager.create_session(host_override=st.session_state.get("custom_ip_input", detected_ip))
                    st.session_state.current_ekyc_sid = sess["session_id"]
                    sid = sess["session_id"]

                # Kiểm tra xem session đã nhận diện thành công chưa
                if sess.get("status") == "VERIFIED" and sess.get("result"):
                    res = sess["result"]
                    st.success(f"🎉 **XÁC THỰC THÀNH CÔNG TỪ THIẾT BỊ DI ĐỘNG!**\n\nKhách hàng: **{res.get('customer_name')}** (Mã CIF: `{res.get('cif_number')}`) | Phân khúc: **{res.get('segment')}** | Độ khớp: **{res.get('confidence')}%** (Engine: {res.get('engine')})")
                    if st.session_state.selected_cif != res.get("cif_number"):
                        st.session_state.selected_cif = res.get("cif_number")
                        st.session_state.ekyc_verified = True
                        st.session_state.ekyc_info = res
                        st.rerun()

                col_qr, col_info = st.columns([1, 1.6], gap="medium")
                with col_qr:
                    st.markdown("##### 1. Quét mã QR bằng Smartphone")
                    st.image(f"data:image/png;base64,{sess['qr_base64']}", width=230)
                    st.caption(f"Mã phiên: `{sid}` | Tự động hết hạn sau 3 phút")
                
                with col_info:
                    st.markdown("##### 2. Hướng Dẫn Khách Hàng Thao Tác")
                    st.markdown(f"""
                    1. Khách hàng bật **Wi-Fi trên điện thoại** (kết nối **cùng mạng Wi-Fi** với laptop này).
                    2. Dùng **Camera / Zalo / Trình duyệt điện thoại** quét mã QR bên cạnh:
                       - URL: [`{sess['mobile_url']}`]({sess['mobile_url']})
                    3. Hoặc **[👉 Bấm vào đây để mở test Camera ngay trên trình duyệt máy tính]({sess['local_url']})**.
                    4. Khách hàng căn mặt vào khung oval và bấm **"Chụp & Gửi Xác Thực"** để kích hoạt hồ sơ tại quầy.
                    """)
                    
                    btn_c1, btn_c2 = st.columns(2)
                    with btn_c1:
                        if st.button("🔄 Kiểm Tra Kết Quả Realtime", key="btn_check_sess"):
                            chk_sess = session_manager.get_session(sid)
                            if chk_sess and chk_sess.get("status") == "VERIFIED":
                                res = chk_sess["result"]
                                st.session_state.selected_cif = res.get("cif_number")
                                st.session_state.ekyc_verified = True
                                st.session_state.ekyc_info = res
                                st.toast(f"Đã nhận diện khách hàng {res.get('customer_name')}!")
                                st.rerun()
                            elif chk_sess and chk_sess.get("status") == "PENDING":
                                st.info("🟡 Đang chờ khách hàng quét mã và gửi ảnh từ điện thoại...")
                            elif chk_sess and chk_sess.get("status") == "FAILED":
                                st.error("❌ Không nhận diện được khuôn mặt trong ảnh gửi về.")
                    with btn_c2:
                        if st.button("➕ Tạo Mã QR Phiên Mới", key="btn_new_sess"):
                            new_sess = session_manager.create_session(host_override=st.session_state.get("custom_ip_input", detected_ip))
                            st.session_state.current_ekyc_sid = new_sess["session_id"]
                            st.session_state.ekyc_verified = False
                            st.session_state.ekyc_info = None
                            st.rerun()
                            
                    st.info("💡 **Mẹo**: Nếu mạng Wi-Fi có bảo mật chặn kết nối giữa 2 thiết bị (Client Isolation), bạn có thể bật **Điểm phát sóng di động (Hotspot)** từ điện thoại cho laptop bắt chung.")
            else:
                st.error(f"❌ Không thể tải Module Session Manager ({face_engine_error if face_engine_error else 'Vui lòng nhấn Rerun hoặc khởi động lại Streamlit'}).")

        # TAB B: QUÉT TẠI QUẦY (WEBCAM)
        with ekyc_tab2:
            st.markdown("##### Quét Khuôn Mặt Trực Tiếp Bằng Camera Tại Quầy")
            st.caption("Dành cho trường hợp khách hàng quét trực tiếp tại thiết bị của Giao Dịch Viên:")
            cam_file = st.camera_input("Bật Camera Quầy", key="cam_direct")
            if cam_file is not None and face_engine:
                with st.spinner("Đang nhận diện sinh trắc học AI..."):
                    rec_res = face_engine.recognize_face(cam_file.getvalue())
                    if rec_res.get("is_identified"):
                        st.success(f"✅ **Nhận diện thành công:** {rec_res['customer_name']} (Mã CIF: `{rec_res['cif_number']}`) | Độ khớp: **{rec_res['confidence']}%** ({rec_res['engine']})")
                        if st.button("Kích Hoạt Hồ Sơ 360° Khách Hàng Này", key="btn_activate_cam_cif"):
                            st.session_state.selected_cif = rec_res["cif_number"]
                            st.session_state.ekyc_verified = True
                            st.session_state.ekyc_info = rec_res
                            st.rerun()
                    else:
                        st.warning(f"⚠️ {rec_res.get('message', 'Không tìm thấy khuôn mặt khớp trong CSDL')}")

        # TAB C: TẢI ẢNH ĐỐI SOÁT / ĐĂNG KÝ MỚI
        with ekyc_tab3:
            sub_col1, sub_col2 = st.columns(2, gap="large")
            with sub_col1:
                st.markdown("##### 📁 Tải Ảnh Đối Soát Nhận Diện")
                up_file = st.file_uploader("Chọn ảnh chân dung kiểm thử", type=["jpg", "jpeg", "png"], key="up_test_face")
                if up_file is not None and face_engine:
                    rec_res = face_engine.recognize_face(up_file.getvalue())
                    if rec_res.get("is_identified"):
                        st.success(f"✅ **Nhận diện khớp:** {rec_res['customer_name']} (CIF: `{rec_res['cif_number']}`) | Độ khớp: **{rec_res['confidence']}%**")
                        if st.button("Mở Hồ Sơ Khách Hàng Này", key="btn_open_uploaded"):
                            st.session_state.selected_cif = rec_res["cif_number"]
                            st.session_state.ekyc_verified = True
                            st.session_state.ekyc_info = rec_res
                            st.rerun()
                    else:
                        st.warning("⚠️ Không nhận diện được khách hàng trong ảnh này.")
            with sub_col2:
                st.markdown("##### ➕ Đăng Ký Khuôn Mặt Mới (Enrollment)")
                all_cifs = sorted(purchase_history['reviewerID'].unique().tolist())
                en_cif = st.selectbox("Chọn mã CIF cần đăng ký khuôn mặt:", all_cifs, key="en_cif_sel")
                cust_recs = purchase_history[purchase_history['reviewerID'] == en_cif]
                en_name = cust_recs['reviewerName'].iloc[0] if not cust_recs.empty else f"Khách hàng {en_cif}"
                en_seg = cust_recs['segment'].iloc[0] if not cust_recs.empty else "MASS"
                
                en_img = st.file_uploader(f"Tải ảnh chân dung mới cho {en_name} ({en_cif})", type=["jpg", "jpeg", "png"], key="up_enroll_face")
                if en_img is not None and st.button("💾 Lưu Dữ Liệu Sinh Trắc Học", key="btn_save_enroll"):
                    if face_engine:
                        res = face_engine.enroll_customer_face(en_cif, en_name, en_seg, en_img.getvalue())
                        if res.get("success"):
                            st.success(f"✅ {res.get('message')}")
                            st.rerun()

    # --------------------------------------------------------------------------
    # HIỂN THỊ HỒ SƠ 360 & ĐỀ XUẤT SẢN PHẨM KHI ĐÃ CÓ KHÁCH HÀNG
    # --------------------------------------------------------------------------
    if selected_name and selected_cif:
        user_records = purchase_history[purchase_history['reviewerID'] == selected_cif]
        user_recs = recommendations[recommendations['reviewerID'] == selected_cif]
        
        segment = user_records['segment'].iloc[0] if 'segment' in user_records.columns else "MASS"
        total_tx = len(user_records)
        channels_used = user_records['channel'].value_counts().index.tolist() if 'channel' in user_records.columns else ['APP', 'QUẦY']
        primary_channel = channels_used[0] if channels_used else "VPBank NEO"
        
        # Badge phân khúc
        if segment == 'DIAMOND':
            badge_html = "<span class='badge-diamond'>KHÁCH HÀNG DIAMOND VIP</span>"
        elif segment == 'PRIME':
            badge_html = "<span class='badge-prime'>KHÁCH HÀNG PRIME PRIORITY</span>"
        else:
            badge_html = "<span class='badge-mass'>KHÁCH HÀNG MASS</span>"

        # Kiểm tra ảnh chân dung
        face_path = face_engine.get_customer_face_path(selected_cif) if face_engine else None
        avatar_img_html = ""
        if face_path and os.path.exists(face_path):
            try:
                import base64
                with open(face_path, "rb") as f:
                    b64_avatar = base64.b64encode(f.read()).decode("utf-8")
                avatar_img_html = f'<img src="data:image/jpeg;base64,{b64_avatar}" class="cust-face-portrait" alt="Chân dung {selected_name}">'
            except Exception:
                avatar_img_html = ""
            
        # 1. Hero Card: Chân dung khách hàng 360 kèm ảnh sinh trắc học
        render_html(f"""
        <div class="cust-profile-card">
            <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 15px;">
                <div style="display: flex; align-items: center; gap: 16px;">
                    {avatar_img_html}
                    <div>
                        <div style="font-size: 1.4rem; font-weight: 800; color: #0A2540;">
                            {selected_name}
                            <span style="color: #64748B; font-size: 0.95rem; margin-left: 8px;">(Mã CIF: <b>{selected_cif}</b>)</span>
                        </div>
                        <div style="margin-top: 6px; display: flex; align-items: center; gap: 8px; flex-wrap: wrap;">
                            {badge_html}
                            <span class="ekyc-verified-badge">🛡️ eKYC: FACEID ACTIVE</span>
                        </div>
                    </div>
                </div>
                <div style="display: flex; gap: 20px; text-align: right; flex-wrap: wrap;">
                    <div>
                        <div style="font-size: 0.78rem; color: #64748B; font-weight: 600; text-transform: uppercase;">Trạng Thái Định Danh</div>
                        <div style="font-size: 0.95rem; font-weight: 700; color: #00B14F;">ĐÃ XÁC THỰC SINH TRẮC HỌC</div>
                    </div>
                    <div>
                        <div style="font-size: 0.78rem; color: #64748B; font-weight: 600; text-transform: uppercase;">Kênh Ưa Chuộng</div>
                        <div style="font-size: 0.95rem; font-weight: 700; color: #0A2540;">{primary_channel}</div>
                    </div>
                    <div>
                        <div style="font-size: 0.78rem; color: #64748B; font-weight: 600; text-transform: uppercase;">Giao Dịch Gần Nhất</div>
                        <div style="font-size: 0.95rem; font-weight: 700; color: #0A2540;">{total_tx} giao dịch</div>
                    </div>
                </div>
            </div>
        </div>
        """)
        
        # 2. Tín hiệu nhu cầu & cơ hội thời gian thực (Smart Intent Signals)
        st.markdown("##### Tín Hiệu Nhu Cầu & Bối Cảnh Thời Gian Thực:")
        
        user_signals = generate_personalized_signals(user_records, user_recs)
        signals_html = " ".join([f"<span class='signal-pill {css_cls}'>{txt}</span>" for css_cls, txt in user_signals])
        render_html(f"<div style='margin-bottom: 0.5rem;'>{signals_html}</div>")
        st.markdown("<br>", unsafe_allow_html=True)
        
        # 3. Layout 2 cột: Cột Trái = Lịch sử tương tác, Cột Phải = Danh mục gợi ý sản phẩm
        col_history, col_recs = st.columns([1, 1.25], gap="large")
        
        with col_history:
            st.markdown("#### Lịch Sử Giao Dịch & Dịch Vụ Đã Dùng")
            st.caption("Tổng hợp các giao dịch tại quầy, ứng dụng số và thẻ của khách hàng:")
            
            cols_show = [c for c in ['transaction_time', 'title', 'category', 'price', 'channel'] if c in user_records.columns]
            rename_map = {
                'transaction_time': 'Thời Gian',
                'title': 'Nội Dung Giao Dịch / Dịch Vụ',
                'category': 'Phân Loại',
                'price': 'Số Tiền',
                'channel': 'Kênh'
            }
            
            df_display = user_records[cols_show].rename(columns=rename_map)
            st.dataframe(
                df_display,
                use_container_width=True,
                height=520,
                hide_index=True
            )
            
        with col_recs:
            st.markdown("#### Sản Phẩm Được Đề Xuất Phù Hợp Nhất (Next-Best-Offers)")
            st.caption("Xếp hạng theo độ phù hợp nhu cầu & quy tắc tài chính cá nhân hóa:")
            
            if not user_recs.empty:
                for rank, (_, row) in enumerate(user_recs.iterrows(), 1):
                    p_name = row.get('title', 'Sản phẩm tài chính')
                    p_group = row.get('category', 'Tài chính')
                    p_price = row.get('price', 'Theo hạn mức')
                    p_fee = row.get('rate_or_fee', 'Theo biểu phí chuẩn')
                    p_val = row.get('value_proposition', 'Giải pháp tài chính tối ưu cho khách hàng.')
                    p_match = row.get('match_score', '92%')
                    p_script = row.get('gdv_script', 'Gợi ý giải pháp tài chính phù hợp cho khách hàng.')
                    
                    # Card sản phẩm cao cấp
                    card_html = f"""
<div class="nba-card">
    <div class="nba-header">
        <div>
            <div class="nba-title">Top {rank} - {p_name}</div>
            <div style="font-size: 0.85rem; color: #64748B; margin-top: 2px;">
                Phân nhóm: <b>{p_group}</b>
            </div>
        </div>
        <div class="nba-match">Độ Phù Hợp: {p_match}</div>
    </div>
    <div class="nba-details">
        <div><b>Hạn mức / Tối thiểu:</b> {p_price}</div>
        <div><b>Lãi suất / Biểu phí:</b> {p_fee}</div>
    </div>
    <div class="nba-value">
        <b>Giá trị mang lại cho KH:</b> {p_val}
    </div>
    <div class="nba-script">
        <span class="nba-script-tag">Kịch Bản Tư Vấn GDV Tại Quầy:</span>
        "{p_script}"
    </div>
</div>
"""
                    render_html(card_html)
                    
                    # Nút tương tác nhanh cho từng sản phẩm
                    btn_col1, btn_col2, btn_col3 = st.columns([1.2, 1.2, 1])
                    with btn_col1:
                        if st.button(f"Mở Hồ Sơ #{rank}", key=f"btn_open_{rank}_{selected_cif}"):
                            st.toast(f"Đã khởi tạo hồ sơ đăng ký [{p_name}] cho khách hàng {selected_name}!")
                    with btn_col2:
                        if st.button(f"Gửi App KH #{rank}", key=f"btn_send_{rank}_{selected_cif}"):
                            st.toast(f"Đã gửi thông báo & ưu đãi [{p_name}] tới ứng dụng VPBank NEO của {selected_name}!")
                    with btn_col3:
                        if st.button(f"Lưu Ghi Chú #{rank}", key=f"btn_note_{rank}_{selected_cif}"):
                            st.toast("Đã ghi nhận phản hồi của khách hàng vào sổ nhật ký giao dịch.")
                    st.markdown("<div style='margin-bottom: 0.8rem;'></div>", unsafe_allow_html=True)
            else:
                st.info("Chưa có danh mục sản phẩm đề xuất sẵn cho khách hàng này.")
                
    else:
        # Giao diện Tổng Quan khi chưa chọn khách hàng cụ thể (Executive Dashboard)
        st.markdown("### Trung Tâm Điều Hành Tiếp Cận & Bán Chéo Chi Nhánh")
        st.info("Hướng dẫn: Vui lòng chọn một khách hàng từ thanh tìm kiếm bên trái để xem Hồ sơ 360° và các Gợi ý sản phẩm phù hợp.")
        
        # 4 Thẻ KPI vận hành
        kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)
        with kpi_col1:
            render_html("""
            <div class="metric-card">
                <div class="metric-label">Khách Hàng Quản Lý</div>
                <div class="metric-value">120</div>
                <div class="metric-note">100% Đã định danh eKYC</div>
            </div>
            """)
        with kpi_col2:
            render_html("""
            <div class="metric-card">
                <div class="metric-label">Cơ Hội Bán Chéo Sẵn Sàng</div>
                <div class="metric-value">600</div>
                <div class="metric-note">Top 5 Đề xuất/Khách hàng</div>
            </div>
            """)
        with kpi_col3:
            render_html("""
            <div class="metric-card">
                <div class="metric-label">Độ Phù Hợp Nhu Cầu TB</div>
                <div class="metric-value">94.6%</div>
                <div class="metric-note">Được tối ưu theo bối cảnh</div>
            </div>
            """)
        with kpi_col4:
            render_html("""
            <div class="metric-card">
                <div class="metric-label">Tỉ Lệ Chấp Thuận Gợi Ý</div>
                <div class="metric-value">78.2%</div>
                <div class="metric-note">+14.5% so với tháng trước</div>
            </div>
            """)
            
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Bảng Khách hàng chờ tư vấn ưu tiên hôm nay
        st.markdown("#### Hàng Đợi Khách Hàng Ưu Tiên Tiếp Cận Tại Quầy Hôm Nay")
        st.caption("Danh sách khách hàng có tín hiệu giao dịch mới nhất cần giao dịch viên chủ động tư vấn sản phẩm bổ sung:")
        
        priority_rows = []
        for cid in purchase_history['reviewerID'].unique()[:10]:
            u_ph = purchase_history[purchase_history['reviewerID'] == cid]
            u_rc = recommendations[recommendations['reviewerID'] == cid]
            top_prod = u_rc['title'].iloc[0] if not u_rc.empty else "Thẻ ghi nợ quốc tế"
            top_match = u_rc['match_score'].iloc[0] if not u_rc.empty else "95%"
            
            priority_rows.append({
                'Mã CIF': cid,
                'Họ và Tên Khách Hàng': u_ph['reviewerName'].iloc[0],
                'Phân Khúc': u_ph['segment'].iloc[0],
                'Tổng Lượt Giao Dịch': len(u_ph),
                'Sản Phẩm Đề Xuất Hàng Đầu': top_prod,
                'Độ Phù Hợp': top_match
            })
            
        df_priority = pd.DataFrame(priority_rows)
        st.dataframe(df_priority, use_container_width=True, hide_index=True)

# ==============================================================================
# TAB 2: BÁO CÁO CƠ HỘI BÁN CHÉO CHI NHÁNH
# ==============================================================================
with tab2:
    st.markdown("### Phân Tích Cơ Hội Kinh Doanh & Phân Khúc Toàn Chi Nhánh")
    st.caption("Báo cáo số liệu thời gian thực hỗ trợ Giám đốc Chi nhánh & Trưởng phòng Dịch vụ Khách hàng:")
    
    col_chart1, col_chart2 = st.columns(2)
    
    with col_chart1:
        st.markdown("##### Cơ Cấu Phân Khúc Khách Hàng")
        seg_dist = purchase_history.drop_duplicates(subset=['reviewerID'])['segment'].value_counts()
        st.bar_chart(seg_dist, color="#0A2540")
        
    with col_chart2:
        st.markdown("##### Top Nhóm Sản Phẩm Được Nhu Cầu Nhiều Nhất")
        rec_cat_dist = recommendations['category'].value_counts().head(5)
        st.bar_chart(rec_cat_dist, color="#00B14F")
        
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(r"##### Danh Sách Khách Hàng Tiềm Năng Cao (Match Score $\ge$ 95%)")
    
    high_potential = recommendations[recommendations['match_score'].astype(str).str.contains('95|96|97|98|99|100', regex=True)].drop_duplicates(subset=['reviewerID'])
    if not high_potential.empty:
        cols_hp = ['reviewerID', 'reviewerName', 'segment', 'title', 'category', 'match_score']
        rename_hp = {
            'reviewerID': 'Mã CIF',
            'reviewerName': 'Họ Tên Khách Hàng',
            'segment': 'Phân Khúc',
            'title': 'Sản Phẩm Đề Xuất',
            'category': 'Nhóm Sản Phẩm',
            'match_score': 'Độ Phù Hợp'
        }
        st.dataframe(high_potential[cols_hp].rename(columns=rename_hp), use_container_width=True, hide_index=True)

# ==============================================================================
# TAB 3: DANH MỤC SẢN PHẨM & BIỂU PHÍ ƯU ĐÃI
# ==============================================================================
with tab3:
    st.markdown("### Danh Mục Sản Phẩm Tài Chính & Chính Sách Ưu Đãi")
    st.caption("Tra cứu nhanh các gói giải pháp tài chính của ngân hàng đang triển khai:")
    
    if product_catalog is not None and not product_catalog.empty:
        prod_groups = ["Tất cả nhóm"] + sorted(product_catalog['Nhom'].dropna().unique().tolist())
        sel_group = st.selectbox("Chọn nhóm sản phẩm:", prod_groups)
        
        display_catalog = product_catalog.copy()
        if sel_group != "Tất cả nhóm":
            display_catalog = display_catalog[display_catalog['Nhom'] == sel_group]
            
        cols_cat = ['Ma_SP', 'Nhom', 'Ten_san_pham', 'Gia_tri_cot_loi', 'Phan_khuc', 'So_tien_toi_thieu', 'Lai_suat_Phi']
        rename_cat = {
            'Ma_SP': 'Mã SP',
            'Nhom': 'Nhóm Sản Phẩm',
            'Ten_san_pham': 'Tên Sản Phẩm',
            'Gia_tri_cot_loi': 'Giá Trị Cốt Lõi',
            'Phan_khuc': 'Phân Khúc Áp Dụng',
            'So_tien_toi_thieu': 'Hạn Mức / Tối Thiểu',
            'Lai_suat_Phi': 'Lãi Suất / Biểu Phí'
        }
        st.dataframe(display_catalog[cols_cat].rename(columns=rename_cat), use_container_width=True, hide_index=True)
    else:
        rec_unique_prods = recommendations[['category', 'title', 'price', 'rate_or_fee', 'value_proposition']].drop_duplicates(subset=['title'])
        st.dataframe(rec_unique_prods.rename(columns={
            'category': 'Nhóm Sản Phẩm',
            'title': 'Tên Sản Phẩm',
            'price': 'Hạn Mức Tối Thiểu',
            'rate_or_fee': 'Lãi Suất / Phí',
            'value_proposition': 'Giá Trị Mang Lại'
        }), use_container_width=True, hide_index=True)
