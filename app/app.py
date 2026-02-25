import reflex as rx

from app.presentation.theme import GLOBAL_STYLES
from app.api.main import api_app

# BACKOFFICE — Dashboard
from .presentation.pages.admin.dashboard import super_admin_dashboard_page

# BACKOFFICE — Operacion
from .presentation.pages.empresas.empresas_page import empresas_page
from .presentation.pages.contratos.contratos_page import contratos_page
from .presentation.pages.pagos.pagos_page import pagos_page
from .presentation.pages.entregables import entregables_page, entregable_detalle_page
from .presentation.pages.requisiciones.requisiciones_page import requisiciones_page

# BACKOFFICE — Personal
from .presentation.pages.empleados import empleados_page
from .presentation.pages.plazas.plazas_page import plazas_page
from .presentation.pages.historial_laboral.historial_laboral_page import historial_laboral_page
from .presentation.pages.sedes.sedes_page import sedes_page

# BACKOFFICE — Catalogos
from .presentation.pages.tipo_servicio.tipo_servicio_page import tipo_servicio_page
from .presentation.pages.categorias_puesto.categorias_puesto_page import categorias_puesto_page

# BACKOFFICE — Herramientas
from .presentation.pages.simulador.simulador_page import simulador_page
from .presentation.pages.configuracion.configuracion_page import configuracion_page
from .presentation.pages.mi_perfil import mi_perfil_page

# BACKOFFICE — Administracion
from .presentation.pages.admin.usuarios.usuarios_page import usuarios_admin_page
from .presentation.pages.admin_onboarding import admin_onboarding_page
from .presentation.pages.instituciones.instituciones_page import instituciones_page

# LOGIN
from .presentation.pages.login.login_page import login_page

# Layout
from .presentation.layout.sidebar_layout import sidebar
from .presentation.components.shared.auth_state import AuthState

# PORTAL — Layout
from .presentation.portal.layout.portal_layout import portal_index

# PORTAL — Dashboard y Autoservicio
from .presentation.portal.pages.portal_dashboard import portal_dashboard_page
from .presentation.portal.pages.mis_datos import mis_datos_page

# PORTAL — Mi Empresa
from .presentation.portal.pages.mi_empresa import mi_empresa_page
from .presentation.portal.pages.configuracion_empresa import configuracion_empresa_page

# PORTAL — RRHH
from .presentation.portal.pages.mis_empleados import mis_empleados_page
from .presentation.portal.pages.alta_masiva import alta_masiva_page
from .presentation.portal.pages.onboarding_alta import onboarding_alta_page
from .presentation.portal.pages.expedientes import expedientes_page

# PORTAL — Operacion
from .presentation.portal.pages.mis_contratos import mis_contratos_page
from .presentation.portal.pages.mis_entregables import mis_entregables_page


def index(content: rx.Component) -> rx.Component:
    """Layout wrapper para todas las paginas del backoffice."""
    return rx.box(
        rx.cond(
            AuthState.debe_redirigir_login,
            # No autenticado: spinner mientras se redirige a /login
            rx.center(
                rx.spinner(size="3"),
                height="100vh",
            ),
            # Autenticado (o SKIP_AUTH=true): layout normal
            rx.hstack(
                sidebar(),
                rx.box(
                    content,
                    background_color='var(--gray-2)',
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
            ),
        ),
        on_mount=AuthState.verificar_y_redirigir,
    )


def root_dispatcher_page() -> rx.Component:
    """Ruta raíz (`/`) como dispatcher por rol/contexto."""
    return rx.center(
        rx.vstack(
            rx.spinner(size="3"),
            rx.text("Redirigiendo...", color="gray"),
            spacing="3",
            align="center",
        ),
        height="100vh",
        on_mount=AuthState.redirigir_desde_raiz,
    )


app = rx.App(
    api_transformer=api_app,
    theme=rx.theme(
        appearance="light",
        has_background=True,
        radius="medium",
        scaling="100%",
        accent_color='blue'
    ),
    style=GLOBAL_STYLES
)

# =============================================================================
# RAIZ — Dispatcher + Dashboard
# =============================================================================
app.add_page(root_dispatcher_page, route="/")
app.add_page(lambda: index(super_admin_dashboard_page()), route="/admin")

# =============================================================================
# BACKOFFICE — Operacion
# =============================================================================
app.add_page(lambda: index(empresas_page()), route="/empresas")
app.add_page(lambda: index(contratos_page()), route="/contratos")
app.add_page(lambda: index(pagos_page()), route="/pagos")
app.add_page(lambda: index(entregables_page()), route="/entregables")
app.add_page(lambda: index(entregable_detalle_page()), route="/entregables/[entregable_id]")
app.add_page(lambda: index(requisiciones_page()), route="/wip/requisiciones")

# =============================================================================
# BACKOFFICE — Personal
# =============================================================================
app.add_page(lambda: index(empleados_page()), route="/empleados")
app.add_page(lambda: index(plazas_page()), route="/plazas")
app.add_page(lambda: index(historial_laboral_page()), route="/historial-laboral")
app.add_page(lambda: index(sedes_page()), route="/sedes")

# =============================================================================
# BACKOFFICE — Catalogos
# =============================================================================
app.add_page(lambda: index(tipo_servicio_page()), route="/tipos-servicio")
app.add_page(lambda: index(categorias_puesto_page()), route="/categorias-puesto")

# =============================================================================
# BACKOFFICE — Herramientas
# =============================================================================
app.add_page(lambda: index(simulador_page()), route="/simulador")
app.add_page(lambda: index(configuracion_page()), route="/configuracion")
app.add_page(lambda: index(mi_perfil_page()), route="/mi-perfil")

# =============================================================================
# BACKOFFICE — Administracion
# =============================================================================
app.add_page(lambda: index(usuarios_admin_page()), route="/admin/usuarios")
app.add_page(lambda: index(admin_onboarding_page()), route="/admin/onboarding")
app.add_page(lambda: index(instituciones_page()), route="/admin/instituciones")

# =============================================================================
# LOGIN
# =============================================================================
app.add_page(login_page, route="/login")

# =============================================================================
# PORTAL — Dashboard y Autoservicio (sin guard de rol)
# =============================================================================
app.add_page(lambda: portal_index(portal_dashboard_page()), route="/portal")
app.add_page(lambda: portal_index(mis_datos_page()), route="/portal/mis-datos")
app.add_page(lambda: portal_index(mi_perfil_page()), route="/portal/mi-perfil")

# =============================================================================
# PORTAL — Mi Empresa (admin_empresa)
# =============================================================================
app.add_page(lambda: portal_index(mi_empresa_page()), route="/portal/mi-empresa")
app.add_page(lambda: portal_index(configuracion_empresa_page()), route="/portal/configuracion-empresa")

# =============================================================================
# PORTAL — RRHH (puede_gestionar_personal / puede_registrar_personal / es_rrhh)
# =============================================================================
app.add_page(lambda: portal_index(mis_empleados_page()), route="/portal/empleados")
app.add_page(lambda: portal_index(alta_masiva_page()), route="/portal/alta-masiva")
app.add_page(lambda: portal_index(onboarding_alta_page()), route="/portal/onboarding")
app.add_page(lambda: portal_index(expedientes_page()), route="/portal/expedientes")

# =============================================================================
# PORTAL — Operacion (es_operaciones / es_contabilidad)
# =============================================================================
app.add_page(lambda: portal_index(mis_contratos_page()), route="/portal/contratos")
app.add_page(lambda: portal_index(mis_entregables_page()), route="/portal/entregables")
