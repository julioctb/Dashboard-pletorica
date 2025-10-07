# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Dashboard application built with Reflex (v0.8.9) for managing dependency contracts in Mexico (empresas, empleados, sedes, nominas). Uses Supabase as backend. **Recently consolidated** to clean layered architecture (2025-10-06).

**Author**: Julio C Tello (julioc.tello@me.com)
**Status**: Production - Consolidated architecture

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

### Backup & Restore
```bash
# Restore from backup if needed
python3 migrate_to_modular.py --restore

# Create backup before changes
python3 migrate_to_modular.py --backup
```

## Architecture

### Clean Layered Architecture

The application follows a **simple layered architecture** optimized for small teams and maintainability:

```
app/
├── domain/                          # Business entities and rules
│   ├── empresas/
│   │   ├── entities.py              # Empresa, EmpresaCreate, EmpresaUpdate, EmpresaResumen
│   │   └── __init__.py              # Clean exports
│   ├── empleados/                   # (TODO: migrate from legacy)
│   ├── sedes/
│   └── nominas/
│
├── infrastructure/                  # Technical implementations
│   └── database/
│       ├── connection.py            # Supabase singleton (db_manager)
│       ├── repositories/
│       │   ├── empresa_repository.py  # IEmpresaRepository + SupabaseEmpresaRepository
│       │   └── __init__.py
│       └── __init__.py
│
├── application/                     # Business logic orchestration
│   └── services/
│       ├── empresa_service.py       # EmpresaService + empresa_service singleton
│       └── __init__.py
│
├── presentation/                    # UI layer (Reflex)
│   ├── pages/
│   │   ├── empresas/
│   │   │   ├── empresas_page.py     # Main page component
│   │   │   ├── empresas_state.py    # Reflex state management
│   │   │   └── __init__.py
│   │   └── dashboard/               # (legacy - TODO: migrate)
│   ├── components/
│   │   ├── shared/
│   │   │   └── base_state.py        # Common Reflex state
│   │   ├── ui/                      # Reusable UI components
│   │   └── business/                # Business-specific components (modals, cards)
│   └── layout/
│       ├── sidebar_layout.py
│       └── navbar_layout.py
│
├── core/                            # Cross-cutting concerns
│   ├── config.py                    # Environment configuration
│   └── calculations/
│       ├── imss.py                  # Mexican social security
│       ├── isr.py                   # Mexican income tax
│       └── payroll.py               # Payroll processing
│
├── app.py                           # Application entry point
│
└── [LEGACY - to be removed]
    ├── modules/                     # Old modular monolith attempt
    ├── database/                    # Old database models
    ├── services/                    # Old services
    ├── components/                  # Old UI components
    └── pages/                       # Old pages
```

### Architecture Benefits

✅ **Simple & Clear**: One location per concept, easy navigation
✅ **No Duplication**: Single source of truth for entities, services, etc.
✅ **Maintainable**: Ideal for small teams (1-3 developers)
✅ **Testable**: Clean dependencies, easy to mock
✅ **Scalable**: Room to add empleados/sedes/nominas modules
✅ **SOLID Principles**: Without over-engineering

## Key Patterns

### 1. Domain Entities

Domain entities use Pydantic for validation and business logic:

```python
from app.domain.empresas import Empresa, TipoEmpresa, EstatusEmpresa

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
if empresa.puede_tener_empleados():  # True for NOMINA companies
    ...

if empresa.esta_activa():
    empresa.suspender()  # Changes status with validation
```

### 2. Repository Pattern

Repositories abstract database access:

```python
from app.infrastructure.database.repositories import SupabaseEmpresaRepository

# Create repository
repository = SupabaseEmpresaRepository()

# CRUD operations
empresa = await repository.obtener_por_id(1)
empresas = await repository.obtener_todas(incluir_inactivas=False)
nueva = await repository.crear(empresa)
await repository.actualizar(empresa)
```

### 3. Service Layer

Services orchestrate business operations:

```python
from app.application.services import empresa_service

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
        self.loading = True  # OK inside async method
        try:
            self.empresas = await empresa_service.obtener_resumen_empresas()
        finally:
            self.loading = False
```

### 5. Database Connection

Single connection manager (singleton):

```python
from app.infrastructure.database import db_manager

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

1. **Update domain entity** if needed: `app/domain/empresas/entities.py`
2. **Add repository method** if needed: `app/infrastructure/database/repositories/empresa_repository.py`
3. **Add service method**: `app/application/services/empresa_service.py`
4. **Update presentation**: `app/presentation/pages/empresas/`

### Adding a New Module (e.g., Empleados)

1. Create domain: `app/domain/empleados/entities.py`
2. Create repository: `app/infrastructure/database/repositories/empleado_repository.py`
3. Create service: `app/application/services/empleado_service.py`
4. Create presentation: `app/presentation/pages/empleados/`

Much simpler than creating 4 subdirectories per module!

### Reflex-Specific Notes

- **State setters**: Always explicit in v0.8.9+
- **Conditional rendering**: `rx.cond(condition, if_true, if_false)`
- **Async methods**: Automatically awaited by Reflex
- **Components**: Pure functions returning `rx.Component`
- **Layout**: Shared sidebar/navbar in `app/presentation/layout/`

### Import Patterns

```python
# Domain
from app.domain.empresas import Empresa, TipoEmpresa, EstatusEmpresa

# Repository
from app.infrastructure.database.repositories import SupabaseEmpresaRepository

# Service (use singleton)
from app.application.services import empresa_service

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
- Domain layer consolidated
- Infrastructure layer consolidated
- Application services consolidated
- Presentation layer for empresas migrated
- Components and layout moved
- Config reorganized to core/

### ⚠️ Legacy Code (To Be Removed)
- `app/modules/` - Old modular monolith attempt
- `app/database/` - Old database models
- `app/services/` - Old service layer
- `app/components/` - Old components (moved to presentation/)
- `app/pages/dashboard/` - Dashboard not yet migrated

**Note**: Legacy code still exists for safety. Once everything is verified working, it can be deleted.

## Backups

Backups available in `backup_migration/`:
- Most recent before consolidation
- Restore with: `python3 migrate_to_modular.py --restore`

## Testing

- Configuration: `pytest.ini` (asyncio mode enabled)
- Tests location: `tests/` directory
- Run with: `pytest` or `pytest tests/empresas`

## Important Files

- **`app/app.py`**: Application entry point, routes
- **`rxconfig.py`**: Reflex config (Sitemap, TailwindV4 plugins)
- **`app/core/config.py`**: Environment configuration
- **`app/infrastructure/database/connection.py`**: Database singleton
- **`pyproject.toml`**: Dependencies and project metadata

## Next Steps

1. Migrate remaining modules (empleados, sedes, nominas) to new structure
2. Migrate dashboard page to presentation layer
3. Remove legacy code after verification
4. Add tests for new architecture
5. Update documentation with examples
