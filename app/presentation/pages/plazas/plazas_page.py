"""Página principal del módulo de plazas."""

import reflex as rx

from app.presentation.components.plazas.plazas_modals import (
    modal_asignar_empleado,
    modal_confirmar_cancelar,
    modal_crear_lote,
    modal_detalle_plaza,
    modal_plaza,
)
from app.presentation.components.ui import (
    breadcrumb_dynamic,
    identifier_badge,
    select_items_from_options,
    skeleton_tabla,
    status_badge_reactive,
    tabla_action_button,
    tabla_action_buttons,
    tabla_vacia,
    table_cell_actions,
    table_cell_badge,
    table_shell,
)
from app.presentation.layout import page_header, page_layout, page_toolbar
from app.presentation.pages.plazas.plazas_state import PlazasState
from app.presentation.theme import Colors, Radius, Shadows, Spacing, Typography


def _metric_card(
    titulo: str,
    valor,
    icono: str,
    color: str,
    fondo: str,
) -> rx.Component:
    return rx.card(
        rx.hstack(
            rx.center(
                rx.icon(icono, size=18, color=color),
                width="38px",
                height="38px",
                background=fondo,
                border_radius=Radius.MD,
            ),
            rx.vstack(
                rx.text(
                    titulo,
                    font_size=Typography.SIZE_XS,
                    color=Colors.TEXT_SECONDARY,
                ),
                rx.text(
                    valor,
                    font_size=Typography.SIZE_XL,
                    font_weight=Typography.WEIGHT_BOLD,
                    color=color,
                ),
                spacing="0",
                align_items="start",
            ),
            spacing="3",
            align="center",
        ),
        size="1",
        width="100%",
    )


def _portal_metric_card(label: str, value) -> rx.Component:
    return rx.vstack(
        rx.text(
            value,
            font_size=Typography.SIZE_LG,
            font_weight=Typography.WEIGHT_BOLD,
            color=Colors.TEXT_PRIMARY,
        ),
        rx.text(
            label,
            font_size=Typography.SIZE_XS,
            color=Colors.TEXT_MUTED,
        ),
        spacing="0",
        align="center",
        padding_x=Spacing.MD,
        padding_y=Spacing.SM,
        border=f"1px solid {Colors.BORDER}",
        border_radius=Radius.MD,
        min_width="88px",
    )


def accion_categorizar_plazas() -> rx.Component:
    return rx.cond(
        PlazasState.tiene_contexto & PlazasState.puede_operar_plazas_en_contexto,
        rx.button(
            rx.icon("tags", size=16),
            "Asignar plazas",
            on_click=PlazasState.abrir_modal_crear_lote,
            color_scheme="blue",
            disabled=~PlazasState.puede_categorizar_lote,
        ),
        rx.fragment(),
    )


def acciones_plaza(plaza: dict) -> rx.Component:
    es_vacante = plaza["estatus"] == "VACANTE"
    es_ocupada = plaza["estatus"] == "OCUPADA"
    es_suspendida = plaza["estatus"] == "SUSPENDIDA"
    es_cancelada = plaza["estatus"] == "CANCELADA"
    tiene_sede = plaza["sede_id"] != None
    tiene_categoria = plaza["categoria_puesto_id"] != None
    puede_operar = PlazasState.puede_operar_plazas_en_contexto

    return tabla_action_buttons(
        [
            tabla_action_button(
                icon="eye",
                tooltip="Ver detalle",
                on_click=lambda: PlazasState.abrir_modal_detalle(plaza),
            ),
            tabla_action_button(
                icon="pencil",
                tooltip="Editar",
                on_click=lambda: PlazasState.abrir_modal_editar(plaza),
                color_scheme="blue",
                visible=puede_operar & ~es_cancelada,
            ),
            tabla_action_button(
                icon="user-plus",
                tooltip="Asignar empleado",
                on_click=lambda: PlazasState.abrir_asignar_empleado(plaza),
                color_scheme="green",
                visible=puede_operar & es_vacante & tiene_categoria & tiene_sede,
            ),
            tabla_action_button(
                icon="user-minus",
                tooltip="Liberar plaza",
                on_click=lambda: PlazasState.liberar_plaza(plaza["id"]),
                color_scheme="orange",
                visible=puede_operar & es_ocupada,
            ),
            tabla_action_button(
                icon="pause",
                tooltip="Suspender",
                on_click=lambda: PlazasState.suspender_plaza(plaza["id"]),
                color_scheme="amber",
                visible=puede_operar & (es_vacante | es_ocupada),
            ),
            tabla_action_button(
                icon="play",
                tooltip="Reactivar",
                on_click=lambda: PlazasState.reactivar_plaza(plaza["id"]),
                color_scheme="green",
                visible=puede_operar & es_suspendida,
            ),
            tabla_action_button(
                icon="x",
                tooltip="Cancelar",
                on_click=lambda: PlazasState.abrir_confirmar_cancelar(plaza),
                color_scheme="red",
                visible=puede_operar & ~es_cancelada,
            ),
        ]
    )


