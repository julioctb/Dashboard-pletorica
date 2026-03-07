"""
Página del dashboard ejecutivo de nóminas.

Ruta: /nominas/dashboard
Acceso: es_rrhh | es_contabilidad | es_admin_empresa

Vista ejecutiva con KPIs por período, comparativo vs período anterior,
top 5 empleados por neto y listado de empleados con deducciones.
"""
import reflex as rx

from app.presentation.pages.nominas.dashboard_state import NominaDashboardState
from app.presentation.components.ui import (
    payroll_period_status_badge,
    tabla_vacia,
    table_shell,
    table_cell_text_sm,
    skeleton_tabla,
    page_header,
)
from app.presentation.layout import page_layout
from app.presentation.theme import Colors, Spacing, Radius, Typography


# =============================================================================
# SELECTOR DE PERÍODO
# =============================================================================

def opcion_periodo(periodo: dict) -> rx.Component:
    return rx.select.item(
        periodo['nombre'],
        value=periodo['id'],
    )


def selector_periodo() -> rx.Component:
    return rx.hstack(
        rx.text("Período:", size="2", weight="medium", color=Colors.TEXT_SECONDARY),
        rx.select.root(
            rx.select.trigger(
                placeholder="Selecciona un período…",
                width="260px",
            ),
            rx.select.content(
                rx.foreach(
                    NominaDashboardState.periodos_disponibles,
                    opcion_periodo,
                ),
            ),
            value=NominaDashboardState.periodo_seleccionado_id,
            on_change=NominaDashboardState.seleccionar_periodo,
            size="2",
        ),
        spacing="2",
        align="center",
    )


# =============================================================================
# KPI CARDS
# =============================================================================

def kpi_card(
    titulo: str,
    valor: rx.Var,
    icono: str,
    color: str,
    prefijo: str = "$",
) -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.icon(icono, size=16, color=color),
                rx.text(titulo, size="1", color=Colors.TEXT_MUTED, weight="medium"),
                spacing="1",
                align="center",
            ),
            rx.text(
                prefijo + valor.to(str),
                size="5",
                weight="bold",
                color=color,
            ),
            spacing="1",
            align="start",
        ),
        padding=Spacing.LG,
        background=Colors.SURFACE,
        border=f"1px solid {Colors.BORDER}",
        border_radius=Radius.LG,
        flex="1",
        min_width="160px",
    )


def grid_kpis() -> rx.Component:
    return rx.flex(
        kpi_card(
            "Total Bruto",
            NominaDashboardState.total_bruto,
            "trending-up",
            Colors.SUCCESS,
        ),
        kpi_card(
            "Total Neto",
            NominaDashboardState.total_neto_kpi,
            "banknote",
            Colors.PRIMARY,
        ),
        kpi_card(
            "Retenciones ISR",
            NominaDashboardState.total_retenciones_isr,
            "receipt",
            Colors.WARNING,
        ),
        kpi_card(
            "Cuotas IMSS",
            NominaDashboardState.total_cuotas_imss,
            "shield",
            Colors.INFO,
        ),
        gap=Spacing.MD,
        flex_wrap="wrap",
        width="100%",
    )


# =============================================================================
# CARD COMPARATIVO
# =============================================================================

def card_comparativo() -> rx.Component:
    return rx.cond(
        NominaDashboardState.tiene_comparativo,
        rx.box(
            rx.vstack(
                rx.hstack(
                    rx.icon("git-compare", size=16, color=Colors.TEXT_MUTED),
                    rx.text(
                        "Comparativo vs período anterior",
                        size="2",
                        weight="bold",
                    ),
                    spacing="2",
                    align="center",
                ),
                rx.hstack(
                    rx.vstack(
                        rx.text("Período actual", size="1", color=Colors.TEXT_MUTED),
                        rx.text(
                            "$" + NominaDashboardState.total_neto_kpi.to(str),
                            size="4",
                            weight="bold",
                            color=Colors.TEXT_PRIMARY,
                        ),
                        spacing="0",
                    ),
                    rx.separator(orientation="vertical", size="2"),
                    rx.vstack(
                        rx.text("Período anterior", size="1", color=Colors.TEXT_MUTED),
                        rx.text(
                            "$" + NominaDashboardState.neto_anterior.to(str),
                            size="4",
                            weight="medium",
                            color=Colors.TEXT_MUTED,
                        ),
                        spacing="0",
                    ),
                    rx.separator(orientation="vertical", size="2"),
                    rx.vstack(
                        rx.text("Variación neto", size="1", color=Colors.TEXT_MUTED),
                        rx.hstack(
                            rx.cond(
                                NominaDashboardState.variacion_es_aumento,
                                rx.icon("trending-up", size=16, color=Colors.ERROR),
                                rx.icon("trending-down", size=16, color=Colors.SUCCESS),
                            ),
                            rx.text(
                                NominaDashboardState.variacion_neto_pct.to(str) + "%",
                                size="4",
                                weight="bold",
                                color=rx.cond(
                                    NominaDashboardState.variacion_es_aumento,
                                    Colors.ERROR,
                                    Colors.SUCCESS,
                                ),
                            ),
                            spacing="1",
                            align="center",
                        ),
                        spacing="0",
                    ),
                    spacing="6",
                    align="center",
                ),
                spacing="3",
                width="100%",
            ),
            padding=Spacing.LG,
            background=Colors.SURFACE,
            border=f"1px solid {Colors.BORDER}",
            border_radius=Radius.LG,
            width="100%",
        ),
        rx.fragment(),
    )


