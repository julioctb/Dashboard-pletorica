# Dashboard Architecture

## Scope

Usar esta referencia cuando el trabajo sea dentro de este repo y haya que decidir dónde tocar código, cómo extender una feature o cómo mantener consistencia entre capas.

## Project Snapshot

- Runtime principal: Python `>=3.10,<4.0`.
- Framework UI: `reflex >=0.8.21,<0.9.0` en `pyproject.toml`.
- Layout de alto nivel: app Reflex en `app/app.py`.
- Patrón dominante: dominio y acceso a datos fuera de UI; presentación separada por páginas y componentes.

## Main Directories

### `app/app.py`

- Registrar la app Reflex.
- Definir tema, wrappers de layout y rutas con `app.add_page(...)`.
- Distinguir rutas de backoffice y portal.

### `app/entities/`

- Reunir entidades, DTOs y modelos compartidos por dominio.
- Mantener aquí estructuras que no deben depender de Reflex.

### `app/services/`

- Concentrar consultas, coordinación con Supabase, armado de reportes y reglas de aplicación.
- Preferir que la presentación consuma servicios antes que hablar directo con infraestructura.

### `app/presentation/`

- Contener páginas, estados, layouts y componentes visuales del backoffice.
- Organizar por módulo funcional.

### `app/presentation/portal/`

- Contener el portal y sus páginas específicas.
- Seguir la misma idea de separación entre page, state y components.

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

- Backoffice: las páginas suelen entrar mediante `index(...)`.
- Portal: las páginas suelen entrar mediante `portal_index(...)`.
- La ruta declarada en `app/app.py` es la referencia final para navegación.
- Si una página parece no renderizar, revisar primero import, wrapper y `app.add_page(...)`.

## Feature Placement Guide

Si el cambio es visual:
- Tocar `page.py`, `components.py` o componentes reutilizables.

Si el cambio es de interacción:
- Tocar el `state.py` del módulo y sus handlers.

Si el cambio es de negocio, persistencia o agregación:
- Tocar `services/`.

Si el cambio altera contratos o forma de los datos:
- Tocar `entities/`, `api/` o ambos.

## Working Style for This Repo

- Buscar primero si ya existe un patrón equivalente en otro módulo.
- Copiar la forma, no solo el resultado visual.
- Mantener nombres y estructura por módulo: `page.py`, `state.py`, `components.py`, `modal.py`, `paso_*.py` cuando aplique.
- Mantener mensajes, loaders y toasts consistentes con los helpers base.
- Evitar introducir una librería o abstracción nueva si el repo ya resolvió ese problema con código propio.

## Fast Checks

1. `rg -n "app.add_page\\(" app/app.py`
2. `rg -n "class .*State\\(" app/presentation app/presentation/portal`
3. `rg -n "BaseState|CRUDStateMixin|AuthState" app`
4. `rg -n "toast|on_mount|model_dump" app`
