"""
Layout principal del portal de cliente.

Provee la funcion portal_index() que envuelve las paginas del portal
con el sidebar de cliente y el area de contenido.
"""
import reflex as rx

from app.presentation.theme import Colors
from app.presentation.portal.layout.portal_sidebar import portal_sidebar
from app.presentation.components.shared.auth_state import AuthState


def portal_index(content: rx.Component) -> rx.Component:
    """
    Layout del portal: sidebar de cliente + contenido.

    Uso en app.py:
        app.add_page(
            lambda: portal_index(portal_dashboard_page()),
            route="/portal",
        )
    """
    return rx.box(
        rx.cond(
            AuthState.debe_redirigir_login,
            rx.center(
                rx.spinner(size="3"),
                height="100vh",
            ),
            rx.hstack(
                portal_sidebar(),
                rx.box(
                    content,
                    background_color=Colors.BACKGROUND,
                    width="100%",
                    flex="1",
                    overflow_y="auto",
                    style={
                        "minHeight": "calc(100vh - 140px)",
                        "padding": "1.5rem",
                    },
                ),
                width="100%",
                spacing="0",
            ),
        ),
        on_mount=AuthState.verificar_y_redirigir,
    )
