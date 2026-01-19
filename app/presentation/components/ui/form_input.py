"""Componentes de formulario reutilizables."""
import reflex as rx
from typing import Optional, Any, List


def form_input(
    placeholder: str,
    value: rx.Var,
    on_change: callable,
    on_blur: callable = None,
    error: rx.Var = None,
    max_length: int = None,
    **props
) -> rx.Component:
    """Input de formulario con manejo de errores."""
    return rx.vstack(
        rx.input(
            placeholder=placeholder,
            value=value,
            on_change=on_change,
            on_blur=on_blur,
            max_length=max_length,
            width="100%",
            **props
        ),
        rx.cond(
            error,
            rx.text(error, color="red", size="1"),
            rx.text("", size="1")  # Espacio reservado
        ),
        spacing="1",
        width="100%",
        align_items="stretch"
    )


def form_textarea(
    placeholder: str,
    value: rx.Var,
    on_change: callable,
    on_blur: callable = None,
    error: rx.Var = None,
    max_length: int = None,
    rows: str = "3",
    **props
) -> rx.Component:
    """Textarea de formulario con manejo de errores."""
    return rx.vstack(
        rx.text_area(
            placeholder=placeholder,
            value=value,
            on_change=on_change,
            on_blur=on_blur,
            max_length=max_length,
            width="100%",
            rows=rows,
            **props
        ),
        rx.cond(
            error,
            rx.text(error, color="red", size="1"),
            rx.text("", size="1")
        ),
        spacing="1",
        width="100%",
        align_items="stretch"
    )


def form_select(
    placeholder: str,
    value: rx.Var,
    on_change: callable,
    options: list,
    error: rx.Var = None,
    **props
) -> rx.Component:
    """
    Select de formulario con manejo de errores.

    Args:
        placeholder: Texto placeholder del select
        value: Variable de estado con el valor seleccionado
        on_change: Callback al cambiar selección
        options: Lista de dicts [{"label": "Texto", "value": "valor"}, ...]
        error: Variable con mensaje de error (opcional)
    """
    return rx.vstack(
        rx.select.root(
            rx.select.trigger(placeholder=placeholder, width="100%"),
            rx.select.content(
                rx.foreach(
                    options,
                    lambda opt: rx.select.item(opt["label"], value=opt["value"])
                ),
            ),
            value=value,
            on_change=on_change,
            **props
        ),
        rx.cond(
            error,
            rx.text(error, color="red", size="1"),
            rx.text("", size="1")
        ),
        spacing="1",
        width="100%",
        align_items="stretch"
    )
