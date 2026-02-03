import reflex as rx

from app.presentation.theme import GLOBAL_STYLES
from app.api.main import api_app

from .presentation.pages.dashboard import dashboard_page
from .presentation.pages.empresas.empresas_page import empresas_page

from .presentation.pages.simulador.simulador_page import simulador_page
from .presentation.pages.tipo_servicio.tipo_servicio_page import tipo_servicio_page
from .presentation.pages.categorias_puesto.categorias_puesto_page import categorias_puesto_page
from .presentation.pages.contratos.contratos_page import contratos_page
from .presentation.pages.plazas.plazas_page import plazas_page
from .presentation.pages.empleados.empleados_page import empleados_page
from .presentation.pages.historial_laboral.historial_laboral_page import historial_laboral_page
from .presentation.pages.requisiciones.requisiciones_page import requisiciones_page
from .presentation.pages.configuracion.configuracion_page import configuracion_page
from .presentation.pages.sedes.sedes_page import sedes_page
from .presentation.pages.login.login_page import login_page
from .presentation.pages.admin.usuarios.usuarios_page import usuarios_admin_page

from .presentation.layout.sidebar_layout import sidebar

# Portal de cliente
from .presentation.portal.layout.portal_layout import portal_index
from .presentation.portal.pages.portal_dashboard import portal_dashboard_page
from .presentation.portal.pages.mi_empresa import mi_empresa_page
from .presentation.portal.pages.mis_empleados import mis_empleados_page
from .presentation.portal.pages.mis_contratos import mis_contratos_page
from .presentation.portal.pages.alta_masiva import alta_masiva_page

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
    api_transformer=api_app,
    theme= rx.theme(
        appearance= "light",
        has_background=True,
        radius="medium",
        scaling="100%",
        accent_color='blue'
    ),
    style=GLOBAL_STYLES
)

#definicion de rutas
app.add_page(lambda: index(dashboard_page()), route="/")
app.add_page(lambda: index(empresas_page()), route="/empresas")

app.add_page(lambda: index(simulador_page()), route="/simulador")
app.add_page(lambda: index(tipo_servicio_page()), route="/tipos-servicio")
app.add_page(lambda: index(categorias_puesto_page()), route="/categorias-puesto")
app.add_page(lambda: index(contratos_page()), route="/contratos")
app.add_page(lambda: index(plazas_page()), route="/plazas")
app.add_page(lambda: index(empleados_page()), route="/empleados")
app.add_page(lambda: index(historial_laboral_page()), route="/historial-laboral")
app.add_page(lambda: index(requisiciones_page()), route="/requisiciones")
app.add_page(lambda: index(configuracion_page()), route="/configuracion")
app.add_page(lambda: index(sedes_page()), route="/sedes")
app.add_page(login_page, route="/login")
app.add_page(lambda: index(usuarios_admin_page()), route="/admin/usuarios")

# Portal de cliente
app.add_page(lambda: portal_index(portal_dashboard_page()), route="/portal")
app.add_page(lambda: portal_index(mi_empresa_page()), route="/portal/mi-empresa")
app.add_page(lambda: portal_index(mis_empleados_page()), route="/portal/empleados")
app.add_page(lambda: portal_index(mis_contratos_page()), route="/portal/contratos")
app.add_page(lambda: portal_index(alta_masiva_page()), route="/portal/alta-masiva")