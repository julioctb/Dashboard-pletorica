"""
Layout principal del portal de cliente.

Provee la funcion portal_index() que envuelve las paginas del portal
con el sidebar de cliente y el area de contenido.
"""
import reflex as rx

from app.presentation.layout.shell_layout import authenticated_sidebar_shell
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
    return authenticated_sidebar_shell(
        sidebar_component=portal_sidebar(),
        content=content,
    )
