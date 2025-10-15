import reflex as rx
from typing import Optional, List, Any

def base_card(
    title: str,
    subtitle: Optional[str],
    badge: Optional[rx.Component] ,
    content: Optional[rx.Component] ,
    actions: Optional[rx.Component] ,
    icon: Optional[rx.Component] ,
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
    
    # Contenido principal con espaciado flexible
    card_content = rx.vstack(
        header,
        rx.cond(
            content,
            rx.box(content, flex="1", overflow_y="auto"),  # Content ocupa espacio disponible
            rx.box(flex="1")  # Espaciador si no hay contenido
        ),
        rx.cond(actions, actions, rx.fragment()),
        spacing="3",
        align="start",
        width="100%",
        height="100%"  # Ocupar toda la altura disponible
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