"""Componentes UI para la pagina unificada de Empleados en portal."""

import reflex as rx

from app.core.enums import EstatusPlaza
from app.presentation.components.ui import (
    empty_state_card,
    employee_status_badge,
    filter_pill,
    metric_card,
    segmented_tab_trigger,
    segmented_tabs,
    select_items_from_options,
    status_badge_reactive,
    tabla_cta_button,
    table_cell_actions,
    table_cell_badge,
    table_cell_text_sm,
    table_pagination,
    table_shell,
    table_text_sm,
)
from app.presentation.portal.pages.expedientes.state import ExpedientesState
from app.presentation.theme import Colors, Radius, Spacing, Typography

from .state import MisEmpleadosState, VISTA_PERSONAL_EMPLEADO, VISTA_PERSONAL_PLAZA


def _celda_centrada(component: rx.Component) -> rx.Component:
    return rx.table.cell(
        rx.center(
            component,
            width="100%",
        ),
    )


def _celda_dos_lineas(
    principal,
    secundario="",
    *,
    tone: str = "primary",
    fallback: str = "—",
) -> rx.Component:
    return rx.table.cell(
        rx.cond(
            principal != "",
            rx.vstack(
                table_text_sm(
                    principal,
                    weight=Typography.WEIGHT_MEDIUM,
                    tone=tone,
                ),
                rx.cond(
                    secundario != "",
                    table_text_sm(
                        secundario,
                        tone="muted",
                    ),
                    rx.fragment(),
                ),
                spacing="0",
                align="start",
                width="100%",
            ),
            table_text_sm(fallback, tone="muted"),
        ),
    )


def _barra_cobertura() -> rx.Component:
    return rx.center(
        rx.box(
            rx.box(
                width=MisEmpleadosState.metrica_porcentaje_cobertura.to(str) + "%",
                height=Spacing.XS,
                border_radius=Radius.FULL,
                background=Colors.SUCCESS,
            ),
            width="100%",
            max_width="160px",
            height=Spacing.XS,
            border_radius=Radius.FULL,
            background=Colors.BORDER,
            overflow="hidden",
        ),
        width="100%",
    )


def metricas_empleados() -> rx.Component:
    return rx.grid(
        metric_card(
            titulo="Plazas totales",
            valor=MisEmpleadosState.metrica_plazas_totales,
            icono=None,
            descripcion=MisEmpleadosState.metrica_hint_plazas,
            show_icon=False,
            background=Colors.SECONDARY_LIGHT,
            border="none",
            hoverable=False,
            align="center",
        ),
        metric_card(
            titulo="Ocupadas",
            valor=MisEmpleadosState.metrica_plazas_ocupadas,
            icono=None,
            descripcion=MisEmpleadosState.metrica_hint_cobertura,
            show_icon=False,
            background=Colors.SECONDARY_LIGHT,
            border="none",
            hoverable=False,
            value_color=Colors.SUCCESS,
            footer=_barra_cobertura(),
            align="center",
        ),
        metric_card(
            titulo="Vacantes",
            valor=MisEmpleadosState.metrica_plazas_vacantes,
            icono=None,
            show_icon=False,
            background=Colors.SECONDARY_LIGHT,
            border="none",
            hoverable=False,
            value_color=Colors.INFO,
            align="center",
        ),
        metric_card(
            titulo="Propuestas por alta",
            valor=MisEmpleadosState.metrica_propuestas_alta,
            icono=None,
            descripcion=MisEmpleadosState.metrica_hint_propuestas,
            show_icon=False,
            background=Colors.SECONDARY_LIGHT,
            border="none",
            hoverable=False,
            value_color=Colors.WARNING,
            align="center",
        ),
        metric_card(
            titulo="Suspendidas",
            valor=MisEmpleadosState.metrica_plazas_suspendidas,
            icono=None,
            show_icon=False,
            background=Colors.SECONDARY_LIGHT,
            border="none",
            hoverable=False,
            align="center",
        ),
        grid_template_columns="repeat(5, minmax(0, 1fr))",
        gap=Spacing.SM,
        width="100%",
    )


