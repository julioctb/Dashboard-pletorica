"""Core routes shared across application shells."""

import reflex as rx

from core.presentation.config.routes import CORE_ROUTES


def register_core_routes(app: rx.App) -> None:
    """Register shell-agnostic routes."""
    for route, page in CORE_ROUTES:
        app.add_page(page, route=route)


__all__ = ["CORE_ROUTES", "register_core_routes"]
