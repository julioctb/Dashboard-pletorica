# Core Source Map

## Fuentes de verdad canónicas

- `app/core/validation/`
  Centraliza `FieldConfig`, factories, constantes de validación, normalizadores y validadores reutilizables de usuario, empleados, bancos, contratos, pagos, sedes y catálogos.
- `app/core/enums.py`
  Enum source of truth compartida por entidades, servicios y UI.
- `app/core/error_messages.py`
  Mensajes y builders de error compartidos.
- `app/core/text_utils.py`
  Normalización y formateo transversal de texto, email, URL, teléfonos e iniciales.
- `app/core/ui_helpers.py`
  Builders base para opciones, filtros y paginación.
- `app/core/ui_option_sets.py`
  Factories de conjuntos de opciones derivados para contextos concretos.
- `app/core/ui_options.py`
  Opciones estáticas ya materializadas para consumo de UI.
- `app/core/catalogs/`
  Datos maestros fiscales, laborales, de nómina y del sistema.
- `app/core/calculations/`
  Cálculos fiscales y laborales deterministas.
- `app/core/constants/`
  Constantes globales muy compartidas, como permisos.
- `app/core/config/`, `app/core/exceptions.py`, `app/core/compresores/`
  Infraestructura transversal.

## Adaptadores y facades conocidos fuera de core

El objetivo es no tener wrappers de validación fuera de `app/core`. Si aún existe alguno, tratarlo como compatibilidad temporal y no como fuente de verdad.

Estado actual del repo:

- No hay wrappers legacy de validación activos en `app/presentation/pages`.

Si un cambio toca reglas nuevas, agregarlas en `app/core/validation/*`. Si reaparecen wrappers en `presentation`, considerarlos deuda técnica y migrar sus consumidores cuanto antes.

## Hotspots actuales del repo

- `app/core/catalogs/fiscal/isr.py`, `app/core/catalogs/fiscal/salario_minimo.py` y `app/core/catalogs/fiscal/uma.py`
  Repiten helpers de coerción de fecha y reglas de vigencia por rango.
- `app/core/enums.py`
  Tiene muchas propiedades `descripcion`; el riesgo no es cada enum aislado, sino la repetición del patrón y la posibilidad de divergencia.
- `app/core/ui_helpers.py` vs `app/core/ui_option_sets.py` vs `app/core/ui_options.py`
  La frontera correcta es: helpers base, factories de dominio y materializaciones estáticas. Si se mezcla, reaparece duplicación.
- Reaparición de `app/presentation/pages/*/*_validators.py`
  Si vuelve a aparecer un wrapper fino hacia `core.validation`, tratarlo como regresión arquitectónica.

## Guardrails para revisión

- No borrar símbolos solo porque un escaneo textual no los encuentre; validar reexports y uso en runtime.
- No mover lógica a `utils.py` genéricos. Preferir nombres específicos por dominio o responsabilidad.
- No centralizar por reflejo; si un helper solo sirve a un módulo, mantenerlo cerca.
- Cuando haya duda entre `core.validation` y `presentation`, la regla reusable normalmente debe vivir en `core.validation`.
