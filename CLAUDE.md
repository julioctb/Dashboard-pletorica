# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Dashboard application built with **Reflex (v0.8.21)** for managing dependency contracts in Mexico (empresas, empleados, contratos, plazas, requisiciones, entregables, etc.). Uses **Supabase** as backend (PostgreSQL + Storage + Auth). Three-app architecture: Admin Dashboard, Client Portal, and REST API.

**Author**: Julio C Tello (julioc.tello@me.com)
**Status**: Production
**Database**: Supabase PostgreSQL (hosted) with Row Level Security (RLS)
**Storage**: Supabase Storage (bucket: `archivos`)
**Auth**: Supabase Auth (JWT tokens)
**Migrations**: Manual SQL scripts in `migrations/` (40 migrations)

## Development Commands

```bash
# Install dependencies
poetry install

# Run the Reflex development server
poetry run reflex run

# Initialize/update Reflex (if needed)
poetry run reflex init

# Tests
pytest                     # All tests
pytest tests/empresas      # Specific module
pytest -v                  # Verbose

# Code quality
poetry run black app/      # Format
poetry run isort app/      # Sort imports
poetry run flake8 app/     # Lint
poetry run mypy app/       # Type checking
```

## Architecture

### Three-App System

The project serves three distinct applications:

1. **Admin Dashboard** (`/` routes) - Internal staff management
2. **Client Portal** (`/portal/*` routes) - External client self-service
3. **REST API** (`/api/v1/*` routes) - Programmatic access (FastAPI)

### Layered Architecture

