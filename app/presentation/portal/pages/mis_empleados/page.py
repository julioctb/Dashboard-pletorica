"""
Pagina Mis Empleados del portal de cliente.

Muestra la lista de empleados de la empresa.
Permite busqueda, filtro por estatus y alta de nuevos empleados.
"""
import reflex as rx

from app.presentation.layout import page_layout, page_header, page_toolbar
from app.presentation.components.reusable import employee_bulk_upload_panel
from app.presentation.portal.pages.expedientes.components import (
    modal_panel_expediente,
    modal_preview_documento,
    modal_rechazo,
)

from .state import MisEmpleadosState
from .components import (
    filtro_contrato_empleados,
    filtros_estatus_empleados,
    metricas_empleados,
    selector_vista_personal,
    tabla_empleados,
    tabla_plazas_por_contrato,
)
from .modal import (
    modal_asignacion_plaza,
    modal_baja,
    modal_detalle_empleado,
    modal_empleado,
    modal_historial_bancario,
)


def mis_empleados_page() -> rx.Component:
    """Pagina de lista de empleados del portal."""
    return rx.box(
        rx.box(
            page_layout(
                header=page_header(
                    titulo="Empleados",
                    subtitulo=MisEmpleadosState.subtitulo_empleados,
                    icono="users",
                    accion_principal=rx.hstack(
                        rx.button(
                            rx.icon("upload", size=16),
                            "Alta masiva",
                            on_click=MisEmpleadosState.abrir_panel_alta_masiva,
                            variant="outline",
                            color_scheme="teal",
                        ),
                        rx.button(
                            rx.icon("plus", size=16),
                            "Nuevo empleado",
                            on_click=MisEmpleadosState.abrir_modal_crear,
                            color_scheme="teal",
                        ),
                        spacing="2",
                    ),
                ),
                toolbar=page_toolbar(
                    search_value=MisEmpleadosState.filtro_busqueda_emp,
                    search_placeholder=MisEmpleadosState.placeholder_busqueda_personal,
                    on_search_change=MisEmpleadosState.set_filtro_busqueda_emp,
                    on_search_clear=lambda: MisEmpleadosState.set_filtro_busqueda_emp(""),
                    filters=filtro_contrato_empleados(),
                    extra_right=selector_vista_personal(),
                    show_view_toggle=False,
                    wrapped=False,
                    compact=True,
                    search_min_width="0px",
                    search_max_width=None,
                    search_flex="1 1 0px",
                ),
                content=rx.vstack(
                    metricas_empleados(),
                    rx.cond(
                        MisEmpleadosState.vista_es_empleado,
                        filtros_estatus_empleados(),
                        rx.fragment(),
                    ),
                    rx.cond(
                        MisEmpleadosState.vista_es_empleado,
                        employee_bulk_upload_panel(MisEmpleadosState),
                        rx.fragment(),
                    ),
                    rx.cond(
                        MisEmpleadosState.vista_es_empleado,
                        tabla_empleados(),
                        tabla_plazas_por_contrato(),
                    ),
                    modal_empleado(),
                    modal_asignacion_plaza(),
                    modal_detalle_empleado(),
                    modal_historial_bancario(),
                    modal_baja(),
                    modal_panel_expediente(),
                    modal_preview_documento(),
                    modal_rechazo(),
                    width="100%",
                    spacing="4",
                ),
            ),
            width="100%",
            max_width="900px",
            margin_x="auto",
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
