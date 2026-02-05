# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Dashboard application built with Reflex (v0.8.21) for managing dependency contracts in Mexico (empresas, empleados, contratos, plazas, requisiciones, etc.). Uses Supabase as backend (DB + Storage). **Scalable layered architecture**.

**Author**: Julio C Tello (julioc.tello@me.com)
**Status**: Production - Scalable Layered Architecture

> **📌 Branch Note (SUPABASE)**
> Esta rama usa **Supabase** (PostgreSQL) como base de datos y almacenamiento de archivos.
> - **Database**: Supabase PostgreSQL (hosted)
> - **Storage**: Supabase Storage (buckets: `archivos`)
> - **Migrations**: Manual SQL scripts in `migrations/` directory
> - **Connection**: Singleton client (`app/database/connection.py`)
>
> Si esta rama se fusiona con `main`, este será el sistema de base de datos definitivo del proyecto.

## Development Commands

### Running the Application
```bash
# Install dependencies
poetry install

# Run the Reflex development server
poetry run reflex run

# Initialize/update Reflex (if needed)
poetry run reflex init
```

### Testing
```bash
# Run all tests
pytest

# Run tests for specific module
pytest tests/empresas

# Run with verbose output
pytest -v
```

### Code Quality
```bash
# Format code
poetry run black app/
poetry run isort app/

# Lint
poetry run flake8 app/

# Type checking
poetry run mypy app/
```

## Architecture

### Scalable Layered Architecture

The application follows a **simple layered architecture** optimized for **scalability and maintainability**:

```
app/
├── core/                        # Cross-cutting concerns
│   ├── config/                 # Environment configuration
│   ├── enums.py               # All enums (Estatus, TipoEmpresa, TipoEntidadArchivo, etc.)
│   ├── exceptions.py          # Custom exceptions (ApplicationError hierarchy)
│   ├── text_utils.py          # Text normalization (capitalizar, formatear_telefono, etc.)
│   ├── validation/            # FieldConfig, constants, custom validators
│   ├── calculations/          # Business calculations (IMSS, ISR, payroll)
│   ├── compresores/           # Image (WebP) and PDF compression
│   └── utils/                 # General utilities
│
├── entities/                    # Domain models (Pydantic)
│   ├── empresa.py             # Empresa, EmpresaCreate, EmpresaUpdate, EmpresaResumen
│   ├── empleado.py            # Empleado, EmpleadoCreate, EmpleadoUpdate
│   ├── contrato.py            # Contrato, ContratoCreate, ContratoUpdate
│   ├── plaza.py               # Plaza, PlazaCreate, PlazaUpdate
│   ├── requisicion.py         # Requisicion, RequisicionItem, etc.
│   ├── archivo.py             # ArchivoSistema, ArchivoSistemaCreate
│   ├── categoria_puesto.py    # CategoriaPuesto
│   ├── contrato_categoria.py  # ContratoCategoria
│   ├── historial_laboral.py   # HistorialLaboral
│   ├── pago.py                # Pago
│   ├── tipo_servicio.py       # TipoServicio
│   └── costo_patronal.py      # CostoPatronal
│
├── repositories/                # Data access layer (Supabase)
│   ├── empresa_repository.py  # IEmpresaRepository + SupabaseEmpresaRepository
│   ├── empleado_repository.py
│   ├── contrato_repository.py
│   ├── plaza_repository.py
│   ├── requisicion_repository.py
│   ├── archivo_repository.py  # Supabase Storage + DB
│   ├── categoria_puesto_repository.py
│   ├── contrato_categoria_repository.py
│   ├── historial_laboral_repository.py
│   ├── pago_repository.py
│   └── tipo_servicio_repository.py
│
├── services/                    # Business logic (singletons)
│   ├── empresa_service.py
│   ├── empleado_service.py
│   ├── contrato_service.py
│   ├── plaza_service.py
│   ├── requisicion_service.py
│   ├── archivo_service.py     # File upload + compression pipeline
│   ├── categoria_puesto_service.py
│   ├── contrato_categoria_service.py
│   ├── historial_laboral_service.py
│   ├── pago_service.py
│   └── tipo_servicio_service.py
│
├── database/                    # Infrastructure
│   └── connection.py           # Supabase singleton (db_manager)
│
├── presentation/                # UI Layer (Reflex)
│   ├── pages/
│   │   ├── empresas/
│   │   ├── empleados/
│   │   ├── contratos/
│   │   ├── plazas/
│   │   ├── requisiciones/
│   │   ├── configuracion/     # Default values for requisiciones
│   │   ├── categorias_puesto/
│   │   ├── historial_laboral/
│   │   ├── tipo_servicio/
│   │   ├── simulador/
│   │   └── dashboard.py
│   │
│   ├── components/
│   │   ├── ui/                # Reusable UI components
│   │   │   ├── form_input.py  # form_input, form_select, form_textarea, form_date, form_row
│   │   │   ├── tables.py     # tabla, tabla_vacia
│   │   │   ├── modals.py     # modal_formulario, modal_confirmar_eliminar, etc.
│   │   │   ├── filters.py    # input_busqueda, barra_filtros, etc.
│   │   │   ├── status_badge.py
│   │   │   ├── breadcrumb.py
│   │   │   ├── view_toggle.py
│   │   │   └── ...
│   │   ├── common/            # Shared file uploader, etc.
│   │   ├── empresas/
│   │   ├── plazas/
│   │   ├── requisiciones/
│   │   └── shared/            # BaseState
│   │
│   ├── layout/
│   │   ├── sidebar_layout.py
│   │   └── navbar_layout.py
│   │
│   └── theme/                 # Colors, Spacing, Typography tokens
│
└── app.py                       # Application entry point + routes
```

### Architecture Benefits

| Benefit | Description |
|---------|-------------|
| **🎯 Scalable** | Easy to add new entities/repos/services - just add a new file |
| **🔍 Easy to find** | One layer = One directory. No nested structures |
| **🚀 Simple** | No over-engineering. Straightforward for small teams |
| **🔄 Maintainable** | Related code is together (feature folders in components/) |
| **✅ Testable** | Each layer is independent and mockable |

### Dependency Flow

