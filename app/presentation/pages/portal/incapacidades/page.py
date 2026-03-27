"""Página administrativa de incapacidades en el portal."""

from __future__ import annotations

import reflex as rx

from app.presentation.layouts.backoffice import page_header, page_layout, page_toolbar
from app.presentation.theme import Colors

from .components import (
    filtros_incapacidades_empresa,
    metricas_incapacidades_empresa,
    modal_registro_incapacidad,
    tabla_incapacidades_empresa,
)
from .state import IncapacidadState


def incapacidades_page() -> rx.Component:
    """Vista principal de incapacidades para RRHH en el portal."""
    return rx.box(
        rx.box(
            page_layout(
                header=page_header(
                    titulo="Incapacidades",
                    subtitulo=(
                        "Seguimiento administrativo y operativo de incapacidades "
                        "con sincronización a asistencias y nómina."
                    ),
                    icono="heart-pulse",
                    color_icono=Colors.PORTAL_ACCENT_SCHEME,
                    accion_principal=rx.button(
                        rx.icon("plus", size=16),
                        "Registrar incapacidad",
                        on_click=IncapacidadState.abrir_modal_registro_global,
                        color_scheme=Colors.PORTAL_ACCENT_SCHEME,
                    ),
                ),
                toolbar=page_toolbar(
                    search_value=IncapacidadState.filtro_busqueda,
                    search_placeholder=(
                        "Buscar por empleado, clave, tipo, sede, categoría o folio IMSS..."
                    ),
                    on_search_change=IncapacidadState.set_filtro_busqueda_incapacidades,
                    on_search_clear=IncapacidadState.limpiar_filtro_busqueda_incapacidades,
                    show_view_toggle=False,
                    filters=filtros_incapacidades_empresa(),
                    wrapped=False,
                    compact=True,
                    search_min_width="0px",
                    search_max_width=None,
                    search_flex="1 1 0px",
                ),
                content=rx.vstack(
                    metricas_incapacidades_empresa(),
                    tabla_incapacidades_empresa(),
                    modal_registro_incapacidad(),
                    spacing="4",
                    width="100%",
                ),
            ),
            width="100%",
            max_width="1120px",
            margin_x="auto",
        ),
        width="100%",
        min_height="100vh",
        on_mount=IncapacidadState.on_mount_incapacidades,
    )
