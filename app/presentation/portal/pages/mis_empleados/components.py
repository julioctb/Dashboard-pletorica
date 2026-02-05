"""
Componentes UI para la pagina Mis Empleados del portal.

Tabla, filtros y badges.
"""
import reflex as rx

from app.presentation.components.ui import skeleton_tabla
from app.presentation.theme import Colors, Typography, Spacing

from .state import MisEmpleadosState


def badge_estatus(estatus: str) -> rx.Component:
    """Badge de estatus del empleado."""
    return rx.match(
        estatus,
        ("ACTIVO", rx.badge("Activo", color_scheme="green", variant="soft", size="1")),
        ("INACTIVO", rx.badge("Inactivo", color_scheme="red", variant="soft", size="1")),
        ("SUSPENDIDO", rx.badge("Suspendido", color_scheme="orange", variant="soft", size="1")),
        rx.badge(estatus, size="1"),
    )


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
            rx.cond(
                puede_editar,
                rx.icon_button(
                    rx.icon("pencil", size=14),
                    variant="ghost",
                    size="1",
                    color_scheme="teal",
                    cursor="pointer",
                    on_click=MisEmpleadosState.abrir_modal_editar(emp),
                ),
                rx.fragment(),
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
    return rx.cond(
        MisEmpleadosState.loading,
        skeleton_tabla(columnas=ENCABEZADOS_EMPLEADOS, filas=5),
        rx.cond(
            MisEmpleadosState.total_empleados_lista > 0,
            rx.vstack(
                rx.table.root(
                    rx.table.header(
                        rx.table.row(
                            rx.foreach(
                                ENCABEZADOS_EMPLEADOS,
                                lambda col: rx.table.column_header_cell(
                                    col["nombre"],
                                    width=col["ancho"],
                                ),
                            ),
                        ),
                    ),
                    rx.table.body(
                        rx.foreach(
                            MisEmpleadosState.empleados_filtrados,
                            fila_empleado,
                        ),
                    ),
                    width="100%",
                    variant="surface",
                ),
                rx.text(
                    "Mostrando ",
                    MisEmpleadosState.total_empleados_lista,
                    " empleado(s)",
                    font_size=Typography.SIZE_SM,
                    color=Colors.TEXT_SECONDARY,
                ),
                width="100%",
                spacing="3",
            ),
            rx.center(
                rx.vstack(
                    rx.icon("users", size=48, color=Colors.TEXT_MUTED),
                    rx.text(
                        "No hay empleados registrados",
                        font_size=Typography.SIZE_LG,
                        color=Colors.TEXT_SECONDARY,
                    ),
                    spacing="3",
                    align="center",
                ),
                padding=Spacing.MD,
                width="100%",
            ),
        ),
    )


def filtros_empleados() -> rx.Component:
    """Filtros de la tabla de empleados."""
    return rx.hstack(
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
        spacing="3",
        align="center",
    )
