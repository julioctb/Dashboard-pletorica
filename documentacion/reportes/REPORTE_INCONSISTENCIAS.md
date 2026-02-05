# Reporte de Inconsistencias de Diseño
## Dashboard Pletorica - Análisis de Código

**Fecha:** 2026-01-13
**Analizado por:** Claude Code

---

## Resumen Ejecutivo

Se encontraron **15 categorías de inconsistencias** en el código del proyecto. Este reporte detalla cada una con ejemplos de código, explicación del problema y recomendación de solución.

| Severidad | Cantidad | Descripción |
|-----------|----------|-------------|
| 🔴 Crítica | 3 | Afectan funcionamiento o mantenibilidad |
| 🟠 Media | 4 | Inconsistencias de patrones |
| 🟡 Menor | 8 | Diferencias estéticas/organizativas |

---

## 🔴 INCONSISTENCIAS CRÍTICAS

### 1. Event Handlers: async vs sync

**Problema:** Los manejadores de eventos de teclado usan patrones completamente diferentes entre módulos. Esto puede causar comportamientos inesperados y dificulta el mantenimiento.

**Empresas** (`app/presentation/pages/empresas/empresas_state.py:516-519`):
```python
async def handle_key_down(self, key):
    """Manejar tecla Enter en el campo de búsqueda"""
    if key == "Enter":
        await self.aplicar_filtros()
```

**Tipo Servicio** (`app/presentation/pages/tipo_servicio/tipo_servicio_state.py:153-156`):
```python
def handle_key_down(self, key: str):  # NO es async
    """Manejar tecla presionada en búsqueda"""
    if key == "Enter":
        return TipoServicioState.buscar_tipos  # Retorna referencia a clase
```

**Explicación:**
- Empresas usa `async/await` y ejecuta la acción directamente
- Tipo Servicio usa función síncrona y retorna una referencia al método

**Recomendación:** Estandarizar todos los event handlers como `async` con `await` directo.

---

### 2. Manejo de Errores: Centralizado vs Inline

**Problema:** Empresas tiene un helper centralizado para manejar errores, mientras Tipo Servicio repite el código de manejo en cada método.

**Empresas** (`app/presentation/pages/empresas/empresas_state.py:398-417`):
```python
def _manejar_error(self, error, operacion="") -> None:
    """Centraliza el manejo de errores con mensajes apropiados"""
    if isinstance(error, DuplicateError):
        campo = getattr(error, 'field', 'campo')
        self.mensaje_info = f"Error: El {campo} ya existe"
    elif isinstance(error, NotFoundError):
        self.mensaje_info = f"Error: Registro no encontrado"
    elif isinstance(error, DatabaseError):
        self.mensaje_info = f"Error de base de datos: {str(error)}"
    else:
        self.mensaje_info = f"Error inesperado en {operacion}: {str(error)}"
    self.tipo_mensaje = "error"
```

**Uso en Empresas:**
```python
except Exception as e:
    self._manejar_error(e, "crear empresa")
```

**Tipo Servicio** (`app/presentation/pages/tipo_servicio/tipo_servicio_state.py:213-222`):
```python
# Código repetido en CADA método
except DuplicateError as e:
    self.error_clave = f"La clave '{self.form_clave}' ya existe"
except NotFoundError as e:
    self.mostrar_mensaje(str(e), "error")
except DatabaseError as e:
    self.mostrar_mensaje(f"Error de base de datos: {str(e)}", "error")
except Exception as e:
    self.mostrar_mensaje(f"Error inesperado: {str(e)}", "error")
```

