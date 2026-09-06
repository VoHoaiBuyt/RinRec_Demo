# -*- coding: utf-8 -*-
"""
frontend/app/components/responsive_utils.py
Responsive layout utilities for RinRec SmartAdvisor 360 Streamlit frontend.

Provides:
  - responsive_columns()  — tự động điều chỉnh số cột theo viewport width
  - inject_viewport_meta()— inject <meta viewport> chuẩn để mobile render đúng
  - render_responsive_image() — ảnh tự co giãn với max-width
  - card_grid_css()       — CSS grid helper cho customer card grid
  - get_screen_size_hint()— gợi ý kích thước màn hình từ URL query param
"""
import streamlit as st
from typing import Optional, List


# ─── Viewport meta injection ──────────────────────────────────────────────────

def inject_viewport_meta() -> None:
    """
    Inject thẻ <meta name="viewport"> chuẩn vào trang Streamlit.
    Cần thiết để mobile browsers scale đúng, không zoom out toàn bộ layout.
    Gọi một lần duy nhất sau st.set_page_config().
    """
    st.markdown(
        """
        <meta name="viewport"
              content="width=device-width, initial-scale=1.0, maximum-scale=5.0, user-scalable=yes">
        <meta name="mobile-web-app-capable" content="yes">
        <meta name="apple-mobile-web-app-capable" content="yes">
        <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
        """,
        unsafe_allow_html=True,
    )


# ─── Responsive columns ───────────────────────────────────────────────────────

def responsive_columns(
    desktop_ratios: List[float],
    tablet_ratios: Optional[List[float]] = None,
    mobile_single: bool = True,
    gap: str = "medium",
) -> list:
    """
    Trả về st.columns() với tỉ lệ phù hợp theo gợi ý kích thước màn hình.

    Streamlit không có API native để detect viewport width trong Python,
    nên hàm này dùng query param `?screen=mobile|tablet|desktop` (optional)
    hoặc mặc định trả về desktop_ratios.

    Cách dùng:
        cols = responsive_columns([1, 3], tablet_ratios=[1, 2], mobile_single=True)
        with cols[0]:
            st.metric(...)
        with cols[1]:
            st.dataframe(...)

    Args:
        desktop_ratios:  Tỉ lệ cột trên desktop (vd: [1, 3])
        tablet_ratios:   Tỉ lệ cột trên tablet (vd: [1, 2]). None = dùng desktop_ratios.
        mobile_single:   Trên mobile: dùng 1 cột duy nhất (True) hay giữ nguyên (False).
        gap:             Khoảng cách giữa cột: "small" | "medium" | "large"

    Returns:
        List các Streamlit column objects
    """
    screen = _get_screen_hint()

    if screen == "mobile" and mobile_single:
        return st.columns([1], gap=gap)
    elif screen == "tablet" and tablet_ratios is not None:
        return st.columns(tablet_ratios, gap=gap)
    else:
        return st.columns(desktop_ratios, gap=gap)


def _get_screen_hint() -> str:
    """
    Đọc query param ?screen=mobile|tablet|desktop.
    Trả về 'desktop' nếu không có hoặc không hợp lệ.

    Frontend JS có thể set param này khi tải trang:
        const w = window.innerWidth;
        const s = w <= 480 ? 'mobile' : w <= 768 ? 'tablet' : 'desktop';
        // Nếu URL chưa có, redirect: window.location.search = `?screen=${s}`
    """
    try:
        hint = st.query_params.get("screen", "desktop")
        if isinstance(hint, list):
            hint = hint[0] if hint else "desktop"
        return hint.lower() if hint in ("mobile", "tablet", "desktop") else "desktop"
    except Exception:
        return "desktop"


def get_screen_size_hint() -> str:
    """Public wrapper để đọc screen hint từ nơi khác trong app."""
    return _get_screen_hint()


# ─── Responsive image renderer ────────────────────────────────────────────────

def render_responsive_image(
    src: str,
    alt: str = "",
    max_width: str = "100%",
    width_mobile: str = "100%",
    width_tablet: str = "100%",
    border_radius: str = "12px",
    caption: Optional[str] = None,
) -> None:
    """
    Render ảnh với CSS responsive — tự co giãn theo container.

    Args:
        src:           URL hoặc base64 data URL của ảnh
        alt:           Alt text (accessibility)
        max_width:     Max-width mặc định (desktop)
        width_mobile:  Width trên mobile ≤480px
        width_tablet:  Width trên tablet ≤768px
        border_radius: Border radius cho ảnh
        caption:       Caption hiện dưới ảnh (optional)
    """
    uid = abs(hash(src[:40])) % 100000  # unique class per image
    css_cls = f"resp-img-{uid}"
    html = f"""
    <style>
    .{css_cls} {{
        width: {max_width};
        max-width: 100%;
        height: auto;
        border-radius: {border_radius};
        display: block;
    }}
    @media (max-width: 768px) {{ .{css_cls} {{ width: {width_tablet}; }} }}
    @media (max-width: 480px) {{ .{css_cls} {{ width: {width_mobile}; border-radius: calc({border_radius} * 0.8); }} }}
    </style>
    <figure style="margin:0;padding:0;">
        <img class="{css_cls}" src="{src}" alt="{alt}" loading="lazy">
        {"" if not caption else f'<figcaption style="font-size:0.78rem;color:#64748B;margin-top:4px;text-align:center;">{caption}</figcaption>'}
    </figure>
    """
    st.markdown(html, unsafe_allow_html=True)


