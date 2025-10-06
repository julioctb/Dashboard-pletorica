"""
Módulo de dominio - Reglas de negocio puras
"""

# Importar entidades
from .entities.empresa_entity import (
    EmpresaEntity,
    EmpresaResumenEntity,
    TipoEmpresa,
    EstatusEmpresa
)

# Importar interfaces
from .repositories.empresa_repository_interface import IEmpresaRepository

# Importar excepciones
from .exceptions.empresa_exceptions import (
    EmpresaDomainException,
    EmpresaNoEncontrada,
    EmpresaDuplicada,
    EmpresaInactiva,
    EmpresaTipoInvalido,
    EmpresaValidacionError,
    EmpresaOperacionNoPermitida,
    EmpresaInfrastructureException,
    EmpresaConexionError,
    EmpresaTimeoutError
)

__all__ = [
    # Entidades
    'EmpresaEntity',
    'EmpresaResumenEntity',
    'TipoEmpresa',
    'EstatusEmpresa',
    
    # Repository interface
    'IEmpresaRepository',
    
    # Excepciones
    'EmpresaDomainException',
    'EmpresaNoEncontrada',
    'EmpresaDuplicada',
    'EmpresaInactiva',
    'EmpresaTipoInvalido',
    'EmpresaValidacionError',
    'EmpresaOperacionNoPermitida',
    'EmpresaInfrastructureException',
    'EmpresaConexionError',
    'EmpresaTimeoutError'
]

