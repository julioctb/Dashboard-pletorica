"""Componentes de la página de plazas por contrato."""

from __future__ import annotations

import reflex as rx

from app.presentation.components.ui import (
    empty_state_card,
    estatus_badge,
    feedback_callout,
    input_busqueda,
    metric_card,
    metric_card_grid,
    page_header,
    segmented_tab_trigger,
    segmented_tabs,
    select_items_from_options,
    skeleton_tabla,
    tabla_cta_button,
    table_pagination,
    table_shell,
)
from app.presentation.theme import Colors, Radius, Spacing, Typography

from .state import ContratoPlazasState


PLAZAS_TABLE_HEADERS = [
    {"nombre": "", "ancho": "40px", "header_align": "center"},
    {"nombre": "#", "ancho": "50px", "header_align": "left"},
    {"nombre": "Categoría", "ancho": "180px", "header_align": "left"},
    {"nombre": "Sede", "ancho": "180px", "header_align": "center"},
    {"nombre": "Empleado asignado", "ancho": "200px", "header_align": "center"},
    {"nombre": "Estado", "ancho": "100px", "header_align": "center"},
    {"nombre": "", "ancho": "120px", "header_align": "center"},
]

def _section_label(texto: str) -> rx.Component:
    return rx.text(
        texto,
        font_size=Typography.SIZE_XS,
        font_weight=Typography.WEIGHT_SEMIBOLD,
        color=Colors.TEXT_MUTED,
        text_transform="uppercase",
        letter_spacing=Typography.LETTER_SPACING_SECTION_LABEL,
    )


def _header_plazas() -> rx.Component:
    """Header con breadcrumb inline — patrón Plazas › Código contrato."""
    return page_header(
        icono="layout-grid",
        titulo_compuesto=rx.hstack(
            rx.link(
                "Plazas",
                href="/portal/plazas",
                size="6",
                weight="bold",
                color=Colors.PORTAL_PRIMARY_TEXT,
                _hover={"text_decoration": "underline"},
            ),
            rx.text("›", color=Colors.TEXT_MUTED, size="5"),
            rx.text(
                ContratoPlazasState.codigo_contrato_actual,
                size="6",
                weight="bold",
            ),
            rx.cond(
                ContratoPlazasState.estatus_contrato_actual != "",
                estatus_badge(ContratoPlazasState.estatus_contrato_actual),
                rx.fragment(),
            ),
            align="center",
            spacing="2",
            wrap="wrap",
        ),
        subtitulo_compuesto=rx.text(
            ContratoPlazasState.subtitulo_contrato_actual,
            font_size=Typography.SIZE_SM,
            color=Colors.TEXT_SECONDARY,
        ),
        color_icono=Colors.PORTAL_ACCENT_SCHEME,
    )


def _callout_sin_sede() -> rx.Component:
    return rx.cond(
        ContratoPlazasState.mostrar_callout_sin_sede,
        feedback_callout(
            content=rx.text(
                ContratoPlazasState.mensaje_callout_sin_sede,
                font_size=Typography.SIZE_SM,
            ),
            kind="warning",
        ),
        rx.fragment(),
    )


def metricas_contrato_plazas() -> rx.Component:
    return metric_card_grid(
        metric_card(
            titulo="Plazas",
            valor=ContratoPlazasState.total_plazas_contrato_actual,
            icono=None,
            color_scheme=Colors.NEUTRAL_SCHEME,
            show_icon=False,
            align="center",
            descripcion="Configuradas en el contrato",
        ),
        metric_card(
            titulo="Ocupadas",
            valor=ContratoPlazasState.plazas_ocupadas_contrato_actual,
            icono=None,
            color_scheme=Colors.NEUTRAL_SCHEME,
            show_icon=False,
            align="center",
            value_color=ContratoPlazasState.color_metrica_ocupadas,
            descripcion=ContratoPlazasState.descripcion_metrica_ocupadas,
        ),
        metric_card(
            titulo="Vacantes",
            valor=ContratoPlazasState.plazas_vacantes_contrato_actual,
            icono=None,
            color_scheme=Colors.NEUTRAL_SCHEME,
            show_icon=False,
            align="center",
            value_color=ContratoPlazasState.color_metrica_vacantes,
            descripcion=ContratoPlazasState.descripcion_metrica_vacantes,
        ),
        metric_card(
            titulo="Costo/mes",
            valor=ContratoPlazasState.costo_presupuestado_contrato_actual_fmt,
            icono=None,
            color_scheme=Colors.NEUTRAL_SCHEME,
            show_icon=False,
            align="center",
            descripcion=ContratoPlazasState.descripcion_metrica_costo,
        ),
    )


def _tabs_contrato_plazas() -> rx.Component:
    return segmented_tabs(
        segmented_tab_trigger(
            label="Plazas",
            value="plazas",
            active_background=Colors.PORTAL_PRIMARY,
            active_hover_background=Colors.PORTAL_PRIMARY_HOVER,
        ),
        segmented_tab_trigger(
            label="Categorías",
            value="categorias",
            active_background=Colors.PORTAL_PRIMARY,
            active_hover_background=Colors.PORTAL_PRIMARY_HOVER,
        ),
        segmented_tab_trigger(
            label="Resumen",
            value="resumen",
            active_background=Colors.PORTAL_PRIMARY,
            active_hover_background=Colors.PORTAL_PRIMARY_HOVER,
        ),
        value=ContratoPlazasState.tab_activa,
        on_change=ContratoPlazasState.set_tab_activa,
    )


