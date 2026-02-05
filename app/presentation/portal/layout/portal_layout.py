"""
Layout principal del portal de cliente.

Provee la funcion portal_index() que envuelve las paginas del portal
con el sidebar de cliente y el area de contenido.
"""
import reflex as rx

from app.presentation.theme import Colors
from app.presentation.portal.layout.portal_sidebar import portal_sidebar


def portal_index(content: rx.Component) -> rx.Component:
    """
    Layout del portal: sidebar de cliente + contenido.

    Uso en app.py:
        app.add_page(
            lambda: portal_index(portal_dashboard_page()),
            route="/portal",
        )
    """
    return rx.hstack(
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
    )
