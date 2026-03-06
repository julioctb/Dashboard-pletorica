# CLAUDE.md

Guia operativa para asistentes de codigo que trabajen en este repositorio.

## Fuente de verdad

Cuando exista conflicto entre este archivo y el codigo, usar en este orden:

1. `app/app.py` para rutas, layouts y composicion entre backoffice y portal.
2. `pyproject.toml` para versiones, dependencias y runtime.
3. `rxconfig.py` para configuracion de Reflex y plugins.
4. La estructura real de `app/` para decidir capas, naming y colocacion.

## Snapshot del proyecto

- Stack principal: Python `>=3.10,<4.0`
- UI: Reflex `>=0.8.21,<0.9.0`
- Backend de datos: Supabase PostgreSQL + Storage + Auth
- API embebida: FastAPI montada via `api_transformer`
- Estado actual: produccion
- Dominio principal: administracion de personal, contratos, entregables, requisiciones, usuarios, nominas y portal cliente

## Comandos de desarrollo

```bash
# Instalar dependencias
poetry install

# Ejecutar app Reflex
poetry run reflex run

# Re-inicializar Reflex si hace falta
poetry run reflex init

# Tests
pytest
pytest app/tests/test_validation.py
pytest -v

# Calidad de codigo
poetry run black app/
poetry run isort app/
poetry run flake8 app/
poetry run mypy app/
```

## Arquitectura real

El repo combina tres superficies:

1. Backoffice Reflex
2. Portal cliente Reflex
3. API REST FastAPI limitada

### Rutas de alto nivel

- `/` es un dispatcher por rol/contexto, no el dashboard principal.
- `/admin` es el dashboard de backoffice.
- `/portal/*` agrupa el portal cliente.
- `/api/v1/*` expone endpoints REST.

### Familias de rutas activas

Backoffice:
- `/admin`
- `/empresas`
- `/contratos`
- `/pagos`
- `/entregables`
- `/entregables/[entregable_id]`
- `/wip/requisiciones`
- `/empleados`
- `/plazas`
- `/historial-laboral`
- `/sedes`
- `/tipos-servicio`
- `/categorias-puesto`
- `/simulador`
- `/configuracion`
- `/mi-perfil`
- `/cotizador`
- `/cotizador/[cotizacion_id]`
- `/nominas`
- `/nominas/preparacion`
- `/nominas/calculo`
- `/nominas/empleado-detalle`
- `/nominas/dashboard`
- `/nominas/conciliacion`
- `/admin/usuarios`
- `/admin/onboarding`
- `/admin/instituciones`
- `/login`

Portal:
- `/portal`
- `/portal/mis-datos`
- `/portal/mi-perfil`
- `/portal/mi-empresa`
- `/portal/configuracion-empresa`
- `/portal/usuarios`
- `/portal/empleados`
- `/portal/alta-masiva`
- `/portal/onboarding`
- `/portal/expedientes`
- `/portal/bajas`
- `/portal/nominas`
- `/portal/nominas/preparacion`
- `/portal/nominas/calculo`
- `/portal/nominas/empleado-detalle`
- `/portal/nominas/dashboard`
- `/portal/nominas/conciliacion`
- `/portal/contratos`
- `/portal/asistencias`
- `/portal/entregables`

API v1 actualmente registrada:
- `empresas`
- `curp`
- `onboarding`

## Mapa de carpetas

```text
app/
├── api/                    # FastAPI, middleware y routers versionados
├── core/                   # Config, enums, exceptions, validation, catalogs, calculations, constants, utils
├── database/               # DatabaseManager y clientes Supabase
├── entities/               # Modelos de dominio y DTOs Pydantic
├── presentation/           # Backoffice Reflex: pages, components, layout, theme
├── repositories/           # Repositories Supabase para modulos que ya usan esa capa
├── services/               # Logica de aplicacion, orquestacion y acceso a datos
└── tests/                  # Tests del paquete app
```

### Entidades relevantes del dominio actual

`app/entities/` ya no solo cubre empresas y contratos. Tambien contiene modelos de:

- usuarios y asignaciones empresa
- onboarding y documentos
- bajas
- asistencias
- nominas
- cotizador
- configuracion fiscal y dispersion
- dashboards y metricas

### Servicios

`app/services/` es la capa principal de logica de aplicacion. El repo usa una mezcla de:

- servicios singleton exportados desde `app/services/__init__.py`
- subpaquetes especializados como `app/services/users`, `app/services/asistencias` y `app/services/dispersion`
- servicios que consumen repositories
- servicios que hablan directo con `db_manager` cuando el modulo todavia no tiene repository propio

No asumir que todos los modulos siguen exactamente el mismo patron. Primero revisar el modulo vecino y extender su estilo actual.

### Repositories

`app/repositories/` existe para modulos con consultas mas complejas o acceso encapsulado a Supabase. Tambien hay helpers compartidos en `app/repositories/shared/query_helpers.py`.

Hoy existen repositories concretos para:

- empresa
- empleado
- contrato
- plaza
- requisicion
- archivo
- categoria_puesto
- contrato_categoria
- tipo_servicio
- pago
- historial_laboral
- entregable

## Flujo de dependencias

El flujo dominante es:

`presentation/state -> services -> repositories -> database`

Pero el repo tambien permite:

`presentation/state -> services -> database`

Reglas practicas:

- UI y componentes no deben consultar Supabase directamente.
- `State` debe concentrar loading, toasts, modales y coordinacion de UI.
- Reglas de negocio y orquestacion deben vivir en `services/`.
- `repositories/` solo deben encapsular acceso a datos.
- `entities/` deben mantenerse libres de dependencias de Reflex.
- `core/` es compartido entre capas.