def fila_plaza(plaza: dict) -> rx.Component:
    return rx.table.row(
        rx.table.cell(
            rx.text(
                "#",
                plaza["numero_plaza"],
                font_size=Typography.SIZE_SM,
                font_weight=Typography.WEIGHT_BOLD,
            ),
        ),
        rx.table.cell(
            rx.cond(
                plaza["codigo"],
                rx.text(plaza["codigo"], font_size=Typography.SIZE_SM),
                rx.text("-", font_size=Typography.SIZE_SM, color=Colors.TEXT_MUTED),
            ),
        ),
        rx.table.cell(
            rx.cond(
                plaza["sede_id"] != None,
                rx.hstack(
                    rx.cond(
                        plaza["sede_codigo"],
                        rx.badge(plaza["sede_codigo"], variant="outline", size="1"),
                        rx.fragment(),
                    ),
                    rx.text(plaza["sede_nombre"], font_size=Typography.SIZE_SM),
                    spacing="2",
                    align="center",
                    wrap="wrap",
                ),
                rx.badge("Sin sede", color_scheme="gray", variant="soft"),
            ),
        ),
        rx.table.cell(
            rx.cond(
                plaza["categoria_puesto_id"] != None,
                rx.hstack(
                    rx.badge(plaza["categoria_clave"], variant="outline", size="1"),
                    rx.text(plaza["categoria_nombre"], font_size=Typography.SIZE_SM),
                    spacing="2",
                    align="center",
                ),
                rx.badge("Sin categoría", color_scheme="gray", variant="soft"),
            ),
        ),
        rx.table.cell(rx.text(plaza["fecha_inicio_fmt"], font_size=Typography.SIZE_SM)),
        rx.table.cell(rx.text(plaza["salario_fmt"], font_size=Typography.SIZE_SM)),
        rx.table.cell(
            rx.cond(
                plaza["empleado_nombre"],
                rx.text(plaza["empleado_nombre"], font_size=Typography.SIZE_SM),
                rx.text("-", font_size=Typography.SIZE_SM, color=Colors.TEXT_MUTED),
            ),
        ),
        table_cell_badge(status_badge_reactive(plaza["estatus"], show_icon=True)),
        table_cell_actions(acciones_plaza(plaza)),
    )


ENCABEZADOS_PLAZAS = [
    {"nombre": "#", "ancho": "70px"},
    {"nombre": "Código", "ancho": "110px"},
    {"nombre": "Sede", "ancho": "220px"},
    {"nombre": "Categoría", "ancho": "220px"},
    {"nombre": "Inicio", "ancho": "110px"},
    {"nombre": "Salario", "ancho": "130px"},
    {"nombre": "Empleado", "ancho": "170px"},
    {"nombre": "Estatus", "ancho": "120px"},
    {"nombre": "Acciones", "ancho": "160px"},
]


def tabla_plazas() -> rx.Component:
    return table_shell(
        loading=PlazasState.loading,
        headers=ENCABEZADOS_PLAZAS,
        rows=PlazasState.plazas_filtradas,
        row_renderer=fila_plaza,
        has_rows=PlazasState.total_plazas_filtradas > 0,
        empty_component=tabla_vacia(
            mensaje=PlazasState.mensaje_tabla_vacia,
            submensaje=PlazasState.submensaje_tabla_vacia,
        ),
        total_caption=(
            "Mostrando "
            + PlazasState.total_plazas_filtradas.to(str)
            + " plaza(s)"
        ),
        loading_rows=6,
    )


