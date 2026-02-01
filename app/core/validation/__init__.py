"""
Módulo de validación centralizado.

Estructura:
- constants.py: Patrones regex y constantes de longitud
- field_config.py: Clase FieldConfig para validación declarativa
- validator_factory.py: crear_validador() + helpers
- fields_catalog.py: Configuraciones predefinidas de campos
- custom_validators.py: Validadores complejos (RFC, registro patronal)

Uso básico:
    from app.core.validation import CAMPO_RFC, crear_validador

    validar_rfc = crear_validador(CAMPO_RFC)
    error = validar_rfc("XAXX010101AB1")  # "" = válido

Uso de validadores personalizados:
    from app.core.validation import validar_rfc_detallado

    error = validar_rfc_detallado("ABC")
    # "RFC debe tener 12 o 13 caracteres (tiene 3)"
"""

# Clase de configuración y tipos
from .field_config import FieldConfig, InputType

# Factory y helpers
from .validator_factory import (
    crear_validador,
    validar_con_config,
    validar_patron,
    validar_longitud,
    validar_requerido,
)

# Validadores personalizados
from .custom_validators import (
    validar_rfc_detallado,
    normalizar_rfc,
    validar_registro_patronal_detallado,
    formatear_registro_patronal,
    limpiar_telefono,
)

# Validadores comunes reutilizables
from .common_validators import (
    # Utilidades
    limpiar_moneda,
    # Select/Dropdown
    validar_select_requerido,
    validar_select_opcional,
    # Fechas
    validar_fecha_requerida,
    validar_fecha_no_futura,
    validar_fecha_rango,
    # Montos/Moneda
    validar_monto_requerido,
    validar_monto_opcional,
    validar_montos_min_max,
    # Enteros
    validar_entero_requerido,
    validar_entero_opcional,
    validar_entero_rango,
    validar_enteros_min_max,
    # Texto
    validar_texto_requerido,
    validar_texto_opcional,
)

# Conversores de Decimal
from .decimal_converters import (
    convertir_a_decimal,
    convertir_a_decimal_opcional,
)

# Helpers para Pydantic
from .pydantic_helpers import (
    pydantic_field,
    campo_validador,
)

# Catálogo de campos - Empresas
from .fields_catalog import (
    CAMPO_NOMBRE_COMERCIAL,
    CAMPO_RAZON_SOCIAL,
    CAMPO_RFC,
    CAMPO_DIRECCION,
    CAMPO_CODIGO_POSTAL,
    CAMPO_EMAIL,
    CAMPO_TELEFONO,
    CAMPO_PAGINA_WEB,
    CAMPO_REGISTRO_PATRONAL,
    CAMPO_PRIMA_RIESGO,
    CAMPO_NOTAS,
    # Catálogos (tipo_servicio, categoria_puesto, etc.)
    CAMPO_CLAVE_CATALOGO,
    CAMPO_NOMBRE_CATALOGO,
    CAMPO_DESCRIPCION_CATALOGO,
    # Diccionarios de campos para iteración
    CAMPOS_EMPRESA,
    CAMPOS_CATALOGO,
    CAMPOS_SIMULADOR,
    CAMPOS_CONTRATO,
    # Secciones - Empresas
    SECCION_INFO_BASICA,
    SECCION_CONTACTO,
    SECCION_IMSS,
    SECCION_CONTROL,
    # Secciones - Simulador
    SECCION_CONFIG_EMPRESA,
    SECCION_PRESTACIONES,
    SECCION_TRABAJADOR,
    # Campos Simulador
    CAMPO_SIM_ESTADO,
    CAMPO_SIM_PRIMA_RIESGO,
    CAMPO_SIM_DIAS_AGUINALDO,
    CAMPO_SIM_PRIMA_VACACIONAL,
    CAMPO_SIM_TIPO_CALCULO,
    CAMPO_SIM_SALARIO_MENSUAL,
    CAMPO_SIM_SALARIO_DIARIO,
    CAMPO_SIM_ANTIGUEDAD,
    CAMPO_SIM_DIAS_COTIZADOS,
    # Secciones - Contratos
    SECCION_CONTRATO_GENERAL,
    SECCION_CONTRATO_VIGENCIA,
    SECCION_CONTRATO_MONTOS,
    SECCION_CONTRATO_ADICIONAL,
    # Campos Contrato
    CAMPO_CODIGO_CONTRATO,
    CAMPO_FOLIO_BUAP,
    CAMPO_DESCRIPCION_OBJETO,
    CAMPO_ORIGEN_RECURSO,
    CAMPO_SEGMENTO_ASIGNACION,
    CAMPO_SEDE_CAMPUS,
    CAMPO_POLIZA_DETALLE,
    # Secciones - Sedes
    SECCION_SEDE_INFO,
    SECCION_SEDE_JERARQUIA,
    SECCION_SEDE_CONTACTO,
    # Campos Sede
    CAMPO_CODIGO_SEDE,
    CAMPO_NOMBRE_SEDE,
    CAMPO_NOMBRE_CORTO_SEDE,
    CAMPO_DIRECCION_SEDE,
    CAMPO_NOTAS_SEDE,
    CAMPOS_SEDE,
    # Campos Contacto BUAP
    CAMPO_NOMBRE_CONTACTO,
    CAMPO_CARGO_CONTACTO,
    CAMPO_EXTENSION_CONTACTO,
    CAMPOS_CONTACTO_BUAP,
)

