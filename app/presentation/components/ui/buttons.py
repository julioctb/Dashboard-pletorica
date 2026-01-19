import reflex as rx
from typing import Callable


def boton_accion(
    icon: str,
    on_click: callable,
    tooltip: str,
    color_scheme: str = "gray",
    disabled: bool = False,
) -> rx.Component:
    """Botón de acción con icono y tooltip"""
    return rx.tooltip(
        rx.icon_button(
            rx.icon(icon, size=16),
            size="1",
            variant="ghost",
            color_scheme=color_scheme,
            on_click=on_click,
            disabled=disabled,
            cursor="pointer",
        ),
        content=tooltip,
    )


def acciones_crud(
    item: dict,
    on_editar: Callable,
    on_eliminar: Callable,
    on_reactivar: Callable,
    campo_estatus: str = "estatus",
    valor_activo: str = "ACTIVO",
) -> rx.Component:
    """
    Botones de acciones CRUD estándar: Editar, Eliminar/Reactivar.

    Args:
        item: Diccionario con los datos del registro
        on_editar: Función al hacer click en editar
        on_eliminar: Función al hacer click en eliminar (solo si activo)
        on_reactivar: Función al hacer click en reactivar (solo si inactivo)
        campo_estatus: Nombre del campo de estatus en el diccionario
        valor_activo: Valor que indica estatus activo
    """
    return rx.hstack(
        boton_accion(
            icon="pencil",
            on_click=lambda: on_editar(item),
            tooltip="Editar",
            color_scheme="blue",
        ),
        rx.cond(
            item[campo_estatus] == valor_activo,
            boton_accion(
                icon="trash-2",
                on_click=lambda: on_eliminar(item),
                tooltip="Eliminar",
                color_scheme="red",
            ),
            boton_accion(
                icon="rotate-ccw",
                on_click=lambda: on_reactivar(item),
                tooltip="Reactivar",
                color_scheme="green",
            ),
        ),
        spacing="1",
    )