def _toolbar_plazas() -> rx.Component:
    return rx.flex(
        rx.box(
            input_busqueda(
                value=ContratoPlazasState.plaza_busqueda,
                on_change=ContratoPlazasState.set_plaza_busqueda,
                on_clear=ContratoPlazasState.limpiar_plaza_busqueda,
                placeholder="Buscar plaza, empleado o sede...",
                toolbar_style=True,
                width="100%",
            ),
            flex="1 1 0px",
            min_width="180px",
        ),
        rx.box(
            rx.select.root(
                rx.select.trigger(
                    placeholder="Categoría",
                    width="100%",
                ),
                rx.select.content(
                    rx.select.item("Todas las categorías", value="all"),
                    select_items_from_options(ContratoPlazasState.plaza_categorias_opciones),
                ),
                value=ContratoPlazasState.plaza_filtro_categoria,
                on_change=ContratoPlazasState.set_plaza_filtro_categoria,
                size="2",
            ),
            flex="1 1 200px",
            min_width="180px",
        ),
        rx.box(
            rx.select.root(
                rx.select.trigger(
                    placeholder="Estado",
                    width="100%",
                ),
                rx.select.content(
                    rx.select.item("Todos los estados", value="all"),
                    rx.select.item("Ocupada", value="OCUPADA"),
                    rx.select.item("Vacante", value="VACANTE"),
                    rx.select.item("Sin sede", value="SIN_SEDE"),
                ),
                value=ContratoPlazasState.plaza_filtro_estado,
                on_change=ContratoPlazasState.set_plaza_filtro_estado,
                size="2",
            ),
            flex="1 1 180px",
            min_width="180px",
        ),
        width="100%",
        align="center",
        wrap="wrap",
        gap=Spacing.SM,
    )


def _barra_acciones_masivas() -> rx.Component:
    return rx.cond(
        ContratoPlazasState.mostrar_barra_acciones_masivas,
        rx.box(
            rx.flex(
                rx.text(
                    ContratoPlazasState.plazas_seleccionadas_count.to(str)
                    + " plazas seleccionadas",
                    font_weight=Typography.WEIGHT_MEDIUM,
                    font_size=Typography.SIZE_SM,
                    color=Colors.TEXT_PRIMARY,
                    white_space="nowrap",
                ),
                rx.flex(
                    rx.select.root(
                        rx.select.trigger(
                            placeholder="Sede...",
                            width="180px",
                        ),
                        rx.select.content(
                            select_items_from_options(ContratoPlazasState.opciones_sedes_plaza),
                        ),
                        value=ContratoPlazasState.sede_masiva_actual,
                        on_change=ContratoPlazasState.set_sede_masiva_actual,
                        size="1",
                    ),
                    rx.button(
                        "Asignar sede",
                        on_click=ContratoPlazasState.asignar_sede_masiva_actual,
                        size="1",
                        variant="outline",
                        color_scheme=Colors.PORTAL_ACCENT_SCHEME,
                        disabled=ContratoPlazasState.sede_masiva_actual == "",
                    ),
                    align="center",
                    gap=Spacing.SM,
                    wrap="wrap",
                ),
                rx.flex(
                    rx.select.root(
                        rx.select.trigger(
                            placeholder="Categoría...",
                            width="220px",
                        ),
                        rx.select.content(
                            select_items_from_options(
                                ContratoPlazasState.opciones_categorias_masivas_actual,
                            ),
                        ),
                        value=ContratoPlazasState.categoria_masiva_actual,
                        on_change=ContratoPlazasState.set_categoria_masiva_actual,
                        size="1",
                    ),
                    rx.button(
                        "Cambiar categoría",
                        on_click=ContratoPlazasState.cambiar_categoria_masiva_actual,
                        size="1",
                        variant="outline",
                        color_scheme=Colors.PORTAL_ACCENT_SCHEME,
                        disabled=ContratoPlazasState.categoria_masiva_actual == "",
                    ),
                    align="center",
                    gap=Spacing.SM,
                    wrap="wrap",
                ),
                rx.text(
                    "Deseleccionar",
                    on_click=ContratoPlazasState.deseleccionar_todas,
                    font_size=Typography.SIZE_XS,
                    color=Colors.TEXT_SECONDARY,
                    text_decoration="underline",
                    cursor="pointer",
                    white_space="nowrap",
                ),
                width="100%",
                align="center",
                justify="between",
                wrap="wrap",
                gap=Spacing.MD,
                padding=Spacing.MD,
                background=Colors.SECONDARY_LIGHT,
                border=f"1px solid {Colors.BORDER_STRONG}",
                border_radius=Radius.MD,
            ),
            position="sticky",
            top=Spacing.SM,
            z_index="2",
            width="100%",
        ),
        rx.fragment(),
    )


