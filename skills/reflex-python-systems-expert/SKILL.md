---
name: reflex-python-systems-expert
description: Diseñar, implementar, depurar, refactorizar y revisar aplicaciones Reflex con criterio fuerte de Python, Supabase y arquitectura de sistemas. Use when Codex needs to work on Reflex pages, rx.State, event handlers, routing, forms, tables, auth, async flows, serialization, performance, reusable UI contracts, Supabase clients, RLS, role-based access, or labor/fiscal domain logic in Python projects organized as entities, services, presentation, repositories, and API layers like this dashboard.
---

# Reflex Python Systems Expert

## Overview

Resolver trabajo en apps Reflex sin perder la disciplina de arquitectura: UI declarativa en componentes, mutaciones en estado, reglas de negocio en servicios y modelos/contratos fuera de la capa visual.

Priorizar consistencia con la documentación oficial de Reflex y con la estructura real de este repo. Leer `references/reflex-guidelines.md` para reglas del framework y `references/dashboard-architecture.md` para el mapa local.

Activar referencias según el tipo de cambio:

- Leer `references/supabase-auth-rls.md` si el trabajo toca login, usuarios, empresas asignadas, permisos, storage, clientes Supabase o seguridad de acceso.
- Leer `references/dashboard-domain-conventions.md` si el trabajo toca naming reusable, portal/backoffice, contratos, entregables, requisiciones, empleados o cálculos fiscales/laborales.

## Workflow

1. Construir mapa de impacto antes de editar.
   Leer `pyproject.toml`, `app/app.py` y los archivos concretos de la feature.
   Ubicar si el cambio cae en `entities/`, `services/`, `presentation/` o `api/`.
2. Elegir la capa correcta para cada cambio.
   Poner composición visual en componentes/páginas.
   Poner mutación de estado, loading, modales y toasts en `rx.State`.
   Poner reglas de negocio, consultas y coordinación externa en servicios.
   Poner validaciones/modelos compartidos en entidades o contratos.
3. Implementar con patrones de Reflex acordes al alcance.
   Mantener el estado serializable.
   Mantener `@rx.var` puro y derivado.
   Mantener handlers y helpers separados.
4. Verificar integridad del flujo completo.
   Revisar imports, `app.add_page(...)`, guards de autenticación, defaults de formulario, estados de loading y manejo de errores.
5. Validar con el método más barato posible.
   Empezar con lectura estática y tests puntuales.
   Ejecutar `pytest` o `poetry run reflex run` solo si hace falta confirmar comportamiento.

## Reflex Rules

- Tratar cada página y componente como una función Python que describe UI; no esconder lógica de negocio dentro del render.
- Modificar vars solo desde event handlers. No mutar estado en helpers de render.
- Usar `@rx.event` cuando el handler reciba argumentos o cuando convenga reforzar tipado y claridad.
- Usar métodos con prefijo `_` como helpers internos del estado cuando no deban exponerse como triggers.
- Mantener substates planos. Separar estados por página o feature antes de crear jerarquías profundas.
- Reservar `rx.ComponentState` para widgets reutilizables que deban vivir de forma independiente; no usarlo para flujos de página amplios.
- Evitar guardar objetos no serializables en el estado. Convertir resultados complejos a `dict`, `list`, `str`, `int`, `float`, `bool` o modelos volcados.
- Mantener `@rx.var` barato y sin efectos secundarios. Si depende de mucho estado, reconsiderar la frontera del state.

## Architecture Rules

- Preservar la separación `entities -> services -> presentation -> api`.
- Preservar también `repositories` cuando el módulo ya usa ese nivel para encapsular acceso a Supabase o storage.
- Evitar que un componente consulte directamente Supabase, HTTP o reglas fiscales; eso pertenece a `services/`.
- Evitar duplicar validaciones si ya existe mixin, helper o servicio reusable.
- Preferir extensión de patrones existentes sobre introducir una abstracción nueva para un solo caso.
- Si un módulo ya usa `BaseState`, `CRUDStateMixin` o `AuthState`, integrarse con esas bases antes de inventar otro ciclo de vida.

## Security and Supabase Rules

