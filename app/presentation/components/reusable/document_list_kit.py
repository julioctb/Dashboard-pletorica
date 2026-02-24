"""Shells reutilizables para secciones/listados de documentos."""

import reflex as rx

from app.presentation.theme import Colors, Typography, Spacing


def document_section_header(
    *,
    title,
    subtitle=None,
    actions=None,
) -> rx.Component:
    """Header reusable para secciones de documentos."""
    return rx.vstack(
        rx.hstack(
            rx.text(
                title,
                font_size=Typography.SIZE_LG,
                font_weight=Typography.WEIGHT_BOLD,
                color=Colors.TEXT_PRIMARY,
            ),
            rx.spacer(),
            actions if actions is not None else rx.fragment(),
            width="100%",
            align="center",
        ),
        rx.cond(
            subtitle is not None,
            rx.text(
                subtitle,
                font_size=Typography.SIZE_SM,
                color=Colors.TEXT_SECONDARY,
            ),
            rx.fragment(),
        ),
        width="100%",
        spacing="1",
    )


def document_section_container(body: rx.Component) -> rx.Component:
    """Contenedor visual reusable para listas de documentos."""
    return rx.box(
        body,
        width="100%",
        border=f"1px solid {Colors.BORDER}",
        border_radius="8px",
        background=Colors.SURFACE,
        overflow="hidden",
    )


def document_empty_state(
    *,
    title: str,
    description: str,
    icon: str = "file-x",
) -> rx.Component:
    """Estado vacío reusable para secciones de documentos."""
    return rx.center(
        rx.vstack(
            rx.icon(icon, size=36, color=Colors.TEXT_MUTED),
            rx.text(
                title,
                font_size=Typography.SIZE_SM,
                color=Colors.TEXT_SECONDARY,
            ),
            rx.text(
                description,
                font_size=Typography.SIZE_XS,
                color=Colors.TEXT_MUTED,
            ),
            spacing="2",
            align="center",
        ),
        padding=Spacing.LG,
        width="100%",
    )