def _table_headers_plazas() -> list[rx.Component]:
    return [
        rx.table.column_header_cell(
            rx.center(
                rx.checkbox(
                    checked=ContratoPlazasState.seleccion_todas_plazas_visibles_actual,
                    on_change=ContratoPlazasState.seleccionar_todas_plazas_actuales,
                    size="1",
                    disabled=ContratoPlazasState.contrato_solo_consulta,
                ),
                width="100%",
            ),
            width="40px",
            text_align="center",
        ),
        *[
            rx.table.column_header_cell(
                rx.text(
                    col["nombre"],
                    font_size=Typography.SIZE_XS,
                    font_weight=Typography.WEIGHT_SEMIBOLD,
                    color=Colors.TEXT_MUTED,
                    text_transform="uppercase",
                    letter_spacing=Typography.LETTER_SPACING_SECTION_LABEL,
                ),
                width=col["ancho"],
                text_align=col.get("header_align", "left"),
            )
            for col in PLAZAS_TABLE_HEADERS[1:]
        ],
    ]


def _celda_categoria(plaza: dict) -> rx.Component:
    return rx.table.cell(
        rx.box(
            rx.text(
                plaza["categoria_nombre_ui"],
                font_weight=Typography.WEIGHT_MEDIUM,
                color=Colors.TEXT_PRIMARY,
                font_size=Typography.SIZE_SM,
            ),
            rx.cond(
                plaza["tiene_sueldo_categoria"],
                rx.text(
                    plaza["sueldo_categoria_label"],
                    font_size=Typography.SIZE_XS,
                    color=Colors.TEXT_MUTED,
                    font_variant_numeric="tabular-nums",
                ),
                rx.text(
                    "—",
                    font_size=Typography.SIZE_XS,
                    color=Colors.TEXT_MUTED,
                ),
            ),
            text_align="left",
        ),
        text_align="left",
    )


def _celda_sede(plaza: dict) -> rx.Component:
    return rx.table.cell(
        rx.cond(
            plaza["tiene_sede"],
            rx.text(
                plaza["sede_display_tabla"],
                font_size=Typography.SIZE_SM,
                color=Colors.TEXT_SECONDARY,
            ),
            rx.text(
                "—",
                font_size=Typography.SIZE_SM,
                color=Colors.TEXT_MUTED,
            ),
        ),
        text_align="center",
    )


def _celda_empleado(plaza: dict) -> rx.Component:
    return rx.table.cell(
        rx.cond(
            plaza["tiene_empleado"],
            rx.cond(
                plaza["empleado_href"] != "",
                rx.link(
                    rx.text(
                        plaza["empleado_nombre_ui"],
                        font_weight=Typography.WEIGHT_MEDIUM,
                        color=Colors.PORTAL_PRIMARY_TEXT,
                        font_size=Typography.SIZE_SM,
                    ),
                    href=plaza["empleado_href"],
                    underline="none",
                    _hover={"text_decoration": "underline"},
                ),
                rx.text(
                    plaza["empleado_nombre_ui"],
                    font_weight=Typography.WEIGHT_MEDIUM,
                    color=Colors.PORTAL_PRIMARY_TEXT,
                    font_size=Typography.SIZE_SM,
                ),
            ),
            rx.text(
                "—",
                font_size=Typography.SIZE_SM,
                color=Colors.TEXT_MUTED,
            ),
        ),
        text_align="center",
    )


def _menu_acciones_ocupada(plaza: dict) -> rx.Component:
    return rx.menu.root(
        rx.menu.trigger(
            tabla_cta_button(
                text=plaza["cta_texto"],
                on_click=rx.noop,
                color_scheme=Colors.NEUTRAL_SCHEME,
                size="1",
                variant="outline",
            ),
        ),
        rx.menu.content(
            rx.menu.item(
                rx.icon("eye", size=14),
                " Ver empleado",
                on_click=ContratoPlazasState.accion_ver_empleado_plaza(plaza["id"]),
            ),
            rx.menu.item(
                rx.icon("map-pin", size=14),
                " Cambiar sede",
                on_click=ContratoPlazasState.accion_cambiar_sede(plaza["id"]),
            ),
            rx.menu.item(
                rx.icon("shuffle", size=14),
                " Reasignar",
                on_click=ContratoPlazasState.accion_reasignar_plaza(plaza["id"]),
            ),
            rx.menu.separator(),
            rx.menu.item(
                rx.icon("user-minus", size=14),
                " Iniciar baja",
                color=Colors.ERROR,
                on_click=ContratoPlazasState.accion_iniciar_baja(plaza["empleado_id"]),
            ),
        ),
    )