def card_plaza(plaza: dict) -> rx.Component:
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.hstack(
                    rx.text(
                        "Plaza #",
                        plaza["numero_plaza"],
                        font_size=Typography.SIZE_LG,
                        font_weight=Typography.WEIGHT_BOLD,
                    ),
                    rx.cond(
                        plaza["codigo"],
                        rx.badge(plaza["codigo"], variant="outline", size="1"),
                        rx.fragment(),
                    ),
                    spacing="2",
                    align="center",
                ),
                rx.spacer(),
                status_badge_reactive(plaza["estatus"], show_icon=True),
                width="100%",
                align="center",
            ),
            rx.divider(),
            rx.vstack(
                rx.hstack(
                    rx.icon("map-pin", size=14, color=Colors.TEXT_MUTED),
                    rx.text("Sede:", font_size=Typography.SIZE_SM, color=Colors.TEXT_SECONDARY),
                    rx.text(plaza["sede_nombre"], font_size=Typography.SIZE_SM),
                    spacing="2",
                    align="center",
                    wrap="wrap",
                ),
                rx.hstack(
                    rx.icon("briefcase", size=14, color=Colors.TEXT_MUTED),
                    rx.text("Categoría:", font_size=Typography.SIZE_SM, color=Colors.TEXT_SECONDARY),
                    rx.cond(
                        plaza["categoria_puesto_id"] != None,
                        rx.text(plaza["categoria_nombre"], font_size=Typography.SIZE_SM),
                        rx.text("Sin categoría", font_size=Typography.SIZE_SM),
                    ),
                    spacing="2",
                    align="center",
                ),
                rx.hstack(
                    rx.icon("calendar", size=14, color=Colors.TEXT_MUTED),
                    rx.text("Inicio:", font_size=Typography.SIZE_SM, color=Colors.TEXT_SECONDARY),
                    rx.text(plaza["fecha_inicio_fmt"], font_size=Typography.SIZE_SM),
                    spacing="2",
                    align="center",
                ),
                rx.hstack(
                    rx.icon("dollar-sign", size=14, color=Colors.TEXT_MUTED),
                    rx.text("Salario:", font_size=Typography.SIZE_SM, color=Colors.TEXT_SECONDARY),
                    rx.text(plaza["salario_fmt"], font_size=Typography.SIZE_SM),
                    spacing="2",
                    align="center",
                ),
                rx.cond(
                    plaza["empleado_nombre"],
                    rx.hstack(
                        rx.icon("user", size=14, color=Colors.TEXT_MUTED),
                        rx.text("Empleado:", font_size=Typography.SIZE_SM, color=Colors.TEXT_SECONDARY),
                        rx.text(plaza["empleado_nombre"], font_size=Typography.SIZE_SM),
                        spacing="2",
                        align="center",
                    ),
                    rx.fragment(),
                ),
                spacing="2",
                align_items="start",
                width="100%",
            ),
            rx.hstack(acciones_plaza(plaza), width="100%", justify="end"),
            spacing="3",
            width="100%",
        ),
        width="100%",
        style={
            "transition": "all 0.2s ease",
            "_hover": {
                "box_shadow": Shadows.MD,
                "border_color": Colors.BORDER_STRONG,
            },
        },
    )


def grid_plazas() -> rx.Component:
    return rx.cond(
        PlazasState.loading,
        rx.center(rx.spinner(size="3"), padding="8"),
        rx.cond(
            PlazasState.total_plazas_filtradas > 0,
            rx.vstack(
                rx.box(
                    rx.foreach(PlazasState.plazas_filtradas, card_plaza),
                    display="grid",
                    grid_template_columns="repeat(auto-fill, minmax(320px, 1fr))",
                    gap=Spacing.MD,
                    width="100%",
                ),
                rx.text(
                    "Mostrando ",
                    PlazasState.total_plazas_filtradas,
                    " plaza(s)",
                    font_size=Typography.SIZE_SM,
                    color=Colors.TEXT_MUTED,
                ),
                width="100%",
                spacing="3",
            ),
            tabla_vacia(
                mensaje=PlazasState.mensaje_tabla_vacia,
                submensaje=PlazasState.submensaje_tabla_vacia,
            ),
        ),
    )


