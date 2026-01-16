"""
Patrones de validación centralizados.

Este módulo contiene todos los patrones regex y constantes de validación
usados tanto en entities (Pydantic) como en validators (frontend).

IMPORTANTE: Cualquier cambio aquí afecta ambas capas de validación.
"""
import re


# =============================================================================
# PATRONES DE RFC
# =============================================================================

# RFC completo: 3-4 letras + 6 dígitos (fecha) + 3 caracteres (homoclave)
RFC_PATTERN = r'^[A-Z&Ñ]{3,4}[0-9]{6}[A-V1-9][A-Z1-9][0-9A]$'

# Prefijo RFC (primeras 3-4 letras)
RFC_PREFIX_PATTERN = r'^[A-Z&Ñ]{3,4}'

# Fecha en RFC (6 dígitos)
RFC_FECHA_PATTERN = r'^[0-9]{6}$'


# =============================================================================
# PATRONES DE CONTACTO
# =============================================================================

# Email estándar
EMAIL_PATTERN = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

# Código postal mexicano (5 dígitos)
CODIGO_POSTAL_PATTERN = r'^[0-9]{5}$'


# =============================================================================
# PATRONES IMSS
# =============================================================================

# Registro patronal IMSS formateado: Y12-34567-10-1
REGISTRO_PATRONAL_PATTERN = r'^[A-Z][0-9]{2}-[0-9]{5}-[0-9]{2}-[0-9]$'

# Registro patronal IMSS sin guiones (11 caracteres): Y1234567101
REGISTRO_PATRONAL_LIMPIO_PATTERN = r'^[A-Z][0-9]{10}$'


# =============================================================================
# PATRONES DE EMPRESA
# =============================================================================

# Código corto de empresa (3 caracteres alfanuméricos)
CODIGO_CORTO_PATTERN = r'^[A-Z0-9]{3}$'


# =============================================================================
# PATRONES DE TIPO DE SERVICIO
# =============================================================================

# Clave de tipo de servicio (2-5 letras mayúsculas)
CLAVE_TIPO_SERVICIO_PATTERN = r'^[A-Z]{2,5}$'


# =============================================================================
# CONSTANTES DE LONGITUD
# =============================================================================

# Empresas
NOMBRE_COMERCIAL_MIN = 2
NOMBRE_COMERCIAL_MAX = 100
RAZON_SOCIAL_MIN = 2
RAZON_SOCIAL_MAX = 100
RFC_MIN = 12
RFC_MAX = 13
EMAIL_MAX = 100
DIRECCION_MAX = 200
TELEFONO_DIGITOS = 10
TELEFONO_MAX = 15
CODIGO_POSTAL_LEN = 5
CODIGO_CORTO_LEN = 3
REGISTRO_PATRONAL_MAX = 15
PAGINA_WEB_MAX = 100

# Tipo de servicio
CLAVE_TIPO_MIN = 2
CLAVE_TIPO_MAX = 5
NOMBRE_TIPO_MIN = 2
NOMBRE_TIPO_MAX = 50
DESCRIPCION_TIPO_MAX = 500


# =============================================================================
# FUNCIONES DE VALIDACIÓN REUTILIZABLES
# =============================================================================

def validar_patron(valor: str, patron: str, mensaje_error: str) -> str:
    """
    Valida un valor contra un patrón regex.

    Args:
        valor: Valor a validar
        patron: Patrón regex a usar
        mensaje_error: Mensaje si no coincide

    Returns:
        String vacío si es válido, mensaje de error si no
    """
    if not re.match(patron, valor):
        return mensaje_error
    return ""


def validar_longitud(
    valor: str,
    min_len: int | None = None,
    max_len: int | None = None,
    nombre_campo: str = "Campo"
) -> str:
    """
    Valida la longitud de un valor.

    Args:
        valor: Valor a validar
        min_len: Longitud mínima (opcional)
        max_len: Longitud máxima (opcional)
        nombre_campo: Nombre para el mensaje de error

    Returns:
        String vacío si es válido, mensaje de error si no
    """
    longitud = len(valor)

    if min_len is not None and longitud < min_len:
        return f"{nombre_campo} debe tener al menos {min_len} caracteres"

    if max_len is not None and longitud > max_len:
        return f"{nombre_campo} no puede tener más de {max_len} caracteres"

    return ""


def validar_requerido(valor: str | None, nombre_campo: str = "Campo") -> str:
    """
    Valida que un campo requerido tenga valor.

    Args:
        valor: Valor a validar
        nombre_campo: Nombre para el mensaje de error

    Returns:
        String vacío si tiene valor, mensaje de error si no
    """
    if not valor or not valor.strip():
        return f"{nombre_campo} es obligatorio"
    return ""
