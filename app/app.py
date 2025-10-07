import reflex as rx
# from .pages.dashboard import dashboard_page  # Legacy dashboard - TODO: migrar a nueva arquitectura
from .presentation.pages.empresas import empresas_page

from .presentation.layout.sidebar_layout import sidebar
from .presentation.layout.navbar_layout import navbar

#Configuracion de la Aplicacion
class AppConfig:
    pass

config = AppConfig()



#se dibuja el layout para todas las paginas
def index(content: rx.Component) -> rx.Component:
    return rx.hstack(
        sidebar(),
        rx.vstack(
        # navbar(),
        rx.container(
            content,
            min_height="calc(100vh - 140px)", #Altura menos navbar y footer
            width = "100%",
            size="4"
        ),
        
    )
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
# app.add_page(lambda: index(dashboard_page()), route="/")  # TODO: migrar dashboard
app.add_page(lambda: index(empresas_page()), route="/")  # Temporalmente empresas como página principal
app.add_page(lambda: index(empresas_page()), route="/empresas")