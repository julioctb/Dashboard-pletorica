"""Backoffice route registry."""

import reflex as rx

from core.bootstrap.pages import backoffice_page
from core.presentation.config.routes import BACKOFFICE_PAGE_ROUTES


def register_backoffice_routes(app: rx.App) -> None:
    """Register all backoffice routes using the shared shell."""
    for route, page_factory in BACKOFFICE_PAGE_ROUTES:
        app.add_page(backoffice_page(page_factory), route=route)


__all__ = ["BACKOFFICE_PAGE_ROUTES", "register_backoffice_routes"]
