"""Factory for the top-level Reflex application."""

import reflex as rx

from core.api.main import api_app
from core.bootstrap.reflex_patch import patch_reflex_context_defaults
from core.bootstrap.routes_backoffice import register_backoffice_routes
from core.bootstrap.routes_core import register_core_routes
from core.bootstrap.routes_portal import register_portal_routes
from core.presentation.config.app_config import (
    APP_STYLE,
    APP_TOASTER_POSITION,
    build_app_theme,
)


def create_app() -> rx.App:
    """Create the Reflex application and register all routes."""
    patch_reflex_context_defaults()

    app = rx.App(
        api_transformer=api_app,
        theme=build_app_theme(),
        toaster=rx.toast.provider(position=APP_TOASTER_POSITION),
        style=APP_STYLE,
    )

    register_core_routes(app)
    register_backoffice_routes(app)
    register_portal_routes(app)
    return app


__all__ = ["create_app"]
