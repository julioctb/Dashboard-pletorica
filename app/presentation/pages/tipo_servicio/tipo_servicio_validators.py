"""
Validadores de formulario para Tipos de Servicio.

Usa crear_validador() con FieldConfig para eliminar duplicación.
"""
from app.core.validation import (
    crear_validador,
    CAMPO_CLAVE_TIPO_SERVICIO,
    CAMPO_NOMBRE_TIPO_SERVICIO,
    CAMPO_DESCRIPCION_TIPO_SERVICIO,
)


# ============================================================================
# VALIDADORES GENERADOS DESDE FIELDCONFIG
# ============================================================================

validar_clave = crear_validador(CAMPO_CLAVE_TIPO_SERVICIO)
validar_nombre = crear_validador(CAMPO_NOMBRE_TIPO_SERVICIO)
validar_descripcion = crear_validador(CAMPO_DESCRIPCION_TIPO_SERVICIO)


# ============================================================================
# VALIDACIÓN DE FORMULARIO COMPLETO
# ============================================================================

def validar_formulario_tipo(clave: str, nombre: str, descripcion: str = "") -> dict:
    """
    Valida todos los campos del formulario de tipo.

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