**Two Patterns** (see [Repository Pattern](#2-repository-pattern-two-approaches)):

**Pattern A - With Repository** (complex queries):
```
Presentation → Service → Repository → Database
                  ↓          ↓
              Entities   Entities
                  ↓
               Core
```

**Pattern B - Direct Access** (simple CRUD):
```
Presentation → Service → Database
                  ↓
              Entities
                  ↓
               Core
```

**Rules:**
- Presentation ONLY imports from Services and Entities (never Database or Repositories)
- Services import from Repositories (if exists) OR Database (direct access)
- Services ONLY import from Repositories and Entities (if using repository pattern)
- Services ONLY import from Database and Entities (if using direct access pattern)
- Repositories ONLY import from Database and Entities
- Entities are pure (no dependencies except Pydantic and Python stdlib)
- Core is shared by all layers (exceptions, enums, utils, validation)

**Dependency Examples:**

```python
# ✅ CORRECT - Presentation imports Service
from app.services import empresa_service
empresas = await empresa_service.obtener_todas()

# ❌ WRONG - Presentation imports Repository directly
from app.repositories import SupabaseEmpresaRepository
repo = SupabaseEmpresaRepository()  # NO!

# ❌ WRONG - Presentation imports Database directly
from app.database import db_manager
result = db_manager.get_client().table('empresas').select('*')  # NO!

# ✅ CORRECT - Service with Repository
class EmpleadoService:
    def __init__(self):
        self.repository = SupabaseEmpleadoRepository()

# ✅ CORRECT - Service with Direct Access
class EmpresaService:
    def __init__(self):
        self.supabase = db_manager.get_client()
```

## Key Patterns

### 1. Entities (Domain Models)

All business entities use Pydantic for validation:

```python
from app.entities import Empresa, TipoEmpresa, EstatusEmpresa

# Create entity
empresa = Empresa(
    nombre_comercial="ACME Corp",
    razon_social="ACME Corporation SA de CV",
    tipo_empresa=TipoEmpresa.NOMINA,
    rfc="ACM010101ABC",
    email="contacto@acme.com",
    estatus=EstatusEmpresa.ACTIVO
)

# Business logic methods
if empresa.puede_tener_empleados():
    ...
```

### 2. Repository Pattern: Two Approaches

**Philosophy**: Use the **simplest pattern that works**. Don't over-engineer.

The codebase uses **two data access patterns** depending on complexity:

#### **Pattern A: Repository Layer** (Complex Queries)

For modules with **complex database operations**:
- Multi-table JOINs
- Aggregations (COUNT, SUM, GROUP BY)
- Complex filtering (multi-field search, date ranges)
- Business logic in queries (availability checks, recursive queries)

**Modules using Repository**:
- `empleado` → `SupabaseEmpleadoRepository`
- `plaza` → `SupabasePlazaRepository`
- `contrato` → `SupabaseContratoRepository`
- `requisicion` → `SupabaseRequisicionRepository`

**Structure**:
```
Service → Repository → Database
```

**Example** (`empleado`):
```python
# app/repositories/empleado_repository.py
class SupabaseEmpleadoRepository:
    def __init__(self, db_manager=None):
        if db_manager is None:
            from app.database import db_manager as default_db
            db_manager = default_db
        self.supabase = db_manager.get_client()
        self.tabla = 'empleados'

    async def obtener_resumen_por_empresa(
        self,
        empresa_id: int,
        incluir_inactivos: bool = False,
        limite: int = 50,
        offset: int = 0
    ) -> List[dict]:
        """Complex query with JOIN to empresas table"""
        query = self.supabase.table(self.tabla)\
            .select('*, empresas(nombre_comercial)')\  # JOIN
            .eq('empresa_id', empresa_id)

        if not incluir_inactivos:
            query = query.eq('estatus', 'ACTIVO')

        query = query.order('apellido_paterno')\
            .range(offset, offset + limite - 1)

        result = query.execute()

        # Custom aggregation/transformation
        resumenes = []
        for data in result.data:
            empresa_nombre = data.get('empresas', {}).get('nombre_comercial')
            nombre_completo = f"{data['nombre']} {data['apellido_paterno']}"
            resumenes.append({
                'id': data['id'],
                'nombre_completo': nombre_completo,
                'empresa_nombre': empresa_nombre,
                # ...
            })
        return resumenes

# app/services/empleado_service.py
class EmpleadoService:
    def __init__(self):
        self.repository = SupabaseEmpleadoRepository()

    async def obtener_resumen_por_empresa(self, empresa_id: int):
        return await self.repository.obtener_resumen_por_empresa(empresa_id)
```

#### **Pattern B: Direct Access** (Simple CRUD)

For modules with **simple database operations**:
- Basic CRUD (Create, Read, Update, Delete)
- Single table queries
- Simple filters (status, ID lookup)
- No JOINs or aggregations

**Modules using Direct Access**:
- `empresa` → `EmpresaService` (no repository)
- `tipo_servicio` → `TipoServicioService` (no repository)
- `categoria_puesto` → `CategoriaPuestoService` (no repository)
- `pago` → `PagoService` (no repository)
- `historial_laboral` → `HistorialLaboralService` (no repository)
- `archivo` → `ArchivoService` (no repository)

**Structure**:
```
Service → Database (direct)
```

**Example** (`empresa`):
```python
# app/services/empresa_service.py
class EmpresaService:
    def __init__(self):
        """Direct connection to Supabase (no repository)"""
        self.supabase = db_manager.get_client()
        self.tabla = 'empresas'

    async def obtener_por_id(self, empresa_id: int) -> Empresa:
        """Simple query - no need for repository"""
        try:
            result = self.supabase.table(self.tabla)\
                .select('*')\
                .eq('id', empresa_id)\
                .execute()

            if not result.data:
                raise NotFoundError(f"Empresa con ID {empresa_id} no encontrada")

            return Empresa(**result.data[0])

        except NotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error obteniendo empresa {empresa_id}: {e}")
            raise DatabaseError(f"Error de base de datos: {str(e)}")

    async def crear(self, empresa_create: EmpresaCreate) -> Empresa:
        """Simple insert - no business logic in query"""
        empresa = Empresa(**empresa_create.model_dump())

        # Validate uniqueness (simple query)
        if await self._existe_rfc(empresa.rfc):
            raise DuplicateError(f"RFC {empresa.rfc} ya existe", field="rfc")

        # Insert
        datos = empresa.model_dump(mode='json', exclude={'id', 'fecha_creacion'})
        result = self.supabase.table(self.tabla).insert(datos).execute()

        return Empresa(**result.data[0])
```

#### **Decision Tree: When to Use Each Pattern**

```
Is your module doing any of the following?
├─ Multi-table JOINs (2+ tables)? ────────────────────────────┐
├─ Aggregations (COUNT, SUM, GROUP BY, HAVING)? ──────────────┤
├─ Complex filtering (multi-field OR, date ranges, ILIKE)? ───┤
├─ Custom data transformations after query? ──────────────────┤
├─ Business logic embedded in queries? ───────────────────────┤
├─ Recursive queries or CTEs? ────────────────────────────────┤
└─ Query logic changes frequently? ───────────────────────────┤
                                                              │
                                                              ├─ YES → Use Repository
                                                              │
                                                              └─ NO  → Use Direct Access
```

#### **Comparison Table**

| Aspect | Repository Pattern | Direct Access |
|--------|-------------------|---------------|
| **Complexity** | Medium (extra layer) | Low (one less file) |
| **Testability** | High (mock repository) | Medium (mock db_manager) |
| **Maintainability** | High (logic centralized) | Medium (logic in service) |
| **Performance** | Same (no overhead) | Same |
| **When to Use** | Complex queries, JOINs, aggregations | Simple CRUD, single table |
| **Example Modules** | Empleado, Plaza, Contrato, Requisicion | Empresa, TipoServicio, CategoriaPuesto, Pago |

#### **Refactoring Guidelines**

**When to extract a Repository** (from Direct Access):

1. You add a JOIN to another table
2. You need aggregations (COUNT users per empresa)
3. You have >3 query methods with similar filters
4. Query logic is duplicated in multiple services
5. Testing becomes difficult without mocking queries

**When to collapse a Repository** (to Direct Access):

1. Repository only has basic CRUD (no complex queries)
2. All queries are single-table
3. No JOINs or aggregations
4. Repository is just a thin wrapper with no value

#### **File Structure for New Modules**

**Option A: With Repository** (complex)
```
app/
├── entities/
│   └── nuevo_modulo.py          # Entity, Create, Update models
├── repositories/
│   └── nuevo_modulo_repository.py  # SupabaseNuevoModuloRepository
├── services/
│   └── nuevo_modulo_service.py     # Service uses repository
└── presentation/
    └── pages/nuevo_modulo/
```

**Option B: Direct Access** (simple)
```
app/
├── entities/
│   └── nuevo_modulo.py          # Entity, Create, Update models
├── services/
│   └── nuevo_modulo_service.py     # Service uses db_manager directly
└── presentation/
    └── pages/nuevo_modulo/
```

### 3. Services (Business Logic)

Services orchestrate business operations:

```python
from app.services import empresa_service

# The singleton is already instantiated
empresas = await empresa_service.obtener_todas()
resumen = await empresa_service.obtener_resumen_empresas()
nueva = await empresa_service.crear(empresa_create)
```

### 4. Reflex State Management (v0.8.21)

Reflex v0.8.21 requires **explicit setter methods**:

```python
from app.presentation.components.shared.base_state import BaseState

class EmpresasState(BaseState):
    empresas: List[EmpresaResumen] = []
    loading: bool = False

    # REQUIRED: explicit setters
    def set_loading(self, value: bool):
        self.loading = value

    # Async methods work inside state
    async def cargar_empresas(self):
        self.loading = True
        try:
            self.empresas = await empresa_service.obtener_resumen_empresas()
        finally:
            self.loading = False
```

### 5. Database Connection

Single connection manager (singleton):

```python
from app.database import db_manager

# Get Supabase client
supabase = db_manager.get_client()

# Test connection
if db_manager.test_connection():
    print("Connected!")
```

**Implementation Details:**
- Located in: `app/database/connection.py`
- Singleton pattern: `db_manager` is instantiated globally
- Uses `supabase-py` client library
- Credentials loaded from environment variables (`.env`)
- **Supabase Storage**: File uploads handled via same client (see `app/services/archivo_service.py`)

## Database Migrations (Supabase)

**Location**: `migrations/` directory in project root

**Naming Convention**: `{number}_{description}.sql`
- Examples: `001_add_search_indices.sql`, `003_create_empleados_table.sql`

### Executing Migrations

Migrations are executed **manually** in Supabase Dashboard:

1. Go to **Supabase Dashboard** → Your Project → **SQL Editor**
2. Copy migration content from `migrations/` directory
3. Paste and click **Run**
4. Verify changes in **Table Editor** or **Database** tab

**Important Notes:**
- No automatic migration tool (like Alembic/Flyway) - migrations are manual
- Always test migrations in a dev environment first
- Each migration includes rollback instructions (commented at bottom)
- Migrations are idempotent (use `IF NOT EXISTS`, `DO $$`, etc.)

### Migration Structure

All migrations follow this structure:

```sql
-- ============================================================================
-- Migration: Create Empleados Table
-- Fecha: 2025-01-21
-- Descripción: [What this migration does]
-- ============================================================================

-- 1. Create ENUMs (if needed)
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'estatus_empleado') THEN
        CREATE TYPE estatus_empleado AS ENUM ('ACTIVO', 'INACTIVO', 'SUSPENDIDO');
    END IF;
END $$;

-- 2. Create table
CREATE TABLE IF NOT EXISTS public.empleados (
    id SERIAL PRIMARY KEY,
    -- ... columns
    CONSTRAINT uk_empleados_curp UNIQUE (curp)
);

-- 3. Add comments (documentation)
COMMENT ON TABLE public.empleados IS 'Description...';

-- 4. Create indices
CREATE INDEX IF NOT EXISTS idx_empleados_empresa
ON public.empleados USING btree (empresa_id);

-- 5. Create triggers (audit fields)
CREATE OR REPLACE FUNCTION update_empleados_fecha_actualizacion()
RETURNS TRIGGER AS $$
BEGIN
    NEW.fecha_actualizacion = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_empleados_fecha_actualizacion
    BEFORE UPDATE ON public.empleados
    FOR EACH ROW
    EXECUTE FUNCTION update_empleados_fecha_actualizacion();

-- ============================================================================
-- Rollback (if you need to revert)
-- ============================================================================
-- DROP TRIGGER IF EXISTS trg_empleados_fecha_actualizacion ON public.empleados;
-- DROP FUNCTION IF EXISTS update_empleados_fecha_actualizacion();
-- DROP TABLE IF EXISTS public.empleados;
-- DROP TYPE IF EXISTS estatus_empleado;
```

### Common Migration Patterns

**1. Adding Performance Indices**

```sql
-- Case-insensitive search (LOWER indices for ilike queries)
CREATE INDEX IF NOT EXISTS idx_empleados_nombre_lower
ON public.empleados USING btree (LOWER(nombre));

-- Composite index for common filter combinations
CREATE INDEX IF NOT EXISTS idx_empleados_empresa_estatus
ON public.empleados USING btree (empresa_id, estatus);

-- Ordering index (DESC for recent-first)
CREATE INDEX IF NOT EXISTS idx_empleados_fecha_creacion
ON public.empleados USING btree (fecha_creacion DESC);
```

**2. Creating PostgreSQL ENUMs**

```sql
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'tipo_empresa') THEN
        CREATE TYPE tipo_empresa AS ENUM ('NOMINA', 'SUMINISTRO', 'SERVICIOS');
    END IF;
END $$;
```

**3. Audit Triggers (fecha_actualizacion)**

All tables include `fecha_creacion` and `fecha_actualizacion`. Update trigger is created in each table's migration.

### Existing Migrations

| Migration | Description |
|-----------|-------------|
| `001_add_search_indices.sql` | Performance indices for empresas table |
| `002_create_plazas_table.sql` | Plazas table (job positions) |
| `003_create_empleados_table.sql` | Empleados table (employees) |
| `004_create_historial_laboral_table.sql` | Employee assignment history |
| `006_create_requisiciones.sql` | Requisiciones + items tables |
| `007_create_lugares_entrega.sql` | Delivery locations |
| `008_permitir_borradores_requisicion.sql` | Allow draft requisitions |
| `009_create_archivo_sistema.sql` | File upload system (generic) |

### Database Schema (Current Tables)

**Core Business Tables:**

| Table | Description | Key Fields | Foreign Keys |
|-------|-------------|------------|--------------|
| `empresas` | Companies/providers | id, rfc (unique), nombre_comercial, tipo_empresa, estatus | - |
| `empleados` | Employees | id, clave (unique), curp (unique), empresa_id, estatus | empresa_id → empresas |
| `contratos` | Service contracts | id, empresa_id, numero_contrato, estatus | empresa_id → empresas |
| `plazas` | Job positions/slots | id, contrato_id, clave, estatus | contrato_id → contratos |
| `historial_laboral` | Employee assignments | id, empleado_id, plaza_id, estatus | empleado_id → empleados, plaza_id → plazas |

**Requisiciones (Purchase Orders):**

| Table | Description | Key Fields | Foreign Keys |
|-------|-------------|------------|--------------|
| `requisiciones` | Requisition headers | id, numero, empresa_id, estatus | empresa_id → empresas |
| `requisicion_items` | Requisition line items | id, requisicion_id, cantidad, precio | requisicion_id → requisiciones |
| `lugares_entrega` | Delivery locations | id, nombre, direccion | - |

**Configuration & Catalogs:**

| Table | Description | Key Fields |
|-------|-------------|------------|
| `categorias_puesto` | Job categories | id, nombre, nivel |
| `tipos_servicio` | Service types | id, nombre, descripcion |
| `contrato_categoria` | Contract-category pricing | contrato_id, categoria_id, tarifa |
| `archivo_sistema` | Generic file storage | id, entidad_tipo, entidad_id, archivo_url |

**PostgreSQL ENUMs Created:**

- `estatus_empresa`: ACTIVO, INACTIVO, SUSPENDIDO
- `tipo_empresa`: NOMINA, SUMINISTRO, SERVICIOS
- `estatus_empleado`: ACTIVO, INACTIVO, SUSPENDIDO
- `genero_empleado`: MASCULINO, FEMENINO
- `motivo_baja`: RENUNCIA, DESPIDO, FIN_CONTRATO, JUBILACION, FALLECIMIENTO, OTRO
- `estatus_plaza`: DISPONIBLE, OCUPADA, SUSPENDIDA, CANCELADA
- `estatus_historial`: ACTIVA, FINALIZADA, SUSPENDIDA
- `estatus_requisicion`: BORRADOR, PENDIENTE, APROBADA, RECHAZADA, CANCELADA

**Supabase Storage Buckets:**

- `archivos` - All uploaded files (PDFs, images, documents)
  - Path structure: `{entidad_tipo}/{year}/{filename}`
  - Example: `requisiciones/2025/REQ-001.pdf`
  - Compression: Images → WebP, PDFs → compressed (see `app/core/compresores/`)

## Supabase Query Patterns

Repositories use the Supabase Python client with a fluent query builder API:

### Basic CRUD

```python
# SELECT
result = self.supabase.table('empleados').select('*').eq('id', 1).execute()
empleado = result.data[0]  # First row

# INSERT
datos = empleado.model_dump(mode='json', exclude={'id', 'fecha_creacion'})
result = self.supabase.table('empleados').insert(datos).execute()

# UPDATE
result = self.supabase.table('empleados')\
    .update({'estatus': 'INACTIVO'})\
    .eq('id', 1)\
    .execute()

# DELETE (not recommended - use soft delete instead)
result = self.supabase.table('empleados').delete().eq('id', 1).execute()
```

### Filtering

```python
# Equality
.eq('estatus', 'ACTIVO')

# Not equal
.neq('estatus', 'INACTIVO')

# Case-insensitive LIKE (requires LOWER() index)
.ilike('nombre', f'%{texto}%')

# OR conditions (multiple fields)
.or_(
    f"nombre.ilike.%{texto}%,"
    f"apellido_paterno.ilike.%{texto}%,"
    f"curp.ilike.%{texto}%"
)

# Multiple filters (AND)
query = query.eq('empresa_id', 1).eq('estatus', 'ACTIVO')
```

### Joins (Foreign Table Select)

```python
# Select with join (empresa data)
result = self.supabase.table('empleados')\
    .select('*, empresas(nombre_comercial, rfc)')\
    .eq('id', 1)\
    .execute()

# Access nested data
data = result.data[0]
empleado_nombre = data['nombre']
empresa_nombre = data['empresas']['nombre_comercial']  # From join
```

### Pagination & Ordering

```python
# Pagination with range (inclusive)
.range(offset, offset + limite - 1)

# Example: page 2, 50 per page
offset = 50  # page * limit
limite = 50
.range(50, 99)  # Records 50-99 (50 total)

# Ordering
.order('apellido_paterno', desc=False)  # ASC
.order('fecha_creacion', desc=True)     # DESC (most recent first)

# Multiple order fields
.order('empresa_id').order('apellido_paterno')
```

### Counting

```python
# Get total count (with filters)
result = self.supabase.table('empleados')\
    .select('id', count='exact')\
    .eq('estatus', 'ACTIVO')\
    .execute()

total = result.count  # Total matching records
```

### Complete Query Example

```python
async def buscar(
    self,
    texto: str,
    empresa_id: Optional[int] = None,
    limite: int = 20,
    offset: int = 0
) -> List[Empleado]:
    """Search employees with filters, joins, pagination"""
    query = self.supabase.table('empleados')\
        .select('*, empresas(nombre_comercial)')\
        .or_(
            f"nombre.ilike.%{texto}%,"
            f"apellido_paterno.ilike.%{texto}%,"
            f"curp.ilike.%{texto}%"
        )

    if empresa_id:
        query = query.eq('empresa_id', empresa_id)

    query = query.order('apellido_paterno')\
        .range(offset, offset + limite - 1)

    result = query.execute()
    return [Empleado(**data) for data in result.data]
```

### Supabase Storage (Files)

For file uploads (PDFs, images, documents):

```python
from app.database import db_manager

supabase = db_manager.get_client()

# Upload file
file_bytes = ...
file_path = "requisiciones/2025/REQ-001.pdf"

supabase.storage.from_('archivos')\
    .upload(file_path, file_bytes, file_options={'content-type': 'application/pdf'})

# Get public URL
url = supabase.storage.from_('archivos').get_public_url(file_path)

# Download file
file_bytes = supabase.storage.from_('archivos').download(file_path)

# Delete file
supabase.storage.from_('archivos').remove([file_path])
```

**See**: `app/services/archivo_service.py` for complete file upload pipeline with compression.

### Important: Date Serialization

Pydantic models with `date`/`datetime` fields must use `mode='json'` for Supabase:

```python
# ❌ Wrong - Supabase can't serialize date objects
datos = empleado.model_dump(exclude={'id'})

# ✅ Correct - Converts dates to ISO strings
datos = empleado.model_dump(mode='json', exclude={'id', 'fecha_creacion'})
```

## Environment Configuration

**Required** `.env` variables:

```bash
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
APP_NAME="Sistema de Administración de Personal"
APP_VERSION="0.1.0"
DEBUG=FALSE
```

Configuration is validated on startup by `app/core/config.py`.

## Development Guidelines

### Adding a New Feature to Empresas

1. **Update entity** if needed: `app/entities/empresa.py`
2. **Add repository method** if needed: `app/repositories/empresa_repository.py`
3. **Add service method**: `app/services/empresa_service.py`
4. **Update presentation**: `app/presentation/pages/empresas/` or `app/presentation/components/empresas/`

### Adding a New Module (e.g., Nóminas)

**Step 1: Decide on data access pattern** (see [Repository Pattern](#2-repository-pattern-two-approaches))

**If Simple CRUD** (single table, no JOINs):
1. Create entity: `app/entities/nomina.py`
2. Create service with direct access: `app/services/nomina_service.py`
3. Create presentation:
   - Page: `app/presentation/pages/nominas/`
   - Components: `app/presentation/components/nominas/`

**If Complex Queries** (JOINs, aggregations):
1. Create entity: `app/entities/nomina.py`
2. Create repository: `app/repositories/nomina_repository.py`
3. Create service using repository: `app/services/nomina_service.py`
4. Create presentation:
   - Page: `app/presentation/pages/nominas/`
   - Components: `app/presentation/components/nominas/`

**Database Migration**:
5. Create migration: `migrations/XXX_create_nominas.sql`
   - Include: Table, ENUMs, Indices, Triggers, Comments
   - Execute in Supabase Dashboard SQL Editor

**Update Exports**:
6. Add to `app/entities/__init__.py`
7. Add to `app/repositories/__init__.py` (if using repository)
8. Add to `app/services/__init__.py`

**Much simpler** - Just add files, no need to create nested directory structures!

### Reflex-Specific Notes

- **State setters**: Always explicit in v0.8.21+
- **Conditional rendering**: `rx.cond(condition, if_true, if_false)` - always both branches
- **Iteration**: `rx.foreach(list_var, render_fn)` - never Python `for` in render
- **Boolean operators**: Use `&`, `|`, `~` with rx.Var (not `and`, `or`, `not`)
- **Async methods**: Automatically awaited by Reflex
- **Components**: Pure functions returning `rx.Component`
- **Layout**: Shared sidebar/navbar in `app/presentation/layout/`
- **rx.foreach + form_input**: Inside `rx.foreach`, dict values become Vars. `form_input` uses Python-level `if` checks that fail with Vars. Use inline `rx.cond` pattern instead of `form_input` for dynamic fields rendered via `rx.foreach`.

### Import Patterns

```python
# Entities
from app.entities import Empresa, TipoEmpresa, EstatusEmpresa

# Repository (only for complex modules: empleado, plaza, contrato, requisicion)
from app.repositories import SupabaseEmpleadoRepository

# Service (use singleton - always imported)
from app.services import empresa_service, empleado_service

# Database (only needed for direct access pattern in services)
from app.database import db_manager

# Core utilities
from app.core.exceptions import NotFoundError, DuplicateError, DatabaseError
from app.core.text_utils import capitalizar_con_preposiciones, formatear_telefono

# UI Components
from app.presentation.components.ui import (
    form_input, form_select, form_textarea, form_date, form_row,
    tabla, tabla_vacia, skeleton_tabla,
    modal_formulario, modal_confirmar_eliminar,
    status_badge, breadcrumb, view_toggle,
    barra_herramientas, barra_filtros,
)

# Theme tokens
from app.presentation.theme import Colors, Spacing, Typography

# Presentation
from app.presentation.pages.empresas import empresas_page, EmpresasState
from app.presentation.components.shared.base_state import BaseState
```

**Import Pattern for New Services**:

**Pattern A - With Repository** (complex queries):
```python
# app/services/empleado_service.py
from app.repositories import SupabaseEmpleadoRepository
from app.entities import Empleado, EmpleadoCreate, EmpleadoUpdate
from app.core.exceptions import NotFoundError, DatabaseError

class EmpleadoService:
    def __init__(self):
        self.repository = SupabaseEmpleadoRepository()
```

**Pattern B - Direct Access** (simple CRUD):
```python
# app/services/empresa_service.py
from app.database import db_manager
from app.entities import Empresa, EmpresaCreate, EmpresaUpdate
from app.core.exceptions import NotFoundError, DuplicateError, DatabaseError

class EmpresaService:
    def __init__(self):
        self.supabase = db_manager.get_client()
        self.tabla = 'empresas'
```

### Form Input Pattern (Standard)

All form fields use `form_input` with `label=` parameter (not placeholder for field name):

```python
from app.presentation.components.ui import form_input, form_select, form_date, form_row

# Standard input with label, example placeholder, and hint
form_input(
    label="Nombre comercial",
    required=True,                          # Adds " *" to label
    placeholder="Ej: ACME Corporation",     # Example value
    hint="Se formatea automaticamente",     # Help text below field
    value=State.form_nombre,
    on_change=State.set_form_nombre,
    on_blur=State.validar_nombre_campo,
    error=State.error_nombre,
    max_length=100,
)

# Select with label
form_select(
    label="Tipo de empresa",
    required=True,
    placeholder="Seleccione tipo",
    options=State.opciones_tipo,
    value=State.form_tipo,
    on_change=State.set_form_tipo,
    error=State.error_tipo,
)

# Date picker
form_date(
    label="Fecha de inicio",
    required=True,
    value=State.form_fecha_inicio,
    on_change=State.set_form_fecha_inicio,
    error=State.error_fecha_inicio,
)

# Row layout (2 fields side by side)
form_row(
    form_input(label="Nombre", ...),
    form_input(label="Apellido", ...),
)
```

**IMPORTANT**: `form_input` cannot be used inside `rx.foreach` because its Python-level `if not label:` check fails when label is a Var. For dynamic fields in `rx.foreach`, use inline `rx.cond` pattern instead (see `configuracion_page.py` for example).

### Validation Strategy (Defense in Depth)

**Philosophy**: Double validation for security and UX - frontend catches errors early, backend ensures data integrity.

#### **Two-Layer Validation**

```
User Input → Frontend Validators → Pydantic Validators → Database
             (UX, Real-time)        (Security, Final)
```

**Rules:**
1. **Frontend validators** (`app/presentation/pages/{module}/{module}_validators.py`):
   - Pure functions that return error messages
   - Execute on `on_blur` (real-time) and on submit
   - Provide immediate user feedback
   - Same rules as Pydantic (synchronized)

2. **Pydantic validators** (`app/entities/{entity}.py`):
   - Field constraints (`Field(min_length=2, max_length=100)`)
   - Custom `@field_validator` decorators for complex logic
   - Last line of defense before database
   - **Must match frontend rules exactly**

#### **Validation Synchronization Checklist**

When adding/modifying validation:
- [ ] Update frontend validator function
- [ ] Update Pydantic Field constraints
- [ ] Update Pydantic @field_validator if needed
- [ ] Ensure error messages are identical
- [ ] Test both layers independently

#### **Current Validation Rules (Empresas)**

| Campo | Min | Max | Pattern/Format | Optional |
|-------|-----|-----|----------------|----------|
| nombre_comercial | 2 | 100 | - | ❌ Required |
| razon_social | 2 | 100 | - | ❌ Required |
| rfc | 12 | 13 | `^[A-Z&Ñ]{3,4}[0-9]{6}[A-V1-9][A-Z1-9][0-9A]$` | ❌ Required |
| email | - | 100 | `^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$` | ✅ Optional |
| codigo_postal | 5 | 5 | `^[0-9]{5}$` | ✅ Optional |
| telefono | 10 dígitos | 15 chars | 10 dígitos sin separadores | ✅ Optional |

**Example: RFC Validation (Synchronized)**

Frontend (`empresas_validators.py:52-89`):
```python
def validar_rfc(rfc: str) -> str:
    if len(rfc_limpio) < 12 or len(rfc_limpio) > 13:
        return f"RFC debe tener 12 o 13 caracteres (tiene {len(rfc_limpio)})"
    patron = r'^[A-Z&Ñ]{3,4}[0-9]{6}[A-V1-9][A-Z1-9][0-9A]$'
    if not re.match(patron, rfc_limpio):
        return "RFC: Las primeras 3-4 letras son inválidas"
    return ""
```

Backend (`empresa.py:108-127`):
```python
@field_validator('rfc')
def validar_rfc(cls, v: str) -> str:
    if len(v) < 12 or len(v) > 13:
        raise ValueError(f'RFC debe tener 12 o 13 caracteres (tiene {len(v)})')
    patron = r'^[A-Z&Ñ]{3,4}[0-9]{6}[A-V1-9][A-Z1-9][0-9A]$'
    if not re.match(patron, v):
        raise ValueError('RFC: Las primeras 3-4 letras son inválidas')
    return v
```

**Why Both?**
- Frontend: Instant feedback, better UX, reduces server load
- Backend: Security (API can be called directly), data integrity guarantee
- Synchronized: Consistent user experience, no surprises

### Error Handling Pattern (Exception Propagation)

**Philosophy**: Let exceptions propagate up from Repository → Service → State, with specific handling at the UI layer.

#### **Exception Hierarchy**

All custom exceptions inherit from `ApplicationError` (`app/core/exceptions.py`):

```python
from app.core.exceptions import (
    ApplicationError,   # Base exception
    NotFoundError,      # Resource not found in database
    DuplicateError,     # Unique constraint violation (RFC, email, etc.)
    DatabaseError,      # Connection/infrastructure errors
    ValidationError,    # Data validation errors (Pydantic)
    BusinessRuleError,  # Business logic violations
)
```

#### **Layer Responsibilities**

**1. Repository Layer** (`app/repositories/`):
- **Raises** specific exceptions (NotFoundError, DuplicateError, DatabaseError)
- **Does NOT catch** exceptions - lets them propagate
- **Documents** exceptions in docstrings with `Raises:` section

```python
async def obtener_por_id(self, empresa_id: int) -> Empresa:
    """
    Obtiene una empresa por su ID.

    Raises:
        NotFoundError: Si la empresa no existe
        DatabaseError: Si hay error de conexión/infraestructura
    """
    try:
        result = self.supabase.table(self.tabla).select('*').eq('id', empresa_id).execute()
        if not result.data:
            raise NotFoundError(f"Empresa con ID {empresa_id} no encontrada")
        return Empresa(**result.data[0])
    except NotFoundError:
        raise  # Re-propagate business errors
    except Exception as e:
        logger.error(f"Error obteniendo empresa {empresa_id}: {e}")
        raise DatabaseError(f"Error de base de datos: {str(e)}")
```

**2. Service Layer** (`app/services/`):
- **Propagates** exceptions from repository (NO try-catch)
- **Documents** exceptions in docstrings
- **May add** business logic validation and raise BusinessRuleError

```python
async def crear(self, empresa_create: EmpresaCreate) -> Empresa:
    """
    Crea una nueva empresa.

    Raises:
        DuplicateError: Si el RFC ya existe
        ValidationError: Si los datos no son válidos
        DatabaseError: Si hay error de BD
    """
    empresa = Empresa(**empresa_create.model_dump())  # May raise ValidationError
    return await self.repository.crear(empresa)  # May raise DuplicateError/DatabaseError
```

**3. Presentation Layer (State)** (`app/presentation/pages/{module}/{module}_state.py`):
- **Catches** specific exceptions
- **Shows** user-friendly messages
- **Handles** UI state (modal open/close, loading, etc.)

```python
async def crear_empresa(self):
    """Crear una nueva empresa"""
    self.saving = True
    try:
        empresa_creada = await empresa_service.crear(nueva_empresa)

        self.cerrar_modal_empresa()
        await self.cargar_empresas()
        return rx.toast.success(f"Empresa '{empresa_creada.nombre_comercial}' creada")

    except DuplicateError as e:
        self.mostrar_mensaje(f"RFC duplicado: {e.field} ya existe", "error")
        return  # Keep modal open
    except ValidationError as e:
        self.mostrar_mensaje(f"Error de validación: {str(e)}", "error")
        return
    except DatabaseError as e:
        self.mostrar_mensaje(f"Error de base de datos: {str(e)}", "error")
        return
    except Exception as e:
        self.mostrar_mensaje(f"Error inesperado: {str(e)}", "error")
        return
    finally:
        self.saving = False
```

#### **Error Handling Checklist (for new modules)**

When implementing a new module (empleados, nóminas, etc.):

**Repository:**
- [ ] Import custom exceptions: `from app.core.exceptions import NotFoundError, DuplicateError, DatabaseError`
- [ ] Raise `NotFoundError` when resource not found
- [ ] Raise `DuplicateError` when unique constraint violated (include field and value)
- [ ] Raise `DatabaseError` for connection/infrastructure errors
- [ ] Document all exceptions in method docstrings (`Raises:` section)
- [ ] Re-propagate business exceptions (don't catch)

**Service:**
- [ ] Import custom exceptions if needed for business rules
- [ ] Let repository exceptions propagate (NO try-catch)
- [ ] Document exceptions in method docstrings
- [ ] Add business logic validation if needed (raise `BusinessRuleError`)

**State (Presentation):**
- [ ] Import exceptions: `from app.core.exceptions import NotFoundError, DuplicateError, DatabaseError, ValidationError, BusinessRuleError`
- [ ] Catch specific exceptions in order of specificity
- [ ] Show user-friendly messages (avoid technical jargon)
- [ ] Handle UI state properly (loading, modals, etc.)
- [ ] Keep modals open on error (don't close)
- [ ] Use `rx.toast.success()` for success messages
- [ ] Use `self.mostrar_mensaje(msg, "error")` for error messages

#### **Common Exception Patterns**

| Operation | Common Exceptions |
|-----------|-------------------|
| `obtener_por_id()` | NotFoundError, DatabaseError |
| `obtener_todas()` | DatabaseError |
| `crear()` | DuplicateError, ValidationError, DatabaseError |
| `actualizar()` | NotFoundError, ValidationError, DatabaseError |
| `eliminar()` | NotFoundError, DatabaseError |
| `buscar_por_texto()` | DatabaseError |

### Performance Optimization Patterns

**Philosophy**: Optimize for real-world scale - databases with 10k+ records, slow networks, concurrent users.

#### **Database Indices**

**Why**: Búsquedas en tablas grandes sin índices son O(n). Con índices: O(log n) → ~100x más rápido.

**Required Indices** (empresas table):

```sql
-- Índices para búsqueda case-insensitive (ilike)
CREATE INDEX idx_empresas_nombre_comercial_lower
ON empresas USING btree (LOWER(nombre_comercial));

CREATE INDEX idx_empresas_razon_social_lower
ON empresas USING btree (LOWER(razon_social));

-- Índice compuesto para filtros combinados
CREATE INDEX idx_empresas_tipo_estatus
ON empresas USING btree (tipo_empresa, estatus);

-- Índice para ordenamiento por fecha (más recientes primero)
CREATE INDEX idx_empresas_fecha_creacion
ON empresas USING btree (fecha_creacion DESC);
```

**Checklist for new tables:**
- [ ] Add LOWER() indices for all text search fields
- [ ] Add composite indices for frequently combined filters
- [ ] Add indices for sorting fields (DESC if showing recent first)
- [ ] Add unique indices for business keys (RFC, CURP, email)

#### **Pagination**

**Why**: Cargar 10k empresas en memoria consume ~50MB y tarda 5+ segundos. Con paginación: ~500KB y <200ms.

**Implementation Pattern:**

**Repository:**
```python
async def obtener_todas(
    self,
    incluir_inactivas: bool = False,
    limite: Optional[int] = None,  # None = default 100
    offset: int = 0
) -> List[Empresa]:
    """
    Args:
        limite: Max results (None = 100 default for safety)
        offset: Records to skip (page * limit)
    """
    query = self.supabase.table(self.tabla).select('*')

    if not incluir_inactivas:
        query = query.eq('estatus', 'ACTIVO')

    # Usar índice para ordenamiento
    query = query.order('fecha_creacion', desc=True)

    # Paginación
    if limite is not None:
        query = query.range(offset, offset + limite - 1)
    else:
        query = query.limit(100)  # Safety limit

    result = query.execute()
    return [Empresa(**data) for data in result.data]
```

**Service:**
```python
async def obtener_resumen_empresas(
    self,
    incluir_inactivas: bool = False,
    limite: Optional[int] = 50,  # Default 50 for responsive UI
    offset: int = 0
) -> List[EmpresaResumen]:
    empresas = await self.repository.obtener_todas(incluir_inactivas, limite, offset)
    return [EmpresaResumen.from_empresa(e) for e in empresas]
```

**Pagination Defaults:**
- Repository: 100 records (safety limit)
- Service (for UI): 50 records (responsive, fits in viewport)
- Search: 10-20 records (quick results)

#### **Search Optimization**

**Problem**: In-memory search loads ALL records, then filters → O(n) always.

**Solution**: Database-level search with indices → O(log n).

**Before (❌ Slow):**
```python
# Loads ALL empresas into memory, then filters
async def buscar_por_nombre(self, termino: str) -> List[Empresa]:
    todas = await self.repository.obtener_todas(incluir_inactivas=True)
    return [e for e in todas if termino.lower() in e.nombre_comercial.lower()]
```

**After (✅ Fast):**
```python
# Uses database index, returns only matches
async def buscar_por_texto(self, termino: str, limite: int = 10) -> List[Empresa]:
    result = self.supabase.table(self.tabla)\
        .select('*')\
        .or_(
            f"nombre_comercial.ilike.%{termino}%,"
            f"razon_social.ilike.%{termino}%"
        )\
        .limit(limite)\
        .execute()
    return [Empresa(**data) for data in result.data]
```

**Key Points:**
- Use `.ilike` for case-insensitive search (requires LOWER() indices)
- ALWAYS limit search results (default 10-20)
- Min 2 characters before searching (avoid loading entire table)

#### **Performance Checklist (for new modules)**

**Repository:**
- [ ] Add pagination support (`limite`, `offset`) to `obtener_todas()`
- [ ] Set safety limit (100) when no limit specified
- [ ] Use database indices for ordering (avoid memory sorts)
- [ ] Implement `buscar_por_texto()` with database-level search
- [ ] Limit search results (10-20 default)

**Service:**
- [ ] Pass pagination parameters to repository
- [ ] Set UI-friendly defaults (50 records for listings)
- [ ] Document performance characteristics in docstrings

**Database:**
- [ ] Create LOWER() indices for all searchable text fields
- [ ] Create composite indices for common filter combinations
- [ ] Create indices for sort fields (DESC if recent-first)
- [ ] Run `EXPLAIN ANALYZE` to verify index usage

**State (Future Enhancement):**
- [ ] Add pagination state vars (`page`, `pageSize`, `totalRecords`)
- [ ] Implement "Load More" or page controls
- [ ] Add debouncing to search input (300-500ms)
- [ ] Show loading skeletons during fetch

#### **Performance Metrics**

| Operation | Without Optimization | With Optimization | Improvement |
|-----------|---------------------|-------------------|-------------|
| Search 10k records | ~5s | ~50ms | **100x faster** |
| Load all records | ~3s, 50MB | ~200ms, 500KB | **15x faster, 100x less memory** |
| Filter + Sort | ~1s (memory) | ~50ms (index) | **20x faster** |

## Business Calculations

Mexican payroll calculations in `app/core/calculations/`:

- **`imss.py`**: IMSS (Instituto Mexicano del Seguro Social)
- **`isr.py`**: ISR (Impuesto Sobre la Renta)
- **`payroll.py`**: General payroll processing

These are independent utilities used across modules.

## Module Status

### Implemented
- Empresas (entity, repository, service, page, components)
- Empleados (entity, repository, service, page)
- Contratos (entity, repository, service, page)
- Plazas (entity, repository, service, page, components)
- Requisiciones (entity, repository, service, page, components, form)
- Configuracion (page, state - default values for requisiciones)
- Archivos (entity, repository, service, compresores - generic file upload with WebP compression, Supabase Storage)
- Categorias de Puesto (entity, repository, service, page)
- Tipos de Servicio (entity, repository, service, page)
- Historial Laboral (entity, repository, service, page)
- Pagos (entity, repository, service)
- Contrato-Categoria (entity, repository, service)
- Costos Patronales (entity)
- Dashboard (page)
- Simulador (page)

### Pending
- Portal de Cliente
- Sedes

## Important Files

### Core Architecture
- **`app/app.py`**: Application entry point, routes, API transformer
- **`rxconfig.py`**: Reflex config (Sitemap, TailwindV4 plugins)
- **`app/database/connection.py`**: Supabase singleton (db_manager)
- **`app/repositories/__init__.py`**: Documents repository pattern philosophy (complex vs simple)

### Entities & Business Logic
- **`app/entities/`**: All domain models (Pydantic entities)
- **`app/core/enums.py`**: All enums (Estatus, TipoEmpresa, TipoEntidadArchivo, TipoArchivo, etc.)
- **`app/core/exceptions.py`**: Custom exception hierarchy (ApplicationError base)
- **`app/core/validation/`**: FieldConfig, constants, custom validators
- **`app/core/text_utils.py`**: Text normalization (normalizar_por_sufijo, capitalizar_con_preposiciones, formatear_telefono, etc.)
- **`app/core/calculations/`**: Business calculations (IMSS, ISR, payroll)
- **`app/core/compresores/`**: Image (WebP) and PDF compression

### Data Access
- **`app/repositories/`**: Complex query repositories (empleado, plaza, contrato, requisicion)
- **`app/services/`**: Business logic services (all modules - some use repositories, some use direct access)

### Presentation Layer
- **`app/presentation/components/ui/form_input.py`**: form_input, form_select, form_textarea, form_date, form_row
- **`app/presentation/components/ui/tables.py`**: tabla, tabla_vacia, skeleton_tabla
- **`app/presentation/components/ui/modals.py`**: modal_formulario, modal_confirmar_eliminar
- **`app/presentation/theme/`**: Colors, Spacing, Typography, StatusColors tokens
- **`app/presentation/components/shared/base_state.py`**: BaseState for all page states

### Configuration & Environment
- **`app/core/config/`**: Environment configuration (Supabase credentials, app settings)
- **`.env`**: Environment variables (SUPABASE_URL, SUPABASE_KEY, etc.)
- **`pyproject.toml`**: Dependencies and project metadata

### Database Migrations
- **`migrations/`**: SQL migration scripts (manually executed in Supabase Dashboard)
- See [Database Migrations](#database-migrations-supabase) section for details

## Next Steps

1. Implement Portal de Cliente module
2. Implement Sedes module
3. Add comprehensive tests
4. Add API documentation
