"""
Catálogos de configuración del sistema.

Contiene valores técnicos para algoritmos y validaciones:
- Tolerancias numéricas para cálculos
- Límites de validación para campos
"""

from .tolerancias import Tolerancias
from .limites import LimitesValidacion

__all__ = [
    "Tolerancias",
    "LimitesValidacion",
]
