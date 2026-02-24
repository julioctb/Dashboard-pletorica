import reflex as rx
from typing import Optional


def empty_state_card(
    title: str,
    description: str,
    icon: str = "inbox",
    action_button: Optional[rx.Component] = None,
) -> rx.Component:
    """Tarjeta reutilizable para estados vacíos."""
    return rx.center(
        rx.vstack(
            rx.icon(icon, size=48, color="var(--gray-6)"),
            rx.text(title, size="4", color="var(--gray-9)", weight="medium"),
            rx.text(description, size="2", color="var(--gray-7)", text_align="center"),
            rx.cond(action_button, action_button, rx.fragment()),
            spacing="3",
            align="center",
            max_width="300px",
        ),
        padding="8",
        width="100%",
    )