```
app/
├── api/                          # REST API (FastAPI)
│   ├── main.py                  # FastAPI app (api_transformer)
│   ├── config.py                # API config (CORS, title, version)
│   ├── middleware/auth.py       # JWT auth middleware
│   └── v1/                      # Versioned endpoints
│       ├── router.py            # Main v1 router
│       ├── schemas.py           # APIResponse, APIListResponse
│       └── empresas/            # Module endpoints + schemas
│
├── core/                         # Cross-cutting concerns
│   ├── config/                  # Environment configuration
│   ├── enums.py                 # All enums (Estatus, TipoEmpresa, RolUsuario, RolPlataforma, RolEmpresa, etc.)
│   ├── exceptions.py            # ApplicationError hierarchy
│   ├── text_utils.py            # capitalizar, formatear_telefono, etc.
│   ├── ui_helpers.py            # opciones_desde_enum, FILTRO_TODOS, paginacion
│   ├── ui_options.py            # Centralized dropdown options
│   ├── error_messages.py        # Centralized error messages
│   ├── validation/              # FieldConfig, constants, pydantic_field, campo_validador
│   ├── calculations/            # IMSS, ISR, payroll calculations
│   ├── catalogs/                # fiscal/, laboral/, sistema/ catalogs
│   └── compresores/             # Image (WebP) and PDF compression
│
├── entities/                     # Domain models (Pydantic)
│   ├── empresa.py               # Empresa, EmpresaCreate, EmpresaUpdate, EmpresaResumen
│   ├── user_profile.py          # UserProfile, UserProfileCreate, UserProfileUpdate
│   ├── user_company.py          # UserCompany, UserCompanyCreate
│   ├── empleado.py              # Empleado, EmpleadoCreate, EmpleadoUpdate
│   ├── contrato.py              # Contrato, ContratoCreate, ContratoUpdate, ContratoResumen
│   ├── contrato_item.py         # ContratoItem, ContratoItemCreate
│   ├── contrato_categoria.py    # ContratoCategoria, ContratoCategoriaResumen
│   ├── plaza.py                 # Plaza, PlazaCreate, PlazaUpdate, PlazaResumen
│   ├── requisicion.py           # Requisicion, RequisicionItem, ConfiguracionRequisicion
│   ├── archivo.py               # ArchivoSistema, ArchivoUploadResponse
│   ├── categoria_puesto.py      # CategoriaPuesto
│   ├── historial_laboral.py     # HistorialLaboral, HistorialLaboralResumen
│   ├── pago.py                  # Pago, PagoCreate, PagoResumen
│   ├── tipo_servicio.py         # TipoServicio
│   ├── sede.py                  # Sede, SedeCreate, SedeUpdate, SedeResumen
│   ├── contacto_buap.py         # ContactoBuap, ContactoBuapCreate
│   ├── entregable.py            # Entregable, ContratoTipoEntregable, AlertaEntregables
│   ├── notificacion.py          # Notificacion, NotificacionCreate
│   ├── dashboard.py             # DashboardMetricas (value object, not persisted)
│   ├── alta_masiva.py           # ResultadoValidacion, ResultadoProcesamiento
│   ├── empleado_restriccion_log.py  # EmpleadoRestriccionLog (audit, immutable)
│   ├── costo_patronal.py        # ConfiguracionEmpresa, Trabajador, ResultadoCuotas
│   ├── institucion.py           # Institucion, InstitucionCreate, InstitucionUpdate, InstitucionResumen
│   ├── empleado_documento.py    # EmpleadoDocumento, EmpleadoDocumentoCreate
│   ├── cuenta_bancaria_historial.py # CuentaBancariaHistorial, CuentaBancariaHistorialCreate
│   ├── configuracion_operativa_empresa.py # ConfiguracionOperativaEmpresa CRUD models
│   ├── curp_validacion.py       # CurpValidacionResponse, CurpRenapoResponse
│   └── onboarding.py            # AltaEmpleadoBuap, CompletarDatosEmpleado, ExpedienteStatus
│
├── repositories/                 # Data access layer (Supabase)
│   ├── base_repository.py       # BaseRepository[T] - generic CRUD, search, pagination
│   ├── empresa_repository.py    # SupabaseEmpresaRepository
│   ├── empleado_repository.py   # SupabaseEmpleadoRepository
│   ├── contrato_repository.py   # SupabaseContratoRepository
│   ├── plaza_repository.py      # SupabasePlazaRepository
│   ├── requisicion_repository.py # SupabaseRequisicionRepository
│   ├── archivo_repository.py    # SupabaseArchivoRepository (Storage + DB)
│   ├── categoria_puesto_repository.py
│   ├── contrato_categoria_repository.py
│   ├── tipo_servicio_repository.py
│   ├── pago_repository.py
│   ├── historial_laboral_repository.py
│   └── entregable_repository.py # SupabaseEntregableRepository
│
├── services/                     # Business logic (singletons)
│   ├── empresa_service.py       # empresa_service
│   ├── empleado_service.py      # empleado_service
│   ├── contrato_service.py      # contrato_service
│   ├── plaza_service.py         # plaza_service
│   ├── requisicion_service.py   # requisicion_service
│   ├── requisicion_pdf_service.py # PDF generation (fpdf2)
│   ├── archivo_service.py       # archivo_service (upload + compression)
│   ├── categoria_puesto_service.py # categoria_puesto_service
│   ├── contrato_categoria_service.py # contrato_categoria_service
│   ├── tipo_servicio_service.py # tipo_servicio_service
│   ├── pago_service.py          # pago_service
│   ├── historial_laboral_service.py # historial_laboral_service
│   ├── sede_service.py          # sede_service (direct access)
│   ├── contacto_buap_service.py # contacto_buap_service (direct access)
│   ├── entregable_service.py    # entregable_service
│   ├── dashboard_service.py     # dashboard_service (direct access)
│   ├── notificacion_service.py  # notificacion_service (direct access)
│   ├── user_service.py          # user_service (auth, profiles, permissions)
│   ├── alta_masiva_service.py   # alta_masiva_service (bulk import orchestrator)
│   ├── alta_masiva_parser.py    # alta_masiva_parser (Excel/CSV parsing)
│   ├── reporte_alta_masiva_service.py # Excel report generation
│   ├── plantilla_service.py     # plantilla_service (templates)
│   ├── institucion_service.py   # institucion_service (direct access)
│   ├── onboarding_service.py    # onboarding_service (alta BUAP + expediente)
│   ├── curp_service.py          # curp_service (CURP validation via RENAPO)
│   ├── empleado_documento_service.py # empleado_documento_service
│   ├── cuenta_bancaria_historial_service.py # cuenta_bancaria_historial_service
│   └── configuracion_operativa_service.py # configuracion_operativa_service
│
├── database/
│   └── connection.py             # DatabaseManager singleton (db_manager)
│
├── presentation/                 # UI Layer (Reflex)
│   ├── pages/                   # Admin pages
│   │   ├── dashboard/
│   │   ├── empresas/
│   │   ├── empleados/
│   │   ├── contratos/
│   │   ├── plazas/
│   │   ├── requisiciones/
│   │   ├── entregables/
│   │   ├── pagos/
│   │   ├── sedes/
│   │   ├── tipo_servicio/
│   │   ├── categorias_puesto/
│   │   ├── historial_laboral/
│   │   ├── configuracion/
│   │   ├── simulador/
│   │   ├── login/
│   │   ├── admin/usuarios/      # User management
│   │   ├── admin_onboarding/    # Admin onboarding management
│   │   └── instituciones/       # Instituciones CRUD + empresas
│   │
│   ├── portal/                  # Client Portal (separate subsystem)
│   │   ├── layout/              # portal_layout.py, portal_sidebar.py
│   │   ├── state/portal_state.py
│   │   └── pages/
│   │       ├── portal_dashboard.py
│   │       ├── mi_empresa.py
│   │       ├── mis_empleados/   # Modularized (page, state, modal, components)
│   │       ├── mis_contratos.py
│   │       ├── alta_masiva/     # 3-step wizard (paso_1, paso_2, paso_3)
│   │       ├── mis_entregables.py
│   │       ├── mis_datos.py     # Autoservicio empleado
│   │       ├── expedientes.py   # Expedientes digitales
│   │       ├── onboarding_alta.py # Alta empleado BUAP
│   │       └── configuracion_empresa.py # Config operativa empresa
│   │
│   ├── components/
│   │   ├── ui/                  # Reusable UI component library
│   │   ├── common/              # Shared file uploader, etc.
│   │   ├── shared/              # BaseState, AuthState
│   │   ├── empresas/
│   │   ├── plazas/
│   │   ├── requisiciones/
│   │   ├── sedes/
│   │   ├── categorias_puesto/
│   │   └── tipo_servicio/
│   │
│   ├── layout/                  # Admin layout (sidebar_layout.py)
│   └── theme/                   # Colors, Spacing, Typography tokens
│
└── app.py                        # Entry point, routes, api_transformer
```

