"""Read-oriented services for the employee module."""

from core.domain.services.empleado_service import EmpleadoService, empleado_service
from core.domain.services.empleados import EmpleadoQueryService
from core.domain.services.historial_laboral_service import HistorialLaboralService, historial_laboral_service
from core.domain.services.incapacidad_service import IncapacidadService, incapacidad_service

queries___all__ = [
    "EmpleadoQueryService",
    "EmpleadoService",
    "HistorialLaboralService",
    "IncapacidadService",
    "empleado_service",
    "historial_laboral_service",
    "incapacidad_service",
]

__all__ = queries___all__
