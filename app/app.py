import reflex as rx
from app.pages.dashboard import dashboard_page
from app.pages.empresas_page import empresas_page

#importacion de prueba
from app.layout.sidebar_layout import sidebar
from app.layout.navbar_layout import navbar

#Configuracion de la Aplicacion
class AppConfig:
    pass

config = AppConfig()







#se dibuja el layout para todas las paginas
def base_layout(content: rx.Component) -> rx.Component:
    return rx.hstack(
        sidebar(),
        rx.vstack(
        # navbar(),
        rx.container(
            content,
            min_height="calc(100vh - 140px)", #Altura menos navbar y footer
            padding="4"
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
app.add_page(lambda: base_layout(dashboard_page()), route="/")
app.add_page(lambda: base_layout(empresas_page()), route="/empresas")