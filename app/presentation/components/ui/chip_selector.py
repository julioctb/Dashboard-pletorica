import reflex as rx
from reflex import Var
from reflex.components.radix.themes.base import LiteralAccentColor

from typing import List, Callable


chip_props = {
    'radius': 'full',
    'variant': 'surface',
    'size': '3',
    'cursor': 'pointer',
    'style': {'_hover': {'opacity': 0.75}}
}

def action_button(
        icon: str,
        label: str,
        on_click: Callable,
        color_scheme: LiteralAccentColor
) -> rx.Component:
    return rx.button(
        rx.icon(icon, size='16'),
        label,
        variant='soft',
        size='2',
        on_click=on_click,
        color_scheme=color_scheme,
        cursor='pointer'
    )

def chip_selector(
        icon:str,
        header: str,
        all_items: List[str],
        selected_items: Var[List[str]],
        on_add: Callable,
        on_remove: Callable,
        on_add_all: Callable,
        on_clear: Callable
) -> rx.Component:
    #Helpers internos

    def selected_item_chip(item: str) -> rx.Component:
        return rx.badge(
            item,
            rx.icon('circle-x', size=18),
            **chip_props,
            on_click= lambda: on_remove(item)
        )

    def unselected_item_chip(item: str) -> rx.Component:
        return rx.cond(
            selected_items.contains(item),
            rx.fragment(),
            rx.badge(
                item,
                rx.icon('circle-plus', size=18),
                color_scheme='gray',
                **chip_props,
                on_click=lambda: on_add(item)
            )
        )

    return rx.vstack(
        #header
        rx.flex(
            rx.hstack(
                rx.icon(icon,size=20),
                rx.heading(
                    header + f"({selected_items.length()})",
                    size='4'
                    ),
                spacing='1',
                align='center',
                width='100%',
                justify_content=['end','start']    
            ),
            #Botones
            rx.hstack(
                action_button(
                    'plus',
                    'Añadir todos',
                    on_add_all,
                    'green'
                ),
                action_button(
                    'trash',
                    'Quitar todos',
                    on_clear,
                    'tomato'
                ),
                spacing='2',
                justify='end',
                width='100%'
            ),
            justify='between',
            flex_direction=['column','row'],
            align='center',
            spacing='2',
            margin_bottom='10px',
            width='100%'
        ),
        #items seleccionados
        rx.flex(
            rx.foreach(
                selected_items,
                selected_item_chip,
            ),
            wrap="wrap",
            spacing="2",
            justify_content="start",
        ),
        rx.divider(),
        #items sin seleccionar
        rx.flex(
            rx.foreach(
                all_items,
                unselected_item_chip
            ),
            wrap="wrap",
            spacing="2",
            justify_content="start",
        ),
        justify_content="start",
        align_items="start",
        width="100%"
    )

