"""
Componentes de botones de acción reutilizables para tablas y cards.

Estilos centralizados para consistencia en toda la aplicación.

Uso:
    from app.presentation.components.ui.action_buttons import (
        tabla_action_button,
        tabla_action_buttons,
    )

    # Botón individual
    tabla_action_button(
        icon="eye",
        tooltip="Ver detalle",
        on_click=State.ver(item["id"]),
    )

    # Botón condicional
    tabla_action_button(
        icon="pencil",
        tooltip="Editar",
        on_click=State.editar(item["id"]),
        color_scheme="blue",
        visible=(item["estado"] == "ACTIVO") & State.puede_editar,
    )

    # Grupo de botones
    tabla_action_buttons([
        tabla_action_button("eye", "Ver", State.ver(id)),
        tabla_action_button("pencil", "Editar", State.editar(id), color_scheme="blue"),
    ])
"""

import reflex as rx
from typing import Any, List, Optional, Union


# =============================================================================
# CONSTANTES DE ESTILO (Centralizadas)
# =============================================================================

# Tamaño del botón (Radix size: "1", "2", "3", "4")
ACTION_BUTTON_SIZE = "2"

# Tamaño del icono en pixels
ACTION_ICON_SIZE = 16

# Variante del botón ("solid", "soft", "surface", "outline", "ghost")
ACTION_BUTTON_VARIANT = "soft"

# Espaciado entre botones en un grupo
ACTION_BUTTONS_SPACING = "2"


# =============================================================================
# COMPONENTE PRINCIPAL
# =============================================================================

def tabla_action_button(
    icon: str,
    tooltip: str,
    on_click: Any,
    color_scheme: str = "gray",
    visible: Any = True,
    disabled: Any = False,
) -> rx.Component:
    """
    Botón de acción para tablas con estilo consistente.

    Args:
        icon: Nombre del icono (lucide icons)
        tooltip: Texto del tooltip
        on_click: Handler del click (lambda o evento)
        color_scheme: Color del botón (gray, blue, green, red, orange, purple, teal)
        visible: Condición de visibilidad (bool, rx.Var, o expresión)
        disabled: Condición de deshabilitado (bool o rx.Var)

    Returns:
        Componente rx.tooltip con rx.icon_button

    Example:
        tabla_action_button(
            icon="eye",
            tooltip="Ver detalle",
            on_click=lambda: State.ver(item["id"]),
        )

        tabla_action_button(
            icon="trash-2",
            tooltip="Eliminar",
            on_click=lambda: State.eliminar(item["id"]),
            color_scheme="red",
            visible=item["puede_eliminar"],
        )
    """
    button = rx.tooltip(
        rx.icon_button(
            rx.icon(icon, size=ACTION_ICON_SIZE),
            size=ACTION_BUTTON_SIZE,
            variant=ACTION_BUTTON_VARIANT,
            color_scheme=color_scheme,
            on_click=on_click,
            disabled=disabled,
        ),
        content=tooltip,
    )

    # Manejar visibilidad
    if isinstance(visible, rx.Var) or hasattr(visible, '_var_name'):
        return rx.cond(visible, button, rx.fragment())
    elif visible is False:
        return rx.fragment()
    return button


def tabla_action_buttons(
    buttons: List[rx.Component],
    spacing: str = ACTION_BUTTONS_SPACING,
) -> rx.Component:
    """
    Contenedor para grupo de botones de acción.

    Args:
        buttons: Lista de componentes (usar tabla_action_button)
        spacing: Espaciado entre botones (default: "2")

    Returns:
        rx.hstack con los botones

    Example:
        tabla_action_buttons([
            tabla_action_button("eye", "Ver", State.ver(id)),
            tabla_action_button("pencil", "Editar", State.editar(id), color_scheme="blue"),
            tabla_action_button("trash-2", "Eliminar", State.eliminar(id), color_scheme="red"),
        ])
    """
    return rx.hstack(
        *buttons,
        spacing=spacing,
        justify="center",
        align="center",
    )


# =============================================================================
# FUNCIONES LEGACY (Mantener compatibilidad)
# =============================================================================

def action_button_config(
    icon: str,
    tooltip: str,
    on_click: Any,
    color_scheme: str = "gray",
    visible: Any = True,
    size: str = ACTION_BUTTON_SIZE,
) -> dict:
    """
    DEPRECATED: Usar tabla_action_button() en su lugar.

    Crea configuración para un botón de acción.
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
    """Renderiza un botón de acción individual (legacy)."""
    button = rx.tooltip(
        rx.icon_button(
            rx.icon(config["icon"], size=ACTION_ICON_SIZE),
            size=config.get("size", ACTION_BUTTON_SIZE),
            variant=ACTION_BUTTON_VARIANT,
            color_scheme=config["color_scheme"],
            cursor="pointer",
            on_click=config["on_click"],
        ),
        content=config["tooltip"],
    )

    if isinstance(config["visible"], rx.Var):
        return rx.cond(config["visible"], button, rx.fragment())
    elif config["visible"] is False:
        return rx.fragment()
    return button


def action_buttons(
    configs: List[dict],
    spacing: str = ACTION_BUTTONS_SPACING,
) -> rx.Component:
    """
    DEPRECATED: Usar tabla_action_buttons() con tabla_action_button() en su lugar.

    Renderiza un grupo de botones de acción.
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
    Usa los nuevos estilos centralizados.

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
                    rx.icon("eye", size=ACTION_ICON_SIZE),
                    size=ACTION_BUTTON_SIZE,
                    variant=ACTION_BUTTON_VARIANT,
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
                rx.icon("pencil", size=ACTION_ICON_SIZE),
                size=ACTION_BUTTON_SIZE,
                variant=ACTION_BUTTON_VARIANT,
                color_scheme="blue",
                cursor="pointer",
                on_click=editar_action,
            ),
            content="Editar",
        )
        if isinstance(puede_editar, rx.Var) or hasattr(puede_editar, '_var_name'):
            botones.append(rx.cond(puede_editar, edit_btn, rx.fragment()))
        elif puede_editar:
            botones.append(edit_btn)

    if eliminar_action is not None:
        del_btn = rx.tooltip(
            rx.icon_button(
                rx.icon("trash-2", size=ACTION_ICON_SIZE),
                size=ACTION_BUTTON_SIZE,
                variant=ACTION_BUTTON_VARIANT,
                color_scheme="red",
                cursor="pointer",
                on_click=eliminar_action,
            ),
            content="Eliminar",
        )
        if isinstance(puede_eliminar, rx.Var) or hasattr(puede_eliminar, '_var_name'):
            botones.append(rx.cond(puede_eliminar, del_btn, rx.fragment()))
        elif puede_eliminar:
            botones.append(del_btn)

    if acciones_extra:
        botones.extend(acciones_extra)

    return rx.hstack(
        *botones,
        spacing=ACTION_BUTTONS_SPACING,
        align="center",
        justify="center",
    )
