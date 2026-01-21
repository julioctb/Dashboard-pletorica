"""
Componente de Breadcrumb reutilizable.
"""
import reflex as rx
from typing import List, Optional
from app.presentation.theme import Colors


def breadcrumb_item(
    texto: str,
    href: Optional[str] = None,
    icono: Optional[str] = None,
    es_actual: bool = False,
) -> rx.Component:
    """
    Item individual del breadcrumb.

    Args:
        texto: Texto a mostrar
        href: URL de navegación (None si es el item actual)
        icono: Nombre del icono (opcional)
        es_actual: Si es el item actual (no clickeable)
    """
    contenido = rx.hstack(
        rx.cond(
            icono is not None,
            rx.icon(icono, size=14),
            rx.fragment(),
        ) if icono else rx.fragment(),
        rx.text(texto, size="2", weight="medium" if es_actual else "regular"),
        spacing="1",
        align="center",
    )

    if es_actual or href is None:
        return rx.text(texto, size="2", weight="medium", color=Colors.TEXT_PRIMARY)

    return rx.link(
        contenido,
        href=href,
        color=Colors.TEXT_SECONDARY,
        underline="none",
        _hover={"color": Colors.PRIMARY},
    )


def breadcrumb(items: List[dict]) -> rx.Component:
    """
    Componente de breadcrumb.

    Args:
        items: Lista de dicts con keys:
            - texto: str (requerido)
            - href: str (opcional, None para item actual)
            - icono: str (opcional)

    Ejemplo:
        breadcrumb([
            {"texto": "Inicio", "href": "/", "icono": "home"},
            {"texto": "Plazas", "href": "/plazas"},
            {"texto": "Vigilante", "href": None},  # Item actual
        ])
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
        *[
            rx.fragment(
                rx.text("/", color=Colors.TEXT_MUTED, size="2", padding_x="2"),
                rx.cond(
                    item.get("href") is not None,
                    rx.link(
                        rx.text(item["texto"], size="2"),
                        href=item.get("href", "#"),
                        color=Colors.TEXT_SECONDARY,
                        underline="none",
                        _hover={"color": Colors.PRIMARY},
                    ),
                    rx.text(item["texto"], size="2", weight="medium", color=Colors.TEXT_PRIMARY),
                ) if item.get("href") else rx.text(
                    item["texto"],
                    size="2",
                    weight="medium",
                    color=Colors.TEXT_PRIMARY
                ),
            )
            for item in items
        ],
        spacing="1",
        align="center",
        padding_y="2",
    )


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
