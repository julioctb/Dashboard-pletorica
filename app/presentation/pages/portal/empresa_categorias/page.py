"""Página portal para el catálogo de puestos de la empresa."""

import reflex as rx

from app.presentation.components.ui import (boton_cancelar, boton_guardar,
                                            empty_state_card, filtros_inline,
                                            form_input, metric_card,
                                            metric_card_grid, tabla_cta_button,
                                            table_shell)
from app.presentation.layouts.backoffice import (page_header, page_layout,
                                                 page_toolbar)
from app.presentation.theme import Colors, Radius, Spacing, Typography

from .modals import modal_categoria_catalogo
from .state import FILTRO_TODOS, EmpresaCategoriasState

GRUPO_HEADERS = [
    {"nombre": "Categoría", "ancho": "200px", "header_align": "left"},
    {"nombre": "Salario base", "ancho": "130px", "header_align": "right"},
    {"nombre": "En contratos", "ancho": "110px"},
    {"nombre": "Estatus", "ancho": "100px"},
    {"nombre": "", "ancho": "100px"},
]


def _metricas() -> rx.Component:
    props = {
        "icono": None,
        "show_icon": False,
        "align": "center",
    }
    return metric_card_grid(
        metric_card(
            titulo="Tipos de servicio",
            valor=EmpresaCategoriasState.total_tipos,
            value_color=Colors.TEXT_PRIMARY,
            **props,
        ),
        metric_card(
            titulo="Categorías activas",
            valor=EmpresaCategoriasState.total_activas,
            value_color=Colors.SUCCESS,
            descripcion="En uso en contratos",
            **props,
        ),
        metric_card(
            titulo="Inactivas",
            valor=EmpresaCategoriasState.total_inactivas,
            value_color=Colors.TEXT_SECONDARY,
            **props,
        ),
        initial_columns="1",
        sm_columns="2",
        md_columns="3",
    )


def _toolbar() -> rx.Component:
    return page_toolbar(
        search_value=EmpresaCategoriasState.busqueda_categoria,
        search_placeholder="Buscar por nombre o clave...",
        on_search_change=EmpresaCategoriasState.set_busqueda_categoria,
        on_search_clear=EmpresaCategoriasState.limpiar_busqueda_categoria,
        show_view_toggle=False,
        filters=filtros_inline(
            rx.select.root(
                rx.select.trigger(placeholder="Estatus: Todos"),
                rx.select.content(
                    rx.select.item("Todos", value=FILTRO_TODOS),
                    rx.select.item("Activas", value="ACTIVO"),
                    rx.select.item("Inactivas", value="INACTIVO"),
                ),
                value=EmpresaCategoriasState.filtro_estatus_categoria,
                on_change=EmpresaCategoriasState.set_filtro_estatus_categoria,
                size="2",
            ),
        ),
        search_min_width="180px",
        search_max_width=None,
        search_flex="1 1 260px",
    )


