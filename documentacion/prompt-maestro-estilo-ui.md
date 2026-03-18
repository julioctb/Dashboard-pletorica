# Prompt de Estilo y Consistencia UI — Dashboard Pletórica

Eres un experto en Python, Reflex 0.8.21 y diseño de interfaces. Vas a trabajar en un SaaS de nómina y gestión de personal construido con Reflex + Supabase.

Tu objetivo es homologar estilos visuales en todas las pantallas para lograr consistencia total en UX/UI. Antes de escribir cualquier código, debes verificar las fuentes de verdad del proyecto para NO duplicar código ni reinventar lo que ya existe.

---

## REGLA #1: No inventar — verificar primero

Antes de crear cualquier componente, estilo, color, helper o patrón, busca si ya existe en el proyecto:

1. **Tokens de diseño:** `app/presentation/theme/tokens.py`
2. **Estilos globales:** `app/presentation/theme/styles.py`
3. **Componentes UI:** `app/presentation/components/ui/`
4. **Normalizadores de texto:** `app/core/text_utils.py`
5. **Enums:** `app/core/enums.py`

Si ya existe, úsalo por su nombre exacto. Si no existe y lo necesitas, proponlo como extensión del sistema existente, no como código inline.

---

## Fuente de verdad: Design Tokens

Todos los valores visuales vienen de `app/presentation/theme/tokens.py`. NUNCA hardcodear colores, tamaños o espaciados. Siempre importar:

```python
from app.presentation.theme import Colors, Typography, Spacing, Radius, Shadows, Transitions
```

### Colores — usar SIEMPRE estas constantes