def selector_vista_personal() -> rx.Component:
    return segmented_tabs(
        segmented_tab_trigger("Por empleado", VISTA_PERSONAL_EMPLEADO),
        segmented_tab_trigger("Por plaza", VISTA_PERSONAL_PLAZA),
        value=MisEmpleadosState.vista_personal,
        on_change=MisEmpleadosState.set_vista_personal,
    )


def filtros_estatus_empleados() -> rx.Component:
    return rx.flex(
        filter_pill(
            "Todos",
            MisEmpleadosState.stats_total.to(str),
            MisEmpleadosState.filtrar_todos,
            MisEmpleadosState.filtro_es_todos,
        ),
        filter_pill(
            "Activos",
            MisEmpleadosState.stats_activos.to(str),
            MisEmpleadosState.filtrar_activos,
            MisEmpleadosState.filtro_es_activos,
            Colors.SUCCESS,
        ),
        filter_pill(
            "En alta",
            MisEmpleadosState.stats_en_alta.to(str),
            MisEmpleadosState.filtrar_en_alta,
            MisEmpleadosState.filtro_es_en_alta,
            Colors.WARNING,
        ),
        filter_pill(
            "Suspendidos",
            MisEmpleadosState.stats_suspendidos.to(str),
            MisEmpleadosState.filtrar_suspendidos,
            MisEmpleadosState.filtro_es_suspendidos,
            Colors.TEXT_MUTED,
        ),
        filter_pill(
            "En baja",
            MisEmpleadosState.stats_en_baja.to(str),
            MisEmpleadosState.filtrar_en_baja,
            MisEmpleadosState.filtro_es_en_baja,
            Colors.ERROR,
        ),
        wrap="wrap",
        gap=Spacing.SM,
        width="100%",
    )


def filtro_contrato_empleados() -> rx.Component:
    return rx.select.root(
        rx.select.trigger(
            placeholder="Todos los contratos",
            width="260px",
        ),
        rx.select.content(
            select_items_from_options(MisEmpleadosState.opciones_contratos_activos),
        ),
        value=MisEmpleadosState.filtro_contrato_id,
        on_change=MisEmpleadosState.set_filtro_contrato_id,
        size="2",
    )


def _expediente_cell(emp: dict) -> rx.Component:
    return rx.table.cell(
        rx.button(
            emp.get("expediente_resumen_ui", "0/0"),
            on_click=ExpedientesState.abrir_panel_expediente(emp),
            variant="ghost",
            size="1",
            padding="0",
            height="auto",
            justify="start",
            font_size=Typography.SIZE_SM,
            font_weight=Typography.WEIGHT_MEDIUM,
            font_variant_numeric="tabular-nums",
            color=rx.match(
                emp.get("expediente_tone", "secondary"),
                ("warning", Colors.WARNING),
                ("success", Colors.SUCCESS),
                Colors.TEXT_SECONDARY,
            ),
        ),
    )


def _accion_empleado(emp: dict) -> rx.Component:
    return rx.match(
        emp.get("estatus_personal", ""),
        (
            "EN_ALTA",
            tabla_cta_button(
                "Completar alta",
                MisEmpleadosState.abrir_modal_editar(emp),
                color_scheme="amber",
            ),
        ),
        (
            "EN_BAJA",
            tabla_cta_button(
                "Ver baja",
                MisEmpleadosState.ver_baja_empleado(emp),
                color_scheme="red",
            ),
        ),
        (
            "SUSPENDIDO",
            tabla_cta_button(
                "Ver",
                MisEmpleadosState.abrir_modal_detalle(emp),
            ),
        ),
        rx.cond(
            emp.get("expediente_requiere_accion", False),
            tabla_cta_button(
                "Completar expediente",
                ExpedientesState.abrir_panel_expediente(emp),
                color_scheme="amber",
            ),
            tabla_cta_button(
                "Ver",
                MisEmpleadosState.abrir_modal_detalle(emp),
            ),
        ),
    )