### Dependency Flow

```
Presentation (State) → Service → Repository → Database (Supabase)
                          ↓           ↓
                      Entities    Entities
                          ↓
                        Core (exceptions, enums, validation)
```

**Rules:**
- Presentation ONLY imports Services and Entities (never Database or Repositories)
- Services import Repositories OR Database directly (depending on pattern)
- Repositories ONLY import Database and Entities
- Entities are pure (Pydantic + Python stdlib only)
- Core is shared across all layers

## Authentication & Authorization

### State Hierarchy

```
rx.State (Reflex)
    └── BaseState (loading, saving, filters, error handling)
            └── AuthState (session, tokens, user, empresas, permissions)
                    └── YourModuleState (business logic)
```

### AuthState (`app/presentation/components/shared/auth_state.py`)

Provides:
- **Session management**: JWT tokens (`_access_token`, `_refresh_token`)
- **User info**: `usuario_actual` (dict), `esta_autenticado` (bool)
- **Permissions**: `es_admin` (bool), role-based checks
- **Multi-empresa**: `empresas_disponibles`, `empresa_actual`
- **Auth guard**: `requiere_login`, `verificar_y_redirigir`

```python
# Protected module state
from app.presentation.components.shared.auth_state import AuthState

class MiModuloState(AuthState):
    # Access: self.usuario_actual, self.esta_autenticado, self.es_admin
    async def cargar_datos(self):
        if not self.esta_autenticado:
            return
        # ...
```

