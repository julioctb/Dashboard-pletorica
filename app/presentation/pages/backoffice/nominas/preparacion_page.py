"""
Pantalla de preparacion de nomina (detalle de periodo).

Ruta: /nominas/preparacion
Acceso: es_rrhh | es_contabilidad | es_admin_empresa
"""

import reflex as rx

from app.presentation.pages.backoffice.nominas.nomina_rrhh_state import NominaRRHHState
from app.presentation.pages.backoffice.nominas.nomina_modals import (
    modal_descuentos_empleado,
    dialog_iniciar_preparacion,
    dialog_enviar_contabilidad,
)
from app.presentation.components.ui import (
    input_busqueda,
    metadata_divider,
    metadata_item,
    payroll_period_status_badge,
    tabla_vacia,
    table_pagination,
    table_shell,
)
from app.presentation.layouts.backoffice import page_layout, page_header
from app.presentation.theme import Colors, Radius, Spacing, Typography

def _metadata_periodo() -> rx.Component:
    return rx.box(
        rx.flex(
            metadata_item(
                "Periodo",
                NominaRRHHState.periodo_rango_compacto,
                min_width="120px",
                label_weight=Typography.WEIGHT_SEMIBOLD,
            ),
            metadata_divider(),
            metadata_item(
                "Tipo",
                NominaRRHHState.periodo_tipo_ficha_label,
                min_width="120px",
                label_weight=Typography.WEIGHT_SEMIBOLD,
            ),
            metadata_divider(),
            metadata_item(
                "Fecha de pago",
                NominaRRHHState.periodo_actual["fecha_pago_fmt"],
                min_width="120px",
                label_weight=Typography.WEIGHT_SEMIBOLD,
            ),
            metadata_divider(),
            metadata_item(
                "Empleados",
                NominaRRHHState.total_empleados_resumen_preparacion.to(str),
                min_width="120px",
                label_weight=Typography.WEIGHT_SEMIBOLD,
            ),
            metadata_divider(),
            metadata_item(
                "Generada",
                NominaRRHHState.periodo_actual["fecha_creacion_fmt"],
                tone="secondary",
                min_width="120px",
                label_weight=Typography.WEIGHT_SEMIBOLD,
            ),
            metadata_divider(),
            metadata_item(
                "Generado por",
                NominaRRHHState.periodo_actual["creado_por_nombre_fmt"],
                tone="secondary",
                min_width="120px",
                label_weight=Typography.WEIGHT_SEMIBOLD,
            ),
            width="100%",
            wrap="wrap",
            align="stretch",
            justify="between",
            column_gap=Spacing.MD,
            row_gap=Spacing.SM,
        ),
        width="100%",
        padding_y=Spacing.SM,
        border_bottom=f"1px solid {Colors.BORDER}",
    )


def _header_action_button() -> rx.Component:
    return rx.cond(
        NominaRRHHState.periodo_es_borrador,
        rx.button(
            "Iniciar preparacion",
            on_click=NominaRRHHState.abrir_dialog_iniciar,
            color_scheme="blue",
            variant="solid",
            size="2",
        ),
        rx.cond(
            NominaRRHHState.periodo_en_preparacion,
            rx.button(
                "Preparar pagos",
                on_click=NominaRRHHState.abrir_dialog_envio,
                color_scheme="blue",
                variant="solid",
                size="2",
            ),
            rx.cond(
                NominaRRHHState.periodo_calculado & NominaRRHHState.puede_abrir_calculo,
                rx.link(
                    rx.button(
                        "Cerrar nomina",
                        color_scheme="blue",
                        variant="solid",
                        size="2",
                    ),
                    href=NominaRRHHState.nomina_calculo_path,
                    underline="none",
                ),
                rx.fragment(),
            ),
        ),
    )


def _header_actions() -> rx.Component:
    return rx.hstack(
        payroll_period_status_badge(NominaRRHHState.periodo_estatus),
        rx.cond(
            NominaRRHHState.mostrar_accion_header_preparacion,
            _header_action_button(),
            rx.fragment(),
        ),
        spacing="3",
        align="center",
    )


