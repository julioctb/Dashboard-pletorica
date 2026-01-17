"""
Enums centralizados del sistema.

Este módulo contiene todos los enums compartidos entre módulos.
Centralizar enums evita duplicación y garantiza consistencia.
"""
from enum import Enum


# =============================================================================
# ENUMS DE ESTATUS
# =============================================================================

class Estatus(str, Enum):
    """Estatus genérico para entidades (activo/inactivo)"""
    ACTIVO = 'ACTIVO'
    INACTIVO = 'INACTIVO'


class EstatusEmpresa(str, Enum):
    """Estados posibles de una empresa (incluye SUSPENDIDO)"""
    ACTIVO = 'ACTIVO'
    INACTIVO = 'INACTIVO'
    SUSPENDIDO = 'SUSPENDIDO'


# =============================================================================
# ENUMS DE TIPO
# =============================================================================

class TipoEmpresa(str, Enum):
    """Tipos de empresa en el sistema"""
    NOMINA = 'NOMINA'
    MANTENIMIENTO = 'MANTENIMIENTO'
