"""Helpers de presentacion reutilizables para contratos."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from core.core.text_utils import (
    capitalizar_palabras,
    capitalizar_con_preposiciones,
    formatear_fecha,
    formatear_moneda,
)


# Mapeos de enum → label legible (fuente: app/core/enums.py .descripcion)
_MODALIDAD_LABELS = {
    "INVITACION_3": "Invitación a cuando menos 3 personas",
    "ADJUDICACION_DIRECTA": "Adjudicación directa",
    "LICITACION_PUBLICA": "Licitación pública",
}

_TIPO_DURACION_LABELS = {
    "TIEMPO_DETERMINADO": "Tiempo determinado",
    "TIEMPO_INDEFINIDO": "Tiempo indefinido",
    "OBRA_DETERMINADA": "Obra determinada",
}

_TIPO_CONTRATO_LABELS = {
    "ADQUISICION": "Adquisición",
    "SERVICIOS": "Servicios",
}

_PLACEHOLDERS_VACIOS = {"sin empresa", "no aplica", "sin folio", "sin tipo", ""}


def _humanizar_enum(valor: str | None, mapeo: dict[str, str]) -> str:
    """Convierte un valor de enum DB a texto legible."""
    if not valor:
        return ""
    texto = str(valor).strip()
    if texto.lower() in _PLACEHOLDERS_VACIOS:
        return ""
    if texto in mapeo:
        return mapeo[texto]
    # Fallback: reemplazar _ por espacio y capitalizar
    return capitalizar_con_preposiciones(texto.replace("_", " ").lower())


def _limpiar_placeholder(valor: str | None) -> str:
    """Devuelve cadena vacía si el valor es un placeholder de datos vacíos."""
    if not valor:
        return ""
    if str(valor).strip().lower() in _PLACEHOLDERS_VACIOS:
        return ""
    return str(valor).strip()


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


def _normalizar_texto(valor: Any) -> str:
    """Normaliza textos opcionales para evitar huecos silenciosos en UI."""
    if not isinstance(valor, str):
        return ""
    return valor.strip()


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
    descripcion_objeto = _normalizar_texto(_get(contrato, "descripcion_objeto"))

    data["fecha_inicio_fmt"] = formatear_fecha(fecha_inicio)
    data["fecha_fin_fmt"] = formatear_fecha(fecha_fin)
    data["descripcion_objeto"] = descripcion_objeto
    data["descripcion_objeto_display"] = (
        descripcion_objeto if descripcion_objeto else "Sin objeto capturado"
    )
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

    # Campos humanizados para la UI
    data["modalidad_adjudicacion_fmt"] = _humanizar_enum(
        _get(contrato, "modalidad_adjudicacion"), _MODALIDAD_LABELS,
    )
    data["tipo_duracion_fmt"] = _humanizar_enum(
        _get(contrato, "tipo_duracion"), _TIPO_DURACION_LABELS,
    )
    data["tipo_contrato_fmt"] = _humanizar_enum(
        _get(contrato, "tipo_contrato"), _TIPO_CONTRATO_LABELS,
    )
    data["nombre_empresa_fmt"] = _limpiar_placeholder(
        data.get("nombre_empresa"),
    )
    data["nombre_servicio_fmt"] = _limpiar_placeholder(
        data.get("nombre_servicio"),
    )
    data["numero_folio_buap_fmt"] = _limpiar_placeholder(
        _get(contrato, "numero_folio_buap"),
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
        "categoria_clave": (_get(item, "categoria_clave", "") or "").upper(),
        "categoria_nombre": capitalizar_palabras(_get(item, "categoria_nombre", "")),
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
