# Guia de Naming y Contratos Reusables

## Objetivo
Estandarizar nombres y contratos de la capa reusable para evitar divergencia entre `admin`, `portal`, `api`, `services` y `repositories`.

## Regla de idioma (repo actual)
- Ingles para componentes tecnicos y genericos: `*_modal`, `*_table`, `*_shell`, `query_helpers`.
- Espanol para texto visible al usuario: labels, mensajes, botones.
- Terminos de dominio MX se conservan cuando son canon del negocio: `curp`, `rfc`, `nss`, `cfdi`, `estatus`.
- No mezclar idiomas en el mismo identificador (`guardarEmployee`, `empleadoFormModal`).

## Naming por tipo de reusable
- `*_field`: campo puntual de formulario.
- `*_row`: fila de formulario o fila de tabla.
- `*_section`: bloque agrupado de UI.
- `*_modal`: modal reusable completo.
- `*_body`: cuerpo reusable de modal/formulario.
- `*_table`: tabla reusable.
- `*_list`: lista reusable.
- `*_shell`: contenedor visual reutilizable (estructura, no negocio).
- `*_kit`: conjunto de piezas relacionadas (opcional, nivel alto).

## Glosario canonico (usar de forma consistente)
- `employee` / `empleado`: usar `employee` en shared/reusable; `empleado` permitido en estados legacy y textos.
- `company` / `empresa`: preferir `empresa` en entidades y dominio existente.
- `status` / `estatus`: preferir `estatus` en dominio y datos.
- `document` / `documento`: `document_*` para reusables shared; `documento` permitido en dominio/UI local.

## Contratos de reusables (actuales)

### `employee_form_modal(...)`
Archivo: `/Users/julioctb/Desktop/Dashboard-pletorica/app/presentation/components/reusable/employee_form_modal.py`

Parametros requeridos:
- `open_state`
- `title`
- `description`
- `body`
- `on_cancel`
- `on_save`
- `save_text`
- `saving`

Opcionales:
- `save_loading_text`
- `save_color_scheme`
- `max_width`

Uso:
- Encapsula shell de `rx.dialog` y footer de acciones.
- No debe contener validaciones de negocio.

### `employee_form_body(...)`
Archivo: `/Users/julioctb/Desktop/Dashboard-pletorica/app/presentation/components/reusable/employee_form_modal.py`

Contrato:
- Recibe componentes hijos de formulario.
- Normaliza `spacing`, `width` y `padding_y`.

### `document_table_shell(...)`
Archivo: `/Users/julioctb/Desktop/Dashboard-pletorica/app/presentation/components/reusable/document_list_kit.py`

Parametros requeridos:
- `headers` (lista de dicts con `nombre`, opcional `ancho`)
- `items`
- `row_renderer`
- `has_items`
- `empty_title`
- `empty_description`

Opcionales:
- `empty_icon`
- `variant`

Uso:
- Reutiliza estructura de tabla + estado vacio.
- Las filas y acciones siguen delegadas al modulo consumidor.

## Reglas para nuevas extracciones
1. Abstraer solo con 2+ usos reales o uso transversal claro.
2. Mantener wrappers/re-exports cuando exista consumo legacy.
3. Separar shell visual de logica de negocio.
4. Documentar variaciones con `mode`, `variant` o `profile` (no crear versiones duplicadas).

## Checklist PR (nuevos reusables)
- Nombre cumple sufijo (`_field`, `_section`, `_shell`, etc.).
- Contrato documentado en docstring.
- Tiene al menos 2 usos o un caso transversal claro.
- No introduce texto hardcode duplicado innecesario.
- Mantiene compatibilidad (wrapper o re-export) si reemplaza algo existente.
