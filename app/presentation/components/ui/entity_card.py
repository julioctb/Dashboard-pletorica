"""
Componente de tarjeta genérica para mostrar entidades en vista de grid.

Uso:
    from app.presentation.components.ui import entity_card

    entity_card(
        titulo=empresa["nombre_comercial"],
        subtitulo=empresa["rfc"],
        badge_superior=rx.badge("NOMINA", color_scheme="blue"),
        status=empresa["estatus"],
        campos=[
            ("Email", empresa["email"]),
            ("Teléfono", empresa["telefono"]),
        ],
        acciones=action_buttons_reactive(empresa, ...),
        on_click=State.ver_detalle(empresa["id"]),
    )
"""

import reflex as rx
from typing import Any, List, Optional, Tuple

from app.presentation.theme import Colors, Spacing, Typography
from app.presentation.components.ui.status_badge import status_badge_reactive


def entity_card(
    titulo: Any,
    subtitulo: Optional[Any] = None,
    badge_superior: Optional[rx.Component] = None,
    status: Optional[Any] = None,
    campos: Optional[List[Tuple[str, Any]]] = None,
    acciones: Optional[rx.Component] = None,
    on_click: Optional[Any] = None,
    icono: Optional[str] = None,
    color_icono: str = Colors.PRIMARY,
) -> rx.Component:
    """
    Tarjeta genérica para mostrar una entidad en vista de grid.

    Args:
        titulo: Texto principal de la tarjeta
        subtitulo: Texto secundario debajo del título
        badge_superior: Badge opcional en la esquina superior izquierda
        status: Valor del estatus para mostrar badge de estado
        campos: Lista de tuplas (label, valor) para mostrar información adicional
        acciones: Componente de botones de acción
        on_click: Handler para click en la tarjeta (opcional)
        icono: Nombre del icono opcional
        color_icono: Color del icono

    Returns:
        Componente rx.card con el diseño estandarizado
    """
    # Header con badge y status
    header_items = []
    if badge_superior:
        header_items.append(badge_superior)
    header_items.append(rx.spacer())
    if status is not None:
        header_items.append(status_badge_reactive(status))

    header = rx.hstack(
        *header_items,
        width="100%",
        align="center",
    ) if header_items else None

    # Título con icono opcional
    titulo_component = rx.hstack(
        rx.icon(icono, size=18, color=color_icono) if icono else rx.fragment(),
        rx.text(
            titulo,
            font_size=Typography.SIZE_BASE,
            font_weight=Typography.WEIGHT_BOLD,
            color=Colors.TEXT_PRIMARY,
            no_of_lines=1,
        ),
        spacing="2",
        align="center",
    ) if icono else rx.text(
        titulo,
        font_size=Typography.SIZE_BASE,
        font_weight=Typography.WEIGHT_BOLD,
        color=Colors.TEXT_PRIMARY,
        no_of_lines=1,
    )

    # Subtítulo
    subtitulo_component = rx.text(
        subtitulo,
        font_size=Typography.SIZE_SM,
        color=Colors.TEXT_SECONDARY,
        no_of_lines=1,
    ) if subtitulo else None

    # Campos adicionales
    campos_component = None
    if campos:
        campos_items = []
        for label, valor in campos:
            campos_items.append(
                rx.hstack(
                    rx.text(
                        f"{label}:",
                        font_size=Typography.SIZE_XS,
                        color=Colors.TEXT_MUTED,
                    ),
                    rx.text(
                        valor,
                        font_size=Typography.SIZE_XS,
                        color=Colors.TEXT_SECONDARY,
                        no_of_lines=1,
                    ),
                    spacing="1",
                    align="center",
                )
            )
        campos_component = rx.vstack(
            *campos_items,
            spacing="1",
            align="start",
            width="100%",
        )

    # Footer con acciones
    footer = rx.hstack(
        rx.spacer(),
        acciones if acciones else rx.fragment(),
        width="100%",
        align="center",
    ) if acciones else None

    # Contenido de la tarjeta
    contenido = []
    if header:
        contenido.append(header)
    contenido.append(titulo_component)
    if subtitulo_component:
        contenido.append(subtitulo_component)
    if campos_component:
        contenido.append(campos_component)
    if footer:
        contenido.append(footer)

    card_style = {
        "transition": "all 0.2s ease",
        "_hover": {
            "boxShadow": "0 4px 12px rgba(0, 0, 0, 0.1)",
            "transform": "translateY(-2px)",
        },
    }

    if on_click:
        card_style["cursor"] = "pointer"

    return rx.card(
        rx.vstack(
            *contenido,
            spacing="3",
            width="100%",
            align="start",
        ),
        padding=Spacing.MD,
        style=card_style,
        on_click=on_click,
    )


def entity_grid(
    items: rx.Var,
    render_card: Any,
    columns: str = "repeat(auto-fill, minmax(320px, 1fr))",
    gap: str = Spacing.MD,
) -> rx.Component:
    """
    Grid responsivo para mostrar tarjetas de entidades.

    Args:
        items: Lista de items a renderizar
        render_card: Función que recibe un item y retorna un entity_card
        columns: Definición de columnas CSS grid
        gap: Espaciado entre tarjetas

    Returns:
        Grid con las tarjetas

    Example:
        entity_grid(
            items=State.empresas,
            render_card=lambda emp: entity_card(
                titulo=emp["nombre_comercial"],
                ...
            ),
        )
    """
    return rx.box(
        rx.foreach(items, render_card),
        display="grid",
        grid_template_columns=columns,
        gap=gap,
        width="100%",
    )
