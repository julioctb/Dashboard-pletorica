"""Componentes de la página de plazas por contrato."""

from __future__ import annotations

import reflex as rx

from app.presentation.components.ui import (
    empty_state_card,
    estatus_badge,
    feedback_callout,
    filtros_inline,
    metric_card,
    metric_card_grid,
    segmented_tab_trigger,
    segmented_tabs,
    select_items_from_options,
    skeleton_tabla,
    tabla_cta_button,
    table_pagination,
    table_shell,
)
from app.presentation.layouts.backoffice import page_header, page_toolbar
from app.presentation.theme import Colors, Radius, Spacing, Typography

from .state import ContratoPlazasState


PLAZAS_TABLE_HEADERS = [
    {"nombre": "", "ancho": "40px", "header_align": "center"},
    {"nombre": "#", "ancho": "50px", "header_align": "left"},
    {"nombre": "Categoría", "ancho": "180px", "header_align": "left"},
    {"nombre": "Sede", "ancho": "170px", "header_align": "center"},
    {"nombre": "Empleado asignado", "ancho": "190px", "header_align": "center"},
    {"nombre": "Configuración", "ancho": "150px", "header_align": "center"},
    {"nombre": "Ocupación", "ancho": "130px", "header_align": "center"},
    {"nombre": "", "ancho": "190px", "header_align": "center"},
]

def _header_cell_text(texto) -> rx.Component:
    return rx.text(
        texto,
        font_size=Typography.SIZE_XS,
        font_weight=Typography.WEIGHT_SEMIBOLD,
        color=Colors.TEXT_MUTED,
        text_transform="uppercase",
        letter_spacing=Typography.LETTER_SPACING_SECTION_LABEL,
    )


def _table_header_cell(texto, ancho: str, align: str = "left") -> rx.Component:
    return rx.table.column_header_cell(
        _header_cell_text(texto),
        width=ancho,
        text_align=align,
    )


def _build_table_headers(columns: list[dict]) -> list[rx.Component]:
    return [
        _table_header_cell(
            col["nombre"],
            col["ancho"],
            col.get("header_align", "left"),
        )
        for col in columns
    ]


def _surface_panel(content: rx.Component) -> rx.Component:
    return rx.box(
        content,
        border=f"1px solid {Colors.BORDER}",
        border_radius=Radius.LG,
        background=Colors.SURFACE,
        overflow="hidden",
        width="100%",
    )


def _boton_agregar_categoria() -> rx.Component:
    return rx.button(
        rx.icon("plus", size=14),
        "Agregar categoría",
        size="2",
        variant="outline",
        color_scheme=Colors.PORTAL_ACCENT_SCHEME,
        on_click=ContratoPlazasState.abrir_modal_categoria,
        disabled=ContratoPlazasState.contrato_solo_consulta,
    )