def _toolbar_tabla_empleados() -> rx.Component:
    return rx.flex(
        rx.box(
            input_busqueda(
                value=NominaRRHHState.filtro_busqueda_empleados,
                on_change=NominaRRHHState.set_filtro_busqueda_empleados,
                on_clear=lambda: NominaRRHHState.set_filtro_busqueda_empleados(""),
                placeholder=rx.cond(
                    NominaRRHHState.periodo_actual_es_aguinaldo,
                    "buscar por nombre...",
                    "buscar por nombre o sede...",
                ),
                width="100%",
                toolbar_style=True,
            ),
            flex="1 1 0%",
            min_width="280px",
        ),
        rx.cond(
            NominaRRHHState.periodo_actual_es_aguinaldo,
            rx.fragment(),
            rx.select.root(
                rx.select.trigger(placeholder="Sede", width="180px"),
                rx.select.content(
                    rx.foreach(
                        NominaRRHHState.opciones_sede_empleados_preparacion,
                        lambda opcion: rx.select.item(
                            opcion["label"],
                            value=opcion["value"],
                        ),
                    )
                ),
                value=NominaRRHHState.filtro_sede_empleados_preparacion,
                on_change=NominaRRHHState.set_filtro_sede_empleados_preparacion,
                size="2",
            ),
        ),
        width="100%",
        align="center",
        wrap="wrap",
        gap=Spacing.SM,
    )


def _callout_readonly() -> rx.Component:
    return rx.cond(
        NominaRRHHState.periodo_enviado,
        rx.callout(
            "Este periodo fue enviado a contabilidad. La vista se mantiene en solo lectura para RRHH.",
            icon="lock",
            color_scheme="orange",
            size="1",
            width="100%",
        ),
        rx.fragment(),
    )


def _sort_indicator(field: str) -> rx.Component:
    return rx.cond(
        NominaRRHHState.columna_orden_empleados_preparacion == field,
        rx.icon(
            rx.cond(
                NominaRRHHState.orden_desc_empleados_preparacion,
                "arrow-down",
                "arrow-up",
            ),
            size=12,
            color=Colors.TEXT_MUTED,
        ),
        rx.fragment(),
    )


def _header_sortable(
    label: str,
    field: str,
    *,
    width: str,
    align: str = "left",
) -> rx.Component:
    justify = "center" if align == "center" else "end" if align == "right" else "start"
    return rx.table.column_header_cell(
        rx.button(
            rx.hstack(
                rx.text(
                    label,
                    font_size=Typography.SIZE_XS,
                    font_weight=Typography.WEIGHT_SEMIBOLD,
                    color=Colors.TEXT_MUTED,
                    text_transform="uppercase",
                ),
                _sort_indicator(field),
                spacing="1",
                justify=justify,
                width="100%",
            ),
            on_click=NominaRRHHState.ordenar_tabla_empleados_preparacion(field),
            variant="ghost",
            size="1",
            width="100%",
            padding_x="0",
            cursor="pointer",
        ),
        width=width,
        text_align=align,
    )


def _header_static(label: str, *, width: str, align: str = "left") -> rx.Component:
    return rx.table.column_header_cell(
        rx.text(
            label,
            font_size=Typography.SIZE_XS,
            font_weight=Typography.WEIGHT_SEMIBOLD,
            color=Colors.TEXT_MUTED,
            text_transform="uppercase",
        ),
        width=width,
        text_align=align,
    )


def _celda_centrada(content: rx.Component) -> rx.Component:
    return rx.table.cell(
        rx.center(content, width="100%"),
        text_align="center",
    )


def _celda_monto(value, *, color: str = Colors.TEXT_SECONDARY) -> rx.Component:
    return rx.table.cell(
        rx.text(
            value,
            font_size=Typography.SIZE_SM,
            color=color,
            width="100%",
            text_align="right",
            style={"fontVariantNumeric": "tabular-nums"},
        ),
        text_align="right",
    )


def _badge_dias_trabajados(empleado: dict) -> rx.Component:
    return rx.badge(
        empleado["dias_trabajados_ui"].to(str),
        color_scheme=rx.cond(empleado["dias_completos"], "green", "amber"),
        variant="soft",
        size="1",
        min_width="34px",
        justify_content="center",
    )


def _badge_medio_pago(empleado: dict) -> rx.Component:
    return rx.badge(
        empleado["medio_pago_badge"],
        color_scheme=empleado["medio_pago_scheme"],
        variant="soft",
        size="1",
    )


