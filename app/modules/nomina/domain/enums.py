"""Nomina domain enums split from the legacy global enum registry."""

from app.domain.enums import (
    EstatusNominaEmpleado,
    EstatusPeriodoNomina,
    ModoCalculoAguinaldo,
    OrigenCaptura,
    OrigenMovimiento,
    PeriodicidadNomina,
    ReglaCalculoQuincenal,
    TipoConcepto,
    TipoPeriodoNomina,
    TratamientoISR,
)

enums___all__ = [
    "EstatusNominaEmpleado",
    "EstatusPeriodoNomina",
    "ModoCalculoAguinaldo",
    "OrigenCaptura",
    "OrigenMovimiento",
    "PeriodicidadNomina",
    "ReglaCalculoQuincenal",
    "TipoConcepto",
    "TipoPeriodoNomina",
    "TratamientoISR",
]

__all__ = enums___all__
