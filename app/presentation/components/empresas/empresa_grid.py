import reflex as rx
from app.presentation.pages.empresas.empresas_state import EmpresasState
from app.presentation.components.empresas.empresa_card import empresa_card
from app.presentation.components.ui.cards import empty_state_card
from app.presentation.components.ui.skeletons import skeleton_empresa_grid


def empresas_grid() -> rx.Component:
    """
    Grid de empresas con skeleton loading y empty state.

    Mejoras:
    - Skeleton loading (6 cards) mientras carga
    - Grid responsive (1 col mobile, 2 tablet, 3 desktop)
    - Contador con contexto de filtros activos
    - Empty state con CTA cuando no hay filtros
    """
    return rx.vstack(
        # Estado: LOADING o LOADED
        rx.cond(
            EmpresasState.loading,
            # LOADING: Mostrar skeletons
            skeleton_empresa_grid(count=6),
            # LOADED: Mostrar grid o empty state
            rx.cond(
                EmpresasState.empresas.length() > 0,
                # Caso A: HAY EMPRESAS
                rx.vstack(
                    # Contador con contexto de filtros
                    rx.cond(
                        EmpresasState.tiene_filtros_activos,
                        rx.text(
                            f"Mostrando {EmpresasState.empresas.length()} empresas ({EmpresasState.cantidad_filtros_activos} filtros activos)",
                            size="2",
                            color="var(--gray-9)"
                        ),
                        rx.text(
                            f"Total: {EmpresasState.empresas.length()} empresas",
                            size="2",
                            color="var(--gray-9)"
                        )
                    ),
                    # Grid responsive
                    rx.grid(
                        rx.foreach(
                            EmpresasState.empresas,
                            lambda empresa: empresa_card(
                                empresa=empresa,
                                on_view=EmpresasState.abrir_modal_detalle,
                                on_edit=EmpresasState.abrir_modal_editar
                            )
                        ),
                        columns=rx.breakpoints(initial="1", sm="2", lg="3", xl="4"),
                        spacing="4",
                        width="100%"
                    ),
                    spacing="3",
                    width="100%"
                ),
                # Caso B: LISTA VACÍA
                rx.box(
                    rx.vstack(
                        empty_state_card(
                            title="No se encontraron empresas",
                            description=rx.cond(
                                EmpresasState.tiene_filtros_activos,
                                "Intente ajustar los filtros para ver más resultados",
                                "No hay empresas registradas. Cree la primera empresa para comenzar"
                            ),
                            icon="building-2"
                        ),
                        # Botón CTA cuando no hay filtros
                        rx.cond(
                            EmpresasState.tiene_filtros_activos == False,
                            rx.button(
                                rx.icon("plus", size=16),
                                "Crear primera empresa",
                                size="3",
                                on_click=EmpresasState.abrir_modal_crear
                            )
                        ),
                        spacing="4",
                        align="center"
                    ),
                    min_height="400px",
                    width="100%",
                    display="flex",
                    align_items="center",
                    justify_content="center"
                )
            )
        ),

        spacing="4",
        width="100%"
    )
