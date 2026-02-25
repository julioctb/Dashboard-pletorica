"""Reusables para listados de empleados (admin/portal)."""

from typing import Any, Callable

import reflex as rx

from app.presentation.components.ui import table_shell


def employee_table(
    *,
    loading,
    headers: list[dict],
    rows,
    row_renderer: Callable,
    has_rows,
    empty_component: rx.Component,
    total_caption: Any | None = None,
    footer_component: rx.Component | None = None,
    loading_rows: int = 5,
) -> rx.Component:
    """Tabla reusable de empleados con skeleton/empty/footer."""
    return table_shell(
        loading=loading,
        headers=headers,
        rows=rows,
        row_renderer=row_renderer,
        has_rows=has_rows,
        empty_component=empty_component,
        total_caption=total_caption,
        footer_component=footer_component,
        loading_rows=loading_rows,
    )


def employee_filters_bar(*children) -> rx.Component:
    """Contenedor reusable para filtros de empleados."""
    return rx.hstack(
        *children,
        spacing="3",
        align="center",
    )
