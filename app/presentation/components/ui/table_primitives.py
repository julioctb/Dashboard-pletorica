"""Primitivas reutilizables para shells de tablas."""

from typing import Any, Callable

import reflex as rx

from app.presentation.components.ui.skeletons import skeleton_tabla
from app.presentation.theme import Colors, Spacing, Typography


def table_header_cells(headers: list[dict], variant: str = "default") -> list[rx.Component]:
    """Construye celdas de encabezado con variantes visuales consistentes."""
    if variant == "uppercase_muted":
        return [
            rx.table.column_header_cell(
                rx.text(
                    col["nombre"],
                    font_size=Typography.SIZE_XS,
                    font_weight=Typography.WEIGHT_SEMIBOLD,
                    color=Colors.TEXT_MUTED,
                    text_transform="uppercase",
                ),
                width=col.get("ancho", "auto"),
            )
            for col in headers
        ]

    return [
        rx.table.column_header_cell(
            col["nombre"],
            width=col.get("ancho", "auto"),
        )
        for col in headers
    ]


def table_cell_text(
    value,
    *,
    tone: str = "primary",
    size: str | None = None,
    weight: str | None = None,
    fallback: str | None = None,
    **text_props,
) -> rx.Component:
    """Celda de texto reutilizable con tonos visuales consistentes."""
    color = {
        "primary": Colors.TEXT_PRIMARY,
        "secondary": Colors.TEXT_SECONDARY,
        "muted": Colors.TEXT_MUTED,
        "success": "var(--green-11)",
    }.get(tone, Colors.TEXT_PRIMARY)

    text_kwargs = {"color": color, **text_props}
    if size is not None:
        text_kwargs["font_size"] = size
    if weight is not None:
        text_kwargs["font_weight"] = weight

    if fallback is None:
        return rx.table.cell(rx.text(value, **text_kwargs))

    return rx.table.cell(
        rx.cond(
            value,
            rx.text(value, **text_kwargs),
            rx.text(fallback, **text_kwargs),
        ),
    )


def table_text(
    value,
    *,
    tone: str = "primary",
    size: str | None = None,
    weight: str | None = None,
    fallback: str | None = None,
    **text_props,
) -> rx.Component:
    """Texto reutilizable para usar dentro de celdas ya personalizadas."""
    color = {
        "primary": Colors.TEXT_PRIMARY,
        "secondary": Colors.TEXT_SECONDARY,
        "muted": Colors.TEXT_MUTED,
        "success": "var(--green-11)",
    }.get(tone, Colors.TEXT_PRIMARY)

    text_kwargs = {"color": color, **text_props}
    if size is not None:
        text_kwargs["font_size"] = size
    if weight is not None:
        text_kwargs["font_weight"] = weight

    if fallback is None:
        return rx.text(value, **text_kwargs)
    return rx.cond(value, rx.text(value, **text_kwargs), rx.text(fallback, **text_kwargs))


def table_cell_text_sm(value, *, tone: str = "primary", **text_props) -> rx.Component:
    """Atajo para celdas de texto tamaño SM."""
    return table_cell_text(value, tone=tone, size=Typography.SIZE_SM, **text_props)


def table_text_sm(value, *, tone: str = "primary", **text_props) -> rx.Component:
    """Atajo para texto de celdas tamaño SM."""
    return table_text(value, tone=tone, size=Typography.SIZE_SM, **text_props)


def table_cell_badge(component: rx.Component) -> rx.Component:
    """Atajo semántico para celdas cuyo contenido principal es un badge."""
    return rx.table.cell(component)


def table_cell_actions(component: rx.Component) -> rx.Component:
    """Atajo semántico para celdas de acciones."""
    return rx.table.cell(component)