# Constantes (re-export para conveniencia)
from .constants import (
    # Patrones - RFC
    RFC_PATTERN,
    RFC_PERSONA_PATTERN,
    RFC_MORAL_PATTERN,
    RFC_PREFIX_PATTERN,
    RFC_FECHA_PATTERN,
    # Patrones - Contacto
    EMAIL_PATTERN,
    CODIGO_POSTAL_PATTERN,
    TELEFONO_PATTERN,
    # Patrones - IMSS
    REGISTRO_PATRONAL_PATTERN,
    REGISTRO_PATRONAL_LIMPIO_PATTERN,
    # Patrones - Empleados
    CURP_PATTERN,
    NSS_PATTERN,
    CLAVE_EMPLEADO_PATTERN,
    # Patrones - Empresa
    CODIGO_CORTO_PATTERN,
    CLAVE_CATALOGO_PATTERN,
    # Longitudes - Empleados
    CURP_LEN,
    RFC_PERSONA_LEN,
    NSS_LEN,
    CLAVE_EMPLEADO_MAX,
    NOMBRE_EMPLEADO_MIN,
    NOMBRE_EMPLEADO_MAX,
    APELLIDO_MIN,
    APELLIDO_MAX,
    CONTACTO_EMERGENCIA_MAX,
    NOTAS_MAX,
    # Longitudes - Empresas
    NOMBRE_COMERCIAL_MIN,
    NOMBRE_COMERCIAL_MAX,
    RAZON_SOCIAL_MIN,
    RAZON_SOCIAL_MAX,
    RFC_MIN,
    RFC_MAX,
    EMAIL_MAX,
    DIRECCION_MAX,
    TELEFONO_DIGITOS,
    TELEFONO_MAX,
    CODIGO_POSTAL_LEN,
    CODIGO_CORTO_LEN,
    REGISTRO_PATRONAL_LEN,
    REGISTRO_PATRONAL_MAX,
    PAGINA_WEB_MAX,
    # Longitudes - Catálogos
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
    # Patrón - Sedes
    CODIGO_SEDE_PATTERN,
    # Longitudes - Sedes
    CODIGO_SEDE_MAX,
    NOMBRE_SEDE_MIN,
    NOMBRE_SEDE_MAX,
    NOMBRE_CORTO_SEDE_MAX,
    # Longitudes - Contactos BUAP
    NOMBRE_CONTACTO_MAX,
    CARGO_CONTACTO_MAX,
    EXTENSION_MAX,
)

