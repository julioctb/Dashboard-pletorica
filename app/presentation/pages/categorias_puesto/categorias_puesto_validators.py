"""
Validadores de formulario para Categorías de Puesto.

Usa crear_validador() con FieldConfig para eliminar duplicación.
Usa validadores centralizados de app.core.validation para operaciones comunes.
"""
from app.core.validation import (
    crear_validador,
    CAMPO_CLAVE_CATALOGO,
    CAMPO_NOMBRE_CATALOGO,
    CAMPO_DESCRIPCION_CATALOGO,
    # Validadores centralizados
    validar_select_requerido,
    validar_entero_rango,
)


# ============================================================================
# VALIDADORES GENERADOS DESDE FIELDCONFIG
# ============================================================================

validar_clave = crear_validador(CAMPO_CLAVE_CATALOGO)
validar_nombre = crear_validador(CAMPO_NOMBRE_CATALOGO)
validar_descripcion = crear_validador(CAMPO_DESCRIPCION_CATALOGO)


def validar_orden(valor: str) -> str:
    """Validar campo orden (opcional, >= 0)"""
    return validar_entero_rango(valor, "orden", minimo=0, maximo=None, requerido=False)


def validar_tipo_servicio_id(valor: str) -> str:
    """Validar que se haya seleccionado un tipo de servicio"""
    return validar_select_requerido(valor, "tipo de servicio")


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
