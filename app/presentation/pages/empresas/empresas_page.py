import reflex as rx
from app.presentation.pages.empresas.empresas_state import EmpresasState

from app.presentation.components.ui.filters import filtros_component
from app.presentation.components.empresas.empresa_modals import modal_empresa, modal_detalle_empresa
from app.presentation.components.empresas.empresa_grid import empresas_grid

def empresas_page() -> rx.Component:
    """Página principal de gestión de empresas"""
    return rx.vstack(
        # Header
        rx.hstack(
            rx.hstack(
                rx.icon("building-2", size=32, color="var(--blue-9)"),
                rx.vstack(
                    rx.text("Gestión de Empresas", size="6", weight="bold"),
                    rx.text("Administre las empresas del sistema", size="3", color="var(--gray-9)"),
                    align="start",
                    spacing="1"
                ),
                spacing="3",
                align="center"
            ),
            rx.spacer(),
            
            rx.hstack(
                rx.button(
                    rx.icon("plus", size=16),
                    "Nueva Empresa",
                    size="2",
                    on_click=EmpresasState.abrir_modal_crear
                ),
                rx.button(
                    rx.icon("refresh-cw", size=16),
                    "Actualizar",
                    on_click=EmpresasState.cargar_empresas,
                    variant="soft",
                    size="2"
                ),
                spacing="2"
            ),
            
            width="100%",
            align="center"
        ),
        
    
        
        # Filtros
        filtros_component(EmpresasState),

        # Grid de empresas
        empresas_grid(),

        # Modales
        modal_empresa(),
        modal_detalle_empresa(),
        
        spacing="4",
        width="100%",
        padding="4",
        on_mount=EmpresasState.cargar_empresas
    )