def resumen_plazas() -> rx.Component:
    return rx.box(
        rx.grid(
            _metric_card("Total", PlazasState.total_plazas, "users", Colors.PRIMARY, Colors.PRIMARY_LIGHT),
            _metric_card("Categorizadas", PlazasState.plazas_categorizadas, "tags", Colors.SUCCESS, Colors.SUCCESS_LIGHT),
            _metric_card("Sin categoría", PlazasState.plazas_sin_categoria, "circle-help", Colors.WARNING, Colors.WARNING_LIGHT),
            _metric_card("Vacantes", PlazasState.plazas_vacantes, "user-plus", Colors.INFO, Colors.INFO_LIGHT),
            _metric_card("Ocupadas", PlazasState.plazas_ocupadas, "user-check", Colors.SUCCESS, Colors.SUCCESS_LIGHT),
            _metric_card("Suspendidas", PlazasState.plazas_suspendidas, "pause", Colors.WARNING, Colors.WARNING_LIGHT),
            _metric_card("Desfase", PlazasState.plazas_desfase, "triangle-alert", Colors.ERROR, Colors.ERROR_LIGHT),
            columns=rx.breakpoints(initial="1", sm="2", md="3", xl="4"),
            spacing="4",
            width="100%",
        ),
        width="100%",
    )


def filtro_estatus() -> rx.Component:
    return rx.select.root(
        rx.select.trigger(placeholder="Estatus", width="150px"),
        rx.select.content(select_items_from_options(PlazasState.opciones_estatus)),
        value=PlazasState.filtro_estatus,
        on_change=PlazasState.set_filtro_estatus,
    )


def filtro_categoria() -> rx.Component:
    return rx.select.root(
        rx.select.trigger(placeholder="Categoría", width="220px"),
        rx.select.content(select_items_from_options(PlazasState.opciones_categorias_contrato)),
        value=PlazasState.categoria_filtro_id,
        on_change=PlazasState.set_categoria_filtro_id,
    )


def fila_resumen(item: dict) -> rx.Component:
    return rx.table.row(
        rx.table.cell(rx.text(item["contrato_codigo"], font_size=Typography.SIZE_SM)),
        rx.table.cell(
            rx.cond(
                item["categoria_puesto_id"] != None,
                rx.hstack(
                    rx.badge(item["categoria_clave"], variant="outline", size="1"),
                    rx.text(item["categoria_nombre"], font_size=Typography.SIZE_SM),
                    spacing="2",
                    align="center",
                ),
                rx.badge("Sin categoría", color_scheme="gray", variant="soft"),
            ),
        ),
        rx.table.cell(rx.text(item["total_plazas"], font_size=Typography.SIZE_SM), align="center"),
        rx.table.cell(
            rx.badge(item["plazas_vacantes"], color_scheme="blue", variant="soft"),
            align="center",
        ),
        rx.table.cell(
            rx.badge(item["plazas_ocupadas"], color_scheme="green", variant="soft"),
            align="center",
        ),
        rx.table.cell(
            rx.badge(item["plazas_suspendidas"], color_scheme="amber", variant="soft"),
            align="center",
        ),
        rx.table.cell(
            tabla_action_button(
                icon="arrow-right",
                tooltip="Ver plazas",
                on_click=lambda: PlazasState.seleccionar_resumen(item),
                color_scheme="blue",
            ),
        ),
        cursor="pointer",
        _hover={"background": Colors.SURFACE_HOVER},
        on_click=lambda: PlazasState.seleccionar_resumen(item),
    )


ENCABEZADOS_RESUMEN = [
    {"nombre": "Contrato", "ancho": "140px"},
    {"nombre": "Categoría", "ancho": "240px"},
    {"nombre": "Plazas", "ancho": "90px"},
    {"nombre": "Vacantes", "ancho": "90px"},
    {"nombre": "Ocupadas", "ancho": "90px"},
    {"nombre": "Suspendidas", "ancho": "100px"},
    {"nombre": "", "ancho": "60px"},
]


def tabla_resumen_inicial() -> rx.Component:
    return rx.cond(
        PlazasState.loading,
        skeleton_tabla(columnas=ENCABEZADOS_RESUMEN, filas=5),
        rx.cond(
            PlazasState.tiene_resumen,
            table_shell(
                loading=False,
                headers=ENCABEZADOS_RESUMEN,
                rows=PlazasState.resumen_categorias,
                row_renderer=fila_resumen,
                has_rows=True,
                empty_component=rx.fragment(),
                total_caption=(
                    PlazasState.resumen_categorias.length().to(str)
                    + " agrupación(es) con plazas"
                ),
            ),
            rx.callout(
                "Aún no hay plazas categorizadas o sin categoría registradas para mostrar en el resumen.",
                icon="info",
                color_scheme="blue",
                size="1",
            ),
        ),
    )


