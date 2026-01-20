"""
Validadores de formulario para contratos.

Usa crear_validador() con FieldConfig para eliminar duplicación.
Los validadores especiales usan funciones detalladas.
Usa validadores centralizados de app.core.validation para operaciones comunes.
"""
from datetime import date

from app.core.validation import (
    crear_validador,
    # Configuraciones de campos
    CAMPO_CODIGO_CONTRATO,
    CAMPO_FOLIO_BUAP,
    CAMPO_DESCRIPCION_OBJETO,
    CAMPO_ORIGEN_RECURSO,
    CAMPO_SEGMENTO_ASIGNACION,
    CAMPO_SEDE_CAMPUS,
    CAMPO_POLIZA_DETALLE,
    # Validadores centralizados
    validar_select_requerido,
    validar_fecha_requerida,
    validar_fecha_rango,
    validar_monto_opcional,
    validar_montos_min_max,
)
from app.core.error_messages import (
    msg_campos_faltantes,
    MSG_FECHA_FIN_ANTERIOR,
    MSG_TIEMPO_DETERMINADO_SIN_FIN,
    MSG_MONTO_MAX_MENOR_MIN,
)


# ============================================================================
# VALIDADORES GENERADOS DESDE FIELDCONFIG
# ============================================================================

validar_codigo = crear_validador(CAMPO_CODIGO_CONTRATO)
validar_folio_buap = crear_validador(CAMPO_FOLIO_BUAP)
validar_descripcion_objeto = crear_validador(CAMPO_DESCRIPCION_OBJETO)
validar_origen_recurso = crear_validador(CAMPO_ORIGEN_RECURSO)
validar_segmento_asignacion = crear_validador(CAMPO_SEGMENTO_ASIGNACION)
validar_sede_campus = crear_validador(CAMPO_SEDE_CAMPUS)
validar_poliza_detalle = crear_validador(CAMPO_POLIZA_DETALLE)


# ============================================================================
# VALIDADORES DE SELECCIÓN (DROPDOWNS)
# Usan validar_select_requerido centralizado
# ============================================================================

def validar_empresa_id(valor: str) -> str:
    """Valida que se haya seleccionado una empresa."""
    return validar_select_requerido(valor, "empresa")


def validar_tipo_servicio_id(valor: str) -> str:
    """Valida que se haya seleccionado un tipo de servicio."""
    return validar_select_requerido(valor, "tipo de servicio")


def validar_modalidad_adjudicacion(valor: str) -> str:
    """Valida que se haya seleccionado una modalidad de adjudicación."""
    return validar_select_requerido(valor, "modalidad de adjudicación")


def validar_tipo_duracion(valor: str) -> str:
    """Valida que se haya seleccionado un tipo de duración."""
    return validar_select_requerido(valor, "tipo de duración")


def validar_tipo_contrato(valor: str) -> str:
    """Valida que se haya seleccionado un tipo de contrato."""
    return validar_select_requerido(valor, "tipo de contrato")


# ============================================================================
# VALIDADORES DE FECHAS
# Usan validadores centralizados donde aplica
# ============================================================================

def validar_fecha_inicio(valor: str) -> str:
    """Valida la fecha de inicio del contrato."""
    return validar_fecha_requerida(valor, "fecha de inicio")


def validar_fecha_fin(
    fecha_fin: str,
    fecha_inicio: str,
    tipo_duracion: str
) -> str:
    """
    Valida la fecha de fin considerando la fecha de inicio y tipo de duración.

    Args:
        fecha_fin: Fecha de fin (puede ser vacía para tiempo indefinido)
        fecha_inicio: Fecha de inicio para comparación
        tipo_duracion: Tipo de duración del contrato

    Returns:
        Mensaje de error o cadena vacía si es válida
    """
    # Si es tiempo determinado, fecha_fin es obligatoria
    if tipo_duracion == "TIEMPO_DETERMINADO":
        if not fecha_fin:
            return MSG_TIEMPO_DETERMINADO_SIN_FIN

    # Si no hay fecha_fin, es válido (tiempo indefinido u obra determinada)
    if not fecha_fin:
        return ""

    # Validar formato
    try:
        date.fromisoformat(fecha_fin)
    except ValueError:
        return "Formato de fecha inválido (use AAAA-MM-DD)"

    # Validar rango usando validador centralizado
    error_rango = validar_fecha_rango(
        fecha_inicio, fecha_fin,
        nombre_inicio="fecha de inicio",
        nombre_fin="fecha de fin"
    )
    if error_rango:
        return MSG_FECHA_FIN_ANTERIOR

    return ""