### BaseState (`app/presentation/components/shared/base_state.py`)

Provides common functionality for all states:
- `loading: bool`, `saving: bool` - Loading/saving indicators
- `filtro_busqueda: str` - Common search filter
- `mostrar_mensaje(msg, tipo)` - Info/error messages
- `manejar_error(error, contexto)` - Centralized error handling (catches `DuplicateError`, `NotFoundError`, etc.)
- `_modulos_montados` - Track mounted modules

### SKIP_AUTH Mode

Set `SKIP_AUTH=True` in `.env` to bypass authentication during development.

## Repository Pattern

**All modules use the Repository pattern** (`app/repositories/__init__.py`). Complex modules have dedicated repositories; simpler/newer modules use direct DB access from their services.

### BaseRepository (`app/repositories/base_repository.py`)

Generic base class `BaseRepository[T]` provides:
- **CRUD**: `obtener_por_id`, `obtener_todos`, `crear`, `actualizar`, `eliminar`
- **Search**: `buscar_por_texto(texto, campos, limite)`
- **Pagination**: `_aplicar_paginacion(query, limite, offset)`
- **Error handling**: `_ejecutar_query()` wraps all operations with proper exception raising
- **Override hooks**: `_query_por_id`, `_query_todos`, `_insertar`, `_delete` for customization

### Data Access Patterns

| Pattern | When | Modules |
|---------|------|---------|
| **Repository** (BaseRepository subclass) | Complex queries, JOINs, aggregations | empresa, empleado, contrato, plaza, requisicion, entregable, archivo, tipo_servicio, categoria_puesto, contrato_categoria, pago, historial_laboral |
| **Direct Access** (db_manager in service) | Simple CRUD, new modules | sede, contacto_buap, dashboard, notificacion, user, plantilla |

### When to create a Repository

Create a repository when the module needs: multi-table JOINs, aggregations (COUNT/SUM), complex filtering, or >3 query methods. Otherwise, use direct access from the service.

## Services

All services are **singletons** instantiated at module level:

```python
from app.services import empresa_service, empleado_service

empresas = await empresa_service.obtener_todas()
```

### Service with Repository
```python
class EmpresaService:
    def __init__(self):
        self.repository = SupabaseEmpresaRepository()

    async def obtener_por_id(self, id: int) -> Empresa:
        return await self.repository.obtener_por_id(id)
```

### Service with Direct Access
```python
class SedeService:
    def __init__(self):
        self.supabase = db_manager.get_client()
        self.tabla = 'sedes'

    async def obtener_por_id(self, id: int) -> Sede:
        result = self.supabase.table(self.tabla).select('*').eq('id', id).execute()
        if not result.data:
            raise NotFoundError(f"Sede con ID {id} no encontrada")
        return Sede(**result.data[0])
```

## Database Connection

```python
from app.database import db_manager

supabase = db_manager.get_client()        # Service role key (bypasses RLS)
anon = db_manager.get_anon_client()       # Anon key (for user auth operations)
connected = db_manager.test_connection()  # Test connectivity
```

**Two clients**: The `DatabaseManager` maintains two Supabase clients:
- **Service role** (`get_client()`): Bypasses RLS, used by repositories/services
- **Anon** (`get_anon_client()`): Respects RLS, used by `user_service` for auth

## Supabase Query Patterns

```python
# SELECT with JOIN
result = self.supabase.table('empleados')\
    .select('*, empresas(nombre_comercial, rfc)')\
    .eq('empresa_id', 1).execute()

# INSERT (use mode='json' for dates)
datos = entity.model_dump(mode='json', exclude={'id', 'fecha_creacion'})
result = self.supabase.table('empleados').insert(datos).execute()

# UPDATE
result = self.supabase.table('empleados')\
    .update({'estatus': 'INACTIVO'}).eq('id', 1).execute()

# SEARCH (case-insensitive, requires LOWER() index)
.or_(f"nombre.ilike.%{texto}%,apellido.ilike.%{texto}%")

# PAGINATION
.order('fecha_creacion', desc=True).range(offset, offset + limite - 1)

# COUNT
result = self.supabase.table('empleados')\
    .select('id', count='exact').eq('estatus', 'ACTIVO').execute()
total = result.count
```

