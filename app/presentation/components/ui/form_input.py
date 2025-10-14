import reflex as rx

from typing import Optional, Any, List


def form_input(
        placeholder: str,
        value: Any,
        on_change: Any,
        on_blur: Optional[Any] = None,
        error: Any = ''

) -> rx.Component:
    '''
    Entrada de datos para formulario con opcion de validación.

    Args:
        placeholder: texto que se muestra dentro del campo
        value: recibe la información del campo en el formulario
        on_change: maneja cuando el campo del formulario cambia
        on_blur: Función de validación que se ejecuta al perder el foco (opcional)
        error: Mensaje de error a mostrar debajo del input (opcional)

    Returns:
        Componente rx.vstack conteniendo un input y, si existe error,
        un mensaje de error en texto rojo debajo del input.
    
    '''
    return rx.vstack(
        rx.input(
            placeholder=placeholder,
            value=value,
            on_change=on_change,
            on_blur=on_blur,
            size="2",
            width="100%"
        ),
        rx.cond(
            error != "",
            rx.text(
                error,
                color="red",
                size="1"
            )
        ),
        spacing="1",
        width="100%"
    )

def form_select(
        label: str,
        options: List[str],
        value: Any,
        on_change: Any
) -> rx.Component:
    '''
    Campo de entrada tipo select con opciones

    Args:
        label: texto de guia para la etiqueta del campo,
        options: listado de valores a seleccionar,
        value: recibe la informacion del campo en el formulario,
        on_change: Función callback ejecutada al cambiar el valor

    Returns:
        Componente rx.vstack con label arriba y rx.Select con lista de valores

    '''
    return rx.vstack(
        rx.text(
            label,
            size="2",
            weight="medium"
        ),
        rx.select(
            options,
            value=value,
            on_change=on_change,
            size="2",
            width="100%"
        ),
        align="start",
        spacing="1",
        width="100%"
    )


def form_textarea(
        label: str,
        placeholder: str,
        value: Any,
        on_change: Any,
        rows: int = 4
) -> rx.Component:
    '''
    Entrada de texto multilínea para formulario con label.

    Args:
        label: Texto de etiqueta visible arriba del campo
        placeholder: Texto que se muestra dentro del campo
        value: Recibe la información del campo en el formulario
        on_change: Maneja cuando el campo del formulario cambia
        rows: Número de filas visibles (default 4)

    Returns:
        Componente rx.vstack conteniendo label y textarea
    '''
    return rx.vstack(
        rx.text(
            label,
            size="2",
            weight="medium"
        ),
        rx.text_area(
            placeholder=placeholder,
            value=value,
            on_change=on_change,
            size="2",
            width="100%",
            rows=str(rows)
        ),
        spacing="1",
        width="100%",
        align="start"
    )