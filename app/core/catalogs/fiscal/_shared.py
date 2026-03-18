"""
Helpers privados compartidos para catálogos fiscales por vigencia.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import date
from typing import ClassVar, Generic, Protocol, TypeVar


class _VigenciaProtocol(Protocol):
    """Contrato mínimo para registros vigentes por rango de fechas."""

    desde: date
    hasta: date

    def aplica_a(self, fecha_referencia: date) -> bool: ...


T = TypeVar("T", bound=_VigenciaProtocol)


class VigenciaPorFechaMixin:
    """Mixin para dataclasses con vigencia delimitada por `desde` y `hasta`."""

    desde: date
    hasta: date

    def aplica_a(self, fecha_referencia: date) -> bool:
        return self.desde <= fecha_referencia <= self.hasta


def coerce_fecha(fecha_referencia: date | str | None) -> date:
    """Convierte fechas ISO o `date` a `date`, usando hoy como default."""
    if fecha_referencia is None:
        return date.today()
    if isinstance(fecha_referencia, date):
        return fecha_referencia
    return date.fromisoformat(str(fecha_referencia))


def resolver_vigencia(
    vigencias: Sequence[T],
    fecha_referencia: date | str | None,
    *,
    permitir_fallback: bool = False,
) -> T | None:
    """Resuelve la vigencia exacta o la última previa si se permite fallback."""
    fecha = coerce_fecha(fecha_referencia)
    for vigencia in vigencias:
        if vigencia.aplica_a(fecha):
            return vigencia
    if not permitir_fallback:
        return None
    anteriores = [vigencia for vigencia in vigencias if vigencia.desde <= fecha]
    if anteriores:
        return anteriores[-1]
    return vigencias[0] if vigencias else None


class CatalogoVigenciasMixin(Generic[T]):
    """Base para catálogos que resuelven elementos vigentes por fecha."""

    VIGENCIAS: ClassVar[Sequence[T]]

    @classmethod
    def obtener_vigencia(
        cls,
        fecha_referencia: date | str | None,
        *,
        permitir_fallback: bool = False,
    ) -> T | None:
        return resolver_vigencia(
            cls.VIGENCIAS,
            fecha_referencia,
            permitir_fallback=permitir_fallback,
        )