__all__ = [
    # Config y tipos
    "FieldConfig",
    "InputType",
    # Factory y helpers
    "crear_validador",
    "validar_con_config",
    "validar_patron",
    "validar_longitud",
    "validar_requerido",
    # Validadores custom
    "validar_rfc_detallado",
    "normalizar_rfc",
    "validar_registro_patronal_detallado",
    "formatear_registro_patronal",
    "limpiar_telefono",
    # Validadores comunes
    "limpiar_moneda",
    "validar_select_requerido",
    "validar_select_opcional",
    "validar_fecha_requerida",
    "validar_fecha_no_futura",
    "validar_fecha_rango",
    "validar_monto_requerido",
    "validar_monto_opcional",
    "validar_montos_min_max",
    "validar_entero_requerido",
    "validar_entero_opcional",
    "validar_entero_rango",
    "validar_enteros_min_max",
    "validar_texto_requerido",
    "validar_texto_opcional",
    # Conversores de Decimal
    "convertir_a_decimal",
    "convertir_a_decimal_opcional",
    # Helpers para Pydantic
    "pydantic_field",
    "campo_validador",
    # Catálogo - Empresas
    "CAMPO_NOMBRE_COMERCIAL",
    "CAMPO_RAZON_SOCIAL",
    "CAMPO_RFC",
    "CAMPO_DIRECCION",
    "CAMPO_CODIGO_POSTAL",
    "CAMPO_EMAIL",
    "CAMPO_TELEFONO",
    "CAMPO_PAGINA_WEB",
    "CAMPO_REGISTRO_PATRONAL",
    "CAMPO_PRIMA_RIESGO",
    "CAMPO_NOTAS",
    # Catálogo - Catálogos genéricos
    "CAMPO_CLAVE_CATALOGO",
    "CAMPO_NOMBRE_CATALOGO",
    "CAMPO_DESCRIPCION_CATALOGO",
    # Diccionarios de campos
    "CAMPOS_EMPRESA",
    "CAMPOS_CATALOGO",
    "CAMPOS_SIMULADOR",
    "CAMPOS_CONTRATO",
    # Secciones - Empresas
    "SECCION_INFO_BASICA",
    "SECCION_CONTACTO",
    "SECCION_IMSS",
    "SECCION_CONTROL",
    # Secciones - Simulador
    "SECCION_CONFIG_EMPRESA",
    "SECCION_PRESTACIONES",
    "SECCION_TRABAJADOR",
    # Campos Simulador
    "CAMPO_SIM_ESTADO",
    "CAMPO_SIM_PRIMA_RIESGO",
    "CAMPO_SIM_DIAS_AGUINALDO",
    "CAMPO_SIM_PRIMA_VACACIONAL",
    "CAMPO_SIM_TIPO_CALCULO",
    "CAMPO_SIM_SALARIO_MENSUAL",
    "CAMPO_SIM_SALARIO_DIARIO",
    "CAMPO_SIM_ANTIGUEDAD",
    "CAMPO_SIM_DIAS_COTIZADOS",
    # Secciones - Contratos
    "SECCION_CONTRATO_GENERAL",
    "SECCION_CONTRATO_VIGENCIA",
    "SECCION_CONTRATO_MONTOS",
    "SECCION_CONTRATO_ADICIONAL",
    # Campos - Contratos
    "CAMPO_CODIGO_CONTRATO",
    "CAMPO_FOLIO_BUAP",
    "CAMPO_DESCRIPCION_OBJETO",
    "CAMPO_ORIGEN_RECURSO",
    "CAMPO_SEGMENTO_ASIGNACION",
    "CAMPO_SEDE_CAMPUS",
    "CAMPO_POLIZA_DETALLE",
    # Patrones - RFC
    "RFC_PATTERN",
    "RFC_PERSONA_PATTERN",
    "RFC_MORAL_PATTERN",
    "RFC_PREFIX_PATTERN",
    "RFC_FECHA_PATTERN",
    # Patrones - Contacto
    "EMAIL_PATTERN",
    "CODIGO_POSTAL_PATTERN",
    "TELEFONO_PATTERN",
    # Patrones - IMSS
    "REGISTRO_PATRONAL_PATTERN",
    "REGISTRO_PATRONAL_LIMPIO_PATTERN",
    # Patrones - Empleados
    "CURP_PATTERN",
    "NSS_PATTERN",
    "CLAVE_EMPLEADO_PATTERN",
    # Patrones - Empresa
    "CODIGO_CORTO_PATTERN",
    "CLAVE_CATALOGO_PATTERN",
    # Longitudes - Empleados
    "CURP_LEN",
    "RFC_PERSONA_LEN",
    "NSS_LEN",
    "CLAVE_EMPLEADO_MAX",
    "NOMBRE_EMPLEADO_MIN",
    "NOMBRE_EMPLEADO_MAX",
    "APELLIDO_MIN",
    "APELLIDO_MAX",
    "CONTACTO_EMERGENCIA_MAX",
    "NOTAS_MAX",
    # Longitudes - Empresas
    "NOMBRE_COMERCIAL_MIN",
    "NOMBRE_COMERCIAL_MAX",
    "RAZON_SOCIAL_MIN",
    "RAZON_SOCIAL_MAX",
    "RFC_MIN",
    "RFC_MAX",
    "EMAIL_MAX",
    "DIRECCION_MAX",
    "TELEFONO_DIGITOS",
    "TELEFONO_MAX",
    "CODIGO_POSTAL_LEN",
    "CODIGO_CORTO_LEN",
    "REGISTRO_PATRONAL_LEN",
    "REGISTRO_PATRONAL_MAX",
    "PAGINA_WEB_MAX",
    "CLAVE_CATALOGO_MIN",
    "CLAVE_CATALOGO_MAX",
    "NOMBRE_CATALOGO_MIN",
    "NOMBRE_CATALOGO_MAX",
    "DESCRIPCION_CATALOGO_MAX",
    # Longitudes - Contratos
    "CODIGO_CONTRATO_MAX",
    "FOLIO_BUAP_MAX",
    "DESCRIPCION_OBJETO_MAX",
    "ORIGEN_RECURSO_MAX",
    "SEGMENTO_ASIGNACION_MAX",
    "SEDE_CAMPUS_MAX",
    "POLIZA_DETALLE_MAX",
    # Patrón - Sedes
    "CODIGO_SEDE_PATTERN",
    # Longitudes - Sedes
    "CODIGO_SEDE_MAX",
    "NOMBRE_SEDE_MIN",
    "NOMBRE_SEDE_MAX",
    "NOMBRE_CORTO_SEDE_MAX",
    # Longitudes - Contactos BUAP
    "NOMBRE_CONTACTO_MAX",
    "CARGO_CONTACTO_MAX",
    "EXTENSION_MAX",
    # Secciones - Sedes
    "SECCION_SEDE_INFO",
    "SECCION_SEDE_JERARQUIA",
    "SECCION_SEDE_CONTACTO",
    # Campos - Sedes
    "CAMPO_CODIGO_SEDE",
    "CAMPO_NOMBRE_SEDE",
    "CAMPO_NOMBRE_CORTO_SEDE",
    "CAMPO_DIRECCION_SEDE",
    "CAMPO_NOTAS_SEDE",
    "CAMPOS_SEDE",
    # Campos - Contacto BUAP
    "CAMPO_NOMBRE_CONTACTO",
    "CAMPO_CARGO_CONTACTO",
    "CAMPO_EXTENSION_CONTACTO",
    "CAMPOS_CONTACTO_BUAP",
]
