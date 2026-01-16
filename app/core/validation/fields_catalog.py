"""
Catálogo de configuraciones de campos para validación.

Contiene configuraciones para:
- Empresas: nombre comercial, razón social, RFC, email, teléfono, etc.
- Tipo de Servicio: clave, nombre, descripción

Uso:
    from app.core.validation import CAMPO_RFC, crear_validador

    validar_rfc = crear_validador(CAMPO_RFC)
    error = validar_rfc("XAXX010101AB1")  # "" = válido
"""
import re

from .field_config import FieldConfig
from .constants import (
    # Patrones
    RFC_PATTERN,
    EMAIL_PATTERN,
    CODIGO_POSTAL_PATTERN,
    TELEFONO_PATTERN,
    REGISTRO_PATRONAL_LIMPIO_PATTERN,
    CLAVE_TIPO_SERVICIO_PATTERN,
    # Longitudes - Empresas
    NOMBRE_COMERCIAL_MIN,
    NOMBRE_COMERCIAL_MAX,
    RAZON_SOCIAL_MIN,
    RAZON_SOCIAL_MAX,
    RFC_MIN,
    RFC_MAX,
    DIRECCION_MAX,
    CODIGO_POSTAL_LEN,
    EMAIL_MAX,
    TELEFONO_DIGITOS,
    REGISTRO_PATRONAL_LEN,
    PAGINA_WEB_MAX,
    # Longitudes - Tipo de Servicio
    CLAVE_TIPO_MIN,
    CLAVE_TIPO_MAX,
    NOMBRE_TIPO_MIN,
    NOMBRE_TIPO_MAX,
    DESCRIPCION_TIPO_MAX,
)
from app.core.error_messages import (
    MSG_EMAIL_FORMATO_INVALIDO,
    MSG_CP_SOLO_NUMEROS,
    MSG_REGISTRO_PATRONAL_INVALIDO,
    MSG_CLAVE_SOLO_LETRAS,
    MSG_PRIMA_RIESGO_NUMERO,
    MSG_PRIMA_RIESGO_MIN,
    MSG_PRIMA_RIESGO_MAX,
)


# =============================================================================
# CAMPOS DE EMPRESA
# =============================================================================

CAMPO_NOMBRE_COMERCIAL = FieldConfig(
    nombre='Nombre comercial',
    requerido=True,
    min_len=NOMBRE_COMERCIAL_MIN,
    max_len=NOMBRE_COMERCIAL_MAX,
    transformar=str.upper
)

CAMPO_RAZON_SOCIAL = FieldConfig(
    nombre='Razón Social',
    requerido=True,
    min_len=RAZON_SOCIAL_MIN,
    max_len=RAZON_SOCIAL_MAX,
    transformar=str.upper
)

CAMPO_RFC = FieldConfig(
    nombre='RFC',
    requerido=True,
    min_len=RFC_MIN,
    max_len=RFC_MAX,
    transformar=str.upper,
    patron=RFC_PATTERN,
    patron_error='RFC no cumple el formato del SAT'
)

CAMPO_DIRECCION = FieldConfig(
    nombre='Dirección',
    requerido=False,
    max_len=DIRECCION_MAX
)

CAMPO_CODIGO_POSTAL = FieldConfig(
    nombre='Código Postal',
    requerido=False,
    min_len=CODIGO_POSTAL_LEN,
    max_len=CODIGO_POSTAL_LEN,
    patron=CODIGO_POSTAL_PATTERN,
    patron_error=MSG_CP_SOLO_NUMEROS
)

CAMPO_EMAIL = FieldConfig(
    nombre='Correo electrónico',
    requerido=False,
    max_len=EMAIL_MAX,
    patron=EMAIL_PATTERN,
    patron_error=MSG_EMAIL_FORMATO_INVALIDO,
    transformar=str.lower
)

CAMPO_TELEFONO = FieldConfig(
    nombre='Teléfono',
    requerido=False,
    min_len=TELEFONO_DIGITOS,
    max_len=TELEFONO_DIGITOS,
    patron=TELEFONO_PATTERN,
    patron_error='Debe tener 10 dígitos',
    transformar=lambda v: re.sub(r'[\s\-\(\)\+]', '', v)
)

CAMPO_PAGINA_WEB = FieldConfig(
    nombre='Página web',
    requerido=False,
    max_len=PAGINA_WEB_MAX
)

CAMPO_REGISTRO_PATRONAL = FieldConfig(
    nombre='Registro Patronal',
    requerido=False,
    min_len=REGISTRO_PATRONAL_LEN,
    max_len=REGISTRO_PATRONAL_LEN,
    patron=REGISTRO_PATRONAL_LIMPIO_PATTERN,
    patron_error=MSG_REGISTRO_PATRONAL_INVALIDO,
    transformar=lambda v: re.sub(r'[\s\-]', '', v.upper())
)


def _validar_prima_riesgo(valor: str) -> str:
    """Validador custom para prima de riesgo (0.5% - 15%)."""
    try:
        numero = float(valor)
    except ValueError:
        return MSG_PRIMA_RIESGO_NUMERO

    if numero < 0.5:
        return MSG_PRIMA_RIESGO_MIN
    if numero > 15:
        return MSG_PRIMA_RIESGO_MAX
    return ""


CAMPO_PRIMA_RIESGO = FieldConfig(
    nombre='Prima de riesgo',
    requerido=False,
    validador_custom=_validar_prima_riesgo
)

CAMPO_NOTAS = FieldConfig(
    nombre='Notas',
    requerido=False
)


# =============================================================================
# CAMPOS DE TIPO DE SERVICIO
# =============================================================================

CAMPO_CLAVE_TIPO_SERVICIO = FieldConfig(
    nombre='Clave',
    requerido=True,
    min_len=CLAVE_TIPO_MIN,
    max_len=CLAVE_TIPO_MAX,
    patron=CLAVE_TIPO_SERVICIO_PATTERN,
    patron_error=MSG_CLAVE_SOLO_LETRAS,
    transformar=str.upper
)

CAMPO_NOMBRE_TIPO_SERVICIO = FieldConfig(
    nombre='Nombre',
    requerido=True,
    min_len=NOMBRE_TIPO_MIN,
    max_len=NOMBRE_TIPO_MAX,
    transformar=str.upper
)

CAMPO_DESCRIPCION_TIPO_SERVICIO = FieldConfig(
    nombre='Descripción',
    requerido=False,
    max_len=DESCRIPCION_TIPO_MAX
)
