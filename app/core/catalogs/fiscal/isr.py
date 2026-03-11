"""
Catálogo de ISR mensual y subsidio al empleo por vigencia.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import ClassVar, Optional


@dataclass(frozen=True)
class RangoISR:
    """Representa un rango de la tabla ISR."""

    limite_inferior: Decimal
    limite_superior: Decimal
    cuota_fija: Decimal
    tasa_excedente: Decimal

    def calcular(self, base_gravable: Decimal) -> Decimal:
        if base_gravable < self.limite_inferior:
            return Decimal("0")
        excedente = base_gravable - self.limite_inferior
        return self.cuota_fija + (excedente * self.tasa_excedente)


@dataclass(frozen=True)
class PoliticaSubsidioEmpleo:
    """Monto de subsidio al empleo aplicable por fecha."""

    desde: date
    hasta: date
    porcentaje_uma_mensual: Decimal
    subsidio_mensual: Decimal
    limite_ingreso_mensual: Decimal

    def aplica_a(self, fecha_referencia: date) -> bool:
        return self.desde <= fecha_referencia <= self.hasta


class CatalogoISR:
    """Tabla ISR mensual y política de subsidio al empleo."""

    ANO: ClassVar[int] = 2026
    FUENTE: ClassVar[str] = "LISR Art. 96 y decretos de subsidio al empleo DOF"
    PUBLICACION: ClassVar[str] = "DOF"

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

    POLITICAS_SUBSIDIO: ClassVar[tuple[PoliticaSubsidioEmpleo, ...]] = (
        PoliticaSubsidioEmpleo(
            desde=date(2024, 5, 1),
            hasta=date(2024, 12, 31),
            porcentaje_uma_mensual=Decimal("0.1182"),
            subsidio_mensual=Decimal("390.12"),
            limite_ingreso_mensual=Decimal("9081.00"),
        ),
        PoliticaSubsidioEmpleo(
            desde=date(2025, 1, 1),
            hasta=date(2025, 1, 31),
            porcentaje_uma_mensual=Decimal("0.1439"),
            subsidio_mensual=Decimal("474.95"),
            limite_ingreso_mensual=Decimal("10171.00"),
        ),
        PoliticaSubsidioEmpleo(
            desde=date(2025, 2, 1),
            hasta=date(2025, 12, 31),
            porcentaje_uma_mensual=Decimal("0.1380"),
            subsidio_mensual=Decimal("474.65"),
            limite_ingreso_mensual=Decimal("10171.00"),
        ),
        PoliticaSubsidioEmpleo(
            desde=date(2026, 1, 1),
            hasta=date(2026, 1, 31),
            porcentaje_uma_mensual=Decimal("0.1559"),
            subsidio_mensual=Decimal("536.21"),
            limite_ingreso_mensual=Decimal("11492.66"),
        ),
        PoliticaSubsidioEmpleo(
            desde=date(2026, 2, 1),
            hasta=date(2026, 12, 31),
            porcentaje_uma_mensual=Decimal("0.1502"),
            subsidio_mensual=Decimal("541.40"),
            limite_ingreso_mensual=Decimal("11492.66"),
        ),
    )

    SUBSIDIO_PORCENTAJE: ClassVar[Decimal] = POLITICAS_SUBSIDIO[-1].porcentaje_uma_mensual
    SUBSIDIO_MENSUAL: ClassVar[Decimal] = POLITICAS_SUBSIDIO[-1].subsidio_mensual
    LIMITE_SUBSIDIO: ClassVar[Decimal] = POLITICAS_SUBSIDIO[-1].limite_ingreso_mensual

    @classmethod
    def _coerce_fecha(cls, fecha_referencia: date | str | None) -> date:
        if fecha_referencia is None:
            return date.today()
        if isinstance(fecha_referencia, date):
            return fecha_referencia
        return date.fromisoformat(str(fecha_referencia))

    @classmethod
    def obtener_politica_subsidio(
        cls,
        fecha_referencia: date | str | None,
        *,
        permitir_fallback: bool = False,
    ) -> PoliticaSubsidioEmpleo | None:
        fecha = cls._coerce_fecha(fecha_referencia)
        for politica in cls.POLITICAS_SUBSIDIO:
            if politica.aplica_a(fecha):
                return politica
        if not permitir_fallback:
            return None
        anteriores = [item for item in cls.POLITICAS_SUBSIDIO if item.desde <= fecha]
        if anteriores:
            return anteriores[-1]
        return cls.POLITICAS_SUBSIDIO[0] if cls.POLITICAS_SUBSIDIO else None

    @classmethod
    def obtener_rango(cls, base_gravable: Decimal) -> Optional[RangoISR]:
        for rango in cls.TABLA_MENSUAL:
            if rango.limite_inferior <= base_gravable <= rango.limite_superior:
                return rango
        return cls.TABLA_MENSUAL[-1] if base_gravable > 0 else None

    @classmethod
    def calcular_isr_mensual(
        cls,
        base_gravable: Decimal,
        fecha_referencia: date | str | None = None,
    ) -> Decimal:
        _ = fecha_referencia
        if base_gravable <= 0:
            return Decimal("0")
        rango = cls.obtener_rango(base_gravable)
        if rango is None:
            return Decimal("0")
        return rango.calcular(base_gravable)

    @classmethod
    def calcular_subsidio(
        cls,
        base_gravable: Decimal,
        fecha_referencia: date | str | None = None,
    ) -> Decimal:
        politica = cls.obtener_politica_subsidio(fecha_referencia, permitir_fallback=True)
        if politica is None:
            return Decimal("0")
        if base_gravable > politica.limite_ingreso_mensual:
            return Decimal("0")
        return politica.subsidio_mensual

    @classmethod
    def calcular_subsidio_aplicable(
        cls,
        base_gravable: Decimal,
        *,
        isr_causado: Decimal,
        fecha_referencia: date | str | None = None,
    ) -> Decimal:
        subsidio = cls.calcular_subsidio(base_gravable, fecha_referencia)
        if subsidio <= 0 or isr_causado <= 0:
            return Decimal("0")
        return min(subsidio, isr_causado)

    @classmethod
    def calcular_isr_neto(
        cls,
        base_gravable: Decimal,
        fecha_referencia: date | str | None = None,
    ) -> Decimal:
        isr = cls.calcular_isr_mensual(base_gravable, fecha_referencia)
        subsidio = cls.calcular_subsidio_aplicable(
            base_gravable,
            isr_causado=isr,
            fecha_referencia=fecha_referencia,
        )
        return isr - subsidio
