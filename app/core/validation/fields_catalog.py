"""
Catálogo de configuraciones de campos para validación y formularios.

Este catálogo define campos reutilizables que incluyen:
- Reglas de validación (backend y frontend)
- Metadatos de UI (labels, placeholders, hints)
- Configuración de formularios (secciones, orden, ancho)

Uso en validación:
    from app.core.validation import CAMPO_RFC, crear_validador
    validar_rfc = crear_validador(CAMPO_RFC)
    error = validar_rfc("XAXX010101AB1")  # "" = válido

Uso en formularios (labels y hints como referencia):
    from app.core.validation import CAMPO_RFC
    # label=CAMPO_RFC.label, placeholder=CAMPO_RFC.placeholder, hint=CAMPO_RFC.hint
"""
import re

from .field_config import FieldConfig, InputType
from .constants import (
    # Patrones
    RFC_PATTERN,
    EMAIL_PATTERN,
    CODIGO_POSTAL_PATTERN,
    TELEFONO_PATTERN,
    REGISTRO_PATRONAL_LIMPIO_PATTERN,
    CLAVE_CATALOGO_PATTERN,
    # Longitudes - Empresas
    NOMBRE_COMERCIAL_MIN,
    NOMBRE_COMERCIAL_MAX,
    RAZON_SOCIAL_MIN,
    RAZON_SOCIAL_MAX,
    RFC_MIN,
    RFC_MAX,
    DIRECCION_MAX,
    CODIGO_POSTAL_LEN,
    EMAIL_MAX,
    TELEFONO_DIGITOS,
    REGISTRO_PATRONAL_LEN,
    PAGINA_WEB_MAX,
    # Longitudes - Catálogos (tipo_servicio, categoria_puesto, etc.)
    CLAVE_CATALOGO_MIN,
    CLAVE_CATALOGO_MAX,
    NOMBRE_CATALOGO_MIN,
    NOMBRE_CATALOGO_MAX,
    DESCRIPCION_CATALOGO_MAX,
    # Longitudes - Contratos
    CODIGO_CONTRATO_MAX,
    FOLIO_BUAP_MAX,
    DESCRIPCION_OBJETO_MAX,
    ORIGEN_RECURSO_MAX,
    SEGMENTO_ASIGNACION_MAX,
    SEDE_CAMPUS_MAX,
    POLIZA_DETALLE_MAX,
)
from app.core.error_messages import (
    MSG_EMAIL_FORMATO_INVALIDO,
    MSG_CP_SOLO_NUMEROS,
    MSG_REGISTRO_PATRONAL_INVALIDO,
    MSG_CLAVE_SOLO_LETRAS,
    MSG_PRIMA_RIESGO_NUMERO,
    MSG_PRIMA_RIESGO_MIN,
    MSG_PRIMA_RIESGO_MAX,
)
from app.core.catalogs import CatalogoPrestaciones, LimitesValidacion


# =============================================================================
# SECCIONES DE FORMULARIO (constantes para consistencia)
# =============================================================================

SECCION_INFO_BASICA = "info_basica"
SECCION_CONTACTO = "contacto"
SECCION_IMSS = "imss"
SECCION_CONTROL = "control"


# =============================================================================
# CAMPOS DE EMPRESA
# =============================================================================

CAMPO_NOMBRE_COMERCIAL = FieldConfig(
    nombre='Nombre comercial',
    requerido=True,
    min_len=NOMBRE_COMERCIAL_MIN,
    max_len=NOMBRE_COMERCIAL_MAX,
    transformar=str.upper,
    # UI
    label='Nombre comercial *',
    placeholder='Nombre comercial de la empresa',
    hint=f'{NOMBRE_COMERCIAL_MIN}-{NOMBRE_COMERCIAL_MAX} caracteres',
    input_type=InputType.TEXT,
    section=SECCION_INFO_BASICA,
    order=1,
)

CAMPO_RAZON_SOCIAL = FieldConfig(
    nombre='Razón Social',
    requerido=True,
    min_len=RAZON_SOCIAL_MIN,
    max_len=RAZON_SOCIAL_MAX,
    transformar=str.upper,
    # UI
    label='Razón social *',
    placeholder='Razón social completa (SA de CV, etc.)',
    input_type=InputType.TEXT,
    section=SECCION_INFO_BASICA,
    order=2,
)

