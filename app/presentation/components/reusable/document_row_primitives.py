"""Primitivas reutilizables para filas/listas de documentos."""

import reflex as rx

from app.presentation.theme import Colors, Typography


def documento_subido_icon(subido) -> rx.Component:
    """Icono de estado de documento (subido/no subido)."""
    return rx.cond(
        subido,
        rx.icon("file-check", size=20, color="var(--green-9)"),
        rx.icon("file-x", size=20, color=Colors.TEXT_MUTED),
    )


def documento_requerido_badge(obligatorio) -> rx.Component:
    """Badge de obligatoriedad del documento."""
    return rx.cond(
        obligatorio,
        rx.badge("Obligatorio", color_scheme="blue", variant="outline", size="1"),
        rx.badge("Opcional", color_scheme="gray", variant="outline", size="1"),
    )


def documento_observacion(observacion: str, *, mode: str = "text") -> rx.Component:
    """Observación de documento (texto o tooltip icon)."""
    if mode == "tooltip":
        return rx.cond(
            observacion != "",
            rx.tooltip(
                rx.icon("message-circle", size=14, color=Colors.ERROR),
                content=observacion,
            ),
            rx.fragment(),
        )

    return rx.cond(
        observacion != "",
        rx.text(
            observacion,
            font_size=Typography.SIZE_XS,
            color="var(--red-9)",
        ),
        rx.fragment(),
    )