def _accion_empleado(empleado: dict) -> rx.Component:
    return rx.button(
        rx.cond(
            NominaRRHHState.periodo_es_borrador | NominaRRHHState.periodo_en_preparacion,
            "Editar",
            "Ver",
        ),
        variant=rx.cond(
            NominaRRHHState.periodo_es_borrador | NominaRRHHState.periodo_en_preparacion,
            "outline",
            "ghost",
        ),
        color_scheme="gray",
        size="1",
        on_click=NominaRRHHState.abrir_modal_descuento(empleado),
    )


def _fila_empleado(empleado: dict) -> rx.Component:
    return rx.table.row(
        rx.table.cell(
            rx.text(
                empleado["nombre_empleado_fmt"],
                font_size=Typography.SIZE_SM,
                font_weight=Typography.WEIGHT_MEDIUM,
                color=Colors.TEXT_PRIMARY,
                max_width="220px",
                overflow="hidden",
                text_overflow="ellipsis",
                white_space="nowrap",
            ),
        ),
        rx.table.cell(
            rx.text(
                empleado["sede_display"],
                font_size=Typography.SIZE_XS,
                color=rx.cond(
                    empleado["sede_display"] == "SIN SEDE",
                    Colors.TEXT_MUTED,
                    Colors.TEXT_SECONDARY,
                ),
                width="100%",
                text_align="center",
                max_width="140px",
                overflow="hidden",
                text_overflow="ellipsis",
                white_space="nowrap",
            ),
            text_align="center",
        ),
        _celda_monto(empleado["salario_diario_fmt"], color=Colors.TEXT_SECONDARY),
        _celda_centrada(_badge_dias_trabajados(empleado)),
        _celda_centrada(
            rx.cond(
                empleado["dias_faltas"].to(int) > 0,
                rx.text(
                    empleado["dias_faltas"].to(str),
                    font_size=Typography.SIZE_SM,
                    font_weight=Typography.WEIGHT_MEDIUM,
                    color=Colors.ERROR,
                ),
                rx.text("—", font_size=Typography.SIZE_SM, color=Colors.TEXT_MUTED),
            )
        ),
        _celda_monto(
            empleado["extras_preview_fmt"],
            color=rx.cond(
                empleado["extras_preview"].to(float) > 0,
                Colors.SUCCESS,
                Colors.TEXT_MUTED,
            ),
        ),
        _celda_monto(
            empleado["descuentos_preview_fmt"],
            color=rx.cond(
                empleado["descuentos_preview"].to(float) > 0,
                Colors.INFO,
                Colors.TEXT_MUTED,
            ),
        ),
        _celda_monto(empleado["neto_preview_fmt"], color=Colors.TEXT_PRIMARY),
        _celda_centrada(_badge_medio_pago(empleado)),
        _celda_centrada(_accion_empleado(empleado)),
    )


def _fila_empleado_aguinaldo(empleado: dict) -> rx.Component:
    return rx.table.row(
        rx.table.cell(
            rx.text(
                empleado["nombre_empleado_fmt"],
                font_size=Typography.SIZE_SM,
                font_weight=Typography.WEIGHT_MEDIUM,
                color=Colors.TEXT_PRIMARY,
                max_width="220px",
                overflow="hidden",
                text_overflow="ellipsis",
                white_space="nowrap",
            ),
        ),
        _celda_centrada(
            rx.text(
                empleado["fecha_ingreso_vigente_aguinaldo_fmt"],
                font_size=Typography.SIZE_SM,
                color=Colors.TEXT_SECONDARY,
            )
        ),
        _celda_centrada(
            rx.text(
                empleado["dias_laborados_aguinaldo"].to(str),
                font_size=Typography.SIZE_SM,
                color=Colors.TEXT_PRIMARY,
            )
        ),
        _celda_centrada(
            rx.text(
                empleado["factor_proporcional_aguinaldo_fmt"],
                font_size=Typography.SIZE_SM,
                color=Colors.TEXT_SECONDARY,
                style={"fontVariantNumeric": "tabular-nums"},
            )
        ),
        _celda_centrada(
            rx.text(
                empleado["dias_aguinaldo_snapshot"].to(str),
                font_size=Typography.SIZE_SM,
                color=Colors.TEXT_PRIMARY,
            )
        ),
        _celda_monto(empleado["monto_aguinaldo_bruto_fmt"], color=Colors.TEXT_PRIMARY),
        _celda_centrada(
            rx.badge(
                rx.cond(
                    empleado["modo_calculo_aguinaldo"] == "MANUAL",
                    "Manual",
                    "Auto",
                ),
                color_scheme=rx.cond(
                    empleado["modo_calculo_aguinaldo"] == "MANUAL",
                    "amber",
                    "gray",
                ),
                variant="soft",
                size="1",
            )
        ),
    )


