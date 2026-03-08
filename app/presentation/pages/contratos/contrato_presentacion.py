"""Helpers de presentacion reutilizables para contratos."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from app.core.text_utils import formatear_fecha, formatear_moneda


def _get(source: Any, key: str, default=None):
    if isinstance(source, dict):
        return source.get(key, default)
    return getattr(source, key, default)


def _normalizar_fecha(valor: Any) -> date | None:
    """Convierte fechas serializadas en valores comparables para reglas de UI."""
    if not valor:
        return None
    if isinstance(valor, datetime):
        return valor.date()
    if isinstance(valor, date):
        return valor
    if not isinstance(valor, str):
        return None

    texto = valor.strip()
    if not texto:
        return None

    candidatos = [texto]
    if texto.endswith("Z"):
        candidatos.append(texto.replace("Z", "+00:00"))
    if "T" in texto:
        candidatos.append(texto.split("T", 1)[0])

    for candidato in candidatos:
        try:
            if len(candidato) <= 10:
                return date.fromisoformat(candidato)
            return datetime.fromisoformat(candidato).date()
        except ValueError:
            continue

    return None


def enriquecer_contrato_presentacion(
    contrato: Any,
    *,
    saldo_pendiente=None,
    nombre_empresa: str | None = None,
    nombre_servicio: str | None = None,
) -> dict:
    """Agrega campos derivados/formatos para mostrar contratos en UI."""
    if isinstance(contrato, dict):
        data = dict(contrato)
    elif hasattr(contrato, "model_dump"):
        data = contrato.model_dump(mode="json")
    else:
        data = dict(contrato)

    if nombre_empresa:
        data["nombre_empresa"] = nombre_empresa
    if nombre_servicio:
        data["nombre_servicio"] = nombre_servicio

    fecha_inicio = _get(contrato, "fecha_inicio")
    fecha_fin = _get(contrato, "fecha_fin")
    fecha_fin_normalizada = _normalizar_fecha(fecha_fin)
    monto_minimo = _get(contrato, "monto_minimo")
    monto_maximo = _get(contrato, "monto_maximo")

    data["fecha_inicio_fmt"] = formatear_fecha(fecha_inicio)
    data["fecha_fin_fmt"] = formatear_fecha(fecha_fin)
    data["monto_minimo_fmt"] = (
        formatear_moneda(str(monto_minimo))
        if monto_minimo is not None else "-"
    )
    data["monto_maximo_fmt"] = (
        formatear_moneda(str(monto_maximo))
        if monto_maximo is not None else "-"
    )
    data["saldo_pendiente_fmt"] = (
        formatear_moneda(str(saldo_pendiente))
        if saldo_pendiente is not None else "-"
    )
    data["vigencia_label"] = (
        "VENCIDO"
        if fecha_fin_normalizada and fecha_fin_normalizada < date.today()
        else "VIGENTE"
    )
    data["vigencia_color_scheme"] = (
        "red" if data["vigencia_label"] == "VENCIDO" else "green"
    )
    return data


def serializar_categoria_contrato_detalle(item: Any) -> dict:
    """Normaliza una categoria de contrato para mostrarla en tablas/cards."""
    costo_unitario = _get(item, "costo_unitario")
    costo_minimo = _get(item, "costo_minimo")
    costo_maximo = _get(item, "costo_maximo")

    return {
        "id": _get(item, "id"),
        "categoria_puesto_id": _get(item, "categoria_puesto_id"),
        "categoria_clave": _get(item, "categoria_clave", ""),
        "categoria_nombre": _get(item, "categoria_nombre", ""),
        "cantidad_minima": _get(item, "cantidad_minima", 0),
        "cantidad_maxima": _get(item, "cantidad_maxima", 0),
        "costo_unitario_fmt": (
            formatear_moneda(str(costo_unitario))
            if costo_unitario is not None else "-"
        ),
        "costo_minimo_fmt": (
            formatear_moneda(str(costo_minimo))
            if costo_minimo is not None else "-"
        ),
        "costo_maximo_fmt": (
            formatear_moneda(str(costo_maximo))
            if costo_maximo is not None else "-"
        ),
    }
