import reflex as rx

from app.presentation.theme import Colors, Spacing


def navbar() -> rx.Component:
    return rx.box(
        rx.hstack(
            # Logo y titulo
            rx.hstack(
                rx.icon("building-2", size=24, color=Colors.PRIMARY),
                spacing="2",
                align="center",
            ),
            rx.spacer(),
            # Links de navegacion
            rx.hstack(
                rx.link("Dashboard", href="/", weight="medium"),
                spacing="6",
            ),
            rx.spacer(),
            # Buscador
            rx.input(
                rx.input.slot(rx.icon("search")),
                placeholder="Buscar...",
                type="search",
                size="2",
                justify="end",
            ),
            width="100%",
            padding=Spacing.MD,
            align="center",
        ),
        padding=Spacing.MD,
        background=Colors.SURFACE,
        border_bottom=f"1px solid {Colors.BORDER}",
        width="100%",
    )
