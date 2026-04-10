"""Componentes UI para la pagina de empleados en portal."""

import reflex as rx

from app.presentation.components.ui import (
    empty_state_card,
    employee_status_badge,
    filter_pill,
    input_busqueda,
    metric_card,
    metric_card_grid,
    select_items_from_options,
    tabla_cta_button,
    table_pagination,
    table_shell,
)
from app.presentation.pages.portal.plaza_shared_components import (
    PLAZA_TABLE_HEADERS,
    tabla_plazas_contrato as shared_tabla_plazas_contrato,
)
from app.presentation.theme import Colors, Radius, Spacing, StatusColors, Typography

from .state import MisEmpleadosState


def metricas_empleados() -> rx.Component:
    return metric_card_grid(
        metric_card(
            titulo="Plazas totales",
            valor=MisEmpleadosState.total_plazas,
            icono=None,
            color_scheme=Colors.NEUTRAL_SCHEME,
            show_icon=False,
            align="center",
            descripcion=MisEmpleadosState.total_contratos_label,
        ),
        metric_card(
            titulo="Ocupadas",
            valor=MisEmpleadosState.plazas_ocupadas,
            icono=None,
            color_scheme=Colors.PORTAL_ACCENT_SCHEME,
            show_icon=False,
            align="center",
            value_color=Colors.SUCCESS,
            descripcion=MisEmpleadosState.cobertura_label,
        ),
        metric_card(
            titulo="Vacantes",
            valor=MisEmpleadosState.plazas_vacantes,
            icono=None,
            color_scheme=Colors.WARNING_SCHEME,
            show_icon=False,
            align="center",
            value_color=Colors.WARNING,
        ),
        metric_card(
            titulo="Inactivos",
            valor=MisEmpleadosState.total_inactivos,
            icono=None,
            color_scheme=Colors.NEUTRAL_SCHEME,
            show_icon=False,
            align="center",
            descripcion="Sin plaza activa en portal",
        ),
        metric_card(
            titulo="Docs pendientes",
            valor=MisEmpleadosState.docs_pendientes,
            icono=None,
            color_scheme=StatusColors.BAJA_SCHEME,
            show_icon=False,
            align="center",
            value_color=Colors.ERROR,
            descripcion="Expedientes incompletos",
        ),
        md_columns="5",
    )


def _pills_empleados() -> rx.Component:
    return rx.flex(
        filter_pill(
            "Todos",
            MisEmpleadosState.total_empleados.to(str),
            MisEmpleadosState.filtrar_todos,
            MisEmpleadosState.filtro_es_todos,
        ),
        filter_pill(
            "Activos",
            MisEmpleadosState.total_activos.to(str),
            MisEmpleadosState.filtrar_activos,
            MisEmpleadosState.filtro_es_activos,
            Colors.SUCCESS,
        ),
        filter_pill(
            "Inactivos",
            MisEmpleadosState.total_inactivos.to(str),
            MisEmpleadosState.filtrar_inactivos,
            MisEmpleadosState.filtro_es_inactivos,
            Colors.TEXT_MUTED,
        ),
        gap=Spacing.SM,
        align="center",
    )


def filtro_contrato_empleados() -> rx.Component:
    return rx.flex(
        rx.box(
            input_busqueda(
                value=MisEmpleadosState.filtro_busqueda_emp,
                on_change=MisEmpleadosState.set_filtro_busqueda_emp,
                on_clear=MisEmpleadosState.limpiar_busqueda,
                placeholder="Buscar...",
                toolbar_style=True,
                width="100%",
            ),
            flex="1",
            min_width="180px",
        ),
        rx.select.root(
            rx.select.trigger(placeholder="Contrato"),
            rx.select.content(select_items_from_options(MisEmpleadosState.contratos_opciones)),
            value=MisEmpleadosState.filtro_contrato_id,
            on_change=MisEmpleadosState.set_filtro_contrato_id,
            size="2",
        ),
        rx.select.root(
            rx.select.trigger(placeholder="Sede"),
            rx.select.content(
                rx.select.item("Todas las sedes", value="all"),
                select_items_from_options(MisEmpleadosState.sedes_opciones),
            ),
            value=MisEmpleadosState.filtro_sede,
            on_change=MisEmpleadosState.set_filtro_sede,
            size="2",
        ),
        rx.select.root(
            rx.select.trigger(placeholder="Categoría"),
            rx.select.content(
                rx.select.item("Todas las categorías", value="all"),
                select_items_from_options(MisEmpleadosState.categorias_opciones),
            ),
            value=MisEmpleadosState.filtro_categoria,
            on_change=MisEmpleadosState.set_filtro_categoria,
            size="2",
        ),
        width="100%",
        align="center",
        gap=Spacing.SM,
    )