def fila_empleado(emp: dict) -> rx.Component:
    return rx.table.row(
        _celda_dos_lineas(
            emp.get("nombre_completo_ui", ""),
            emp.get("contacto_secundario_ui", ""),
            fallback="Sin nombre",
        ),
        table_cell_text_sm(
            emp.get("contrato_codigo", ""),
            tone="secondary",
            fallback="—",
        ),
        table_cell_text_sm(
            emp.get("categoria_nombre", ""),
            tone="secondary",
            fallback="—",
        ),
        table_cell_badge(
            employee_status_badge(emp.get("estatus_personal", "")),
        ),
        _expediente_cell(emp),
        table_cell_actions(
            _accion_empleado(emp),
        ),
    )


ENCABEZADOS_EMPLEADOS = [
    {"nombre": "Nombre", "ancho": "290px"},
    {"nombre": "Contrato", "ancho": "140px"},
    {"nombre": "Categoría", "ancho": "180px"},
    {"nombre": "Estatus", "ancho": "130px"},
    {"nombre": "Expediente", "ancho": "140px"},
    {"nombre": "Acción", "ancho": "180px"},
]


def tabla_empleados() -> rx.Component:
    return table_shell(
        loading=MisEmpleadosState.loading,
        headers=ENCABEZADOS_EMPLEADOS,
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
            rx.badge("Ocupada", color_scheme="green", variant="soft", size="1"),
        ),
        (
            EstatusPlaza.VACANTE.value,
            rx.badge("Vacante", color_scheme="blue", variant="soft", size="1"),
        ),
        (
            EstatusPlaza.SUSPENDIDA.value,
            rx.badge("Suspendida", color_scheme="gray", variant="soft", size="1"),
        ),
        rx.badge("Sin estatus", color_scheme="gray", variant="soft", size="1"),
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
        f"3px solid {Colors.TEXT_MUTED}",
    )


def _accion_plaza(plaza: dict) -> rx.Component:
    return rx.match(
        plaza.get("estatus", ""),
        (
            EstatusPlaza.OCUPADA.value,
            tabla_cta_button(
                "Reasignar",
                MisEmpleadosState.abrir_modal_asignacion_plaza(plaza),
            ),
        ),
        (
            EstatusPlaza.VACANTE.value,
            tabla_cta_button(
                "Asignar",
                MisEmpleadosState.abrir_modal_asignacion_plaza(plaza),
                color_scheme="blue",
                variant="soft",
                style={
                    "background": Colors.INFO_LIGHT,
                    "color": Colors.INFO,
                    "border": "none",
                },
            ),
        ),
        (
            EstatusPlaza.SUSPENDIDA.value,
            tabla_cta_button(
                "Reactivar",
                MisEmpleadosState.reactivar_plaza_portal(plaza),
                color_scheme="amber",
            ),
        ),
        tabla_cta_button(
            "Ver",
            MisEmpleadosState.abrir_modal_asignacion_plaza(plaza),
        ),
    )


def fila_plaza(plaza: dict, contrato_id) -> rx.Component:
    return rx.table.row(
        rx.table.cell(
            rx.center(
                rx.checkbox(
                    checked=plaza.get("seleccionada", False),
                    on_change=lambda checked: MisEmpleadosState.toggle_plaza_seleccionada(
                        contrato_id,
                        plaza.get("id"),
                        checked,
                    ),
                    size="1",
                ),
                width="100%",
            ),
        ),
        _celda_centrada(
            table_text_sm(
                plaza.get("numero_plaza", ""),
                tone="muted",
                font_variant_numeric="tabular-nums",
            ),
        ),
        table_cell_text_sm(
            plaza.get("categoria_nombre", ""),
            tone="secondary",
            fallback="—",
        ),
        rx.table.cell(
            table_text_sm(
                plaza.get("sede_display", ""),
                tone="secondary",
                fallback="sin sede",
            ),
        ),
        _celda_dos_lineas(
            plaza.get("empleado_nombre", ""),
            "",
            fallback="—",
        ),
        table_cell_badge(
            _badge_estado_plaza(plaza.get("estatus", "")),
        ),
        table_cell_actions(
            _accion_plaza(plaza),
        ),
        border_left=_borde_izquierdo_plaza(plaza.get("estatus", "")),
        background=rx.cond(
            plaza.get("seleccionada", False),
            Colors.PRIMARY_LIGHTER,
            Colors.SURFACE,
        ),
    )


