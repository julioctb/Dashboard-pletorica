import reflex as rx
from app.presentation.pages.empresas.empresas_state import EmpresasState
from app.presentation.components.empresas.empresa_card import empresa_card
from app.presentation.components.ui.cards import empty_state_card


def empresas_grid() -> rx.Component:
    """Grid de empresas con loading y empty state"""
    return rx.vstack(
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

        spacing="4",
        width="100%"
    )
