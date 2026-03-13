"""
Página de períodos de nómina.

Mantiene búsqueda y tabla de períodos, ahora con filtro anual y
cards operativas del periodo actual calculado por política.
"""
import reflex as rx

from app.presentation.components.ui import (
    payroll_period_status_badge,
    tabla_vacia,
    table_cell_text_sm,
    table_shell,
)
from app.presentation.layout import page_header, page_layout, page_toolbar
from app.presentation.pages.nominas.dashboard_page import (
    callout_warning_operativo,
    card_comparativo,
    grid_cards_operativas,
    resumen_financiero_periodo,
    selector_periodo,
    skeleton_dashboard_nomina,
)
from app.presentation.pages.nominas.dashboard_state import NominaDashboardState
from app.presentation.pages.nominas.nomina_contabilidad_state import NominaContabilidadState
from app.presentation.pages.nominas.nomina_modals import modal_crear_periodo
from app.presentation.pages.nominas.nomina_modals import dialog_enviar_contabilidad
from app.presentation.pages.nominas.nomina_rrhh_state import NominaRRHHState
from app.presentation.theme import Colors, Spacing


ENCABEZADOS = [
    {"nombre": "Nombre", "ancho": "220px"},
    {"nombre": "Pago", "ancho": "120px", "header_align": "center"},
    {"nombre": "Generado por", "ancho": "160px"},
    {"nombre": "Estatus", "ancho": "140px", "header_align": "center"},
    {"nombre": "Empleados", "ancho": "90px", "header_align": "center"},
    {"nombre": "Neto total", "ancho": "130px", "header_align": "center"},
    {"nombre": "Acciones", "ancho": "130px", "header_align": "center"},
]


def _filtro_anio() -> rx.Component:
    return rx.select.root(
        rx.select.trigger(placeholder="Ano", width="120px"),
        rx.select.content(
            rx.foreach(
                NominaRRHHState.anios_disponibles_periodos,
                lambda anio: rx.select.item(
                    anio["label"],
                    value=anio["value"],
                ),
            ),
        ),
        value=NominaRRHHState.filtro_anio_periodos,
        on_change=NominaRRHHState.cambiar_filtro_anio_periodos,
    )


def _filtro_contrato() -> rx.Component:
    return rx.select.root(
        rx.select.trigger(placeholder="Contrato", width="320px"),
        rx.select.content(
            rx.foreach(
                NominaRRHHState.contratos_filtro_nomina_opciones,
                lambda contrato: rx.select.item(
                    contrato["label"],
                    value=contrato["value"],
                ),
            ),
        ),
        value=NominaRRHHState.filtro_contrato_nomina_id,
        on_change=NominaRRHHState.cambiar_filtro_contrato_nomina,
    )


def _filtros_toolbar() -> rx.Component:
    return rx.hstack(
        _filtro_anio(),
        _filtro_contrato(),
        spacing="2",
        wrap="wrap",
    )