def filtros_estatus_empleados() -> rx.Component:
    return rx.flex(
        _pills_empleados(),
        width="100%",
        align="center",
        gap=Spacing.SM,
        wrap="wrap",
    )


def _celda_texto_centrada(
    valor,
    *,
    color: str = Colors.TEXT_SECONDARY,
    fallback: str = "—",
    font_variant_numeric: str | None = None,
) -> rx.Component:
    texto_props = {
        "font_size": Typography.SIZE_XS,
        "color": color,
    }
    if font_variant_numeric is not None:
        texto_props["font_variant_numeric"] = font_variant_numeric

    fallback_props = dict(texto_props)
    fallback_props["color"] = Colors.TEXT_MUTED

    return rx.table.cell(
        rx.cond(
            valor != "",
            rx.text(valor, **texto_props),
            rx.text(fallback, **fallback_props),
        ),
        text_align="center",
    )


def _docs_color_texto(tone) -> rx.Var | str:
    return rx.match(
        tone,
        ("success", Colors.SUCCESS),
        ("warning", Colors.WARNING),
        Colors.TEXT_MUTED,
    )


def _docs_color_barra(tone) -> rx.Var | str:
    return rx.match(
        tone,
        ("success", Colors.SUCCESS),
        ("warning", Colors.WARNING),
        Colors.BORDER,
    )


def _docs_cell(emp: dict) -> rx.Component:
    docs_tone = emp.get("docs_tone", "muted")
    return rx.table.cell(
        rx.center(
            rx.flex(
                rx.text(
                    emp.get("docs_resumen_ui", "0/0"),
                    font_size=Typography.SIZE_XS,
                    font_weight=Typography.WEIGHT_MEDIUM,
                    font_variant_numeric="tabular-nums",
                    color=_docs_color_texto(docs_tone),
                ),
                rx.box(
                    rx.box(
                        width=emp.get("docs_porcentaje_ui", "0%"),
                        height="100%",
                        border_radius=Radius.FULL,
                        background=_docs_color_barra(docs_tone),
                    ),
                    width=Spacing.XXL,
                    height=Spacing.XS,
                    background=Colors.SECONDARY_LIGHT,
                    border_radius=Radius.FULL,
                    overflow="hidden",
                ),
                align="center",
                justify="center",
                gap=Spacing.XS,
                width="100%",
                cursor="pointer",
                on_click=MisEmpleadosState.ver_ficha_empleado(emp),
            ),
            width="100%",
        ),
        text_align="center",
    )


def _render_nombre_cell(emp: dict) -> rx.Component:
    nombre = emp.get("nombre_completo_ui", "")
    curp = emp.get("curp_ui", "")
    uuid = emp.get("uuid", "")
    iniciales = emp.get("avatar_iniciales_ui", "?")
    estatus = emp.get("estatus_portal", "INACTIVO")
    return rx.table.cell(
        rx.flex(
            rx.center(
                rx.text(
                    iniciales,
                    font_size=Typography.SIZE_XS,
                    font_weight=Typography.WEIGHT_MEDIUM,
                    color=rx.cond(
                        estatus == "ACTIVO",
                        Colors.PORTAL_PRIMARY_TEXT,
                        Colors.TEXT_MUTED,
                    ),
                ),
                width="30px",
                height="30px",
                border_radius=Radius.FULL,
                background=rx.cond(
                    estatus == "ACTIVO",
                    Colors.PORTAL_PRIMARY_LIGHTER,
                    Colors.SECONDARY_LIGHT,
                ),
                flex_shrink="0",
            ),
            rx.flex(
                rx.cond(
                    uuid != "",
                    rx.link(
                        rx.cond(nombre != "", nombre, "Sin nombre"),
                        href="/portal/empleados/" + uuid.to(str),
                        font_weight=Typography.WEIGHT_MEDIUM,
                        color=Colors.TEXT_PRIMARY,
                        text_decoration="none",
                        white_space="nowrap",
                        overflow="hidden",
                        text_overflow="ellipsis",
                        _hover={
                            "color": Colors.PORTAL_PRIMARY_TEXT,
                            "text_decoration": "underline",
                        },
                    ),
                    rx.text(
                        rx.cond(nombre != "", nombre, "Sin nombre"),
                        font_weight=Typography.WEIGHT_MEDIUM,
                        color=Colors.TEXT_PRIMARY,
                        white_space="nowrap",
                        overflow="hidden",
                        text_overflow="ellipsis",
                    ),
                ),
                rx.text(
                    rx.cond(curp != "", curp, "—"),
                    font_size=Typography.SIZE_XS,
                    font_family="var(--font-mono)",
                    color=Colors.TEXT_MUTED,
                ),
                direction="column",
                min_width="0",
            ),
            align="center",
            gap=Spacing.SM,
        )
    )


