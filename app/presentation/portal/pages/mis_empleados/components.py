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
    return rx.box(
        rx.box(
            width=MisEmpleadosState.metrica_porcentaje_cobertura.to(str) + "%",
            height=Spacing.XS,
            border_radius=Radius.FULL,
            background=Colors.SUCCESS,
        ),
        width="100%",
        height=Spacing.XS,
        border_radius=Radius.FULL,
        background=Colors.BORDER,
        overflow="hidden",
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
        ),
        metric_card(
            titulo="Suspendidas",
            valor=MisEmpleadosState.metrica_plazas_suspendidas,
            icono=None,
            show_icon=False,
            background=Colors.SECONDARY_LIGHT,
            border="none",
            hoverable=False,
        ),
        columns=rx.breakpoints(initial="1", sm="2", lg="5"),
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
                color_scheme="teal",
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
            color_scheme="teal",
        ),
        loading_rows=5,
        table_size="1",
    )


def _sede_inline_plaza(plaza: dict) -> rx.Component:
    return rx.select.root(
        rx.select.trigger(
            placeholder="Sin sede",
            width="190px",
        ),
        rx.select.content(
            select_items_from_options(MisEmpleadosState.opciones_sedes_plaza),
        ),
        value=plaza.get("sede_id_text", ""),
        on_change=lambda value: MisEmpleadosState.actualizar_sede_plaza(plaza.get("id"), value),
        size="1",
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


def fila_plaza(plaza: dict) -> rx.Component:
    return rx.table.row(
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
            _sede_inline_plaza(plaza),
        ),
        _celda_dos_lineas(
            plaza.get("empleado_nombre", ""),
            "",
            fallback="—",
        ),
        table_cell_badge(
            status_badge_reactive(plaza.get("estatus", "")),
        ),
        table_cell_actions(
            _accion_plaza(plaza),
        ),
        border_left=rx.match(
            plaza.get("estatus", ""),
            (
                EstatusPlaza.OCUPADA.value,
                f"3px solid {Colors.SUCCESS}",
            ),
            (
                EstatusPlaza.VACANTE.value,
                f"3px solid {Colors.INFO}",
            ),
            f"3px solid {Colors.BORDER}",
        ),
    )


ENCABEZADOS_PLAZAS = [
    {"nombre": "#", "ancho": "52px", "header_align": "center"},
    {"nombre": "Categoría", "ancho": "220px"},
    {"nombre": "Sede", "ancho": "220px"},
    {"nombre": "Empleado asignado", "ancho": "260px"},
    {"nombre": "Estado", "ancho": "140px"},
    {"nombre": "Acción", "ancho": "140px"},
]


def _encabezado_grupo_plaza(grupo: dict) -> rx.Component:
    return rx.flex(
        rx.vstack(
            table_text_sm(
                grupo.get("contrato_codigo", "Sin contrato"),
                weight=Typography.WEIGHT_SEMIBOLD,
            ),
            rx.cond(
                grupo.get("tipo_servicio_nombre", "") != "",
                table_text_sm(
                    grupo.get("tipo_servicio_nombre", ""),
                    tone="secondary",
                ),
                rx.fragment(),
            ),
            spacing="0",
            align="start",
        ),
        table_text_sm(
            grupo.get("resumen_plazas", ""),
            tone="muted",
        ),
        width="100%",
        justify="between",
        align="center",
        padding_x=Spacing.MD,
        padding_y=Spacing.SM,
        background=Colors.SECONDARY_LIGHT,
        border_radius=Radius.LG,
    )


def fila_plaza_agrupada(fila: dict) -> rx.Component:
    return rx.cond(
        fila.get("tipo_fila", "") == "grupo",
        rx.table.row(
            rx.table.cell(
                _encabezado_grupo_plaza(fila),
                col_span=6,
                padding_top=Spacing.MD,
                padding_bottom=Spacing.XS,
            ),
        ),
        fila_plaza(fila),
    )


def _loading_tabla_plazas() -> rx.Component:
    return table_shell(
        loading=True,
        headers=ENCABEZADOS_PLAZAS,
        rows=[],
        row_renderer=lambda _row: rx.fragment(),
        has_rows=False,
        empty_component=rx.fragment(),
        loading_rows=6,
        table_size="1",
    )


def tabla_plazas_por_contrato() -> rx.Component:
    return rx.cond(
        MisEmpleadosState.loading,
        _loading_tabla_plazas(),
        rx.cond(
            MisEmpleadosState.tiene_plazas_visibles,
            table_shell(
                loading=False,
                headers=ENCABEZADOS_PLAZAS,
                rows=MisEmpleadosState.filas_plazas_agrupadas,
                row_renderer=fila_plaza_agrupada,
                has_rows=MisEmpleadosState.total_plazas_visibles > 0,
                empty_component=empty_state_card(
                    title="No hay plazas para este filtro",
                    description="Ajuste la búsqueda o cambie el contrato para revisar la asignación de personal.",
                    icon="briefcase",
                ),
                total_caption=MisEmpleadosState.resumen_paginacion_plazas,
                table_size="1",
            ),
            empty_state_card(
                title="No hay plazas para este filtro",
                description="Ajuste la búsqueda o cambie el contrato para revisar la asignación de personal.",
                icon="briefcase",
            ),
        ),
    )
