import reflex as rx
from reflex.components.radix.themes.base import LiteralAccentColor

from typing import List

chip_props = {
    'radius': 'full',
    'variant': 'surface',
    'size': '3',
    'cursor': 'pointer',
    'style': {'_hover': {'opacity': 0.75}}
}

class BasicChipState(rx.State):
    
    selected_items: List[str]

    @rx.event
    def add_selected(self, item: str):
        self.selected_items.append(item)

    @rx.event
    def remove_selected(self, item: str):
        self.selected_items.remove(item)

    @rx.event
    def add_all_selected(self, lista: List):
        self.selected_items = lista

    @rx.event
    def clear_selected(self):
        self.selected_items.clear()

def action_button(
        icon: str,
        label: str,
        on_click: callable,
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

def selected_item_chip(item: str) -> rx.Component:
    return rx.badge(
        item,
        rx.icon('circle-x', size=18),
        **chip_props,
        on_click=BasicChipState.remove_selected(item)
    )

def unselected_item_chip(item: str) -> rx.Component:
    return rx.cond(
        BasicChipState.selected_items.contains(item),
        rx.fragment(),
        rx.badge(
            item,
            rx.icon('cirlcle-plus', size=18),
            color_scheme='gray',
            **chip_props,
            on_click=BasicChipState.add_selected(item)
        )
    )

def item_selector(icon: str, header: str) -> rx.Component:
    return rx.vstack(
        rx.flex(
            rx.hstack(
                rx.icon(icon,size=20),
                rx.heading(
                    header,
                    + f"({BasicChipState.selected_items.length()})",
                    size='4'
                    ),
                spacing='1',
                align='center',
                width='100%',
                justify_content=['end','start']    
            ),
            rx.hstack(
                action_button(
                    'plus',
                    'Añadir todos',
                    BasicChipState.add_all_selected,
                    'green'
                )
            ),
            rx.hstack(
                action_button(
                    'trash',
                    'Quitar todos',
                    BasicChipState.clear_selected,
                    'tomato'
                )
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

        #TODO arreglar las indentaciones
    ),
rx.divider(),
# items sin seleccionar
rx.flex(
    rx.foreach(
        BasicChipState.selected_items,
        selected_item_chip,        
    ),
    wrap='wrap',
    spacing='2',
    justify_content='start'
)

