import reflex as rx
from app.presentation.pages.empresas.empresas_state import EmpresasState

from app.presentation.components.ui.headers import page_header
from app.presentation.components.empresas.empresa_filters import empresa_filters
from app.presentation.components.empresas.empresa_modals import modal_empresa, modal_detalle_empresa
from app.presentation.components.empresas.empresa_grid import empresas_grid

def empresas_page() -> rx.Component:
    """Página principal de gestión de empresas"""
    return rx.vstack(
        # Header
        rx.hstack(
            page_header(
                icono="building-2",
                titulo="Gestión de empresas",
                subtitulo="Administre las empresas del sistema"
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
        empresa_filters(EmpresasState),

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