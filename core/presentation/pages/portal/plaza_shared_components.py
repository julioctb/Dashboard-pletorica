"""Componentes reutilizables para la gestion de plazas en portal."""

import reflex as rx

from core.core.enums import EstatusPlaza
from core.presentation.components.ui import (
    empty_state_card,
    input_busqueda,
    select_items_from_options,
    table_cell_actions,
    table_cell_badge,
    table_cell_text_sm,
    table_pagination,
    table_shell,
    table_text_sm,
)
from core.presentation.theme import Colors, Radius, Spacing, StatusColors, Typography


PLAZA_TABLE_HEADERS = [
    {"nombre": "", "ancho": "36px", "header_align": "center"},
    {"nombre": "#", "ancho": "60px", "header_align": "left"},
    {"nombre": "Categoria", "ancho": "22%", "header_align": "left"},
    {"nombre": "Sede", "ancho": "20%", "header_align": "center"},
    {"nombre": "Empleado asignado", "ancho": "24%", "header_align": "center"},
    {"nombre": "Estado", "ancho": "12%", "header_align": "center"},
    {"nombre": "Accion", "ancho": "14%", "header_align": "center"},
]

PLAZA_VACANTE_ROW_BG = Colors.WARNING_LIGHT


def _badge_resumen_contrato(texto, color_scheme: str) -> rx.Component:
    return rx.badge(
        texto,
        color_scheme=color_scheme,
        variant="soft",
        size="1",
    )


def _badge_estado_plaza(estatus) -> rx.Component:
    return rx.match(
        estatus,
        (
            EstatusPlaza.OCUPADA.value,
            rx.badge("Ocupada", color_scheme=StatusColors.OCUPADA_SCHEME, variant="soft", size="1"),
        ),
        (
            EstatusPlaza.VACANTE.value,
            rx.badge("Vacante", color_scheme=StatusColors.VACANTE_SCHEME, variant="soft", size="1"),
        ),
        (
            EstatusPlaza.SUSPENDIDA.value,
            rx.badge("Suspendida", color_scheme=StatusColors.SUSPENDIDA_SCHEME, variant="soft", size="1"),
        ),
        rx.badge("Sin estatus", color_scheme=Colors.NEUTRAL_SCHEME, variant="soft", size="1"),
    )


def _borde_izquierdo_plaza(estatus) -> rx.Var | str:
    return rx.match(
        estatus,
        (
            EstatusPlaza.OCUPADA.value,
            f"3px solid {Colors.SUCCESS}",
        ),
        (
            EstatusPlaza.VACANTE.value,
            f"3px solid {Colors.INFO}",
        ),
        (
            EstatusPlaza.SUSPENDIDA.value,
            f"3px solid {Colors.WARNING}",
        ),
        f"3px solid {Colors.BORDER_STRONG}",
    )


def _accion_plaza(plaza: dict, state_cls) -> rx.Component:
    return rx.select.root(
        rx.select.trigger(
            placeholder=plaza["acciones_placeholder"],
            width="160px",
        ),
        rx.select.content(
            select_items_from_options(plaza["acciones_disponibles"].to(list[dict])),
        ),
        value="",
        on_change=lambda value: state_cls.ejecutar_accion_plaza(plaza, value),
        size="1",
    )


def _celda_empleado_plaza(plaza: dict) -> rx.Component:
    nombre = plaza.get("empleado_nombre", "")
    empleado_uuid = plaza.get("empleado_uuid", "")
    return rx.table.cell(
        rx.cond(
            nombre != "",
            rx.cond(
                empleado_uuid != "",
                rx.link(
                    nombre,
                    href="/portal/empleados/" + empleado_uuid.to(str),
                    font_weight=Typography.WEIGHT_MEDIUM,
                    font_size=Typography.SIZE_SM,
                    color=Colors.TEXT_PRIMARY,
                    text_decoration="none",
                    _hover={
                        "color": Colors.PORTAL_PRIMARY_TEXT,
                        "text_decoration": "underline",
                    },
                ),
                table_text_sm(
                    nombre,
                    weight=Typography.WEIGHT_MEDIUM,
                ),
            ),
            table_text_sm("—", tone="muted"),
        ),
    )


