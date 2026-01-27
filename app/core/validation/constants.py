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
# Homoclave: 2 caracteres alfanuméricos + 1 dígito verificador (0-9 o A)
RFC_PATTERN = r'^[A-Z&Ñ]{3,4}[0-9]{6}[A-Z0-9]{2}[0-9A]$'

# RFC persona física (13 caracteres): 4 letras + 6 dígitos + 3 homoclave
RFC_PERSONA_PATTERN = r'^[A-Z&Ñ]{4}[0-9]{6}[A-Z0-9]{2}[0-9A]$'

# RFC persona moral (12 caracteres): 3 letras + 6 dígitos + 3 homoclave
RFC_MORAL_PATTERN = r'^[A-Z&Ñ]{3}[0-9]{6}[A-Z0-9]{2}[0-9A]$'

# Prefijo RFC (primeras 3-4 letras)
RFC_PREFIX_PATTERN = r'^[A-Z&Ñ]{3,4}'

# Fecha en RFC (6 dígitos)
RFC_FECHA_PATTERN = r'^[0-9]{6}$'


# =============================================================================
# PATRONES DE EMPLEADOS
# =============================================================================

# CURP: 18 caracteres
# 4 letras + 6 dígitos (fecha) + H/M (sexo) + 2 letras (estado) + 3 consonantes + homoclave + dígito
CURP_PATTERN = r'^[A-Z]{4}[0-9]{6}[HM][A-Z]{5}[0-9A-Z][0-9]$'

# NSS (Número de Seguro Social IMSS): 11 dígitos
NSS_PATTERN = r'^[0-9]{11}$'

# Clave de empleado: B25-00001 (B + 2 dígitos año + guión + 5 dígitos consecutivo)
CLAVE_EMPLEADO_PATTERN = r'^B[0-9]{2}-[0-9]{5}$'


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
# CONSTANTES DE LONGITUD - EMPLEADOS
# =============================================================================

CURP_LEN = 18
RFC_PERSONA_LEN = 13
NSS_LEN = 11
CLAVE_EMPLEADO_MAX = 10
NOMBRE_EMPLEADO_MIN = 2
NOMBRE_EMPLEADO_MAX = 100
APELLIDO_MIN = 2
APELLIDO_MAX = 100
CONTACTO_EMERGENCIA_MAX = 200
NOTAS_MAX = 1000


# =============================================================================
# CONSTANTES DE LONGITUD - CATÁLOGOS (tipo_servicio, categoria_puesto, etc.)
# =============================================================================

CLAVE_CATALOGO_MIN = 2
CLAVE_CATALOGO_MAX = 5
NOMBRE_CATALOGO_MIN = 2
NOMBRE_CATALOGO_MAX = 50
DESCRIPCION_CATALOGO_MAX = 500


# =============================================================================
# CONSTANTES DE LONGITUD - CONTRATOS
# =============================================================================

CODIGO_CONTRATO_MAX = 20
FOLIO_BUAP_MAX = 50
DESCRIPCION_OBJETO_MAX = 2000
ORIGEN_RECURSO_MAX = 200
SEGMENTO_ASIGNACION_MAX = 100
SEDE_CAMPUS_MAX = 200
POLIZA_DETALLE_MAX = 200


# =============================================================================
# CONSTANTES DE LONGITUD - PAGOS
# =============================================================================

CONCEPTO_PAGO_MAX = 500
NUMERO_FACTURA_MAX = 50
COMPROBANTE_MAX = 200
NOTAS_PAGO_MAX = 1000


# =============================================================================
# CONSTANTES DE LONGITUD - REQUISICIONES
# =============================================================================

NUMERO_REQUISICION_MAX = 20
DEPENDENCIA_MAX = 255
NOMBRE_PERSONA_MAX = 150
CARGO_MAX = 150
TELEFONO_REQUISICION_MAX = 20
EMAIL_REQUISICION_MAX = 100
DOMICILIO_REQUISICION_MAX = 255
LUGAR_ENTREGA_MAX = 255
TIPO_GARANTIA_MAX = 100
FORMA_PAGO_MAX = 100
GARANTIA_VIGENCIA_MAX = 100
EXISTENCIA_ALMACEN_MAX = 100
PARTIDA_PRESUPUESTARIA_MAX = 100
AREA_DESTINO_MAX = 150
ORIGEN_RECURSO_REQUISICION_MAX = 150
OFICIO_SUFICIENCIA_MAX = 100
UNIDAD_MEDIDA_MAX = 50
CLAVE_CONFIGURACION_MAX = 50
DESCRIPCION_CONFIGURACION_MAX = 255
