import reflex as rx
from .states import EmpresasState

from app.components.ui.cards import empty_state_card
from app.components.modules.empresas.empresa_modals import modal_crear_empresa, modal_detalle_empresa, modal_editar_empresa 
from app.components.modules.empresas.empresa_card import empresa_card
from app.components.ui.filters import filtros_component

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
                modal_crear_empresa(),
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
        
        # Mensaje informativo
        rx.cond(
            EmpresasState.mensaje_info,
            rx.callout(
                EmpresasState.mensaje_info,
                icon=rx.cond(
                    EmpresasState.tipo_mensaje == "info", 
                    "info",
                    rx.cond(
                        EmpresasState.tipo_mensaje == "success",
                        "check",
                        "alert-triangle"
                    )
                ),
                color_scheme=rx.cond(
                    EmpresasState.tipo_mensaje == "info",
                    "blue",
                    rx.cond(
                        EmpresasState.tipo_mensaje == "success",
                        "green",
                        "red"
                    )
                ),
                size="2"
            )
        ),
        
        # Filtros
        filtros_component(EmpresasState),
        
        # Loading state
        rx.cond(
            EmpresasState.loading,
            rx.center(
                rx.spinner(size="3"),
                padding="4"
            )
        ),
        
        # Lista de empresas
        rx.cond(
            EmpresasState.loading == False,
            rx.cond(
                EmpresasState.empresas.length() > 0,
                rx.vstack(
                    rx.text(
                        f"Total: {EmpresasState.empresas.length()} empresas", 
                        size="2", 
                        color="var(--gray-9)"
                    ),
                    rx.grid(
                        rx.foreach(
                            EmpresasState.empresas,
                            lambda empresa: empresa_card(
                                empresa=empresa,
                                on_view=EmpresasState.abrir_modal_detalle,
                                on_edit=EmpresasState.abrir_modal_editar
                            )
                        ),
                        columns="3",
                        spacing="4",
                        width="100%"
                    ),
                    spacing="3",
                    width="100%"
                ),
                empty_state_card(
                    title="No se encontraron empresas",
                    description="Intente ajustar los filtros o crear una nueva empresa",
                    icon="building-2"
                )
            )
        ),
        
        # Modales
        modal_detalle_empresa(),
        modal_editar_empresa(),
        
        spacing="4",
        width="100%",
        padding="4",
        on_mount=EmpresasState.cargar_empresas
    )