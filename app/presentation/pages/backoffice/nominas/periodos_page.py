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
from app.presentation.components.ui.filters import input_busqueda
from app.presentation.layouts.backoffice import page_header, page_layout
from app.presentation.pages.backoffice.nominas.dashboard_page import (
    callout_warning_operativo,
    grid_cards_operativas,
    resumen_financiero_periodo,
    skeleton_dashboard_nomina,
)
from app.presentation.pages.backoffice.nominas.dashboard_state import NominaDashboardState
from app.presentation.pages.backoffice.nominas.nomina_contabilidad_state import NominaContabilidadState
from app.presentation.pages.backoffice.nominas.nomina_modals import modal_crear_periodo
from app.presentation.pages.backoffice.nominas.nomina_modals import dialog_enviar_contabilidad
from app.presentation.pages.backoffice.nominas.nomina_rrhh_state import NominaRRHHState
from app.presentation.theme import Colors, Spacing, Typography


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
        rx.select.trigger(placeholder="Contrato", width="260px"),
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


def _toolbar_nominas() -> rx.Component:
    return rx.flex(
        rx.box(
            input_busqueda(
                value=NominaRRHHState.filtro_busqueda,
                on_change=NominaRRHHState.set_filtro_busqueda,
                on_clear=lambda: NominaRRHHState.set_filtro_busqueda(""),
                placeholder="Buscar por nombre o generado por...",
                width="100%",
                toolbar_style=False,
            ),
            flex="1 1 320px",
            min_width="260px",
        ),
        _filtro_anio(),
        _filtro_contrato(),
        wrap="wrap",
        align="center",
        column_gap=Spacing.SM,
        row_gap=Spacing.SM,
        width="100%",
        margin_bottom=Spacing.BASE,
    )


def _boton_accion_periodo(periodo: dict, total_empleados) -> rx.Component:
    return rx.match(
        periodo["estatus"],
        (
            "BORRADOR",
            rx.cond(
                NominaRRHHState.puede_abrir_preparacion,
                rx.button(
                    "Preparar nómina",
                    size="1",
                    variant="soft",
                    color_scheme="gray",
                    on_click=NominaRRHHState.abrir_periodo(periodo).stop_propagation,
                ),
                rx.fragment(),
            ),
        ),
        (
            "EN_PREPARACION_RRHH",
            rx.cond(
                NominaRRHHState.puede_abrir_preparacion,
                rx.button(
                    "Editar nómina",
                    size="1",
                    variant="soft",
                    color_scheme="blue",
                    on_click=NominaRRHHState.abrir_periodo(periodo).stop_propagation,
                ),
                rx.fragment(),
            ),
        ),
        (
            "CALCULADO",
            rx.cond(
                NominaRRHHState.puede_abrir_calculo,
                rx.button(
                    "Cerrar nómina",
                    size="1",
                    variant="soft",
                    color_scheme="blue",
                    on_click=NominaContabilidadState.abrir_periodo_calculo(periodo).stop_propagation,
                ),
                rx.fragment(),
            ),
        ),
        (
            "ENVIADO_A_CONTABILIDAD",
            rx.cond(
                NominaRRHHState.puede_abrir_calculo,
                rx.button(
                    "Consultar",
                    size="1",
                    variant="soft",
                    color_scheme="amber",
                    on_click=NominaContabilidadState.abrir_periodo_calculo(periodo).stop_propagation,
                ),
                rx.fragment(),
            ),
        ),
        (
            "EN_PROCESO_CONTABILIDAD",
            rx.cond(
                NominaRRHHState.puede_abrir_calculo,
                rx.button(
                    "Consultar",
                    size="1",
                    variant="soft",
                    color_scheme="blue",
                    on_click=NominaContabilidadState.abrir_periodo_calculo(periodo).stop_propagation,
                ),
                rx.fragment(),
            ),
        ),
        (
            "CERRADO",
            rx.cond(
                NominaRRHHState.puede_abrir_calculo,
                rx.button(
                    "Consultar",
                    size="1",
                    variant="soft",
                    color_scheme="green",
                    on_click=NominaContabilidadState.abrir_periodo_calculo(periodo).stop_propagation,
                ),
                rx.fragment(),
            ),
        ),
        rx.fragment(),
    )


def _fila_periodo(periodo: dict) -> rx.Component:
    total_empleados = periodo.get("total_empleados", 0).to(int)
    periodo_id = periodo["id"].to(str)
    neto_visible = rx.cond(
        (periodo["estatus"] == "BORRADOR") & (periodo["total_neto_fmt"] == "$0.00"),
        "—",
        periodo["total_neto_fmt"],
    )
    fila_seleccionada = NominaDashboardState.periodo_seleccionado_id == periodo_id
    return rx.table.row(
        rx.table.cell(
            rx.hstack(
                rx.cond(
                    fila_seleccionada,
                    rx.icon("chevron-right", size=14, color=Colors.PRIMARY),
                    rx.box(width="14px", height="14px"),
                ),
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
                spacing="2",
                align="center",
                width="100%",
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
                neto_visible,
                size="2",
                weight="medium",
                color=rx.cond(
                    neto_visible == "—",
                    Colors.TEXT_MUTED,
                    Colors.PRIMARY,
                ),
                width="100%",
                text_align="center",
                style={"font_variant_numeric": "tabular-nums"},
            ),
            text_align="center",
        ),
        rx.table.cell(
            rx.flex(
                _boton_accion_periodo(periodo, total_empleados),
                justify="center",
                width="100%",
            ),
            text_align="center",
        ),
        on_click=NominaDashboardState.seleccionar_periodo(periodo_id),
        cursor="pointer",
        background=rx.cond(
            fila_seleccionada,
            Colors.PRIMARY_LIGHT,
            "transparent",
        ),
        _hover={
            "background": rx.cond(
                fila_seleccionada,
                Colors.PRIMARY_LIGHT,
                Colors.SECONDARY_LIGHT,
            ),
        },
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
                    resumen_financiero_periodo(),
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
            header=rx.box(
                page_header(
                    titulo="Nóminas",
                    subtitulo=NominaDashboardState.contrato_activo_label,
                    icono="calculator",
                    accion_principal=rx.cond(
                        NominaRRHHState.es_rrhh,
                        rx.button(
                            rx.icon("plus", size=16),
                            "Nueva nómina",
                            on_click=NominaRRHHState.abrir_modal_periodo,
                            color_scheme="blue",
                            variant="solid",
                        ),
                        rx.fragment(),
                    ),
                ),
                width="100%",
                max_width="1024px",
                margin_x="auto",
            ),
            toolbar=rx.box(
                _toolbar_nominas(),
                width="100%",
                max_width="1024px",
                margin_x="auto",
            ),
            content=rx.vstack(
                _bloque_dashboard(),
                rx.vstack(
                    rx.text(
                        "Períodos de nómina",
                        font_size=Typography.SIZE_XS,
                        font_weight=Typography.WEIGHT_SEMIBOLD,
                        color=Colors.TEXT_MUTED,
                        text_transform="uppercase",
                        letter_spacing=Typography.LETTER_SPACING_WIDE,
                    ),
                    _tabla_periodos(),
                    spacing="3",
                    width="100%",
                ),
                modal_crear_periodo(),
                dialog_enviar_contabilidad(),
                spacing="4",
                width="100%",
                max_width="1024px",
                margin_x="auto",
            ),
        ),
        width="100%",
        min_height="100vh",
        on_mount=[
            NominaRRHHState.on_mount_periodos,
            NominaDashboardState.on_mount_dashboard,
        ],
    )
