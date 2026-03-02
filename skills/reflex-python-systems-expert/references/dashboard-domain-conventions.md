# Dashboard Domain Conventions

## Scope

Usar esta referencia cuando el cambio toque dominio laboral/fiscal, naming reusable, contratos UI o la separación entre portal y backoffice.

## Naming Rules

- Inglés para componentes técnicos y genéricos.
- Español para texto visible al usuario.
- Conservar términos canónicos del negocio MX: `curp`, `rfc`, `nss`, `cfdi`, `estatus`.
- No mezclar idiomas en el mismo identificador.

Sufijos canónicos para reusables:

- `_field`
- `_row`
- `_section`
- `_modal`
- `_body`
- `_table`
- `_list`
- `_shell`
- `_kit`

## Reusable Contract Rules

- Extraer solo con 2+ usos reales o con transversalidad clara.
- Separar shell visual de lógica de negocio.
- Mantener wrappers o compatibilidad si se reemplaza un reusable existente.
- Documentar variaciones con `mode`, `variant` o `profile` antes de duplicar componentes.

## Portal and Backoffice Boundaries

- Backoffice usa wrappers y permisos más amplios.
- Portal usa `portal_index(...)`, `PortalState` y alcance limitado por empresa/rol.
- No copiar una feature del backoffice al portal sin revisar reducción de permisos, visibilidad y navegación.
- Si agregas una página al portal, revisar también el sidebar y el `on_mount` con validación portal.

## Domain Vocabulary

Entidades y flujos recurrentes del repo:

- empresas
- empleados
- contratos
- requisiciones
- entregables
- pagos
- plazas
- historial laboral
- onboarding
- sedes
- instituciones

Regla práctica:

- Si el cambio toca una de estas áreas, buscar primero DTOs, resúmenes, enums y servicios ya existentes antes de crear nuevas estructuras.

## Fiscal and Labor Domain

- Existen catálogos especializados en `app/core/catalogs/` para:
  - `UMA`
  - `IMSS`
  - `ISR`
  - `ISN`
  - `INFONAVIT`
  - prestaciones laborales
  - vacaciones
- Existen cálculos especializados en `app/core/calculations/`.
- Mantener tasas y fórmulas en catálogos/cálculos, no hardcodearlas en states, páginas o modales.
- Si una pantalla necesita mostrar resultados fiscales, consumir salidas de cálculo ya estructuradas o delegar el armado al servicio.

## User and Permission Domain

- `UserProfile` extiende `auth.users`.
- `user_profiles` concentra rol, nombre, teléfono, institución y permisos.
- `user_companies` representa acceso de usuarios a empresas.
- La matriz de permisos por módulo forma parte del contrato del dominio; no inventar flags paralelos si esa matriz ya cubre el caso.

## Practical Checklist

1. El nombre del componente/state sigue la convención del repo.
2. El cambio respeta la frontera portal/backoffice.
3. La lógica de negocio vive en service/calculation/catalog, no en UI.
4. Los términos del dominio se mantienen consistentes.
5. Los permisos se leen del modelo/capa de auth existente, no de flags ad hoc.
