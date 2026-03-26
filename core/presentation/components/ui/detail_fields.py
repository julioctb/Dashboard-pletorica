"""Primitives reutilizables para campos read-only y metadata visual."""

from __future__ import annotations

import reflex as rx

from core.presentation.theme import Colors, Typography


def detail_label(texto: str) -> rx.Component:
    """Label estándar en uppercase para metadata y detalle solo lectura."""
    return rx.text(
        texto,
        font_size="10px",
        font_weight=Typography.WEIGHT_MEDIUM,
        color=Colors.TEXT_MUTED,
        text_transform="uppercase",
        letter_spacing="0.04em",
        width="100%",
        text_align="left",
    )


def section_title(texto: str) -> rx.Component:
    """Título ligero de sección para pantallas de detalle."""
    return rx.text(
        texto,
        font_size=Typography.SIZE_SM,
        font_weight=Typography.WEIGHT_MEDIUM,
        color=Colors.TEXT_PRIMARY,
    )


def modal_section_label(texto: str) -> rx.Component:
    """Label de sección uppercase muted para modals de formulario."""
    return rx.text(
        texto,
        font_size=Typography.SIZE_XS,
        font_weight=Typography.WEIGHT_MEDIUM,
        color=Colors.TEXT_MUTED,
        text_transform="uppercase",
        letter_spacing="0.04em",
    )


def fallback_text(texto: str = "No disponible") -> rx.Component:
    """Texto fallback consistente para campos vacíos."""
    return rx.text(
        texto,
        font_size=Typography.SIZE_SM,
        color=Colors.TEXT_MUTED,
        font_style="italic",
    )


def detail_text_item(
    label: str,
    value,
    *,
    weight: str = Typography.WEIGHT_REGULAR,
    fallback: str = "No disponible",
) -> rx.Component:
    """Campo read-only con texto simple y fallback."""
    return rx.vstack(
        detail_label(label),
        rx.cond(
            value != "",
            rx.text(
                value,
                font_size=Typography.SIZE_SM,
                font_weight=weight,
                color=Colors.TEXT_PRIMARY,
            ),
            fallback_text(fallback),
        ),
        spacing="1",
        align="start",
        width="100%",
    )


def detail_link_item(
    label: str,
    value,
    href,
    *,
    external: bool = False,
    fallback: str = "No disponible",
) -> rx.Component:
    """Campo read-only con link y fallback."""
    return rx.vstack(
        detail_label(label),
        rx.cond(
            (value != "") & (href != ""),
            rx.link(
                rx.text(
                    value,
                    font_size=Typography.SIZE_SM,
                    color=Colors.INFO,
                ),
                href=href,
                underline="none",
                is_external=external,
            ),
            fallback_text(fallback),
        ),
        spacing="1",
        align="start",
        width="100%",
    )


def metadata_item(
    label: str,
    value,
    *,
    tone: str = "primary",
    min_width: str = "140px",
    label_weight: str = Typography.WEIGHT_MEDIUM,
    value_weight: str = Typography.WEIGHT_MEDIUM,
) -> rx.Component:
    """Item de metadata horizontal para strips superiores."""
    color = Colors.TEXT_PRIMARY if tone == "primary" else Colors.TEXT_SECONDARY
    return rx.vstack(
        rx.text(
            label,
            font_size="10px",
            font_weight=label_weight,
            color=Colors.TEXT_MUTED,
            text_transform="uppercase",
            letter_spacing="0.04em",
            width="100%",
            text_align="left",
        ),
        rx.text(
            value,
            font_size=Typography.SIZE_SM,
            font_weight=value_weight,
            color=color,
            width="100%",
            text_align="left",
        ),
        spacing="1",
        align="start",
        min_width=min_width,
    )


def metadata_divider() -> rx.Component:
    """Separador vertical sutil para tiras de metadata."""
    return rx.box(
        width="1px",
        align_self="stretch",
        background=Colors.BORDER,
        opacity="0.7",
    )
