"""
Pagina Alta de Empleados (Onboarding) del portal de cliente.
"""
import reflex as rx

from app.presentation.layout import page_layout, page_header, page_toolbar

from .state import OnboardingAltaState
from .components import tabla_onboarding, filtros_onboarding
from .modal import modal_alta_empleado


def onboarding_alta_page() -> rx.Component:
    """Pagina de alta de empleados en onboarding."""
    return rx.box(
        page_layout(
            header=page_header(
                titulo="Alta de Empleados",
                subtitulo="Registro de nuevos empleados para onboarding",
                icono="user-plus",
                accion_principal=rx.button(
                    rx.icon("plus", size=16),
                    "Nuevo Empleado",
                    on_click=OnboardingAltaState.abrir_modal_alta,
                    color_scheme="teal",
                ),
            ),
            toolbar=page_toolbar(
                search_value=OnboardingAltaState.filtro_busqueda,
                search_placeholder="Buscar por nombre, clave o CURP...",
                on_search_change=OnboardingAltaState.set_filtro_busqueda,
                on_search_clear=lambda: OnboardingAltaState.set_filtro_busqueda(""),
                show_view_toggle=False,
                filters=filtros_onboarding(),
            ),
            content=rx.vstack(
                tabla_onboarding(),
                modal_alta_empleado(),
                width="100%",
            ),
        ),
        width="100%",
        min_height="100vh",
        on_mount=OnboardingAltaState.on_mount_onboarding_alta,
    )
