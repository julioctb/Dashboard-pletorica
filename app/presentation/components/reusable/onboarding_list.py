"""Componentes reutilizables para listados de onboarding (admin/portal)."""

from typing import Any, Callable

import reflex as rx

from app.presentation.components.ui import (
    empty_state_card,
    select_estatus_onboarding,
    table_shell,
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
    return table_shell(
        loading=loading,
        headers=headers,
        rows=rows,
        row_renderer=row_renderer,
        has_rows=total_condition,
        empty_component=empty_state_card(
            title=empty_title,
            description=empty_description,
            icon=empty_icon,
        ),
        total_caption=total_caption,
        loading_rows=loading_rows,
        header_variant="uppercase_muted" if header_variant == "admin" else "default",
    )
