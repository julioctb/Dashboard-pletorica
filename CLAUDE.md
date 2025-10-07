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
