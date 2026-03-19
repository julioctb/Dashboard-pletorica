"""Página de ficha de empleado para el portal RRHH."""

import reflex as rx

from .components import contenido_ficha_empleado
from .state import EmpleadoFichaState


def empleado_ficha_page() -> rx.Component:
    """Página principal de ficha del empleado."""
    return rx.box(
        contenido_ficha_empleado(),
        width="100%",
        min_height="100vh",
        on_mount=EmpleadoFichaState.on_mount_empleado_ficha,
    )
