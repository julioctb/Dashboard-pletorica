"""Compatibilidad de validadores de Empresas (wrapper sobre core.validation)."""
from app.core.validation.empresa_form_validators import (
    validar_nombre_comercial_empresa as validar_nombre_comercial,
    validar_razon_social_empresa as validar_razon_social,
    validar_email_empresa as validar_email,
    validar_codigo_postal_empresa as validar_codigo_postal,
    validar_telefono_empresa as validar_telefono,
    validar_prima_riesgo_empresa as validar_prima_riesgo,
    validar_rfc_empresa as validar_rfc,
    validar_registro_patronal_empresa as validar_registro_patronal,
    validar_campos_requeridos_empresa as validar_campos_requeridos,
)

__all__ = [
    "validar_nombre_comercial",
    "validar_razon_social",
    "validar_email",
    "validar_codigo_postal",
    "validar_telefono",
    "validar_prima_riesgo",
    "validar_rfc",
    "validar_registro_patronal",
    "validar_campos_requeridos",
]
