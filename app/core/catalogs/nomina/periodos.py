"""
Helpers de dominio para periodos calculados de nomina.

Centraliza:
- calendario real semanal, quincenal y mensual
- nombre persistido del periodo
- etiqueta visible para selects
- fecha de pago sugerida segun configuracion operativa
"""
from __future__ import annotations

from calendar import monthrange
from dataclasses import dataclass
from datetime import date, timedelta
import re

from app.domain.enums import PeriodicidadNomina


_MESES_ES = (
    "",
    "Enero",
    "Febrero",
    "Marzo",
    "Abril",
    "Mayo",
    "Junio",
    "Julio",
    "Agosto",
    "Septiembre",
    "Octubre",
    "Noviembre",
    "Diciembre",
)

_QUINCENA_KEY_RE = re.compile(
    r"^(?:QUINCENAL:)?(?P<year>\d{4})-(?P<month>\d{2})-(?P<half>[12])Q?$"
)
_SEMANA_KEY_RE = re.compile(r"^SEMANAL:(?P<start>\d{4}-\d{2}-\d{2})$")
_MENSUAL_KEY_RE = re.compile(r"^MENSUAL:(?P<year>\d{4})-(?P<month>\d{2})$")


@dataclass(frozen=True)
class PeriodoNominaCalculado:
    """Value object serializable para un periodo de nomina calculado."""

    key: str
    periodicidad: PeriodicidadNomina
    fecha_inicio: date
    fecha_fin: date
    nombre: str
    label: str
    fecha_pago_sugerida: date
    titulo_actual: str
    rango_actual_label: str

    def to_option(self) -> dict[str, str]:
        return {
            "key": self.key,
            "value": self.key,
            "label": self.label,
            "nombre": self.nombre,
            "periodicidad": self.periodicidad.value,
            "fecha_inicio": self.fecha_inicio.isoformat(),
            "fecha_fin": self.fecha_fin.isoformat(),
            "fecha_pago_sugerida": self.fecha_pago_sugerida.isoformat(),
            "titulo_actual": self.titulo_actual,
            "rango_actual_label": self.rango_actual_label,
        }


def _normalizar_periodicidad(
    periodicidad: str | PeriodicidadNomina,
) -> PeriodicidadNomina:
    if isinstance(periodicidad, PeriodicidadNomina):
        return periodicidad
    return PeriodicidadNomina(str(periodicidad))


def nombre_mes_es(mes: int) -> str:
    if mes < 1 or mes > 12:
        raise ValueError("Mes fuera de rango")
    return _MESES_ES[mes]


def _mes_siguiente(anio: int, mes: int) -> tuple[int, int]:
    if mes == 12:
        return anio + 1, 1
    return anio, mes + 1


def _primer_dia_mes(anio: int, mes: int) -> date:
    return date(anio, mes, 1)


def _ultimo_dia_mes(anio: int, mes: int) -> date:
    return date(anio, mes, monthrange(anio, mes)[1])


def _clamp_day(anio: int, mes: int, dia: int) -> int:
    return min(max(dia, 1), monthrange(anio, mes)[1])


def formatear_rango_periodo_corto(fecha_inicio: date, fecha_fin: date) -> str:
    """Rango legible corto para cards y selects."""
    if fecha_inicio.year == fecha_fin.year and fecha_inicio.month == fecha_fin.month:
        return (
            f"{fecha_inicio.day} - {fecha_fin.day} "
            f"{nombre_mes_es(fecha_inicio.month)}"
        )

    if fecha_inicio.year == fecha_fin.year:
        return (
            f"{fecha_inicio.day} {nombre_mes_es(fecha_inicio.month)} - "
            f"{fecha_fin.day} {nombre_mes_es(fecha_fin.month)} {fecha_fin.year}"
        )

    return (
        f"{fecha_inicio.day} {nombre_mes_es(fecha_inicio.month)} {fecha_inicio.year} - "
        f"{fecha_fin.day} {nombre_mes_es(fecha_fin.month)} {fecha_fin.year}"
    )


def calcular_rango_quincena(anio: int, mes: int, numero_quincena: int) -> tuple[date, date]:
    if numero_quincena == 1:
        return date(anio, mes, 1), date(anio, mes, 15)
    if numero_quincena == 2:
        return date(anio, mes, 16), _ultimo_dia_mes(anio, mes)
    raise ValueError("numero_quincena debe ser 1 o 2")


def compactar_nombre_quincena(fecha_inicio: date, numero_quincena: int) -> str:
    return f"{numero_quincena}A Quincena {nombre_mes_es(fecha_inicio.month)} {fecha_inicio.year}"


