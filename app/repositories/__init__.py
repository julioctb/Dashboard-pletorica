"""
Repositorios de acceso a datos.

Este módulo exporta todos los repositorios para facilitar imports:
    from app.repositories import SupabaseEmpresaRepository, etc.
"""

# Empresa
from app.repositories.empresa_repository import (
    IEmpresaRepository,
    SupabaseEmpresaRepository,
)

# Área de Servicio
from app.repositories.area_servicio_repository import (
    IAreaServicioRepository,
    SupabaseAreaServicioRepository,
)


__all__ = [
    # Empresa
    "IEmpresaRepository",
    "SupabaseEmpresaRepository",
    # Área de Servicio
    "IAreaServicioRepository",
    "SupabaseAreaServicioRepository",
]