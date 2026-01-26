import reflex as rx
from typing import Callable
from .filters import input_busqueda


def tabla_vacia(
    onclick: Callable = None,
    mensaje: str = "No hay registros guardados",
    submensaje: str = "",
) -> rx.Component:
    """Mensaje cuando no hay registros.

    Args:
        onclick: Callback para el botón de crear (si es None, no muestra botón)
        mensaje: Texto principal
        submensaje: Texto secundario debajo del mensaje
    """
    items = [
        rx.icon("inbox", size=48, color="gray"),
        rx.text(mensaje, color="gray", size="3"),
    ]

    if submensaje:
        items.append(
            rx.text(submensaje, color="gray", size="2", text_align="center", max_width="400px")
        )

    if onclick is not None:
        items.append(
            rx.button(
                rx.icon("plus", size=16),
                "Crear primer registro",
                on_click=onclick,
                color_scheme="blue",
            )
        )

    return rx.center(
        rx.vstack(
            *items,
            spacing="3",
            align="center",
            padding="8",
        ),
        width="100%",
        min_height="200px",
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
    Tabla con búsqueda opcional.

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
        rx.table.root(
            rx.table.header(
                rx.table.row(
                    rx.foreach(
                        columnas,
                        lambda h: rx.table.column_header_cell(
                            h['nombre'],
                            width=h.get('ancho', 'auto'),
                        ),
                    )
                ),
            ),
            rx.table.body(
                rx.foreach(
                    lista,
                    filas
                ),
            ),
            width="100%",
            variant="surface",
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
    )