# ============================================================================
# VALIDADORES DE MONTOS
# Usan validadores centralizados
# ============================================================================

def validar_monto_minimo(valor: str) -> str:
    """Valida el monto mínimo del contrato."""
    return validar_monto_opcional(valor, "monto mínimo")


def validar_monto_maximo(valor: str) -> str:
    """Valida el monto máximo del contrato."""
    return validar_monto_opcional(valor, "monto máximo")


def validar_montos_coherentes(monto_minimo: str, monto_maximo: str) -> str:
    """
    Valida que el monto máximo no sea menor al monto mínimo.

    Args:
        monto_minimo: Monto mínimo (string)
        monto_maximo: Monto máximo (string)

    Returns:
        Mensaje de error o cadena vacía si son coherentes
    """
    error = validar_montos_min_max(
        monto_minimo, monto_maximo,
        nombre_min="monto mínimo",
        nombre_max="monto máximo"
    )
    # Usar mensaje de error estándar del proyecto
    if error:
        return MSG_MONTO_MAX_MENOR_MIN
    return ""


# ============================================================================
# VALIDACIÓN DE FORMULARIO COMPLETO
# ============================================================================

def validar_campos_requeridos(
    empresa_id: str,
    tipo_servicio_id: str,
    modalidad: str,
    tipo_duracion: str,
    fecha_inicio: str
) -> str:
    """
    Valida que todos los campos obligatorios estén presentes.

    Args:
        empresa_id: ID de la empresa seleccionada
        tipo_servicio_id: ID del tipo de servicio seleccionado
        modalidad: Modalidad de adjudicación seleccionada
        tipo_duracion: Tipo de duración seleccionado
        fecha_inicio: Fecha de inicio del contrato

    Returns:
        Mensaje de error con campos faltantes o cadena vacía
    """
    faltantes = []

    if validar_empresa_id(empresa_id):
        faltantes.append("Empresa")

    if validar_tipo_servicio_id(tipo_servicio_id):
        faltantes.append("Tipo de servicio")

    if validar_modalidad_adjudicacion(modalidad):
        faltantes.append("Modalidad de adjudicación")

    if validar_tipo_duracion(tipo_duracion):
        faltantes.append("Tipo de duración")

    if validar_fecha_inicio(fecha_inicio):
        faltantes.append("Fecha de inicio")

    return msg_campos_faltantes(faltantes) if faltantes else ""


def validar_formulario_completo(
    empresa_id: str,
    tipo_servicio_id: str,
    modalidad: str,
    tipo_duracion: str,
    fecha_inicio: str,
    fecha_fin: str,
    monto_minimo: str,
    monto_maximo: str
) -> dict:
    """
    Valida todo el formulario de contrato y retorna errores por campo.

    Returns:
        Diccionario con errores por campo. Vacío si todo es válido.
    """
    errores = {}

    # Campos requeridos (selects)
    if error := validar_empresa_id(empresa_id):
        errores["empresa_id"] = error

    if error := validar_tipo_servicio_id(tipo_servicio_id):
        errores["tipo_servicio_id"] = error

    if error := validar_modalidad_adjudicacion(modalidad):
        errores["modalidad_adjudicacion"] = error

    if error := validar_tipo_duracion(tipo_duracion):
        errores["tipo_duracion"] = error

    # Fechas
    if error := validar_fecha_inicio(fecha_inicio):
        errores["fecha_inicio"] = error

    if error := validar_fecha_fin(fecha_fin, fecha_inicio, tipo_duracion):
        errores["fecha_fin"] = error

    # Montos
    if error := validar_monto_minimo(monto_minimo):
        errores["monto_minimo"] = error

    if error := validar_monto_maximo(monto_maximo):
        errores["monto_maximo"] = error

    # Coherencia de montos (solo si ambos tienen valor)
    if "monto_minimo" not in errores and "monto_maximo" not in errores:
        if error := validar_montos_coherentes(monto_minimo, monto_maximo):
            errores["monto_maximo"] = error

    return errores
