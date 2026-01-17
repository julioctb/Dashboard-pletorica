"""
Catálogo de UMA (Unidad de Medida y Actualización).

La UMA es la referencia económica para determinar la cuantía de obligaciones
y supuestos previstos en las leyes federales. Sustituye al salario mínimo
como unidad de referencia.

Fuente: INEGI
Publicación: DOF (Diario Oficial de la Federación)
Vigencia: Del 1 de febrero al 31 de enero del siguiente año
"""

from decimal import Decimal
from typing import ClassVar


class CatalogoUMA:
    """
    Valores de la UMA (Unidad de Medida y Actualización) 2026.

    La UMA se publica en enero y entra en vigor el 1 de febrero.
    Los valores se calculan a partir del valor diario.

    Uso:
        from app.core.catalogs import CatalogoUMA

        uma_diario = CatalogoUMA.DIARIO  # $113.14
        tope_sbc = CatalogoUMA.tope_sbc()  # 25 UMA
    """

    # ═══════════════════════════════════════════════════════════════
    # METADATOS
    # ═══════════════════════════════════════════════════════════════
    ANO: ClassVar[int] = 2026
    VIGENCIA_DESDE: ClassVar[str] = "2025-02-01"
    VIGENCIA_HASTA: ClassVar[str] = "2026-01-31"
    FUENTE: ClassVar[str] = "INEGI, DOF"

    # ═══════════════════════════════════════════════════════════════
    # VALORES UMA 2026
    # ═══════════════════════════════════════════════════════════════
    DIARIO: ClassVar[Decimal] = Decimal("113.14")
    MENSUAL: ClassVar[Decimal] = Decimal("3439.46")  # DIARIO * 30.4
    ANUAL: ClassVar[Decimal] = Decimal("41273.52")   # DIARIO * 365

    # ═══════════════════════════════════════════════════════════════
    # HISTÓRICO (para cálculos retroactivos)
    # ═══════════════════════════════════════════════════════════════
    HISTORICO: ClassVar[dict[int, Decimal]] = {
        2026: Decimal("113.14"),
        2025: Decimal("108.57"),
        2024: Decimal("103.74"),
        2023: Decimal("96.22"),
        2022: Decimal("96.22"),
        2021: Decimal("89.62"),
        2020: Decimal("86.88"),
    }

    # ═══════════════════════════════════════════════════════════════
    # MULTIPLICADORES COMUNES
    # ═══════════════════════════════════════════════════════════════
    TRES_UMA: ClassVar[Decimal] = DIARIO * 3    # Base para excedente IMSS
    TOPE_SBC: ClassVar[Decimal] = DIARIO * 25   # Tope SBC = 25 UMA

    # ═══════════════════════════════════════════════════════════════
    # MÉTODOS
    # ═══════════════════════════════════════════════════════════════

    @classmethod
    def obtener(cls, ano: int = 2026) -> Decimal:
        """
        Obtiene el valor diario de la UMA para un año específico.

        Args:
            ano: Año fiscal (default: 2026)

        Returns:
            Valor diario de la UMA
        """
        return cls.HISTORICO.get(ano, cls.DIARIO)

    @classmethod
    def mensual(cls, ano: int = 2026) -> Decimal:
        """Calcula el valor mensual de la UMA (diario * 30.4)."""
        return cls.obtener(ano) * Decimal("30.4")

    @classmethod
    def tope_sbc(cls, ano: int = 2026) -> Decimal:
        """Calcula el tope de SBC diario (25 UMA)."""
        return cls.obtener(ano) * 25

    @classmethod
    def tres_uma(cls, ano: int = 2026) -> Decimal:
        """Calcula 3 UMA (base para excedente IMSS)."""
        return cls.obtener(ano) * 3
