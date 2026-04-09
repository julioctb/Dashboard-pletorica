# CLAUDE.md

Guia operativa para asistentes de codigo que trabajen en este repositorio.

## Fuente de verdad

Cuando exista conflicto entre este archivo y el codigo, usar en este orden:

1. `app/bootstrap/app_factory.py` para composicion de la app Reflex.
2. `app/presentation/config/routes.py` para rutas registradas.
3. `pyproject.toml` para versiones, dependencias y runtime.
4. `rxconfig.py` para configuracion de Reflex y plugins.
5. La estructura real de `app/` para decidir capas, naming y colocacion.

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

### Entry point y bootstrap

`app/app.py` llama a `create_app()` desde `app/bootstrap/`. La composicion se separa en:

- `app/bootstrap/app_factory.py` — crea `rx.App` con theme, API y rutas
- `app/bootstrap/routes_core.py` — rutas base (`/`, `/login`, share)
- `app/bootstrap/routes_backoffice.py` — rutas admin (29)
- `app/bootstrap/routes_portal.py` — rutas portal (24+)
- `app/bootstrap/reflex_patch.py` — patches para defaults de Reflex

Las rutas estan definidas en `app/presentation/config/routes.py` como tuplas (`CORE_ROUTES`, `BACKOFFICE_PAGE_ROUTES`, `PORTAL_PAGE_ROUTES`).

### Rutas de alto nivel

- `/` es un dispatcher por rol/contexto, no el dashboard principal.
- `/admin` es el dashboard de backoffice.
- `/portal/*` agrupa el portal cliente.
- `/api/v1/*` expone endpoints REST.

### Familias de rutas activas

Backoffice:

- `/admin`
- `/empresas`
- `/empresas/[empresa_documentacion_empresa_id]/documentacion`
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
- `/portal/documentacion-empresa`
- `/portal/configuracion-empresa`
- `/portal/usuarios`
- `/portal/empleados`
- `/portal/empleados/[id]`
- `/portal/alta-masiva`
- `/portal/plazas`
- `/portal/onboarding`
- `/portal/incapacidades`
- `/portal/bajas`
- `/portal/nominas`
- `/portal/nominas/preparacion`
- `/portal/nominas/calculo`
- `/portal/nominas/empleado-detalle`
- `/portal/nominas/dashboard`
- `/portal/nominas/conciliacion`
- `/portal/contratos`
- `/portal/contratos/[id]/plazas`
- `/portal/simulador`
- `/portal/cotizador`
- `/portal/cotizador/[cotizacion_id]`
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
├── bootstrap/              # Factory de app Reflex + registro de rutas
├── core/                   # Config, enums, exceptions, validation, catalogs, calculations, constants, utils
├── database/               # DatabaseManager y clientes Supabase
├── domain/                 # Capa legacy monolitica
│   ├── models/             # Modelos de dominio y DTOs Pydantic
│   ├── enums/              # Enums del dominio
│   ├── services/           # Logica de aplicacion, orquestacion y acceso a datos
│   └── repositories/       # Repositories Supabase
│       └── shared/         # query_helpers.py
├── infrastructure/         # Auth, database adapters, external, storage
├── modules/                # Modulos DDD (fachadas sobre domain/)
│   ├── application/        # Bridge: re-exporta servicios legacy
│   ├── cotizaciones/       # domain/ application/ infrastructure/ ui/
│   ├── empleados/          # domain/ application/ infrastructure/ ui/
│   └── nomina/             # domain/ application/ infrastructure/ ui/
├── presentation/           # Reflex UI: pages, components, layout, theme
│   ├── components/         # Compartidos: ui/, shared/, common/, backoffice/
│   ├── config/             # routes.py, app_config.py
│   ├── layouts/            # backoffice/, portal/
│   ├── pages/
│   │   ├── backoffice/     # Paginas admin (20+ features)
│   │   └── portal/         # Paginas portal cliente (15+ features)
│   └── theme/              # Tema global
├── shared/                 # Exceptions, formatting, pagination, validation utils
└── tests/                  # Tests del paquete app
```

### Dos patrones de dominio coexisten

#### Legacy (`app/domain/`)

Estructura plana: `models/`, `services/`, `repositories/` — todo junto, sin separacion por feature. Esta es la capa donde vive la logica real hoy.

#### Modular DDD (`app/modules/`)

Cada modulo sigue la estructura:

```text
modules/{feature}/
├── domain/          # Re-exporta models, enums, validators desde app.domain
├── application/     # Re-exporta y organiza servicios (queries, mutations)
├── infrastructure/  # Repositories propios (solo empleados tiene implementacion real)
└── ui/
    ├── backoffice/  # Exports de paginas y estados para admin
    └── portal/      # Exports de paginas y estados para portal
