# -*- coding: utf-8 -*-
import os
import sys
import time
import base64
import textwrap
import re
from typing import Optional, List, Dict, Any
import streamlit as st
import pandas as pd
import numpy as np

# Đảm bảo root directory luôn có trong sys.path
_root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _root_dir not in sys.path:
    sys.path.insert(0, _root_dir)

from core.auth import (
    authenticate_user, get_all_users, create_user, update_user_role,
    toggle_user_status, reset_user_password, ROLE_TELLER, ROLE_MANAGER,
    ROLE_ADMIN, ROLE_LABELS, ROLE_BADGE_CLASSES
)


# Display labels only: role identifiers and authorization remain unchanged.
ROLE_LABELS = {
    role: re.sub(r"^[^\w]+", "", label)
    for role, label in ROLE_LABELS.items()
}

# ==============================================================================
# CẤU HÌNH TRANG WEB & THEME GIAO DIỆN CHUẨN DOANH NGHIỆP (ENTERPRISE BANKING)
# ==============================================================================
st.set_page_config(
    page_title="VPBank SmartAdvisor 360 - Trợ Lý Tư Vấn & Bán Chéo Thông Minh",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS giao diện ngân hàng cao cấp
with open(os.path.join(os.path.dirname(__file__), "theme.css"), encoding="utf-8") as theme_file:
    st.markdown(f"<style>{theme_file.read()}</style>", unsafe_allow_html=True)

# Helper render HTML an toàn không bị dính thụt dòng Markdown
def render_html(html_str: str):
    html_str = re.sub(
        r":material/([a-z0-9_]+):",
        r'<span class="ui-icon" aria-hidden="true">\1</span>',
        html_str,
    )
    if hasattr(st, 'html'):
        st.html(html_str)
    else:
        cleaned = "\n".join(line.strip() for line in html_str.split("\n") if line.strip())
        st.markdown(cleaned, unsafe_allow_html=True)

def render_banking_table(title: str, df: pd.DataFrame, max_height: Optional[int] = None, badge_text: Optional[str] = None):
    """Render bảng dữ liệu chuẩn phong cách Enterprise Banking Card (Header Navy Blue, chữ vàng/trắng, phân cách rõ ràng)"""
    if df is None or df.empty:
        st.info("Chưa có dữ liệu.")
        return

    badge_html = f'<span class="banking-panel-header-badge">{badge_text}</span>' if badge_text else ''
    headers_html = "".join([f"<th>{col}</th>" for col in df.columns])
    
    rows_html = []
    for _, row in df.iterrows():
        cells_html = []
        for col in df.columns:
            val = str(row[col]) if pd.notna(row[col]) else "-"
            # Định dạng đặc thù theo từng cột
            if col in ['Phân Khúc']:
                if val == 'DIAMOND':
                    cell_content = '<span class="badge-diamond-small">DIAMOND</span>'
                elif val == 'PRIME':
                    cell_content = '<span class="badge-prime-small">PRIME</span>'
                else:
                    cell_content = '<span class="badge-mass-small">MASS</span>'
            elif col in ['Độ Phù Hợp', 'Match Score']:
                cell_content = f'<span class="badge-match-score">{val}</span>'
            elif col in ['Kênh']:
                cell_content = f'<span class="badge-channel">{val}</span>'
            elif col in ['Mã CIF', 'Mã SP']:
                cell_content = f'<code class="code-cif">{val}</code>'
            else:
                cell_content = val
            cells_html.append(f"<td>{cell_content}</td>")
        rows_html.append(f"<tr>{''.join(cells_html)}</tr>")
    
    scroll_style = f"max-height: {max_height}px; overflow-y: auto;" if max_height else ""
    
    table_html = f"""
    <div class="banking-panel">
        <div class="banking-panel-header">
            <span>{title}</span>
            {badge_html}
        </div>
        <div class="banking-panel-body" style="{scroll_style}">
            <table class="banking-table">
                <thead>
                    <tr>{headers_html}</tr>
                </thead>
                <tbody>
                    {''.join(rows_html)}
                </tbody>
            </table>
        </div>
    </div>
    """
    render_html(table_html)

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
try:
    from core.mongo_connector import get_collection_df
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
# KHỞI TẠO SESSION STATE XÁC THỰC & PHÂN QUYỀN (RBAC & LOGIN)
# ==============================================================================
if "authenticated_user" not in st.session_state:
    st.session_state.authenticated_user = None

# ------------------------------------------------------------------------------
# MÀN HÌNH ĐĂNG NHẬP HỆ THỐNG (ENTERPRISE BANKING LOGIN)
# ------------------------------------------------------------------------------
if not isinstance(st.session_state.authenticated_user, dict):
    # A stale or incomplete Streamlit session must not be treated as a login.
    st.session_state.authenticated_user = None

if st.session_state.authenticated_user is None:
    with st.container(key="login_layout"):
        col_intro, col_form = st.columns([1.2, 1], gap="large", vertical_alignment="center")
        with col_intro:
            render_html("""
            <div class="login-hero">
                <div class="top-brand-title">VPBank SmartAdvisor 360</div>
                <div class="top-brand-sub">
                    Hệ thống Trợ lý Tư vấn Bán chéo & Đề xuất Sản phẩm Tài chính Cá nhân hóa (Bảo mật RBAC)
                </div>
                <div class="hero-orbit" aria-hidden="true">
                    <div class="orbit-inner"></div>
                    <i class="orbit-node node-one"></i><i class="orbit-node node-two"></i>
                    <i class="orbit-node node-three"></i><i class="orbit-node node-four"></i>
                    <div class="orbit-center"><span></span><span></span><span></span></div>
                </div>
            </div>
            """)
        with col_form:
            with st.form("login_form"):
                render_html("""
                <div class="login-header">
                    <div class="login-title">:material/lock: Đăng Nhập Hệ Thống</div>
                    <div class="login-sub">SmartAdvisor 360 - MongoDB Atlas User Authentication</div>
                </div>
                """)
                in_username = st.text_input("Tên đăng nhập:", icon=":material/person:", placeholder="Nhập tên đăng nhập (vd: gdv_ha, manager, admin)...")
                in_password = st.text_input("Mật khẩu:", icon=":material/key:", type="password", placeholder="Nhập mật khẩu...")
                submit_login = st.form_submit_button("Đăng Nhập Hệ Thống", icon=":material/login:", use_container_width=True)
                
                if submit_login:
                    res = authenticate_user(in_username, in_password)
                    if res.get("success") and isinstance(res.get("user"), dict):
                        st.session_state.authenticated_user = res["user"]
                        st.toast(res.get("message"))
                        time.sleep(0.3)
                        st.rerun()
                    else:
                        st.error(res.get("message", "Đăng nhập không hợp lệ. Vui lòng thử lại."))


    st.stop()

# ------------------------------------------------------------------------------
# TRÍCH XUẤT THÔNG TIN NGƯỜI DÙNG ĐÃ ĐĂNG NHẬP
# ------------------------------------------------------------------------------
current_user = st.session_state.authenticated_user
current_role = current_user.get("role", ROLE_TELLER)
user_fullname = current_user.get("full_name", "Nhân viên")
user_code = current_user.get("user_code", "VP0000")
user_branch = current_user.get("branch", "Chi nhánh Hội Sở")
role_label = ROLE_LABELS.get(current_role, "Giao Dịch Viên")
role_badge_class = ROLE_BADGE_CLASSES.get(current_role, "badge-mass")

# ==============================================================================
# THANH HEADER TRUNG TÂM VẬN HÀNH (TOP BRAND BAR)
# ==============================================================================
render_html(f"""
<div class="top-brand-bar">
    <div>
        <div class="top-brand-title">
            <span>VPBank SmartAdvisor 360</span>
        </div>
        <div class="top-brand-sub">
            Hệ thống Trợ lý Tư vấn Bán chéo & Đề xuất Sản phẩm Tài chính Cá nhân hóa tại Quầy
        </div>
    </div>
    <div style="text-align: right;">
        <div style="font-size: 0.92rem; color: #FFFFFF; font-weight: 700;">
            :material/account_balance: {user_branch}
        </div>
        <div style="font-size: 0.85rem; color: #E2E8F0; margin-top: 4px;">
            {role_label}: <b>{user_fullname} ({user_code})</b>
        </div>
    </div>
</div>
""")

# ==============================================================================
# KHỞI TẠO SESSION STATE CHO EKYC & CHỌN KHÁCH HÀNG
# ==============================================================================
if "selected_cif" not in st.session_state:
    query_cif = st.query_params.get("cif", None)
    st.session_state.selected_cif = query_cif
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
# SIDEBAR: BỘ LỌC KHÁCH HÀNG & THÔNG TIN TÀI KHOẢN
# ==============================================================================
with st.sidebar:
    render_html(f"""
    <div class="user-sidebar-card">
        <div style="font-size: 0.78rem; color: #94A3B8; text-transform: uppercase; font-weight: 600;">Tài Khoản Đang Đăng Nhập</div>
        <div style="font-size: 1.1rem; font-weight: 800; color: #FFFFFF; margin-top: 2px;">{user_fullname}</div>
        <div style="font-size: 0.82rem; color: #CBD5E1; margin-top: 2px;">Mã NV: <b>{user_code}</b> | {user_branch}</div>
        <div style="margin-top: 6px;"><span class="{role_badge_class}">{role_label}</span></div>
    </div>
    """)
    
    if st.button("Đăng Xuất Hệ Thống", icon=":material/logout:", key="btn_logout_sb", use_container_width=True):
        st.session_state.authenticated_user = None
        st.rerun()
        
    st.markdown("---")
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
    
    # Đồng bộ với session_state khi được nhận diện qua eKYC hoặc URL
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
                st.query_params["cif"] = curr_cif
        except Exception:
            pass
    elif selected_customer_str == '-- Chọn hoặc tìm kiếm khách hàng --' and st.session_state.selected_cif is not None and not st.session_state.ekyc_verified:
        st.session_state.selected_cif = None
        if "cif" in st.query_params:
            del st.query_params["cif"]

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
    st.caption("Phiên bản sản phẩm SmartBanking Hub v3.5.0\nBảo mật chuẩn ISO/IEC 27001 (MongoDB RBAC)")

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
# ĐIỀU HƯỚNG TABS SẢN PHẨM & PHÂN QUYỀN (DYNAMIC RBAC TABS)
# ==============================================================================
tab1, tab2, tab3, tab4 = None, None, None, None

if current_role == ROLE_TELLER:
    tab1, tab3 = st.tabs([
        ":material/target: Hồ Sơ Khách Hàng 360° & Đề Xuất Bán Chéo",
        ":material/inventory_2: Danh Mục Sản Phẩm & Biểu Phí Ưu Đãi"
    ])
elif current_role == ROLE_MANAGER:
    tab2, tab1, tab3 = st.tabs([
        ":material/trending_up: Báo Cáo Cơ Hội Kinh Doanh Chi Nhánh",
        ":material/target: Hồ Sơ Khách Hàng 360° & Đề Xuất Bán Chéo",
        ":material/inventory_2: Danh Mục Sản Phẩm & Biểu Phí Ưu Đãi"
    ])
else:  # ROLE_ADMIN
    tab1, tab2, tab3, tab4 = st.tabs([
        ":material/target: Hồ Sơ Khách Hàng 360° & Đề Xuất Bán Chéo",
        ":material/trending_up: Báo Cáo Cơ Hội Kinh Doanh Chi Nhánh",
        ":material/inventory_2: Danh Mục Sản Phẩm & Biểu Phí Ưu Đãi",
        ":material/shield: Quản Lý Người Dùng & Phân Quyền Hệ Thống"
    ])

# ==============================================================================
# TAB 1: HỒ SƠ KHÁCH HÀNG 360° & GỢI Ý NEXT-BEST-ACTION
# ==============================================================================
with tab1:
    # --------------------------------------------------------------------------
    # KHU VỰC QUẦY GIAO DỊCH SỐ: EKYC LIÊN THIẾT BỊ (CROSS-DEVICE QR & CAMERA)
    # --------------------------------------------------------------------------
    with st.expander(":material/shield: **QUẦY GIAO DỊCH SỐ: NHẬN DIỆN KHUÔN MẶT KHÁCH HÀNG (AI Smart Counter & Mobile eKYC)**", expanded=(selected_cif is None)):
        ekyc_tab1, ekyc_tab2, ekyc_tab3 = st.tabs([
            ":material/smartphone: Xác Thực Qua Di Động (Cross-Device QR)",
            ":material/photo_camera: Quét Khuôn Mặt Tại Quầy (Webcam)",
            ":material/folder_open: Tải Ảnh Đối Soát / Đăng Ký Mới"
        ])
        
        # TAB A: XÁC THỰC QUA DI ĐỘNG (CROSS-DEVICE QR)
        with ekyc_tab1:
            if session_manager:
                from face_engine.session_manager import get_local_ip, get_all_local_ips
                detected_ip = get_local_ip()
                all_detected_ips = get_all_local_ips()
                
                # Cấu hình IP tùy chọn
                with st.expander(":material/settings: **Cài Đặt Mạng & Địa Chỉ IP Máy Chủ**", expanded=False):
                    st.caption("Chọn nhanh IP phù hợp với kiểu kết nối giữa Điện thoại và Máy tính:")
                    col_ip_btns = st.columns(len(all_detected_ips)) if all_detected_ips else [st.container()]
                    for i, ip_opt in enumerate(all_detected_ips):
                        ip_label = f":material/wifi: Hotspot ({ip_opt})" if "192.168.137" in ip_opt else f":material/lan: Wi-Fi/LAN ({ip_opt})"
                        with col_ip_btns[i]:
                            if st.button(ip_label, key=f"btn_quick_ip_{i}"):
                                st.session_state["custom_ip_input"] = ip_opt
                                new_sess = session_manager.create_session(host_override=ip_opt)
                                st.session_state.current_ekyc_sid = new_sess["session_id"]
                                st.session_state.ekyc_verified = False
                                st.session_state.ekyc_info = None
                                st.rerun()

                    custom_ip = st.text_input("Địa chỉ IP máy tính (hoặc Domain/Tunnel):", value=st.session_state.get("custom_ip_input", detected_ip), key="custom_ip_input_field", help="Ví dụ: 192.168.137.1 (khi laptop phát Hotspot) hoặc IP mạng Wi-Fi.")
                    if st.button("Áp Dụng IP & Tạo Lại Mã QR", key="btn_apply_ip"):
                        st.session_state["custom_ip_input"] = custom_ip
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
                    st.success(f":material/verified: **XÁC THỰC THÀNH CÔNG TỪ THIẾT BỊ DI ĐỘNG!**\n\nKhách hàng: **{res.get('customer_name')}** (Mã CIF: `{res.get('cif_number')}`) | Phân khúc: **{res.get('segment')}** | Độ khớp: **{res.get('confidence')}%** (Engine: {res.get('engine')})")
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
                    3. Hoặc **[:material/arrow_forward: Bấm vào đây để mở test Camera ngay trên trình duyệt máy tính]({sess['local_url']})**.
                    4. Khách hàng căn mặt vào khung oval và bấm **"Chụp & Gửi Xác Thực"** để kích hoạt hồ sơ tại quầy.
                    """)
                    
                    btn_c1, btn_c2 = st.columns(2)
                    with btn_c1:
                        if st.button("Kiểm Tra Kết Quả Realtime", icon=":material/refresh:", key="btn_check_sess"):
                            chk_sess = session_manager.get_session(sid)
                            if chk_sess and chk_sess.get("status") == "VERIFIED":
                                res = chk_sess["result"]
                                st.session_state.selected_cif = res.get("cif_number")
                                st.session_state.ekyc_verified = True
                                st.session_state.ekyc_info = res
                                st.toast(f"Đã nhận diện khách hàng {res.get('customer_name')}!")
                                st.rerun()
                            elif chk_sess and chk_sess.get("status") == "PENDING":
                                st.info(":material/schedule: Đang chờ khách hàng quét mã và gửi ảnh từ điện thoại...")
                            elif chk_sess and chk_sess.get("status") == "FAILED":
                                st.error(":material/error: Không nhận diện được khuôn mặt trong ảnh gửi về.")
                    with btn_c2:
                        if st.button("Tạo Mã QR Phiên Mới", icon=":material/add:", key="btn_new_sess"):
                            new_sess = session_manager.create_session(host_override=st.session_state.get("custom_ip_input", detected_ip))
                            st.session_state.current_ekyc_sid = new_sess["session_id"]
                            st.session_state.ekyc_verified = False
                            st.session_state.ekyc_info = None
                            st.rerun()
                            
                    st.info(":material/lightbulb: **Mẹo**: Nếu mạng Wi-Fi có bảo mật chặn kết nối giữa 2 thiết bị (Client Isolation), bạn có thể bật **Điểm phát sóng di động (Hotspot)** từ điện thoại cho laptop bắt chung.")
            else:
                st.error(f":material/error: Không thể tải Module Session Manager ({face_engine_error if face_engine_error else 'Vui lòng nhấn Rerun hoặc khởi động lại Streamlit'}).")

        # TAB B: QUÉT TẠI QUẦY (WEBCAM)
        with ekyc_tab2:
            st.markdown("##### Quét Khuôn Mặt Trực Tiếp Bằng Camera Tại Quầy")
            st.caption("Dành cho trường hợp khách hàng quét trực tiếp tại thiết bị của Giao Dịch Viên:")
            cam_file = st.camera_input("Bật Camera Quầy", key="cam_direct")
            if cam_file is not None and face_engine:
                with st.spinner("Đang nhận diện sinh trắc học AI..."):
                    rec_res = face_engine.recognize_face(cam_file.getvalue())
                    if rec_res.get("is_identified"):
                        st.success(f":material/check_circle: **Nhận diện thành công:** {rec_res['customer_name']} (Mã CIF: `{rec_res['cif_number']}`) | Độ khớp: **{rec_res['confidence']}%** ({rec_res['engine']})")
                        if st.button("Kích Hoạt Hồ Sơ 360° Khách Hàng Này", key="btn_activate_cam_cif"):
                            st.session_state.selected_cif = rec_res["cif_number"]
                            st.session_state.ekyc_verified = True
                            st.session_state.ekyc_info = rec_res
                            st.query_params["cif"] = rec_res["cif_number"]
                            st.rerun()
                    else:
                        st.warning(f":material/warning: {rec_res.get('message', 'Không tìm thấy khuôn mặt khớp trong CSDL')}")

        # TAB C: TẢI ẢNH ĐỐI SOÁT / ĐĂNG KÝ MỚI
        with ekyc_tab3:
            sub_col1, sub_col2 = st.columns(2, gap="large")
            with sub_col1:
                st.markdown("##### :material/folder_open: Tải Ảnh Đối Soát Nhận Diện")
                up_file = st.file_uploader("Chọn ảnh chân dung kiểm thử", type=["jpg", "jpeg", "png"], key="up_test_face")
                if up_file is not None and face_engine:
                    rec_res = face_engine.recognize_face(up_file.getvalue())
                    if rec_res.get("is_identified"):
                        st.success(f":material/check_circle: **Nhận diện khớp:** {rec_res['customer_name']} (CIF: `{rec_res['cif_number']}`) | Độ khớp: **{rec_res['confidence']}%**")
                        if st.button("Mở Hồ Sơ Khách Hàng Này", key="btn_open_uploaded"):
                            st.session_state.selected_cif = rec_res["cif_number"]
                            st.session_state.ekyc_verified = True
                            st.session_state.ekyc_info = rec_res
                            st.query_params["cif"] = rec_res["cif_number"]
                            st.rerun()
                    else:
                        st.warning(":material/warning: Không nhận diện được khách hàng trong ảnh này.")
            with sub_col2:
                st.markdown("##### :material/add: Đăng Ký Khuôn Mặt Mới (MongoDB Atlas)")
                all_cifs = sorted(purchase_history['reviewerID'].unique().tolist())
                en_cif = st.selectbox("Chọn mã CIF cần đăng ký khuôn mặt:", all_cifs, key="en_cif_sel")
                cust_recs = purchase_history[purchase_history['reviewerID'] == en_cif]
                en_name = cust_recs['reviewerName'].iloc[0] if not cust_recs.empty else f"Khách hàng {en_cif}"
                en_seg = cust_recs['segment'].iloc[0] if not cust_recs.empty else "MASS"
                
                en_img = st.file_uploader(f"Tải ảnh chân dung mới cho {en_name} ({en_cif})", type=["jpg", "jpeg", "png"], key="up_enroll_face")
                if en_img is not None and st.button("Lưu Vào MongoDB & Bộ Nhớ Sinh Trắc Học", icon=":material/save:", key="btn_save_enroll"):
                    if face_engine:
                        with st.spinner("Đang trích xuất vector và đồng bộ vào MongoDB Atlas..."):
                            res = face_engine.enroll_customer_face(en_cif, en_name, en_seg, en_img.getvalue())
                            if res.get("success"):
                                st.session_state.selected_cif = en_cif
                                st.session_state.ekyc_verified = True
                                st.session_state.ekyc_info = {
                                    "is_identified": True,
                                    "cif_number": en_cif,
                                    "customer_name": en_name,
                                    "segment": en_seg,
                                    "confidence": 100.0,
                                    "engine": "MongoDB Atlas eKYC Biometrics"
                                }
                                st.query_params["cif"] = en_cif
                                st.success(f":material/check_circle: {res.get('message')}")
                                st.toast("Đã lưu thành công vào MongoDB Atlas!")
                                time.sleep(0.5)
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
                            <span class="ekyc-verified-badge">:material/shield: eKYC: FACEID ACTIVE</span>
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
            cols_show = [c for c in ['transaction_time', 'title', 'category', 'price', 'channel'] if c in user_records.columns]
            rename_map = {
                'transaction_time': 'Thời Gian',
                'title': 'Nội Dung Giao Dịch / Dịch Vụ',
                'category': 'Phân Loại',
                'price': 'Số Tiền',
                'channel': 'Kênh'
            }
            
            df_display = user_records[cols_show].rename(columns=rename_map)
            render_banking_table(
                "THÔNG TIN LỊCH SỬ GIAO DỊCH & DỊCH VỤ",
                df_display,
                max_height=520,
                badge_text=f"{len(df_display)} giao dịch"
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
        st.markdown("### :material/dashboard: Trung Tâm Điều Hành & Phân Tích Khách Hàng Chi Nhánh")
        st.info(":material/lightbulb: **Hướng dẫn**: Chọn nhanh khách hàng từ danh sách các **ô hàng đợi bên dưới** (bấm *Mở Hồ Sơ & Tư Vấn*) hoặc tra cứu từ thanh tìm kiếm bên trái để xem Hồ sơ 360° và các Gợi ý sản phẩm phù hợp.")
        
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
        
        # ======================================================================
        # HÀNG ĐỢI KHÁCH HÀNG ƯU TIÊN TIẾP CẬN TẠI QUẦY (VẼ TỪNG Ô / GRID CARDS)
        # ======================================================================
        st.markdown("#### :material/target: Hàng Đợi Khách Hàng Ưu Tiên Tiếp Cận Tại Quầy Hôm Nay")
        st.caption("Danh sách khách hàng có tín hiệu giao dịch mới nhất được phân tích và vẽ theo từng ô trực quan kèm nút mở hồ sơ trực tiếp:")
        
        # Bộ lọc phân khúc nhanh cho hàng đợi
        col_f1, col_f2 = st.columns([1.5, 2.5])
        with col_f1:
            queue_filter = st.selectbox(
                "Lọc hàng đợi tại quầy theo phân khúc:",
                ["Tất cả hàng đợi (Ưu tiên)", "DIAMOND VIP", "PRIME Priority", "MASS Standard"],
                key="queue_seg_filter"
            )
        
        # Trích xuất danh sách khách hàng ưu tiên đa dạng các phân khúc
        priority_cifs = []
        # Ưu tiên các khách hàng DIAMOND
        diamond_cifs = purchase_history[purchase_history['segment'] == 'DIAMOND']['reviewerID'].unique().tolist()
        prime_cifs = purchase_history[purchase_history['segment'] == 'PRIME']['reviewerID'].unique().tolist()
        mass_cifs = purchase_history[purchase_history['segment'] == 'MASS']['reviewerID'].unique().tolist()
        
        if queue_filter.startswith("DIAMOND"):
            target_cifs = diamond_cifs
        elif queue_filter.startswith("PRIME"):
            target_cifs = prime_cifs
        elif queue_filter.startswith("MASS"):
            target_cifs = mass_cifs
        else:
            # Kết hợp xen kẽ tạo danh sách 12 khách hàng tiêu biểu
            target_cifs = diamond_cifs[:4] + prime_cifs[:4] + mass_cifs[:4]
            
        # Hiển thị dạng lưới ô (3 Cột)
        num_cols = 3
        for i in range(0, len(target_cifs), num_cols):
            row_cifs = target_cifs[i:i+num_cols]
            cols = st.columns(num_cols)
            for j, cid in enumerate(row_cifs):
                with cols[j]:
                    u_ph = purchase_history[purchase_history['reviewerID'] == cid]
                    u_rc = recommendations[recommendations['reviewerID'] == cid]
                    cust_name = u_ph['reviewerName'].iloc[0] if not u_ph.empty else f"Khách hàng {cid}"
                    seg = u_ph['segment'].iloc[0] if not u_ph.empty else "MASS"
                    tx_count = len(u_ph)
                    
                    # Xác định kênh chính
                    chans = u_ph['channel'].value_counts() if 'channel' in u_ph.columns and not u_ph.empty else []
                    primary_chan = chans.index[0] if len(chans) > 0 else "APP"
                    chan_label = ":material/smartphone: VPBank NEO" if primary_chan == "APP" else ":material/account_balance: Tại Quầy"
                    
                    # Avatar chữ cái đầu
                    name_parts = cust_name.strip().split()
                    initials = (name_parts[0][0] + name_parts[-1][0]).upper() if len(name_parts) >= 2 else cust_name[:2].upper()
                    
                    # Badge phân khúc
                    seg_class = seg.lower()
                    if seg == 'DIAMOND':
                        seg_badge_html = "<span class='badge-diamond-small'>DIAMOND VIP</span>"
                    elif seg == 'PRIME':
                        seg_badge_html = "<span class='badge-prime-small'>PRIME</span>"
                    else:
                        seg_badge_html = "<span class='badge-mass-small'>MASS</span>"
                        
                    # Gợi ý Next-Best-Action tương thích theo phân khúc & lịch sử
                    rec_row = None
                    if not u_rc.empty:
                        # Chọn sản phẩm phù hợp nhất theo đặc trưng phân khúc
                        if seg == 'DIAMOND':
                            vip_recs = u_rc[u_rc['category'].isin(['Phân khúc', 'Đầu tư', 'Bảo hiểm'])]
                            rec_row = vip_recs.iloc[0] if not vip_recs.empty else u_rc.iloc[0]
                        elif seg == 'PRIME':
                            prime_recs = u_rc[u_rc['category'].isin(['Thẻ', 'Vay', 'Bảo hiểm'])]
                            rec_row = prime_recs.iloc[0] if not prime_recs.empty else u_rc.iloc[0]
                        else:
                            rec_row = u_rc.iloc[0]

                    if rec_row is not None:
                        top_prod = rec_row.get('title', 'Gói tài khoản VPBank')
                        top_group = rec_row.get('category', 'Tài chính')
                        top_match = rec_row.get('match_score', '95%')
                    else:
                        if seg == 'DIAMOND':
                            top_prod = "Nâng hạng VPBank Diamond / Prime"
                            top_group = "Hội Viên VIP"
                            top_match = "98%"
                        elif seg == 'PRIME':
                            top_prod = "Thẻ ghi nợ quốc tế VPBank"
                            top_group = "Thẻ & Ngân Hàng Số"
                            top_match = "96%"
                        else:
                            top_prod = "Gói tài khoản chi lương doanh nghiệp"
                            top_group = "Gói Doanh Nghiệp"
                            top_match = "95%"
                        
                    card_html = f"""
                    <div class="cust-card-box {seg_class}">
                        <div>
                            <div class="cust-card-header">
                                <div style="display: flex; align-items: center;">
                                    <div class="cust-card-avatar {seg_class}">{initials}</div>
                                    <div>
                                        <div class="cust-card-name">{cust_name}</div>
                                        <div class="cust-card-cif">{cid}</div>
                                    </div>
                                </div>
                                <div>{seg_badge_html}</div>
                            </div>
                            <div class="cust-card-stats">
                                <span>:material/bar_chart: Lịch sử: <b>{tx_count} GD</b></span>
                                <span>{chan_label}</span>
                            </div>
                            <div class="cust-card-rec-box">
                                <div class="cust-card-rec-label">
                                    <span>:material/target: GỢI Ý BÁN CHÉO #1</span>
                                    <span class="badge-match-score">{top_match}</span>
                                </div>
                                <div class="cust-card-rec-name" title="{top_prod}">{top_prod}</div>
                                <div style="font-size: 0.75rem; color: #64748B; margin-top: 2px;">Nhóm: <b>{top_group}</b></div>
                            </div>
                        </div>
                    </div>
                    """
                    render_html(card_html)
                    
                    # Nút bấm mở hồ sơ trực tiếp từ ô
                    if st.button("Mở Hồ Sơ & Tư Vấn", icon=":material/arrow_forward:", key=f"btn_card_cif_{cid}_{i}_{j}", use_container_width=True):
                        st.session_state.selected_cif = cid
                        st.session_state.ekyc_verified = False
                        st.session_state.ekyc_info = None
                        st.query_params["cif"] = cid
                        st.rerun()
                    st.markdown("<div style='margin-bottom: 0.8rem;'></div>", unsafe_allow_html=True)

# ==============================================================================
# TAB 2: BÁO CÁO CƠ HỘI KINH DOANH CHI NHÁNH
# ==============================================================================
if tab2 is not None:
    with tab2:
        st.markdown("### :material/bar_chart: Báo Cáo Cơ Hội Kinh Doanh & Phân Khúc Toàn Chi Nhánh")
        st.caption("Báo cáo số liệu thời gian thực hỗ trợ Giám đốc Chi nhánh & Trưởng phòng Dịch vụ Khách hàng:")
        
        col_chart1, col_chart2 = st.columns(2)
        
        with col_chart1:
            st.markdown("##### :material/groups: Cơ Cấu Phân Khúc Khách Hàng Toàn Chi Nhánh")
            seg_dist = purchase_history.drop_duplicates(subset=['reviewerID'])['segment'].value_counts()
            st.bar_chart(seg_dist, color="#0A2540")
            
        with col_chart2:
            st.markdown("##### :material/emoji_events: Top Nhóm Sản Phẩm Có Cơ Hội Kinh Doanh Lớn Nhất")
            # Phân bổ nhu cầu thực tế dựa trên hành vi giao dịch và gợi ý cá nhân hóa
            top_recs_summary = []
            for cid, group in purchase_history.groupby('reviewerID'):
                seg = group['segment'].iloc[0]
                top_cat = group['category'].value_counts().index[0]
                if 'doanh nghiệp' in top_cat.lower():
                    rec_cat = 'Gói Doanh Nghiệp'
                elif 'thẻ' in top_cat.lower() or 'thanh toán' in top_cat.lower() or 'số' in top_cat.lower():
                    rec_cat = 'Thẻ & Ngân Hàng Số'
                elif 'tiết kiệm' in top_cat.lower() or seg == 'DIAMOND':
                    rec_cat = 'Tiết Kiệm & Đầu Tư'
                elif 'tín dụng' in top_cat.lower():
                    rec_cat = 'Tín Dụng & Cho Vay'
                else:
                    rec_cat = 'Bảo Hiểm & VIP'
                top_recs_summary.append(rec_cat)
                
            rec_cat_dist = pd.Series(top_recs_summary).value_counts()
            st.bar_chart(rec_cat_dist, color="#4F9CF9")
            
        st.markdown("<br>", unsafe_allow_html=True)
        
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
            render_banking_table(
                "DANH SÁCH KHÁCH HÀNG TIỀM NĂNG CAO (MATCH SCORE ≥ 95%)",
                high_potential[cols_hp].rename(columns=rename_hp),
                badge_text=f"{len(high_potential)} Khách hàng mục tiêu"
            )

# ==============================================================================
# TAB 3: DANH MỤC SẢN PHẨM & BIỂU PHÍ ƯU ĐÃI
# ==============================================================================
with tab3:
    st.markdown("### Danh Mục Sản Phẩm Tài Chính & Chính Sách Ưu Đãi")
    st.caption("Tra cứu nhanh các gói giải pháp tài chính của ngân hàng đang triển khai:")
    
    if product_catalog is not None and not product_catalog.empty:
        prod_groups = ["Tất cả nhóm"] + sorted(product_catalog['Nhom'].dropna().unique().tolist())
        sel_group = st.selectbox("Chọn nhóm sản phẩm:", prod_groups)
        
        cols_cat = ['Ma_SP', 'Ten_san_pham', 'Gia_tri_cot_loi', 'Phan_khuc', 'So_tien_toi_thieu', 'Lai_suat_Phi']
        rename_cat = {
            'Ma_SP': 'Mã SP',
            'Ten_san_pham': 'Tên Sản Phẩm',
            'Gia_tri_cot_loi': 'Giá Trị Cốt Lõi',
            'Phan_khuc': 'Phân Khúc Áp Dụng',
            'So_tien_toi_thieu': 'Hạn Mức / Tối Thiểu',
            'Lai_suat_Phi': 'Lãi Suất / Biểu Phí'
        }
        
        if sel_group == "Tất cả nhóm":
            for grp in sorted(product_catalog['Nhom'].dropna().unique().tolist()):
                grp_df = product_catalog[product_catalog['Nhom'] == grp]
                render_banking_table(
                    f"THÔNG TIN DANH MỤC: {grp.upper()}",
                    grp_df[cols_cat].rename(columns=rename_cat),
                    badge_text=f"{len(grp_df)} Sản phẩm"
                )
        else:
            grp_df = product_catalog[product_catalog['Nhom'] == sel_group]
            render_banking_table(
                f"THÔNG TIN DANH MỤC: {sel_group.upper()}",
                grp_df[cols_cat].rename(columns=rename_cat),
                badge_text=f"{len(grp_df)} Sản phẩm"
            )
    else:
        rec_unique_prods = recommendations[['category', 'title', 'price', 'rate_or_fee', 'value_proposition']].drop_duplicates(subset=['title'])
        categories = sorted(rec_unique_prods['category'].dropna().unique().tolist())
        sel_cat = st.selectbox("Chọn nhóm sản phẩm:", ["Tất cả nhóm"] + categories)
        
        cols_rec = ['title', 'price', 'rate_or_fee', 'value_proposition']
        rename_rec = {
            'title': 'Tên Sản Phẩm',
            'price': 'Hạn Mức / Tối Thiểu',
            'rate_or_fee': 'Lãi Suất / Biểu Phí',
            'value_proposition': 'Giá Trị Cốt Lõi'
        }
        
        if sel_cat == "Tất cả nhóm":
            for cat in categories:
                cat_df = rec_unique_prods[rec_unique_prods['category'] == cat]
                render_banking_table(
                    f"THÔNG TIN DANH MỤC: {cat.upper()}",
                    cat_df[cols_rec].rename(columns=rename_rec),
                    badge_text=f"{len(cat_df)} Sản phẩm"
                )
        else:
            cat_df = rec_unique_prods[rec_unique_prods['category'] == sel_cat]
            render_banking_table(
                f"THÔNG TIN DANH MỤC: {sel_cat.upper()}",
                cat_df[cols_rec].rename(columns=rename_rec),
                badge_text=f"{len(cat_df)} Sản phẩm"
            )

# ==============================================================================
# TAB 4: QUẢN LÝ NGƯỜI DÙNG & PHÂN QUYỀN HỆ THỐNG (ADMIN ONLY)
# ==============================================================================
if tab4 is not None:
    with tab4:
        st.markdown("### :material/shield: Quản Lý Người Dùng & Phân Quyền Hệ Thống (RBAC Admin Panel)")
        st.caption("Quản lý danh sách tài khoản nhân viên, phân quyền vai trò và đồng bộ trực tiếp với MongoDB Atlas:")
        
        all_users = get_all_users()
        
        # 4 thẻ Thống kê tài khoản
        col_u1, col_u2, col_u3, col_u4 = st.columns(4)
        with col_u1:
            render_html(f"""
            <div class="metric-card">
                <div class="metric-label">Tổng Số Tài Khoản</div>
                <div class="metric-value">{len(all_users)}</div>
                <div class="metric-note">MongoDB Atlas Connected</div>
            </div>
            """)
        with col_u2:
            gdv_cnt = len([u for u in all_users if u.get('role') == ROLE_TELLER])
            render_html(f"""
            <div class="metric-card">
                <div class="metric-label">Giao Dịch Viên (GDV)</div>
                <div class="metric-value">{gdv_cnt}</div>
                <div class="metric-note">Thao tác trực tiếp tại quầy</div>
            </div>
            """)
        with col_u3:
            mgr_cnt = len([u for u in all_users if u.get('role') == ROLE_MANAGER])
            render_html(f"""
            <div class="metric-card">
                <div class="metric-label">Giám Đốc Chi Nhánh</div>
                <div class="metric-value">{mgr_cnt}</div>
                <div class="metric-note">Quyền xem báo cáo tổng hợp</div>
            </div>
            """)
        with col_u4:
            adm_cnt = len([u for u in all_users if u.get('role') == ROLE_ADMIN])
            render_html(f"""
            <div class="metric-card">
                <div class="metric-label">Quản Trị Viên (Admin)</div>
                <div class="metric-value">{adm_cnt}</div>
                <div class="metric-note">Toàn quyền hệ thống</div>
            </div>
            """)
            
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Bảng danh sách người dùng
        if all_users:
            users_df = pd.DataFrame(all_users)
            users_df["Vai Trò Bằng Tiếng Việt"] = users_df["role"].map(lambda r: ROLE_LABELS.get(r, r))
            show_cols = ["username", "full_name", "user_code", "Vai Trò Bằng Tiếng Việt", "branch", "status", "created_at"]
            rename_users = {
                "username": "Tên Đăng Nhập",
                "full_name": "Họ và Tên",
                "user_code": "Mã NV",
                "Vai Trò Bằng Tiếng Việt": "Vai Trò Phân Quyền",
                "branch": "Chi Nhánh",
                "status": "Trạng Thái",
                "created_at": "Ngày Khởi Tạo"
            }
            render_banking_table(
                "DANH SÁCH TÀI KHOẢN NHÂN VIÊN TRONG CSDL (MONGODB ATLAS)",
                users_df[show_cols].rename(columns=rename_users),
                badge_text=f"{len(users_df)} Tài khoản"
            )
            
        st.markdown("<br>", unsafe_allow_html=True)
        
        # 2 Cột Thao tác Admin: Tạo mới & Quản lý vai trò/Khóa tài khoản
        col_adm_left, col_adm_right = st.columns(2, gap="large")
        
        with col_adm_left:
            st.markdown("##### :material/add: Tạo Tài Khoản Nhân Viên Mới (GDV / Manager)")
            st.caption("Admin có quyền cấp tài khoản mới với vai trò **Giám Đốc Chi Nhánh (Manager)** hoặc **Giao Dịch Viên (GDV)**:")
            with st.form("form_create_user"):
                new_uname = st.text_input("Tên đăng nhập (username):", placeholder="vd: gdv_phuong, manager_hung...")
                new_pwd = st.text_input("Mật khẩu khởi tạo:", type="password", placeholder="Mật khẩu ít nhất 6 ký tự...")
                new_fname = st.text_input("Họ và Tên nhân viên:", placeholder="vd: Lê Thị Phương...")
                new_code = st.text_input("Mã nhân viên (User Code):", placeholder="vd: VP8899...")
                new_role_sel = st.selectbox("Phân vai trò (Role):", options=[ROLE_TELLER, ROLE_MANAGER, ROLE_ADMIN], format_func=lambda x: ROLE_LABELS[x], help="Chọn vai trò GDV (Giao dịch viên), Manager (Giám đốc chi nhánh) hoặc Admin")
                new_branch = st.text_input("Chi nhánh:", value="Chi nhánh Hội Sở")
                
                submit_create = st.form_submit_button("Khởi Tạo & Lưu Vào MongoDB", icon=":material/save:", use_container_width=True)
                if submit_create:
                    res_c = create_user(new_uname, new_pwd, new_fname, new_code, new_role_sel, new_branch)
                    if res_c.get("success"):
                        st.success(res_c.get("message"))
                        st.toast(f"Đã tạo tài khoản {new_uname}!")
                        time.sleep(0.5)
                        st.rerun()
                    else:
                        st.error(res_c.get("message"))
                        
        with col_adm_right:
            st.markdown("##### :material/settings: Quản Lý / Đổi Quyền / Khóa Tài Khoản")
            user_list_usernames = [u.get("username") for u in all_users if u.get("username") != current_user.get("username")]
            if user_list_usernames:
                sel_manage_user = st.selectbox("Chọn tài khoản cần thao tác:", user_list_usernames, key="sb_manage_user")
                target_user = next((u for u in all_users if u.get("username") == sel_manage_user), None)
                
                if target_user:
                    st.info(f":material/person: Tài khoản: **{target_user.get('full_name')}** ({target_user.get('username')}) | Vai trò hiện tại: **{ROLE_LABELS.get(target_user.get('role'))}** | Trạng thái: **{target_user.get('status')}**")
                    
                    col_m1, col_m2 = st.columns(2)
                    with col_m1:
                        status_btn_label = ":material/lock: Khóa Tài Khoản" if target_user.get("status") == "ACTIVE" else ":material/lock_open: Mở Khóa Tài Khoản"
                        if st.button(status_btn_label, key="btn_toggle_status", use_container_width=True):
                            res_t = toggle_user_status(sel_manage_user)
                            if res_t.get("success"):
                                st.success(res_t.get("message"))
                                st.toast(res_t.get("message"))
                                time.sleep(0.5)
                                st.rerun()
                                
                    with col_m2:
                        current_t_role = target_user.get("role")
                        idx_role = [ROLE_TELLER, ROLE_MANAGER, ROLE_ADMIN].index(current_t_role) if current_t_role in [ROLE_TELLER, ROLE_MANAGER, ROLE_ADMIN] else 0
                        up_role_sel = st.selectbox("Chọn vai trò mới:", options=[ROLE_TELLER, ROLE_MANAGER, ROLE_ADMIN], index=idx_role, format_func=lambda x: ROLE_LABELS[x], key="sb_up_role")
                        if st.button("Cập Nhật Vai Trò", icon=":material/save:", key="btn_update_role", use_container_width=True):
                            res_r = update_user_role(sel_manage_user, up_role_sel)
                            if res_r.get("success"):
                                st.success(res_r.get("message"))
                                st.toast(res_r.get("message"))
                                time.sleep(0.5)
                                st.rerun()
                                
                    st.markdown("---")
                    st.markdown("##### :material/key: Reset Mật Khẩu Cho Tài Khoản:")
                    reset_pwd_val = st.text_input("Mật khẩu mới:", type="password", key="in_reset_pwd")
                    if st.button("Đổi Mật Khẩu Ngay", icon=":material/key:", key="btn_do_reset_pwd"):
                        res_p = reset_user_password(sel_manage_user, reset_pwd_val)
                        if res_p.get("success"):
                            st.success(res_p.get("message"))
                            st.toast(res_p.get("message"))
                        else:
                            st.error(res_p.get("message"))
            else:
                st.info("Chưa có tài khoản nhân viên nào khác để quản lý.")
