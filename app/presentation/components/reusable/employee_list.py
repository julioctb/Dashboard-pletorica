"""Reusables para listados de empleados (admin/portal)."""

from typing import Any, Callable

import reflex as rx

from app.presentation.components.ui import skeleton_tabla
from app.presentation.theme import Colors, Typography


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
    content_with_rows = [  # type: ignore[var-annotated]
        rx.table.root(
            rx.table.header(
                rx.table.row(
                    rx.foreach(
                        headers,
                        lambda col: rx.table.column_header_cell(
                            col["nombre"],
                            width=col["ancho"],
                        ),
                    ),
                ),
            ),
            rx.table.body(
                rx.foreach(rows, row_renderer),
            ),
            width="100%",
            variant="surface",
        )
    ]

    if total_caption is not None:
        content_with_rows.append(
            rx.text(
                total_caption,
                font_size=Typography.SIZE_SM,
                color=Colors.TEXT_SECONDARY,
            )
        )

    if footer_component is not None:
        content_with_rows.append(footer_component)

    rows_component = rx.vstack(
        *content_with_rows,
        width="100%",
        spacing="3",
    )

    return rx.cond(
        loading,
        skeleton_tabla(columnas=headers, filas=loading_rows),
        rx.cond(
            has_rows,
            rows_component,
            empty_component,
        ),
    )


def employee_filters_bar(*children) -> rx.Component:
    """Contenedor reusable para filtros de empleados."""
    return rx.hstack(
        *children,
        spacing="3",
        align="center",
    )
