"""Backoffice UI surface for the nomina module."""

from app.presentation.pages.backoffice.nominas import (
    calculo_nomina_page,
    conciliacion_nomina_page,
    dashboard_nomina_page,
    detalle_empleado_page,
    periodos_nomina_page,
    preparacion_nomina_page,
)
from app.presentation.pages.backoffice.nominas.conciliacion_state import NominaConciliacionState
from app.presentation.pages.backoffice.nominas.dashboard_state import NominaDashboardState
from app.presentation.pages.backoffice.nominas.nomina_contabilidad_state import NominaContabilidadState
from app.presentation.pages.backoffice.nominas.nomina_rrhh_state import NominaRRHHState

__all__ = [
    "NominaConciliacionState",
    "NominaContabilidadState",
    "NominaDashboardState",
    "NominaRRHHState",
    "calculo_nomina_page",
    "conciliacion_nomina_page",
    "dashboard_nomina_page",
    "detalle_empleado_page",
    "periodos_nomina_page",
    "preparacion_nomina_page",
]
