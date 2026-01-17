"""
Validadores de formulario para empresas.

Usa crear_validador() con FieldConfig para eliminar duplicación.
Los validadores especiales (RFC, registro patronal) usan funciones detalladas.
"""
from app.core.validation import (
    crear_validador,
    validar_requerido,
    validar_rfc_detallado,
    validar_registro_patronal_detallado,
    # Configuraciones de campos
    CAMPO_NOMBRE_COMERCIAL,
    CAMPO_RAZON_SOCIAL,
    CAMPO_EMAIL,
    CAMPO_CODIGO_POSTAL,
    CAMPO_TELEFONO,
    CAMPO_PRIMA_RIESGO,
)
from app.core.error_messages import msg_campos_faltantes


# ============================================================================
# VALIDADORES GENERADOS DESDE FIELDCONFIG
# ============================================================================

validar_nombre_comercial = crear_validador(CAMPO_NOMBRE_COMERCIAL)
validar_razon_social = crear_validador(CAMPO_RAZON_SOCIAL)
validar_email = crear_validador(CAMPO_EMAIL)
validar_codigo_postal = crear_validador(CAMPO_CODIGO_POSTAL)
validar_telefono = crear_validador(CAMPO_TELEFONO)
validar_prima_riesgo = crear_validador(CAMPO_PRIMA_RIESGO)


# ============================================================================
# VALIDADORES ESPECIALES (requieren lógica custom)
# ============================================================================

def validar_rfc(rfc: str) -> str:
    """Valida RFC con feedback detallado."""
    return validar_rfc_detallado(rfc, requerido=True)


def validar_registro_patronal(valor: str) -> str:
    """Valida registro patronal IMSS."""
    return validar_registro_patronal_detallado(valor, requerido=False)


# ============================================================================
# VALIDACIÓN DE FORMULARIO COMPLETO
# ============================================================================

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