def _headers_ordinaria() -> list[rx.Component]:
    return [
        _header_sortable("Nombre", "nombre", width="220px"),
        _header_sortable("Sede", "sede", width="140px", align="center"),
        _header_sortable("Salario diario", "salario", width="120px", align="right"),
        _header_static("Dias trab.", width="90px", align="center"),
        _header_sortable("Faltas", "faltas", width="80px", align="center"),
        _header_sortable("Extras", "extras", width="120px", align="right"),
        _header_sortable("Descuentos", "descuentos", width="120px", align="right"),
        _header_sortable("Neto a pagar", "neto", width="130px", align="right"),
        _header_static("Medio de pago", width="110px", align="center"),
        _header_static("Accion", width="90px", align="center"),
    ]


def _headers_aguinaldo() -> list[rx.Component]:
    return [
        _header_sortable("Nombre", "nombre", width="220px"),
        _header_static("Ingreso vigente", width="120px", align="center"),
        _header_static("Dias laborados", width="110px", align="center"),
        _header_static("Factor", width="90px", align="center"),
        _header_static("Dias aguinaldo", width="110px", align="center"),
        _header_sortable("Monto bruto", "neto", width="130px", align="right"),
        _header_static("Auto / Manual", width="110px", align="center"),
    ]


def _tabla_empleados() -> rx.Component:
    tabla = rx.cond(
        NominaRRHHState.periodo_actual_es_aguinaldo,
        table_shell(
            loading=NominaRRHHState.loading,
            header_cells=_headers_aguinaldo(),
            body_component=rx.foreach(
                NominaRRHHState.empleados_periodo_paginados,
                _fila_empleado_aguinaldo,
            ),
            has_rows=NominaRRHHState.tiene_empleados_filtrados,
            empty_component=rx.cond(
                NominaRRHHState.filtro_busqueda_empleados != "",
                tabla_vacia(mensaje="No hay empleados que coincidan con la busqueda."),
                tabla_vacia(mensaje="No hay empleados en este periodo."),
            ),
            total_caption=NominaRRHHState.total_caption_empleados_preparacion,
            footer_component=table_pagination(
                current_page=NominaRRHHState.pagina_empleados_preparacion_actual,
                total_pages=NominaRRHHState.total_paginas_empleados_preparacion,
                page_numbers=NominaRRHHState.paginas_visibles_empleados_preparacion,
                on_page_change=NominaRRHHState.ir_a_pagina_empleados_preparacion,
                on_previous=NominaRRHHState.pagina_anterior_empleados_preparacion,
                on_next=NominaRRHHState.pagina_siguiente_empleados_preparacion,
                color_scheme="blue",
            ),
            loading_rows=5,
        ),
        table_shell(
            loading=NominaRRHHState.loading,
            header_cells=_headers_ordinaria(),
            body_component=rx.foreach(
                NominaRRHHState.empleados_periodo_paginados,
                _fila_empleado,
            ),
            has_rows=NominaRRHHState.tiene_empleados_filtrados,
            empty_component=rx.cond(
                NominaRRHHState.filtro_busqueda_empleados != "",
                tabla_vacia(mensaje="No hay empleados que coincidan con la busqueda."),
                tabla_vacia(mensaje="No hay empleados en este periodo."),
            ),
            total_caption=NominaRRHHState.total_caption_empleados_preparacion,
            footer_component=table_pagination(
                current_page=NominaRRHHState.pagina_empleados_preparacion_actual,
                total_pages=NominaRRHHState.total_paginas_empleados_preparacion,
                page_numbers=NominaRRHHState.paginas_visibles_empleados_preparacion,
                on_page_change=NominaRRHHState.ir_a_pagina_empleados_preparacion,
                on_previous=NominaRRHHState.pagina_anterior_empleados_preparacion,
                on_next=NominaRRHHState.pagina_siguiente_empleados_preparacion,
                color_scheme="blue",
            ),
            loading_rows=5,
        ),
    )
    return rx.box(
        tabla,
        width="100%",
        overflow_x="auto",
    )