def _acciones_plaza(plaza: dict) -> rx.Component:
    return rx.cond(
        plaza["mostrar_menu_acciones"],
        _menu_acciones_ocupada(plaza),
        rx.match(
            plaza["cta_texto"],
            (
                "Asignar",
                tabla_cta_button(
                    text="Asignar",
                    on_click=ContratoPlazasState.accion_asignar_empleado(plaza["id"]),
                    color_scheme=Colors.PORTAL_ACCENT_SCHEME,
                    size="1",
                    variant="outline",
                ),
            ),
            (
                "Asignar sede",
                tabla_cta_button(
                    text="Asignar sede",
                    on_click=ContratoPlazasState.accion_asignar_sede(plaza["id"]),
                    color_scheme=Colors.WARNING_SCHEME,
                    size="1",
                    variant="outline",
                ),
            ),
            (
                "Consultar",
                tabla_cta_button(
                    text="Consultar",
                    on_click=ContratoPlazasState.ver_plaza(plaza["id"]),
                    color_scheme=Colors.NEUTRAL_SCHEME,
                    size="1",
                    variant="outline",
                ),
            ),
            tabla_cta_button(
                text="Ver",
                on_click=ContratoPlazasState.ver_plaza(plaza["id"]),
                color_scheme=Colors.NEUTRAL_SCHEME,
                size="1",
                variant="outline",
            ),
        ),
    )


def _plaza_row(plaza: dict) -> rx.Component:
    return rx.table.row(
        rx.table.cell(
            rx.center(
                rx.checkbox(
                    checked=plaza["seleccionada"],
                    on_change=lambda checked: ContratoPlazasState.toggle_plaza_contrato_actual(
                        plaza["id"],
                        checked,
                    ),
                    size="1",
                    disabled=ContratoPlazasState.contrato_solo_consulta,
                ),
                width="100%",
            ),
        ),
        rx.table.cell(
            rx.text(
                plaza["numero_plaza_texto"],
                font_size=Typography.SIZE_SM,
                color=Colors.TEXT_MUTED,
                font_variant_numeric="tabular-nums",
            ),
            text_align="left",
        ),
        _celda_categoria(plaza),
        _celda_sede(plaza),
        _celda_empleado(plaza),
        rx.table.cell(
            estatus_badge(plaza["estatus_plaza"]),
            text_align="center",
        ),
        rx.table.cell(
            _acciones_plaza(plaza),
            text_align="center",
        ),
        background=rx.cond(
            plaza["seleccionada"],
            Colors.PORTAL_PRIMARY_LIGHTER,
            Colors.SURFACE,
        ),
        _hover={
            "background": rx.cond(
                plaza["seleccionada"],
                Colors.PORTAL_PRIMARY_LIGHTER,
                Colors.SURFACE_HOVER,
            ),
        },
    )


def _empty_state_plazas() -> rx.Component:
    return empty_state_card(
        title=ContratoPlazasState.titulo_empty_state_plazas_contrato,
        description=ContratoPlazasState.descripcion_empty_state_plazas_contrato,
        icon="layout-grid",
        action_button=rx.cond(
            ContratoPlazasState.hay_filtros_plazas_contrato_activos,
            tabla_cta_button(
                text="Limpiar filtros",
                on_click=ContratoPlazasState.limpiar_filtros_plazas_contrato,
                color_scheme=Colors.PORTAL_ACCENT_SCHEME,
                variant="outline",
                size="1",
            ),
            tabla_cta_button(
                text="Ver contratos",
                on_click=ContratoPlazasState.volver_a_contratos,
                color_scheme=Colors.PORTAL_ACCENT_SCHEME,
                variant="outline",
                size="1",
            ),
        ),
    )


def _tabla_plazas() -> rx.Component:
    return rx.box(
        table_shell(
            loading=ContratoPlazasState.loading | ContratoPlazasState.cargando_plazas_contrato_actual,
            headers=PLAZAS_TABLE_HEADERS,
            header_cells=_table_headers_plazas(),
            rows=ContratoPlazasState.plazas_tabla_rows,
            row_renderer=_plaza_row,
            has_rows=ContratoPlazasState.plaza_total_filtradas > 0,
            empty_component=_empty_state_plazas(),
            total_caption=ContratoPlazasState.caption_plazas_contrato_actual,
            footer_component=table_pagination(
                current_page=ContratoPlazasState.pagina_plaza_actual,
                total_pages=ContratoPlazasState.total_paginas_plaza_actual,
                page_numbers=ContratoPlazasState.page_numbers_plaza_actual,
                on_page_change=ContratoPlazasState.ir_a_pagina_actual,
                on_previous=ContratoPlazasState.pagina_anterior_actual,
                on_next=ContratoPlazasState.pagina_siguiente_actual,
                color_scheme=Colors.PORTAL_ACCENT_SCHEME,
            ),
            table_size="1",
            loading_rows=8,
        ),
        border=f"1px solid {Colors.BORDER}",
        border_radius=Radius.LG,
        background=Colors.SURFACE,
        overflow="hidden",
        width="100%",
    )


