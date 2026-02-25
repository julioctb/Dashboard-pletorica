"""Validadores de formulario (UI) para Contratos, centralizados en core.validation."""
from datetime import date

from .validator_factory import crear_validador
from .fields_catalog import (
    CAMPO_CODIGO_CONTRATO,
    CAMPO_FOLIO_BUAP,
    CAMPO_DESCRIPCION_OBJETO,
    CAMPO_ORIGEN_RECURSO,
    CAMPO_SEGMENTO_ASIGNACION,
    CAMPO_SEDE_CAMPUS,
    CAMPO_POLIZA_DETALLE,
)
from .common_validators import (
    validar_select_requerido,
    validar_fecha_requerida,
    validar_fecha_rango,
    validar_monto_opcional,
    validar_montos_min_max,
)
from app.core.error_messages import (
    msg_campos_faltantes,
    MSG_FECHA_FIN_ANTERIOR,
    MSG_TIEMPO_DETERMINADO_SIN_FIN,
    MSG_MONTO_MAX_MENOR_MIN,
)


validar_codigo_contrato = crear_validador(CAMPO_CODIGO_CONTRATO)
validar_folio_buap_contrato = crear_validador(CAMPO_FOLIO_BUAP)
validar_descripcion_objeto_contrato = crear_validador(CAMPO_DESCRIPCION_OBJETO)
validar_origen_recurso_contrato = crear_validador(CAMPO_ORIGEN_RECURSO)
validar_segmento_asignacion_contrato = crear_validador(CAMPO_SEGMENTO_ASIGNACION)
validar_sede_campus_contrato = crear_validador(CAMPO_SEDE_CAMPUS)
validar_poliza_detalle_contrato = crear_validador(CAMPO_POLIZA_DETALLE)


def validar_empresa_id_contrato(valor: str) -> str:
    return validar_select_requerido(valor, "empresa")


def validar_tipo_servicio_id_contrato(valor: str) -> str:
    return validar_select_requerido(valor, "tipo de servicio")


def validar_modalidad_adjudicacion_contrato(valor: str) -> str:
    return validar_select_requerido(valor, "modalidad de adjudicación")


def validar_tipo_duracion_contrato(valor: str) -> str:
    return validar_select_requerido(valor, "tipo de duración")


def validar_tipo_contrato_contrato(valor: str) -> str:
    return validar_select_requerido(valor, "tipo de contrato")


def validar_fecha_inicio_contrato(valor: str) -> str:
    return validar_fecha_requerida(valor, "fecha de inicio")


def validar_fecha_fin_contrato(fecha_fin: str, fecha_inicio: str, tipo_duracion: str) -> str:
    if tipo_duracion == "TIEMPO_DETERMINADO" and not fecha_fin:
        return MSG_TIEMPO_DETERMINADO_SIN_FIN
    if not fecha_fin:
        return ""
    try:
        date.fromisoformat(fecha_fin)
    except ValueError:
        return "Formato de fecha inválido (use AAAA-MM-DD)"
    if validar_fecha_rango(fecha_inicio, fecha_fin, nombre_inicio="fecha de inicio", nombre_fin="fecha de fin"):
        return MSG_FECHA_FIN_ANTERIOR
    return ""


def validar_monto_minimo_contrato(valor: str) -> str:
    return validar_monto_opcional(valor, "monto mínimo")


def validar_monto_maximo_contrato(valor: str) -> str:
    return validar_monto_opcional(valor, "monto máximo")


def validar_montos_coherentes_contrato(monto_minimo: str, monto_maximo: str) -> str:
    error = validar_montos_min_max(monto_minimo, monto_maximo, nombre_min="monto mínimo", nombre_max="monto máximo")
    return MSG_MONTO_MAX_MENOR_MIN if error else ""


def validar_campos_requeridos_contrato(
    empresa_id: str,
    tipo_servicio_id: str,
    modalidad: str,
    tipo_duracion: str,
    fecha_inicio: str,
) -> str:
    faltantes = []
    if validar_empresa_id_contrato(empresa_id):
        faltantes.append("Empresa")
    if validar_tipo_servicio_id_contrato(tipo_servicio_id):
        faltantes.append("Tipo de servicio")
    if validar_modalidad_adjudicacion_contrato(modalidad):
        faltantes.append("Modalidad de adjudicación")
    if validar_tipo_duracion_contrato(tipo_duracion):
        faltantes.append("Tipo de duración")
    if validar_fecha_inicio_contrato(fecha_inicio):
        faltantes.append("Fecha de inicio")
    return msg_campos_faltantes(faltantes) if faltantes else ""


def validar_formulario_completo_contrato(
    empresa_id: str,
    tipo_servicio_id: str,
    modalidad: str,
    tipo_duracion: str,
    fecha_inicio: str,
    fecha_fin: str,
    monto_minimo: str,
    monto_maximo: str,
) -> dict:
    errores = {}
    if error := validar_empresa_id_contrato(empresa_id):
        errores["empresa_id"] = error
    if error := validar_tipo_servicio_id_contrato(tipo_servicio_id):
        errores["tipo_servicio_id"] = error
    if error := validar_modalidad_adjudicacion_contrato(modalidad):
        errores["modalidad_adjudicacion"] = error
    if error := validar_tipo_duracion_contrato(tipo_duracion):
        errores["tipo_duracion"] = error
    if error := validar_fecha_inicio_contrato(fecha_inicio):
        errores["fecha_inicio"] = error
    if error := validar_fecha_fin_contrato(fecha_fin, fecha_inicio, tipo_duracion):
        errores["fecha_fin"] = error
    if error := validar_monto_minimo_contrato(monto_minimo):
        errores["monto_minimo"] = error
    if error := validar_monto_maximo_contrato(monto_maximo):
        errores["monto_maximo"] = error
    if "monto_minimo" not in errores and "monto_maximo" not in errores:
        if error := validar_montos_coherentes_contrato(monto_minimo, monto_maximo):
            errores["monto_maximo"] = error
    return errores


__all__ = [
    "validar_codigo_contrato",
    "validar_folio_buap_contrato",
    "validar_descripcion_objeto_contrato",
    "validar_origen_recurso_contrato",
    "validar_segmento_asignacion_contrato",
    "validar_sede_campus_contrato",
    "validar_poliza_detalle_contrato",
    "validar_empresa_id_contrato",
    "validar_tipo_servicio_id_contrato",
    "validar_modalidad_adjudicacion_contrato",
    "validar_tipo_duracion_contrato",
    "validar_tipo_contrato_contrato",
    "validar_fecha_inicio_contrato",
    "validar_fecha_fin_contrato",
    "validar_monto_minimo_contrato",
    "validar_monto_maximo_contrato",
    "validar_montos_coherentes_contrato",
    "validar_campos_requeridos_contrato",
    "validar_formulario_completo_contrato",
]