**Important**: Always use `model_dump(mode='json')` for Supabase to serialize dates as ISO strings.

## UI Component Library

All reusable components in `app/presentation/components/ui/`:

```python
from app.presentation.components.ui import (
    # Forms
    form_input, form_select, form_textarea, form_date, form_row,
    # Tables
    tabla, tabla_vacia, skeleton_tabla,
    # Modals
    modal_formulario, modal_confirmar_eliminar, modal_confirmar_accion, modal_detalle,
    # Buttons
    boton_guardar, boton_cancelar, boton_eliminar, botones_modal,
    # Filters
    input_busqueda, indicador_filtros, contador_registros, switch_inactivos, barra_filtros,
    # Badges
    status_badge, status_badge_reactive, estatus_badge,
    # Cards & Layout
    entity_card, entity_grid, metric_card, page_header,
    view_toggle, breadcrumb_dynamic,
    # Actions
    action_buttons, action_button_config, action_buttons_reactive,
    # Notifications
    notification_bell, notification_bell_portal, NotificationBellState,
)
```

### Form Input Pattern

```python
form_input(
    label="Nombre comercial",
    required=True,
    placeholder="Ej: ACME Corporation",
    hint="Se formatea automaticamente",
    value=State.form_nombre,
    on_change=State.set_form_nombre,
    on_blur=State.validar_nombre_campo,
    error=State.error_nombre,
    max_length=100,
)
```

**Important**: `form_input` cannot be used inside `rx.foreach` because its Python-level `if` checks fail with Vars. For dynamic fields in `rx.foreach`, use inline `rx.cond` pattern instead.

## Routing

### Admin Routes (wrapped in `index()` layout)

| Route | Page | Module |
|-------|------|--------|
| `/` | Dashboard | dashboard |
| `/empresas` | Empresas | empresas |
| `/contratos` | Contratos | contratos |
| `/pagos` | Pagos | pagos |
| `/plazas` | Plazas | plazas |
| `/empleados` | Empleados | empleados |
| `/historial-laboral` | Historial Laboral | historial_laboral |
| `/requisiciones` | Requisiciones | requisiciones |
| `/entregables` | Entregables | entregables |
| `/entregables/[entregable_id]` | Detalle Entregable | entregables |
| `/sedes` | Sedes | sedes |
| `/tipos-servicio` | Tipos de Servicio | tipo_servicio |
| `/categorias-puesto` | Categorias de Puesto | categorias_puesto |
| `/configuracion` | Configuracion Requisiciones | configuracion |
| `/simulador` | Simulador | simulador |
| `/admin/usuarios` | Admin Usuarios | admin/usuarios |
| `/admin/onboarding` | Admin Onboarding | admin_onboarding |
| `/admin/instituciones` | Instituciones | instituciones |
| `/login` | Login (no layout) | login |

### Portal Routes (wrapped in `portal_index()` layout)

| Route | Page |
|-------|------|
| `/portal` | Portal Dashboard |
| `/portal/mi-empresa` | Mi Empresa |
| `/portal/empleados` | Mis Empleados |
| `/portal/contratos` | Mis Contratos |
| `/portal/alta-masiva` | Alta Masiva (3-step wizard) |
| `/portal/entregables` | Mis Entregables |
| `/portal/mis-datos` | Autoservicio Mis Datos |
| `/portal/expedientes` | Expedientes Digitales |
| `/portal/onboarding` | Alta Empleado BUAP |
| `/portal/configuracion-empresa` | Configuracion Operativa |

### API Routes