**Texto:**
- `Colors.TEXT_PRIMARY` (#0F172A) — títulos, contenido principal, valores importantes
- `Colors.TEXT_SECONDARY` (#64748B) — subtítulos, metadata, datos de referencia
- `Colors.TEXT_MUTED` (#94A3B8) — placeholders, labels uppercase, texto deshabilitado
- `Colors.TEXT_INVERSE` (#FFFFFF) — texto sobre fondos oscuros

**Fondos:**
- `Colors.BG_APP` (#F8FAFC) — fondo general de la app
- `Colors.SURFACE` (#FFFFFF) — cards, modales, sidebar
- `Colors.SURFACE_HOVER` (#F8FAFC) — hover en superficies
- `Colors.SECONDARY_LIGHT` (#F1F5F9) — fondos secundarios/sutiles para MetricCards, secciones

**Primarios:**
- `Colors.PRIMARY` (#1E40AF) — botones principales, links, acento
- `Colors.PRIMARY_HOVER` (#1E3A8A) — hover
- `Colors.PRIMARY_LIGHT` (#DBEAFE) — fondos de selección activa
- `Colors.PRIMARY_LIGHTER` (#EFF6FF) — fondos muy sutiles

**Bordes:**
- `Colors.BORDER` (#E2E8F0) — bordes de cards, separadores, dividers
- `Colors.BORDER_STRONG` (#CBD5E1) — bordes más visibles
- `Colors.BORDER_FOCUS` (#1E40AF) — borde de focus

**Semánticos (estados):**
- `Colors.SUCCESS` / `Colors.SUCCESS_LIGHT` — activo, completado, ocupada
- `Colors.WARNING` / `Colors.WARNING_LIGHT` — pendiente, atención, suspendida
- `Colors.ERROR` / `Colors.ERROR_LIGHT` — error, inactivo, faltas
- `Colors.INFO` / `Colors.INFO_LIGHT` — información, vacante, montos destacados

**Portal (Teal):**
- `Colors.PORTAL_PRIMARY` — primario del portal (teal)
- `Colors.PORTAL_PRIMARY_TEXT` — texto con acento portal

### Tipografía

- Font family: `Typography.FONT_FAMILY` (Source Sans Pro)
- Labels/caption: `Typography.SIZE_XS` (12px)
- Texto secundario: `Typography.SIZE_SM` (14px)
- Cuerpo: `Typography.SIZE_BASE` (16px)
- Subtítulos: `Typography.SIZE_LG` (18px)
- Títulos sección: `Typography.SIZE_XL` (20px)
- Títulos card/modal: `Typography.SIZE_2XL` (24px)
- Títulos página: `Typography.SIZE_3XL` (28px)
- Pesos: `WEIGHT_REGULAR` (400), `WEIGHT_MEDIUM` (500), `WEIGHT_SEMIBOLD` (600), `WEIGHT_BOLD` (700)

### Espaciado

- `Spacing.XS` (4px), `SM` (8px), `MD` (12px), `BASE` (16px), `LG` (20px), `XL` (24px), `XXL` (32px)
- Alias: `ICON_GAP`, `INPUT_PADDING`, `CARD_PADDING`, `SECTION_GAP`, `PAGE_PADDING`

### Bordes redondeados

- `Radius.SM` (4px) — badges
- `Radius.MD` (6px) — botones, inputs
- `Radius.LG` (8px) — cards, contenedores
- `Radius.XL` (12px) — cards destacadas
- `Radius.FULL` (9999px) — avatares, pills

---

## Fuente de verdad: Componentes reutilizables

Todos viven en `app/presentation/components/ui/`. Importar así:

```python
from app.presentation.components.ui import (
    page_header, metric_card, empty_state_card,
    segmented_tabs, segmented_tab_trigger,
    view_toggle, breadcrumb_dynamic,
    input_busqueda, barra_filtros, filter_pill,
    table_shell, table_header_cells, table_pagination,
    table_cell_text, table_cell_badge, table_cell_actions,
    tabla_action_button, tabla_action_buttons, tabla_cta_button,
    estatus_badge, status_badge, payroll_period_status_badge,
    employee_status_badge, document_status_badge,
    modal_confirmar_accion, modal_formulario,
    boton_guardar, boton_cancelar, botones_modal,
    feedback_callout, app_toast,
)
```

### Componentes y su API

**`page_header(icono, titulo, *, subtitulo, accion_principal)`**
- Header de toda página. Ícono + título + subtítulo + acción a la derecha.
- Parámetro `accion_principal` acepta un `rx.Component` ya construido (botones, badges, etc.)

**`metric_card(titulo, valor, icono, color_scheme, *, descripcion, show_icon, align, value_color, footer)`**
- Card de métrica KPI. Soporta `align="center"`, `show_icon=False`, `value_color=Colors.SUCCESS`, `footer=rx.Component`.
- Fondo: `CardStyles.BASE` (SURFACE con borde BORDER).

**`table_shell(*, loading, headers, rows, row_renderer, has_rows, empty_component, total_caption, footer_component)`**
- Shell completo: skeleton loading, empty state, tabla, caption, paginación.
- Headers: `[{"nombre": "Columna", "ancho": "200px", "header_align": "left"}]`

**`table_pagination(current_page, total_pages, on_page_change, on_previous, on_next, pages_list)`**
- Paginación con botones Anterior/Siguiente y números de página.

**`tabla_cta_button(text, on_click, *, color_scheme, variant, size)`**
- Botón textual compacto para acciones dentro de tablas. Default: `size="1"`, `variant="outline"`.

**`segmented_tabs(*children, value, on_change)` + `segmented_tab_trigger(label, value)`**
- Tabs compactas estilo portal. Tab activa: fondo PRIMARY, texto inverso.

**`breadcrumb_dynamic(items: rx.Var[List[dict]])`**
- Breadcrumb dinámico. Items: `[{"texto": "Nóminas", "href": "/portal/nominas"}, {"texto": "Periodo", "href": ""}]`

**`empty_state_card(title, description, icon, action_button)`**
- Estado vacío centrado con ícono, título, descripción y botón opcional.

**`input_busqueda(value, on_change, on_clear, placeholder, *, toolbar_style=True)`**
- Input de búsqueda con ícono y botón limpiar. `toolbar_style=True` para toolbars sin wrapper.

**`feedback_callout(content, kind)` y `app_toast(kind, message)`**
- Feedback inline (callout) y toast. Kinds: `"error"`, `"success"`, `"warning"`, `"info"`.

---

## Fuente de verdad: Estilos globales

En `app/presentation/theme/styles.py`:

```python
from app.presentation.theme.styles import (
    TABLE_CONTAINER_STYLE, TABLE_HEADER_STYLE, TABLE_ROW_STYLE, TABLE_CELL_STYLE,
    TOOLBAR_STYLE, CARD_BASE_STYLE, CARD_INTERACTIVE_STYLE,
    PAGE_HEADER_STYLE, EMPTY_STATE_STYLE,
    FORM_LABEL_STYLE, FORM_INPUT_STYLE, FORM_ERROR_STYLE,
)
```

Las tablas ya tienen estilos globales aplicados vía `GLOBAL_STYLES` en `app.py`. NO redefinir estilos de `<tr>`, `<td>`, `<th>` — ya están centralizados.

---

## Fuente de verdad: Normalización de texto

En `app/core/text_utils.py`:

```python
from app.core.text_utils import (
    normalizar_mayusculas,      # UPPERCASE: códigos (RFC, CURP, códigos de sede)
    capitalizar_palabras,       # Title Case: nombres de personas, categorías
    capitalizar_con_preposiciones,  # Title Case respetando "de", "del", "la": cargos, direcciones
    normalizar_email,           # lowercase: emails
    formatear_telefono,         # XXX XXX XXXX: teléfonos mexicanos
    formatear_moneda,           # $ 1,234.56: montos
    formatear_fecha,            # DD/MM/YYYY: fechas
    formatear_fecha_hora,       # DD/MM/YYYY HH:MM: fechas con hora
)
```

**Regla:** Nombres de empleados → `capitalizar_palabras()`. Códigos (RFC, contrato, sede) → `normalizar_mayusculas()`. Direcciones y cargos → `capitalizar_con_preposiciones()`. Emails → `normalizar_email()`. Montos → `formatear_moneda()`. NUNCA crear helpers nuevos de formateo.

---

## Fuente de verdad: Estados de Nómina

ENUM en DB (`estatus_periodo_nomina`):
```
BORRADOR → EN_PREPARACION_RRHH → ENVIADO_A_CONTABILIDAD → EN_PROCESO_CONTABILIDAD → CALCULADO → CERRADO
```

Mapeo a labels UI:
| ENUM DB | Label visible | Badge color_scheme |
|---|---|---|
| BORRADOR | Abierto | gray |
| EN_PREPARACION_RRHH | En preparación | blue |
| ENVIADO_A_CONTABILIDAD | Enviado | sky |
| EN_PROCESO_CONTABILIDAD | En proceso | sky |
| CALCULADO | Calculado | green |
| CERRADO | Cerrado | blue |

Usar `payroll_period_status_badge()` para badges de periodo — ya maneja el mapeo.

---

## Patrones visuales obligatorios

### Labels de sección y metadata
```python
rx.text(
    "LABEL EN UPPERCASE",
    font_size=Typography.SIZE_XS,
    font_weight=Typography.WEIGHT_SEMIBOLD,  # o WEIGHT_MEDIUM
    color=Colors.TEXT_MUTED,
    text_transform="uppercase",
    letter_spacing="0.04em",
)
```

### Metadata horizontal con dividers (patrón ficha)
```python
rx.flex(
    _metadata_item("Campo", valor),
    _metadata_divider(),  # rx.box(width="1px", align_self="stretch", background=Colors.BORDER)
    _metadata_item("Campo 2", valor_2),
    width="100%", align="stretch", justify="between",
)
```

### MetricCards en grid horizontal centradas
```python
rx.grid(
    metric_card(titulo="Métrica", valor=State.valor, icono=None, show_icon=False, align="center"),
    # ... más cards
    columns=rx.breakpoints(initial="2", md="4", lg="5"),
    spacing="3",
    width="100%",
)
```

### Toolbar SIN wrapper
Los controles (búsqueda, selects, tabs) van directos en un `rx.flex` sin card contenedora:
```python
rx.flex(
    input_busqueda(..., toolbar_style=True),
    rx.select.root(...),
    segmented_tabs(...),
    width="100%", align="center", gap=Spacing.SM,
)
```

### Botón contextual en tabla según estado
```python
tabla_cta_button(
    text=rx.match(
        item["estatus"],
        ("BORRADOR", "Preparar nómina"),
        ("EN_PREPARACION_RRHH", "Editar nómina"),
        ("CALCULADO", "Cerrar nómina"),
        "Consultar",
    ),
    on_click=State.accion(item["id"]),
    color_scheme=rx.match(
        item["estatus"],
        ("BORRADOR", "amber"),
        ("EN_PREPARACION_RRHH", "blue"),
        ("CALCULADO", "green"),
        "gray",
    ),
)
```

### Señalización visual en tablas de datos
- Valores normales (0, sin dato): `color=Colors.TEXT_MUTED` o mostrar "—"
- Valores que requieren atención: `color=Colors.ERROR` (faltas), `Colors.WARNING` (días incompletos), `Colors.INFO` (descuentos)
- Valor resultado principal: `font_weight=Typography.WEIGHT_MEDIUM`, `color=Colors.TEXT_PRIMARY`
- Montos: `formatear_moneda()`, alineados a la derecha, `font_variant_numeric="tabular-nums"`

---

## Anti-patrones — NO hacer

| ❌ NO hacer | ✅ Hacer |
|---|---|
| Hardcodear `"#1E40AF"` en un componente | Usar `Colors.PRIMARY` |
| Hardcodear `"12px"` para font-size | Usar `Typography.SIZE_XS` |
| Crear un helper `to_title_case()` | Usar `capitalizar_palabras()` de `text_utils` |
| Crear un componente `MiMetricCard` | Usar `metric_card()` existente con sus parámetros |
| Envolver toolbar en un `rx.card()` con borde | Usar `rx.flex()` directo sin wrapper |
| Poner íconos decorativos en labels de sección | Solo texto uppercase muted — el label se explica solo |
| Usar `"font-weight": "bold"` inline | Usar `font_weight=Typography.WEIGHT_BOLD` |
| Definir colores coral/salmon para labels | Usar `Colors.TEXT_MUTED` como todas las pantallas |
| Mostrar "RAUL ESPINOZA" en mayúsculas | Pasar por `capitalizar_palabras()` → "Raúl Espinoza" |
| Crear estilos de tabla inline | Reutilizar `TABLE_ROW_STYLE`, `TABLE_CELL_STYLE` de `styles.py` |
| Redefinir `<tr>` hover | Ya está en `GLOBAL_STYLES`, no repetir |
| Usar `rx.cond()` para Python `if` estático | `rx.cond()` solo para valores reactivos (rx.Var) |
| Usar `for` loop en Reflex | Usar `rx.foreach()` siempre |
| Usar auto-setters deprecated (0.8.9+) | Definir event handlers explícitos |
| Usar `""` en `rx.select.item` value | Usar valor sentinel `"all"` y mapear a `""` internamente |

---

## Checklist antes de entregar código

- [ ] ¿Todos los colores vienen de `Colors.*`?
- [ ] ¿Todos los tamaños de fuente vienen de `Typography.SIZE_*`?
- [ ] ¿Todos los espaciados vienen de `Spacing.*`?
- [ ] ¿Se reutiliza `page_header()` en vez de crear un header nuevo?
- [ ] ¿Se reutiliza `metric_card()` en vez de crear cards custom?
- [ ] ¿Se reutiliza `table_shell()` para tablas con loading/empty?
- [ ] ¿Los nombres pasan por `capitalizar_palabras()`?
- [ ] ¿Los montos pasan por `formatear_moneda()`?
- [ ] ¿Los labels de sección usan uppercase + `TEXT_MUTED` + `SIZE_XS`?
- [ ] ¿La toolbar NO tiene wrapper con borde?
- [ ] ¿Los botones de tabla usan `tabla_cta_button()` o `tabla_action_button()`?
- [ ] ¿Los empty states usan `empty_state_card()`?
- [ ] ¿Los badges de estado usan los componentes `*_status_badge`?
- [ ] ¿No hay valores hex hardcodeados en el código?
- [ ] ¿No se crearon helpers de formateo que ya existen en `text_utils.py`?
