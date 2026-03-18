# Auditoría de código (`app/core`) — repetición, código muerto y redundancia

Fecha: 2026-03-16

## Alcance

- Se auditó el árbol `app/core` como **fuente de verdad**.
- El análisis incluyó:
  - Búsqueda de definiciones públicas sin referencias en el repositorio.
  - Detección de funciones duplicadas por estructura (normalización AST ligera).
  - Revisión manual de módulos con posible solapamiento funcional.

---

## 1) Código repetitivo detectado

### 1.1 Función `_coerce_fecha` repetida en 3 catálogos fiscales

Se encontró la misma lógica en:

- `app/core/catalogs/fiscal/isr.py`
- `app/core/catalogs/fiscal/salario_minimo.py`
- `app/core/catalogs/fiscal/uma.py`

**Impacto**: triplica mantenimiento para una misma normalización de fecha.

**Recomendación**: extraer a helper compartido (ej. `app/core/catalogs/fiscal/_shared.py`) y reutilizar.

### 1.2 Método `aplica_a` repetido en 3 dataclasses de vigencia

Se repite el mismo patrón en:

- `RangoISR.aplica_a`
- `VigenciaSalarioMinimo.aplica_a`
- `VigenciaUMA.aplica_a`

**Impacto**: duplicación de regla de inclusión por fecha.

**Recomendación**: mover a mixin/base class (`VigenciaBase`) para unificar comportamiento.

### 1.3 Lógica duplicada de `descripcion` en enums

Se detectaron dos implementaciones idénticas en `app/core/enums.py`.

**Impacto**: riesgo de divergencia en labels de UI si se modifica solo una.

**Recomendación**: unificar en helper privado reutilizable dentro del mismo módulo.

---

## 2) Código muerto (candidatos) en `core`

> Nota: esto es análisis estático por referencias textuales; requiere validación funcional antes de eliminar.

Se detectaron símbolos públicos sin referencias externas en `app/`:

- `app/core/text_utils.py::formatear_telefono`
- `app/core/error_messages.py::msg_clave_longitud`
- `app/core/ui_helpers.py::opciones_desde_lista`
- `app/core/ui_helpers.py::opciones_si_no`
- `app/core/validation/cfdi_validator.py::ResultadoValidacionCFDI`
- `app/core/catalogs/laboral/prestaciones.py::PrestacionMinima`
- `app/core/catalogs/fiscal/imss.py::RamaSeguro`
- `app/core/catalogs/fiscal/imss.py::TasaIMSS`
- `app/core/catalogs/fiscal/isr.py::RangoISR`
- `app/core/catalogs/fiscal/isr.py::PoliticaSubsidioEmpleo`
- `app/core/catalogs/fiscal/isn.py::EstadoISN`
- `app/core/catalogs/fiscal/salario_minimo.py::VigenciaSalarioMinimo`
- `app/core/catalogs/fiscal/uma.py::VigenciaUMA`

**Recomendación**:

1. Marcar como `@deprecated` lo que no se use en runtime.
2. Agregar pruebas de contrato para los símbolos realmente públicos.
3. Eliminar en una segunda fase lo no referenciado y no exportado.

---

## 3) Redundancia estructural

### 3.1 Módulos de catálogo sin referencias directas por import

Hay módulos de `app/core/catalogs/*` que no aparecen importados directamente desde `app/`.
Aunque varios podrían usarse indirectamente vía `__init__.py`, conviene validar su uso real en runtime.

**Riesgo**: mantener catálogos huérfanos o legacy sin consumidor.

### 3.2 `ui_options.py` + `ui_option_sets.py`

Existe separación saludable, pero hay frontera difusa entre:

- opciones estáticas de display
- factories de opciones dinámicas

**Recomendación**: consolidar criterio:

- `ui_options.py` solo constantes estáticas.
- `ui_option_sets.py` solo builders/factories.

---

## 4) Priorización sugerida

1. **Alta**: extraer `_coerce_fecha` y `aplica_a` a util compartida/base class.
2. **Media**: depurar candidatos de código muerto con pruebas de no-regresión.
3. **Media**: normalizar frontera `ui_options` vs `ui_option_sets`.
4. **Baja**: limpieza progresiva de exports públicos no usados.

---

## 5) Comandos usados en la auditoría

```bash
python - <<'PY'
# (script AST) símbolos públicos sin referencias en app/
PY
```

```bash
python - <<'PY'
# (script AST+hash) detección de funciones duplicadas en app/core
PY
```

```bash
for f in app/core/*.py app/core/catalogs/**/*.py app/core/validation/*.py; do
  # conteo de referencias por import textual
done
```
