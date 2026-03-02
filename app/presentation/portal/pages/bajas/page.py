"""
Pagina de Bajas de Personal del portal RRHH.
"""
import reflex as rx

from app.presentation.layout import page_layout, page_header, page_toolbar

from .state import BajasState
from .components import alertas_liquidacion, filtros_bajas, tabla_bajas, modal_cancelacion


def bajas_page() -> rx.Component:
    """Pagina de bajas del portal."""
    return rx.box(
        page_layout(
            header=page_header(
                titulo="Bajas de Personal",
                subtitulo="Seguimiento de liquidacion y cierre de bajas",
                icono="user-minus",
            ),
            toolbar=page_toolbar(
                search_value=BajasState.filtro_busqueda,
                search_placeholder="Buscar por empleado, clave o motivo...",
                on_search_change=BajasState.set_filtro_busqueda,
                on_search_clear=lambda: BajasState.set_filtro_busqueda(""),
                show_view_toggle=False,
                filters=filtros_bajas(),
            ),
            content=rx.vstack(
                alertas_liquidacion(),
                tabla_bajas(),
                modal_cancelacion(),
                spacing="4",
                width="100%",
            ),
        ),
        width="100%",
        min_height="100vh",
        on_mount=BajasState.on_mount_bajas,
    )
