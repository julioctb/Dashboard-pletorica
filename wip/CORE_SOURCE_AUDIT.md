# Auditoria de app/core

Generado: 2026-03-17

## 1. Fuentes de verdad detectadas

- `calculations`: 5 modulo(s)
  - `app/core/calculations/__init__.py`
  - `app/core/calculations/calculadora_imss.py`
  - `app/core/calculations/calculadora_isr.py`
  - `app/core/calculations/calculadora_provisiones.py`
  - `app/core/calculations/simulador_costo_patronal.py`
- `catalogs`: 21 modulo(s)
  - `app/core/catalogs/__init__.py`
  - `app/core/catalogs/fiscal/__init__.py`
  - `app/core/catalogs/fiscal/_shared.py`
  - `app/core/catalogs/fiscal/imss.py`
  - `app/core/catalogs/fiscal/infonavit.py`
  - `app/core/catalogs/fiscal/isn.py`
  - `app/core/catalogs/fiscal/isr.py`
  - `app/core/catalogs/fiscal/politica.py`
  - `app/core/catalogs/fiscal/salario_minimo.py`
  - `app/core/catalogs/fiscal/uma.py`
  - `app/core/catalogs/laboral/__init__.py`
  - `app/core/catalogs/laboral/prestaciones.py`
  - `app/core/catalogs/laboral/vacaciones.py`
  - `app/core/catalogs/nomina/__init__.py`
  - `app/core/catalogs/nomina/conceptos.py`
  - `app/core/catalogs/nomina/enums.py`
  - `app/core/catalogs/nomina/periodos.py`
  - `app/core/catalogs/nomina/quincenas.py`
  - `app/core/catalogs/sistema/__init__.py`
  - `app/core/catalogs/sistema/limites.py`
  - `app/core/catalogs/sistema/tolerancias.py`
- `compresores`: 3 modulo(s)
  - `app/core/compresores/__init__.py`
  - `app/core/compresores/imagen_compressor.py`
  - `app/core/compresores/pdf_compressor.py`
- `config`: 2 modulo(s)
  - `app/core/config/__init__.py`
  - `app/core/config/archivos_config.py`
- `constants`: 2 modulo(s)
  - `app/core/constants/__init__.py`
  - `app/core/constants/permisos.py`
- `enums.py`: 1 modulo(s)
  - `app/core/enums.py`
- `error_messages.py`: 1 modulo(s)
  - `app/core/error_messages.py`
- `exceptions.py`: 1 modulo(s)
  - `app/core/exceptions.py`
- `root`: 1 modulo(s)
  - `app/core/__init__.py`
- `text_utils.py`: 1 modulo(s)
  - `app/core/text_utils.py`
- `ui_helpers.py`: 1 modulo(s)
  - `app/core/ui_helpers.py`
- `ui_option_sets.py`: 1 modulo(s)
  - `app/core/ui_option_sets.py`
- `ui_options.py`: 1 modulo(s)
  - `app/core/ui_options.py`
- `utils`: 3 modulo(s)
  - `app/core/utils/__init__.py`
  - `app/core/utils/codigo_generator.py`
  - `app/core/utils/date_input.py`
- `validation`: 20 modulo(s)
  - `app/core/validation/__init__.py`
  - `app/core/validation/bank_validators.py`
  - `app/core/validation/catalogo_form_validators.py`
  - `app/core/validation/cfdi_validator.py`
  - `app/core/validation/common_validators.py`
  - `app/core/validation/constants.py`
  - `app/core/validation/contrato_categoria_form_validators.py`
  - `app/core/validation/contrato_form_validators.py`
  - `app/core/validation/custom_validators.py`
  - `app/core/validation/decimal_converters.py`
  - `app/core/validation/employee_validators.py`
  - `app/core/validation/empresa_form_validators.py`
  - `app/core/validation/field_config.py`
  - `app/core/validation/fields_catalog.py`
  - `app/core/validation/form_shared_validators.py`
  - `app/core/validation/pago_form_validators.py`
  - `app/core/validation/pydantic_helpers.py`
  - `app/core/validation/sede_form_validators.py`
  - `app/core/validation/user_validators.py`
  - `app/core/validation/validator_factory.py`

## 2. Consumidores directos fuera de core

- `calculations`: 3 archivo(s) consumidor(es)
- `catalogs`: 6 archivo(s) consumidor(es)
- `compresores`: 1 archivo(s) consumidor(es)
- `config`: 10 archivo(s) consumidor(es)
- `constants`: 4 archivo(s) consumidor(es)
- `enums`: 81 archivo(s) consumidor(es)
- `error_messages`: 7 archivo(s) consumidor(es)
- `exceptions`: 83 archivo(s) consumidor(es)
- `text_utils`: 29 archivo(s) consumidor(es)
- `ui_helpers`: 24 archivo(s) consumidor(es)
- `ui_options`: 4 archivo(s) consumidor(es)
- `utils`: 16 archivo(s) consumidor(es)
- `validation`: 42 archivo(s) consumidor(es)

## 3. Wrappers o facades fuera de core

- No se detectaron wrappers puros de `app.core`.

## 4. Duplicacion estructural en app/core

- No se detectaron funciones o metodos con cuerpo identico.

## 5. Candidatos de codigo muerto

- `app/core/catalogs/fiscal/imss.py:17` -> `RamaSeguro` (class)
- `app/core/catalogs/fiscal/imss.py:28` -> `TasaIMSS` (class)
- `app/core/catalogs/fiscal/isn.py:17` -> `EstadoISN` (class)
- `app/core/catalogs/fiscal/isr.py:16` -> `RangoISR` (class)
- `app/core/catalogs/fiscal/isr.py:32` -> `PoliticaSubsidioEmpleo` (class)
- `app/core/catalogs/fiscal/salario_minimo.py:19` -> `VigenciaSalarioMinimo` (class)
- `app/core/catalogs/fiscal/uma.py:16` -> `VigenciaUMA` (class)
- `app/core/catalogs/laboral/prestaciones.py:17` -> `PrestacionMinima` (class)
- `app/core/error_messages.py:90` -> `msg_clave_longitud` (function)
- `app/core/error_messages.py:126` -> `MSG_REQUISICION_SIN_PARTIDAS` (constant)
- `app/core/error_messages.py:130` -> `MSG_CONTRATAR_SIN_CONTRATO` (constant)
- `app/core/ui_helpers.py:89` -> `opciones_desde_lista` (function)
- `app/core/ui_helpers.py:141` -> `opciones_si_no` (function)
- `app/core/validation/cfdi_validator.py:24` -> `NS_CFDI` (constant)
- `app/core/validation/cfdi_validator.py:25` -> `NS_TFD` (constant)
- `app/core/validation/cfdi_validator.py:28` -> `ResultadoValidacionCFDI` (class)
- `app/core/validation/constants.py:175` -> `AREA_DESTINO_MAX` (constant)
- `app/core/validation/constants.py:213` -> `ROLES_EMPRESA_VALIDOS` (constant)
- `app/core/validation/empresa_form_validators.py:40` -> `validar_campos_requeridos_empresa` (function)

## 6. Notas

- Los candidatos de codigo muerto se calculan de forma estatica y deben validarse antes de borrar.
- Los wrappers detectados no son necesariamente un problema, pero si un indicador de capa legacy o compatibilidad.
- La duplicacion estructural apunta a puntos naturales de centralizacion; no implica que todos deban abstraerse del mismo modo.
