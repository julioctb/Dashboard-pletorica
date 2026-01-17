"""
Validadores de formulario para Categorías de Puesto.

Usa crear_validador() con FieldConfig para eliminar duplicación.
"""
from app.core.validation import (
    crear_validador,
    CAMPO_CLAVE_CATALOGO,
    CAMPO_NOMBRE_CATALOGO,
    CAMPO_DESCRIPCION_CATALOGO,
)


# ============================================================================
# VALIDADORES GENERADOS DESDE FIELDCONFIG
# ============================================================================

validar_clave = crear_validador(CAMPO_CLAVE_CATALOGO)
validar_nombre = crear_validador(CAMPO_NOMBRE_CATALOGO)
validar_descripcion = crear_validador(CAMPO_DESCRIPCION_CATALOGO)


def validar_orden(valor: str) -> str:
    """Validar campo orden"""
    if not valor:
        return ""  # Opcional
    try:
        num = int(valor)
        if num < 0:
            return "El orden debe ser mayor o igual a 0"
        return ""
    except ValueError:
        return "El orden debe ser un número entero"


def validar_tipo_servicio_id(valor: str) -> str:
    """Validar que se haya seleccionado un tipo de servicio"""
    if not valor or valor == "":
        return "Debe seleccionar un tipo de servicio"
    return ""


# ============================================================================
# VALIDACIÓN DE FORMULARIO COMPLETO
# ============================================================================

def validar_formulario_categoria(
    tipo_servicio_id: str,
    clave: str,
    nombre: str,
    descripcion: str = "",
    orden: str = ""
) -> dict:
    """
    Valida todos los campos del formulario de categoría.

    Returns:
        Diccionario con errores por campo. Vacío si todo es válido.
    """
    errores = {}

    error_tipo = validar_tipo_servicio_id(tipo_servicio_id)
    if error_tipo:
        errores["tipo_servicio_id"] = error_tipo

    error_clave = validar_clave(clave)
    if error_clave:
        errores["clave"] = error_clave

    error_nombre = validar_nombre(nombre)
    if error_nombre:
        errores["nombre"] = error_nombre

    error_descripcion = validar_descripcion(descripcion)
    if error_descripcion:
        errores["descripcion"] = error_descripcion

    error_orden = validar_orden(orden)
    if error_orden:
        errores["orden"] = error_orden

    return errores
