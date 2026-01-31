"""
Repositorios de acceso a datos.

Solo se mantienen repositorios para módulos con queries complejas
(JOINs manuales, agregaciones, filtros multi-campo).

Los módulos simples (CRUD) acceden a Supabase directamente desde su servicio.
"""

# Contrato
from app.repositories.contrato_repository import SupabaseContratoRepository

# Plaza
from app.repositories.plaza_repository import SupabasePlazaRepository

# Empleado
from app.repositories.empleado_repository import SupabaseEmpleadoRepository

# Requisicion
from app.repositories.requisicion_repository import SupabaseRequisicionRepository


__all__ = [
    "SupabaseContratoRepository",
    "SupabasePlazaRepository",
    "SupabaseEmpleadoRepository",
    "SupabaseRequisicionRepository",
]