CAMPO_RFC = FieldConfig(
    nombre='RFC',
    requerido=True,
    min_len=RFC_MIN,
    max_len=RFC_MAX,
    transformar=str.upper,
    patron=RFC_PATTERN,
    patron_error='RFC no cumple el formato del SAT',
    # UI
    label='RFC *',
    placeholder='RFC con homoclave',
    hint='12-13 caracteres alfanuméricos',
    input_type=InputType.TEXT,
    section=SECCION_INFO_BASICA,
    order=3,
)

CAMPO_DIRECCION = FieldConfig(
    nombre='Dirección',
    requerido=False,
    max_len=DIRECCION_MAX,
    # UI
    label='Dirección',
    placeholder='Calle, número, colonia, ciudad',
    input_type=InputType.TEXT,
    section=SECCION_CONTACTO,
    order=1,
)

CAMPO_CODIGO_POSTAL = FieldConfig(
    nombre='Código Postal',
    requerido=False,
    min_len=CODIGO_POSTAL_LEN,
    max_len=CODIGO_POSTAL_LEN,
    patron=CODIGO_POSTAL_PATTERN,
    patron_error=MSG_CP_SOLO_NUMEROS,
    # UI
    label='Código Postal',
    placeholder='00000',
    hint='5 dígitos',
    input_type=InputType.TEXT,
    section=SECCION_CONTACTO,
    order=2,
    width='half',
)

CAMPO_TELEFONO = FieldConfig(
    nombre='Teléfono',
    requerido=False,
    min_len=TELEFONO_DIGITOS,
    max_len=TELEFONO_DIGITOS,
    patron=TELEFONO_PATTERN,
    patron_error='Debe tener 10 dígitos',
    transformar=lambda v: re.sub(r'[\s\-\(\)\+]', '', v),
    # UI
    label='Teléfono',
    placeholder='(55) 1234-5678',
    hint='10 dígitos',
    input_type=InputType.TEL,
    section=SECCION_CONTACTO,
    order=3,
    width='half',
)

CAMPO_EMAIL = FieldConfig(
    nombre='Correo electrónico',
    requerido=False,
    max_len=EMAIL_MAX,
    patron=EMAIL_PATTERN,
    patron_error=MSG_EMAIL_FORMATO_INVALIDO,
    transformar=str.lower,
    # UI
    label='Correo electrónico',
    placeholder='correo@ejemplo.com',
    input_type=InputType.EMAIL,
    section=SECCION_CONTACTO,
    order=4,
)

CAMPO_PAGINA_WEB = FieldConfig(
    nombre='Página web',
    requerido=False,
    max_len=PAGINA_WEB_MAX,
    # UI
    label='Página web',
    placeholder='https://www.ejemplo.com',
    input_type=InputType.TEXT,
    section=SECCION_CONTACTO,
    order=5,
)

CAMPO_REGISTRO_PATRONAL = FieldConfig(
    nombre='Registro Patronal',
    requerido=False,
    min_len=REGISTRO_PATRONAL_LEN,
    max_len=REGISTRO_PATRONAL_LEN,
    patron=REGISTRO_PATRONAL_LIMPIO_PATTERN,
    patron_error=MSG_REGISTRO_PATRONAL_INVALIDO,
    transformar=lambda v: re.sub(r'[\s\-]', '', v.upper()),
    # UI
    label='Registro Patronal IMSS',
    placeholder='Y12-34567-10-1',
    hint='Formato: letra + 10 dígitos',
    input_type=InputType.TEXT,
    section=SECCION_IMSS,
    order=1,
)


def _validar_prima_riesgo(valor: str) -> str:
    """Validador custom para prima de riesgo usando límites del catálogo."""
    try:
        numero = float(valor)
    except ValueError:
        return MSG_PRIMA_RIESGO_NUMERO

    min_pct = float(LimitesValidacion.PRIMA_RIESGO_MIN_PORCENTAJE)
    max_pct = float(LimitesValidacion.PRIMA_RIESGO_MAX_PORCENTAJE)

    if numero < min_pct:
        return MSG_PRIMA_RIESGO_MIN
    if numero > max_pct:
        return MSG_PRIMA_RIESGO_MAX
    return ""


