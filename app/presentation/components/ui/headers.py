"""Componentes genéricos de headers para páginas."""
import reflex as rx

from typing import Callable

from app.presentation.theme import Colors


def page_header(
    icono: str | None,
    titulo: str = "",
    *,
    subtitulo: str = "",
    titulo_compuesto: rx.Component | None = None,
    subtitulo_compuesto: rx.Component | None = None,
    icono_boton: str = "",
    texto_boton: str = "",
    onclick: Callable | None = None,
    accion_principal: rx.Component | None = None,
    color_icono: str | None = None,
) -> rx.Component:
    """
    Header de página con título, subtítulo y botón opcional.

    Args:
        icono: Nombre del icono del título
        titulo: Texto del título
        subtitulo: Texto opcional del subtítulo
        titulo_compuesto: Slot opcional para renderizar un título ya construido
        subtitulo_compuesto: Slot opcional para renderizar un subtítulo ya construido
        icono_boton: Icono del botón (vacío = sin icono, API legacy)
        texto_boton: Texto del botón (vacío = sin botón, API legacy)
        onclick: Función al hacer click en el botón (API legacy)
        accion_principal: Componente de acción ya construido (API nueva)
        color_icono: Ramp Radix para colorear el ícono ("teal", "blue", etc.).
            Si None, usa Colors.PRIMARY (azul institucional).
    """
    # Colores del ícono: ramp Radix o fallback azul institucional
    _icon_color = f"var(--{color_icono}-11)" if color_icono else Colors.PRIMARY
    _icon_bg = f"var(--{color_icono}-3)" if color_icono else Colors.PRIMARY_LIGHT

    return rx.hstack(
        # Bloque de Título e Icono
        rx.hstack(
            rx.cond(
                icono is not None,
                rx.center(
                    rx.icon(icono, size=28, color=_icon_color),
                    width="48px",
                    height="48px",
                    background=_icon_bg,
                    border_radius="12px",
                ),
                rx.fragment(),
            ),
            rx.vstack(
                titulo_compuesto
                if titulo_compuesto is not None
                else rx.text(titulo, size="6", weight="bold"),
                (
                    subtitulo_compuesto
                    if subtitulo_compuesto is not None
                    else rx.cond(
                        subtitulo != "",
                        rx.text(
                            subtitulo,
                            size="3",
                            color=Colors.TEXT_SECONDARY,
                        ),
                        rx.fragment(),
                    )
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
