import reflex as rx
from app.presentation.pages.empresas.empresas_state import EmpresasState
from app.presentation.components.empresas.empresa_card import empresa_card
from app.presentation.components.ui.cards import empty_state_card
from app.presentation.components.ui.skeletons import skeleton_empresa_grid


def empresas_grid() -> rx.Component:
    """
    Grid de empresas con skeleton loading y empty state.

    Muestra:
    - Skeleton loading (6 cards) mientras carga
    - Grid de empresas cuando hay resultados
    - Empty state cuando no hay resultados
    """
    return rx.vstack(
        # Loading state con SKELETONS (mejor UX que spinner)
        rx.cond(
            EmpresasState.loading,
            skeleton_empresa_grid(count=6)  # Mostrar 6 skeletons (2 filas de 3)
        ),

        # Lista de empresas (cuando NO está cargando)
        rx.cond(
            EmpresasState.loading == False,
            rx.cond(
                EmpresasState.empresas.length() > 0,
                rx.box(
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
                    width="100%",
                    style={
                        "minWidth": "100%",
                        "maxWidth": "100%"
                    }
                ),
                rx.box(
                    empty_state_card(
                        title="No se encontraron empresas",
                        description="Intente ajustar los filtros o crear una nueva empresa",
                        icon="building-2"
                    ),
                    min_height="400px",
                    width="100%",
                    display="flex",
                    align_items="center",
                    justify_content="center",
                    style={
                        "minWidth": "100%",
                        "maxWidth": "100%"
                    }
                )
            )
        ),

        spacing="4",
        width="100%"
    )
