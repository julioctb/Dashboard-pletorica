"""
Componentes UI para la pagina Mis Empleados del portal.

Tabla, filtros y badges.
"""
import reflex as rx

from app.presentation.components.ui import (
    tabla_action_button,
    empty_state_card,
    employee_status_badge,
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
            tabla_action_button(
                icon="pencil",
                tooltip="Editar",
                on_click=MisEmpleadosState.abrir_modal_editar(emp),
                color_scheme="teal",
                visible=puede_editar,
            ),
        ),
    )


ENCABEZADOS_EMPLEADOS = [
    {"nombre": "Clave", "ancho": "120px"},
    {"nombre": "Nombre", "ancho": "auto"},
    {"nombre": "CURP", "ancho": "200px"},
    {"nombre": "Estatus", "ancho": "100px"},
    {"nombre": "Acciones", "ancho": "80px"},
]


def tabla_empleados() -> rx.Component:
    """Tabla de empleados."""
    return employee_table(
        loading=MisEmpleadosState.loading,
        headers=ENCABEZADOS_EMPLEADOS,
        rows=MisEmpleadosState.empleados_filtrados,
        row_renderer=fila_empleado,
        has_rows=MisEmpleadosState.total_empleados_lista > 0,
        empty_component=empty_state_card(
            title="No hay empleados registrados",
            description="Cree el primer empleado para esta empresa.",
            icon="users",
        ),
        total_caption="Mostrando "
        + MisEmpleadosState.total_empleados_lista.to(str)
        + " empleado(s)",
        loading_rows=5,
    )


def filtros_empleados() -> rx.Component:
    """Filtros de la tabla de empleados."""
    return employee_filters_bar(
        rx.select.root(
            rx.select.trigger(placeholder="Estatus"),
            rx.select.content(
                rx.select.item("Activos", value="ACTIVO"),
                rx.select.item("Todos", value="TODOS"),
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
