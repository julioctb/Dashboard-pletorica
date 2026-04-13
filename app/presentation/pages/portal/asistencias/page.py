"""
Pagina de asistencias del portal de operaciones.
"""
import reflex as rx

from app.presentation.layouts.backoffice import page_header, page_layout
from app.presentation.theme import Colors, Layout

from .components import (
    configuracion_asistencias,
    modal_incidencia,
    modal_horario,
    modal_supervision,
    resumen_jornada,
    tabla_asistencias,
    toolbar_asistencias,
)
from .state import AsistenciasState

def asistencias_page() -> rx.Component:
    """Pagina principal del modulo de asistencias."""
    return rx.box(
        rx.box(
            page_layout(
                header=page_header(
                    titulo="Asistencias",
                    subtitulo="Operacion, precargas y configuracion operativa",
                    icono="clipboard-check",
                    color_icono=Colors.PORTAL_ACCENT_SCHEME,
                ),
                toolbar=toolbar_asistencias(),
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
            max_width=Layout.CONTENT_MAX_WIDTH_COMPACT,
            margin_x="auto",
        ),
        width="100%",
        min_height="100vh",
        on_mount=AsistenciasState.on_mount_asistencias,
    )
