import reflex as rx
from typing import Callable
from .filters import input_busqueda
from .cards import empty_state_card
from .table_primitives import table_shell
from app.presentation.theme import Colors


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

def tabla(
    columnas: list[dict],
    lista: list[dict],
    filas: Callable,
    filtro_busqueda: rx.Var = None,
    on_change_busqueda: Callable = None,
    on_clear_busqueda: Callable = None,
    boton_derecho: rx.Component = None,
) -> rx.Component:
    """
    Tabla con búsqueda opcional (legacy; preferir `table_shell` y wrappers especializados).

    Args:
        columnas: Lista de columnas con 'nombre' y 'ancho'
        lista: Lista de datos a mostrar
        filas: Función para renderizar cada fila
        filtro_busqueda: Valor del input de búsqueda (opcional)
        on_change_busqueda: Handler al cambiar búsqueda (opcional)
        on_clear_busqueda: Handler al limpiar búsqueda (opcional)
        boton_derecho: Componente opcional a la derecha del input (opcional)
    """
    # Componentes de la tabla
    contenido = []

    # Agregar barra superior (búsqueda + botón derecho)
    if filtro_busqueda is not None and on_change_busqueda is not None:
        barra_items = [
            input_busqueda(
                value=filtro_busqueda,
                on_change=on_change_busqueda,
                on_clear=on_clear_busqueda,
            ),
        ]

        # Agregar spacer y botón si existe
        if boton_derecho is not None:
            barra_items.append(rx.spacer())
            barra_items.append(boton_derecho)

        contenido.append(
            rx.hstack(
                *barra_items,
                width="100%",
                align="center",
                padding_bottom="3",
            )
        )

    # Tabla
    contenido.append(
        table_shell(
            loading=False,
            headers=columnas,
            rows=lista,
            row_renderer=filas,
            has_rows=True,
            empty_component=rx.fragment(),
        )
    )

    return rx.card(
        rx.vstack(
            *contenido,
            spacing="3",
            width="100%",
        ),
        size='3',
        width='100%',
        background=Colors.SURFACE,
    )
