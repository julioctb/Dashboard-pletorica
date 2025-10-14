import reflex as rx
from .presentation.pages.dashboard import dashboard_page  
from .presentation.pages.empresas import empresas_page

from .presentation.layout.sidebar_layout import sidebar

#se dibuja el layout para todas las paginas
def index(content: rx.Component) -> rx.Component:
    return rx.hstack(
        sidebar(),
        rx.box(
            content,
            width="100%",
            flex="1",
            overflow_y="auto",
            style={
                "minHeight": "calc(100vh - 140px)",
                "padding": "1.5rem"
            }
        ),
        width="100%",
        spacing="0"
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
app.add_page(lambda: index(dashboard_page()), route="/") 
app.add_page(lambda: index(empresas_page()), route="/empresas")