def _table_headers_categorias() -> list[rx.Component]:
    return [
        rx.table.column_header_cell(
            rx.text(
                "Categoría",
                font_size=Typography.SIZE_XS,
                font_weight=Typography.WEIGHT_SEMIBOLD,
                color=Colors.TEXT_MUTED,
                text_transform="uppercase",
                letter_spacing=Typography.LETTER_SPACING_SECTION_LABEL,
            ),
            width="220px",
            text_align="left",
        ),
        rx.table.column_header_cell(
            rx.text(
                rx.cond(
                    ContratoPlazasState.toggle_vista_sueldo == "BRUTO",
                    "Sueldo bruto",
                    "Sueldo neto",
                ),
                font_size=Typography.SIZE_XS,
                font_weight=Typography.WEIGHT_SEMIBOLD,
                color=Colors.TEXT_MUTED,
                text_transform="uppercase",
                letter_spacing=Typography.LETTER_SPACING_SECTION_LABEL,
            ),
            width="170px",
            text_align="right",
        ),
        rx.table.column_header_cell(
            rx.text(
                "Costo empresa",
                font_size=Typography.SIZE_XS,
                font_weight=Typography.WEIGHT_SEMIBOLD,
                color=Colors.TEXT_MUTED,
                text_transform="uppercase",
                letter_spacing=Typography.LETTER_SPACING_SECTION_LABEL,
            ),
            width="150px",
            text_align="right",
        ),
        rx.table.column_header_cell(
            rx.text(
                "Margen",
                font_size=Typography.SIZE_XS,
                font_weight=Typography.WEIGHT_SEMIBOLD,
                color=Colors.TEXT_MUTED,
                text_transform="uppercase",
                letter_spacing=Typography.LETTER_SPACING_SECTION_LABEL,
            ),
            width="130px",
            text_align="right",
        ),
        rx.table.column_header_cell(
            rx.text(
                "Plazas",
                font_size=Typography.SIZE_XS,
                font_weight=Typography.WEIGHT_SEMIBOLD,
                color=Colors.TEXT_MUTED,
                text_transform="uppercase",
                letter_spacing=Typography.LETTER_SPACING_SECTION_LABEL,
            ),
            width="120px",
            text_align="center",
        ),
        rx.table.column_header_cell(
            rx.text(
                "Costo total/mes",
                font_size=Typography.SIZE_XS,
                font_weight=Typography.WEIGHT_SEMIBOLD,
                color=Colors.TEXT_MUTED,
                text_transform="uppercase",
                letter_spacing=Typography.LETTER_SPACING_SECTION_LABEL,
            ),
            width="170px",
            text_align="right",
        ),
        rx.table.column_header_cell(
            rx.text(""),
            width="150px",
            text_align="center",
        ),
    ]


