"""
Catálogo de INFONAVIT.

El INFONAVIT (Instituto del Fondo Nacional de la Vivienda
para los Trabajadores) es una aportación patronal obligatoria.

Fuente: Ley del INFONAVIT
"""

from decimal import Decimal
from typing import ClassVar


class CatalogoINFONAVIT:
    """
    Tasa de aportación INFONAVIT.

    Uso:
        from app.core.catalogs import CatalogoINFONAVIT

        aportacion = sbc * CatalogoINFONAVIT.TASA_PATRONAL
    """

    # ═══════════════════════════════════════════════════════════════
    # METADATOS
    # ═══════════════════════════════════════════════════════════════
    FUENTE: ClassVar[str] = "Ley del INFONAVIT"
    ARTICULO: ClassVar[str] = "Art. 29"

    # ═══════════════════════════════════════════════════════════════
    # TASA
    # ═══════════════════════════════════════════════════════════════

    # 5% del SBC (solo patronal)
    TASA_PATRONAL: ClassVar[Decimal] = Decimal("0.05")

    # Alias para compatibilidad
    TASA: ClassVar[Decimal] = TASA_PATRONAL