## Jerarquia real de estados

Base compartida:

`rx.State -> BaseState -> AuthState`

Especializaciones activas:

- `PortalState(AuthState)` para portal cliente
- `NominaBaseState(AuthState)` para rutas de nomina en backoffice y portal

Composicion frecuente:

- `CRUDStateMixin` se combina con `BaseState` o `AuthState` segun el modulo
- algunos componentes chicos usan `rx.State` directo si son widgets aislados

No asumir que todo modulo protegido hereda solo de `AuthState`; revisar si ya existe una base intermedia del feature.

## Auth y seguridad

- `AuthState` centraliza sesion, usuario actual, empresa activa, permisos y redirecciones.
- `PortalState` agrega validacion de contexto cliente y señales de empresa/portal.
- `DatabaseManager.get_client()` usa `SUPABASE_SERVICE_KEY` si existe, por lo que puede bypassear RLS.
- `DatabaseManager.get_anon_client()` se usa para auth y flujos que deben respetar contexto anon/user.
- No confiar en RLS como unica proteccion cuando el backend corre con `service_role`; reforzar permisos en `services` y `state`.
- `SKIP_AUTH=True` desactiva autenticacion para desarrollo.

## Configuracion

Variables relevantes en `.env`:

```bash
SUPABASE_URL=...
SUPABASE_KEY=...
SUPABASE_SERVICE_KEY=...
APP_NAME="Sistema de Administración de Personal"
APP_VERSION="0.7.0"
DEBUG=FALSE
SKIP_AUTH=FALSE
API_AUTH_ENABLED=FALSE
API_CORS_ORIGINS=*
```

## Reflex y UI

Configuracion actual de Reflex:

- `rxconfig.py` habilita `SitemapPlugin`
- `rxconfig.py` habilita `TailwindV4Plugin`
- la app usa fuente `Source Sans Pro`
- el tema global vive en `app/presentation/theme/`

Reglas de implementacion:

- usar `rx.cond(...)` para render condicional con `rx.Var`
- usar `rx.foreach(...)` para iteracion reactiva
- mantener setters explicitos en `State`
- mantener `@rx.var` puro y barato
- no meter logica de negocio pesada dentro del render

## Patrones de organizacion de paginas

Conviven dos estilos en el repo:

Patron legacy:

```text
modulo/
├── modulo_page.py
├── modulo_state.py
├── modulo_modals.py
└── modulo_validators.py
```

Patron modular:

```text
modulo/
├── page.py
├── state.py
├── components.py
├── modal.py
└── __init__.py
```

Criterio:

- para codigo nuevo, preferir el patron modular
- si el modulo vecino usa el patron legacy y el cambio es pequeno, preservar consistencia local
- no mezclar layout, servicios y acceso a datos dentro de componentes visuales

## Validacion

La validacion esta duplicada a proposito en dos capas:

1. validadores de formulario para UX en `presentation/pages/.../*validators.py`
2. validadores de modelos en `entities/` y helpers en `app/core/validation/`

Reusar `FieldConfig`, `pydantic_field`, catalogos y helpers existentes antes de crear validadores ad hoc.

## UI reusable

Los componentes compartidos viven principalmente en:

- `app/presentation/components/ui`
- `app/presentation/components/shared`
- `app/presentation/components/common`

Ademas existen componentes por dominio en carpetas como:

- `empresas`
- `contratos`
- `entregables`
- `requisiciones`
- `plazas`
- `sedes`
- `categorias_puesto`
- `tipo_servicio`

## API

La capa API no replica todo el dominio del dashboard. Hoy es una superficie acotada.

Reglas:

- usar `app/api/main.py` como entrada FastAPI
- registrar routers v1 en `app/api/v1/router.py`
- mantener contratos HTTP en `schemas.py` del modulo correspondiente
- no asumir que si existe una pantalla tambien existe su endpoint REST

## Migrations

- Las migraciones SQL viven en `migrations/`.
- Se aplican manualmente en Supabase.
- La numeracion historica no debe asumirse perfecta; el arbol actual llega a `046`.
- Antes de crear una nueva migracion, revisar el directorio real y seguir la convencion existente.

## Guia para cambios nuevos

Si agregas o extiendes una feature:

1. ubica la ruta y el wrapper en `app/app.py`
2. identifica si el modulo pertenece a backoffice, portal o API
3. reusa la base de estado correcta (`BaseState`, `AuthState`, `PortalState`, `NominaBaseState`)
4. coloca logica de negocio en `services/`
5. crea repository solo si el modulo ya usa esa capa o realmente necesita encapsular queries complejas
6. reusa validadores, helpers y componentes compartidos antes de duplicar
7. registra exports solo donde el repo ya centraliza imports (`entities/__init__.py`, `services/__init__.py`, etc.)

## Imports utiles

```python
from app.entities import Empresa, Empleado, Contrato
from app.services import empresa_service, empleado_service, contrato_service
from app.presentation.components.shared.base_state import BaseState
from app.presentation.components.shared.auth_state import AuthState
from app.presentation.portal.state.portal_state import PortalState
from app.presentation.pages.nominas.base_state import NominaBaseState
from app.presentation.components.shared.crud_state_mixin import CRUDStateMixin
from app.database.connection import db_manager
```

## Nota final

Este archivo debe mantenerse como guia de arquitectura viva, no como inventario exhaustivo de todos los archivos. Si el repo cambia, actualizar primero las reglas, bases compartidas y fuentes de verdad, y solo despues los ejemplos.
