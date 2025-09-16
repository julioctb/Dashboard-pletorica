import reflex as rx
from typing import Optional, List, Any

def base_card(
    title: str,
    subtitle: Optional[str] = None,
    badge: Optional[rx.Component] = None,
    content: Optional[rx.Component] = None,
    actions: Optional[rx.Component] = None,
    icon: Optional[rx.Component] = None,
    max_width: str = "400px",
    hover_effect: bool = True
) -> rx.Component:
    """
    Tarjeta base reutilizable para todo el sistema
    
    Args:
        title: Título principal de la tarjeta
        subtitle: Subtítulo opcional 
        badge: Badge/etiqueta (ej: tipo, estatus)
        content: Contenido principal de la tarjeta
        actions: Botones de acción
        icon: Icono opcional para el header
        max_width: Ancho máximo de la tarjeta
        hover_effect: Si aplicar efecto hover
    """
    
    # Header de la tarjeta
    header = rx.hstack(
        rx.hstack(
            rx.cond(icon, icon, rx.fragment()),
            rx.vstack(
                rx.text(title, size="4", weight="bold"),
                rx.cond(
                    subtitle,
                    rx.text(subtitle, size="2", color="var(--gray-9)"),
                    rx.fragment()
                ),
                align="start",
                spacing="1"
            ),
            spacing=rx.cond(icon, "2", "0"),
            align="center"
        ),
        rx.spacer(),
        rx.cond(badge, badge, rx.fragment()),
        width="100%",
        align="center"
    )
    
    # Contenido principal
    card_content = rx.vstack(
        header,
        rx.cond(content, content, rx.fragment()),
        rx.cond(actions, actions, rx.fragment()),
        spacing="3",
        align="start",
        width="100%"
    )
    
    # Aplicar hover effect si está habilitado
    hover_props = {
        "_hover": {"cursor": "pointer", "bg": "var(--gray-2)"}
    } if hover_effect else {}
    
    return rx.card(
        card_content,
        width="100%",
        max_width=max_width,
        **hover_props
    )

def info_card(
    title: str,
    value: str,
    icon: str,
    color_scheme: str = "blue",
    size: str = "sm"
) -> rx.Component:
    """
    Tarjeta de información estadística
    
    Args:
        title: Título de la métrica
        value: Valor a mostrar
        icon: Nombre del icono
        color_scheme: Esquema de color
        size: Tamaño (sm, md, lg)
    """
    
    icon_size = {"sm": 16, "md": 20, "lg": 24}[size]
    title_size = {"sm": "2", "md": "3", "lg": "4"}[size]
    value_size = {"sm": "4", "md": "5", "lg": "6"}[size]
    
    return rx.card(
        rx.hstack(
            rx.icon(
                icon, 
                size=icon_size, 
                color=f"var(--{color_scheme}-9)"
            ),
            rx.vstack(
                rx.text(title, size=title_size, color="var(--gray-9)"),
                rx.text(value, size=value_size, weight="bold"),
                align="start",
                spacing="1"
            ),
            spacing="3",
            align="center"
        ),
        width="100%"
    )

def list_card(
    title: str,
    items: List[str],
    icon: Optional[str] = None,
    max_items: int = 5,
    show_count: bool = True
) -> rx.Component:
    """
    Tarjeta para mostrar listas de elementos
    
    Args:
        title: Título de la lista
        items: Lista de elementos a mostrar
        icon: Icono opcional
        max_items: Máximo número de items a mostrar
        show_count: Si mostrar el contador total
    """
    
    # Mostrar solo los primeros max_items
    visible_items = items[:max_items]
    remaining_count = len(items) - max_items
    
    return rx.card(
        rx.vstack(
            # Header
            rx.hstack(
                rx.cond(icon, rx.icon(icon, size=20), rx.fragment()),
                rx.text(title, size="3", weight="bold"),
                rx.spacer(),
                rx.cond(
                    show_count,
                    rx.badge(str(len(items)), color_scheme="gray"),
                    rx.fragment()
                ),
                width="100%",
                align="center"
            ),
            
            # Lista de items
            rx.vstack(
                rx.foreach(
                    visible_items,
                    lambda item: rx.hstack(
                        rx.icon("circle", size=6, color="var(--gray-6)"),
                        rx.text(item, size="2"),
                        spacing="2",
                        align="center"
                    )
                ),
                
                # Mostrar "y X más" si hay elementos restantes
                rx.cond(
                    remaining_count > 0,
                    rx.text(
                        f"y {remaining_count} más...",
                        size="2",
                        color="var(--gray-7)",
                        style={"font-style": "italic"}
                    ),
                    rx.fragment()
                ),
                
                spacing="2",
                align="start",
                width="100%"
            ),
            
            spacing="3",
            align="start",
            width="100%"
        ),
        width="100%"
    )

def action_card(
    title: str,
    description: str,
    action_text: str,
    on_click: Any,
    icon: str = "plus",
    color_scheme: str = "blue"
) -> rx.Component:
    """
    Tarjeta de acción (ej: "Crear nueva empresa")
    
    Args:
        title: Título de la acción
        description: Descripción de la acción
        action_text: Texto del botón
        on_click: Función a ejecutar
        icon: Icono del botón
        color_scheme: Esquema de color
    """
    
    return rx.card(
        rx.vstack(
            rx.vstack(
                rx.text(title, size="4", weight="bold"),
                rx.text(description, size="2", color="var(--gray-9)"),
                align="center",
                spacing="2"
            ),
            
            rx.button(
                rx.icon(icon, size=16),
                action_text,
                on_click=on_click,
                color_scheme=color_scheme,
                size="2"
            ),
            
            spacing="4",
            align="center",
            padding="4"
        ),
        width="100%",
        text_align="center",
        _hover={"cursor": "pointer", "transform": "translateY(-2px)"},
        transition="all 0.2s ease"
    )

def empty_state_card(
    title: str,
    description: str,
    icon: str = "inbox",
    action_button: Optional[rx.Component] = None
) -> rx.Component:
    """
    Tarjeta para estados vacíos
    
    Args:
        title: Título del estado vacío
        description: Descripción del estado
        icon: Icono a mostrar
        action_button: Botón de acción opcional
    """
    
    return rx.center(
        rx.vstack(
            rx.icon(icon, size=48, color="var(--gray-6)"),
            rx.text(title, size="4", color="var(--gray-9)", weight="medium"),
            rx.text(description, size="2", color="var(--gray-7)", text_align="center"),
            rx.cond(action_button, action_button, rx.fragment()),
            spacing="3",
            align="center",
            max_width="300px"
        ),
        padding="8",
        width="100%"
    )