def fila_plaza(plaza: dict, contrato_id, state_cls) -> rx.Component:
    es_vacante = plaza.get("estatus", "") == EstatusPlaza.VACANTE.value
    return rx.table.row(
        rx.table.cell(
            rx.center(
                rx.checkbox(
                    checked=plaza.get("seleccionada", False),
                    on_change=lambda checked: state_cls.toggle_plaza_seleccionada(
                        contrato_id,
                        plaza.get("id"),
                        checked,
                    ),
                    size="1",
                ),
                width="100%",
            ),
        ),
        rx.table.cell(
            table_text_sm(
                plaza.get("numero_plaza", ""),
                tone="muted",
                font_variant_numeric="tabular-nums",
            ),
        ),
        table_cell_text_sm(plaza.get("categoria_nombre", ""), tone="secondary", fallback="—"),
        rx.table.cell(
            table_text_sm(
                plaza.get("sede_display", ""),
                tone="secondary",
                fallback="SIN SEDE",
            ),
            text_align="center",
        ),
        _celda_empleado_plaza(plaza),
        table_cell_badge(
            _badge_estado_plaza(plaza.get("estatus", "")),
        ),
        table_cell_actions(
            _accion_plaza(plaza, state_cls),
        ),
        border_left=_borde_izquierdo_plaza(plaza.get("estatus", "")),
        background=rx.cond(
            plaza.get("seleccionada", False),
            Colors.PRIMARY_LIGHTER,
            rx.cond(es_vacante, PLAZA_VACANTE_ROW_BG, Colors.SURFACE),
        ),
        _hover={
            "background": rx.cond(
                plaza.get("seleccionada", False),
                Colors.PRIMARY_LIGHTER,
                rx.cond(es_vacante, PLAZA_VACANTE_ROW_BG, Colors.SURFACE_HOVER),
            ),
        },
    )


def _plaza_filtros_internos(state_cls) -> rx.Component:
    return rx.flex(
        rx.box(
            input_busqueda(
                value=state_cls.plaza_busqueda,
                on_change=state_cls.set_plaza_busqueda,
                on_clear=state_cls.limpiar_plaza_busqueda,
                placeholder="Buscar plaza...",
                toolbar_style=True,
                width="100%",
            ),
            flex="2 1 280px",
            min_width="220px",
        ),
        rx.box(
            rx.select.root(
                rx.select.trigger(
                    placeholder="Categoria",
                    width="100%",
                ),
                rx.select.content(
                    rx.select.item("Todas las categorias", value="all"),
                    select_items_from_options(state_cls.plaza_categorias_opciones),
                ),
                value=rx.cond(
                    state_cls.plaza_filtro_categoria == "all",
                    "",
                    state_cls.plaza_filtro_categoria,
                ),
                on_change=state_cls.set_plaza_filtro_categoria,
                size="2",
            ),
            flex="1 1 180px",
            min_width="180px",
        ),
        rx.box(
            rx.select.root(
                rx.select.trigger(
                    placeholder="Sede",
                    width="100%",
                ),
                rx.select.content(
                    rx.select.item("Todas las sedes", value="all"),
                    select_items_from_options(state_cls.plaza_sedes_opciones),
                ),
                value=rx.cond(
                    state_cls.plaza_filtro_sede == "all",
                    "",
                    state_cls.plaza_filtro_sede,
                ),
                on_change=state_cls.set_plaza_filtro_sede,
                size="2",
            ),
            flex="1 1 180px",
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
                    rx.select.item("Ocupada", value=EstatusPlaza.OCUPADA.value),
                    rx.select.item("Vacante", value=EstatusPlaza.VACANTE.value),
                    rx.select.item("Suspendida", value=EstatusPlaza.SUSPENDIDA.value),
                ),
                value=rx.cond(
                    state_cls.plaza_filtro_estado == "all",
                    "",
                    state_cls.plaza_filtro_estado,
                ),
                on_change=state_cls.set_plaza_filtro_estado,
                size="2",
            ),
            flex="1 1 180px",
            min_width="180px",
        ),
        width="100%",
        align="center",
        wrap="wrap",
        gap=Spacing.SM,
        padding_x=Spacing.MD,
        padding_y=Spacing.MD,
        background=Colors.SECONDARY_LIGHT,
        border_bottom=f"1px solid {Colors.BORDER}",
    )


