"""
Componente reutilizable: Tarjeta de Métrica (KPI Card).

Muestra un indicador numérico con título, icono y color temático.
Opcionalmente funciona como enlace de navegación.

Diseñado para usuarios +42 años:
- Números grandes (SIZE_3XL = 28px) para lectura rápida
- Alto contraste (TEXT_PRIMARY sobre SURFACE)
- Área de clic generosa (card completa)

Patrón visual:
    ┌────────────────────────────┐
    │  Título              [ico] │
    │  42                        │
    │  Descripción opcional      │
    └────────────────────────────┘

Uso:
    from core.presentation.components.ui import metric_card
    
    metric_card(
        titulo="Empleados activos",
        valor=State.metricas["empleados_activos"],
        icono="users",
        color_scheme="green",
        href="/empleados",
    )
"""

import reflex as rx
from core.presentation.theme import (
    Colors,
    Typography,
    CardStyles,
    Shadows,
    Radius,
    Transitions,
)


def metric_card(
    titulo: str,
    valor: rx.Var | str,
    icono: str | None,
    color_scheme: str = "blue",
    href: rx.Var | str | None = None,
    descripcion: rx.Var | str | None = None,
    show_icon: bool = True,
    background: str | None = None,
    border: str | None = None,
    hoverable: bool = True,
    value_color: str | None = None,
    footer: rx.Component | None = None,
    align: str = "start",
) -> rx.Component:
    """
    Tarjeta de métrica KPI reutilizable.

    Args:
        titulo: Etiqueta descriptiva (ej: "Empleados activos")
        valor: Número o rx.Var reactivo a mostrar
        icono: Nombre del icono Lucide (ej: "users", "file-text")
        color_scheme: Color Radix para icono y fondo (ej: "blue", "green", "teal")
        href: Si se proporciona, la card funciona como enlace
        descripcion: Texto auxiliar opcional bajo el valor
        show_icon: Si False, oculta el icono decorativo
        background: Override opcional para el fondo de la card
        border: Override opcional para el borde de la card
        hoverable: Si False, desactiva el estado hover

    Returns:
        rx.Component con la tarjeta de métrica
    """
    text_align = "center" if align == "center" else "left"
    align_items = "center" if align == "center" else "start"

    text_content = rx.vstack(
        rx.text(
            titulo,
            font_size=Typography.SIZE_XS,
            color=Colors.TEXT_MUTED,
            font_weight=Typography.WEIGHT_MEDIUM,
            line_height=Typography.LINE_HEIGHT_TIGHT,
            text_align=text_align,
            width="100%",
        ),
        rx.text(
            valor,
            font_size=Typography.SIZE_3XL,
            font_weight=Typography.WEIGHT_BOLD,
            color=value_color if value_color is not None else Colors.TEXT_PRIMARY,
            line_height="1",
            text_align=text_align,
            width="100%",
        ),
        rx.cond(
            descripcion is not None,
            rx.text(
                descripcion,
                font_size=Typography.SIZE_XS,
                color=Colors.TEXT_SECONDARY,
                line_height=Typography.LINE_HEIGHT_TIGHT,
                text_align=text_align,
                width="100%",
            ),
            rx.fragment(),
        ),
        rx.cond(
            footer is not None,
            footer,
            rx.fragment(),
        ),
        spacing="1",
        align_items=align_items,
        width="100%",
    )

    if show_icon and icono:
        card_content = rx.hstack(
            text_content,
            rx.spacer(),
            rx.center(
                rx.icon(icono, size=24, color=f"var(--{color_scheme}-9)"),
                width="48px",
                height="48px",
                border_radius=Radius.XL,
                background=f"var(--{color_scheme}-3)",
                flex_shrink="0",
            ),
            width="100%",
            align="center",
        )
    else:
        card_content = text_content

    card_style = {
        **CardStyles.BASE,
        "transition": Transitions.FAST,
    }
    if hoverable:
        card_style["_hover"] = {"box_shadow": Shadows.MD}
    if background is not None:
        card_style["background"] = background
    if border is not None:
        card_style["border"] = border

    # Card base con estilos del theme
    card = rx.card(
        card_content,
        width="100%",
        style=card_style,
    )

    # Si tiene href, envolver en link
    if href is not None:
        return rx.link(
            card,
            href=href,
            underline="none",
            width="100%",
        )

    return card
