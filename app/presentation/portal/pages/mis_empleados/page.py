"""
Pagina Mis Empleados del portal de cliente.

Muestra la lista de empleados de la empresa.
Permite busqueda, filtro por estatus y alta de nuevos empleados.
"""
import reflex as rx

from app.presentation.layout import page_layout, page_header, page_toolbar
from app.presentation.components.reusable import employee_bulk_upload_panel

from .state import MisEmpleadosState
from .components import tabla_empleados, filtros_empleados
from .modal import (
    modal_baja,
    modal_detalle_empleado,
    modal_empleado,
    modal_historial_bancario,
)


def mis_empleados_page() -> rx.Component:
    """Pagina de lista de empleados del portal."""
    return rx.box(
        page_layout(
            header=page_header(
                titulo="Empleados",
                subtitulo="Empleados de la empresa actual",
                icono="users",
                accion_principal=rx.hstack(
                    rx.cond(
                        MisEmpleadosState.mostrar_panel_alta_masiva,
                        rx.button(
                            rx.icon("x", size=16),
                            "Cerrar alta masiva",
                            on_click=MisEmpleadosState.cerrar_panel_alta_masiva,
                            variant="soft",
                            color_scheme="gray",
                        ),
                        rx.button(
                            rx.icon("upload", size=16),
                            "Alta masiva",
                            on_click=MisEmpleadosState.abrir_panel_alta_masiva,
                            variant="outline",
                            color_scheme="teal",
                        ),
                    ),
                    rx.button(
                        rx.icon("plus", size=16),
                        "Nuevo Empleado",
                        on_click=MisEmpleadosState.abrir_modal_crear,
                        color_scheme="teal",
                    ),
                    spacing="2",
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
                employee_bulk_upload_panel(MisEmpleadosState),
                tabla_empleados(),
                modal_empleado(),
                modal_detalle_empleado(),
                modal_historial_bancario(),
                modal_baja(),
                width="100%",
                spacing="4",
            ),
        ),
        width="100%",
        min_height="100vh",
        on_mount=MisEmpleadosState.on_mount_empleados,
    )


def alta_masiva_redirect_page() -> rx.Component:
    """Ruta de compatibilidad que reenvía al panel inline de empleados."""
    return rx.center(
        rx.vstack(
            rx.spinner(size="3"),
            rx.text("Redirigiendo a empleados...", color="gray"),
            spacing="3",
            align="center",
        ),
        width="100%",
        min_height="40vh",
        on_mount=rx.redirect("/portal/empleados?alta_masiva=1", replace=True),
    )
