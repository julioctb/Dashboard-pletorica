import reflex as rx
#importar pagina de dashboard
from app.pages.dashboard import dashboard_page
from app.config import Config

#Configuracion de la Aplicacion
class AppConfig:
    pass

config = AppConfig()

def navbar() -> rx.Component:
    return rx.hstack(
        #logo y titulo
        rx.hstack(
        rx.icon("building-2", size=24, color="var(--blue-9)"),
        rx.text(Config.APP_NAME, size="4", weight="bold"),
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
        rx.text(f"v{Config.APP_VERSION}",size="1", color="var(--gray-9)"),

        width="100%",
        padding="4",
        border_bottom="1px solid var(--gray-6)"
    )


def footer() -> rx.Component:
    return rx.center(
        rx.text(
            f"v{Config.APP_VERSION} - Desarrollado para Pletorica",
            size="1",
            color="var(--gray-9)"
        ),
        padding="4",
        border_top="1px solid var(--gray-6)",
        margin_top="auto"
    )

#se dibuja el layout para todas las paginas
def base_layout(content: rx.Component) -> rx.Component:
    return rx.vstack(
        navbar(),
        rx.container(
            content,
            min_height="calc(100vh - 140px)", #Altura menos navbar y footer
            padding="4"
        ),
        footer()
    )


#se genera la aplicacion
app= rx.App(
    theme= rx.theme(
        appearance= "light",
        has_background=True,
        radius="medium",
        scaling="100%"
    )
)

#definicion de rutas
app.add_page(lambda: base_layout(dashboard_page()), route="/")