| Route | Description |
|-------|-------------|
| `/api/docs` | Swagger UI |
| `/api/redoc` | ReDoc |
| `/api/openapi.json` | OpenAPI schema |
| `/api/v1/empresas/` | Empresas endpoints |

## Exception Hierarchy

```python
from app.core.exceptions import (
    ApplicationError,     # Base
    ValidationError,      # Data validation errors
    NotFoundError,        # Resource not found
    DuplicateError,       # Unique constraint violation (field, value)
    DatabaseError,        # Connection/infrastructure errors
    BusinessRuleError,    # Business logic violations
)
```

**Error flow**: Repository raises specific exceptions -> Service propagates (no try-catch) -> State catches and shows user-friendly messages via `self.manejar_error(error, contexto)`.

## Validation Strategy

Double validation (frontend + backend):

1. **Frontend validators** (`pages/{module}/{module}_validators.py`): Pure functions, run on `on_blur` and submit, instant UX feedback
2. **Pydantic validators** (`entities/{entity}.py`): `Field()` constraints + `@field_validator`, last line of defense

Both layers must have synchronized rules and error messages.

### Centralized Validation (`app/core/validation/`)

Uses `FieldConfig` + `pydantic_field()` + `campo_validador()` for DRY validation:

```python
from app.core.validation import CAMPO_NOMBRE, pydantic_field, campo_validador

class MiEntidad(BaseModel):
    nombre: str = pydantic_field(CAMPO_NOMBRE)
    validar_nombre = campo_validador('nombre', CAMPO_NOMBRE)
```

## Page Modularization Pattern

Large pages (>500 lines) are split into:

```
module/
├── module_page.py        # Main page component
├── module_state.py       # State management
├── module_modals.py      # Modal dialogs
├── module_validators.py  # Frontend validators (optional)
└── __init__.py           # Exports page function
```

## Database Migrations

**Location**: `migrations/` - Executed manually in Supabase Dashboard SQL Editor.

| # | Migration | Description |
|---|-----------|-------------|
| 000 | create_empresas | Empresas table + ENUMs |
| 001 | create_tipos_servicio | Service types catalog |
| 002 | create_categorias_puesto | Job categories |
| 003 | create_contratos | Contracts table |
| 004 | create_pagos | Payments table |
| 005 | create_contrato_categorias | Contract-category pricing |
| 006 | create_plazas_table | Job positions |
| 007 | create_empleados_table | Employees |
| 008 | create_historial_laboral_table | Employment history |
| 009 | create_requisiciones | Requisitions + items |
| 010 | create_lugares_entrega | Delivery locations |
| 011 | permitir_borradores_requisicion | Allow draft requisitions |
| 012 | create_archivo_sistema | Generic file storage |
| 013 | add_search_indices | Performance indices |
| 014 | create_sedes_tables | Locations (sedes + contactos) |
| 015 | create_user_auth_tables | User profiles, companies, roles |
| 016 | apply_rls_business_tables | Row Level Security for all tables |
| 017 | add_employee_restrictions | Employee restriction logs |
| 018 | add_reingreso_historial | Reentry support for historial |
| 019 | create_entregables_tables | Deliverables system |
| 020 | alter_pagos_archivo_sistema | Pagos + archivo alterations |
| 021 | apply_rls_entregables | RLS for entregables |
| 022 | add_facturacion_estados | Billing states |
| 023 | create_notificaciones | Notifications system |
| 024 | add_requisicion_audit_fields | Audit fields for requisiciones |
| 025 | add_requisicion_id_to_contratos | Link contratos to requisiciones |
| 026 | create_contrato_items | Contract line items |
| 027 | add_partida_presupuestal_to_items | Budget line fields |
| 028 | add_inicio_desde_firma_to_requisiciones | Start-from-signature flag |
| 029 | add_transferencia_bancaria_to_requisiciones | Bank transfer fields |
| 030 | move_partida_fields_to_requisicion | Move budget fields |
| 031 | ampliar_campos_requisicion | Expand requisicion fields |
| 032 | numero_requisicion_nullable | Nullable requisicion number |
| 033 | permisos_granulares | Granular permissions system |
| 034 | add_rol_empresa_to_user_companies | RolEmpresa enum + column |
| 035 | extend_empleados_onboarding | Onboarding fields for empleados |
| 036 | create_empleado_documentos | Employee document management |
| 037 | create_cuenta_bancaria_historial | Bank account change history |
| 038 | create_configuracion_operativa_empresa | Company operational config |
| 039 | pivot_saas_roles | SaaS role pivot (RolPlataforma, RolEmpresa) |

