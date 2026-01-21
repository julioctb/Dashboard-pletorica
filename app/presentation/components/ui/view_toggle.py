"""
View Toggle - Toggle de Vista Tabla/Cards
==========================================

Componente para cambiar entre vista de tabla y vista de cards.

IMPORTANTE: Reflex no soporta mixins para State. Debes agregar
los campos y métodos directamente en tu clase State.

Uso:
    from app.presentation.components.ui import view_toggle
    
    # 1. En tu State, agrega estos campos y métodos:
    class MiState(rx.State):
        view_mode: str = "table"  # "table" o "cards"
        
        def set_view_table(self):
            self.view_mode = "table"
        
        def set_view_cards(self):
            self.view_mode = "cards"
        
        @rx.var
        def is_table_view(self) -> bool:
            return self.view_mode == "table"
        
        @rx.var
        def is_cards_view(self) -> bool:
            return self.view_mode == "cards"
    
    # 2. En tu componente:
    view_toggle(
        value=MiState.view_mode,
        on_change_table=MiState.set_view_table,
        on_change_cards=MiState.set_view_cards,
    )
"""

import reflex as rx
from app.presentation.theme import Colors, Transitions


# =============================================================================
# CAMPOS Y MÉTODOS PARA COPIAR A TU STATE
# =============================================================================
# 
# Copia esto directamente en tu clase State:
#
# class MiState(rx.State):
#     view_mode: str = "table"
#     
#     def set_view_table(self):
#         self.view_mode = "table"
#     
#     def set_view_cards(self):
#         self.view_mode = "cards"
#     
#     def toggle_view(self):
#         self.view_mode = "cards" if self.view_mode == "table" else "table"
#     
#     @rx.var
#     def is_table_view(self) -> bool:
#         return self.view_mode == "table"
#     
#     @rx.var
#     def is_cards_view(self) -> bool:
#         return self.view_mode == "cards"
#
# =============================================================================


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


def view_toggle_with_label(
    value: str,
    on_change_table: callable,
    on_change_cards: callable,
    label: str = "Vista:",
) -> rx.Component:
    """
    Toggle con etiqueta descriptiva.
    
    Args:
        value: Valor actual ("table" o "cards")
        on_change_table: Callback al seleccionar tabla
        on_change_cards: Callback al seleccionar cards
        label: Texto de etiqueta
    """
    return rx.hstack(
        rx.text(
            label,
            font_size="14px",
            color=Colors.TEXT_SECONDARY,
            font_weight="500",
        ),
        view_toggle(
            value=value,
            on_change_table=on_change_table,
            on_change_cards=on_change_cards,
        ),
        spacing="2",
        align="center",
    )


def view_toggle_segmented(
    value: str,
    on_change_table: callable,
    on_change_cards: callable,
) -> rx.Component:
    """
    Versión segmentada (estilo tabs) del toggle.
    
    Más prominente visualmente, ideal para colocar solo.
    """
    return rx.hstack(
        # Opción Tabla
        rx.box(
            rx.hstack(
                rx.icon("list", size=16),
                rx.text("Tabla", font_weight="500"),
                spacing="2",
                align="center",
            ),
            padding_x="12px",
            padding_y="8px",
            background=rx.cond(
                value == "table",
                Colors.PRIMARY,
                "transparent"
            ),
            color=rx.cond(
                value == "table",
                Colors.TEXT_INVERSE,
                Colors.TEXT_SECONDARY
            ),
            border_radius="6px",
            cursor="pointer",
            transition=Transitions.FAST,
            on_click=on_change_table,
            style={
                "_hover": {
                    "background": rx.cond(
                        value == "table",
                        Colors.PRIMARY_HOVER,
                        Colors.SECONDARY_LIGHT
                    ),
                },
            },
        ),
        
        # Opción Cards
        rx.box(
            rx.hstack(
                rx.icon("layout-grid", size=16),
                rx.text("Tarjetas", font_weight="500"),
                spacing="2",
                align="center",
            ),
            padding_x="12px",
            padding_y="8px",
            background=rx.cond(
                value == "cards",
                Colors.PRIMARY,
                "transparent"
            ),
            color=rx.cond(
                value == "cards",
                Colors.TEXT_INVERSE,
                Colors.TEXT_SECONDARY
            ),
            border_radius="6px",
            cursor="pointer",
            transition=Transitions.FAST,
            on_click=on_change_cards,
            style={
                "_hover": {
                    "background": rx.cond(
                        value == "cards",
                        Colors.PRIMARY_HOVER,
                        Colors.SECONDARY_LIGHT
                    ),
                },
            },
        ),
        
        spacing="1",
        padding="4px",
        background=Colors.SURFACE,
        border=f"1px solid {Colors.BORDER}",
        border_radius="8px",
    )