**Explicación:**
- El patrón de Empresas es DRY (Don't Repeat Yourself)
- Tipo Servicio repite ~10 líneas de manejo de errores en cada método CRUD
- Si se necesita cambiar el formato de mensaje, hay que hacerlo en múltiples lugares

**Recomendación:** Implementar `_manejar_error()` en TipoServicioState (o mejor, en BaseState).

---

### 3. Variables de Estado de Carga Inconsistentes

**Problema:** Cada módulo usa nombres diferentes para indicar estados de carga/procesamiento.

| Módulo | Variable | Archivo |
|--------|----------|---------|
| Empresas | `saving` | `empresas_state.py:53` |
| Tipo Servicio | `loading`, `saving` | `tipo_servicio_state.py:32-33` |
| Simulador | `is_calculating` | `simulador_state.py:38` |

**Explicación:**
- `loading` = cargando datos iniciales
- `saving` = guardando cambios
- `is_calculating` = procesando cálculos

El problema es que no hay consistencia. Simulador debería usar `loading` o `processing`.

**Recomendación:**
```python
# Estandarizar en BaseState:
loading: bool = False      # Carga inicial de datos
saving: bool = False       # Operaciones de escritura
processing: bool = False   # Cálculos/operaciones largas
```

---

## 🟠 INCONSISTENCIAS MEDIAS

### 4. Patrón CRUD: Directo vs Wrapper

**Problema:** Los módulos usan diferentes patrones para operaciones CRUD.

**Empresas** - Métodos directos públicos:
```python
# app/presentation/pages/empresas/empresas_state.py
async def crear_empresa(self):      # Línea ~180
async def actualizar_empresa(self): # Línea ~220
```

**Tipo Servicio** - Wrapper con métodos privados:
```python
# app/presentation/pages/tipo_servicio/tipo_servicio_state.py
async def guardar_tipo(self):       # Línea 195 - WRAPPER público
async def _crear_tipo(self):        # Línea 229 - Privado
async def _actualizar_tipo(self):   # Línea 245 - Privado
```

**Explicación:**
- Empresas: El botón "Guardar" llama a `crear_empresa()` o `actualizar_empresa()` según contexto
- Tipo Servicio: El botón siempre llama a `guardar_tipo()` que decide internamente

**Ventaja del wrapper:** Un solo punto de entrada, lógica de decisión encapsulada.

**Recomendación:** Adoptar patrón wrapper en todos los módulos:
```python
async def guardar_empresa(self):
    if self.es_edicion:
        await self._actualizar_empresa()
    else:
        await self._crear_empresa()
```

---

### 5. Modelo Resumen Faltante

**Problema:** Empresas tiene un modelo optimizado para UI, Tipo Servicio no.

**Empresas** (`app/entities/empresa.py:273-302`):
```python
class EmpresaResumen(BaseModel):
    """Modelo resumido para listados - solo campos necesarios para UI"""
    id: int
    nombre_comercial: str
    rfc: str
    tipo_empresa: TipoEmpresa
    estatus: EstatusEmpresa

    @classmethod
    def from_empresa(cls, empresa: Empresa) -> 'EmpresaResumen':
        """Factory method para crear desde entidad completa"""
        return cls(
            id=empresa.id,
            nombre_comercial=empresa.nombre_comercial,
            # ...
        )
```

**Tipo Servicio** - No existe, usa conversión manual:
```python
# app/presentation/pages/tipo_servicio/tipo_servicio_state.py:137
self.tipos = [tipo.model_dump() for tipo in tipos]  # Conversión a dict
```

**Explicación:**
- `EmpresaResumen` reduce payload enviado al frontend
- Tipo Servicio envía la entidad completa (incluyendo campos innecesarios)

**Recomendación:** Crear `TipoServicioResumen` en `app/entities/tipo_servicio.py`.

---

### 6. Normalización de Texto en Diferentes Momentos

**Problema:** La conversión a mayúsculas ocurre en momentos diferentes.

**Empresas** - En helper separado (`empresas_state.py:420`):
```python
@staticmethod
def _normalizar_texto(texto: str) -> str:
    """Normaliza texto: strip + upper"""
    return texto.strip().upper() if texto else ""

# Se usa al preparar datos:
def _preparar_empresa_desde_formulario(self):
    return EmpresaCreate(
        rfc=self._normalizar_texto(self.form_rfc),
        # ...
    )
```

**Tipo Servicio** - En setters (`tipo_servicio_state.py:63-69`):
```python
def set_form_clave(self, value: str):
    """Set clave con auto-conversión a mayúsculas"""
    self.form_clave = value.upper() if value else ""

def set_form_nombre(self, value: str):
    """Set nombre con auto-conversión a mayúsculas"""
    self.form_nombre = value.upper() if value else ""
```

**Explicación:**
- Empresas: El usuario escribe en minúsculas, se normaliza al guardar
- Tipo Servicio: Se convierte a mayúsculas mientras el usuario escribe

**Recomendación:** Normalizar en setters (feedback inmediato al usuario).

---

### 7. Estado de Modal: String vs Boolean

**Problema:** Diferentes formas de rastrear el modo del modal.

**Empresas** (`empresas_state.py:50-52`):
```python
modo_modal_empresa: str = ""  # "crear" | "editar" | ""
mostrar_modal_empresa: bool = False
```

**Tipo Servicio** (`tipo_servicio_state.py:34-36`):
```python
es_edicion: bool = False
mostrar_modal_tipo: bool = False
```

**Explicación:**
- String permite más estados (futuro: "ver", "duplicar")
- Boolean es más simple pero menos extensible

**Recomendación:** Usar string para consistencia y extensibilidad.

---

## 🟡 INCONSISTENCIAS MENORES

### 8. Imports: Relative vs Absolute

**Empresas** - Relative imports:
```python
from .empresas_validators import validar_rfc
```

**Tipo Servicio** - Absolute imports:
```python
from app.presentation.pages.tipo_servicio.tipo_servicio_validators import validar_clave
```

**Recomendación:** Usar relative imports dentro del mismo módulo.

---

### 9. Métodos de Limpieza: Naming

| Módulo | Método | Visibilidad |
|--------|--------|-------------|
| Empresas | `limpiar_formulario()` | Público |
| Tipo Servicio | `_limpiar_formulario()` | Privado |
| Simulador | `limpiar()` | Público (nombre vago) |

**Recomendación:** `_limpiar_formulario()` privado en todos.

---

### 10. Propiedades Calculadas (@rx.var)

**Empresas:**
```python
@rx.var
def tiene_errores_formulario(self) -> bool:

@rx.var
def tiene_filtros_activos(self) -> bool:

@rx.var
def cantidad_filtros_activos(self) -> int:
```

**Tipo Servicio:**
```python
@rx.var
def tiene_errores_formulario(self) -> bool:

@rx.var
def puede_guardar(self) -> bool:  # NO EXISTE EN EMPRESAS
```

**Recomendación:** Agregar `puede_guardar` a Empresas.

---

### 11. Enums de Estatus

**Empresa** (3 estados):
```python
class EstatusEmpresa(str, Enum):
    ACTIVO = 'ACTIVO'
    INACTIVO = 'INACTIVO'
    SUSPENDIDO = 'SUSPENDIDO'
```

**Tipo Servicio** (2 estados):
```python
class EstatusTipoServicio(str, Enum):
    ACTIVO = 'ACTIVO'
    INACTIVO = 'INACTIVO'
```

**Nota:** Puede ser intencional (empresas necesitan más estados).

---

### 12. Dataclasses vs Pydantic

**costo_patronal.py** usa `@dataclass`:
```python
@dataclass
class ConfiguracionEmpresa:
    # ...
```

**Resto del proyecto** usa Pydantic:
```python
class Empresa(BaseModel):
    # ...
```

**Recomendación:** Migrar costo_patronal a Pydantic.

---

### 13. Métodos Adicionales en Servicios

**Tipo Servicio tiene métodos que Empresa no:**
- `obtener_por_clave()` - buscar por campo único
- `obtener_activas()` - conveniencia para dropdowns
- `contar()` - total de registros
- `existe_clave()` - validación

**Recomendación:** Agregar métodos equivalentes a EmpresaService si son útiles.

---

### 14. BaseState Subutilizado

**BaseState define:**
```python
class BaseState(rx.State):
    loading: bool = True
    mensaje_info: str = ""
    tipo_mensaje: str = "info"
```

**Pero cada State redefine `loading`:**
```python
class EmpresasState(BaseState):
    loading: bool = False  # Redefinido!
```

**Recomendación:** No redefinir variables del padre.

---

### 15. Archivos de Validators: Funciones Extra

**Empresas** (`empresas_validators.py`):
```python
def validar_campos_requeridos(data: dict) -> dict:
    """Valida múltiples campos a la vez"""
```

**Tipo Servicio** (`tipo_servicio_validators.py`):
```python
def validar_formulario_tipo(clave, nombre, descripcion) -> dict:
    """Similar pero con firma diferente"""
```

**Recomendación:** Estandarizar firma de funciones batch.

---

## Plan de Acción Recomendado

### Fase 1 - Críticas (Inmediato)
1. [ ] Estandarizar event handlers a async/await
2. [ ] Implementar `_manejar_error()` en BaseState
3. [ ] Renombrar variables de estado de carga

### Fase 2 - Medias (Corto plazo)
4. [ ] Adoptar patrón wrapper CRUD en Empresas
5. [ ] Crear TipoServicioResumen
6. [ ] Mover normalización a setters en Empresas
7. [ ] Usar string para modo_modal en Tipo Servicio

### Fase 3 - Menores (Cuando sea conveniente)
8. [ ] Unificar estilo de imports
9. [ ] Renombrar métodos de limpieza
10. [ ] Agregar `puede_guardar` a Empresas
11. [ ] Migrar costo_patronal a Pydantic

---

## Archivos Afectados

| Archivo | Inconsistencias |
|---------|-----------------|
| `empresas_state.py` | #1, #2, #4, #6, #7, #9, #10 |
| `tipo_servicio_state.py` | #1, #2, #3, #4, #6, #7, #8, #9 |
| `simulador_state.py` | #3, #9 |
| `base_state.py` | #14 |
| `empresa.py` | #5, #11 |
| `tipo_servicio.py` | #5, #11 |
| `costo_patronal.py` | #12 |
| `*_validators.py` | #15 |
| `*_service.py` | #13 |

---

*Generado automáticamente por Claude Code*
