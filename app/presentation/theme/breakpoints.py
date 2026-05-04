"""
Constantes de layout y contenedor de contenido del portal.

Centraliza valores de layout que se repiten en el portal.
Los breakpoints de Reflex/Radix (sm, md, lg, xl) se usan
directamente con rx.breakpoints() — no se abstraen aquí.

Área de contenido real por viewport (restando SIDEBAR_WIDTH):
- md (≥992px):  752px de contenido
- lg (≥1280px): 1040px de contenido  ← target principal (laptop 1366 = 1126px)
- xl (≥1536px): 1296px de contenido
"""
import reflex as rx

from app.presentation.theme import Spacing


class Layout:
    """Constantes de layout del portal."""

    SIDEBAR_WIDTH: str = "240px"
    SIDEBAR_MIN_WIDTH: str = "240px"
    CONTENT_MAX_WIDTH: str = "1400px"
    CONTENT_MAX_WIDTH_COMPACT: str = "900px"
    CONTENT_MAX_WIDTH_OPERATIONS: str = "1200px"


def content_container(*children, **props) -> rx.Component:
    """
    Wrapper de contenido para páginas del portal.

    Aplica max-width centrado para que en pantallas xl+
    el contenido no se estire más allá de 1400px.
    Recibe children y props adicionales que se pasan al rx.box.

    Uso:
        content_container(
            page_header(...),
            metric_cards_grid,
            tabla,
        )
    """
    return rx.box(
        *children,
        width="100%",
        max_width=Layout.CONTENT_MAX_WIDTH,
        margin_x="auto",
        padding_x=Spacing.PAGE_PADDING,
        **props,
    )