- Asumir que `db_manager.get_client()` usa `service_role` cuando está disponible; eso bypasea RLS.
- No confiar en RLS para proteger operaciones backend ejecutadas con `service_role`; reforzar permisos y filtros en services/state.
- Usar `db_manager.get_anon_client()` para flujos de autenticación y validación de sesión del usuario.
- Tratar creación de usuarios, resets y operaciones privilegiadas como rutas de alto riesgo; validar rol, permisos y precondiciones explícitamente.
- Si un módulo protegido no hereda de `AuthState` o `PortalState`, corregir eso antes de agregar más lógica.
- Si el cambio toca archivos, revisar si ya existe un repository o contrato de storage antes de escribir acceso directo a buckets.

## Domain Rules

- Mantener el vocabulario canónico del dominio mexicano: `curp`, `rfc`, `nss`, `cfdi`, `estatus`, `IMSS`, `ISR`, `ISN`, `INFONAVIT`, `UMA`.
- No mover cálculos fiscales o laborales a la UI; usar `app/core/catalogs/` y `app/core/calculations/`.
- Si el cambio toca contratos, entregables, pagos, empleados o plazas, verificar si la entidad ya define DTOs/resúmenes útiles antes de crear dicts nuevos.
- Si el cambio toca portal de cliente, recordar que el portal es de acceso acotado por empresa/rol y no debe replicar capacidades de backoffice.
- Mantener inglés en reusables técnicos y español en textos visibles, siguiendo la guía del repo.

## Common Tasks

### Crear o extender una página

1. Ubicar la página y su state actual.
2. Revisar la ruta en `app/app.py`.
3. Añadir solo el estado necesario para la UI.
4. Delegar fetch o persistencia a servicios.
5. Conectar `on_mount`, handlers y feedback visual de forma consistente.

### Corregir formularios o CRUD

1. Revisar si el módulo ya hereda de `CRUDStateMixin` o `BaseState`.
2. Mantener setters explícitos para los campos que Reflex necesita observar.
3. Limpiar errores al cambiar inputs y limpiar formularios al abrir/cerrar modales.
4. Centralizar mensajes y toasts en el state, no en los componentes.

### Revisar rendimiento o complejidad

1. Medir cuántas responsabilidades vive en un mismo state.
2. Reducir computed vars costosas o demasiado acopladas.
3. Dividir por feature antes de introducir jerarquías profundas de substates.
4. Sacar lógica pesada de handlers si realmente pertenece a servicios.

## Repo-Specific Heuristics

- Tomar `app/app.py` como la fuente de verdad para rutas y wrappers de layout.
- En backoffice, validar si la página entra por `index(...)`; en portal, validar si entra por `portal_index(...)`.
- Reusar patrones del repo para skeletons, toasts, paginación, filtros y modales antes de crear componentes nuevos.
- Si aparece una tensión entre `README.md` y `pyproject.toml`, usar `pyproject.toml` y el código real como referencia operativa.
- Cuando un resultado de servicio llegue como modelo Pydantic, convertirlo con `model_dump()` antes de persistirlo en state si eso evita problemas de serialización.
- Si el módulo es autenticado, revisar `AuthState` antes de crear flags locales de rol o sesión.
- Si el cambio es portal, revisar `PortalState` y la documentación de integración antes de registrar rutas.
- Si el cambio afecta usuarios o permisos, revisar el contrato de `UserProfile` y las reglas de `UserService`.
- Si el cambio afecta módulos reusables, respetar sufijos `_field`, `_section`, `_modal`, `_table`, `_list`, `_shell`, `_kit`.

## Useful Searches

- `rg -n "class .*State\\(" app/presentation`
- `rg -n "@rx.var|@rx.event" app`
- `rg -n "app.add_page\\(" app/app.py`
- `rg -n "BaseState|CRUDStateMixin|AuthState" app`
- `rg -n "model_dump\\(" app`
- `rg -n "get_client|get_anon_client|service_role|RLS|storage.from_" app`
- `rg -n "rol|permisos|puede_gestionar_usuarios|empresa_actual" app`
- `rg -n "IMSS|ISR|ISN|INFONAVIT|UMA|prestaciones|vacaciones" app/core app/entities app/services`

## References

- Leer `references/reflex-guidelines.md` para decisiones de framework.
- Leer `references/dashboard-architecture.md` para navegación del repo y patrones ya existentes.
- Leer `references/supabase-auth-rls.md` para seguridad, clientes y roles.
- Leer `references/dashboard-domain-conventions.md` para naming, dominio y reglas del portal.
