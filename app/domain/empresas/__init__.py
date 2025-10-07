"""
Módulo de dominio de Empresas.
Exporta entidades y enums consolidados.
"""
from .entities import (
    # Entidades
    Empresa,
    EmpresaCreate,
    EmpresaUpdate,
    EmpresaResumen,
    # Enums
    TipoEmpresa,
    EstatusEmpresa,
)

__all__ = [
    # Entidades
    'Empresa',
    'EmpresaCreate',
    'EmpresaUpdate',
    'EmpresaResumen',
    # Enums
    'TipoEmpresa',
    'EstatusEmpresa',
]
