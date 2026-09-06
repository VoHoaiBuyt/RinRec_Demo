# -*- coding: utf-8 -*-
"""
frontend/app/components/__init__.py
Reusable UI components for RinRec SmartAdvisor 360 Frontend.

Components:
  - auth_ui:          Glassmorphism login / register screens
  - responsive_utils: Viewport meta, responsive columns, card grid helpers
"""
from .auth_ui import render_auth_screen
from .responsive_utils import (
    inject_viewport_meta,
    inject_screen_size_detector,
    inject_card_grid_css,
    responsive_columns,
    render_responsive_image,
    scrollable_table_wrapper,
    metric_row,
    get_screen_size_hint,
)

__all__ = [
    "render_auth_screen",
    "inject_viewport_meta",
    "inject_screen_size_detector",
    "inject_card_grid_css",
    "responsive_columns",
    "render_responsive_image",
    "scrollable_table_wrapper",
    "metric_row",
    "get_screen_size_hint",
]
