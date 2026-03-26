"""Portal UI surface for the nomina module."""

from core.modules.nomina.ui.backoffice import (
    NominaConciliacionState,
    NominaContabilidadState,
    NominaDashboardState,
    NominaRRHHState,
    calculo_nomina_page,
    conciliacion_nomina_page,
    dashboard_nomina_page,
    detalle_empleado_page,
    periodos_nomina_page,
    preparacion_nomina_page,
)

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
