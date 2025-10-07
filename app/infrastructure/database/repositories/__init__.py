"""Repositorios de base de datos"""
from .empresa_repository import IEmpresaRepository, SupabaseEmpresaRepository

__all__ = [
    'IEmpresaRepository',
    'SupabaseEmpresaRepository',
]
