"""Componentes de formulario reutilizables con labels visibles."""
import reflex as rx
from typing import Any


# =============================================================================
# HELPERS INTERNOS
# =============================================================================

def _render_label(label: str, required: bool = False, error: Any = None) -> rx.Component:
    """Renderiza label encima del input. Cambia a rojo si hay error."""
    if not label:
        return rx.fragment()

    parts = [label]
    if required:
        parts.append(rx.text.span(" *", color="var(--red-9)"))

    color = "var(--gray-11)"
    if error is not None:
        color = rx.cond(error != "", "var(--red-9)", "var(--gray-11)")

    return rx.text(
        *parts,
        size="2",
        weight="medium",
        color=color,
    )


def _render_footer(error: Any = None, hint: str = "") -> rx.Component:
    """Renderiza error (prioridad) o hint debajo del input."""
    if error is not None and hint:
        return rx.cond(
            error != "",
            rx.text(error, color="var(--red-9)", size="1"),
            rx.text(hint, size="1", color="var(--gray-9)"),
        )
    elif error is not None:
        return rx.cond(
            error != "",
            rx.text(error, color="var(--red-9)", size="1"),
            rx.text("", size="1"),
        )
    elif hint:
        return rx.text(hint, size="1", color="var(--gray-9)")
    else:
        return rx.text("", size="1")


# =============================================================================
# COMPONENTES DE FORMULARIO
# =============================================================================

def form_input(
    placeholder: str = "",
    value: Any = "",
    on_change: callable = None,
    on_blur: callable = None,
    error: Any = None,
    max_length: int = None,
    label: str = "",
    required: bool = False,
    hint: str = "",
    **props
) -> rx.Component:
    """
    Input de formulario con label visible y manejo de errores.

    Args:
        placeholder: Texto placeholder dentro del input
        value: Variable de estado con el valor actual
        on_change: Callback al cambiar valor
        on_blur: Callback al perder foco (para validacion)
        error: Variable con mensaje de error (opcional)
        max_length: Longitud maxima permitida
        label: Texto del label visible encima del input
        required: Si True, muestra asterisco rojo en el label
        hint: Texto de ayuda debajo del input (error tiene prioridad)
        **props: Props adicionales para rx.input (type, disabled, step, min, etc.)
    """
    return rx.vstack(
        _render_label(label, required, error),
        rx.input(
            placeholder=placeholder,
            value=value,
            on_change=on_change,
            on_blur=on_blur,
            max_length=max_length,
            width="100%",
            **props
        ),
        _render_footer(error, hint),
        spacing="1",
        width="100%",
        align_items="stretch",
    )


def form_textarea(
    placeholder: str = "",
    value: Any = "",
    on_change: callable = None,
    on_blur: callable = None,
    error: Any = None,
    max_length: int = None,
    rows: str = "3",
    label: str = "",
    required: bool = False,
    hint: str = "",
    **props
) -> rx.Component:
    """
    Textarea de formulario con label visible y manejo de errores.

    Args:
        placeholder: Texto placeholder dentro del textarea
        value: Variable de estado con el valor actual
        on_change: Callback al cambiar valor
        on_blur: Callback al perder foco
        error: Variable con mensaje de error (opcional)
        max_length: Longitud maxima permitida
        rows: Numero de filas visibles
        label: Texto del label visible encima del textarea
        required: Si True, muestra asterisco rojo en el label
        hint: Texto de ayuda debajo del textarea
    """
    return rx.vstack(
        _render_label(label, required, error),
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
        _render_footer(error, hint),
        spacing="1",
        width="100%",
        align_items="stretch",
    )


def form_select(
    placeholder: str = "",
    value: Any = "",
    on_change: callable = None,
    options: list = None,
    error: Any = None,
    label: str = "",
    required: bool = False,
    hint: str = "",
    **props
) -> rx.Component:
    """
    Select de formulario con label visible y manejo de errores.

    Args:
        placeholder: Texto placeholder del select
        value: Variable de estado con el valor seleccionado
        on_change: Callback al cambiar seleccion
        options: Lista de dicts [{"label": "Texto", "value": "valor"}, ...]
        error: Variable con mensaje de error (opcional)
        label: Texto del label visible encima del select
        required: Si True, muestra asterisco rojo en el label
        hint: Texto de ayuda debajo del select
    """
    if options is None:
        options = []

    return rx.vstack(
        _render_label(label, required, error),
        rx.select.root(
            rx.select.trigger(placeholder=placeholder, width="100%"),
            rx.select.content(
                rx.foreach(
                    options,
                    lambda opt: rx.select.item(opt["label"], value=opt["value"]),
                ),
            ),
            value=value,
            on_change=on_change,
            **props
        ),
        _render_footer(error, hint),
        spacing="1",
        width="100%",
        align_items="stretch",
    )


def form_date(
    label: str = "",
    value: Any = "",
    on_change: callable = None,
    error: Any = None,
    required: bool = False,
    hint: str = "",
    **props
) -> rx.Component:
    """
    Input de fecha con label visible y manejo de errores.

    Args:
        label: Texto del label visible encima del input
        value: Variable de estado con la fecha (formato YYYY-MM-DD)
        on_change: Callback al cambiar fecha
        error: Variable con mensaje de error (opcional)
        required: Si True, muestra asterisco rojo en el label
        hint: Texto de ayuda debajo del input
    """
    return rx.vstack(
        _render_label(label, required, error),
        rx.input(
            type="date",
            value=value,
            on_change=on_change,
            width="100%",
            **props
        ),
        _render_footer(error, hint),
        spacing="1",
        width="100%",
        align_items="stretch",
    )


def form_row(*children) -> rx.Component:
    """
    Pone campos de formulario en fila (columnas lado a lado).

    Uso:
        form_row(
            form_input(label="Nombre", ...),
            form_input(label="RFC", ...),
        )
    """
    return rx.hstack(
        *children,
        spacing="2",
        width="100%",
    )
