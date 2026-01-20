import reflex as rx
from .presentation.pages.dashboard import dashboard_page
from .presentation.pages.empresas.empresas_page import empresas_page

from .presentation.pages.simulador.simulador_page import simulador_page
from .presentation.pages.tipo_servicio.tipo_servicio_page import tipo_servicio_page
from .presentation.pages.categorias_puesto.categorias_puesto_page import categorias_puesto_page
from .presentation.pages.contratos.contratos_page import contratos_page

from .presentation.layout.sidebar_layout import sidebar

#se dibuja el layout para todas las paginas
def index(content: rx.Component) -> rx.Component:
    return rx.hstack(
        sidebar(),
        rx.box(
            content,
            background_color = 'var(--gray-2)',
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
        scaling="100%",
        accent_color='indigo'
    )
)

#definicion de rutas
app.add_page(lambda: index(dashboard_page()), route="/")
app.add_page(lambda: index(empresas_page()), route="/empresas")

app.add_page(lambda: index(simulador_page()), route="/simulador")
app.add_page(lambda: index(tipo_servicio_page()), route="/tipos-servicio")
app.add_page(lambda: index(categorias_puesto_page()), route="/categorias-puesto")
app.add_page(lambda: index(contratos_page()), route="/contratos")