"""Single source of truth for page route maps."""

from typing import Callable

import reflex as rx

from app.bootstrap.pages import (
    portal_onboarding_redirect_page,
    portal_plazas_redirect_page,
    root_dispatcher_page,
)
from app.modules.cotizaciones.ui.portal import cotizador_detalle_page, cotizador_page
from app.modules.empleados.ui.backoffice import empleados_page
from app.modules.empleados.ui.portal import (
    alta_masiva_redirect_page,
    bajas_page,
    empleado_ficha_page,
    incapacidades_page,
    mis_empleados_page,
)
from app.modules.nomina.ui.backoffice import (
    calculo_nomina_page,
    conciliacion_nomina_page,
    dashboard_nomina_page,
    detalle_empleado_page,
    periodos_nomina_page,
    preparacion_nomina_page,
)
from app.modules.nomina.ui.portal import (
    calculo_nomina_page as portal_calculo_nomina_page,
    conciliacion_nomina_page as portal_conciliacion_nomina_page,
    dashboard_nomina_page as portal_dashboard_nomina_page,
    detalle_empleado_page as portal_detalle_empleado_page,
    periodos_nomina_page as portal_periodos_nomina_page,
    preparacion_nomina_page as portal_preparacion_nomina_page,
)
from app.presentation.pages.backoffice.admin.dashboard import super_admin_dashboard_page
from app.presentation.pages.backoffice.admin.usuarios.usuarios_page import usuarios_admin_page
from app.presentation.pages.backoffice.admin_onboarding import admin_onboarding_page
from app.presentation.pages.backoffice.categorias_puesto.categorias_puesto_page import (
    categorias_puesto_page,
)
from app.presentation.pages.backoffice.configuracion.configuracion_page import (
    configuracion_page,
)
from app.presentation.pages.backoffice.contratos.contratos_page import contratos_page
from app.presentation.pages.backoffice.empresas.empresa_documentacion_page import (
    empresa_documentacion_page,
)
from app.presentation.pages.backoffice.empresas.empresas_page import empresas_page
from app.presentation.pages.backoffice.entregables import (
    entregable_detalle_page,
    entregables_page,
)
from app.presentation.pages.backoffice.historial_laboral.historial_laboral_page import (
    historial_laboral_page,
)
from app.presentation.pages.backoffice.instituciones.instituciones_page import (
    instituciones_page,
)
from app.presentation.pages.backoffice.login.login_page import login_page
from app.presentation.pages.backoffice.mi_perfil import mi_perfil_page
from app.presentation.pages.backoffice.pagos.pagos_page import pagos_page
from app.presentation.pages.backoffice.plazas.plazas_page import plazas_page
from app.presentation.pages.backoffice.requisiciones.requisiciones_page import (
    requisiciones_page,
)
from app.presentation.pages.backoffice.sedes.sedes_page import sedes_page
from app.presentation.pages.backoffice.shared.empresa_documentacion_share_page import (
    empresa_documentacion_share_page,
)
from app.presentation.pages.backoffice.simulador.simulador_page import simulador_page
from app.presentation.pages.backoffice.tipo_servicio.tipo_servicio_page import (
    tipo_servicio_page,
)
from app.presentation.pages.portal.asistencias import asistencias_page
from app.presentation.pages.portal.configuracion_empresa import configuracion_empresa_page
from app.presentation.pages.portal.contrato_plazas import contrato_plazas_page
from app.presentation.pages.portal.documentacion_empresa import (
    documentacion_empresa_portal_page,
)
from app.presentation.pages.portal.empresa_categorias import empresa_categorias_page
from app.presentation.pages.portal.mi_empresa import mi_empresa_page
from app.presentation.pages.portal.mis_contratos import mis_contratos_page
from app.presentation.pages.portal.mis_datos import mis_datos_page
from app.presentation.pages.portal.mis_entregables import mis_entregables_page
from app.presentation.pages.portal.portal_dashboard import portal_dashboard_page
from app.presentation.pages.portal.usuarios_empresa import usuarios_empresa_page

