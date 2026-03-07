"""
Página de lista de períodos de nómina.

Ruta: /nominas
Acceso: es_rrhh | es_contabilidad | es_admin_empresa
"""
import reflex as rx

from app.core.ui_helpers import FILTRO_TODOS
from app.presentation.pages.nominas.nomina_rrhh_state import NominaRRHHState
from app.presentation.pages.nominas.nomina_contabilidad_state import NominaContabilidadState
from app.presentation.pages.nominas.nomina_modals import modal_crear_periodo
from app.presentation.pages.nominas.dashboard_state import NominaDashboardState
from app.presentation.pages.nominas.dashboard_page import (
    selector_periodo,
    grid_kpis,
    card_comparativo,
)
from app.presentation.components.ui import (
    tabla_vacia,
    table_shell,
    table_cell_text_sm,
    skeleton_tabla,
    input_busqueda,
    contador_registros,
)
from app.presentation.layout import page_layout, page_header, page_toolbar
from app.presentation.theme import Colors, Spacing, Typography, Radius


# =============================================================================
# BADGE DE ESTATUS
# =============================================================================

def _badge_estatus(estatus: rx.Var) -> rx.Component:
    """Badge de color según el estatus del período."""
    return rx.match(
        estatus,
        ('BORRADOR',
         rx.badge('Borrador', color_scheme='gray', size='1')),
        ('EN_PREPARACION_RRHH',
         rx.badge('Preparando', color_scheme='blue', size='1')),
        ('ENVIADO_A_CONTABILIDAD',
         rx.badge('Enviado', color_scheme='orange', size='1')),
        ('EN_PROCESO_CONTABILIDAD',
         rx.badge('En proceso', color_scheme='purple', size='1')),
        ('CALCULADO',
         rx.badge('Calculado', color_scheme='green', size='1')),
        ('CERRADO',
         rx.badge('Cerrado', color_scheme='gray', size='1', variant='surface')),
        rx.badge(estatus, size='1'),
    )


# =============================================================================
# TABLA DE PERÍODOS
# =============================================================================

ENCABEZADOS = [
    {"nombre": "Nombre", "ancho": "220px"},
    {"nombre": "Periodicidad", "ancho": "100px"},
    {"nombre": "Período", "ancho": "180px"},
    {"nombre": "Estatus", "ancho": "140px"},
    {"nombre": "Empleados", "ancho": "90px"},
    {"nombre": "Neto total", "ancho": "110px"},
    {"nombre": "Acciones", "ancho": "80px"},
]


def _fila_periodo(periodo: dict) -> rx.Component:
    """Fila de la tabla de períodos."""
    fechas = rx.text(
        periodo['fecha_inicio'].to(str) + "  →  " + periodo['fecha_fin'].to(str),
        size="2",
        color=Colors.TEXT_SECONDARY,
    )
    return rx.table.row(
        rx.table.cell(
            rx.text(
                periodo['nombre'],
                size="2",
                weight="medium",
                color=Colors.TEXT_PRIMARY,
                max_width="220px",
                overflow="hidden",
                text_overflow="ellipsis",
                white_space="nowrap",
            ),
        ),
        rx.table.cell(
            rx.badge(
                rx.match(
                    periodo['periodicidad'],
                    ('QUINCENAL', 'Quincenal'),
                    ('SEMANAL', 'Semanal'),
                    ('MENSUAL', 'Mensual'),
                    periodo['periodicidad'],
                ),
                color_scheme='blue',
                variant='soft',
                size='1',
            ),
        ),
        rx.table.cell(fechas),
        rx.table.cell(_badge_estatus(periodo['estatus'])),
        table_cell_text_sm(periodo['total_empleados'].to(str), tone="muted"),
        rx.table.cell(
            rx.text(
                "$" + periodo['total_neto'].to(str),
                size="2",
                weight="medium",
                color=Colors.SUCCESS,
            ),
        ),
        rx.table.cell(
            rx.hstack(
                # Botón RRHH — preparación (siempre visible para RRHH)
                rx.cond(
                    NominaRRHHState.es_rrhh,
                    rx.tooltip(
                        rx.icon_button(
                            rx.icon("folder-open", size=15),
                            size="2",
                            variant="soft",
                            color_scheme="blue",
                            on_click=NominaRRHHState.abrir_periodo(periodo),
                        ),
                        content="Abrir preparación (RRHH)",
                    ),
                    rx.fragment(),
                ),
                # Botón Contabilidad — visible cuando el período está en flujo de Contabilidad
                rx.cond(
                    NominaRRHHState.es_contabilidad & (
                        (periodo['estatus'] == 'ENVIADO_A_CONTABILIDAD')
                        | (periodo['estatus'] == 'EN_PROCESO_CONTABILIDAD')
                        | (periodo['estatus'] == 'CALCULADO')
                        | (periodo['estatus'] == 'CERRADO')
                    ),
                    rx.tooltip(
                        rx.icon_button(
                            rx.icon("calculator", size=15),
                            size="2",
                            variant="soft",
                            color_scheme="purple",
                            on_click=NominaContabilidadState.abrir_periodo_calculo(periodo),
                        ),
                        content="Vista Contabilidad",
                    ),
                    rx.fragment(),
                ),
                spacing="1",
            ),
        ),
    )