CAMPO_PRIMA_RIESGO = FieldConfig(
    nombre='Prima de riesgo',
    requerido=False,
    validador_custom=_validar_prima_riesgo,
    # UI
    label='Prima de riesgo (%)',
    placeholder='2.5',
    hint=f'Entre {LimitesValidacion.PRIMA_RIESGO_MIN_PORCENTAJE}% y {LimitesValidacion.PRIMA_RIESGO_MAX_PORCENTAJE}%',
    input_type=InputType.NUMBER,
    section=SECCION_IMSS,
    order=2,
    width='half',
)

CAMPO_NOTAS = FieldConfig(
    nombre='Notas',
    requerido=False,
    # UI
    label='Notas',
    placeholder='Observaciones adicionales...',
    input_type=InputType.TEXTAREA,
    section=SECCION_CONTROL,
    order=2,
    rows=3,
)


# =============================================================================
# CAMPOS DE CATÁLOGOS (tipo_servicio, categoria_puesto, etc.)
# =============================================================================

CAMPO_CLAVE_CATALOGO = FieldConfig(
    nombre='Clave',
    requerido=True,
    min_len=CLAVE_CATALOGO_MIN,
    max_len=CLAVE_CATALOGO_MAX,
    patron=CLAVE_CATALOGO_PATTERN,
    patron_error=MSG_CLAVE_SOLO_LETRAS,
    transformar=str.upper,
    # UI
    label='Clave *',
    placeholder='Ej: JAR, OPE, SUP',
    hint=f'{CLAVE_CATALOGO_MIN}-{CLAVE_CATALOGO_MAX} letras mayúsculas',
    input_type=InputType.TEXT,
    order=1,
)

CAMPO_NOMBRE_CATALOGO = FieldConfig(
    nombre='Nombre',
    requerido=True,
    min_len=NOMBRE_CATALOGO_MIN,
    max_len=NOMBRE_CATALOGO_MAX,
    transformar=str.upper,
    # UI
    label='Nombre *',
    placeholder='Nombre del elemento',
    input_type=InputType.TEXT,
    order=2,
)

CAMPO_DESCRIPCION_CATALOGO = FieldConfig(
    nombre='Descripción',
    requerido=False,
    max_len=DESCRIPCION_CATALOGO_MAX,
    # UI
    label='Descripción',
    placeholder='Descripción detallada...',
    hint=f'Máximo {DESCRIPCION_CATALOGO_MAX} caracteres',
    input_type=InputType.TEXTAREA,
    order=3,
    rows=3,
)


# =============================================================================
# CAMPOS DE SIMULADOR DE COSTO PATRONAL
# =============================================================================

SECCION_CONFIG_EMPRESA = "config_empresa"
SECCION_PRESTACIONES = "prestaciones"
SECCION_TRABAJADOR = "trabajador"

CAMPO_SIM_ESTADO = FieldConfig(
    nombre='Estado',
    requerido=True,
    # UI
    label='Estado',
    placeholder='Selecciona un estado',
    input_type=InputType.SELECT,
    section=SECCION_CONFIG_EMPRESA,
    order=1,
    width='half',
)

CAMPO_SIM_PRIMA_RIESGO = FieldConfig(
    nombre='Prima de riesgo',
    requerido=True,
    # UI
    label='Prima de riesgo (%)',
    placeholder='2.5984',
    hint='Porcentaje según giro de la empresa',
    input_type=InputType.NUMBER,
    section=SECCION_CONFIG_EMPRESA,
    order=2,
    width='half',
)

CAMPO_SIM_DIAS_AGUINALDO = FieldConfig(
    nombre='Días de aguinaldo',
    requerido=True,
    # UI
    label='Días de aguinaldo',
    placeholder=str(CatalogoPrestaciones.AGUINALDO_DIAS),
    hint=f'Mínimo legal: {CatalogoPrestaciones.AGUINALDO_DIAS} días',
    input_type=InputType.NUMBER,
    section=SECCION_PRESTACIONES,
    order=1,
    width='half',
)