def _barra_acciones_masivas(bloque: dict, state_cls) -> rx.Component:
    return rx.cond(
        bloque.get("tiene_seleccion", False),
        rx.flex(
            table_text_sm(
                bloque.get("seleccion_label", ""),
                weight=Typography.WEIGHT_MEDIUM,
            ),
            rx.flex(
                rx.select.root(
                    rx.select.trigger(
                        placeholder="Asignar sede...",
                        width="180px",
                    ),
                    rx.select.content(
                        select_items_from_options(state_cls.opciones_sedes_plaza),
                    ),
                    value=bloque.get("sede_masiva_value", ""),
                    on_change=lambda value: state_cls.set_sede_masiva_contrato(
                        bloque.get("contrato_id"),
                        value,
                    ),
                    size="1",
                ),
                rx.button(
                    "Aplicar",
                    size="1",
                    variant="soft",
                    color_scheme=Colors.PORTAL_ACCENT_SCHEME,
                    on_click=state_cls.aplicar_sede_masiva_contrato(
                        bloque.get("contrato_id"),
                    ),
                ),
                rx.select.root(
                    rx.select.trigger(
                        placeholder="Cambiar categoria...",
                        width="220px",
                    ),
                    rx.select.content(
                        select_items_from_options(
                            bloque["opciones_categorias_masivas"].to(list[dict]),
                        ),
                    ),
                    value=bloque["categoria_masiva_value"],
                    on_change=lambda value: state_cls.set_categoria_masiva_contrato(
                        bloque["contrato_id"],
                        value,
                    ),
                    size="1",
                ),
                rx.button(
                    "Aplicar",
                    size="1",
                    variant="soft",
                    color_scheme=Colors.PORTAL_ACCENT_SCHEME,
                    on_click=state_cls.aplicar_categoria_masiva_contrato(
                        bloque["contrato_id"],
                    ),
                ),
                rx.button(
                    "Deseleccionar",
                    size="1",
                    variant="ghost",
                    on_click=state_cls.limpiar_seleccion_plazas(
                        bloque.get("contrato_id"),
                    ),
                ),
                wrap="wrap",
                justify="end",
                gap=Spacing.SM,
                flex="1",
            ),
            width="100%",
            justify="between",
            align="center",
            wrap="wrap",
            gap=Spacing.SM,
            padding_x=Spacing.MD,
            padding_y=Spacing.SM,
            background=Colors.PRIMARY_LIGHTER,
            border_radius=Radius.MD,
        ),
        rx.fragment(),
    )


def resumen_contrato_plaza(state_cls, bloque: dict) -> rx.Component:
    return rx.flex(
        rx.flex(
            rx.flex(
                table_text_sm(
                    bloque.get("contrato_codigo", "Sin contrato"),
                    weight=Typography.WEIGHT_MEDIUM,
                    tone="primary",
                ),
                table_text_sm(
                    bloque.get("tipo_servicio_nombre", ""),
                    tone="muted",
                ),
                direction="column",
                gap=Spacing.XS,
                min_width="0",
            ),
        ),
        rx.flex(
            _badge_resumen_contrato(
                f"{bloque.get('plazas_ocupadas', 0)} ocupadas",
                StatusColors.OCUPADA_SCHEME,
            ),
            _badge_resumen_contrato(
                f"{bloque.get('plazas_vacantes', 0)} vacantes",
                StatusColors.VACANTE_SCHEME,
            ),
            rx.cond(
                bloque.get("mostrar_badge_suspendidas", False),
                _badge_resumen_contrato(
                    f"{bloque.get('plazas_suspendidas', 0)} suspendidas",
                    Colors.NEUTRAL_SCHEME,
                ),
                rx.fragment(),
            ),
            table_text_sm(
                bloque.get("resumen_plazas", ""),
                tone="muted",
            ),
            wrap="wrap",
            justify="end",
            gap=Spacing.SM,
            align="center",
        ),
        padding_x=Spacing.MD,
        padding_y=Spacing.MD,
        width="100%",
        justify="between",
        align="center",
        wrap="wrap",
        gap=Spacing.SM,
        background=Colors.SURFACE,
        border=f"1px solid {Colors.BORDER}",
        border_radius=Radius.LG,
    )


