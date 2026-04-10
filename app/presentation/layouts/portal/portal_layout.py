"""
Layout principal del portal de cliente.

Provee la funcion portal_index() que envuelve las paginas del portal
con el sidebar de cliente y el area de contenido.
"""
import reflex as rx

from app.presentation.layouts.backoffice.shell_layout import authenticated_sidebar_shell
from app.presentation.layouts.portal.portal_sidebar import portal_sidebar
from app.presentation.theme import content_container


def portal_index(content: rx.Component) -> rx.Component:
    """
    Layout del portal: sidebar de cliente + contenido.

    Nota: el shell NO usa `key=id_empresa_actual` para remontar al cambiar
    empresa. Ese patrón causaba doble mount (y por tanto doble skeleton) en
    la hidratación inicial de las páginas protegidas. El refresh al cambiar
    empresa activa se dispara explícitamente desde
    `PortalState.cambiar_empresa_portal` via `rx.redirect(ruta_actual)`.
    """
    return authenticated_sidebar_shell(
        sidebar_component=portal_sidebar(),
        content=content_container(content),
    )
