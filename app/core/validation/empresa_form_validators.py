"""Validadores de formulario (UI) para Empresas, centralizados en core.validation."""
from .validator_factory import crear_validador, validar_requerido
from .custom_validators import validar_rfc_detallado, validar_registro_patronal_detallado
from .fields_catalog import (
    CAMPO_NOMBRE_COMERCIAL,
    CAMPO_RAZON_SOCIAL,
    CAMPO_EMAIL,
    CAMPO_CODIGO_POSTAL,
    CAMPO_TELEFONO,
    CAMPO_PRIMA_RIESGO,
)
from app.core.error_messages import msg_campos_faltantes


validar_nombre_comercial_empresa = crear_validador(CAMPO_NOMBRE_COMERCIAL)
validar_razon_social_empresa = crear_validador(CAMPO_RAZON_SOCIAL)
validar_email_empresa = crear_validador(CAMPO_EMAIL)
validar_codigo_postal_empresa = crear_validador(CAMPO_CODIGO_POSTAL)
validar_telefono_empresa = crear_validador(CAMPO_TELEFONO)
validar_prima_riesgo_empresa = crear_validador(CAMPO_PRIMA_RIESGO)


def validar_rfc_empresa(rfc: str) -> str:
    return validar_rfc_detallado(rfc, requerido=True)


def validar_registro_patronal_empresa(valor: str) -> str:
    return validar_registro_patronal_detallado(valor, requerido=False)


def validar_campos_requeridos_empresa(nombre_comercial: str, razon_social: str, rfc: str) -> str:
    faltantes = []
    if validar_requerido(nombre_comercial):
        faltantes.append("Nombre comercial")
    if validar_requerido(razon_social):
        faltantes.append("Razón social")
    if validar_requerido(rfc):
        faltantes.append("RFC")
    return msg_campos_faltantes(faltantes) if faltantes else ""


__all__ = [
    "validar_nombre_comercial_empresa",
    "validar_razon_social_empresa",
    "validar_email_empresa",
    "validar_codigo_postal_empresa",
    "validar_telefono_empresa",
    "validar_prima_riesgo_empresa",
    "validar_rfc_empresa",
    "validar_registro_patronal_empresa",
    "validar_campos_requeridos_empresa",
]
