"""
View Toggle - Toggle de Vista Tabla/Cards
==========================================

Componente para cambiar entre vista de tabla y vista de cards.

Los metodos set_view_table, set_view_cards, toggle_view, is_table_view
e is_cards_view estan definidos en BaseState. Solo necesitas declarar
la variable `view_mode: str = "table"` en tu State.

Uso:
    from app.presentation.components.ui import view_toggle

    class MiState(BaseState):
        view_mode: str = "table"
        # Los metodos de view toggle se heredan de BaseState

    # En tu componente:
    view_toggle(
        value=MiState.view_mode,
        on_change_table=MiState.set_view_table,
        on_change_cards=MiState.set_view_cards,
    )
"""

import reflex as rx
from app.presentation.theme import Colors, Transitions


def view_toggle(
    value: str,
    on_change_table: callable,
    on_change_cards: callable,
    size: str = "2",
) -> rx.Component:
    """
    Toggle visual para cambiar entre tabla y cards.
    
    Args:
        value: Valor actual ("table" o "cards")
        on_change_table: Callback al seleccionar tabla
        on_change_cards: Callback al seleccionar cards
        size: Tamaño de los botones ("1", "2", "3")
    
    Returns:
        Componente de toggle con dos botones
    """
    return rx.hstack(
        # Botón Tabla
        rx.tooltip(
            rx.icon_button(
                rx.icon("list", size=18),
                size=size,
                variant=rx.cond(value == "table", "solid", "ghost"),
                color_scheme=rx.cond(value == "table", "blue", "gray"),
                on_click=on_change_table,
                cursor="pointer",
                style={
                    "transition": Transitions.FAST,
                },
            ),
            content="Vista de tabla",
        ),
        
        # Botón Cards
        rx.tooltip(
            rx.icon_button(
                rx.icon("layout-grid", size=18),
                size=size,
                variant=rx.cond(value == "cards", "solid", "ghost"),
                color_scheme=rx.cond(value == "cards", "blue", "gray"),
                on_click=on_change_cards,
                cursor="pointer",
                style={
                    "transition": Transitions.FAST,
                },
            ),
            content="Vista de tarjetas",
        ),
        
        spacing="1",
        padding="4px",
        background=Colors.SECONDARY_LIGHT,
        border_radius="8px",
    )