def table_pagination(
    *,
    current_page,
    total_pages,
    page_numbers,
    on_page_change: Callable,
    on_previous: Callable,
    on_next: Callable,
    color_scheme: str = "blue",
) -> rx.Component:
    """Paginador reusable para tablas con patrón visual consistente."""
    page_buttons = rx.foreach(
        page_numbers,
        lambda page: rx.cond(
            page == current_page,
            rx.button(
                page.to(str),
                size="2",
                variant="solid",
                color_scheme=color_scheme,
                min_width="40px",
                disabled=True,
                cursor="default",
            ),
            rx.button(
                page.to(str),
                size="2",
                variant="soft",
                color_scheme="gray",
                min_width="40px",
                on_click=on_page_change(page),
            ),
        ),
    )

    return rx.cond(
        total_pages > 1,
        rx.flex(
            rx.button(
                rx.icon("chevron-left", size=16),
                "Anterior",
                size="2",
                variant="soft",
                color_scheme="gray",
                on_click=on_previous,
                disabled=current_page <= 1,
            ),
            rx.flex(
                page_buttons,
                wrap="wrap",
                align="center",
                justify="center",
                gap=Spacing.XS,
            ),
            rx.button(
                "Siguiente",
                rx.icon("chevron-right", size=16),
                size="2",
                variant="soft",
                color_scheme="gray",
                on_click=on_next,
                disabled=current_page >= total_pages,
            ),
            width="100%",
            wrap="wrap",
            align="center",
            justify="end",
            column_gap=Spacing.SM,
            row_gap=Spacing.XS,
        ),
        rx.fragment(),
    )


def table_shell(
    *,
    loading,
    headers: list[dict] | None = None,
    rows=None,
    row_renderer: Callable | None = None,
    has_rows,
    empty_component: rx.Component,
    total_caption: Any | None = None,
    footer_component: rx.Component | None = None,
    loading_rows: int = 5,
    header_variant: str = "default",
    table_variant: str = "surface",
    header_cells: list[rx.Component] | None = None,
    body_component: rx.Component | None = None,
    table_size: str | None = None,
) -> rx.Component:
    """Shell base para tablas con skeleton, empty state y footer/caption opcionales."""
    if header_cells is None:
        if headers is None:
            raise ValueError("`headers` or `header_cells` is required")
        computed_header_cells = table_header_cells(headers, variant=header_variant)
    else:
        computed_header_cells = header_cells

    if body_component is None:
        if rows is None or row_renderer is None:
            raise ValueError("`rows` and `row_renderer` are required when `body_component` is not provided")
        computed_body = rx.foreach(rows, row_renderer)
    else:
        computed_body = body_component

    table_props = {
        "width": "100%",
        "variant": table_variant,
    }
    if table_size is not None:
        table_props["size"] = table_size

    content_with_rows: list[rx.Component] = [
        rx.table.root(
            rx.table.header(
                rx.table.row(
                    *computed_header_cells,
                ),
            ),
            rx.table.body(computed_body),
            **table_props,
        )
    ]

    footer_caption = None
    if total_caption is not None:
        footer_caption = rx.text(
            total_caption,
            font_size=Typography.SIZE_SM,
            color=Colors.TEXT_SECONDARY,
        )

    if footer_caption is not None or footer_component is not None:
        footer_children: list[rx.Component] = []
        if footer_caption is not None:
            footer_children.append(footer_caption)
        if footer_component is not None:
            footer_children.append(footer_component)

        footer_justify = "between"
        if footer_caption is None and footer_component is not None:
            footer_justify = "end"
        elif footer_caption is not None and footer_component is None:
            footer_justify = "start"

        content_with_rows.append(
            rx.flex(
                *footer_children,
                width="100%",
                wrap="wrap",
                align="center",
                justify=footer_justify,
                column_gap=Spacing.MD,
                row_gap=Spacing.SM,
                padding_top=Spacing.SM,
                border_top=f"1px solid {Colors.BORDER}",
            )
        )

    rows_component = rx.vstack(
        *content_with_rows,
        width="100%",
        spacing="3",
    )

    return rx.cond(
        loading,
        skeleton_tabla(columnas=headers or [], filas=loading_rows),
        rx.cond(has_rows, rows_component, empty_component),
    )