```

Los modulos son **fachadas** sobre `app/domain/`. La logica real sigue en el monolito; los modulos proveen una API publica organizada por feature y separacion de superficies UI.

Modulos activos: `cotizaciones`, `empleados`, `nomina`.

`modules/application/` es un bridge temporal que re-exporta servicios legacy de `app.domain.services`.

### Modelos del dominio

`app/domain/models/` contiene modelos Pydantic para:

- empresas, contratos, empleados, plazas
- usuarios y asignaciones empresa
- onboarding y documentos
- bajas, incapacidades
- asistencias
- nominas (periodos, movimientos, conceptos)
- cotizador (cotizaciones, partidas, items)
- configuracion fiscal y dispersion
- dashboards y metricas
- historial laboral

### Servicios

`app/domain/services/` es la capa principal de logica de aplicacion. El repo usa una mezcla de:

- servicios singleton exportados desde `app/domain/services/__init__.py`
- subpaquetes especializados como `app/domain/services/users`, `app/domain/services/asistencias` y `app/domain/services/dispersion`
- servicios que consumen repositories
- servicios que hablan directo con `db_manager` cuando el modulo todavia no tiene repository propio

No asumir que todos los modulos siguen exactamente el mismo patron. Primero revisar el modulo vecino y extender su estilo actual.

### Repositories

`app/domain/repositories/` existe para modulos con consultas mas complejas o acceso encapsulado a Supabase. Tambien hay helpers compartidos en `app/domain/repositories/shared/query_helpers.py`.

Hoy existen repositories concretos para:

- empresa
- empleado
- contrato
- plaza
- requisicion
- archivo
- pago
- historial_laboral
- entregable
- incapacidad

## Flujo de dependencias

El flujo dominante es:

`presentation/state -> domain/services -> domain/repositories -> database`

Pero el repo tambien permite:

`presentation/state -> domain/services -> database`

Y con los modulos DDD:

`presentation/state -> modules/*/application -> domain/services -> domain/repositories -> database`

Reglas practicas:

- UI y componentes no deben consultar Supabase directamente.
- `State` debe concentrar loading, toasts, modales y coordinacion de UI.
- Reglas de negocio y orquestacion deben vivir en `domain/services/`.
- `domain/repositories/` solo deben encapsular acceso a datos.
- Modelos en `domain/models/` deben mantenerse libres de dependencias de Reflex.
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
APP_VERSION="0.8.1"
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
2. validadores de dominio en `app/domain/` y helpers en `app/core/validation/`

Reusar `FieldConfig`, `pydantic_field`, catalogos y helpers existentes antes de crear validadores ad hoc.

## UI reusable

Los componentes compartidos viven principalmente en:

- `app/presentation/components/ui`
- `app/presentation/components/shared`
- `app/presentation/components/common`

Ademas existen componentes por dominio en `app/presentation/components/backoffice/`:

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
- La numeracion historica no debe asumirse perfecta; el arbol actual llega a `061`.
- Antes de crear una nueva migracion, revisar el directorio real y seguir la convencion existente.

## Guia para cambios nuevos

Si agregas o extiendes una feature:

1. ubica la ruta en `app/presentation/config/routes.py` y el registro en `app/bootstrap/`
2. identifica si el modulo pertenece a backoffice, portal o API
3. reusa la base de estado correcta (`BaseState`, `AuthState`, `PortalState`, `NominaBaseState`)
4. coloca logica de negocio en `domain/services/`
5. crea repository solo si el modulo ya usa esa capa o realmente necesita encapsular queries complejas
6. si el modulo tiene fachada en `modules/`, registra exports ahi tambien
7. reusa validadores, helpers y componentes compartidos antes de duplicar
8. registra exports solo donde el repo ya centraliza imports (`domain/models/__init__.py`, `domain/services/__init__.py`, etc.)

## Imports utiles

```python
from app.domain.models import Empresa, Empleado, Contrato
from app.domain.services import empresa_service, empleado_service, contrato_service
from app.presentation.components.shared.base_state import BaseState
from app.presentation.components.shared.auth_state import AuthState
from app.presentation.pages.portal.state.portal_state import PortalState
from app.presentation.pages.backoffice.nominas.base_state import NominaBaseState
from app.presentation.components.shared.crud_state_mixin import CRUDStateMixin
from app.database.connection import db_manager
```

## Nota final

Este archivo debe mantenerse como guia de arquitectura viva, no como inventario exhaustivo de todos los archivos. Si el repo cambia, actualizar primero las reglas, bases compartidas y fuentes de verdad, y solo despues los ejemplos.
