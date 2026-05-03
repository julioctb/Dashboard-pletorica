"""
Catálogo de UMA (Unidad de Medida y Actualización) por vigencia.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from typing import ClassVar

from ._shared import CatalogoVigenciasMixin, VigenciaPorFechaMixin


@dataclass(frozen=True)
class VigenciaUMA(VigenciaPorFechaMixin):
    """Valor de UMA vigente para un rango de fechas."""

    desde: date
    hasta: date
    diario: Decimal

    @property
    def mensual(self) -> Decimal:
        return (self.diario * Decimal("30.4")).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP,
        )

    @property
    def anual(self) -> Decimal:
        return (self.diario * Decimal("365")).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP,
        )

class CatalogoUMA(CatalogoVigenciasMixin[VigenciaUMA]):
    """Resuelve UMA diaria, mensual y topes por fecha."""

    VIGENCIAS: ClassVar[tuple[VigenciaUMA, ...]] = (
        VigenciaUMA(
            desde=date(2024, 2, 1),
            hasta=date(2025, 1, 31),
            diario=Decimal("108.57"),
        ),
        VigenciaUMA(
            desde=date(2025, 2, 1),
            hasta=date(2026, 1, 31),
            diario=Decimal("113.14"),
        ),
        VigenciaUMA(
            desde=date(2026, 2, 1),
            hasta=date(2027, 1, 31),
            diario=Decimal("117.31"),
        ),
    )

    ANO: ClassVar[int] = 2026
    VIGENCIA_DESDE: ClassVar[str] = VIGENCIAS[-1].desde.isoformat()
    VIGENCIA_HASTA: ClassVar[str] = VIGENCIAS[-1].hasta.isoformat()
    FUENTE: ClassVar[str] = "INEGI, DOF"

    DIARIO: ClassVar[Decimal] = VIGENCIAS[-1].diario
    MENSUAL: ClassVar[Decimal] = VIGENCIAS[-1].mensual
    ANUAL: ClassVar[Decimal] = VIGENCIAS[-1].anual
    HISTORICO: ClassVar[dict[int, Decimal]] = {
        2024: Decimal("108.57"),
        2025: Decimal("113.14"),
        2026: Decimal("117.31"),
    }
    TRES_UMA: ClassVar[Decimal] = DIARIO * 3
    TOPE_SBC: ClassVar[Decimal] = DIARIO * 25

    @classmethod
    def obtener(cls, ano: int = 2026) -> Decimal:
        return cls.HISTORICO.get(ano, cls.DIARIO)

    @classmethod
    def diario_vigente(
        cls,
        fecha_referencia: date | str | None,
        *,
        permitir_fallback: bool = False,
    ) -> Decimal | None:
        vigencia = cls.obtener_vigencia(
            fecha_referencia,
            permitir_fallback=permitir_fallback,
        )
        return vigencia.diario if vigencia is not None else None

    @classmethod
    def mensual_vigente(
        cls,
        fecha_referencia: date | str | None,
        *,
        permitir_fallback: bool = False,
    ) -> Decimal | None:
        vigencia = cls.obtener_vigencia(
            fecha_referencia,
            permitir_fallback=permitir_fallback,
        )
        return vigencia.mensual if vigencia is not None else None

    @classmethod
    def anual_vigente(
        cls,
        fecha_referencia: date | str | None,
        *,
        permitir_fallback: bool = False,
    ) -> Decimal | None:
        vigencia = cls.obtener_vigencia(
            fecha_referencia,
            permitir_fallback=permitir_fallback,
        )
        return vigencia.anual if vigencia is not None else None

    @classmethod
    def mensual(cls, ano: int = 2026) -> Decimal:
        return (cls.obtener(ano) * Decimal("30.4")).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP,
        )

    @classmethod
    def tope_sbc(cls, ano: int = 2026) -> Decimal:
        return cls.obtener(ano) * 25

    @classmethod
    def tope_sbc_vigente(
        cls,
        fecha_referencia: date | str | None,
        *,
        permitir_fallback: bool = False,
    ) -> Decimal | None:
        diario = cls.diario_vigente(
            fecha_referencia,
            permitir_fallback=permitir_fallback,
        )
        return (diario * Decimal("25")) if diario is not None else None

    @classmethod
    def tres_uma(cls, ano: int = 2026) -> Decimal:
        return cls.obtener(ano) * 3

    @classmethod
    def tres_uma_vigente(
        cls,
        fecha_referencia: date | str | None,
        *,
        permitir_fallback: bool = False,
    ) -> Decimal | None:
        diario = cls.diario_vigente(
            fecha_referencia,
            permitir_fallback=permitir_fallback,
        )
        return (diario * Decimal("3")) if diario is not None else None
