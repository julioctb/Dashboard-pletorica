"""
Validadores de formulario para Áreas de Servicio.
Funciones puras que retornan mensaje de error o string vacío si es válido.
"""
import re


def validar_clave(clave: str) -> str:
    """
    Valida la clave del área de servicio.

    Args:
        clave: Clave a validar

    Returns:
        Mensaje de error o string vacío si es válido
    """
    if not clave or not clave.strip():
        return "La clave es obligatoria"

    clave_limpia = clave.strip().upper()

    if len(clave_limpia) < 2:
        return "Debe tener al menos 2 caracteres"

    if len(clave_limpia) > 5:
        return "Máximo 5 caracteres"

    if not clave_limpia.isalpha():
        return "Solo se permiten letras (sin números ni símbolos)"

    return ""


def validar_nombre(nombre: str) -> str:
    """
    Valida el nombre del área de servicio.

    Args:
        nombre: Nombre a validar

    Returns:
        Mensaje de error o string vacío si es válido
    """
    if not nombre or not nombre.strip():
        return "El nombre es obligatorio"

    nombre_limpio = nombre.strip()

    if len(nombre_limpio) < 2:
        return "Debe tener al menos 2 caracteres"

    if len(nombre_limpio) > 50:
        return "Máximo 50 caracteres"

    return ""


def validar_descripcion(descripcion: str) -> str:
    """
    Valida la descripción del área de servicio.

    Args:
        descripcion: Descripción a validar

    Returns:
        Mensaje de error o string vacío si es válido
    """
    if not descripcion or not descripcion.strip():
        return ""  # Descripción es opcional

    if len(descripcion.strip()) > 500:
        return "Máximo 500 caracteres"

    return ""


def validar_formulario_area(clave: str, nombre: str, descripcion: str = "") -> dict:
    """
    Valida todos los campos del formulario de área.

    Args:
        clave: Clave del área
        nombre: Nombre del área
        descripcion: Descripción del área (opcional)

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