ENCABEZADOS_PLAZAS = [
    {"nombre": "", "ancho": "36px", "header_align": "center"},
    {"nombre": "#", "ancho": "52px", "header_align": "center"},
    {"nombre": "Categoría", "ancho": "220px"},
    {"nombre": "Sede", "ancho": "220px"},
    {"nombre": "Empleado asignado", "ancho": "260px"},
    {"nombre": "Estado", "ancho": "140px"},
    {"nombre": "Acción", "ancho": "140px"},
]


def _barra_acciones_masivas(bloque: dict) -> rx.Component:
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
                        select_items_from_options(MisEmpleadosState.opciones_sedes_plaza),
                    ),
                    value=bloque.get("sede_masiva_value", ""),
                    on_change=lambda value: MisEmpleadosState.set_sede_masiva_contrato(
                        bloque.get("contrato_id"),
                        value,
                    ),
                    size="1",
                ),
                rx.button(
                    "Aplicar",
                    size="1",
                    variant="soft",
                    color_scheme="blue",
                    on_click=MisEmpleadosState.aplicar_sede_masiva_contrato(
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
                            MisEmpleadosState.opciones_categorias_masivas_actuales,
                        ),
                    ),
                    value=bloque.get("categoria_masiva_value", ""),
                    on_change=lambda value: MisEmpleadosState.set_categoria_masiva_contrato(
                        bloque.get("contrato_id"),
                        value,
                    ),
                    size="1",
                ),
                rx.button(
                    "Aplicar",
                    size="1",
                    variant="soft",
                    color_scheme="blue",
                    on_click=MisEmpleadosState.aplicar_categoria_masiva_contrato(
                        bloque.get("contrato_id"),
                    ),
                ),
                rx.button(
                    "Deseleccionar",
                    size="1",
                    variant="ghost",
                    on_click=MisEmpleadosState.limpiar_seleccion_plazas(
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
            border_radius=Radius.LG,
        ),
        rx.fragment(),
    )


