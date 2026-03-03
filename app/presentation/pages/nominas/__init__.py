"""
Módulo de Nóminas.

Páginas:
    /nominas                  → periodos_nomina_page      (RRHH + Contabilidad)
    /nominas/preparacion      → preparacion_nomina_page   (RRHH)
    /nominas/calculo          → calculo_nomina_page       (Contabilidad)
    /nominas/empleado-detalle → detalle_empleado_page     (Contabilidad)
    /nominas/dashboard        → dashboard_nomina_page     (RRHH + Contabilidad + Admin)
    /nominas/conciliacion     → conciliacion_nomina_page  (RRHH + Contabilidad + Admin)
"""
from .periodos_page import periodos_nomina_page
from .preparacion_page import preparacion_nomina_page
from .calculo_page import calculo_nomina_page
from .detalle_empleado_page import detalle_empleado_page
from .dashboard_page import dashboard_nomina_page
from .conciliacion_page import conciliacion_nomina_page

__all__ = [
    "periodos_nomina_page",
    "preparacion_nomina_page",
    "calculo_nomina_page",
    "detalle_empleado_page",
    "dashboard_nomina_page",
    "conciliacion_nomina_page",
]
