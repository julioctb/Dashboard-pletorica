import reflex as rx
from typing import Callable
from .cards import empty_state_card


def tabla_vacia(
    onclick: Callable = None,
    mensaje: str = "No hay registros guardados",
    submensaje: str = "",
) -> rx.Component:
    """Mensaje cuando no hay registros (legacy; preferir `empty_state_card`).

    Args:
        onclick: Callback para el botón de crear (si es None, no muestra botón)
        mensaje: Texto principal
        submensaje: Texto secundario debajo del mensaje
    """
    return empty_state_card(
        title=mensaje,
        description=submensaje or "Use el botón para crear el primer registro.",
        icon="inbox",
        action_button=rx.cond(
            onclick is not None,
            rx.button(
                rx.icon("plus", size=16),
                "Crear primer registro",
                on_click=onclick,
                color_scheme="blue",
            ),
            rx.fragment(),
        ),
    )
