"""
Catálogos centralizados de datos maestros.

Este módulo organiza todos los datos de referencia del sistema:
- Fiscales: UMA, IMSS, ISR, ISN, INFONAVIT
- Laborales: Prestaciones mínimas LFT, vacaciones
- Sistema: Tolerancias y configuración de algoritmos

Uso:
    from app.core.catalogs import CatalogoUMA, CatalogoIMSS, CatalogoPrestaciones

    uma = CatalogoUMA.DIARIO  # $113.14
    tasa = CatalogoIMSS.CUOTA_FIJA  # 0.204
    dias = CatalogoPrestaciones.AGUINALDO_DIAS  # 15
"""

# Fiscal
from .fiscal import (
    CatalogoUMA,
    CatalogoIMSS,
    CatalogoISR,
    CatalogoISN,
    CatalogoINFONAVIT,
)

# Laboral
from .laboral import (
    CatalogoPrestaciones,
    CatalogoVacaciones,
)

# Sistema
from .sistema import (
    Tolerancias,
    LimitesValidacion,
)

__all__ = [
    # Fiscal
    "CatalogoUMA",
    "CatalogoIMSS",
    "CatalogoISR",
    "CatalogoISN",
    "CatalogoINFONAVIT",
    # Laboral
    "CatalogoPrestaciones",
    "CatalogoVacaciones",
    # Sistema
    "Tolerancias",
    "LimitesValidacion",
]
