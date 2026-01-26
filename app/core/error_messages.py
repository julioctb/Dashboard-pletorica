"""
Mensajes de error centralizados.

Este módulo contiene los mensajes de error usados en validaciones,
tanto en entities (Pydantic) como en validators (frontend).

IMPORTANTE: Cualquier cambio aquí afecta ambas capas de validación.
"""


# =============================================================================
# MENSAJES GENÉRICOS
# =============================================================================

def msg_campos_faltantes(campos: list[str]) -> str:
    """Mensaje para múltiples campos faltantes."""
    return f"Campos obligatorios faltantes: {', '.join(campos)}"


# =============================================================================
# MENSAJES DE RFC
# =============================================================================

MSG_RFC_OBLIGATORIO = "RFC es obligatorio"
MSG_RFC_LETRAS_INVALIDAS = "Las primeras 3-4 letras son inválidas"
MSG_RFC_FECHA_INVALIDA = "La fecha (6 dígitos) es inválida"


def msg_rfc_longitud(actual: int) -> str:
    """Mensaje para RFC con longitud incorrecta."""
    return f"RFC debe tener 12 o 13 caracteres (tiene {actual})"


def msg_rfc_homoclave_invalida(homoclave: str) -> str:
    """Mensaje para homoclave inválida."""
    return f"La homoclave '{homoclave}' no cumple el formato del SAT"


# =============================================================================
# MENSAJES DE EMAIL
# =============================================================================

MSG_EMAIL_FORMATO_INVALIDO = "Formato de email inválido (ejemplo: usuario@dominio.com)"


# =============================================================================
# MENSAJES DE TELÉFONO Y CÓDIGO POSTAL
# =============================================================================

MSG_CP_SOLO_NUMEROS = "Solo números permitidos"


# =============================================================================
# MENSAJES DE REGISTRO PATRONAL
# =============================================================================

MSG_REGISTRO_PATRONAL_INVALIDO = "Registro patronal inválido. Debe iniciar con letra seguida de 10 dígitos"


def msg_registro_patronal_longitud(esperado: int, actual: int) -> str:
    """Mensaje para registro patronal con longitud incorrecta."""
    return f"Debe tener {esperado} caracteres (tiene {actual})"


# =============================================================================
# MENSAJES DE PRIMA DE RIESGO
# =============================================================================

MSG_PRIMA_RIESGO_NUMERO = "Debe ser un número válido (ejemplo: 2.598)"
MSG_PRIMA_RIESGO_MIN = "Mínimo 0.5%"
MSG_PRIMA_RIESGO_MAX = "Máximo 15%"
MSG_PRIMA_RIESGO_RANGO = "Prima de riesgo debe estar entre 0.5% y 15%"


# =============================================================================
# MENSAJES DE CLAVE (CATÁLOGOS)
# =============================================================================

MSG_CLAVE_SOLO_LETRAS = "Solo se permiten letras (sin números ni símbolos)"


def msg_clave_longitud(min_len: int, max_len: int) -> str:
    """Mensaje para clave con longitud fuera de rango."""
    return f"La clave debe tener entre {min_len} y {max_len} caracteres"


# =============================================================================
# MENSAJES DE ESTADO/ESTATUS
# =============================================================================

def msg_entidad_ya_estado(entidad: str, estado: str) -> str:
    """Mensaje genérico para entidad ya en cierto estado."""
    return f"{entidad} ya está {estado}"


# =============================================================================
# MENSAJES DE CONTRATO
# =============================================================================

MSG_FECHA_FIN_ANTERIOR = "La fecha de fin no puede ser anterior a la fecha de inicio"
MSG_TIEMPO_DETERMINADO_SIN_FIN = "Los contratos de tiempo determinado deben tener fecha de fin"
MSG_MONTO_MAX_MENOR_MIN = "El monto máximo no puede ser menor al monto mínimo"
MSG_CONTRATO_YA_CANCELADO = "El contrato ya está cancelado"
MSG_SOLO_SUSPENDER_ACTIVOS = "Solo se pueden suspender contratos activos"
MSG_SOLO_VENCER_ACTIVOS = "Solo se pueden marcar como vencidos contratos activos"


def msg_no_puede_activar(estado: str) -> str:
    """Mensaje cuando no se puede activar un contrato."""
    return f"No se puede activar un contrato en estado {estado}"


# =============================================================================
# MENSAJES DE REQUISICIÓN
# =============================================================================

MSG_REQUISICION_SIN_ITEMS = "La requisición debe tener al menos un item"
MSG_REQUISICION_SIN_PARTIDAS = "La requisición debe tener al menos una partida presupuestal"
MSG_SOLO_ELIMINAR_BORRADOR = "Solo se pueden eliminar requisiciones en estado BORRADOR"
MSG_ADJUDICAR_SIN_EMPRESA = "Debe seleccionar una empresa para adjudicar"
MSG_ADJUDICAR_SIN_FECHA = "Debe indicar fecha de adjudicación"
MSG_CONTRATAR_SIN_CONTRATO = "Debe existir un contrato asociado para marcar como contratada"
MSG_FECHA_ENTREGA_FIN_ANTERIOR = "La fecha de entrega fin no puede ser anterior a la fecha de entrega inicio"
MSG_REQUISICION_NO_EDITABLE = "La requisición no puede editarse en su estado actual"


def msg_transicion_invalida(estado_actual: str, estado_nuevo: str) -> str:
    """Mensaje cuando una transición de estado no es válida."""
    return f"No se puede cambiar de estado {estado_actual} a {estado_nuevo}"