def fila_resumen_contrato_portal(item: dict) -> rx.Component:
    return rx.table.row(
        rx.table.cell(
            rx.text(
                item["contrato_codigo"],
                font_size=Typography.SIZE_SM,
                font_weight=Typography.WEIGHT_BOLD,
                color=Colors.TEXT_PRIMARY,
            ),
        ),
        rx.table.cell(
            rx.cond(
                item["tipo_servicio_clave"] != "",
                rx.hstack(
                    identifier_badge(item["tipo_servicio_clave"]),
                    rx.text(
                        item["tipo_servicio_nombre"],
                        font_size=Typography.SIZE_SM,
                    ),
                    spacing="2",
                    align="center",
                    wrap="wrap",
                ),
                rx.text(
                    item["tipo_servicio_nombre"],
                    font_size=Typography.SIZE_SM,
                    color=Colors.TEXT_MUTED,
                ),
            ),
        ),
        rx.table.cell(
            rx.text(item["total_plazas"], font_size=Typography.SIZE_SM),
            align="center",
        ),
        rx.table.cell(
            rx.badge(item["plazas_vacantes"], color_scheme="blue", variant="soft"),
            align="center",
        ),
        rx.table.cell(
            rx.badge(item["plazas_ocupadas"], color_scheme="green", variant="soft"),
            align="center",
        ),
        rx.table.cell(
            rx.badge(item["plazas_suspendidas"], color_scheme="amber", variant="soft"),
            align="center",
        ),
        cursor="pointer",
        _hover={"background": Colors.SURFACE_HOVER},
        on_click=lambda: PlazasState.seleccionar_contrato(item["contrato_id"]),
    )


ENCABEZADOS_CONTRATOS_PORTAL = [
    {"nombre": "Contrato", "ancho": "220px"},
    {"nombre": "Tipo de servicio", "ancho": "240px"},
    {"nombre": "Plazas", "ancho": "100px"},
    {"nombre": "Vacantes", "ancho": "110px"},
    {"nombre": "Ocupadas", "ancho": "110px"},
    {"nombre": "Suspendidas", "ancho": "120px"},
]


def tabla_contratos_portal() -> rx.Component:
    return rx.cond(
        PlazasState.loading,
        skeleton_tabla(columnas=ENCABEZADOS_CONTRATOS_PORTAL, filas=5),
        table_shell(
            loading=False,
            headers=ENCABEZADOS_CONTRATOS_PORTAL,
            rows=PlazasState.resumen_contratos,
            row_renderer=fila_resumen_contrato_portal,
            has_rows=PlazasState.resumen_contratos.length() > 0,
            empty_component=tabla_vacia(
                mensaje=PlazasState.mensaje_sin_contratos_disponibles,
                submensaje="",
            ),
            total_caption=(
                PlazasState.resumen_contratos.length().to(str)
                + " contrato(s) activos"
            ),
        ),
    )


def selector_contrato() -> rx.Component:
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.center(
                    rx.icon("folder-open", size=24, color=Colors.PRIMARY),
                    width="48px",
                    height="48px",
                    background=Colors.PRIMARY_LIGHT,
                    border_radius=Radius.MD,
                ),
                rx.vstack(
                    rx.text(
                        "Seleccionar Contrato",
                        font_size=Typography.SIZE_XL,
                        font_weight=Typography.WEIGHT_BOLD,
                    ),
                    rx.text(
                        PlazasState.descripcion_selector_contrato,
                        font_size=Typography.SIZE_SM,
                        color=Colors.TEXT_SECONDARY,
                    ),
                    spacing="1",
                    align_items="start",
                ),
                spacing="3",
                align="center",
                width="100%",
            ),
            rx.divider(),
            rx.select.root(
                rx.select.trigger(
                    placeholder="Seleccionar contrato...",
                    width="100%",
                ),
                rx.select.content(
                    rx.cond(
                        PlazasState.cargando_contratos,
                        rx.select.item("Cargando...", value="loading", disabled=True),
                        rx.cond(
                            PlazasState.contratos_disponibles.length() > 0,
                            rx.foreach(
                                PlazasState.opciones_contratos,
                                lambda opt: rx.select.item(opt["label"], value=opt["value"]),
                            ),
                            rx.select.item(
                                "Sin contratos disponibles",
                                value="empty",
                                disabled=True,
                            ),
                        ),
                    )
                ),
                value=PlazasState.contrato_seleccionado_id,
                on_change=PlazasState.set_contrato_seleccionado_id,
            ),
            rx.callout(
                "Las plazas se materializan desde el contrato. Aquí solo se categorizan y operan.",
                icon="info",
                color_scheme="blue",
                size="1",
            ),
            rx.cond(
                PlazasState.contratos_disponibles.length() == 0,
                rx.callout(
                    PlazasState.mensaje_sin_contratos_disponibles,
                    icon="triangle-alert",
                    color_scheme="amber",
                    size="1",
                ),
                rx.fragment(),
            ),
            spacing="4",
            width="100%",
        ),
        width="100%",
    )