def etiquetar_quincena(fecha_inicio: date, fecha_fin: date, numero_quincena: int) -> str:
    mes = nombre_mes_es(fecha_inicio.month)
    return f"{numero_quincena}A Quincena {mes}: {fecha_inicio.day} - {fecha_fin.day} {mes}"


def calcular_fecha_pago_quincena(
    anio: int,
    mes: int,
    numero_quincena: int,
    dia_pago_primera_quincena: int = 15,
    dia_pago_segunda_quincena: int = 0,
) -> date:
    ultimo_dia_mes = monthrange(anio, mes)[1]

    if numero_quincena == 1:
        dia = min(max(dia_pago_primera_quincena, 1), ultimo_dia_mes)
        return date(anio, mes, dia)

    if numero_quincena != 2:
        raise ValueError("numero_quincena debe ser 1 o 2")

    if dia_pago_segunda_quincena == 0:
        return date(anio, mes, ultimo_dia_mes)

    if dia_pago_segunda_quincena >= 16:
        dia = min(dia_pago_segunda_quincena, ultimo_dia_mes)
        return date(anio, mes, dia)

    siguiente_anio, siguiente_mes = _mes_siguiente(anio, mes)
    dia = _clamp_day(siguiente_anio, siguiente_mes, dia_pago_segunda_quincena)
    return date(siguiente_anio, siguiente_mes, dia)


def construir_quincena_nomina(
    anio: int,
    mes: int,
    numero_quincena: int,
    dia_pago_primera_quincena: int = 15,
    dia_pago_segunda_quincena: int = 0,
) -> PeriodoNominaCalculado:
    fecha_inicio, fecha_fin = calcular_rango_quincena(anio, mes, numero_quincena)
    return PeriodoNominaCalculado(
        key=f"QUINCENAL:{anio:04d}-{mes:02d}-{numero_quincena}Q",
        periodicidad=PeriodicidadNomina.QUINCENAL,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        nombre=compactar_nombre_quincena(fecha_inicio, numero_quincena),
        label=etiquetar_quincena(fecha_inicio, fecha_fin, numero_quincena),
        fecha_pago_sugerida=calcular_fecha_pago_quincena(
            anio=anio,
            mes=mes,
            numero_quincena=numero_quincena,
            dia_pago_primera_quincena=dia_pago_primera_quincena,
            dia_pago_segunda_quincena=dia_pago_segunda_quincena,
        ),
        titulo_actual=nombre_mes_es(fecha_inicio.month),
        rango_actual_label=formatear_rango_periodo_corto(fecha_inicio, fecha_fin),
    )


def resolver_quincena_por_key(
    quincena_key: str,
    dia_pago_primera_quincena: int = 15,
    dia_pago_segunda_quincena: int = 0,
) -> PeriodoNominaCalculado:
    match = _QUINCENA_KEY_RE.match((quincena_key or "").strip())
    if not match:
        raise ValueError("quincena_key no tiene el formato esperado")

    return construir_quincena_nomina(
        anio=int(match.group("year")),
        mes=int(match.group("month")),
        numero_quincena=int(match.group("half")),
        dia_pago_primera_quincena=dia_pago_primera_quincena,
        dia_pago_segunda_quincena=dia_pago_segunda_quincena,
    )


def generar_catalogo_quincenas(
    fecha_inicio_catalogo: date,
    fecha_fin_catalogo: date,
    dia_pago_primera_quincena: int = 15,
    dia_pago_segunda_quincena: int = 0,
) -> list[PeriodoNominaCalculado]:
    cursor = _primer_dia_mes(fecha_inicio_catalogo.year, fecha_inicio_catalogo.month)
    limite = _primer_dia_mes(fecha_fin_catalogo.year, fecha_fin_catalogo.month)
    quincenas: list[PeriodoNominaCalculado] = []

    while cursor <= limite:
        quincenas.append(
            construir_quincena_nomina(
                anio=cursor.year,
                mes=cursor.month,
                numero_quincena=1,
                dia_pago_primera_quincena=dia_pago_primera_quincena,
                dia_pago_segunda_quincena=dia_pago_segunda_quincena,
            )
        )
        quincenas.append(
            construir_quincena_nomina(
                anio=cursor.year,
                mes=cursor.month,
                numero_quincena=2,
                dia_pago_primera_quincena=dia_pago_primera_quincena,
                dia_pago_segunda_quincena=dia_pago_segunda_quincena,
            )
        )
        siguiente_anio, siguiente_mes = _mes_siguiente(cursor.year, cursor.month)
        cursor = _primer_dia_mes(siguiente_anio, siguiente_mes)

    return quincenas


def calcular_rango_semana(fecha_referencia: date) -> tuple[date, date]:
    inicio = fecha_referencia - timedelta(days=fecha_referencia.weekday())
    return inicio, inicio + timedelta(days=6)