def _fila_categoria(item: dict) -> rx.Component:
    return rx.table.row(
        rx.table.cell(
            rx.box(
                rx.text(
                    item["nombre_display"],
                    font_weight=Typography.WEIGHT_MEDIUM,
                    color=Colors.TEXT_PRIMARY,
                    font_size=Typography.SIZE_SM,
                    text_transform="uppercase",
                ),
                rx.text(
                    item["clave_display"],
                    font_size=Typography.SIZE_XS,
                    color=Colors.TEXT_MUTED,
                    font_family="monospace",
                ),
                text_align="left",
            ),
            text_align="left",
        ),
        rx.table.cell(
            rx.text(
                item["salario_base_fmt"],
                font_weight=Typography.WEIGHT_MEDIUM,
                color=Colors.TEXT_PRIMARY,
                font_variant_numeric="tabular-nums",
                font_size=Typography.SIZE_SM,
                width="100%",
                text_align="right",
            ),
            text_align="right",
        ),
        rx.table.cell(
            rx.cond(
                item["tiene_contratos"],
                rx.text(
                    item["contratos_label"],
                    font_size=Typography.SIZE_SM,
                    color=Colors.TEXT_SECONDARY,
                ),
                rx.text(
                    "Sin uso",
                    font_size=Typography.SIZE_SM,
                    color=Colors.TEXT_MUTED,
                ),
            ),
            text_align="center",
        ),
        rx.table.cell(
            rx.center(
                rx.cond(
                    item["es_activa"],
                    rx.badge("Activa", color_scheme="green", size="1", variant="soft"),
                    rx.badge("Inactiva", color_scheme="gray", size="1", variant="soft"),
                ),
                width="100%",
            ),
            text_align="center",
        ),
        rx.table.cell(
            rx.center(
                rx.cond(
                    item["es_activa"],
                    tabla_cta_button(
                        text="Editar",
                        on_click=EmpresaCategoriasState.editar_categoria_puesto(
                            item["id"]
                        ),
                        color_scheme=Colors.NEUTRAL_SCHEME,
                        size="1",
                        variant="outline",
                    ),
                    tabla_cta_button(
                        text="Reactivar",
                        on_click=EmpresaCategoriasState.reactivar_categoria_puesto(
                            item["id"]
                        ),
                        color_scheme="green",
                        size="1",
                        variant="outline",
                    ),
                ),
                width="100%",
            ),
            text_align="center",
        ),
        align="center",
    )


def _empty_group(tipo: dict) -> rx.Component:
    return empty_state_card(
        title="No hay categorías en este tipo de servicio",
        description="Agregue la primera categoría para empezar a usar este grupo en contratos.",
        icon="briefcase",
        action_button=rx.button(
            rx.icon("plus", size=14),
            "Agregar categoría",
            on_click=EmpresaCategoriasState.abrir_modal_categoria_en_tipo(tipo["id"]),
            color_scheme=Colors.PORTAL_ACCENT_SCHEME,
            variant="outline",
            size="2",
        ),
    )


def _tipo_servicio_group(tipo: dict) -> rx.Component:
    return rx.vstack(
        rx.flex(
            rx.flex(
                rx.text(
                    tipo["nombre_display"],
                    font_size=Typography.SIZE_SM,
                    font_weight=Typography.WEIGHT_MEDIUM,
                    color=Colors.TEXT_PRIMARY,
                ),
                rx.text(
                    tipo["total_categorias_label"],
                    font_size=Typography.SIZE_XS,
                    color=Colors.TEXT_MUTED,
                ),
                align="center",
                gap=Spacing.SM,
            ),
            rx.button(
                rx.icon("plus", size=14),
                "Agregar categoría",
                on_click=EmpresaCategoriasState.abrir_modal_categoria_en_tipo(
                    tipo["id"]
                ),
                color_scheme=Colors.PORTAL_ACCENT_SCHEME,
                variant="soft",
                size="2",
                white_space="nowrap",
                flex_shrink="0",
            ),
            width="100%",
            justify="between",
            align="center",
            wrap="wrap",
            gap=Spacing.SM,
            padding_y=Spacing.SM,
        ),
        rx.box(
            table_shell(
                loading=EmpresaCategoriasState.loading,
                headers=GRUPO_HEADERS,
                rows=tipo["categorias"].to(list[dict]),
                row_renderer=_fila_categoria,
                has_rows=tipo["tiene_categorias"],
                empty_component=_empty_group(tipo),
                table_size="1",
                loading_rows=3,
            ),
            width="100%",
            overflow_x="auto",
            background=Colors.SURFACE,
            border=f"1px solid {Colors.BORDER}",
            border_radius=Radius.LG,
        ),
        width="100%",
        spacing="2",
    )


def _empty_state_principal() -> rx.Component:
    return empty_state_card(
        title="No hay categorías configuradas",
        description="Empiece creando un tipo de servicio y luego agregue sus categorías de puesto.",
        icon="briefcase",
    )


