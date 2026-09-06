# -*- coding: utf-8 -*-
"""
frontend/app/components/auth_ui.py
Glassmorphism Authentication Component (Login & Register / Sign Up).
Thiết kế pixel-perfect theo mẫu UI Glassmorphism tím sang trọng.
Được tách thành component độc lập để tối ưu bảo trì và hiệu năng.
"""
import time
from typing import Callable, Optional, Dict, Any
import streamlit as st


# ─── CSS Theme: Premium Glassmorphism Violet ──────────────────────────────────
AUTH_GLASS_CSS = """
<style>
/* ── Container Background Gradient ─────────────────────────────────────────── */
.stApp {
    background: radial-gradient(circle at 50% 20%, #6352d0 0%, #4a3cb4 40%, #35288f 75%, #231969 100%) !important;
    background-attachment: fixed !important;
}

/* ── Hide default Streamlit elements on Auth screen ────────────────────────── */
[data-testid="stSidebar"] {
    display: none !important;
}
header[data-testid="stHeader"] {
    background: transparent !important;
}

/* ── Centered Glass Card Wrapper ───────────────────────────────────────────── */
.auth-wrapper {
    display: flex;
    justify-content: center;
    align-items: center;
    width: 100%;
    padding: 2rem 0;
}

.auth-glass-card {
    width: 100%;
    max-width: 440px;
    background: rgba(255, 255, 255, 0.08) !important;
    backdrop-filter: blur(28px) saturate(180%) !important;
    -webkit-backdrop-filter: blur(28px) saturate(180%) !important;
    border: 1px solid rgba(255, 255, 255, 0.18) !important;
    border-radius: 28px !important;
    padding: 40px 36px 32px !important;
    box-shadow: 0 25px 50px -12px rgba(15, 7, 45, 0.55),
                0 0 35px rgba(124, 58, 237, 0.15),
                inset 0 1px 1px rgba(255, 255, 255, 0.25) !important;
    color: #ffffff !important;
    animation: fadeInScale 0.4s ease-out forwards;
}

@keyframes fadeInScale {
    from {
        opacity: 0;
        transform: scale(0.96) translateY(10px);
    }
    to {
        opacity: 1;
        transform: scale(1) translateY(0);
    }
}

/* ── Header Typography ─────────────────────────────────────────────────────── */
.auth-title {
    font-size: 1.85rem !important;
    font-weight: 700 !important;
    color: #ffffff !important;
    text-align: center !important;
    margin: 0 0 0.4rem 0 !important;
    letter-spacing: -0.02em !important;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
}

.auth-subtitle {
    font-size: 0.92rem !important;
    color: #c4b5fd !important;
    text-align: center !important;
    margin: 0 0 1.8rem 0 !important;
    font-weight: 400 !important;
    opacity: 0.85;
}

/* ── Form Inputs Override inside Glass Card ────────────────────────────────── */
[data-testid="stForm"] {
    border: none !important;
    background: transparent !important;
    padding: 0 !important;
}

div[data-testid="stTextInput"] > label,
div[data-testid="stSelectbox"] > label {
    color: #e2e8f0 !important;
    font-size: 0.84rem !important;
    font-weight: 500 !important;
    margin-bottom: 0.35rem !important;
}

div[data-testid="stTextInput"] input {
    background: rgba(255, 255, 255, 0.12) !important;
    border: 1px solid rgba(255, 255, 255, 0.18) !important;
    border-radius: 12px !important;
    color: #ffffff !important;
    font-size: 0.92rem !important;
    padding: 0.65rem 1rem !important;
    height: 46px !important;
    box-shadow: inset 0 1px 2px rgba(0, 0, 0, 0.15) !important;
    transition: all 0.2s ease !important;
}

div[data-testid="stTextInput"] input::placeholder {
    color: rgba(255, 255, 255, 0.45) !important;
}

div[data-testid="stTextInput"] input:focus {
    border-color: #38bdf8 !important;
    box-shadow: 0 0 0 3px rgba(56, 189, 248, 0.25), inset 0 1px 2px rgba(0, 0, 0, 0.15) !important;
    background: rgba(255, 255, 255, 0.16) !important;
}

/* ── Primary Submit Button (Vibrant Blue/Cyan Gradient) ───────────────────── */
div[data-testid="stFormSubmitButton"] button {
    width: 100% !important;
    background: linear-gradient(90deg, #4f46e5 0%, #3b82f6 50%, #06b6d4 100%) !important;
    border: none !important;
    border-radius: 12px !important;
    color: #ffffff !important;
    font-weight: 600 !important;
    font-size: 1rem !important;
    height: 48px !important;
    margin-top: 0.8rem !important;
    box-shadow: 0 10px 22px -5px rgba(59, 130, 246, 0.5) !important;
    transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1) !important;
    cursor: pointer !important;
}

div[data-testid="stFormSubmitButton"] button:hover {
    transform: translateY(-1.5px) !important;
    box-shadow: 0 14px 28px -5px rgba(6, 182, 212, 0.6) !important;
    opacity: 0.96 !important;
}

div[data-testid="stFormSubmitButton"] button:active {
    transform: translateY(0) !important;
}

/* ── Extras Row (Remember Me & Forgot Password) ───────────────────────────── */
.auth-extras {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin: 0.6rem 0 1.2rem 0;
    font-size: 0.84rem;
    color: #cbd5e1;
}

.auth-forgot {
    color: #38bdf8 !important;
    text-decoration: none !important;
    cursor: pointer;
    transition: color 0.2s;
}
.auth-forgot:hover {
    color: #7dd3fc !important;
    text-decoration: underline !important;
}

/* ── Divider: "or continue with" ───────────────────────────────────────────── */
.auth-divider {
    display: flex;
    align-items: center;
    text-align: center;
    margin: 1.5rem 0 1.2rem 0;
    color: rgba(255, 255, 255, 0.45);
    font-size: 0.82rem;
}

.auth-divider::before,
.auth-divider::after {
    content: '';
    flex: 1;
    border-bottom: 1px solid rgba(255, 255, 255, 0.16);
}

.auth-divider span {
    padding: 0 0.85rem;
}

/* ── Social Login Buttons ──────────────────────────────────────────────────── */
.social-btn {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 0.5rem;
    width: 100%;
    height: 42px;
    background: rgba(255, 255, 255, 0.1) !important;
    border: 1px solid rgba(255, 255, 255, 0.16) !important;
    border-radius: 12px !important;
    color: #ffffff !important;
    font-size: 0.88rem !important;
    font-weight: 500 !important;
    cursor: pointer;
    transition: all 0.2s ease;
}

.social-btn:hover {
    background: rgba(255, 255, 255, 0.18) !important;
    border-color: rgba(255, 255, 255, 0.3) !important;
    transform: translateY(-1px);
}

/* ── Footer Switch Mode Link ───────────────────────────────────────────────── */
.auth-footer {
    text-align: center;
    margin-top: 1.5rem;
    font-size: 0.86rem;
    color: #cbd5e1;
}

.auth-footer-link {
    color: #38bdf8 !important;
    font-weight: 600 !important;
    cursor: pointer;
    text-decoration: none !important;
}
.auth-footer-link:hover {
    text-decoration: underline !important;
    color: #7dd3fc !important;
}

/* ── Quick Demo Helper Pill ────────────────────────────────────────────────── */
.auth-demo-helper {
    background: rgba(0, 0, 0, 0.22);
    border: 1px dashed rgba(255, 255, 255, 0.2);
    border-radius: 12px;
    padding: 10px 14px;
    margin-top: 1.2rem;
    font-size: 0.78rem;
    color: #e2e8f0;
    text-align: center;
}
.auth-demo-badge {
    background: rgba(56, 189, 248, 0.25);
    color: #38bdf8;
    padding: 2px 6px;
    border-radius: 6px;
    font-weight: 600;
}
</style>
"""


