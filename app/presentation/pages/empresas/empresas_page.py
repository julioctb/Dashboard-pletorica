import reflex as rx
from app.presentation.pages.empresas.empresas_state import EmpresasState

from app.presentation.components.ui.headers import page_header
from app.presentation.components.empresas.empresa_filters import empresa_filters
from app.presentation.components.empresas.empresa_modals import modal_empresa, modal_detalle_empresa
from app.presentation.components.empresas.empresa_grid import empresas_grid

def empresas_page() -> rx.Component:
    """Página principal de gestión de empresas"""
    return rx.vstack(
        # Header con botón integrado
        page_header(
            icono="building-2",
            titulo="Gestión de empresas",
            subtitulo="Administre las empresas del sistema",
            icono_boton="plus",
            texto_boton="Nueva Empresa",
            onclick=EmpresasState.abrir_modal_crear,
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
        min_width="100%",
        on_mount=EmpresasState.cargar_empresas
    )