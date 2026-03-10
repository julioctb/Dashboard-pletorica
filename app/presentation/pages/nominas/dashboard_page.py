"""
Página del dashboard de nóminas.

Prioriza las métricas operativas del periodo actual y conserva
el comparativo financiero del periodo seleccionado.
"""
import reflex as rx

from app.presentation.components.ui import (
    metric_card,
    payroll_period_status_badge,
    tabla_vacia,
    table_cell_text_sm,
    table_shell,
)
from app.presentation.layout import page_header, page_layout
from app.presentation.pages.nominas.dashboard_state import NominaDashboardState
from app.presentation.theme import CardStyles, Colors, Radius, Spacing, Typography


def _opcion_periodo(periodo: dict) -> rx.Component:
    return rx.select.item(
        periodo["nombre"],
        value=periodo["id"],
    )


def _opcion_anio(anio: dict) -> rx.Component:
    return rx.select.item(
        anio["label"],
        value=anio["value"],
    )


def selector_anio_dashboard() -> rx.Component:
    return rx.hstack(
        rx.text("Ano:", size="2", weight="medium", color=Colors.TEXT_SECONDARY),
        rx.select.root(
            rx.select.trigger(placeholder="Ano", width="120px"),
            rx.select.content(
                rx.foreach(
                    NominaDashboardState.anios_disponibles,
                    _opcion_anio,
                ),
            ),
            value=NominaDashboardState.filtro_anio,
            on_change=NominaDashboardState.cambiar_filtro_anio,
            size="2",
        ),
        spacing="2",
        align="center",
    )


def _opcion_contrato(contrato: dict) -> rx.Component:
    return rx.select.item(
        contrato["label"],
        value=contrato["value"],
    )


def selector_contrato_dashboard() -> rx.Component:
    return rx.hstack(
        rx.text("Contrato:", size="2", weight="medium", color=Colors.TEXT_SECONDARY),
        rx.select.root(
            rx.select.trigger(placeholder="Contrato", width="320px"),
            rx.select.content(
                rx.foreach(
                    NominaDashboardState.contratos_nomina_opciones,
                    _opcion_contrato,
                ),
            ),
            value=NominaDashboardState.filtro_contrato_nomina_id,
            on_change=NominaDashboardState.cambiar_filtro_contrato_nomina,
            size="2",
        ),
        spacing="2",
        align="center",
    )


def selector_periodo() -> rx.Component:
    return rx.hstack(
        rx.text("Periodo:", size="2", weight="medium", color=Colors.TEXT_SECONDARY),
        rx.select.root(
            rx.select.trigger(
                placeholder="Selecciona un periodo",
                width="320px",
            ),
            rx.select.content(
                rx.foreach(
                    NominaDashboardState.periodos_disponibles,
                    _opcion_periodo,
                ),
            ),
            value=NominaDashboardState.periodo_seleccionado_id,
            on_change=NominaDashboardState.seleccionar_periodo,
            size="2",
        ),
        spacing="2",
        align="center",
    )


def _metrica_shell(card: rx.Component) -> rx.Component:
    return rx.box(
        card,
        min_width="220px",
        flex="1 1 220px",
        width="100%",
    )


def grid_cards_operativas() -> rx.Component:
    return rx.flex(
        _metrica_shell(
            metric_card(
                titulo="Activos",
                valor=NominaDashboardState.valor_activos_card,
                icono="users",
                color_scheme="green",
                descripcion=rx.cond(
                    NominaDashboardState.metricas_contrato_disponibles,
                    "Activos / plazas del contrato",
                    "Selecciona contrato",
                ),
            ),
        ),
        _metrica_shell(
            metric_card(
                titulo="Inasistencias",
                valor=NominaDashboardState.valor_inasistencias_card,
                icono="calendar-x-2",
                color_scheme="orange",
                descripcion=rx.cond(
                    NominaDashboardState.metricas_contrato_disponibles,
                    "Dentro del periodo actual",
                    "Selecciona contrato",
                ),
            ),
        ),
        _metrica_shell(
            metric_card(
                titulo="Incapacidades",
                valor=NominaDashboardState.valor_incapacidades_card,
                icono="shield-alert",
                color_scheme="red",
                descripcion=rx.cond(
                    NominaDashboardState.metricas_contrato_disponibles,
                    "Dentro del periodo actual",
                    "Selecciona contrato",
                ),
            ),
        ),
        gap=Spacing.MD,
        wrap="wrap",
        width="100%",
    )


