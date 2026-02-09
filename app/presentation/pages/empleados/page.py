"""
Pagina principal de Empleados.
"""
import reflex as rx

from app.presentation.pages.empleados.empleados_state import EmpleadosState
from app.presentation.layout import page_layout, page_header, page_toolbar

from .components import tabla_empleados, grid_empleados, filtros_empleados
from .modals import (
    modal_empleado,
    modal_detalle_empleado,
    modal_baja,
    modal_restriccion,
    modal_liberacion,
    modal_historial_restricciones,
)


def empleados_page() -> rx.Component:
    """Pagina de Empleados usando el nuevo layout"""
    return rx.box(
        page_layout(
            header=page_header(
                titulo="Empleados",
                subtitulo="Administre los empleados del sistema",
                icono="users",
                accion_principal=rx.cond(
                    EmpleadosState.puede_operar_empleados,
                    rx.button(
                        rx.icon("plus", size=16),
                        "Nuevo Empleado",
                        on_click=EmpleadosState.abrir_modal_crear,
                        color_scheme="blue",
                    ),
                    rx.fragment(),
                ),
            ),
            toolbar=page_toolbar(
                search_value=EmpleadosState.filtro_busqueda,
                search_placeholder="Buscar por nombre, CURP o clave...",
                on_search_change=EmpleadosState.on_busqueda_change,
                on_search_clear=lambda: EmpleadosState.on_busqueda_change(""),
                filters=filtros_empleados(),
                show_view_toggle=True,
                current_view=EmpleadosState.view_mode,
                on_view_table=EmpleadosState.set_view_table,
                on_view_cards=EmpleadosState.set_view_cards,
            ),
            content=rx.vstack(
                # Contenido segun vista
                rx.cond(
                    EmpleadosState.is_table_view,
                    tabla_empleados(),
                    grid_empleados(),
                ),

                # Modales
                modal_empleado(),
                modal_detalle_empleado(),
                modal_baja(),
                modal_restriccion(),
                modal_liberacion(),
                modal_historial_restricciones(),

                spacing="4",
                width="100%",
            ),
        ),
        width="100%",
        min_height="100vh",
        on_mount=EmpleadosState.on_mount,
    )
