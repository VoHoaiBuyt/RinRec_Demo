# -*- coding: utf-8 -*-
"""
dashboard/app/admin_dashboard_complete.py
Admin Dashboard with Pilot Metrics & Plotly charts for RinRec SmartAdvisor 360.
"""
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import requests
from datetime import datetime, timedelta

st.set_page_config(page_title="RinRec Admin Dashboard", layout="wide", page_icon="📊")

API_BASE = "http://localhost:8000/api/v1"

# CSS
st.markdown("""
<style>
.metric-card {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 1.5rem;
    border-radius: 12px;
    text-align: center;
}
.metric-value {
    font-size: 2.5rem;
    font-weight: 700;
}
.metric-label {
    font-size: 0.9rem;
    opacity: 0.9;
    margin-top: 0.5rem;
}
</style>
""", unsafe_allow_html=True)

#=== SIDEBAR LOGIN ===
with st.sidebar:
    st.title("🛡️ Admin Dashboard")
    
    if "admin_token" not in st.session_state:
        username = st.text_input("Admin Username")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            resp = requests.post(f"{API_BASE}/auth/login", json={"username": username, "password": password})
            if resp.status_code == 200 and resp.json().get("user", {}).get("role") in ("ADMIN", "MANAGER"):
                st.session_state["admin_token"] = resp.json()["access_token"]
                st.session_state["admin_user"] = resp.json()["user"]
                st.success("Logged in!")
                st.rerun()
            else:
                st.error("Admin access only")
        st.stop()
    
    user = st.session_state.get("admin_user", {})
    st.success(f"👤 {user.get('full_name')}")
    if st.button("Logout"):
        st.session_state.clear()
        st.rerun()

token = st.session_state["admin_token"]
headers = {"Authorization": f"Bearer {token}"}

#=== MAIN CONTENT ===
st.title("📊 RinRec SmartAdvisor 360 - Admin Dashboard")

# Fetch pilot metrics
try:
    metrics_resp = requests.get(f"{API_BASE}/metrics", headers=headers, timeout=5)
    if metrics_resp.status_code == 200:
        metrics = metrics_resp.json()
    else:
        metrics = None
except:
    metrics = None

if metrics:
    st.header("🎯 Pilot Metrics (Chỉ số kinh doanh)")
    
    # KPI Row 1
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{metrics['aht_after']:.1f} min</div>
            <div class="metric-label">AHT (After RinRec)</div>
            <div style="font-size:0.8rem;margin-top:0.5rem;">↓ {metrics['aht_improvement']:.1f}%</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{metrics['conversion_rate']:.1f}%</div>
            <div class="metric-label">Conversion Rate</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{metrics['roi_estimate']:.0f}%</div>
            <div class="metric-label">ROI Estimate</div>
        </div>
        """, unsafe_allow_html=True)
    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{metrics['nps_score']}</div>
            <div class="metric-label">NPS Score</div>
        </div>
        """, unsafe_allow_html=True)
    
    # KPI Row 2
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Customers Served (Increase)", f"+{metrics['customers_served_increase']}")
    with col2:
        cost_savings_bn = metrics['cost_savings'] / 1_000_000_000
        st.metric("Cost Savings (VND)", f"{cost_savings_bn:.2f} tỷ/năm")

st.divider()

# Charts
st.header("📈 Analytics & Performance")

tab1, tab2, tab3, tab4 = st.tabs(["Transactions", "Top Products", "Teller Performance", "Audit Logs"])

with tab1:
    st.subheader("Giao dịch theo thời gian")
    # Mock data
    dates = pd.date_range(end=datetime.now(), periods=30, freq='D')
    txn_counts = [20 + i % 10 + (i // 5) * 2 for i in range(30)]
    df_txn = pd.DataFrame({'Ngày': dates, 'Số giao dịch': txn_counts})
    
    fig = px.line(df_txn, x='Ngày', y='Số giao dịch', title='Daily Transactions (30 days)', markers=True)
    fig.update_layout(height=400)
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.subheader("Top sản phẩm được tư vấn")
    products = pd.DataFrame({
        'Sản phẩm': ['Thẻ tín dụng', 'Vay tiêu dùng', 'Tiết kiệm', 'Bảo hiểm', 'Đầu tư'],
        'Số lần gợi ý': [450, 320, 280, 150, 90]
    })
    fig2 = px.bar(products, x='Sản phẩm', y='Số lần gợi ý', color='Sản phẩm', title='Top Products Recommended')
    fig2.update_layout(showlegend=False, height=400)
    st.plotly_chart(fig2, use_container_width=True)

with tab3:
    st.subheader("Hiệu suất Teller")
    tellers = pd.DataFrame({
        'Teller': ['Nguyễn Văn A', 'Trần Thị B', 'Lê Minh C', 'Phạm Thu D'],
        'Số ca tư vấn': [120, 98, 105, 87],
        'Tỷ lệ chấp nhận': [0.85, 0.78, 0.82, 0.75]
    })
    st.dataframe(tellers.style.format({'Tỷ lệ chấp nhận': '{:.1%}'}), use_container_width=True)
    
    # Bar chart
    fig3 = px.bar(tellers, x='Teller', y='Số ca tư vấn', title='Consultations by Teller')
    st.plotly_chart(fig3, use_container_width=True)

with tab4:
    st.subheader("Audit Logs (Real-time)")
    # Fetch audit logs
    try:
        logs_resp = requests.get(f"{API_BASE}/audit_logs?limit=20", headers=headers, timeout=5)
        if logs_resp.status_code == 200:
            logs = logs_resp.json()
            if logs:
                df_logs = pd.DataFrame(logs)
                st.dataframe(df_logs, use_container_width=True)
            else:
                st.info("No audit logs yet")
        else:
            st.warning("Could not fetch audit logs")
    except:
        st.error("API connection error")

st.divider()
st.caption("© 2024 VPBank RinRec SmartAdvisor 360 | Admin Dashboard")