def callout_warning_operativo() -> rx.Component:
    return rx.cond(
        NominaDashboardState.warning_resumen_operativo != "",
        rx.callout.root(
            rx.callout.icon(rx.icon("triangle-alert", size=16)),
            rx.callout.text(NominaDashboardState.warning_resumen_operativo),
            color_scheme="orange",
            variant="soft",
            width="100%",
        ),
        rx.fragment(),
    )


def _panel_shell(*children, min_width: str | None = None, flex: str | None = None) -> rx.Component:
    style = {**CardStyles.BASE}
    if min_width is not None:
        style["min_width"] = min_width
    if flex is not None:
        style["flex"] = flex
    return rx.card(
        rx.vstack(
            *children,
            spacing="3",
            width="100%",
        ),
        width="100%",
        style=style,
    )


def _encabezado_panel_financiero(
    etiqueta: str,
    titulo: rx.Var | str | None,
    derecho: rx.Component,
) -> rx.Component:
    return rx.hstack(
        rx.vstack(
            rx.text(
                etiqueta,
                font_size=Typography.SIZE_XS,
                font_weight=Typography.WEIGHT_MEDIUM,
                color=Colors.TEXT_SECONDARY,
            ),
            rx.cond(
                titulo is not None,
                rx.text(
                    titulo,
                    font_size=Typography.SIZE_XL,
                    font_weight=Typography.WEIGHT_BOLD,
                    color=Colors.TEXT_PRIMARY,
                    line_height=Typography.LINE_HEIGHT_TIGHT,
                ),
                rx.fragment(),
            ),
            spacing="1",
            align="start",
        ),
        rx.spacer(),
        derecho,
        spacing="2",
        align="center",
        wrap="wrap",
        width="100%",
    )


def _resumen_stat_card(
    titulo: str,
    valor: rx.Var | str,
    *,
    prefijo: str = "",
    sufijo: str = "",
    icono: rx.Var | str,
    color: rx.Var | str,
    background: rx.Var | str,
    descripcion: rx.Var | str | None = None,
) -> rx.Component:
    return rx.box(
        rx.hstack(
            rx.vstack(
                rx.text(
                    titulo,
                    font_size=Typography.SIZE_XS,
                    font_weight=Typography.WEIGHT_MEDIUM,
                    color=Colors.TEXT_SECONDARY,
                    line_height=Typography.LINE_HEIGHT_TIGHT,
                ),
                rx.text(
                    prefijo + valor.to(str) + sufijo,
                    font_size=Typography.SIZE_XL,
                    font_weight=Typography.WEIGHT_BOLD,
                    color=Colors.TEXT_PRIMARY,
                    line_height=Typography.LINE_HEIGHT_TIGHT,
                ),
                rx.cond(
                    descripcion is not None,
                    rx.text(
                        descripcion,
                        font_size=Typography.SIZE_XS,
                        color=Colors.TEXT_MUTED,
                        line_height=Typography.LINE_HEIGHT_TIGHT,
                    ),
                    rx.fragment(),
                ),
                spacing="1",
                align="start",
            ),
            rx.spacer(),
            rx.center(
                rx.icon(icono, size=18, color=color),
                width="36px",
                height="36px",
                border_radius=Radius.FULL,
                background=background,
                flex_shrink="0",
            ),
            width="100%",
            align="center",
        ),
        padding=Spacing.MD,
        background=Colors.SECONDARY_LIGHT,
        border=f"1px solid {Colors.BORDER}",
        border_radius=Radius.MD,
        min_width="160px",
        flex="1 1 160px",
        width="100%",
    )