def _categoria_row(categoria: dict) -> rx.Component:
    return rx.table.row(
        rx.table.cell(
            rx.box(
                rx.text(
                    categoria["categoria_nombre_ui"],
                    font_size=Typography.SIZE_SM,
                    font_weight=Typography.WEIGHT_MEDIUM,
                    color=Colors.TEXT_PRIMARY,
                ),
                rx.text(
                    categoria["plazas_resumen_label"],
                    font_size=Typography.SIZE_XS,
                    color=Colors.TEXT_MUTED,
                ),
                text_align="left",
            ),
            text_align="left",
        ),
        rx.table.cell(
            rx.box(
                rx.text(
                    categoria["sueldo_visible_fmt"],
                    font_size=Typography.SIZE_SM,
                    font_weight=rx.cond(
                        categoria["es_ancla"],
                        Typography.WEIGHT_MEDIUM,
                        Typography.WEIGHT_REGULAR,
                    ),
                    color=Colors.TEXT_PRIMARY,
                    font_variant_numeric="tabular-nums",
                ),
                rx.text(
                    categoria["sueldo_diario_label"],
                    font_size=Typography.SIZE_XS,
                    color=Colors.TEXT_MUTED,
                    font_variant_numeric="tabular-nums",
                ),
                rx.cond(
                    categoria["mostrar_calculado"],
                    rx.text(
                        "calculado",
                        font_size=Typography.SIZE_XS,
                        color=Colors.TEXT_MUTED,
                        font_style="italic",
                    ),
                    rx.fragment(),
                ),
                rx.cond(
                    categoria["mostrar_warning_salario_minimo"],
                    rx.flex(
                        rx.icon("triangle-alert", size=12, color=Colors.WARNING),
                        rx.text(
                            "Menor al salario mínimo — requiere jornada parcial",
                            font_size=Typography.SIZE_XS,
                            color=Colors.WARNING,
                        ),
                        align="center",
                        gap=Spacing.XS,
                        justify="end",
                        width="100%",
                    ),
                    rx.fragment(),
                ),
                text_align="right",
            ),
            text_align="right",
        ),
        rx.table.cell(
            rx.box(
                rx.text(
                    categoria["costo_empresa_fmt"],
                    font_size=Typography.SIZE_SM,
                    font_weight=Typography.WEIGHT_MEDIUM,
                    color=Colors.TEXT_PRIMARY,
                    font_variant_numeric="tabular-nums",
                ),
                rx.text(
                    categoria["carga_patronal_pct_texto"],
                    font_size=Typography.SIZE_XS,
                    color=Colors.TEXT_MUTED,
                ),
                text_align="right",
            ),
            text_align="right",
        ),
        rx.table.cell(
            rx.box(
                rx.text(
                    categoria["margen_fmt"],
                    font_size=Typography.SIZE_SM,
                    font_weight=Typography.WEIGHT_MEDIUM,
                    font_variant_numeric="tabular-nums",
                    color=rx.cond(
                        categoria["margen_es_positivo"],
                        Colors.SUCCESS,
                        rx.cond(
                            categoria["margen_es_negativo"],
                            Colors.ERROR,
                            Colors.TEXT_MUTED,
                        ),
                    ),
                ),
                rx.cond(
                    categoria["mostrar_warning_margen_negativo"],
                    rx.text(
                        "Costo supera al contractual",
                        font_size=Typography.SIZE_XS,
                        color=Colors.ERROR,
                    ),
                    rx.fragment(),
                ),
                text_align="right",
            ),
            text_align="right",
        ),
        rx.table.cell(
            rx.box(
                rx.text(
                    categoria["plazas_total_texto"],
                    font_size=Typography.SIZE_SM,
                    font_weight=Typography.WEIGHT_MEDIUM,
                    color=Colors.TEXT_PRIMARY,
                    font_variant_numeric="tabular-nums",
                ),
                rx.text(
                    categoria["plazas_min_max_label"],
                    font_size=Typography.SIZE_XS,
                    color=Colors.TEXT_MUTED,
                ),
                text_align="center",
            ),
            text_align="center",
        ),
        rx.table.cell(
            rx.box(
                rx.text(
                    categoria["costo_total_presupuestado_fmt"],
                    font_size=Typography.SIZE_SM,
                    font_weight=Typography.WEIGHT_MEDIUM,
                    color=Colors.TEXT_PRIMARY,
                    font_variant_numeric="tabular-nums",
                ),
                rx.cond(
                    categoria["mostrar_costo_total_actual"],
                    rx.text(
                        categoria["costo_total_actual_label"],
                        font_size=Typography.SIZE_XS,
                        color=Colors.TEXT_MUTED,
                        font_variant_numeric="tabular-nums",
                    ),
                    rx.text(
                        "—",
                        font_size=Typography.SIZE_XS,
                        color=Colors.TEXT_MUTED,
                    ),
                ),
                text_align="right",
            ),
            text_align="right",
        ),
        rx.table.cell(
            rx.flex(
                rx.text(
                    categoria["toggle_desglose_texto"],
                    on_click=ContratoPlazasState.toggle_desglose_categoria(categoria["id"]),
                    font_size=Typography.SIZE_XS,
                    color=Colors.PORTAL_PRIMARY_TEXT,
                    text_decoration="underline",
                    cursor="pointer",
                    white_space="nowrap",
                ),
                rx.text("·", color=Colors.TEXT_MUTED),
                tabla_cta_button(
                    text=rx.cond(
                        ContratoPlazasState.contrato_solo_consulta,
                        "Consultar",
                        "Editar",
                    ),
                    on_click=ContratoPlazasState.editar_categoria(categoria["id"]),
                    color_scheme=Colors.NEUTRAL_SCHEME,
                    size="1",
                    variant="outline",
                ),
                align="center",
                justify="center",
                gap=Spacing.SM,
                wrap="wrap",
            ),
            text_align="center",
        ),
    )


def _categoria_desglose_row(categoria: dict) -> rx.Component:
    return rx.table.row(
        rx.table.cell(
            rx.grid(
                _desglose_item("IMSS obrero", categoria["imss_obrero_fmt"]),
                _desglose_item("IMSS patronal", categoria["imss_patronal_fmt"]),
                _desglose_item("ISR (estimado)", categoria["isr_estimado_fmt"]),
                _desglose_item("INFONAVIT", categoria["infonavit_fmt"]),
                _desglose_item("Retiro / cesantía", categoria["retiro_cesantia_fmt"]),
                _desglose_item(
                    "Neto estimado",
                    categoria["neto_estimado_fmt"],
                    valor_color=Colors.PORTAL_PRIMARY_TEXT,
                ),
                columns=rx.breakpoints(initial="1", sm="2", lg="3"),
                spacing="3",
                width="100%",
            ),
            col_span=7,
            background=Colors.SECONDARY_LIGHT,
            padding=Spacing.MD,
        ),
    )


def _desglose_item(
    label: str,
    value,
    *,
    valor_color=Colors.TEXT_PRIMARY,
) -> rx.Component:
    return rx.box(
        rx.text(
            label,
            font_size=Typography.SIZE_XS,
            font_weight=Typography.WEIGHT_MEDIUM,
            color=Colors.TEXT_MUTED,
            text_transform="uppercase",
            letter_spacing=Typography.LETTER_SPACING_SECTION_LABEL,
        ),
        rx.text(
            value,
            font_size=Typography.SIZE_SM,
            font_weight=Typography.WEIGHT_MEDIUM,
            color=valor_color,
            font_variant_numeric="tabular-nums",
        ),
    )