def contexto_contrato_portal() -> rx.Component:
    return rx.flex(
        rx.vstack(
            rx.text(
                PlazasState.contrato_codigo,
                font_size=Typography.SIZE_LG,
                font_weight=Typography.WEIGHT_BOLD,
                color=Colors.TEXT_PRIMARY,
            ),
            rx.hstack(
                rx.cond(
                    PlazasState.contrato_tipo_servicio_clave != "",
                    rx.hstack(
                        identifier_badge(PlazasState.contrato_tipo_servicio_clave),
                        rx.text(
                            PlazasState.contrato_tipo_servicio_nombre,
                            font_size=Typography.SIZE_SM,
                            color=Colors.TEXT_SECONDARY,
                        ),
                        spacing="2",
                        align="center",
                        wrap="wrap",
                    ),
                    rx.cond(
                        PlazasState.contrato_tipo_servicio_nombre != "",
                        rx.text(
                            PlazasState.contrato_tipo_servicio_nombre,
                            font_size=Typography.SIZE_SM,
                            color=Colors.TEXT_SECONDARY,
                        ),
                        rx.fragment(),
                    ),
                ),
                status_badge_reactive(
                    PlazasState.contrato_estatus,
                    show_icon=True,
                ),
                spacing="2",
                wrap="wrap",
                align="center",
            ),
            rx.cond(
                PlazasState.nombre_categoria_filtro != "",
                rx.hstack(
                    rx.text(
                        "Categoría filtrada:",
                        font_size=Typography.SIZE_SM,
                        color=Colors.TEXT_SECONDARY,
                    ),
                    rx.badge(
                        PlazasState.nombre_categoria_filtro,
                        color_scheme="gray",
                        variant="soft",
                    ),
                    spacing="2",
                    align="center",
                    wrap="wrap",
                ),
                rx.text(
                    "Gestione las plazas del contrato seleccionado.",
                    font_size=Typography.SIZE_SM,
                    color=Colors.TEXT_SECONDARY,
                ),
            ),
            spacing="1",
            align_items="start",
            flex="1",
            min_width="280px",
        ),
        rx.flex(
            _portal_metric_card("Plazas", PlazasState.total_plazas),
            _portal_metric_card("Vacantes", PlazasState.plazas_vacantes),
            _portal_metric_card("Ocupadas", PlazasState.plazas_ocupadas),
            _portal_metric_card("Suspendidas", PlazasState.plazas_suspendidas),
            direction="row",
            wrap="wrap",
            justify="end",
            column_gap=Spacing.SM,
            row_gap=Spacing.SM,
            flex="0 1 auto",
            min_width="fit-content",
        ),
        width="100%",
        align="center",
        justify="between",
        padding=Spacing.MD,
        background=Colors.SURFACE,
        border=f"1px solid {Colors.BORDER}",
        border_radius=Radius.MD,
        direction="row",
        wrap="wrap",
        gap=Spacing.MD,
    )


