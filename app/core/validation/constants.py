"""
Constantes de validación centralizadas.

Este módulo contiene todos los patrones regex y constantes de longitud
usados tanto en entities (Pydantic) como en validators (frontend).

IMPORTANTE: Cualquier cambio aquí afecta ambas capas de validación.
"""

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

# Patrón de números de teléfono (10 dígitos)
TELEFONO_PATTERN = r'^[0-9]{10}$'


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
# PATRONES DE CATÁLOGOS (tipo_servicio, categoria_puesto, etc.)
# =============================================================================

# Clave de catálogo (2-5 letras mayúsculas)
CLAVE_CATALOGO_PATTERN = r'^[A-Z]{2,5}$'


# =============================================================================
# CONSTANTES DE LONGITUD - EMPRESAS
# =============================================================================

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
REGISTRO_PATRONAL_LEN = 11
REGISTRO_PATRONAL_MAX = 15
PAGINA_WEB_MAX = 100


# =============================================================================
# CONSTANTES DE LONGITUD - CATÁLOGOS (tipo_servicio, categoria_puesto, etc.)
# =============================================================================

CLAVE_CATALOGO_MIN = 2
CLAVE_CATALOGO_MAX = 5
NOMBRE_CATALOGO_MIN = 2
NOMBRE_CATALOGO_MAX = 50
DESCRIPCION_CATALOGO_MAX = 500
