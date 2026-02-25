import reflex as rx
from typing import Optional

from app.presentation.theme import Colors


def empty_state_card(
    title: str,
    description: str,
    icon: str = "inbox",
    action_button: Optional[rx.Component] = None,
) -> rx.Component:
    """Tarjeta reutilizable para estados vacíos."""
    return rx.center(
        rx.vstack(
            rx.icon(icon, size=48, color=Colors.TEXT_MUTED),
            rx.text(title, size="4", color=Colors.TEXT_SECONDARY, weight="medium"),
            rx.text(description, size="2", color=Colors.TEXT_MUTED, text_align="center"),
            rx.cond(action_button, action_button, rx.fragment()),
            spacing="3",
            align="center",
            max_width="300px",
        ),
        padding="8",
        width="100%",
    )