def detalle_portal_plazas() -> rx.Component:
    filtros = rx.hstack(
        filtro_categoria(),
        filtro_estatus(),
        spacing="2",
        wrap="wrap",
    )

    return rx.vstack(
        rx.hstack(
            rx.button(
                rx.icon("arrow-left", size=16),
                "Volver a contratos",
                on_click=PlazasState.volver_a_resumen,
                variant="ghost",
                size="2",
            ),
            rx.spacer(),
            accion_categorizar_plazas(),
            spacing="3",
            width="100%",
            align="center",
        ),
        contexto_contrato_portal(),
        alertas_contrato(),
        page_toolbar(
            search_value=PlazasState.filtro_busqueda,
            search_placeholder="Buscar por número, código, sede, categoría o empleado...",
            on_search_change=PlazasState.set_filtro_busqueda,
            on_search_clear=lambda: PlazasState.set_filtro_busqueda(""),
            filters=filtros,
            show_view_toggle=False,
        ),
        tabla_plazas(),
        width="100%",
        spacing="4",
        padding=Spacing.LG,
    )


def alertas_contrato() -> rx.Component:
    return rx.vstack(
        rx.cond(
            PlazasState.plazas_sin_sede_total > 0,
            rx.callout(
                "Hay plazas sin sede. Use 'Asignar plazas' o edite cada plaza antes de ocuparlas o asignarles personal.",
                icon="triangle-alert",
                color_scheme="amber",
                size="1",
            ),
            rx.fragment(),
        ),
        rx.cond(
            PlazasState.plazas_sin_categoria > 0,
            rx.callout(
                "Hay plazas sin categoría. Use 'Asignar plazas' o edite cada plaza individualmente.",
                icon="triangle-alert",
                color_scheme="amber",
                size="1",
            ),
            rx.fragment(),
        ),
        rx.cond(
            PlazasState.plazas_desfase > 0,
            rx.callout(
                "El contrato tiene más plazas materializadas que su máximo actual. Revise la configuración del contrato.",
                icon="triangle-alert",
                color_scheme="red",
                size="1",
            ),
            rx.fragment(),
        ),
        spacing="3",
        width="100%",
    )


def plazas_page() -> rx.Component:
    accion_principal = accion_categorizar_plazas()

    filtros = rx.hstack(
        filtro_categoria(),
        filtro_estatus(),
        spacing="2",
        wrap="wrap",
    )

    return rx.box(
        page_layout(
            header=rx.cond(
                PlazasState.es_detalle_portal,
                rx.fragment(),
                page_header(
                    titulo=PlazasState.titulo_pagina,
                    subtitulo=rx.cond(
                        PlazasState.mostrar_vista_inicial,
                        PlazasState.subtitulo_inicio,
                        "",
                    ),
                    icono="briefcase",
                    accion_principal=accion_principal,
                ),
            ),
            toolbar=rx.cond(
                PlazasState.tiene_contexto & ~PlazasState.es_detalle_portal,
                page_toolbar(
                    search_value=PlazasState.filtro_busqueda,
                    search_placeholder="Buscar por número, código, sede, categoría o empleado...",
                    on_search_change=PlazasState.set_filtro_busqueda,
                    on_search_clear=lambda: PlazasState.set_filtro_busqueda(""),
                    filters=filtros,
                    show_view_toggle=True,
                    current_view=PlazasState.view_mode,
                    on_view_table=PlazasState.set_view_table,
                    on_view_cards=PlazasState.set_view_cards,
                ),
                rx.fragment(),
            ),
            content=rx.vstack(
                rx.cond(
                    PlazasState.es_detalle_portal,
                    detalle_portal_plazas(),
                    rx.cond(
                        PlazasState.mostrar_vista_inicial,
                        rx.cond(
                            PlazasState.es_contexto_portal,
                            tabla_contratos_portal(),
                            rx.vstack(
                                selector_contrato(),
                                tabla_resumen_inicial(),
                                spacing="4",
                                width="100%",
                            ),
                        ),
                        rx.vstack(
                            rx.cond(
                                PlazasState.es_contexto_portal,
                                contexto_contrato_portal(),
                                breadcrumb_dynamic(PlazasState.breadcrumb_items),
                            ),
                            alertas_contrato(),
                            resumen_plazas(),
                            rx.cond(
                                PlazasState.is_table_view,
                                tabla_plazas(),
                                grid_plazas(),
                            ),
                            spacing="4",
                            width="100%",
                        ),
                    ),
                ),
                modal_plaza(),
                modal_detalle_plaza(),
                modal_confirmar_cancelar(),
                modal_crear_lote(),
                modal_asignar_empleado(),
                spacing="4",
                width="100%",
            ),
        ),
        width="100%",
        min_height="100vh",
        on_mount=PlazasState.on_mount_plazas,
    )
