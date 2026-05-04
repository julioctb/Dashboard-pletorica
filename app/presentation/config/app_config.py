"""Configuracion central de la capa de presentacion."""

import reflex as rx

from app.presentation.theme import GLOBAL_STYLES
from app.presentation.theme.feedback import DEFAULT_TOAST_POSITION

APP_THEME_OPTIONS: dict[str, str | bool] = {
    "appearance": "light",
    "has_background": True,
    "radius": "medium",
    "scaling": "100%",
    "accent_color": "blue",
}

APP_STYLE = GLOBAL_STYLES
APP_TOASTER_POSITION = DEFAULT_TOAST_POSITION


def build_app_theme() -> rx.Component:
    """Build the shared Reflex theme configuration."""
    return rx.theme(**APP_THEME_OPTIONS)


__all__ = [
    "APP_STYLE",
    "APP_THEME_OPTIONS",
    "APP_TOASTER_POSITION",
    "build_app_theme",
]
