"""
Validadores de formulario para Tipos de Servicio.
Funciones puras que retornan mensaje de error o string vacío si es válido.
"""
import re

from app.core.validation.constants import (
    CLAVE_TIPO_SERVICIO_PATTERN,
    CLAVE_TIPO_MIN,
    CLAVE_TIPO_MAX,
    NOMBRE_TIPO_MIN,
    NOMBRE_TIPO_MAX,
    DESCRIPCION_TIPO_MAX,
)
from app.core.error_messages import (
    MSG_CLAVE_OBLIGATORIA,
    MSG_CLAVE_SOLO_LETRAS,
    MSG_NOMBRE_OBLIGATORIO,
    msg_min_caracteres,
    msg_max_caracteres,
)


def validar_clave(clave: str) -> str:
    """
    Valida la clave del tipo de servicio.

    Args:
        clave: Clave a validar

    Returns:
        Mensaje de error o string vacío si es válido
    """
    if not clave or not clave.strip():
        return MSG_CLAVE_OBLIGATORIA

    clave_limpia = clave.strip().upper()

    if len(clave_limpia) < CLAVE_TIPO_MIN:
        return msg_min_caracteres(CLAVE_TIPO_MIN)

    if len(clave_limpia) > CLAVE_TIPO_MAX:
        return msg_max_caracteres(CLAVE_TIPO_MAX)

    if not re.match(CLAVE_TIPO_SERVICIO_PATTERN, clave_limpia):
        return MSG_CLAVE_SOLO_LETRAS

    return ""


def validar_nombre(nombre: str) -> str:
    """
    Valida el nombre del tipo de servicio.

    Args:
        nombre: Nombre a validar

    Returns:
        Mensaje de error o string vacío si es válido
    """
    if not nombre or not nombre.strip():
        return MSG_NOMBRE_OBLIGATORIO

    nombre_limpio = nombre.strip()

    if len(nombre_limpio) < NOMBRE_TIPO_MIN:
        return msg_min_caracteres(NOMBRE_TIPO_MIN)

    if len(nombre_limpio) > NOMBRE_TIPO_MAX:
        return msg_max_caracteres(NOMBRE_TIPO_MAX)

    return ""


def validar_descripcion(descripcion: str) -> str:
    """
    Valida la descripción del tipo de servicio.

    Args:
        descripcion: Descripción a validar

    Returns:
        Mensaje de error o string vacío si es válido
    """
    if not descripcion or not descripcion.strip():
        return ""  # Descripción es opcional

    if len(descripcion.strip()) > DESCRIPCION_TIPO_MAX:
        return msg_max_caracteres(DESCRIPCION_TIPO_MAX)

    return ""


def validar_formulario_tipo(clave: str, nombre: str, descripcion: str = "") -> dict:
    """
    Valida todos los campos del formulario de tipo.

    Args:
        clave: Clave del tipo
        nombre: Nombre del tipo
        descripcion: Descripción del tipo (opcional)

    Returns:
        Diccionario con errores por campo. Vacío si todo es válido.
    """
    errores = {}

    error_clave = validar_clave(clave)
    if error_clave:
        errores["clave"] = error_clave

    error_nombre = validar_nombre(nombre)
    if error_nombre:
        errores["nombre"] = error_nombre

    error_descripcion = validar_descripcion(descripcion)
    if error_descripcion:
        errores["descripcion"] = error_descripcion

    return errores
