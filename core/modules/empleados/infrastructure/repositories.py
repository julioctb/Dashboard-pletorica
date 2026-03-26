"""Repository adapters for the employee module."""

from core.domain.repositories.empleado_repository import SupabaseEmpleadoRepository
from core.domain.repositories.historial_laboral_repository import SupabaseHistorialLaboralRepository
from core.domain.repositories.incapacidad_repository import SupabaseIncapacidadRepository

repositories___all__ = [
    "SupabaseEmpleadoRepository",
    "SupabaseHistorialLaboralRepository",
    "SupabaseIncapacidadRepository",
]

__all__ = repositories___all__