def _table_headers_plazas(bloque: dict, state_cls) -> list[rx.Component]:
    return [
        rx.table.column_header_cell(
            rx.center(
                rx.checkbox(
                    checked=bloque.get("seleccion_todas_visibles", False),
                    on_change=lambda checked: state_cls.seleccionar_todas_plazas_visibles(
                        bloque.get("contrato_id"),
                        checked,
                    ),
                    size="1",
                ),
                width="100%",
            ),
            width="36px",
            text_align="center",
        ),
        *[
            rx.table.column_header_cell(
                rx.text(
                    col["nombre"],
                    font_size=Typography.SIZE_XS,
                    font_weight=Typography.WEIGHT_MEDIUM,
                    color=Colors.TEXT_SECONDARY,
                    text_transform="uppercase",
                    letter_spacing="0.04em",
                ),
                width=col["ancho"],
                text_align=col.get("header_align", "left"),
            )
            for col in PLAZA_TABLE_HEADERS[1:]
        ],
    ]


def _tabla_contrato_plaza(state_cls, bloque: dict) -> rx.Component:
    return rx.vstack(
        _plaza_filtros_internos(state_cls),
        rx.box(
            _barra_acciones_masivas(bloque, state_cls),
            padding_x=Spacing.MD,
            padding_top=Spacing.MD,
            width="100%",
        ),
        rx.box(
            table_shell(
                loading=False,
                headers=PLAZA_TABLE_HEADERS,
                header_cells=_table_headers_plazas(bloque, state_cls),
                rows=state_cls.plazas_pagina_actual,
                row_renderer=lambda plaza: fila_plaza(plaza, bloque.get("contrato_id"), state_cls),
                has_rows=state_cls.plaza_total_filtradas > 0,
                empty_component=empty_state_card(
                    title="Sin plazas",
                    description="No hay plazas que coincidan con los filtros aplicados.",
                    icon="layout-grid",
                ),
                footer_component=rx.flex(
                    rx.text(
                        state_cls.resumen_pagina_contrato_actual,
                        font_size=Typography.SIZE_XS,
                        color=Colors.TEXT_MUTED,
                    ),
                    rx.cond(
                        state_cls.total_paginas_plaza_actual > 1,
                        table_pagination(
                            current_page=state_cls.pagina_plaza_actual,
                            total_pages=state_cls.total_paginas_plaza_actual,
                            page_numbers=state_cls.page_numbers_plaza_actual,
                            on_page_change=lambda page: state_cls.ir_a_pagina_plaza_contrato(
                                bloque.get("contrato_id"),
                                page,
                            ),
                            on_previous=state_cls.pagina_anterior_plaza_contrato(
                                bloque.get("contrato_id"),
                            ),
                            on_next=state_cls.pagina_siguiente_plaza_contrato(
                                bloque.get("contrato_id"),
                            ),
                            color_scheme=Colors.PORTAL_ACCENT_SCHEME,
                        ),
                        rx.fragment(),
                    ),
                    width="100%",
                    justify="between",
                    align="center",
                    wrap="wrap",
                    gap=Spacing.SM,
                ),
                table_size="1",
            ),
            padding=Spacing.MD,
            width="100%",
        ),
        spacing="2",
        width="100%",
    )


def tabla_plazas_contrato(state_cls) -> rx.Component:
    return rx.cond(
        state_cls.loading,
        rx.center(
            rx.spinner(size="3"),
            width="100%",
            padding_y=Spacing.XL,
        ),
        rx.cond(
            state_cls.tiene_contrato_plaza_contexto,
            rx.vstack(
                resumen_contrato_plaza(state_cls, state_cls.contrato_plaza_contexto),
                rx.cond(
                    state_cls.cargando_plazas_contrato_actual,
                    rx.box(
                        rx.center(
                            rx.spinner(size="2"),
                            width="100%",
                            padding_y=Spacing.XL,
                        ),
                        border=f"1px solid {Colors.BORDER}",
                        border_radius=Radius.LG,
                        background=Colors.SURFACE,
                        width="100%",
                    ),
                    _tabla_contrato_plaza(state_cls, state_cls.contrato_plaza_contexto),
                ),
                spacing="3",
                width="100%",
            ),
            empty_state_card(
                title="No hay plazas disponibles",
                description="Este contrato todavía no tiene plazas visibles para operar en portal.",
                icon="briefcase",
            ),
        ),
    )
