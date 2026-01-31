"""
Validadores personalizados para campos complejos.

Contiene validadores que requieren lógica específica más allá de
patrón/longitud simple, como RFC con feedback detallado.

Estos validadores son usados tanto por frontend (empresas_validators.py)
como por backend (entities con Pydantic).
"""
import re

from .constants import (
    RFC_PATTERN,
    RFC_PREFIX_PATTERN,
    RFC_FECHA_PATTERN,
    RFC_MIN,
    RFC_MAX,
    REGISTRO_PATRONAL_LIMPIO_PATTERN,
    REGISTRO_PATRONAL_LEN,
)
from app.core.error_messages import (
    MSG_RFC_OBLIGATORIO,
    msg_rfc_longitud,
    MSG_RFC_LETRAS_INVALIDAS,
    MSG_RFC_FECHA_INVALIDA,
    msg_rfc_homoclave_invalida,
    msg_registro_patronal_longitud,
    MSG_REGISTRO_PATRONAL_INVALIDO,
)


# =============================================================================
# VALIDADOR DE RFC
# =============================================================================

def validar_rfc_detallado(rfc: str, requerido: bool = True) -> str:
    """
    Valida RFC mexicano con feedback detallado sobre qué parte está mal.

    Usado tanto por frontend (retorna mensaje) como por Pydantic (raise ValueError).

    Args:
        rfc: RFC a validar
        requerido: Si es campo obligatorio

    Returns:
        String vacío si es válido, mensaje de error específico si no

    Example:
        >>> validar_rfc_detallado("XAXX010101AB1")
        ""
        >>> validar_rfc_detallado("ABC")
        "RFC debe tener 12 o 13 caracteres (tiene 3)"
    """
    # Campo vacío
    if not rfc or not rfc.strip():
        return MSG_RFC_OBLIGATORIO if requerido else ""

    rfc_limpio = rfc.strip().upper()

    # Validar longitud
    if len(rfc_limpio) < RFC_MIN or len(rfc_limpio) > RFC_MAX:
        return msg_rfc_longitud(len(rfc_limpio))

    # Validar patrón completo
    if re.match(RFC_PATTERN, rfc_limpio):
        return ""  # Válido

    # Feedback específico: identificar qué parte está mal

    # 1. Validar prefijo (3-4 letras)
    if not re.match(RFC_PREFIX_PATTERN, rfc_limpio[:4]):
        return MSG_RFC_LETRAS_INVALIDAS

    # 2. Validar fecha (6 dígitos después del prefijo)
    inicio = 4 if len(rfc_limpio) == 13 else 3
    fecha = rfc_limpio[inicio:inicio + 6]

    if not re.match(RFC_FECHA_PATTERN, fecha):
        return MSG_RFC_FECHA_INVALIDA

    # 3. Si llegamos aquí, es la homoclave
    return msg_rfc_homoclave_invalida(rfc_limpio[-3:])


def normalizar_rfc(rfc: str) -> str:
    """
    Normaliza un RFC (mayúsculas, sin espacios).

    Args:
        rfc: RFC a normalizar

    Returns:
        RFC normalizado
    """
    if not rfc:
        return rfc
    return rfc.strip().upper()


# =============================================================================
# VALIDADOR DE REGISTRO PATRONAL
# =============================================================================

def validar_registro_patronal_detallado(valor: str, requerido: bool = False) -> str:
    """
    Valida registro patronal IMSS con feedback detallado.

    Formato esperado: letra + 10 dígitos (Y1234567101)
    Se formatea automáticamente a: Y12-34567-10-1

    Args:
        valor: Registro patronal a validar
        requerido: Si es campo obligatorio

    Returns:
        String vacío si es válido, mensaje de error específico si no
    """
    if not valor or not valor.strip():
        return "Registro patronal es obligatorio" if requerido else ""

    # Limpiar: quitar guiones, espacios, convertir a mayúsculas
    limpio = re.sub(r'[\s\-]', '', valor.strip().upper())

    # Validar longitud
    if len(limpio) != REGISTRO_PATRONAL_LEN:
        return msg_registro_patronal_longitud(REGISTRO_PATRONAL_LEN, len(limpio))

    # Validar que inicie con letra
    if not limpio[0].isalpha():
        return "Debe iniciar con una letra"

    # Validar que el resto sean dígitos
    if not limpio[1:].isdigit():
        return "Después de la letra deben ser 10 dígitos"

    return ""


def formatear_registro_patronal(valor: str) -> str:
    """
    Formatea el registro patronal al formato estándar: Y12-34567-10-1

    Acepta:
        - Y1234567101 (sin guiones)
        - Y12-34567-10-1 (con guiones)

    Args:
        valor: Registro patronal a formatear

    Returns:
        Registro patronal formateado

    Raises:
        ValueError: Si el formato es inválido
    """
    # Limpiar: solo letras y números
    limpio = re.sub(r'[^A-Z0-9]', '', valor.upper())

    if len(limpio) != REGISTRO_PATRONAL_LEN:
        raise ValueError(msg_registro_patronal_longitud(REGISTRO_PATRONAL_LEN, len(limpio)))

    if not re.match(REGISTRO_PATRONAL_LIMPIO_PATTERN, limpio):
        raise ValueError(MSG_REGISTRO_PATRONAL_INVALIDO)

    # Formatear: Y12-34567-10-1
    return f"{limpio[0:3]}-{limpio[3:8]}-{limpio[8:10]}-{limpio[10]}"


# =============================================================================
# VALIDADOR DE TELÉFONO
# =============================================================================

def limpiar_telefono(telefono: str) -> str:
    """
    Limpia un teléfono removiendo separadores.

    Args:
        telefono: Teléfono con posibles separadores

    Returns:
        Solo dígitos
    """
    if not telefono:
        return ""
    return re.sub(r'[\s\-\(\)\+]', '', telefono.strip())
