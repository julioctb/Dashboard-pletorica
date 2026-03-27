"""Repository adapters for the employee module."""

from app.domain.repositories.empleado_repository import SupabaseEmpleadoRepository
from app.domain.repositories.historial_laboral_repository import SupabaseHistorialLaboralRepository
from app.domain.repositories.incapacidad_repository import SupabaseIncapacidadRepository

repositories___all__ = [
    "SupabaseEmpleadoRepository",
    "SupabaseHistorialLaboralRepository",
    "SupabaseIncapacidadRepository",
]

__all__ = repositories___all__
