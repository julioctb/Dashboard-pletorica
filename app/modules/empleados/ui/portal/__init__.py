"""Portal UI surface for the employee module."""

from app.presentation.pages.portal.bajas import BajasState, bajas_page
from app.presentation.pages.portal.empleado_ficha import EmpleadoFichaState, empleado_ficha_page
from app.presentation.pages.portal.incapacidades import IncapacidadState, incapacidades_page
from app.presentation.pages.portal.mis_empleados import (
    MisEmpleadosState,
    alta_masiva_redirect_page,
    mis_empleados_page,
)

__all__ = [
    "BajasState",
    "EmpleadoFichaState",
    "IncapacidadState",
    "MisEmpleadosState",
    "alta_masiva_redirect_page",
    "bajas_page",
    "empleado_ficha_page",
    "incapacidades_page",
    "mis_empleados_page",
]