CAMPO_SIM_PRIMA_VACACIONAL = FieldConfig(
    nombre='Prima vacacional',
    requerido=True,
    # UI
    label='Prima vacacional (%)',
    placeholder=str(int(CatalogoPrestaciones.PRIMA_VACACIONAL * 100)),
    hint=f'Mínimo legal: {int(CatalogoPrestaciones.PRIMA_VACACIONAL * 100)}%',
    input_type=InputType.NUMBER,
    section=SECCION_PRESTACIONES,
    order=2,
    width='half',
)

CAMPO_SIM_TIPO_CALCULO = FieldConfig(
    nombre='Tipo de cálculo',
    requerido=True,
    # UI
    label='Tipo de cálculo',
    placeholder='Selecciona un tipo',
    input_type=InputType.SELECT,
    section=SECCION_TRABAJADOR,
    order=1,
    width='third',
)

CAMPO_SIM_SALARIO_MENSUAL = FieldConfig(
    nombre='Salario mensual',
    requerido=False,
    # UI
    label='Salario mensual ($)',
    placeholder='0.00',
    input_type=InputType.NUMBER,
    section=SECCION_TRABAJADOR,
    order=2,
    width='third',
)

CAMPO_SIM_SALARIO_DIARIO = FieldConfig(
    nombre='Salario diario',
    requerido=False,
    # UI
    label='Salario diario ($)',
    placeholder='0.00',
    hint='Calculado automáticamente',
    input_type=InputType.NUMBER,
    section=SECCION_TRABAJADOR,
    order=3,
    width='third',
)

CAMPO_SIM_ANTIGUEDAD = FieldConfig(
    nombre='Antigüedad',
    requerido=True,
    # UI
    label='Antigüedad (años)',
    placeholder='1',
    hint='Mínimo 1 año',
    input_type=InputType.NUMBER,
    section=SECCION_TRABAJADOR,
    order=4,
    width='half',
)

CAMPO_SIM_DIAS_COTIZADOS = FieldConfig(
    nombre='Días cotizados',
    requerido=True,
    # UI
    label='Días cotizados',
    placeholder='30',
    hint='Días del mes a cotizar',
    input_type=InputType.NUMBER,
    section=SECCION_TRABAJADOR,
    order=5,
    width='half',
)


# =============================================================================
# DICCIONARIOS DE CAMPOS POR MÓDULO (para iterar fácilmente)
# =============================================================================

CAMPOS_EMPRESA = {
    'nombre_comercial': CAMPO_NOMBRE_COMERCIAL,
    'razon_social': CAMPO_RAZON_SOCIAL,
    'rfc': CAMPO_RFC,
    'direccion': CAMPO_DIRECCION,
    'codigo_postal': CAMPO_CODIGO_POSTAL,
    'telefono': CAMPO_TELEFONO,
    'email': CAMPO_EMAIL,
    'pagina_web': CAMPO_PAGINA_WEB,
    'registro_patronal': CAMPO_REGISTRO_PATRONAL,
    'prima_riesgo': CAMPO_PRIMA_RIESGO,
    'notas': CAMPO_NOTAS,
}

CAMPOS_CATALOGO = {
    'clave': CAMPO_CLAVE_CATALOGO,
    'nombre': CAMPO_NOMBRE_CATALOGO,
    'descripcion': CAMPO_DESCRIPCION_CATALOGO,
}

CAMPOS_SIMULADOR = {
    'estado': CAMPO_SIM_ESTADO,
    'prima_riesgo': CAMPO_SIM_PRIMA_RIESGO,
    'dias_aguinaldo': CAMPO_SIM_DIAS_AGUINALDO,
    'prima_vacacional': CAMPO_SIM_PRIMA_VACACIONAL,
    'tipo_calculo': CAMPO_SIM_TIPO_CALCULO,
    'salario_mensual': CAMPO_SIM_SALARIO_MENSUAL,
    'salario_diario': CAMPO_SIM_SALARIO_DIARIO,
    'antiguedad': CAMPO_SIM_ANTIGUEDAD,
    'dias_cotizados': CAMPO_SIM_DIAS_COTIZADOS,
}