### Migration Structure

All migrations are idempotent (`IF NOT EXISTS`, `DO $$`), include rollback instructions (commented), and follow this pattern:

```sql
-- 1. Create ENUMs (if needed)
-- 2. Create table
-- 3. Add comments
-- 4. Create indices (LOWER() for search, composite for filters)
-- 5. Create triggers (fecha_actualizacion)
-- Rollback section (commented)
```

## Environment Configuration

Required `.env` variables:

```bash
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
SUPABASE_SERVICE_KEY=your-service-role-key  # Recommended (bypasses RLS)
APP_NAME="Sistema de Administracion de Personal"
APP_VERSION="0.1.0"
DEBUG=FALSE
SKIP_AUTH=FALSE  # Set TRUE for development without auth
```

## Reflex-Specific Notes

- **Version**: >=0.8.21, <0.9.0
- **Config**: `rxconfig.py` with SitemapPlugin and TailwindV4Plugin
- **State setters**: Always explicit (Reflex doesn't recognize dynamically assigned handlers)
- **Conditional rendering**: `rx.cond(condition, if_true, if_false)` - always both branches
- **Iteration**: `rx.foreach(list_var, render_fn)` - never Python `for` in render
- **Boolean operators**: Use `&`, `|`, `~` with `rx.Var` (not `and`, `or`, `not`)
- **Async methods**: Automatically awaited by Reflex
- **Components**: Pure functions returning `rx.Component`
- **Theme**: Tokens in `app/presentation/theme/` (Colors, Spacing, Typography)

## Key Import Patterns

```python
# Entities
from app.entities import Empresa, EmpresaCreate, TipoEmpresa, EstatusEmpresa

# Services (singletons)
from app.services import empresa_service, empleado_service

# Auth state (for protected modules)
from app.presentation.components.shared.auth_state import AuthState

# Base state (for unprotected modules)
from app.presentation.components.shared.base_state import BaseState

# Exceptions
from app.core.exceptions import NotFoundError, DuplicateError, DatabaseError

# UI Components
from app.presentation.components.ui import (
    form_input, form_select, tabla, modal_formulario,
    boton_guardar, botones_modal, action_buttons,
)

# Theme
from app.presentation.theme import Colors, Spacing, Typography

# UI Helpers
from app.core.ui_helpers import opciones_desde_enum, FILTRO_TODOS, calcular_paginas

# Database (only in services/repositories)
from app.database import db_manager
```

## Adding a New Module

1. **Entity**: Create `app/entities/nuevo_modulo.py` (Pydantic models)
2. **Repository** (if complex queries): Create `app/repositories/nuevo_modulo_repository.py`
3. **Service**: Create `app/services/nuevo_modulo_service.py` (singleton)
4. **Page**: Create `app/presentation/pages/nuevo_modulo/` (page, state, modals)
5. **Migration**: Create `migrations/NNN_create_nuevo_modulo.sql`
6. **Register**: Add to `entities/__init__.py`, `services/__init__.py`, `repositories/__init__.py` (if applicable)
7. **Route**: Add to `app/app.py`

## Dependencies

**Runtime**: reflex, supabase, pydantic, pydantic-settings, python-dotenv, loguru, httpx, python-dateutil, openpyxl, fastapi, pillow, defusedxml, fpdf2, fpdf

**Dev**: pytest, black, isort, flake8, mypy
