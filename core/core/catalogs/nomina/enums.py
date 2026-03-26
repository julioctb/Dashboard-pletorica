"""
Enums internos del catálogo de conceptos de nómina.

Estos enums son específicos del catálogo y NO se exportan
al módulo general de enums. Son value objects del catálogo.
"""
from enum import Enum


class CategoriaConcepto(str, Enum):
    """Agrupación funcional de conceptos para la UI."""
    SUELDO = 'SUELDO'
    TIEMPO_EXTRA = 'TIEMPO_EXTRA'
    PRESTACIONES = 'PRESTACIONES'
    BONOS = 'BONOS'
    SEGURIDAD_SOCIAL = 'SEGURIDAD_SOCIAL'
    IMPUESTOS = 'IMPUESTOS'
    CREDITOS = 'CREDITOS'
    OTROS = 'OTROS'