def _encabezado_contrato_plaza(bloque: dict) -> rx.Component:
    return rx.flex(
        rx.hstack(
            rx.icon(
                "chevron-right",
                size=16,
                color=Colors.TEXT_MUTED,
                transform=bloque.get("rotacion_chevron", "rotate(0deg)"),
                transition="transform 0.2s",
            ),
            rx.vstack(
                table_text_sm(
                    bloque.get("contrato_codigo", "Sin contrato"),
                    weight=Typography.WEIGHT_MEDIUM,
                ),
                table_text_sm(
                    bloque.get("tipo_servicio_nombre", ""),
                    tone="muted",
                ),
                spacing="0",
                align="start",
            ),
            spacing="2",
            align="center",
        ),
        rx.flex(
            _badge_resumen_contrato(
                f"{bloque.get('plazas_ocupadas', 0)} ocupadas",
                "green",
            ),
            _badge_resumen_contrato(
                f"{bloque.get('plazas_vacantes', 0)} vacantes",
                "blue",
            ),
            rx.cond(
                bloque.get("mostrar_badge_suspendidas", False),
                _badge_resumen_contrato(
                    f"{bloque.get('plazas_suspendidas', 0)} suspendidas",
                    "gray",
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
        padding_y=Spacing.SM,
        width="100%",
        justify="between",
        align="center",
        wrap="wrap",
        gap=Spacing.SM,
        cursor="pointer",
        background=Colors.SURFACE,
        border=f"1px solid {Colors.BORDER}",
        border_radius=Radius.LG,
        _hover={"background": Colors.SECONDARY_LIGHT},
        on_click=MisEmpleadosState.toggle_contrato_plaza(bloque.get("contrato_id")),
    )


def _tabla_contrato_plaza(bloque: dict) -> rx.Component:
    return rx.vstack(
        _barra_acciones_masivas(bloque),
        rx.table.root(
            rx.table.header(
                rx.table.row(
                    rx.table.column_header_cell(
                        rx.center(
                            rx.checkbox(
                                checked=bloque.get("seleccion_todas_visibles", False),
                                on_change=lambda checked: MisEmpleadosState.seleccionar_todas_plazas_visibles(
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
                            col["nombre"],
                            width=col["ancho"],
                            text_align=col.get("header_align", "left"),
                        )
                        for col in ENCABEZADOS_PLAZAS[1:]
                    ],
                ),
            ),
            rx.table.body(
                rx.foreach(
                    MisEmpleadosState.plazas_visibles_contrato_actual,
                    lambda plaza: fila_plaza(plaza, bloque.get("contrato_id")),
                ),
            ),
            width="100%",
            size="1",
            variant="surface",
        ),
        rx.vstack(
            table_text_sm(
                MisEmpleadosState.resumen_pagina_contrato_actual,
                tone="secondary",
            ),
            table_pagination(
                current_page=MisEmpleadosState.pagina_plaza_actual,
                total_pages=MisEmpleadosState.total_paginas_plaza_actual,
                page_numbers=MisEmpleadosState.page_numbers_plaza_actual,
                on_page_change=lambda page: MisEmpleadosState.ir_a_pagina_plaza_contrato(
                    bloque.get("contrato_id"),
                    page,
                ),
                on_previous=MisEmpleadosState.pagina_anterior_plaza_contrato(
                    bloque.get("contrato_id"),
                ),
                on_next=MisEmpleadosState.pagina_siguiente_plaza_contrato(
                    bloque.get("contrato_id"),
                ),
                color_scheme=Colors.PORTAL_ACCENT_SCHEME,
            ),
            spacing="2",
            width="100%",
        ),
        spacing="2",
        width="100%",
    )


def _bloque_contrato_plaza(bloque: dict) -> rx.Component:
    return rx.vstack(
        _encabezado_contrato_plaza(bloque),
        rx.cond(
            bloque.get("expandido", False),
            rx.cond(
                bloque.get("cargando_plazas", False),
                rx.center(
                    rx.spinner(size="2"),
                    width="100%",
                    padding_y=Spacing.LG,
                ),
                rx.cond(
                    bloque.get("tiene_plazas_tabla", False),
                    _tabla_contrato_plaza(bloque),
                    empty_state_card(
                        title="Sin plazas para este contrato",
                        description="No hay plazas disponibles para mostrar con el filtro actual.",
                        icon="briefcase",
                    ),
                ),
            ),
            rx.fragment(),
        ),
        spacing="2",
        width="100%",
    )


def tabla_plazas_por_contrato() -> rx.Component:
    return rx.cond(
        MisEmpleadosState.loading,
        rx.center(
            rx.spinner(size="3"),
            width="100%",
            padding_y=Spacing.XL,
        ),
        rx.cond(
            MisEmpleadosState.tiene_plazas_visibles,
            rx.vstack(
                rx.foreach(
                    MisEmpleadosState.bloques_contrato_plaza,
                    _bloque_contrato_plaza,
                ),
                spacing="3",
                width="100%",
            ),
            empty_state_card(
                title="No hay plazas para este filtro",
                description="Ajuste la búsqueda o cambie el contrato para revisar la asignación de personal.",
                icon="briefcase",
            ),
        ),
    )