PageRoute = tuple[str, Callable[[], rx.Component]]

CORE_ROUTES: tuple[PageRoute, ...] = (
    ("/", root_dispatcher_page),
    ("/login", login_page),
    ("/share/empresa-documentacion/[share_token]", empresa_documentacion_share_page),
)

BACKOFFICE_PAGE_ROUTES: tuple[PageRoute, ...] = (
    ("/admin", super_admin_dashboard_page),
    ("/empresas", empresas_page),
    (
        "/empresas/[empresa_documentacion_empresa_id]/documentacion",
        empresa_documentacion_page,
    ),
    ("/contratos", contratos_page),
    ("/pagos", pagos_page),
    ("/entregables", entregables_page),
    ("/entregables/[entregable_id]", entregable_detalle_page),
    ("/wip/requisiciones", requisiciones_page),
    ("/empleados", empleados_page),
    ("/plazas", plazas_page),
    ("/historial-laboral", historial_laboral_page),
    ("/sedes", sedes_page),
    ("/tipos-servicio", tipo_servicio_page),
    ("/categorias-puesto", categorias_puesto_page),
    ("/simulador", simulador_page),
    ("/configuracion", configuracion_page),
    ("/mi-perfil", mi_perfil_page),
    ("/nominas", periodos_nomina_page),
    ("/nominas/preparacion", preparacion_nomina_page),
    ("/nominas/calculo", calculo_nomina_page),
    ("/nominas/empleado-detalle", detalle_empleado_page),
    ("/nominas/dashboard", dashboard_nomina_page),
    ("/nominas/conciliacion", conciliacion_nomina_page),
    ("/admin/usuarios", usuarios_admin_page),
    ("/admin/onboarding", admin_onboarding_page),
    ("/admin/instituciones", instituciones_page),
)

PORTAL_PAGE_ROUTES: tuple[PageRoute, ...] = (
    ("/portal", portal_dashboard_page),
    ("/portal/mis-datos", mis_datos_page),
    ("/portal/mi-perfil", mi_perfil_page),
    ("/portal/mi-empresa", mi_empresa_page),
    ("/portal/empresa/categorias", empresa_categorias_page),
    ("/portal/documentacion-empresa", documentacion_empresa_portal_page),
    ("/portal/configuracion-empresa", configuracion_empresa_page),
    ("/portal/usuarios", usuarios_empresa_page),
    ("/portal/empleados", mis_empleados_page),
    ("/portal/empleados/[uuid]", empleado_ficha_page),
    ("/portal/alta-masiva", alta_masiva_redirect_page),
    ("/portal/plazas", portal_plazas_redirect_page),
    ("/portal/onboarding", portal_onboarding_redirect_page),
    ("/portal/incapacidades", incapacidades_page),
    ("/portal/bajas", bajas_page),
    ("/portal/nominas", portal_periodos_nomina_page),
    ("/portal/nominas/preparacion", portal_preparacion_nomina_page),
    ("/portal/nominas/calculo", portal_calculo_nomina_page),
    ("/portal/nominas/empleado-detalle", portal_detalle_empleado_page),
    ("/portal/nominas/dashboard", portal_dashboard_nomina_page),
    ("/portal/nominas/conciliacion", portal_conciliacion_nomina_page),
    ("/portal/contratos", mis_contratos_page),
    ("/portal/contratos/[codigo_contrato]/plazas", contrato_plazas_page),
    ("/portal/simulador", simulador_page),
    ("/portal/cotizador", cotizador_page),
    ("/portal/cotizador/[cotizacion_id]", cotizador_detalle_page),
    ("/portal/asistencias", asistencias_page),
    ("/portal/entregables", mis_entregables_page),
)

__all__ = [
    "PageRoute",
    "CORE_ROUTES",
    "BACKOFFICE_PAGE_ROUTES",
    "PORTAL_PAGE_ROUTES",
]
