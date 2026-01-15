import reflex as rx
from app.presentation.pages.empresas.empresas_state import EmpresasState

from app.presentation.components.ui.headers import page_header

def estatus_badge(estatus: str) -> rx.Component:
    """Badge de estatus con color"""
    return rx.badge(
        estatus,
        color_scheme=rx.cond(
            estatus == "ACTIVO",
            "green",
            "red"
        ),
        size="1",
    )

def boton_accion(
    icon: str,
    on_click: callable,
    tooltip: str,
    color_scheme: str = "gray",
    disabled: bool = False,
) -> rx.Component:
    """Botón de acción con icono y tooltip"""
    return rx.tooltip(
        rx.icon_button(
            rx.icon(icon, size=16),
            size="1",
            variant="ghost",
            color_scheme=color_scheme,
            on_click=on_click,
            disabled=disabled,
            cursor="pointer",
        ),
        content=tooltip,
    )




def tabla_empresas() -> rx.Component:
    """Tabla de tipos de empresas"""
    return rx.data_table(
        data= EmpresasState.empresas,
        columns=EmpresasState.empresas_columnas,
        width="100%",
        variant="surface",
    )

def empresas_page2() -> rx.Component:
    """Página principal de gestión de empresas"""
    return rx.vstack(
        # Header
        rx.hstack(
            page_header(
                icono="building-2",
                titulo="Gestión de empresas 2",
                subtitulo="Administre las empresas del sistema"
            ),

            rx.spacer(),

            tabla_empresas(),

            width="100%",
            align="center"
        ),


    )

