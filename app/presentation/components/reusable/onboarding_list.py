"""Componentes reutilizables para listados de onboarding (admin/portal)."""

from typing import Any, Callable

import reflex as rx

from app.presentation.components.ui import (
    empty_state_card,
    select_estatus_onboarding,
    skeleton_tabla,
)
from app.presentation.theme import Colors, Typography


def onboarding_filters(
    *,
    opciones,
    value,
    on_change: Callable,
    on_reload: Callable | None = None,
    placeholder: str = "Estatus onboarding",
    total_text: Any = None,
) -> rx.Component:
    """Filtro de estatus onboarding con contador opcional."""
    select_component = select_estatus_onboarding(
        opciones=opciones,
        value=value,
        on_change=on_change,
        on_reload=on_reload,
        placeholder=placeholder,
    )

    if total_text is None:
        return select_component

    return rx.hstack(
        select_component,
        rx.spacer(),
        rx.text(
            total_text,
            font_size=Typography.SIZE_SM,
            color=Colors.TEXT_SECONDARY,
        ),
        align="center",
        width="100%",
    )


def onboarding_table(
    *,
    loading,
    headers: list[dict],
    rows,
    row_renderer: Callable,
    total,
    total_condition,
    empty_title: str,
    empty_description: str,
    empty_icon: str,
    loading_rows: int = 5,
    total_caption: Any = None,
    header_variant: str = "default",
) -> rx.Component:
    """Tabla reusable de onboarding con skeleton y empty state."""
    if header_variant == "admin":
        header_cells = [
            rx.table.column_header_cell(
                rx.text(
                    h["nombre"],
                    font_size=Typography.SIZE_XS,
                    font_weight=Typography.WEIGHT_SEMIBOLD,
                    color=Colors.TEXT_MUTED,
                    text_transform="uppercase",
                ),
                width=h["ancho"],
            )
            for h in headers
        ]
    else:
        header_cells = [
            rx.table.column_header_cell(h["nombre"], width=h["ancho"])
            for h in headers
        ]

    table_component = rx.table.root(
        rx.table.header(rx.table.row(*header_cells)),
        rx.table.body(rx.foreach(rows, row_renderer)),
        width="100%",
        variant="surface",
    )

    if total_caption is not None:
        content_when_has_rows = rx.vstack(
            table_component,
            rx.text(
                total_caption,
                font_size=Typography.SIZE_SM,
                color=Colors.TEXT_SECONDARY,
            ),
            width="100%",
            spacing="3",
        )
    else:
        content_when_has_rows = table_component

    return rx.cond(
        loading,
        skeleton_tabla(columnas=headers, filas=loading_rows),
        rx.cond(
            total_condition,
            content_when_has_rows,
            empty_state_card(
                title=empty_title,
                description=empty_description,
                icon=empty_icon,
            ),
        ),
    )