def _fila_periodo(periodo: dict) -> rx.Component:
    total_empleados = periodo.get("total_empleados", 0).to(int)
    return rx.table.row(
        rx.table.cell(
            rx.vstack(
                rx.text(
                    periodo["nombre"],
                    size="2",
                    weight="medium",
                    color=Colors.TEXT_PRIMARY,
                    max_width="220px",
                    overflow="hidden",
                    text_overflow="ellipsis",
                    white_space="nowrap",
                ),
                rx.cond(
                    periodo["es_aguinaldo"],
                    rx.badge(
                        "Aguinaldo",
                        color_scheme="amber",
                        variant="soft",
                        size="1",
                    ),
                    rx.fragment(),
                ),
                spacing="1",
                align="start",
            ),
        ),
        rx.table.cell(
            rx.text(
                periodo["fecha_pago_fmt"],
                size="2",
                color=Colors.TEXT_MUTED,
                width="100%",
                text_align="center",
            ),
            text_align="center",
        ),
        table_cell_text_sm(periodo["creado_por_nombre_fmt"], tone="muted"),
        rx.table.cell(
            rx.flex(
                payroll_period_status_badge(periodo["estatus"]),
                justify="center",
                width="100%",
            ),
            text_align="center",
        ),
        rx.table.cell(
            rx.text(
                total_empleados.to(str),
                size="2",
                color=Colors.TEXT_MUTED,
                width="100%",
                text_align="center",
            ),
            text_align="center",
        ),
        rx.table.cell(
            rx.text(
                periodo["total_neto_fmt"],
                size="2",
                weight="medium",
                color=Colors.SUCCESS,
                width="100%",
                text_align="center",
            ),
            text_align="center",
        ),
        rx.table.cell(
            rx.hstack(
                rx.cond(
                    NominaRRHHState.puede_abrir_preparacion,
                    rx.tooltip(
                        rx.icon_button(
                            rx.icon("pencil", size=15),
                            size="2",
                            variant="soft",
                            color_scheme="blue",
                            on_click=NominaRRHHState.abrir_periodo(periodo),
                        ),
                        content="Preparar nómina",
                    ),
                    rx.fragment(),
                ),
                rx.cond(
                    NominaRRHHState.puede_abrir_preparacion
                    & (periodo["estatus"] == "EN_PREPARACION_RRHH")
                    & (total_empleados > 0),
                    rx.tooltip(
                        rx.icon_button(
                            rx.icon("send", size=15),
                            size="2",
                            variant="soft",
                            color_scheme="orange",
                            on_click=NominaRRHHState.abrir_dialog_envio_periodo(periodo),
                        ),
                        content="Enviar a Contabilidad",
                    ),
                    rx.fragment(),
                ),
                rx.cond(
                    NominaRRHHState.puede_abrir_calculo & (
                        (periodo["estatus"] == "ENVIADO_A_CONTABILIDAD")
                        | (periodo["estatus"] == "EN_PROCESO_CONTABILIDAD")
                        | (periodo["estatus"] == "CALCULADO")
                        | (periodo["estatus"] == "CERRADO")
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
                justify="center",
                width="100%",
            ),
            text_align="center",
        ),
    )


def _tabla_periodos() -> rx.Component:
    return table_shell(
        loading=NominaRRHHState.loading,
        headers=ENCABEZADOS,
        rows=NominaRRHHState.periodos_filtrados,
        row_renderer=_fila_periodo,
        has_rows=NominaRRHHState.tiene_periodos_filtrados,
        empty_component=tabla_vacia(
            mensaje="No hay periodos de nómina para los filtros actuales.",
            onclick=NominaRRHHState.abrir_modal_periodo,
        ),
        total_caption=(
            "Mostrando "
            + NominaRRHHState.periodos_filtrados.length().to(str)
            + " periodo(s)"
        ),
        loading_rows=4,
    )


def _bloque_dashboard() -> rx.Component:
    return rx.box(
        rx.cond(
            NominaDashboardState.loading,
            skeleton_dashboard_nomina(),
            rx.vstack(
                callout_warning_operativo(),
                grid_cards_operativas(),
                rx.cond(
                    NominaDashboardState.tiene_periodos_disponibles,
                    rx.vstack(
                        rx.hstack(
                            rx.spacer(),
                            selector_periodo(),
                            width="100%",
                            align="center",
                        ),
                        resumen_financiero_periodo(),
                        card_comparativo(),
                        spacing="3",
                        width="100%",
                    ),
                    rx.callout.root(
                        rx.callout.icon(rx.icon("calendar-range", size=16)),
                        rx.callout.text(
                            "No hay periodos ordinarios creados para el ano seleccionado. Puedes cambiar el filtro o generar una nueva nomina."
                        ),
                        color_scheme="blue",
                        variant="soft",
                        width="100%",
                    ),
                ),
                spacing="3",
                width="100%",
            ),
        ),
        width="100%",
        padding_bottom=Spacing.MD,
    )


def periodos_nomina_page() -> rx.Component:
    return rx.box(
        page_layout(
            header=page_header(
                titulo="Nominas",
                subtitulo="Gestión de periodos y operación actual de nómina",
                icono="calculator",
                accion_principal=rx.cond(
                    NominaRRHHState.es_rrhh,
                    rx.button(
                        rx.icon("plus", size=16),
                        "Nueva nómina",
                        on_click=NominaRRHHState.abrir_modal_periodo,
                        color_scheme="blue",
                    ),
                    rx.fragment(),
                ),
            ),
            toolbar=page_toolbar(
                search_value=NominaRRHHState.filtro_busqueda,
                search_placeholder="Buscar por nombre o generado por...",
                on_search_change=NominaRRHHState.set_filtro_busqueda,
                on_search_clear=lambda: NominaRRHHState.set_filtro_busqueda(""),
                filters=_filtros_toolbar(),
                show_view_toggle=False,
            ),
            content=rx.vstack(
                _bloque_dashboard(),
                _tabla_periodos(),
                modal_crear_periodo(),
                dialog_enviar_contabilidad(),
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
