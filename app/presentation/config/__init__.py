"""Public configuration surface for presentation bootstrap."""

from app.presentation.config.app_config import (
    APP_STYLE,
    APP_THEME_OPTIONS,
    APP_TOASTER_POSITION,
    build_app_theme,
)
from app.presentation.config.routes import (
    BACKOFFICE_PAGE_ROUTES,
    CORE_ROUTES,
    PORTAL_PAGE_ROUTES,
    PageRoute,
)

__all__ = [
    "APP_STYLE",
    "APP_THEME_OPTIONS",
    "APP_TOASTER_POSITION",
    "build_app_theme",
    "PageRoute",
    "CORE_ROUTES",
    "BACKOFFICE_PAGE_ROUTES",
    "PORTAL_PAGE_ROUTES",
]
