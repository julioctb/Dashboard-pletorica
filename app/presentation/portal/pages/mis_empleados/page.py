"""
Pagina Mis Empleados del portal de cliente.

Muestra la lista de empleados de la empresa.
Permite busqueda, filtro por estatus y alta de nuevos empleados.
"""
import reflex as rx

from app.presentation.layout import page_layout, page_header, page_toolbar

from .state import MisEmpleadosState
from .components import tabla_empleados, filtros_empleados
from .modal import modal_empleado


def mis_empleados_page() -> rx.Component:
    """Pagina de lista de empleados del portal."""
    return rx.box(
        page_layout(
            header=page_header(
                titulo="Empleados",
                subtitulo="Empleados de la empresa",
                icono="users",
                accion_principal=rx.button(
                    rx.icon("plus", size=16),
                    "Nuevo Empleado",
                    on_click=MisEmpleadosState.abrir_modal_crear,
                    color_scheme="teal",
                ),
            ),
            toolbar=page_toolbar(
                search_value=MisEmpleadosState.filtro_busqueda_emp,
                search_placeholder="Buscar por nombre, clave o CURP...",
                on_search_change=MisEmpleadosState.set_filtro_busqueda_emp,
                on_search_clear=lambda: MisEmpleadosState.set_filtro_busqueda_emp(""),
                show_view_toggle=False,
                filters=filtros_empleados(),
            ),
            content=rx.vstack(
                tabla_empleados(),
                modal_empleado(),
                width="100%",
            ),
        ),
        width="100%",
        min_height="100vh",
        on_mount=MisEmpleadosState.on_mount_empleados,
    )
