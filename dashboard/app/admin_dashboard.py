# -*- coding: utf-8 -*-
"""
dashboard/app/admin_dashboard.py
Admin Dashboard cho RinRec — quản lý hệ thống, người dùng, và analytics.
"""
import os
import sys

_root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _root_dir not in sys.path:
    sys.path.insert(0, _root_dir)

import streamlit as st

st.set_page_config(
    page_title="RinRec Admin Dashboard",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;700;800&display=swap');
html, body, [class*="css"] { font-family: 'Plus Jakarta Sans', sans-serif; }
</style>
""", unsafe_allow_html=True)

st.title("🛡️ RinRec Admin Dashboard")
st.caption("Quản trị hệ thống — Người dùng, Logs, và Analytics")

try:
    from backend.app.core.mongo_connector import get_database, test_connection
    from backend.app.core.auth import get_all_users

    col1, col2, col3 = st.columns(3)

    with col1:
        db_ok = test_connection()
        st.metric("🔌 MongoDB Atlas", "✅ Kết nối" if db_ok else "❌ Mất kết nối")

    with col2:
        users = get_all_users()
        st.metric("👥 Tổng nhân viên", len(users))

    with col3:
        db = get_database()
        logs = db["consultation_logs"].count_documents({})
        st.metric("📋 Nhật ký tư vấn", logs)

    st.subheader("👥 Danh Sách Tài Khoản Nhân Viên")
    import pandas as pd
    df_users = pd.DataFrame([{k: v for k, v in u.items() if k != "password_hash"} for u in users])
    if not df_users.empty:
        st.dataframe(df_users, use_container_width=True)

except Exception as e:
    st.error(f"⚠️ Lỗi kết nối backend: {e}")
    st.info("Chạy `make run-backend` để khởi động API trước.")
