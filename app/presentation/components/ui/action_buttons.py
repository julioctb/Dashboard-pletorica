"""
Componentes de botones de acción reutilizables para tablas y cards.

Uso:
    from app.presentation.components.ui import action_buttons, action_button_config

    # Configuración de acciones
    acciones = [
        action_button_config("eye", "Ver detalle", State.ver_detalle(item["id"])),
        action_button_config("pencil", "Editar", State.editar(item["id"]),
                            visible=item["estatus"] == "ACTIVO"),
        action_button_config("trash-2", "Eliminar", State.confirmar_eliminar(item["id"]),
                            color_scheme="red", visible=item["puede_eliminar"]),
    ]

    action_buttons(acciones)
"""

import reflex as rx
from typing import Any, List, Optional



def action_button_config(
    icon: str,
    tooltip: str,
    on_click: Any,
    color_scheme: str = "gray",
    visible: Any = True,
    size: str = "1",
) -> dict:
    """
    Crea configuración para un botón de acción.

    Args:
        icon: Nombre del icono (lucide)
        tooltip: Texto del tooltip
        on_click: Handler del click
        color_scheme: Esquema de color (gray, red, blue, green, etc.)
        visible: Condición de visibilidad (bool o rx.Var)
        size: Tamaño del botón ("1", "2", etc.)

    Returns:
        Dict con la configuración del botón
    """
    return {
        "icon": icon,
        "tooltip": tooltip,
        "on_click": on_click,
        "color_scheme": color_scheme,
        "visible": visible,
        "size": size,
    }


def _render_action_button(config: dict) -> rx.Component:
    """Renderiza un botón de acción individual."""
    button = rx.tooltip(
        rx.icon_button(
            rx.icon(config["icon"], size=14),
            size=config["size"],
            variant="ghost",
            color_scheme=config["color_scheme"],
            cursor="pointer",
            on_click=config["on_click"],
        ),
        content=config["tooltip"],
    )

    # Si visible es un rx.Var, usar rx.cond
    if isinstance(config["visible"], rx.Var):
        return rx.cond(config["visible"], button, rx.fragment())
    # Si es False estático, no renderizar
    elif config["visible"] is False:
        return rx.fragment()
    # Si es True o cualquier otro valor truthy, renderizar
    return button


def action_buttons(
    configs: List[dict],
    spacing: str = "1",
) -> rx.Component:
    """
    Renderiza un grupo de botones de acción.

    Args:
        configs: Lista de configuraciones creadas con action_button_config()
        spacing: Espaciado entre botones

    Returns:
        Componente con los botones de acción

    Example:
        action_buttons([
            action_button_config("eye", "Ver", State.ver(id)),
            action_button_config("pencil", "Editar", State.editar(id)),
        ])
    """
    return rx.hstack(
        *[_render_action_button(config) for config in configs],
        spacing=spacing,
        align="center",
    )


def action_buttons_reactive(
    item: rx.Var,
    ver_action: Optional[Any] = None,
    editar_action: Optional[Any] = None,
    eliminar_action: Optional[Any] = None,
    puede_editar: Any = True,
    puede_eliminar: Any = False,
    acciones_extra: List[rx.Component] = None,
) -> rx.Component:
    """
    Versión simplificada para acciones comunes (ver, editar, eliminar).

    Args:
        item: Variable reactiva del item
        ver_action: Handler para ver detalle (opcional)
        editar_action: Handler para editar (opcional)
        eliminar_action: Handler para eliminar (opcional)
        puede_editar: Condición para mostrar botón editar
        puede_eliminar: Condición para mostrar botón eliminar
        acciones_extra: Lista de componentes adicionales

    Example:
        action_buttons_reactive(
            item=emp,
            ver_action=State.ver_detalle(emp["id"]),
            editar_action=State.editar(emp["id"]),
            puede_editar=emp["estatus"] == "ACTIVO",
        )
    """
    botones = []

    if ver_action is not None:
        botones.append(
            rx.tooltip(
                rx.icon_button(
                    rx.icon("eye", size=14),
                    size="1",
                    variant="ghost",
                    color_scheme="gray",
                    cursor="pointer",
                    on_click=ver_action,
                ),
                content="Ver detalle",
            )
        )

    if editar_action is not None:
        edit_btn = rx.tooltip(
            rx.icon_button(
                rx.icon("pencil", size=14),
                size="1",
                variant="ghost",
                color_scheme="gray",
                cursor="pointer",
                on_click=editar_action,
            ),
            content="Editar",
        )
        if isinstance(puede_editar, rx.Var):
            botones.append(rx.cond(puede_editar, edit_btn, rx.fragment()))
        elif puede_editar:
            botones.append(edit_btn)

    if eliminar_action is not None:
        del_btn = rx.tooltip(
            rx.icon_button(
                rx.icon("trash-2", size=14),
                size="1",
                variant="ghost",
                color_scheme="red",
                cursor="pointer",
                on_click=eliminar_action,
            ),
            content="Eliminar",
        )
        if isinstance(puede_eliminar, rx.Var):
            botones.append(rx.cond(puede_eliminar, del_btn, rx.fragment()))
        elif puede_eliminar:
            botones.append(del_btn)

    if acciones_extra:
        botones.extend(acciones_extra)

    return rx.hstack(
        *botones,
        spacing="1",
        align="center",
        justify="center",
    )