def calcular_fecha_pago_semanal(fecha_fin: date, dia_pago_semanal: int = 5) -> date:
    objetivo = min(max(dia_pago_semanal, 1), 7) - 1
    delta = (objetivo - fecha_fin.weekday()) % 7
    return fecha_fin + timedelta(days=delta)


def construir_semana_nomina(
    fecha_inicio_semana: date,
    dia_pago_semanal: int = 5,
) -> PeriodoNominaCalculado:
    inicio = fecha_inicio_semana - timedelta(days=fecha_inicio_semana.weekday())
    fin = inicio + timedelta(days=6)
    rango = formatear_rango_periodo_corto(inicio, fin)
    nombre = f"Semana {rango} {fin.year}" if str(fin.year) not in rango else f"Semana {rango}"
    return PeriodoNominaCalculado(
        key=f"SEMANAL:{inicio.isoformat()}",
        periodicidad=PeriodicidadNomina.SEMANAL,
        fecha_inicio=inicio,
        fecha_fin=fin,
        nombre=nombre,
        label=nombre,
        fecha_pago_sugerida=calcular_fecha_pago_semanal(fin, dia_pago_semanal),
        titulo_actual="Semana actual",
        rango_actual_label=rango,
    )


def resolver_semana_por_key(
    semana_key: str,
    dia_pago_semanal: int = 5,
) -> PeriodoNominaCalculado:
    match = _SEMANA_KEY_RE.match((semana_key or "").strip())
    if not match:
        raise ValueError("semana_key no tiene el formato esperado")
    return construir_semana_nomina(
        date.fromisoformat(match.group("start")),
        dia_pago_semanal=dia_pago_semanal,
    )


def generar_catalogo_semanas(
    fecha_inicio_catalogo: date,
    fecha_fin_catalogo: date,
    dia_pago_semanal: int = 5,
) -> list[PeriodoNominaCalculado]:
    inicio = fecha_inicio_catalogo - timedelta(days=fecha_inicio_catalogo.weekday())
    semanas: list[PeriodoNominaCalculado] = []

    while inicio <= fecha_fin_catalogo:
        semana = construir_semana_nomina(inicio, dia_pago_semanal=dia_pago_semanal)
        if semana.fecha_fin >= fecha_inicio_catalogo and semana.fecha_inicio <= fecha_fin_catalogo:
            semanas.append(semana)
        inicio += timedelta(days=7)

    return semanas


def calcular_rango_mensual(anio: int, mes: int) -> tuple[date, date]:
    return _primer_dia_mes(anio, mes), _ultimo_dia_mes(anio, mes)


def calcular_fecha_pago_mensual(
    anio: int,
    mes: int,
    dia_pago_mensual: int = 0,
) -> date:
    fecha_fin = _ultimo_dia_mes(anio, mes)
    if dia_pago_mensual == 0:
        return fecha_fin

    dia_mismo_mes = _clamp_day(anio, mes, dia_pago_mensual)
    fecha_mismo_mes = date(anio, mes, dia_mismo_mes)
    if fecha_mismo_mes >= fecha_fin:
        return fecha_mismo_mes

    siguiente_anio, siguiente_mes = _mes_siguiente(anio, mes)
    dia_sig_mes = _clamp_day(siguiente_anio, siguiente_mes, dia_pago_mensual)
    return date(siguiente_anio, siguiente_mes, dia_sig_mes)


def construir_mes_nomina(
    anio: int,
    mes: int,
    dia_pago_mensual: int = 0,
) -> PeriodoNominaCalculado:
    fecha_inicio, fecha_fin = calcular_rango_mensual(anio, mes)
    nombre_mes = nombre_mes_es(mes)
    nombre = f"Nomina {nombre_mes} {anio}"
    return PeriodoNominaCalculado(
        key=f"MENSUAL:{anio:04d}-{mes:02d}",
        periodicidad=PeriodicidadNomina.MENSUAL,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        nombre=nombre,
        label=nombre,
        fecha_pago_sugerida=calcular_fecha_pago_mensual(
            anio=anio,
            mes=mes,
            dia_pago_mensual=dia_pago_mensual,
        ),
        titulo_actual=nombre_mes,
        rango_actual_label=formatear_rango_periodo_corto(fecha_inicio, fecha_fin),
    )


def resolver_mes_por_key(
    mes_key: str,
    dia_pago_mensual: int = 0,
) -> PeriodoNominaCalculado:
    match = _MENSUAL_KEY_RE.match((mes_key or "").strip())
    if not match:
        raise ValueError("mes_key no tiene el formato esperado")
    return construir_mes_nomina(
        anio=int(match.group("year")),
        mes=int(match.group("month")),
        dia_pago_mensual=dia_pago_mensual,
    )