def render_auth_screen(
    authenticate_fn: Callable[[str, str], Dict[str, Any]],
    register_fn: Callable[..., Dict[str, Any]]
) -> Optional[Dict[str, Any]]:
    """
    Hiển thị giao diện Đăng nhập / Đăng ký Glassmorphism.
    Trả về dict thông tin user nếu đăng nhập thành công, hoặc None nếu chưa xác thực.
    """
    # Nạp style Glassmorphism tím cao cấp
    st.markdown(AUTH_GLASS_CSS, unsafe_allow_html=True)

    # Quản lý chế độ auth trong session_state: 'login' | 'register'
    if "auth_mode" not in st.session_state:
        st.session_state.auth_mode = "login"

    # Layout căn giữa màn hình
    _, col_center, _ = st.columns([1, 2.2, 1])

    with col_center:
        is_login = st.session_state.auth_mode == "login"

        if is_login:
            _render_login_view(authenticate_fn)
        else:
            _render_register_view(register_fn)

    return st.session_state.get("authenticated_user")


def _render_login_view(authenticate_fn: Callable[[str, str], Dict[str, Any]]):
    """Render giao diện Đăng Nhập chuẩn theo mẫu ảnh."""
    # Header Card
    st.markdown("""
    <div style="text-align: center; margin-bottom: 0.5rem;">
        <h1 class="auth-title">Welcome Back</h1>
        <p class="auth-subtitle">Sign in to your account</p>
    </div>
    """, unsafe_allow_html=True)

    # Lấy giá trị quick fill nếu có
    default_u = st.session_state.get("quick_fill_user", "")
    default_p = st.session_state.get("quick_fill_pass", "")

    with st.form("form_glass_login"):
        username_input = st.text_input(
            label="Email or Username",
            value=default_u,
            placeholder="Email Address",
            label_visibility="collapsed"
        )

        password_input = st.text_input(
            label="Password",
            value=default_p,
            type="password",
            placeholder="Password",
            label_visibility="collapsed"
        )

        # Extras: Remember me & Forgot Password
        st.markdown("""
        <div class="auth-extras">
            <label style="display: flex; align-items: center; gap: 6px; cursor: pointer; user-select: none;">
                <input type="checkbox" checked style="accent-color: #38bdf8; cursor: pointer;">
                <span>Remember me</span>
            </label>
            <span class="auth-forgot">Forgot password?</span>
        </div>
        """, unsafe_allow_html=True)

        submit_login = st.form_submit_button("Sign In", use_container_width=True)

        if submit_login:
            if not username_input.strip() or not password_input.strip():
                st.error("⚠️ Vui lòng nhập đầy đủ Email / Tên đăng nhập và Mật khẩu.")
            else:
                with st.spinner("Đang xác thực bảo mật..."):
                    res = authenticate_fn(username_input, password_input)
                    if res.get("success"):
                        st.session_state.authenticated_user = res.get("user")
                        st.toast(res.get("message", "Đăng nhập thành công!"))
                        time.sleep(0.3)
                        st.rerun()
                    else:
                        st.error(f"❌ {res.get('message')}")

    # Divider: or continue with
    st.markdown("""
    <div class="auth-divider">
        <span>or continue with</span>
    </div>
    """, unsafe_allow_html=True)

    # Social Login Buttons (Google & GitHub Quick Access)
    c_soc1, c_soc2 = st.columns(2)
    with c_soc1:
        if st.button("🌐 Google (GDV)", key="btn_quick_google", use_container_width=True):
            st.session_state["quick_fill_user"] = "gdv_ha"
            st.session_state["quick_fill_pass"] = "GDV@123"
            st.rerun()

    with c_soc2:
        if st.button("🐙 GitHub (Admin)", key="btn_quick_github", use_container_width=True):
            st.session_state["quick_fill_user"] = "admin"
            st.session_state["quick_fill_pass"] = "Admin@123"
            st.rerun()

    # Switch to Register
    st.markdown("<div style='margin-top: 1rem;'></div>", unsafe_allow_html=True)
    c_sw1, c_sw2, c_sw3 = st.columns([1, 2, 1])
    with c_sw2:
        if st.button("Don't have an account? Sign up", key="btn_switch_register", use_container_width=True):
            st.session_state.auth_mode = "register"
            st.rerun()

    # Helper Demo Info Box
    st.markdown("""
    <div class="auth-demo-helper">
        🔑 <b>Tài khoản mẫu:</b> Admin: <span class="auth-demo-badge">admin</span> / <span class="auth-demo-badge">Admin@123</span> &nbsp;|&nbsp; 
        GDV: <span class="auth-demo-badge">gdv_ha</span> / <span class="auth-demo-badge">GDV@123</span>
    </div>
    """, unsafe_allow_html=True)


