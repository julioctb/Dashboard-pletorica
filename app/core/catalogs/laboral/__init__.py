"""
Catálogos laborales de México.

Contiene prestaciones y derechos definidos por la Ley Federal del Trabajo:
- Prestaciones mínimas (aguinaldo, prima vacacional)
- Vacaciones por antigüedad
"""

from .prestaciones import CatalogoPrestaciones
from .vacaciones import CatalogoVacaciones

__all__ = [
    "CatalogoPrestaciones",
    "CatalogoVacaciones",
]
