"""Shells reutilizables para pantallas autenticadas con sidebar fijo."""

import reflex as rx

from app.presentation.components.shared.auth_state import AuthState
from app.presentation.theme import (
    APP_SHELL_CONTENT_INNER_STYLE,
    APP_SHELL_CONTENT_VIEWPORT_STYLE,
    APP_SHELL_STYLE,
)


def _fullscreen_spinner() -> rx.Component:
    """Spinner de pantalla completa para estados de auth/redirección."""
    return rx.center(
        rx.spinner(size="3"),
        width="100%",
        height="100vh",
    )


def sidebar_shell(
    *,
    sidebar_component: rx.Component,
    content: rx.Component,
) -> rx.Component:
    """Layout base con sidebar fijo y contenido con scroll independiente."""
    return rx.hstack(
        rx.box(
            sidebar_component,
            height="100vh",
            flex_shrink="0",
            overflow="visible",
        ),
        rx.box(
            rx.box(
                content,
                **APP_SHELL_CONTENT_INNER_STYLE,
            ),
            **APP_SHELL_CONTENT_VIEWPORT_STYLE,
        ),
        spacing="0",
        **APP_SHELL_STYLE,
    )


def authenticated_sidebar_shell(
    *,
    sidebar_component: rx.Component,
    content: rx.Component,
) -> rx.Component:
    """Shell autenticado compartido para portal y backoffice."""
    return rx.box(
        rx.cond(
            ~AuthState.auth_contexto_listo,
            _fullscreen_spinner(),
            rx.cond(
                AuthState.debe_redirigir_login,
                _fullscreen_spinner(),
                sidebar_shell(
                    sidebar_component=sidebar_component,
                    content=content,
                ),
            ),
        ),
        width="100%",
        height="100vh",
        overflow="hidden",
        on_mount=AuthState.verificar_y_redirigir,
    )
