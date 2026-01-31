"""
Componente de Breadcrumb reutilizable.
"""
import reflex as rx
from typing import List
from app.presentation.theme import Colors


def breadcrumb_dynamic(items: rx.Var[List[dict]]) -> rx.Component:
    """
    Breadcrumb dinámico que acepta una lista reactiva de items.

    Args:
        items: rx.Var con lista de dicts:
            - texto: str
            - href: str o None
    """
    return rx.hstack(
        rx.link(
            rx.hstack(
                rx.icon("home", size=14),
                rx.text("Inicio", size="2"),
                spacing="1",
                align="center",
            ),
            href="/",
            color=Colors.TEXT_SECONDARY,
            underline="none",
            _hover={"color": Colors.PRIMARY},
        ),
        rx.foreach(
            items,
            lambda item: rx.hstack(
                rx.text("/", color=Colors.TEXT_MUTED, size="2"),
                rx.cond(
                    item["href"] != "",
                    rx.link(
                        rx.text(item["texto"], size="2"),
                        href=item["href"],
                        color=Colors.TEXT_SECONDARY,
                        underline="none",
                        _hover={"color": Colors.PRIMARY},
                    ),
                    rx.text(
                        item["texto"],
                        size="2",
                        weight="medium",
                        color=Colors.TEXT_PRIMARY,
                    ),
                ),
                spacing="2",
                align="center",
            ),
        ),
        spacing="1",
        align="center",
        padding_y="2",
    )
