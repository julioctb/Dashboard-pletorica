"""
Catálogo de ISR (Impuesto Sobre la Renta).

Contiene la tabla de ISR mensual y el subsidio al empleo para
cálculo de retenciones a trabajadores.

Fuente: LISR Art. 96, Anexo 8 RMF 2026
Publicación: DOF 28/12/2025
"""

from decimal import Decimal
from typing import ClassVar, Optional
from dataclasses import dataclass


@dataclass(frozen=True)
class RangoISR:
    """Representa un rango de la tabla ISR."""
    limite_inferior: Decimal
    limite_superior: Decimal
    cuota_fija: Decimal
    tasa_excedente: Decimal  # Como decimal (0.1088 = 10.88%)

    def calcular(self, base_gravable: Decimal) -> Decimal:
        """Calcula el ISR para una base gravable en este rango."""
        if base_gravable < self.limite_inferior:
            return Decimal("0")
        excedente = base_gravable - self.limite_inferior
        return self.cuota_fija + (excedente * self.tasa_excedente)


class CatalogoISR:
    """
    Tabla ISR Mensual 2026 y Subsidio al Empleo.

    Uso:
        from app.core.catalogs import CatalogoISR

        isr = CatalogoISR.calcular_isr_mensual(Decimal("15000"))
        subsidio = CatalogoISR.calcular_subsidio(Decimal("8000"))
    """

    # ═══════════════════════════════════════════════════════════════
    # METADATOS
    # ═══════════════════════════════════════════════════════════════
    ANO: ClassVar[int] = 2026
    FUENTE: ClassVar[str] = "LISR Art. 96, Anexo 8 RMF 2026"
    PUBLICACION: ClassVar[str] = "DOF 28/12/2025"

    # ═══════════════════════════════════════════════════════════════
    # TABLA ISR MENSUAL (Art. 96 LISR)
    # ═══════════════════════════════════════════════════════════════

    TABLA_MENSUAL: ClassVar[list[RangoISR]] = [
        RangoISR(Decimal("0.01"), Decimal("844.59"), Decimal("0.00"), Decimal("0.0192")),
        RangoISR(Decimal("844.60"), Decimal("7168.51"), Decimal("16.22"), Decimal("0.0640")),
        RangoISR(Decimal("7168.52"), Decimal("12598.02"), Decimal("420.95"), Decimal("0.1088")),
        RangoISR(Decimal("12598.03"), Decimal("14644.64"), Decimal("1011.68"), Decimal("0.1600")),
        RangoISR(Decimal("14644.65"), Decimal("17533.64"), Decimal("1339.14"), Decimal("0.1792")),
        RangoISR(Decimal("17533.65"), Decimal("35362.83"), Decimal("1856.84"), Decimal("0.2136")),
        RangoISR(Decimal("35362.84"), Decimal("55736.68"), Decimal("5665.16"), Decimal("0.2352")),
        RangoISR(Decimal("55736.69"), Decimal("106410.50"), Decimal("10457.09"), Decimal("0.3000")),
        RangoISR(Decimal("106410.51"), Decimal("141880.66"), Decimal("25659.23"), Decimal("0.3200")),
        RangoISR(Decimal("141880.67"), Decimal("425641.99"), Decimal("37009.69"), Decimal("0.3400")),
        RangoISR(Decimal("425642.00"), Decimal("999999999"), Decimal("133488.54"), Decimal("0.3500")),
    ]

    # ═══════════════════════════════════════════════════════════════
    # SUBSIDIO AL EMPLEO (Decreto DOF 31-dic-2024)
    # ═══════════════════════════════════════════════════════════════

    # 13.8% del UMA mensual = $474.65 (con UMA 2026)
    SUBSIDIO_PORCENTAJE: ClassVar[Decimal] = Decimal("0.138")
    SUBSIDIO_MENSUAL: ClassVar[Decimal] = Decimal("474.65")
    LIMITE_SUBSIDIO: ClassVar[Decimal] = Decimal("10171.00")

    # ═══════════════════════════════════════════════════════════════
    # MÉTODOS DE CÁLCULO
    # ═══════════════════════════════════════════════════════════════

    @classmethod
    def obtener_rango(cls, base_gravable: Decimal) -> Optional[RangoISR]:
        """
        Obtiene el rango de ISR correspondiente a una base gravable.

        Args:
            base_gravable: Ingreso mensual gravable

        Returns:
            RangoISR correspondiente o None si no aplica
        """
        for rango in cls.TABLA_MENSUAL:
            if rango.limite_inferior <= base_gravable <= rango.limite_superior:
                return rango
        return cls.TABLA_MENSUAL[-1] if base_gravable > 0 else None

    @classmethod
    def calcular_isr_mensual(cls, base_gravable: Decimal) -> Decimal:
        """
        Calcula el ISR mensual para una base gravable.

        Args:
            base_gravable: Ingreso mensual gravable

        Returns:
            ISR a retener (antes de subsidio)
        """
        if base_gravable <= 0:
            return Decimal("0")

        rango = cls.obtener_rango(base_gravable)
        if rango is None:
            return Decimal("0")

        return rango.calcular(base_gravable)

    @classmethod
    def calcular_subsidio(cls, base_gravable: Decimal) -> Decimal:
        """
        Calcula el subsidio al empleo aplicable.

        El subsidio solo aplica si la base gravable es menor al límite.

        Args:
            base_gravable: Ingreso mensual gravable

        Returns:
            Subsidio al empleo aplicable
        """
        if base_gravable > cls.LIMITE_SUBSIDIO:
            return Decimal("0")
        return cls.SUBSIDIO_MENSUAL

    @classmethod
    def calcular_isr_neto(cls, base_gravable: Decimal) -> Decimal:
        """
        Calcula el ISR neto (ISR - subsidio).

        Args:
            base_gravable: Ingreso mensual gravable

        Returns:
            ISR neto a retener (puede ser negativo si subsidio > ISR)
        """
        isr = cls.calcular_isr_mensual(base_gravable)
        subsidio = cls.calcular_subsidio(base_gravable)
        return isr - subsidio
