"""Componentes genéricos de headers para páginas"""
import reflex as rx

from typing import Callable
from app.presentation.theme import Colors, Typography

def page_header(
    icono: str | None,
    titulo: str,
    *,
    subtitulo: str = "",
    icono_boton: str = "",
    texto_boton: str = "",
    onclick: Callable | None = None,
    accion_principal: rx.Component | None = None,
) -> rx.Component:
    """
    Header de página con título, subtítulo y botón opcional.

    Args:
        icono: Nombre del icono del título
        titulo: Texto del título
        subtitulo: Texto opcional del subtítulo
        icono_boton: Icono del botón (vacío = sin icono, API legacy)
        texto_boton: Texto del botón (vacío = sin botón, API legacy)
        onclick: Función al hacer click en el botón (API legacy)
        accion_principal: Componente de acción ya construido (API nueva)
    """
    return rx.hstack(
        # Bloque de Título e Icono
        rx.hstack(
            rx.cond(
                icono is not None,
                rx.center(
                    rx.icon(icono, size=28, color=Colors.PRIMARY),
                    width="48px",
                    height="48px",
                    background=Colors.PRIMARY_LIGHT,
                    border_radius="12px",
                ),
                rx.fragment(),
            ),
            rx.vstack(
                rx.text(titulo, size="6", weight="bold"),
                rx.cond(
                    subtitulo != "",
                    rx.text(
                        subtitulo,
                        size="3",
                        color=Colors.TEXT_SECONDARY,
                    ),
                    rx.fragment()
                ),
                spacing="1",
                align_items="start",
            ),
            spacing="4",
            align="center"
        ),

        rx.spacer(),

        rx.cond(
            accion_principal is not None,
            accion_principal,
            rx.cond(
                texto_boton != "",
                rx.button(
                    rx.cond(
                        icono_boton != "",
                        rx.icon(icono_boton if icono_boton else "circle", size=16),
                        rx.fragment(),
                    ),
                    texto_boton if texto_boton else "",
                    on_click=onclick,
                    size="2",
                    variant="soft",
                    cursor="pointer"
                ),
                rx.fragment()
            ),
        ),
        width="100%",
        align="center",
        padding_y="4",
    )
