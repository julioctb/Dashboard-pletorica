import reflex as rx




def navbar() -> rx.Component:
    return rx.box(
    rx.hstack(
        #logo y titulo
        rx.hstack(
        rx.icon("building-2", size=24, color="var(--blue-9)"),
       
        spacing="2",
        align="center"
        ),
        rx.spacer(),

        #links de navegacion
        rx.hstack(
            rx.link("Dashboard", href="/", weight="medium"),#cada linea de estas es un link
            spacing="6"
        ),
        rx.spacer(),

        #info de la version (pendiente cambio)
        rx.input(
            rx.input.slot(rx.icon("search")),
            placeholder="Buscar...",
            type="search",
            size="2",
            justify="end"
        ),
       

        width="100%",
        padding="4",
        border_bottom="1px solid var(--gray-6)"
    ),
    padding='1em'

    )