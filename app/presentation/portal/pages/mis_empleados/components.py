"""
Componentes UI para la pagina Mis Empleados del portal.

Tabla, filtros y badges.
"""
import reflex as rx

from app.presentation.constants import FILTRO_TODOS
from app.presentation.components.ui import (
    tabla_action_button,
    tabla_action_buttons,
    empty_state_card,
    employee_status_badge,
    table_pagination,
)
from app.presentation.components.reusable import employee_filters_bar, employee_table
from app.presentation.theme import Colors, Typography

from .state import MisEmpleadosState


def badge_estatus(estatus: str) -> rx.Component:
    """Badge de estatus del empleado."""
    return employee_status_badge(estatus)


def fila_empleado(emp: dict) -> rx.Component:
    """Fila de la tabla de empleados."""
    # Editable: ACTIVO y no restringido
    puede_editar = (emp["estatus"] == "ACTIVO") & (~emp["is_restricted"])
    puede_dar_baja = emp["estatus"] == "ACTIVO"
    return rx.table.row(
        rx.table.cell(
            rx.text(
                emp["clave"],
                font_size=Typography.SIZE_SM,
                font_weight=Typography.WEIGHT_MEDIUM,
                color=Colors.PORTAL_PRIMARY_TEXT,
            ),
        ),
        rx.table.cell(
            rx.text(
                emp["nombre_completo"],
                font_size=Typography.SIZE_SM,
                font_weight=Typography.WEIGHT_MEDIUM,
            ),
        ),
        rx.table.cell(
            rx.text(
                emp["curp"],
                font_size=Typography.SIZE_SM,
                color=Colors.TEXT_SECONDARY,
            ),
        ),
        rx.table.cell(
            badge_estatus(emp["estatus"]),
        ),
        rx.table.cell(
            tabla_action_buttons([
                tabla_action_button(
                    icon="pencil",
                    tooltip="Editar",
                    on_click=MisEmpleadosState.abrir_modal_editar(emp),
                    color_scheme="teal",
                    visible=puede_editar,
                ),
                tabla_action_button(
                    icon="user-minus",
                    tooltip="Dar de baja",
                    on_click=MisEmpleadosState.abrir_modal_baja(emp),
                    color_scheme="red",
                    visible=puede_dar_baja,
                ),
            ]),
        ),
    )


ENCABEZADOS_EMPLEADOS = [
    {"nombre": "Clave", "ancho": "120px"},
    {"nombre": "Nombre", "ancho": "auto"},
    {"nombre": "CURP", "ancho": "200px"},
    {"nombre": "Estatus", "ancho": "100px"},
    {"nombre": "Acciones", "ancho": "120px"},
]


def tabla_empleados() -> rx.Component:
    """Tabla de empleados."""
    return employee_table(
        loading=MisEmpleadosState.loading,
        headers=ENCABEZADOS_EMPLEADOS,
        rows=MisEmpleadosState.empleados_paginados,
        row_renderer=fila_empleado,
        has_rows=MisEmpleadosState.total_empleados_filtrados > 0,
        empty_component=empty_state_card(
            title="No hay empleados registrados",
            description="Cree el primer empleado de esta empresa.",
            icon="users",
            action_button=rx.button(
                rx.icon("plus", size=16),
                "Nuevo Empleado",
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
    )


def filtros_empleados() -> rx.Component:
    """Filtros de la tabla de empleados."""
    return employee_filters_bar(
        rx.select.root(
            rx.select.trigger(placeholder="Estatus"),
            rx.select.content(
                rx.select.item("Activos", value="ACTIVO"),
                rx.select.item("Todos", value=FILTRO_TODOS),
            ),
            value=MisEmpleadosState.filtro_estatus_emp,
            on_change=MisEmpleadosState.set_filtro_estatus_emp,
            size="2",
        ),
        rx.button(
            rx.icon("filter", size=14),
            "Filtrar",
            on_click=MisEmpleadosState.aplicar_filtros_emp,
            variant="soft",
            size="2",
        ),
    )