def _comparativo_variacion_card() -> rx.Component:
    return _resumen_stat_card(
        "Variacion neto",
        NominaDashboardState.variacion_neto_pct,
        prefijo="",
        sufijo="%",
        icono=rx.cond(
            NominaDashboardState.variacion_es_aumento,
            "trending-up",
            "trending-down",
        ),
        color=rx.cond(
            NominaDashboardState.variacion_es_aumento,
            Colors.ERROR,
            Colors.SUCCESS,
        ),
        background=rx.cond(
            NominaDashboardState.variacion_es_aumento,
            Colors.ERROR_LIGHT,
            Colors.SUCCESS_LIGHT,
        ),
        descripcion=rx.cond(
            NominaDashboardState.variacion_es_aumento,
            "Incremento vs periodo anterior",
            "Disminucion vs periodo anterior",
        ),
    )


def resumen_financiero_periodo() -> rx.Component:
    return rx.cond(
        NominaDashboardState.tiene_resumen,
        _panel_shell(
            _encabezado_panel_financiero(
                "Resumen financiero",
                NominaDashboardState.periodo_nombre_actual,
                payroll_period_status_badge(NominaDashboardState.periodo_estatus_actual),
            ),
            rx.flex(
                _resumen_stat_card(
                    "Empleados",
                    NominaDashboardState.total_empleados_kpi,
                    icono="users",
                    color=Colors.SECONDARY,
                    background=Colors.SECONDARY_LIGHT,
                ),
                _resumen_stat_card(
                    "Bruto",
                    NominaDashboardState.total_bruto,
                    prefijo="$",
                    icono="trending-up",
                    color=Colors.SUCCESS,
                    background=Colors.SUCCESS_LIGHT,
                ),
                _resumen_stat_card(
                    "Neto",
                    NominaDashboardState.total_neto_kpi,
                    prefijo="$",
                    icono="banknote",
                    color=Colors.PRIMARY,
                    background=Colors.PRIMARY_LIGHT,
                ),
                _resumen_stat_card(
                    "ISR",
                    NominaDashboardState.total_retenciones_isr,
                    prefijo="$",
                    icono="receipt",
                    color=Colors.WARNING,
                    background=Colors.WARNING_LIGHT,
                ),
                _resumen_stat_card(
                    "IMSS",
                    NominaDashboardState.total_cuotas_imss,
                    prefijo="$",
                    icono="shield",
                    color=Colors.INFO,
                    background=Colors.INFO_LIGHT,
                ),
                gap=Spacing.MD,
                wrap="wrap",
                width="100%",
            ),
        ),
        rx.fragment(),
    )


def card_comparativo() -> rx.Component:
    return rx.cond(
        NominaDashboardState.tiene_comparativo,
        _panel_shell(
            _encabezado_panel_financiero(
                "Comparativo vs periodo anterior",
                None,
                rx.badge(
                    rx.cond(
                        NominaDashboardState.variacion_es_aumento,
                        "Incremento",
                        "Disminucion",
                    ),
                    color_scheme=rx.cond(
                        NominaDashboardState.variacion_es_aumento,
                        "red",
                        "green",
                    ),
                    variant="soft",
                    radius="full",
                ),
            ),
            rx.flex(
                _resumen_stat_card(
                    "Periodo actual",
                    NominaDashboardState.total_neto_kpi,
                    prefijo="$",
                    icono="banknote",
                    color=Colors.PRIMARY,
                    background=Colors.PRIMARY_LIGHT,
                ),
                _resumen_stat_card(
                    "Periodo anterior",
                    NominaDashboardState.neto_anterior,
                    prefijo="$",
                    icono="clock-3",
                    color=Colors.SECONDARY,
                    background=Colors.SECONDARY_LIGHT,
                ),
                _comparativo_variacion_card(),
                gap=Spacing.MD,
                wrap="wrap",
                width="100%",
            ),
        ),
        rx.fragment(),
    )


_COLS_TOP = [
    {"nombre": "Clave", "ancho": "80px"},
    {"nombre": "Nombre", "ancho": "220px"},
    {"nombre": "Neto", "ancho": "120px"},
]

