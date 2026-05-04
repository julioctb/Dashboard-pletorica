# Dashboard Architecture

## Scope

Usar esta referencia cuando el trabajo sea dentro de este repo y haya que decidir dónde tocar código, cómo extender una feature o cómo mantener consistencia entre capas.

## Project Snapshot

- Runtime principal: Python `>=3.10,<4.0`.
- Framework UI: `reflex >=0.8.21,<0.9.0` en `pyproject.toml`.
- Layout de alto nivel: app Reflex en `app/app.py` y bootstrap en `app/bootstrap/app_factory.py`.
- Patrón dominante: dominio y acceso a datos fuera de UI; presentación separada por páginas y componentes.

## Main Directories

### `app/app.py` + `app/bootstrap/`

- `app/app.py` delega a `create_app()`.
- `app/bootstrap/app_factory.py` compone tema, toaster, API transformer y registro de rutas.
- El registro de rutas vive en `app/bootstrap/routes_core.py`, `routes_backoffice.py` y `routes_portal.py`.

### `app/domain/`

- Reunir modelos, servicios y repositories legacy donde vive gran parte de la lógica actual.
- Mantener aquí estructuras que no deben depender de Reflex.

### `app/modules/`

- Fachadas DDD por feature (`cotizaciones`, `empleados`, `nomina`) sobre `app/domain/`.
- Útil para ubicar exports de UI/state por superficie (backoffice/portal).

### `app/presentation/`

- Contener páginas, estados, layouts y componentes visuales de backoffice y portal.
- Organizar por módulo funcional.

### `app/api/`

- Exponer rutas FastAPI y contratos externos.
- Mantener aquí la frontera HTTP, no en la capa Reflex.

## Existing State Patterns

### `BaseState`

- Centralizar loading, mensajes, manejo de errores y utilidades repetidas.
- Reusar cuando el módulo necesite ciclos comunes de fetch, recarga o mensajes.

### `CRUDStateMixin`

- Resolver patrones estándar de modal, formulario y operaciones CRUD.
- Reusar antes de crear otro helper genérico de CRUD.

### `AuthState`

- Resolver autenticación, guardas y redirecciones.
- Revisar si una página depende de auth antes de moverla o duplicarla.

## Route and Layout Patterns

- Backoffice: revisar `BACKOFFICE_PAGE_ROUTES` en `app/presentation/config/routes.py`.
- Portal: revisar `PORTAL_PAGE_ROUTES` en `app/presentation/config/routes.py`.
- La referencia final de rutas es `app/presentation/config/routes.py` + registro en `app/bootstrap/routes_*.py`.
- Si una página parece no renderizar, revisar primero import, route map y registro en bootstrap.

## Feature Placement Guide

Si el cambio es visual:

- Tocar `page.py`, `components.py` o componentes reutilizables.

Si el cambio es de interacción:

- Tocar el `state.py` del módulo y sus handlers.

Si el cambio es de negocio, persistencia o agregación:

- Tocar `app/domain/services/` (o `app/modules/*/application` cuando aplique).

Si el cambio altera contratos o forma de los datos:

- Tocar `app/domain/models/`, `app/core/validation/`, `app/api/` o combinación según el caso.

## Working Style for This Repo

- Buscar primero si ya existe un patrón equivalente en otro módulo.
- Copiar la forma, no solo el resultado visual.
- Mantener nombres y estructura por módulo: `page.py`, `state.py`, `components.py`, `modal.py`, `paso_*.py` cuando aplique.
- Mantener mensajes, loaders y toasts consistentes con los helpers base.
- Evitar introducir una librería o abstracción nueva si el repo ya resolvió ese problema con código propio.

## Fast Checks

1. `rg -n "CORE_ROUTES|BACKOFFICE_PAGE_ROUTES|PORTAL_PAGE_ROUTES" app/presentation/config/routes.py`
2. `rg -n "register_core_routes|register_backoffice_routes|register_portal_routes" app/bootstrap`
3. `rg -n "class .*State\\(" app/presentation`
4. `rg -n "BaseState|CRUDStateMixin|AuthState|PortalState|NominaBaseState" app`