# ─── Card grid CSS helper ─────────────────────────────────────────────────────

def inject_card_grid_css(
    min_card_width_desktop: str = "280px",
    min_card_width_tablet: str = "220px",
    min_card_width_mobile: str = "100%",
    gap: str = "1rem",
    grid_id: str = "cust-grid",
) -> None:
    """
    Inject CSS Grid tự động điều chỉnh số cột cho customer card grid.
    Dùng kết hợp với st.markdown() render HTML grid container.

    Args:
        min_card_width_desktop: Chiều rộng tối thiểu mỗi card (desktop)
        min_card_width_tablet:  Chiều rộng tối thiểu mỗi card (tablet)
        min_card_width_mobile:  Chiều rộng tối thiểu mỗi card (mobile)
        gap:                    Khoảng cách giữa các card
        grid_id:                CSS class name cho grid container
    """
    st.markdown(
        f"""
        <style>
        .{grid_id} {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax({min_card_width_desktop}, 1fr));
            gap: {gap};
            width: 100%;
        }}
        @media (max-width: 1024px) {{
            .{grid_id} {{
                grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
                gap: 0.85rem;
            }}
        }}
        @media (max-width: 768px) {{
            .{grid_id} {{
                grid-template-columns: repeat(auto-fill, minmax({min_card_width_tablet}, 1fr));
                gap: 0.75rem;
            }}
        }}
        @media (max-width: 480px) {{
            .{grid_id} {{
                grid-template-columns: 1fr;
                gap: 0.6rem;
            }}
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


# ─── Viewport detection JS injection ─────────────────────────────────────────

def inject_screen_size_detector() -> None:
    """
    Inject một đoạn JavaScript nhỏ để tự động set query param ?screen=
    dựa trên window.innerWidth — chạy một lần khi trang load.

    Khi Streamlit reload, _get_screen_hint() sẽ đọc được param này
    và responsive_columns() sẽ dùng đúng breakpoint.
    """
    st.markdown(
        """
        <script>
        (function() {
            try {
                const w = window.innerWidth;
                const s = w <= 480 ? 'mobile' : (w <= 768 ? 'tablet' : 'desktop');
                const url = new URL(window.location.href);
                if (url.searchParams.get('screen') !== s) {
                    url.searchParams.set('screen', s);
                    // Dùng replaceState để không trigger full reload
                    window.history.replaceState({}, '', url.toString());
                }
                // Cũng set lại khi resize (debounced)
                let resizeTimer;
                window.addEventListener('resize', function() {
                    clearTimeout(resizeTimer);
                    resizeTimer = setTimeout(function() {
                        const nw = window.innerWidth;
                        const ns = nw <= 480 ? 'mobile' : (nw <= 768 ? 'tablet' : 'desktop');
                        const cu = new URL(window.location.href);
                        if (cu.searchParams.get('screen') !== ns) {
                            cu.searchParams.set('screen', ns);
                            window.history.replaceState({}, '', cu.toString());
                        }
                    }, 300);
                });
            } catch(e) { /* silent fail */ }
        })();
        </script>
        """,
        unsafe_allow_html=True,
    )


# ─── Scrollable container wrapper ────────────────────────────────────────────

def scrollable_table_wrapper(html_table: str, max_height: str = "400px") -> None:
    """
    Bọc bảng HTML trong div có overflow-x:auto và max-height để
    responsive trên cả mobile lẫn desktop.

    Args:
        html_table: Chuỗi HTML bảng cần wrap
        max_height: Chiều cao tối đa (vertical scroll)
    """
    wrapper = f"""
    <div style="
        width: 100%;
        overflow-x: auto;
        overflow-y: auto;
        max-height: {max_height};
        -webkit-overflow-scrolling: touch;
        border-radius: 0 0 8px 8px;
    ">
        {html_table}
    </div>
    """
    st.markdown(wrapper, unsafe_allow_html=True)


# ─── Responsive metric row ────────────────────────────────────────────────────

def metric_row(metrics: List[dict], min_col_width: int = 150) -> None:
    """
    Render một hàng metric cards tự động wrap theo màn hình.
    Thay thế st.columns() cố định bằng CSS flexbox wrap.

    Args:
        metrics: List of dict với keys: label, value, note (optional), delta (optional)
        min_col_width: Chiều rộng tối thiểu mỗi metric card (px)

    Example:
        metric_row([
            {"label": "Khách hàng", "value": "120", "note": "+5 hôm nay"},
            {"label": "Tỷ lệ chốt", "value": "76.7%", "delta": "↑3.2%"},
        ])
    """
    cards_html = ""
    for m in metrics:
        note_html = (
            f'<div class="metric-note">{m["note"]}</div>'
            if m.get("note") else ""
        )
        delta_html = (
            f'<div style="font-size:0.78rem;color:#00B14F;font-weight:600;">{m["delta"]}</div>'
            if m.get("delta") else ""
        )
        cards_html += f"""
        <div class="metric-card" style="
            flex: 1 1 {min_col_width}px;
            min-width: {min_col_width}px;
            max-width: 300px;
        ">
            <div class="metric-label">{m.get('label','')}</div>
            <div class="metric-value">{m.get('value','—')}</div>
            {note_html}{delta_html}
        </div>
        """

    html = f"""
    <div style="
        display: flex;
        flex-wrap: wrap;
        gap: 0.75rem;
        margin-bottom: 1rem;
    ">
        {cards_html}
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)
