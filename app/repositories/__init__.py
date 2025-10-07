"""
Repositories - Data access layer
All repositories in one place for easy discovery
"""
from .empresa_repository import IEmpresaRepository, SupabaseEmpresaRepository

__all__ = [
    'IEmpresaRepository',
    'SupabaseEmpresaRepository',
]
