# Instrucciones para Proteger Modulos con Autenticacion

## Objetivo

Cada modulo del sistema (empresas, empleados, contratos, etc.) debe verificar
que el usuario tenga una sesion activa antes de mostrar datos. Esto se logra
cambiando la herencia del State de `BaseState` a `AuthState`.

## Cadena de Herencia

```
rx.State (Reflex)
    -> BaseState (loading, errores, mensajes)
        -> AuthState (sesion, usuario, empresas, permisos)
            -> TuModuloState (datos del modulo)
```

Al heredar de `AuthState` en lugar de `BaseState`, el state del modulo
obtiene acceso a:

- `self.usuario_actual` - perfil del usuario logueado (dict)
- `self.empresa_actual` - empresa seleccionada (dict)
- `self.esta_autenticado` - True si hay sesion activa
- `self.es_admin` / `self.es_client` - rol del usuario
- `self.nombre_usuario` - nombre para mostrar en UI
- `self.id_empresa_actual` - ID de la empresa seleccionada
- `self.verificar_y_redirigir()` - verifica sesion y redirige a login si no hay
- Todos los helpers de BaseState (loading, saving, mensajes, errores)

## Pasos para Proteger un Modulo

### Paso 1: Cambiar import en el State

**Archivo:** `app/presentation/pages/{modulo}/{modulo}_state.py`

Antes:
```python
from app.presentation.components.shared.base_state import BaseState

class MiModuloState(BaseState):
```

Despues:
```python
from app.presentation.components.shared.auth_state import AuthState

class MiModuloState(AuthState):
```

### Paso 2: Agregar metodo on_mount con verificacion

Agregar un metodo `on_mount_{modulo}` que primero verifique la sesion
y luego cargue los datos:

```python
async def on_mount_mi_modulo(self):
    """Verifica autenticacion y carga datos."""
    resultado = await self.verificar_y_redirigir()
    if resultado:
        return resultado
    await self.cargar_datos()
```

Si el modulo ya tenia un metodo de carga (ej: `cargar_empresas`), no lo
elimines. Solo crea el nuevo `on_mount_*` que lo llama despues de verificar auth.

### Paso 3: Actualizar la pagina para usar el nuevo on_mount

**Archivo:** `app/presentation/pages/{modulo}/{modulo}_page.py`

Buscar el `on_mount` actual y cambiarlo:

Antes:
```python
on_mount=MiModuloState.cargar_datos,
```

Despues:
```python
on_mount=MiModuloState.on_mount_mi_modulo,
```

### Paso 4: Verificar imports

Ejecutar para confirmar que no hay errores de importacion:

```bash
poetry run python -c "from app.presentation.pages.{modulo}.{modulo}_state import MiModuloState; print('OK')"
```

## Ejemplo Completo: Empresas

### empresas_state.py (cambios)

```python
# Cambio 1: import
from app.presentation.components.shared.auth_state import AuthState

# Cambio 2: herencia
class EmpresasState(AuthState):
    """Estado para la gestion de empresas (protegido con autenticacion)."""

    # Cambio 3: nuevo on_mount
    async def on_mount_empresas(self):
        """Verifica autenticacion y carga empresas."""
        resultado = await self.verificar_y_redirigir()
        if resultado:
            return resultado
        await self.cargar_empresas()

    # El resto del state no cambia
    async def cargar_empresas(self):
        ...
```

### empresas_page.py (cambio)

```python
# Cambio 4: usar nuevo on_mount
rx.box(
    ...,
    on_mount=EmpresasState.on_mount_empresas,  # antes: cargar_empresas
)
```

## Lista de Modulos a Proteger

| Modulo | State | on_mount actual | Estado |
|--------|-------|-----------------|--------|
| Empresas | EmpresasState | cargar_empresas | Protegido |
| Empleados | EmpleadosState | cargar_empleados | Pendiente |
| Contratos | ContratosState | cargar_contratos | Pendiente |
| Plazas | PlazasState | cargar_plazas | Pendiente |
| Requisiciones | RequisicionesState | cargar_requisiciones | Pendiente |
| Categorias Puesto | CategoriasPuestoState | cargar_categorias | Pendiente |
| Tipos de Servicio | TipoServicioState | cargar_tipos_servicio | Pendiente |
| Historial Laboral | HistorialLaboralState | cargar_historial | Pendiente |
| Sedes | SedesState | cargar_sedes | Pendiente |
| Configuracion | ConfiguracionState | cargar_configuracion | Pendiente |
| Simulador | SimuladorState | (verificar) | Pendiente |
| Admin Usuarios | UsuariosAdminState | on_mount_admin | Ya protegido |

## Notas Importantes

1. **No eliminar el metodo de carga original** (ej: `cargar_empresas`).
   Otros componentes pueden llamarlo directamente (ej: despues de crear/editar).

2. **DEBUG mode**: Si `Config.DEBUG=True`, `verificar_y_redirigir()` no redirige.
   Esto permite desarrollo local sin autenticacion.

3. **El sidebar ya esta protegido**: `SidebarState` hereda de `AuthState`,
   por lo que muestra el nombre del usuario y oculta el menu de admin
   para usuarios no-admin.

4. **Filtrado por empresa**: Despues de verificar auth, puedes usar
   `self.obtener_empresa_id_para_filtro()` para filtrar datos segun el
   usuario (admin ve todo, client solo su empresa).