_COLS_INC = [
    {"nombre": "Clave", "ancho": "80px"},
    {"nombre": "Nombre", "ancho": "220px"},
    {"nombre": "Deducciones", "ancho": "120px"},
]


def _fila_top_empleado(emp: dict) -> rx.Component:
    return rx.table.row(
        table_cell_text_sm(emp["clave_empleado"], tone="muted"),
        rx.table.cell(rx.text(emp["nombre_empleado"], size="2")),
        rx.table.cell(
            rx.text(
                "$" + emp["total_neto"].to(str),
                size="2",
                weight="bold",
                color=Colors.PRIMARY,
            ),
        ),
    )


def _fila_incidencia(emp: dict) -> rx.Component:
    return rx.table.row(
        table_cell_text_sm(emp["clave_empleado"], tone="muted"),
        rx.table.cell(rx.text(emp["nombre_empleado"], size="2")),
        rx.table.cell(
            rx.text(
                "$" + emp["total_deducciones"].to(str),
                size="2",
                color=Colors.ERROR,
            ),
        ),
    )


def _tabla_top_empleados() -> rx.Component:
    return _panel_shell(
        rx.hstack(
            rx.icon("trophy", size=16, color=Colors.WARNING),
            rx.text("Top 5 por neto", size="3", weight="bold"),
            spacing="2",
            align="center",
        ),
        table_shell(
            loading=NominaDashboardState.loading,
            headers=_COLS_TOP,
            rows=NominaDashboardState.top_empleados,
            row_renderer=_fila_top_empleado,
            has_rows=NominaDashboardState.tiene_top_empleados,
            empty_component=tabla_vacia(mensaje="Sin datos para este periodo"),
            loading_rows=3,
        ),
        min_width="320px",
        flex="1 1 320px",
    )


def _tabla_incidencias() -> rx.Component:
    return _panel_shell(
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
            empty_component=tabla_vacia(mensaje="Sin deducciones en este periodo"),
            loading_rows=3,
        ),
        min_width="320px",
        flex="1 1 320px",
    )


def _contenido_financiero() -> rx.Component:
    return rx.cond(
        NominaDashboardState.tiene_periodos_disponibles,
        rx.vstack(
            rx.hstack(
                rx.spacer(),
                selector_periodo(),
                spacing="3",
                align="center",
                width="100%",
            ),
            resumen_financiero_periodo(),
            card_comparativo(),
            rx.flex(
                _tabla_top_empleados(),
                _tabla_incidencias(),
                gap=Spacing.MD,
                wrap="wrap",
                width="100%",
                align_items="start",
            ),
            spacing="4",
            width="100%",
        ),
        rx.callout.root(
            rx.callout.icon(rx.icon("calendar-range", size=16)),
            rx.callout.text(
                "No hay periodos creados para los filtros seleccionados. Puedes cambiar el año, el contrato o generar una nueva nomina."
            ),
            color_scheme="blue",
            variant="soft",
            width="100%",
        ),
    )


def _contenido_dashboard() -> rx.Component:
    return rx.vstack(
        callout_warning_operativo(),
        grid_cards_operativas(),
        _contenido_financiero(),
        spacing="4",
        width="100%",
    )


def dashboard_nomina_page() -> rx.Component:
    return rx.box(
        page_layout(
            header=page_header(
                titulo="Dashboard Nomina",
                subtitulo="Operacion actual, comparativo y resumen financiero",
                icono="chart-bar",
                accion_principal=rx.hstack(
                    selector_contrato_dashboard(),
                    selector_anio_dashboard(),
                    spacing="3",
                    align="center",
                    wrap="wrap",
                ),
            ),
            content=rx.cond(
                NominaDashboardState.loading,
                rx.center(rx.spinner(size="3"), padding_y="80px"),
                _contenido_dashboard(),
            ),
        ),
        width="100%",
        min_height="100vh",
        on_mount=NominaDashboardState.on_mount_dashboard,
    )
