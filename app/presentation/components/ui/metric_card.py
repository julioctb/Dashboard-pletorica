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
    from app.presentation.components.ui import metric_card
    
    metric_card(
        titulo="Empleados activos",
        valor=DashboardState.metricas["empleados_activos"],
        icono="users",
        color_scheme="green",
        href="/empleados",
    )
"""

import reflex as rx
from app.presentation.theme import (
    Colors,
    Typography,
    Shadows,
    Radius,
    Transitions,
)


def metric_card(
    titulo: str,
    valor: rx.Var | str,
    icono: str,
    color_scheme: str = "blue",
    href: str | None = None,
    descripcion: rx.Var | str | None = None,
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

    Returns:
        rx.Component con la tarjeta de métrica
    """
    # Contenido interno de la card (siempre el mismo, con o sin link)
    card_content = rx.hstack(
        # Columna izquierda: título + valor + descripción
        rx.vstack(
            rx.text(
                titulo,
                font_size=Typography.SIZE_XS,
                color=Colors.TEXT_MUTED,
                font_weight=Typography.WEIGHT_MEDIUM,
                line_height=Typography.LINE_HEIGHT_TIGHT,
            ),
            rx.text(
                valor,
                font_size=Typography.SIZE_3XL,
                font_weight=Typography.WEIGHT_BOLD,
                color=Colors.TEXT_PRIMARY,
                line_height="1",
            ),
            # Descripción opcional
            rx.cond(
                descripcion is not None,
                rx.text(
                    descripcion if descripcion else "",
                    font_size=Typography.SIZE_XS,
                    color=Colors.TEXT_SECONDARY,
                    line_height=Typography.LINE_HEIGHT_TIGHT,
                ),
                rx.fragment(),
            ),
            spacing="1",
            align_items="start",
        ),
        rx.spacer(),
        # Icono con fondo circular temático
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

    # Card base con estilos del theme
    card = rx.card(
        card_content,
        width="100%",
        style={
            "_hover": {"box_shadow": Shadows.MD},
            "transition": Transitions.FAST,
        },
    )

    # Si tiene href, envolver en link
    if href:
        return rx.link(
            card,
            href=href,
            underline="none",
            width="100%",
        )

    return card
