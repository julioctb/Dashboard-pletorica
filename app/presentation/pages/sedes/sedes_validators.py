"""
Validadores de formulario para Sedes BUAP.

Usa crear_validador() con FieldConfig para eliminar duplicacion.
"""
from app.core.validation import (
    crear_validador,
    CAMPO_CODIGO_SEDE,
    CAMPO_NOMBRE_SEDE,
    CAMPO_NOMBRE_CORTO_SEDE,
)


# ============================================================================
# VALIDADORES GENERADOS DESDE FIELDCONFIG
# ============================================================================

validar_codigo = crear_validador(CAMPO_CODIGO_SEDE)
validar_nombre = crear_validador(CAMPO_NOMBRE_SEDE)
validar_nombre_corto = crear_validador(CAMPO_NOMBRE_CORTO_SEDE)


# ============================================================================
# VALIDACION DE FORMULARIO COMPLETO
# ============================================================================

def validar_formulario_sede(codigo: str, nombre: str, nombre_corto: str = "") -> dict:
    """
    Valida todos los campos del formulario de sede.

    Returns:
        Diccionario con errores por campo. Vacio si todo es valido.
    """
    errores = {}

    error_codigo = validar_codigo(codigo)
    if error_codigo:
        errores["codigo"] = error_codigo

    error_nombre = validar_nombre(nombre)
    if error_nombre:
        errores["nombre"] = error_nombre

    error_nombre_corto = validar_nombre_corto(nombre_corto)
    if error_nombre_corto:
        errores["nombre_corto"] = error_nombre_corto

    return errores