def _render_register_view(register_fn: Callable[..., Dict[str, Any]]):
    """Render giao diện Đăng Ký (Sign Up) tài khoản mới."""
    st.markdown("""
    <div style="text-align: center; margin-bottom: 0.5rem;">
        <h1 class="auth-title">Create Account</h1>
        <p class="auth-subtitle">Sign up for a new account</p>
    </div>
    """, unsafe_allow_html=True)

    with st.form("form_glass_register"):
        full_name = st.text_input(
            label="Full Name",
            placeholder="Full Name (Họ và Tên)",
            label_visibility="collapsed"
        )

        email = st.text_input(
            label="Email Address",
            placeholder="Email Address (vd: user@vpbank.com.vn)",
            label_visibility="collapsed"
        )

        username = st.text_input(
            label="Username",
            placeholder="Username (Tên đăng nhập)",
            label_visibility="collapsed"
        )

        col_p1, col_p2 = st.columns(2)
        with col_p1:
            password = st.text_input(
                label="Password",
                type="password",
                placeholder="Password (≥ 6 ký tự)",
                label_visibility="collapsed"
            )
        with col_p2:
            confirm_password = st.text_input(
                label="Confirm Password",
                type="password",
                placeholder="Confirm Password",
                label_visibility="collapsed"
            )

        role = st.selectbox(
            "Vai trò nghiệp vụ:",
            options=["GDV", "MANAGER"],
            format_func=lambda r: "🏢 Giao Dịch Viên (GDV)" if r == "GDV" else "📊 Giám Đốc Chi Nhánh (Manager)"
        )

        submit_register = st.form_submit_button("Sign Up", use_container_width=True)

        if submit_register:
            if not full_name.strip() or not username.strip() or not password.strip():
                st.error("⚠️ Vui lòng điền đầy đủ Họ tên, Tên đăng nhập và Mật khẩu.")
            elif len(password) < 6:
                st.error("⚠️ Mật khẩu phải từ 6 ký tự trở lên.")
            elif password != confirm_password:
                st.error("❌ Mật khẩu xác nhận không khớp!")
            else:
                with st.spinner("Đang khởi tạo tài khoản mới..."):
                    res = register_fn(
                        username=username.strip(),
                        password=password.strip(),
                        full_name=full_name.strip(),
                        email=email.strip() if email else None,
                        role=role
                    )
                    if res.get("success"):
                        st.success(res.get("message"))
                        time.sleep(1.2)
                        st.session_state.auth_mode = "login"
                        st.session_state["quick_fill_user"] = username.strip()
                        st.session_state["quick_fill_pass"] = password.strip()
                        st.rerun()
                    else:
                        st.error(f"❌ {res.get('message')}")

    # Switch back to Login
    st.markdown("<div style='margin-top: 1rem;'></div>", unsafe_allow_html=True)
    c_sw1, c_sw2, c_sw3 = st.columns([1, 2, 1])
    with c_sw2:
        if st.button("Already have an account? Sign in", key="btn_switch_login", use_container_width=True):
            st.session_state.auth_mode = "login"
            st.rerun()
