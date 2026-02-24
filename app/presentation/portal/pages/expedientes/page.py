"""
Pagina Expedientes del portal de cliente.

Muestra lista de empleados en onboarding con acceso
al detalle de su expediente documental.
"""
import reflex as rx

from app.presentation.layout import page_layout, page_header, page_toolbar

from .state import ExpedientesState
from .components import (
    tabla_expedientes,
    filtros_expedientes,
    detalle_expediente,
    modal_rechazo,
)


def expedientes_page() -> rx.Component:
    """Pagina de expedientes del portal."""
    return rx.box(
        rx.cond(
            ExpedientesState.mostrando_detalle,
            # Vista detalle
            rx.box(
                detalle_expediente(),
                modal_rechazo(),
                width="100%",
                min_height="100vh",
            ),
            # Vista lista
            page_layout(
                header=page_header(
                    titulo="Expedientes",
                    subtitulo="Revision de expedientes documentales de empleados",
                    icono="folder-check",
                ),
                toolbar=page_toolbar(
                    search_value=ExpedientesState.filtro_busqueda,
                    search_placeholder="Buscar por nombre o clave...",
                    on_search_change=ExpedientesState.set_filtro_busqueda,
                    on_search_clear=lambda: ExpedientesState.set_filtro_busqueda(""),
                    show_view_toggle=False,
                    filters=filtros_expedientes(),
                ),
                content=tabla_expedientes(),
            ),
        ),
        width="100%",
        min_height="100vh",
        on_mount=ExpedientesState.on_mount_expedientes,
    )
