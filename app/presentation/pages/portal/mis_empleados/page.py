"""
Pagina Mis Empleados del portal de cliente.

Muestra la lista de empleados de la empresa.
Permite busqueda, filtro por estatus y alta de nuevos empleados.
"""
import reflex as rx

from app.presentation.layouts.backoffice import page_layout, page_header
from app.presentation.components.reusable import employee_bulk_upload_panel
from app.presentation.components.ui import skeleton_tabla
from app.presentation.theme import CardStyles, Colors, Radius, Spacing
from app.presentation.pages.portal.incapacidades import modal_registro_incapacidad

from .state import MisEmpleadosState
from .components import (
    ENCABEZADOS_EMPLEADOS,
    filtro_contrato_empleados,
    filtros_estatus_empleados,
    metricas_empleados,
    tabla_empleados,
)
from .modal import (
    modal_baja,
    modal_detalle_empleado,
    modal_empleado,
    modal_historial_bancario,
)


def _metric_skeleton() -> rx.Component:
    return rx.card(
        rx.vstack(
            rx.skeleton(width="110px", height="14px"),
            rx.skeleton(width="72px", height="30px"),
            rx.skeleton(width="140px", height="10px"),
            spacing="2",
            align_items="center",
            width="100%",
        ),
        width="100%",
        style={**CardStyles.BASE},
    )


def _contenido_loading() -> rx.Component:
    return rx.vstack(
        rx.grid(
            *[_metric_skeleton() for _ in range(5)],
            grid_template_columns="repeat(5, minmax(0, 1fr))",
            gap=Spacing.SM,
            width="100%",
        ),
        rx.flex(
            rx.skeleton(height="36px", border_radius=Radius.LG, flex="1", min_width="180px"),
            rx.skeleton(width="120px", height="36px", border_radius=Radius.MD),
            rx.skeleton(width="100px", height="36px", border_radius=Radius.MD),
            rx.skeleton(width="130px", height="36px", border_radius=Radius.MD),
            gap=Spacing.SM,
            align="center",
            width="100%",
        ),
        rx.hstack(
            rx.skeleton(width="180px", height="28px", border_radius=Radius.FULL),
            rx.skeleton(width="100px", height="28px", border_radius=Radius.FULL),
            rx.skeleton(width="100px", height="28px", border_radius=Radius.FULL),
            rx.skeleton(width="100px", height="28px", border_radius=Radius.FULL),
            spacing="2",
            wrap="wrap",
            width="100%",
        ),
        skeleton_tabla(columnas=ENCABEZADOS_EMPLEADOS, filas=6),
        spacing="4",
        width="100%",
    )


def _contenido_principal() -> rx.Component:
    return rx.cond(
        MisEmpleadosState.loading,
        _contenido_loading(),
        rx.vstack(
            metricas_empleados(),
            filtro_contrato_empleados(),
            filtros_estatus_empleados(),
            employee_bulk_upload_panel(MisEmpleadosState),
            tabla_empleados(),
            spacing="4",
            width="100%",
        ),
    )


def mis_empleados_page() -> rx.Component:
    """Pagina de lista de empleados del portal."""
    return rx.box(
        page_layout(
            header=page_header(
                titulo="Empleados",
                subtitulo_compuesto=rx.text(
                    MisEmpleadosState.nombre_empresa + " — Plantilla y gestión de personal",
                    size="3",
                    color=Colors.TEXT_SECONDARY,
                ),
                icono="users",
                color_icono=Colors.PORTAL_ACCENT_SCHEME,
                accion_principal=rx.hstack(
                    rx.button(
                        rx.icon("upload", size=16),
                        "Alta masiva",
                        on_click=MisEmpleadosState.abrir_panel_alta_masiva,
                        variant="outline",
                        color_scheme=Colors.PORTAL_ACCENT_SCHEME,
                    ),
                    rx.button(
                        rx.icon("plus", size=16),
                        "Nuevo empleado",
                        on_click=MisEmpleadosState.abrir_modal_crear,
                        color_scheme=Colors.PORTAL_ACCENT_SCHEME,
                    ),
                    spacing="2",
                ),
            ),
            content=rx.vstack(
                _contenido_principal(),
                modal_empleado(),
                modal_detalle_empleado(),
                modal_historial_bancario(),
                modal_baja(),
                modal_registro_incapacidad(),
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
