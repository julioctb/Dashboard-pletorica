"""
Mensajes de error centralizados.

Este módulo contiene los mensajes de error usados en validaciones,
tanto en entities (Pydantic) como en validators (frontend).

IMPORTANTE: Cualquier cambio aquí afecta ambas capas de validación.
"""


# =============================================================================
# MENSAJES GENÉRICOS
# =============================================================================

def msg_min_caracteres(min_len: int) -> str:
    """Mensaje para longitud mínima."""
    return f"Debe tener al menos {min_len} caracteres"


def msg_max_caracteres(max_len: int) -> str:
    """Mensaje para longitud máxima."""
    return f"Máximo {max_len} caracteres"


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
# MENSAJES DE TELÉFONO
# =============================================================================

MSG_TELEFONO_SOLO_NUMEROS = "Solo números (puede usar espacios, guiones o paréntesis)"


def msg_telefono_digitos(esperado: int, actual: int) -> str:
    """Mensaje para teléfono con dígitos incorrectos."""
    return f"Debe tener {esperado} dígitos (tiene {actual})"


# =============================================================================
# MENSAJES DE CÓDIGO POSTAL
# =============================================================================

MSG_CP_SOLO_NUMEROS = "Solo números permitidos"


def msg_cp_digitos(esperado: int, actual: int) -> str:
    """Mensaje para código postal con dígitos incorrectos."""
    return f"Debe tener {esperado} dígitos (tiene {actual})"


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
# MENSAJES DE CLAVE (TIPO SERVICIO)
# =============================================================================

MSG_CLAVE_OBLIGATORIA = "La clave es obligatoria"
MSG_CLAVE_SOLO_LETRAS = "Solo se permiten letras (sin números ni símbolos)"
MSG_CLAVE_SOLO_MAYUSCULAS = "La clave solo puede contener letras mayúsculas"


def msg_clave_longitud(min_len: int, max_len: int) -> str:
    """Mensaje para clave con longitud fuera de rango."""
    return f"La clave debe tener entre {min_len} y {max_len} caracteres"


def msg_clave_longitud_actual(min_len: int, max_len: int, actual: int) -> str:
    """Mensaje para clave con longitud fuera de rango (incluye actual)."""
    return f"La clave debe tener entre {min_len} y {max_len} caracteres (tiene {actual})"


# =============================================================================
# MENSAJES DE NOMBRE (TIPO SERVICIO)
# =============================================================================

MSG_NOMBRE_OBLIGATORIO = "El nombre es obligatorio"


# =============================================================================
# MENSAJES DE ESTADO/ESTATUS
# =============================================================================

def msg_entidad_ya_estado(entidad: str, estado: str) -> str:
    """Mensaje genérico para entidad ya en cierto estado."""
    return f"{entidad} ya está {estado}"