def _resumen_item(label: str, value, hint, *, accent: str = Colors.TEXT_PRIMARY) -> rx.Component:
    return rx.vstack(
        rx.text(
            label,
            font_size=Typography.SIZE_XS,
            color=Colors.TEXT_MUTED,
            text_transform="uppercase",
            font_weight=Typography.WEIGHT_SEMIBOLD,
            text_align="center",
            width="100%",
        ),
        rx.text(
            value,
            font_size=Typography.SIZE_LG,
            font_weight=Typography.WEIGHT_MEDIUM,
            color=accent,
            text_align="center",
            width="100%",
            style={"fontVariantNumeric": "tabular-nums"},
        ),
        rx.cond(
            hint != "",
            rx.text(
                hint,
                font_size=Typography.SIZE_XS,
                color=Colors.TEXT_SECONDARY,
                text_align="center",
                width="100%",
            ),
            rx.fragment(),
        ),
        spacing="1",
        align="center",
        min_width="140px",
    )


def _resumen_footer_divider() -> rx.Component:
    return rx.box(
        width="1px",
        align_self="stretch",
        background=Colors.BORDER,
        opacity="0.7",
    )


def _resumen_pie_nomina() -> rx.Component:
    return rx.box(
        rx.flex(
            _resumen_item(
                "Total empleados",
                NominaRRHHState.total_empleados_resumen_preparacion.to(str),
                "",
            ),
            _resumen_footer_divider(),
            _resumen_item(
                rx.cond(
                    NominaRRHHState.periodo_actual_es_aguinaldo,
                    "Total bruto",
                    "Total neto",
                ),
                NominaRRHHState.total_neto_resumen_preparacion_fmt,
                "",
                accent=Colors.INFO,
            ),
            _resumen_footer_divider(),
            _resumen_item(
                "Transferencias",
                NominaRRHHState.total_transferencias_resumen_preparacion.to(str),
                NominaRRHHState.monto_transferencias_resumen_preparacion_fmt,
            ),
            _resumen_footer_divider(),
            _resumen_item(
                "Efectivo",
                NominaRRHHState.total_efectivo_resumen_preparacion.to(str),
                NominaRRHHState.monto_efectivo_resumen_preparacion_fmt,
            ),
            _resumen_footer_divider(),
            _resumen_item(
                "Total descuentos",
                NominaRRHHState.total_descuentos_resumen_preparacion_fmt,
                "",
            ),
            width="100%",
            wrap="wrap",
            align="stretch",
            justify="between",
            column_gap=Spacing.MD,
            row_gap=Spacing.SM,
        ),
        width="100%",
        padding_x=Spacing.LG,
        padding_y=Spacing.MD,
        background=Colors.SECONDARY_LIGHT,
        border=f"1px solid {Colors.BORDER}",
        border_radius=Radius.LG,
    )


def preparacion_nomina_page() -> rx.Component:
    return rx.box(
        page_layout(
            header=rx.box(
                page_header(
                    titulo=rx.hstack(
                        rx.link(
                            "Nominas",
                            href=NominaRRHHState.nomina_base_path,
                            size="4",
                            color=Colors.TEXT_MUTED,
                            underline="none",
                        ),
                        rx.icon("chevron-right", size=14, color=Colors.TEXT_MUTED),
                        rx.text(
                            NominaRRHHState.nombre_periodo_actual,
                            size="4",
                            weight="medium",
                        ),
                        spacing="2",
                        align="center",
                    ),
                    subtitulo="Captura descuentos e incidencias antes de enviar a contabilidad",
                    icono="clipboard-list",
                    accion_principal=_header_actions(),
                ),
                width="100%",
                max_width="960px",
                margin_x="auto",
            ),
            content=rx.vstack(
                _metadata_periodo(),
                _callout_readonly(),
                _toolbar_tabla_empleados(),
                _tabla_empleados(),
                _resumen_pie_nomina(),
                modal_descuentos_empleado(),
                dialog_iniciar_preparacion(),
                dialog_enviar_contabilidad(),
                spacing="4",
                width="100%",
                max_width="960px",
                margin_x="auto",
            ),
        ),
        width="100%",
        min_height="100vh",
        on_mount=NominaRRHHState.on_mount_preparacion,
    )