def _empty_state_filtros() -> rx.Component:
    return empty_state_card(
        title="No se encontraron categorías",
        description="Pruebe con otra búsqueda o cambie el filtro de estatus.",
        icon="search",
    )


def _crear_tipo_inline() -> rx.Component:
    return rx.cond(
        EmpresaCategoriasState.creando_tipo_servicio,
        rx.box(
            rx.flex(
                rx.box(
                    form_input(
                        label="Nuevo tipo de servicio",
                        placeholder="Ej: Seguridad",
                        value=EmpresaCategoriasState.form_nombre_tipo,
                        on_change=EmpresaCategoriasState.set_form_nombre_tipo,
                        on_key_down=EmpresaCategoriasState.handle_key_down_crear_tipo,
                        error=EmpresaCategoriasState.error_form_nombre_tipo,
                        hint="Presione Enter para crear más rápido",
                        label_variant="portal",
                        style_variant="portal",
                        auto_focus=True,
                    ),
                    flex="1 1 280px",
                    min_width="220px",
                ),
                rx.flex(
                    boton_guardar(
                        texto="Crear",
                        texto_guardando="Creando...",
                        on_click=EmpresaCategoriasState.crear_tipo_servicio,
                        saving=EmpresaCategoriasState.saving,
                        disabled=EmpresaCategoriasState.form_nombre_tipo == "",
                        size="2",
                        color_scheme=Colors.PORTAL_ACCENT_SCHEME,
                    ),
                    boton_cancelar(
                        texto="Cancelar",
                        on_click=EmpresaCategoriasState.cancelar_crear_tipo,
                        disabled=EmpresaCategoriasState.saving,
                        size="2",
                    ),
                    align="center",
                    gap=Spacing.SM,
                    wrap="wrap",
                    justify="end",
                    flex_shrink="0",
                ),
                width="100%",
                align="end",
                gap=Spacing.SM,
                wrap="wrap",
            ),
            padding=Spacing.MD,
            border=f"1px dashed {Colors.BORDER_STRONG}",
            border_radius=Radius.LG,
            background=Colors.SURFACE,
            width="100%",
        ),
        rx.button(
            rx.icon("plus", size=16),
            "Agregar tipo de servicio",
            on_click=EmpresaCategoriasState.iniciar_crear_tipo,
            color_scheme=Colors.PORTAL_ACCENT_SCHEME,
            variant="surface",
            size="3",
            width="100%",
            justify="center",
            gap=Spacing.SM,
            border=f"1px dashed {Colors.BORDER_STRONG}",
            background=Colors.PORTAL_PRIMARY_LIGHTER,
            _hover={
                "background": Colors.PORTAL_PRIMARY_LIGHT,
                "border_color": Colors.PORTAL_PRIMARY,
            },
        ),
    )


def empresa_categorias_page() -> rx.Component:
    return rx.box(
        page_layout(
            header=page_header(
                titulo="Catálogo de servicios",
                subtitulo="Categorías de personal por tipo de servicio",
                icono="briefcase",
                color_icono=Colors.PORTAL_ACCENT_SCHEME,
            ),
            toolbar=_toolbar(),
            content=rx.vstack(
                _metricas(),
                rx.cond(
                    EmpresaCategoriasState.mostrar_empty_state_principal,
                    _empty_state_principal(),
                    rx.cond(
                        EmpresaCategoriasState.mostrar_empty_state_filtros,
                        _empty_state_filtros(),
                        rx.vstack(
                            rx.foreach(
                                EmpresaCategoriasState.tipos_servicio_con_categorias,
                                _tipo_servicio_group,
                            ),
                            width="100%",
                            spacing="4",
                        ),
                    ),
                ),
                _crear_tipo_inline(),
                width="100%",
                spacing="4",
            ),
        ),
        modal_categoria_catalogo(),
        width="100%",
        min_height="100vh",
        on_mount=EmpresaCategoriasState.on_mount_empresa_categorias,
    )
