"""
Detalle de expediente de empleados dentro del portal.
"""
import reflex as rx

from .components import (
    detalle_expediente,
    modal_preview_documento,
    modal_rechazo,
)
from .state import ExpedientesState


def expedientes_page() -> rx.Component:
    """Pagina detalle de expediente bajo el modulo de empleados."""
    return rx.box(
        detalle_expediente(),
        modal_rechazo(),
        modal_preview_documento(),
        width="100%",
        min_height="100vh",
        on_mount=ExpedientesState.on_mount_expedientes,
    )
