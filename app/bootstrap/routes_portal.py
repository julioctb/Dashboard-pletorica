"""Portal route registry."""

import reflex as rx

from app.bootstrap.pages import portal_page
from app.presentation.config.routes import PORTAL_PAGE_ROUTES


def register_portal_routes(app: rx.App) -> None:
    """Register all portal routes using the shared shell."""
    for route, page_factory in PORTAL_PAGE_ROUTES:
        app.add_page(portal_page(page_factory), route=route)


__all__ = ["PORTAL_PAGE_ROUTES", "register_portal_routes"]