def _accion_empleado(emp: dict) -> rx.Component:
    return rx.match(
        emp.get("estatus_portal", ""),
        (
            "INACTIVO",
            tabla_cta_button(
                "Completar datos",
                MisEmpleadosState.ver_ficha_empleado(emp),
                color_scheme=Colors.PORTAL_ACCENT_SCHEME,
            ),
        ),
        rx.fragment(),
    )


def fila_empleado(emp: dict) -> rx.Component:
    return rx.table.row(
        _render_nombre_cell(emp),
        _celda_texto_centrada(emp.get("contrato_codigo", ""), color=Colors.TEXT_SECONDARY, fallback="—"),
        _celda_texto_centrada(emp.get("categoria_nombre", ""), fallback="—"),
        _celda_texto_centrada(emp.get("sede_nombre_ui", ""), color=Colors.TEXT_PRIMARY, fallback="—"),
        _celda_texto_centrada(
            emp.get("telefono_ui", ""),
            color=Colors.TEXT_SECONDARY,
            font_variant_numeric="tabular-nums",
            fallback="—",
        ),
        _docs_cell(emp),
        rx.table.cell(
            rx.center(employee_status_badge(emp.get("estatus_portal", "")), width="100%"),
            text_align="center",
        ),
        rx.table.cell(rx.center(_accion_empleado(emp), width="100%"), text_align="center"),
        _hover={"background": Colors.SURFACE_HOVER},
    )


ENCABEZADOS_EMPLEADOS = [
    {"nombre": "Nombre", "ancho": "23%", "header_align": "left"},
    {"nombre": "Contrato", "ancho": "10%", "header_align": "center"},
    {"nombre": "Categoría", "ancho": "13%", "header_align": "center"},
    {"nombre": "Sede", "ancho": "13%", "header_align": "center"},
    {"nombre": "Teléfono", "ancho": "11%", "header_align": "center"},
    {"nombre": "Docs", "ancho": "7%", "header_align": "center"},
    {"nombre": "Estatus", "ancho": "9%", "header_align": "center"},
    {"nombre": "Acción", "ancho": "14%", "header_align": "center"},
]

ENCABEZADOS_PLAZAS = PLAZA_TABLE_HEADERS


def _table_headers_empleados() -> list[rx.Component]:
    return [
        rx.table.column_header_cell(
            rx.text(
                col["nombre"],
                font_size=Typography.SIZE_XS,
                font_weight=Typography.WEIGHT_MEDIUM,
                color=Colors.TEXT_SECONDARY,
                text_transform="uppercase",
                letter_spacing="0.04em",
            ),
            width=col.get("ancho", "auto"),
            text_align=col.get("header_align", "left"),
        )
        for col in ENCABEZADOS_EMPLEADOS
    ]


def tabla_empleados() -> rx.Component:
    return table_shell(
        loading=MisEmpleadosState.loading,
        headers=ENCABEZADOS_EMPLEADOS,
        header_cells=_table_headers_empleados(),
        rows=MisEmpleadosState.empleados_paginados,
        row_renderer=fila_empleado,
        has_rows=MisEmpleadosState.total_empleados_filtrados > 0,
        empty_component=empty_state_card(
            title="No hay empleados para este filtro",
            description="Ajuste la búsqueda, cambie el contrato o registre un nuevo empleado.",
            icon="users",
            action_button=rx.button(
                rx.icon("plus", size=16),
                "Nuevo empleado",
                on_click=MisEmpleadosState.abrir_modal_crear,
                color_scheme=Colors.PORTAL_ACCENT_SCHEME,
                variant="soft",
            ),
        ),
        total_caption=MisEmpleadosState.resumen_paginacion_empleados,
        footer_component=table_pagination(
            current_page=MisEmpleadosState.pagina_empleados_actual,
            total_pages=MisEmpleadosState.total_paginas_empleados,
            page_numbers=MisEmpleadosState.paginas_visibles_empleados,
            on_page_change=MisEmpleadosState.ir_a_pagina,
            on_previous=MisEmpleadosState.pagina_anterior,
            on_next=MisEmpleadosState.pagina_siguiente,
            color_scheme=Colors.PORTAL_ACCENT_SCHEME,
        ),
        loading_rows=5,
        table_size="1",
    )


def tabla_plazas_por_contrato() -> rx.Component:
    return shared_tabla_plazas_contrato(MisEmpleadosState)
