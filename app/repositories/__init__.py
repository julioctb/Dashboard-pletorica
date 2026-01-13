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

# Tipo de Servicio
from app.repositories.tipo_servicio_repository import (
    ITipoServicioRepository,
    SupabaseTipoServicioRepository,
)


__all__ = [
    # Empresa
    "IEmpresaRepository",
    "SupabaseEmpresaRepository",
    # Tipo de Servicio
    "ITipoServicioRepository",
    "SupabaseTipoServicioRepository",
]