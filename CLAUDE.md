# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Dashboard application built with Reflex (v0.8.9) for managing dependency contracts in Mexico (empresas, empleados, sedes, nominas). Uses Supabase as backend. **Simplified to scalable layered architecture** (2025-10-06).

**Author**: Julio C Tello (julioc.tello@me.com)
**Status**: Production - Scalable Layered Architecture

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
├── core/                        # ⚙️ Cross-cutting concerns
│   ├── config.py               # Environment configuration
│   └── calculations/           # Business calculations (IMSS, ISR, payroll)
│
├── entities/                    # 📦 Domain models (ALL in one place)
│   ├── empresa.py              # Empresa, EmpresaCreate, EmpresaUpdate, EmpresaResumen
│   ├── empleado.py             # (TODO: migrate)
│   ├── sede.py                 # (TODO: migrate)
│   └── nomina.py               # (TODO: migrate)
│
├── repositories/                # 💾 Data access layer (ALL in one place)
│   ├── empresa_repository.py  # IEmpresaRepository + SupabaseEmpresaRepository
│   ├── empleado_repository.py # (TODO: migrate)
│   └── sede_repository.py      # (TODO: migrate)
│
├── services/                    # 🔧 Business logic (ALL in one place)
│   ├── empresa_service.py      # EmpresaService + empresa_service singleton
│   ├── empleado_service.py     # (TODO: migrate)
│   └── nomina_service.py       # (TODO: migrate)
│
├── database/                    # 🗄️ Infrastructure
│   └── connection.py           # Supabase singleton (db_manager)
│
├── presentation/                # 🎨 UI Layer (Reflex)
│   ├── pages/
│   │   └── empresas/
│   │       ├── empresas_page.py    # Main page component
│   │       └── empresas_state.py   # Reflex state management
│   │
│   ├── components/
│   │   ├── empresas/           # Empresa-specific components
│   │   │   ├── empresa_card.py
│   │   │   └── empresa_modals.py
│   │   ├── shared/             # Common state
│   │   │   └── base_state.py
│   │   └── ui/                 # Reusable UI components
│   │       ├── cards.py
│   │       ├── modals.py
│   │       ├── filters.py
│   │       └── toasts.py
│   │
│   └── layout/
│       ├── sidebar_layout.py
│       └── navbar_layout.py
│
├── tests/                       # 🧪 Unit tests
│   ├── empresas/
│   ├── empleados/
│   ├── sedes/
│   └── nominas/
│
└── app.py                       # Application entry point
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

```
Presentation → Services → Repositories → Database
                   ↓           ↓
               Entities    Entities
                   ↓
                Core
```

**Rules:**
- Presentation ONLY imports from Services and Entities
- Services ONLY import from Repositories and Entities
- Repositories ONLY import from Database and Entities
- Entities are pure (no dependencies)

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

### 2. Repositories (Data Access)

Repositories abstract database operations:

```python
from app.repositories import SupabaseEmpresaRepository

# Create repository
repository = SupabaseEmpresaRepository()

# CRUD operations
empresa = await repository.obtener_por_id(1)
empresas = await repository.obtener_todas(incluir_inactivas=False)
nueva = await repository.crear(empresa)
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

### 4. Reflex State Management (v0.8.9)

Reflex v0.8.9 requires **explicit setter methods**:

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

### Adding a New Module (e.g., Empleados)

1. Create entity: `app/entities/empleado.py`
2. Create repository: `app/repositories/empleado_repository.py`
3. Create service: `app/services/empleado_service.py`
4. Create presentation:
   - Page: `app/presentation/pages/empleados/`
   - Components: `app/presentation/components/empleados/`

**Much simpler** - Just add files, no need to create nested directory structures!

### Reflex-Specific Notes

- **State setters**: Always explicit in v0.8.9+
- **Conditional rendering**: `rx.cond(condition, if_true, if_false)`
- **Async methods**: Automatically awaited by Reflex
- **Components**: Pure functions returning `rx.Component`
- **Layout**: Shared sidebar/navbar in `app/presentation/layout/`

### Import Patterns

```python
# Entities
from app.entities import Empresa, TipoEmpresa, EstatusEmpresa

# Repository
from app.repositories import SupabaseEmpresaRepository

# Service (use singleton)
from app.services import empresa_service

# Database
from app.database import db_manager

# Presentation
from app.presentation.pages.empresas import empresas_page, EmpresasState
from app.presentation.components.shared.base_state import BaseState
```

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
    NotFoundError,      # Resource not found in database
    DuplicateError,     # Unique constraint violation (RFC, email, etc.)
    DatabaseError,      # Connection/infrastructure errors
    ValidationError,    # Data validation errors (Pydantic)
    BusinessRuleError,  # Business logic violations
    AuthorizationError  # Permission denied
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
- [ ] Import exceptions: `from app.core.exceptions import NotFoundError, DuplicateError, DatabaseError, ValidationError`
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

## Migration Status

### ✅ Completed
- ✅ Simplified to flat layered architecture
- ✅ All code for empresas migrated
- ✅ Removed all nested/complex directory structures
- ✅ Clean imports throughout

### ⚠️ TODO
- Migrate empleados module
- Migrate sedes module
- Migrate nominas module
- Implement dashboard with new architecture
- Add unit tests

## Important Files

- **`app/app.py`**: Application entry point, routes
- **`rxconfig.py`**: Reflex config (Sitemap, TailwindV4 plugins)
- **`app/core/config.py`**: Environment configuration
- **`app/database/connection.py`**: Database singleton
- **`app/entities/empresa.py`**: Main business entity
- **`pyproject.toml`**: Dependencies and project metadata

## Next Steps

1. Migrate remaining modules (empleados, sedes, nominas) to new flat structure
2. Each module = 1 entity file + 1 repository file + 1 service file
3. Add comprehensive tests
4. Implement dashboard
5. Add API documentation