# =============================================================================
# CAMPOS DE CONTRATO
# =============================================================================

SECCION_CONTRATO_GENERAL = "contrato_general"
SECCION_CONTRATO_VIGENCIA = "contrato_vigencia"
SECCION_CONTRATO_MONTOS = "contrato_montos"
SECCION_CONTRATO_ADICIONAL = "contrato_adicional"

CAMPO_CODIGO_CONTRATO = FieldConfig(
    nombre='Código',
    requerido=True,
    max_len=CODIGO_CONTRATO_MAX,
    transformar=str.upper,
    # UI
    label='Código *',
    placeholder='MAN-JAR-25001',
    hint='Se genera automáticamente',
    input_type=InputType.TEXT,
    section=SECCION_CONTRATO_GENERAL,
    order=1,
)

CAMPO_FOLIO_BUAP = FieldConfig(
    nombre='Folio BUAP',
    requerido=False,
    max_len=FOLIO_BUAP_MAX,
    # UI
    label='Número de folio BUAP',
    placeholder='Folio oficial asignado por BUAP',
    input_type=InputType.TEXT,
    section=SECCION_CONTRATO_GENERAL,
    order=2,
)

CAMPO_DESCRIPCION_OBJETO = FieldConfig(
    nombre='Descripción del objeto',
    requerido=False,
    max_len=DESCRIPCION_OBJETO_MAX,
    # UI
    label='Descripción del objeto',
    placeholder='Descripción del objeto del contrato...',
    hint=f'Máximo {DESCRIPCION_OBJETO_MAX} caracteres',
    input_type=InputType.TEXTAREA,
    section=SECCION_CONTRATO_GENERAL,
    order=5,
    rows=4,
)

CAMPO_ORIGEN_RECURSO = FieldConfig(
    nombre='Origen del recurso',
    requerido=False,
    max_len=ORIGEN_RECURSO_MAX,
    # UI
    label='Origen del recurso',
    placeholder='Artículo de ley, subsidio, etc.',
    input_type=InputType.TEXT,
    section=SECCION_CONTRATO_ADICIONAL,
    order=1,
)

CAMPO_SEGMENTO_ASIGNACION = FieldConfig(
    nombre='Segmento de asignación',
    requerido=False,
    max_len=SEGMENTO_ASIGNACION_MAX,
    # UI
    label='Segmento de asignación',
    placeholder='Partida o segmento de BUAP',
    input_type=InputType.TEXT,
    section=SECCION_CONTRATO_ADICIONAL,
    order=2,
    width='half',
)

CAMPO_SEDE_CAMPUS = FieldConfig(
    nombre='Sede/Campus',
    requerido=False,
    max_len=SEDE_CAMPUS_MAX,
    # UI
    label='Sede o campus',
    placeholder='Sede o campus donde aplica',
    input_type=InputType.TEXT,
    section=SECCION_CONTRATO_ADICIONAL,
    order=3,
    width='half',
)

CAMPO_POLIZA_DETALLE = FieldConfig(
    nombre='Detalle de póliza',
    requerido=False,
    max_len=POLIZA_DETALLE_MAX,
    # UI
    label='Detalles de póliza',
    placeholder='Detalles de la póliza requerida',
    input_type=InputType.TEXT,
    section=SECCION_CONTRATO_ADICIONAL,
    order=4,
)

CAMPOS_CONTRATO = {
    'codigo': CAMPO_CODIGO_CONTRATO,
    'numero_folio_buap': CAMPO_FOLIO_BUAP,
    'descripcion_objeto': CAMPO_DESCRIPCION_OBJETO,
    'origen_recurso': CAMPO_ORIGEN_RECURSO,
    'segmento_asignacion': CAMPO_SEGMENTO_ASIGNACION,
    'sede_campus': CAMPO_SEDE_CAMPUS,
    'poliza_detalle': CAMPO_POLIZA_DETALLE,
}