def _tab_categorias() -> rx.Component:
    categorias_body = rx.foreach(
        ContratoPlazasState.categorias_tabla_resumen,
        lambda categoria: rx.fragment(
            _categoria_row(categoria),
            rx.cond(
                categoria["desglose_visible"],
                _categoria_desglose_row(categoria),
                rx.fragment(),
            ),
        ),
    )

    return rx.vstack(
        rx.cond(
            ContratoPlazasState.mostrar_callout_nivel_riesgo,
            feedback_callout(
                content=rx.flex(
                    rx.text(
                        ContratoPlazasState.mensaje_callout_nivel_riesgo,
                        font_size=Typography.SIZE_SM,
                    ),
                    rx.link(
                        "Configurar",
                        href="/portal/mi-empresa",
                        color=Colors.PORTAL_PRIMARY_TEXT,
                        font_weight=Typography.WEIGHT_MEDIUM,
                        text_decoration="underline",
                        white_space="nowrap",
                    ),
                    align="center",
                    wrap="wrap",
                    gap=Spacing.SM,
                ),
                kind="warning",
            ),
            rx.fragment(),
        ),
        rx.flex(
            segmented_tabs(
                segmented_tab_trigger(
                    label="Bruto",
                    value="BRUTO",
                    active_background=Colors.PORTAL_PRIMARY,
                    active_hover_background=Colors.PORTAL_PRIMARY_HOVER,
                ),
                segmented_tab_trigger(
                    label="Neto",
                    value="NETO",
                    active_background=Colors.PORTAL_PRIMARY,
                    active_hover_background=Colors.PORTAL_PRIMARY_HOVER,
                ),
                value=ContratoPlazasState.toggle_vista_sueldo,
                on_change=ContratoPlazasState.set_toggle_vista_sueldo,
            ),
            rx.spacer(),
            rx.button(
                rx.icon("plus", size=14),
                "Agregar categoría",
                size="2",
                variant="outline",
                color_scheme=Colors.PORTAL_ACCENT_SCHEME,
                on_click=ContratoPlazasState.abrir_modal_categoria,
                disabled=ContratoPlazasState.contrato_solo_consulta,
            ),
            width="100%",
            align="center",
            gap=Spacing.SM,
            wrap="wrap",
        ),
        rx.box(
            table_shell(
                loading=ContratoPlazasState.loading,
                headers=[],
                header_cells=_table_headers_categorias(),
                body_component=categorias_body,
                has_rows=ContratoPlazasState.tiene_categorias_detalle_contrato,
                empty_component=empty_state_card(
                    title="No hay categorías configuradas",
                    description="Agregue la primera categoría para definir sueldo y costo base del contrato.",
                    icon="tags",
                    action_button=rx.button(
                        rx.icon("plus", size=14),
                        "Agregar categoría",
                        size="2",
                        variant="outline",
                        color_scheme=Colors.PORTAL_ACCENT_SCHEME,
                        on_click=ContratoPlazasState.abrir_modal_categoria,
                        disabled=ContratoPlazasState.contrato_solo_consulta,
                    ),
                ),
                total_caption=ContratoPlazasState.caption_tabla_categorias,
                table_size="1",
            ),
            border=f"1px solid {Colors.BORDER}",
            border_radius=Radius.LG,
            background=Colors.SURFACE,
            overflow="hidden",
            width="100%",
        ),
        rx.flex(
            rx.icon("info", size=12, color=Colors.TEXT_MUTED),
            rx.text(
                ContratoPlazasState.referencia_salario_minimo_label,
                font_size=Typography.SIZE_XS,
                color=Colors.TEXT_MUTED,
            ),
            align="center",
            gap=Spacing.XS,
            wrap="wrap",
            width="100%",
        ),
        spacing="4",
        width="100%",
    )


def _resumen_card(
    titulo: str,
    valor,
    detalle: str | rx.Var = "",
    extra: rx.Component | None = None,
) -> rx.Component:
    return rx.box(
        _section_label(titulo),
        rx.text(
            valor,
            font_size=Typography.SIZE_LG,
            font_weight=Typography.WEIGHT_SEMIBOLD,
            color=Colors.TEXT_PRIMARY,
            margin_top=Spacing.XS,
        ),
        rx.cond(
            detalle != "",
            rx.text(
                detalle,
                font_size=Typography.SIZE_SM,
                color=Colors.TEXT_SECONDARY,
                margin_top=Spacing.XS,
            ),
            rx.fragment(),
        ),
        rx.cond(extra is not None, extra, rx.fragment()),
        padding=Spacing.MD,
        background=Colors.SURFACE,
        border=f"1px solid {Colors.BORDER}",
        border_radius=Radius.LG,
        width="100%",
    )