def _header_plazas() -> rx.Component:
    """Header con breadcrumb inline — patrón Contratos › Código contrato."""
    return page_header(
        titulo="",
        icono="layout-grid",
        titulo_compuesto=rx.hstack(
            rx.link(
                "Contratos",
                href="/portal/contratos",
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


def _banner_incidencias() -> rx.Component:
    """Banner agregado con todas las incidencias de configuración pendientes."""
    return rx.cond(
        ContratoPlazasState.mostrar_banner_incidencias,
        feedback_callout(
            content=rx.flex(
                rx.text(
                    ContratoPlazasState.mensaje_banner_incidencias,
                    font_size=Typography.SIZE_SM,
                    color=Colors.TEXT_PRIMARY,
                ),
                rx.button(
                    rx.icon("map-pin", size=14),
                    "Revisar pendientes",
                    size="1",
                    variant="outline",
                    color_scheme=Colors.PORTAL_ACCENT_SCHEME,
                    on_click=ContratoPlazasState.set_tab_activa("pendientes"),
                ),
                gap=Spacing.SM,
                justify="between",
                align="center",
                wrap="wrap",
                width="100%",
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
            descripcion="Totales en el contrato",
        ),
        metric_card(
            titulo="Configuradas",
            valor=ContratoPlazasState.plazas_configuradas_contrato_actual,
            icono=None,
            color_scheme=Colors.NEUTRAL_SCHEME,
            show_icon=False,
            align="center",
            descripcion=ContratoPlazasState.descripcion_metrica_configuradas,
        ),
        metric_card(
            titulo="Pendientes",
            valor=ContratoPlazasState.plazas_pendientes_contrato_actual,
            icono=None,
            color_scheme=Colors.NEUTRAL_SCHEME,
            show_icon=False,
            align="center",
            value_color=rx.cond(
                ContratoPlazasState.plazas_pendientes_contrato_actual > 0,
                Colors.WARNING,
                Colors.TEXT_PRIMARY,
            ),
            descripcion=ContratoPlazasState.descripcion_metrica_pendientes,
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
            label="Pendientes",
            value="pendientes",
            active_background=Colors.PORTAL_PRIMARY,
            active_hover_background=Colors.PORTAL_PRIMARY_HOVER,
        ),
        value=ContratoPlazasState.tab_activa,
        on_change=ContratoPlazasState.set_tab_activa,
    )


def _toolbar_plazas() -> rx.Component:
    return page_toolbar(
        search_value=ContratoPlazasState.plaza_busqueda,
        search_placeholder="Buscar plaza, empleado o sede...",
        on_search_change=ContratoPlazasState.set_plaza_busqueda,
        on_search_clear=ContratoPlazasState.limpiar_plaza_busqueda,
        show_view_toggle=False,
        wrapped=False,
        compact=True,
        search_min_width="0px",
        search_max_width=None,
        search_flex="1 1 0px",
        filters=filtros_inline(
            rx.box(
                rx.select.root(
                    rx.select.trigger(
                        placeholder="Categoría",
                        width="100%",
                    ),
                    rx.select.content(
                        rx.select.item("Todas las categorías", value="all"),
                        select_items_from_options(
                            ContratoPlazasState.plaza_categorias_opciones
                        ),
                    ),
                    value=ContratoPlazasState.plaza_filtro_categoria,
                    on_change=ContratoPlazasState.set_plaza_filtro_categoria,
                    size="2",
                ),
                width="180px",
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
                        rx.select.item("Sin categoría", value="SIN_CATEGORIA"),
                        rx.select.item("Incompleta", value="CONFIGURACION_INCOMPLETA"),
                    ),
                    value=ContratoPlazasState.plaza_filtro_estado,
                    on_change=ContratoPlazasState.set_plaza_filtro_estado,
                    size="2",
                ),
                width="180px",
                min_width="180px",
            ),
        ),
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
                background=Colors.SURFACE,
                border=f"1px solid {Colors.BORDER}",
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
        *_build_table_headers(PLAZAS_TABLE_HEADERS[1:]),
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
                text="Acciones",
                on_click=rx.noop,
                color_scheme=Colors.NEUTRAL_SCHEME,
                size="1",
                variant="outline",
            ),
        ),
        rx.menu.content(
            rx.menu.item(
                rx.icon("eye", size=14),
                " Ver plaza",
                on_click=ContratoPlazasState.ver_plaza(plaza["id"]),
            ),
            rx.menu.item(
                rx.icon("user", size=14),
                " Ver empleado",
                on_click=ContratoPlazasState.accion_ver_empleado_plaza(plaza["id"]),
            ),
            rx.menu.separator(),
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
    """CTA por fila basado en cta_tipo (configuración u ocupación)."""
    return rx.match(
        plaza["cta_tipo"],
        (
            "menu_ocupada",
            _menu_acciones_ocupada(plaza),
        ),
        (
            "asignar_sede",
            tabla_cta_button(
                text="Asignar sede",
                on_click=ContratoPlazasState.accion_asignar_sede(plaza["id"]),
                color_scheme=Colors.WARNING_SCHEME,
                size="1",
                variant="outline",
            ),
        ),
        (
            "completar_config",
            tabla_cta_button(
                text="Completar configuración",
                on_click=ContratoPlazasState.accion_completar_configuracion(plaza["id"]),
                color_scheme=Colors.WARNING_SCHEME,
                size="1",
                variant="outline",
            ),
        ),
        (
            "ir_a_empleados",
            tabla_cta_button(
                text="Ir a empleados",
                on_click=ContratoPlazasState.accion_ir_a_empleados(plaza["id"]),
                color_scheme=Colors.PORTAL_ACCENT_SCHEME,
                size="1",
                variant="outline",
            ),
        ),
        tabla_cta_button(
            text="Consultar",
            on_click=ContratoPlazasState.ver_plaza(plaza["id"]),
            color_scheme=Colors.NEUTRAL_SCHEME,
            size="1",
            variant="outline",
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
            estatus_badge(plaza["configuracion_estado"]),
            text_align="center",
        ),
        rx.table.cell(
            estatus_badge(plaza["ocupacion_estado"]),
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
    return _surface_panel(
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
    )


_CATEGORIAS_SIMPLE_HEADERS = [
    {"nombre": "Categoría", "ancho": "200px", "header_align": "left"},
    {"nombre": "Mín", "ancho": "70px", "header_align": "center"},
    {"nombre": "Máx", "ancho": "70px", "header_align": "center"},
    {"nombre": "Configuradas", "ancho": "120px", "header_align": "center"},
    {"nombre": "Ocupadas", "ancho": "110px", "header_align": "center"},
    {"nombre": "Pendientes", "ancho": "110px", "header_align": "center"},
    {"nombre": "Estado", "ancho": "180px", "header_align": "center"},
    {"nombre": "", "ancho": "120px", "header_align": "center"},
]


def _headers_categorias_simple() -> list[rx.Component]:
    return _build_table_headers(_CATEGORIAS_SIMPLE_HEADERS)


def _categoria_simple_row(categoria: dict) -> rx.Component:
    celda_numero = lambda valor: rx.table.cell(
        rx.text(
            valor,
            font_size=Typography.SIZE_SM,
            color=Colors.TEXT_PRIMARY,
            font_variant_numeric="tabular-nums",
            text_align="center",
        ),
        text_align="center",
    )
    return rx.table.row(
        rx.table.cell(
            rx.text(
                categoria["nombre"],
                font_weight=Typography.WEIGHT_MEDIUM,
                color=Colors.TEXT_PRIMARY,
                font_size=Typography.SIZE_SM,
            ),
            text_align="left",
        ),
        celda_numero(categoria["minimo_texto"]),
        celda_numero(categoria["maximo_texto"]),
        celda_numero(categoria["configuradas_texto"]),
        celda_numero(categoria["ocupadas_texto"]),
        celda_numero(categoria["pendientes_texto"]),
        rx.table.cell(
            estatus_badge(categoria["estado"]),
            text_align="center",
        ),
        rx.table.cell(
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
            text_align="center",
        ),
    )


def _tab_categorias_simple() -> rx.Component:
    body = rx.foreach(
        ContratoPlazasState.categorias_resumen_simple,
        _categoria_simple_row,
    )
    return rx.vstack(
        rx.flex(
            rx.text(
                "Resumen operativo por categoría — sin métricas financieras.",
                font_size=Typography.SIZE_XS,
                color=Colors.TEXT_MUTED,
            ),
            rx.spacer(),
            _boton_agregar_categoria(),
            width="100%",
            align="center",
            gap=Spacing.SM,
            wrap="wrap",
        ),
        _surface_panel(
            table_shell(
                loading=ContratoPlazasState.loading,
                headers=[],
                header_cells=_headers_categorias_simple(),
                body_component=body,
                has_rows=ContratoPlazasState.tiene_categorias_resumen_simple,
                empty_component=empty_state_card(
                    title="No hay categorías configuradas",
                    description="Agregue la primera categoría para poder crear plazas del contrato.",
                    icon="tags",
                    action_button=_boton_agregar_categoria(),
                ),
                table_size="1",
            ),
        ),
        spacing="4",
        width="100%",
    )


_PENDIENTES_HEADERS = [
    {"nombre": "#", "ancho": "50px", "header_align": "left"},
    {"nombre": "Categoría", "ancho": "200px", "header_align": "left"},
    {"nombre": "Sede", "ancho": "180px", "header_align": "center"},
    {"nombre": "Configuración", "ancho": "180px", "header_align": "center"},
    {"nombre": "", "ancho": "200px", "header_align": "center"},
]


def _headers_pendientes() -> list[rx.Component]:
    return _build_table_headers(_PENDIENTES_HEADERS)


def _pendiente_row(plaza: dict) -> rx.Component:
    return rx.table.row(
        rx.table.cell(
            rx.text(
                plaza["numero_plaza_texto"],
                font_size=Typography.SIZE_SM,
                color=Colors.TEXT_MUTED,
                font_variant_numeric="tabular-nums",
            ),
            text_align="left",
        ),
        rx.table.cell(
            rx.text(
                plaza["categoria_nombre_ui"],
                font_weight=Typography.WEIGHT_MEDIUM,
                color=Colors.TEXT_PRIMARY,
                font_size=Typography.SIZE_SM,
            ),
            text_align="left",
        ),
        rx.table.cell(
            rx.cond(
                plaza["tiene_sede"],
                rx.text(
                    plaza["sede_display_tabla"],
                    font_size=Typography.SIZE_SM,
                    color=Colors.TEXT_SECONDARY,
                ),
                rx.text("—", font_size=Typography.SIZE_SM, color=Colors.TEXT_MUTED),
            ),
            text_align="center",
        ),
        rx.table.cell(
            estatus_badge(plaza["configuracion_estado"]),
            text_align="center",
        ),
        rx.table.cell(
            _acciones_plaza(plaza),
            text_align="center",
        ),
    )


def _tab_pendientes() -> rx.Component:
    return rx.vstack(
        _barra_acciones_masivas(),
        _surface_panel(
            table_shell(
                loading=ContratoPlazasState.loading,
                headers=[],
                header_cells=_headers_pendientes(),
                rows=ContratoPlazasState.pendientes_tabla_rows,
                row_renderer=_pendiente_row,
                has_rows=ContratoPlazasState.total_pendientes_tabla > 0,
                empty_component=empty_state_card(
                    title="No hay plazas pendientes",
                    description="Todas las plazas del contrato están listas para ocuparse.",
                    icon="badge-check",
                ),
                table_size="1",
            ),
        ),
        spacing="4",
        width="100%",
    )


def tabla_plazas_contrato_actual() -> rx.Component:
    return rx.match(
        ContratoPlazasState.tab_activa,
        (
            "categorias",
            _tab_categorias_simple(),
        ),
        (
            "pendientes",
            _tab_pendientes(),
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
        _surface_panel(
            skeleton_tabla(PLAZAS_TABLE_HEADERS, filas=8),
        ),
        spacing="4",
        width="100%",
    )


def contenido_contrato_plazas() -> rx.Component:
    return rx.cond(
        ContratoPlazasState.loading,
        _contrato_plazas_skeleton(),
        rx.vstack(
            _banner_incidencias(),
            metricas_contrato_plazas(),
            _tabs_contrato_plazas(),
            tabla_plazas_contrato_actual(),
            spacing="4",
            width="100%",
        ),
    )