# =============================================================================
# MINI TABLAS
# =============================================================================

_COLS_TOP = [
    {"nombre": "Clave",  "ancho": "70px"},
    {"nombre": "Nombre", "ancho": "200px"},
    {"nombre": "Neto",   "ancho": "110px"},
]

_COLS_INC = [
    {"nombre": "Clave",       "ancho": "70px"},
    {"nombre": "Nombre",      "ancho": "200px"},
    {"nombre": "Deducciones", "ancho": "110px"},
]


def _fila_top_empleado(emp: dict) -> rx.Component:
    return rx.table.row(
        table_cell_text_sm(emp['clave_empleado'], tone="muted"),
        rx.table.cell(rx.text(emp['nombre_empleado'], size="2")),
        rx.table.cell(
            rx.text(
                "$" + emp['total_neto'].to(str),
                size="2",
                weight="bold",
                color=Colors.PRIMARY,
            )
        ),
    )


def _fila_incidencia(emp: dict) -> rx.Component:
    return rx.table.row(
        table_cell_text_sm(emp['clave_empleado'], tone="muted"),
        rx.table.cell(rx.text(emp['nombre_empleado'], size="2")),
        rx.table.cell(
            rx.text(
                "$" + emp['total_deducciones'].to(str),
                size="2",
                color=Colors.ERROR,
            )
        ),
    )


def _tabla_top_empleados() -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.icon("trophy", size=16, color=Colors.WARNING),
                rx.text("Top 5 — Mayor neto", size="3", weight="bold"),
                spacing="2",
                align="center",
            ),
            table_shell(
                loading=NominaDashboardState.loading,
                headers=_COLS_TOP,
                rows=NominaDashboardState.top_empleados,
                row_renderer=_fila_top_empleado,
                has_rows=NominaDashboardState.tiene_top_empleados,
                empty_component=tabla_vacia(mensaje="Sin datos para este período"),
                loading_rows=3,
            ),
            spacing="3",
            width="100%",
        ),
        padding=Spacing.LG,
        background=Colors.SURFACE,
        border=f"1px solid {Colors.BORDER}",
        border_radius=Radius.LG,
        flex="1",
        min_width="320px",
    )


def _tabla_incidencias() -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.icon("circle-alert", size=16, color=Colors.ERROR),
                rx.text("Empleados con deducciones", size="3", weight="bold"),
                spacing="2",
                align="center",
            ),
            table_shell(
                loading=NominaDashboardState.loading,
                headers=_COLS_INC,
                rows=NominaDashboardState.empleados_con_incidencias,
                row_renderer=_fila_incidencia,
                has_rows=NominaDashboardState.tiene_incidencias,
                empty_component=tabla_vacia(mensaje="Sin empleados con deducciones"),
                loading_rows=3,
            ),
            spacing="3",
            width="100%",
        ),
        padding=Spacing.LG,
        background=Colors.SURFACE,
        border=f"1px solid {Colors.BORDER}",
        border_radius=Radius.LG,
        flex="1",
        min_width="320px",
    )


# =============================================================================
# CONTENIDO PRINCIPAL
# =============================================================================

def _contenido_dashboard() -> rx.Component:
    return rx.cond(
        NominaDashboardState.tiene_resumen,
        rx.vstack(
            # Encabezado del período
            rx.hstack(
                rx.text(
                    NominaDashboardState.periodo_nombre_actual,
                    size="3",
                    weight="bold",
                    color=Colors.TEXT_PRIMARY,
                ),
                payroll_period_status_badge(NominaDashboardState.periodo_estatus_actual),
                spacing="2",
                align="center",
            ),
            grid_kpis(),
            card_comparativo(),
            rx.flex(
                _tabla_top_empleados(),
                _tabla_incidencias(),
                gap=Spacing.MD,
                flex_wrap="wrap",
                width="100%",
                align_items="start",
            ),
            spacing="4",
            width="100%",
        ),
        rx.cond(
            NominaDashboardState.loading,
            rx.vstack(
                *[rx.skeleton(height="60px", width="100%") for _ in range(4)],
                spacing="3",
                width="100%",
            ),
            rx.callout(
                "Selecciona un período para ver el dashboard ejecutivo.",
                icon="bar-chart-2",
                color_scheme="blue",
                size="1",
                width="100%",
            ),
        ),
    )


# =============================================================================
# PÁGINA
# =============================================================================

def dashboard_nomina_page() -> rx.Component:
    """Página del dashboard ejecutivo de nóminas."""
    return rx.box(
        page_layout(
            header=page_header(
                "chart-bar",
                "Dashboard Nómina",
                subtitulo="KPIs, comparativos y resumen ejecutivo por período",
                accion_principal=selector_periodo(),
            ),
            content=_contenido_dashboard(),
        ),
        width="100%",
        min_height="100vh",
        on_mount=NominaDashboardState.on_mount_dashboard,
    )
