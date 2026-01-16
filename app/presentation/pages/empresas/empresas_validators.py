"""
Validadores de formulario para empresas.
Funciones puras que retornan mensaje de error o string vacío si es válido.

Usa validadores compartidos de app.core.validation para reducir duplicación.
"""
import re

from app.core.validation.constants import (
    NOMBRE_COMERCIAL_MIN,
    NOMBRE_COMERCIAL_MAX,
    RAZON_SOCIAL_MIN,
    RAZON_SOCIAL_MAX,
    EMAIL_MAX,
    TELEFONO_DIGITOS,
    CODIGO_POSTAL_LEN,
    EMAIL_PATTERN,
)
from app.core.validation.validator_factory import (
    validar_requerido,
    validar_longitud,
    validar_patron,
)
from app.core.validation.custom_validators import (
    validar_rfc_detallado,
    validar_registro_patronal_detallado,
    limpiar_telefono,
)
from app.core.error_messages import (
    msg_campos_faltantes,
    MSG_EMAIL_FORMATO_INVALIDO,
    MSG_CP_SOLO_NUMEROS,
    msg_cp_digitos,
    MSG_TELEFONO_SOLO_NUMEROS,
    msg_telefono_digitos,
    MSG_PRIMA_RIESGO_NUMERO,
    MSG_PRIMA_RIESGO_MIN,
    MSG_PRIMA_RIESGO_MAX,
)


def validar_nombre_comercial(nombre: str) -> str:
    """Valida nombre comercial (requerido, 2-100 chars)."""
    error = validar_requerido(nombre, "Nombre comercial")
    if error:
        return error

    return validar_longitud(nombre.strip(), NOMBRE_COMERCIAL_MIN, NOMBRE_COMERCIAL_MAX, "Nombre comercial")


def validar_razon_social(razon: str) -> str:
    """Valida razón social (requerido, 2-100 chars)."""
    error = validar_requerido(razon, "Razón social")
    if error:
        return error

    return validar_longitud(razon.strip(), RAZON_SOCIAL_MIN, RAZON_SOCIAL_MAX, "Razón social")


def validar_rfc(rfc: str) -> str:
    """
    Valida RFC mexicano con homoclave.
    Usa validador compartido con feedback específico.
    """
    return validar_rfc_detallado(rfc, requerido=True)


def validar_email(email: str) -> str:
    """Valida formato de email (opcional, max 100 chars)."""
    if not email or not email.strip():
        return ""  # Opcional

    email_limpio = email.strip()

    # Validar patrón
    error = validar_patron(email_limpio, EMAIL_PATTERN, MSG_EMAIL_FORMATO_INVALIDO)
    if error:
        return error

    # Validar longitud máxima
    return validar_longitud(email_limpio, max_len=EMAIL_MAX, nombre_campo="Email")


def validar_codigo_postal(cp: str) -> str:
    """Valida código postal mexicano (opcional, 5 dígitos)."""
    if not cp or not cp.strip():
        return ""  # Opcional

    cp_limpio = cp.strip()

    if not cp_limpio.isdigit():
        return MSG_CP_SOLO_NUMEROS

    if len(cp_limpio) != CODIGO_POSTAL_LEN:
        return msg_cp_digitos(CODIGO_POSTAL_LEN, len(cp_limpio))

    return ""


def validar_telefono(telefono: str) -> str:
    """Valida teléfono mexicano (opcional, 10 dígitos, permite separadores)."""
    if not telefono or not telefono.strip():
        return ""  # Opcional

    # Usar función compartida para limpiar
    tel_solo_digitos = limpiar_telefono(telefono)

    if not tel_solo_digitos.isdigit():
        return MSG_TELEFONO_SOLO_NUMEROS

    if len(tel_solo_digitos) != TELEFONO_DIGITOS:
        return msg_telefono_digitos(TELEFONO_DIGITOS, len(tel_solo_digitos))

    return ""


def validar_registro_patronal(valor: str) -> str:
    """Valida registro patronal IMSS (opcional, letra + 10 dígitos)."""
    return validar_registro_patronal_detallado(valor, requerido=False)


def validar_prima_riesgo(valor: str) -> str:
    """Valida prima de riesgo (opcional, 0.5% - 15%)."""
    if not valor or not valor.strip():
        return ""  # Opcional

    try:
        numero = float(valor.strip())
    except ValueError:
        return MSG_PRIMA_RIESGO_NUMERO

    if numero < 0.5:
        return MSG_PRIMA_RIESGO_MIN

    if numero > 15:
        return MSG_PRIMA_RIESGO_MAX

    return ""


def validar_campos_requeridos(nombre_comercial: str, razon_social: str, rfc: str) -> str:
    """Valida que todos los campos obligatorios estén presentes."""
    faltantes = []

    if validar_requerido(nombre_comercial):
        faltantes.append("Nombre comercial")

    if validar_requerido(razon_social):
        faltantes.append("Razón social")

    if validar_requerido(rfc):
        faltantes.append("RFC")

    return msg_campos_faltantes(faltantes) if faltantes else ""