def _tabla_periodos() -> rx.Component:
    return table_shell(
        loading=NominaRRHHState.loading,
        headers=ENCABEZADOS,
        rows=NominaRRHHState.periodos_filtrados,
        row_renderer=_fila_periodo,
        has_rows=NominaRRHHState.tiene_periodos,
        empty_component=tabla_vacia(
            mensaje="No hay períodos de nómina",
            onclick=NominaRRHHState.abrir_modal_periodo,
        ),
        total_caption=(
            "Mostrando " + NominaRRHHState.periodos_filtrados.length().to(str) + " período(s)"
        ),
        loading_rows=4,
    )


# =============================================================================
# FILTROS
# =============================================================================

def _filtro_estatus() -> rx.Component:
    """Select para filtrar por estatus."""
    return rx.select.root(
        rx.select.trigger(placeholder="Todos los estatus", width="200px"),
        rx.select.content(
            rx.select.item("Todos", value=FILTRO_TODOS),
            rx.select.item("Borrador", value="BORRADOR"),
            rx.select.item("Preparando", value="EN_PREPARACION_RRHH"),
            rx.select.item("Enviado", value="ENVIADO_A_CONTABILIDAD"),
            rx.select.item("En proceso", value="EN_PROCESO_CONTABILIDAD"),
            rx.select.item("Calculado", value="CALCULADO"),
            rx.select.item("Cerrado", value="CERRADO"),
        ),
        value=NominaRRHHState.filtro_estatus_periodos,
        on_change=NominaRRHHState.set_filtro_estatus_periodos,
    )


# =============================================================================
# PÁGINA
# =============================================================================

def periodos_nomina_page() -> rx.Component:
    """Página de lista de períodos de nómina."""
    return rx.box(
        page_layout(
            header=page_header(
                titulo="Nóminas",
                subtitulo="Gestión de períodos de nómina",
                icono="calculator",
                accion_principal=rx.cond(
                    NominaRRHHState.es_rrhh,
                    rx.button(
                        rx.icon("plus", size=16),
                        "Nuevo período",
                        on_click=NominaRRHHState.abrir_modal_periodo,
                        color_scheme="blue",
                    ),
                    rx.fragment(),
                ),
            ),
            toolbar=page_toolbar(
                search_value=NominaRRHHState.filtro_busqueda,
                search_placeholder="Buscar por nombre...",
                on_search_change=NominaRRHHState.set_filtro_busqueda,
                on_search_clear=lambda: NominaRRHHState.set_filtro_busqueda(""),
                filters=_filtro_estatus(),
                show_view_toggle=False,
            ),
            content=rx.vstack(
                # --- Dashboard KPIs integrado ---
                rx.vstack(
                    rx.hstack(
                        selector_periodo(),
                        spacing="2",
                        align="center",
                        width="100%",
                    ),
                    rx.cond(
                        NominaDashboardState.tiene_resumen,
                        rx.vstack(
                            grid_kpis(),
                            card_comparativo(),
                            spacing="4",
                            width="100%",
                        ),
                        rx.fragment(),
                    ),
                    spacing="3",
                    width="100%",
                    padding_bottom=Spacing.MD,
                ),
                # --- Tabla de períodos ---
                _tabla_periodos(),
                modal_crear_periodo(),
                spacing="4",
                width="100%",
            ),
        ),
        width="100%",
        min_height="100vh",
        on_mount=[
            NominaRRHHState.on_mount_periodos,
            NominaDashboardState.on_mount_dashboard,
        ],
    )
