"""
Catálogos fiscales de México.

Contiene tasas y valores definidos por ley:
- UMA (Unidad de Medida y Actualización)
- IMSS (Instituto Mexicano del Seguro Social)
- ISR (Impuesto Sobre la Renta)
- ISN (Impuesto Sobre Nómina por estado)
- INFONAVIT
"""

from .uma import CatalogoUMA
from .imss import CatalogoIMSS
from .isr import CatalogoISR
from .isn import CatalogoISN
from .infonavit import CatalogoINFONAVIT

__all__ = [
    "CatalogoUMA",
    "CatalogoIMSS",
    "CatalogoISR",
    "CatalogoISN",
    "CatalogoINFONAVIT",
]
