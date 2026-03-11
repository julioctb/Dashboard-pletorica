"""
Catálogo de salario mínimo por vigencia oficial.

Fuente: CONASAMI / DOF.
La vigencia corre por año calendario.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import ClassVar


@dataclass(frozen=True)
class VigenciaSalarioMinimo:
    """Salario mínimo general y de frontera para una vigencia."""

    desde: date
    hasta: date
    general: Decimal
    frontera: Decimal

    def aplica_a(self, fecha_referencia: date) -> bool:
        return self.desde <= fecha_referencia <= self.hasta


class CatalogoSalarioMinimo:
    """Resuelve salario mínimo aplicable por fecha y zona."""

    VIGENCIAS: ClassVar[tuple[VigenciaSalarioMinimo, ...]] = (
        VigenciaSalarioMinimo(
            desde=date(2024, 1, 1),
            hasta=date(2024, 12, 31),
            general=Decimal("248.93"),
            frontera=Decimal("374.89"),
        ),
        VigenciaSalarioMinimo(
            desde=date(2025, 1, 1),
            hasta=date(2025, 12, 31),
            general=Decimal("278.80"),
            frontera=Decimal("419.88"),
        ),
        VigenciaSalarioMinimo(
            desde=date(2026, 1, 1),
            hasta=date(2026, 12, 31),
            general=Decimal("315.04"),
            frontera=Decimal("440.87"),
        ),
    )

    GENERAL: ClassVar[Decimal] = VIGENCIAS[-1].general
    FRONTERA: ClassVar[Decimal] = VIGENCIAS[-1].frontera

    @classmethod
    def _coerce_fecha(cls, fecha_referencia: date | str | None) -> date:
        if fecha_referencia is None:
            return date.today()
        if isinstance(fecha_referencia, date):
            return fecha_referencia
        return date.fromisoformat(str(fecha_referencia))

    @classmethod
    def obtener_vigencia(
        cls,
        fecha_referencia: date | str | None,
        *,
        permitir_fallback: bool = False,
    ) -> VigenciaSalarioMinimo | None:
        fecha = cls._coerce_fecha(fecha_referencia)
        for vigencia in cls.VIGENCIAS:
            if vigencia.aplica_a(fecha):
                return vigencia
        if not permitir_fallback:
            return None
        anteriores = [vigencia for vigencia in cls.VIGENCIAS if vigencia.desde <= fecha]
        if anteriores:
            return anteriores[-1]
        return cls.VIGENCIAS[0] if cls.VIGENCIAS else None

    @classmethod
    def diario_vigente(
        cls,
        fecha_referencia: date | str | None,
        *,
        zona_frontera: bool = False,
        permitir_fallback: bool = False,
    ) -> Decimal | None:
        vigencia = cls.obtener_vigencia(
            fecha_referencia,
            permitir_fallback=permitir_fallback,
        )
        if vigencia is None:
            return None
        return vigencia.frontera if zona_frontera else vigencia.general