def _tab_resumen() -> rx.Component:
    return rx.vstack(
        rx.grid(
            _resumen_card(
                "Cobertura",
                ContratoPlazasState.plazas_ocupadas_contrato_actual.to(str)
                + "/"
                + ContratoPlazasState.total_plazas_contrato_actual.to(str)
                + " plazas",
                detalle=ContratoPlazasState.descripcion_metrica_ocupadas,
            ),
            _resumen_card(
                "Sedes activas",
                ContratoPlazasState.total_sedes_contrato_actual.to(str) + " sedes",
                detalle=rx.cond(
                    ContratoPlazasState.plazas_sin_sede_contrato_actual > 0,
                    ContratoPlazasState.plazas_sin_sede_contrato_actual.to(str)
                    + " sin sede asignada",
                    "Todas las plazas tienen sede",
                ),
            ),
            _resumen_card(
                "Categorías",
                ContratoPlazasState.total_categorias_detalle_contrato.to(str) + " categorías",
                detalle="Configuradas en el contrato",
            ),
            _resumen_card(
                "Vigencia",
                ContratoPlazasState.vigencia_contrato_actual,
                extra=rx.box(
                    rx.cond(
                        ContratoPlazasState.estatus_contrato_actual != "",
                        estatus_badge(ContratoPlazasState.estatus_contrato_actual),
                        rx.fragment(),
                    ),
                    margin_top=Spacing.SM,
                ),
            ),
            columns=rx.breakpoints(initial="1", md="2"),
            spacing="4",
            width="100%",
        ),
        rx.box(
            _section_label("Costo mensual"),
            rx.flex(
                rx.text(
                    "Presupuestado",
                    font_size=Typography.SIZE_SM,
                    color=Colors.TEXT_SECONDARY,
                ),
                rx.text(
                    ContratoPlazasState.costo_presupuestado_contrato_actual_fmt,
                    font_size=Typography.SIZE_SM,
                    font_weight=Typography.WEIGHT_MEDIUM,
                    color=Colors.TEXT_PRIMARY,
                    font_variant_numeric="tabular-nums",
                ),
                justify="between",
                align="center",
                width="100%",
                margin_top=Spacing.XS,
            ),
            rx.cond(
                ContratoPlazasState.mostrar_costo_actual_contrato,
                rx.flex(
                    rx.text(
                        "Actual",
                        font_size=Typography.SIZE_SM,
                        color=Colors.TEXT_SECONDARY,
                    ),
                    rx.text(
                        ContratoPlazasState.costo_actual_contrato_actual_fmt,
                        font_size=Typography.SIZE_SM,
                        color=Colors.TEXT_SECONDARY,
                        font_variant_numeric="tabular-nums",
                    ),
                    justify="between",
                    align="center",
                    width="100%",
                    margin_top=Spacing.XS,
                ),
                rx.fragment(),
            ),
            padding=Spacing.MD,
            background=Colors.SURFACE,
            border=f"1px solid {Colors.BORDER}",
            border_radius=Radius.LG,
            width="100%",
        ),
        rx.box(
            _section_label("Objeto del contrato"),
            rx.text(
                ContratoPlazasState.descripcion_contrato_actual,
                font_size=Typography.SIZE_SM,
                color=Colors.TEXT_PRIMARY,
                margin_top=Spacing.XS,
            ),
            padding=Spacing.MD,
            background=Colors.SURFACE,
            border=f"1px solid {Colors.BORDER}",
            border_radius=Radius.LG,
            width="100%",
        ),
        spacing="4",
        width="100%",
    )


def tabla_plazas_contrato_actual() -> rx.Component:
    return rx.match(
        ContratoPlazasState.tab_activa,
        (
            "categorias",
            _tab_categorias(),
        ),
        (
            "resumen",
            _tab_resumen(),
        ),
        rx.vstack(
            _toolbar_plazas(),
            _barra_acciones_masivas(),
            _tabla_plazas(),
            spacing="4",
            width="100%",
        ),
    )


def _metric_card_skeleton() -> rx.Component:
    """Placeholder de una tarjeta de métrica mientras carga."""
    return rx.box(
        rx.vstack(
            rx.skeleton(
                rx.box(height="12px", width="60%"),
                loading=True,
            ),
            rx.skeleton(
                rx.box(height="28px", width="40%"),
                loading=True,
            ),
            rx.skeleton(
                rx.box(height="10px", width="50%"),
                loading=True,
            ),
            spacing="2",
            align="center",
            width="100%",
        ),
        padding=Spacing.MD,
        border=f"1px solid {Colors.BORDER}",
        border_radius=Radius.LG,
        background=Colors.SURFACE,
        width="100%",
    )


def _contrato_plazas_skeleton() -> rx.Component:
    """Skeleton de la vista inicial (métricas + tabs + tabla)."""
    return rx.vstack(
        metric_card_grid(
            _metric_card_skeleton(),
            _metric_card_skeleton(),
            _metric_card_skeleton(),
            _metric_card_skeleton(),
        ),
        rx.skeleton(
            rx.box(height="40px", width="340px", border_radius=Radius.MD),
            loading=True,
        ),
        rx.box(
            skeleton_tabla(PLAZAS_TABLE_HEADERS, filas=8),
            border=f"1px solid {Colors.BORDER}",
            border_radius=Radius.LG,
            background=Colors.SURFACE,
            overflow="hidden",
            width="100%",
        ),
        spacing="4",
        width="100%",
    )


def contenido_contrato_plazas() -> rx.Component:
    return rx.cond(
        ContratoPlazasState.loading,
        _contrato_plazas_skeleton(),
        rx.vstack(
            _callout_sin_sede(),
            metricas_contrato_plazas(),
            _tabs_contrato_plazas(),
            tabla_plazas_contrato_actual(),
            spacing="4",
            width="100%",
        ),
    )
