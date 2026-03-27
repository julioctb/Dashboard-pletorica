"""Componente reutilizable para patrón select + agregar + lista acumulada."""

import reflex as rx

from app.presentation.components.ui.form_input import (
    _render_footer,
    _render_label,
    select_items_from_options,
)
from app.presentation.theme import Colors


def accumulating_select(
    *,
    label: str,
    placeholder: str,
    value,
    on_change,
    options,
    on_add,
    can_add,
    add_button_text: str = "Agregar",
    selected_items,
    render_selected_item,
    empty_message: str = "Sin elementos seleccionados",
    error=None,
    hint: str = "",
) -> rx.Component:
    """Renderiza un selector acumulativo reutilizable para listas pequeñas/medias."""
    return rx.vstack(
        _render_label(label, error=error),
        rx.hstack(
            rx.box(
                rx.select.root(
                    rx.select.trigger(
                        placeholder=placeholder,
                        width="100%",
                    ),
                    rx.select.content(select_items_from_options(options)),
                    value=value,
                    on_change=on_change,
                ),
                flex="1",
                min_width="0",
                width="100%",
            ),
            rx.button(
                rx.icon("plus", size=14),
                add_button_text,
                on_click=on_add,
                disabled=~can_add,
                variant="soft",
                size="2",
                flex_shrink="0",
            ),
            width="100%",
            align="end",
            spacing="2",
        ),
        _render_footer(error, hint),
        rx.cond(
            selected_items.length() > 0,
            rx.vstack(
                rx.foreach(selected_items, render_selected_item),
                width="100%",
                spacing="2",
            ),
            rx.text(
                empty_message,
                size="1",
                color=Colors.TEXT_MUTED,
                width="100%",
            ),
        ),
        width="100%",
        spacing="2",
    )