def generar_catalogo_meses(
    fecha_inicio_catalogo: date,
    fecha_fin_catalogo: date,
    dia_pago_mensual: int = 0,
) -> list[PeriodoNominaCalculado]:
    cursor = _primer_dia_mes(fecha_inicio_catalogo.year, fecha_inicio_catalogo.month)
    limite = _primer_dia_mes(fecha_fin_catalogo.year, fecha_fin_catalogo.month)
    meses: list[PeriodoNominaCalculado] = []

    while cursor <= limite:
        meses.append(
            construir_mes_nomina(
                anio=cursor.year,
                mes=cursor.month,
                dia_pago_mensual=dia_pago_mensual,
            )
        )
        siguiente_anio, siguiente_mes = _mes_siguiente(cursor.year, cursor.month)
        cursor = _primer_dia_mes(siguiente_anio, siguiente_mes)

    return meses


def resolver_periodo_por_key(
    periodo_key: str,
    periodicidad: str | PeriodicidadNomina,
    *,
    dia_pago_primera_quincena: int = 15,
    dia_pago_segunda_quincena: int = 0,
    dia_pago_semanal: int = 5,
    dia_pago_mensual: int = 0,
) -> PeriodoNominaCalculado:
    periodicidad_resuelta = _normalizar_periodicidad(periodicidad)

    if periodicidad_resuelta == PeriodicidadNomina.QUINCENAL:
        return resolver_quincena_por_key(
            periodo_key,
            dia_pago_primera_quincena=dia_pago_primera_quincena,
            dia_pago_segunda_quincena=dia_pago_segunda_quincena,
        )
    if periodicidad_resuelta == PeriodicidadNomina.SEMANAL:
        return resolver_semana_por_key(
            periodo_key,
            dia_pago_semanal=dia_pago_semanal,
        )
    return resolver_mes_por_key(
        periodo_key,
        dia_pago_mensual=dia_pago_mensual,
    )


def generar_catalogo_periodos(
    periodicidad: str | PeriodicidadNomina,
    *,
    fecha_inicio_catalogo: date,
    fecha_fin_catalogo: date,
    dia_pago_primera_quincena: int = 15,
    dia_pago_segunda_quincena: int = 0,
    dia_pago_semanal: int = 5,
    dia_pago_mensual: int = 0,
) -> list[PeriodoNominaCalculado]:
    periodicidad_resuelta = _normalizar_periodicidad(periodicidad)

    if periodicidad_resuelta == PeriodicidadNomina.QUINCENAL:
        return generar_catalogo_quincenas(
            fecha_inicio_catalogo=fecha_inicio_catalogo,
            fecha_fin_catalogo=fecha_fin_catalogo,
            dia_pago_primera_quincena=dia_pago_primera_quincena,
            dia_pago_segunda_quincena=dia_pago_segunda_quincena,
        )
    if periodicidad_resuelta == PeriodicidadNomina.SEMANAL:
        return generar_catalogo_semanas(
            fecha_inicio_catalogo=fecha_inicio_catalogo,
            fecha_fin_catalogo=fecha_fin_catalogo,
            dia_pago_semanal=dia_pago_semanal,
        )
    return generar_catalogo_meses(
        fecha_inicio_catalogo=fecha_inicio_catalogo,
        fecha_fin_catalogo=fecha_fin_catalogo,
        dia_pago_mensual=dia_pago_mensual,
    )


def detectar_periodo_actual(
    periodicidad: str | PeriodicidadNomina,
    *,
    fecha_referencia: date | None = None,
    dia_pago_primera_quincena: int = 15,
    dia_pago_segunda_quincena: int = 0,
    dia_pago_semanal: int = 5,
    dia_pago_mensual: int = 0,
) -> PeriodoNominaCalculado:
    referencia = fecha_referencia or date.today()
    periodicidad_resuelta = _normalizar_periodicidad(periodicidad)

    if periodicidad_resuelta == PeriodicidadNomina.QUINCENAL:
        numero_quincena = 1 if referencia.day <= 15 else 2
        return construir_quincena_nomina(
            anio=referencia.year,
            mes=referencia.month,
            numero_quincena=numero_quincena,
            dia_pago_primera_quincena=dia_pago_primera_quincena,
            dia_pago_segunda_quincena=dia_pago_segunda_quincena,
        )

    if periodicidad_resuelta == PeriodicidadNomina.SEMANAL:
        return construir_semana_nomina(
            referencia,
            dia_pago_semanal=dia_pago_semanal,
        )

    return construir_mes_nomina(
        anio=referencia.year,
        mes=referencia.month,
        dia_pago_mensual=dia_pago_mensual,
    )
