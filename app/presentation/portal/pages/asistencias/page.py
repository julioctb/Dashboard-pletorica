"""
Pagina de asistencias del portal de operaciones.
"""
import reflex as rx

from app.presentation.layout import page_header, page_layout, page_toolbar

from .components import (
    configuracion_asistencias,
    filtros_asistencias,
    modal_incidencia,
    modal_horario,
    modal_supervision,
    resumen_jornada,
    tabla_asistencias,
)
from .state import AsistenciasState


def asistencias_page() -> rx.Component:
    """Pagina principal del modulo de asistencias."""
    return rx.box(
        page_layout(
            header=page_header(
                titulo="Asistencias",
                subtitulo="Operacion, precargas RH y configuracion operativa en un mismo modulo",
                icono="clipboard-check",
            ),
            toolbar=page_toolbar(
                search_value=AsistenciasState.filtro_busqueda,
                search_placeholder=AsistenciasState.placeholder_busqueda,
                on_search_change=AsistenciasState.set_filtro_busqueda,
                on_search_clear=lambda: AsistenciasState.set_filtro_busqueda(""),
                filters=filtros_asistencias(),
                extra_right=rx.fragment(),
                show_view_toggle=False,
            ),
            content=rx.vstack(
                rx.cond(
                    AsistenciasState.panel_es_configuracion,
                    configuracion_asistencias(),
                    rx.vstack(
                        resumen_jornada(),
                        tabla_asistencias(),
                        spacing="4",
                        width="100%",
                    ),
                ),
                modal_incidencia(),
                modal_horario(),
                modal_supervision(),
                spacing="4",
                width="100%",
            ),
        ),
        width="100%",
        min_height="100vh",
        on_mount=AsistenciasState.on_mount_asistencias,
    )
