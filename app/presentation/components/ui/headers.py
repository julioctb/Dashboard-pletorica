"""Componentes genéricos de headers para páginas"""
import reflex as rx

from typing import Callable

def page_header(
    icono: str,
    titulo: str,
    *,
    subtitulo: str = "",
    icono_boton: str = "",
    texto_boton: str = "",
    onclick: Callable | None = None,
) -> rx.Component:
    """
    Header de página con título, subtítulo y botón opcional.

    Args:
        icono: Nombre del icono del título
        titulo: Texto del título
        subtitulo: Texto opcional del subtítulo
        icono_boton: Icono del botón (vacío = sin icono)
        texto_boton: Texto del botón (vacío = sin botón)
        onclick: Función al hacer click en el botón
    """
    return rx.hstack(
        # Bloque de Título e Icono
        rx.hstack(
            rx.icon(icono, size=32, color="var(--blue-9)"),
                rx.text(titulo, size="6", weight="bold"),
                rx.cond(
                    subtitulo != "",
                    rx.text(subtitulo, size="3", color_scheme="gray"),
                    rx.fragment()
                ),
           
            spacing="4",
            align="end"
        ),

        rx.spacer(),

        # Bloque de Botón (solo si hay texto_boton)
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
        width="100%",
        align="center",
        padding_y="4",
        
    )
