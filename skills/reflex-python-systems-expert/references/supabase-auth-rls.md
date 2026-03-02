# Supabase Auth and RLS

## Scope

Usar esta referencia cuando el trabajo toque autenticación, sesión, usuarios, roles, empresas asignadas, storage, clientes de Supabase o Row Level Security.

## Client Model

- `db_manager.get_client()` usa `SUPABASE_SERVICE_KEY` si existe.
- Cuando hay `service_role`, el backend bypasea RLS.
- `db_manager.get_anon_client()` usa `SUPABASE_KEY` y sirve para auth del usuario y flujos sujetos a sesión.
- No asumir que una query backend ya está protegida por RLS; revisar siempre el cliente usado.

## Security Consequences

- Si una operación usa `get_client()`, proteger con validaciones de rol, permisos y empresa desde services/state.
- RLS sigue siendo importante para acceso directo desde API REST o SDK del cliente, pero no reemplaza autorización backend cuando existe `service_role`.
- Creación de usuarios, reseteo de password y operaciones administrativas requieren atención especial porque usan cliente privilegiado.

## AuthState Pattern

- Los módulos protegidos deben heredar de `AuthState`, no de `BaseState`.
- `AuthState` concentra:
  - JWT (`_access_token`, `_refresh_token`, expiración)
  - `usuario_actual`
  - `empresa_actual`
  - `empresas_disponibles`
  - helpers de rol y permisos
- Si el cambio es portal, revisar también `PortalState`.
- Si `Config.SKIP_AUTH=True`, el sistema relaja login para desarrollo; no diseñar reglas de producción asumiendo ese modo.

## Roles and Access

Roles observados en el repo:

- `superadmin`
- `admin`
- `institucion`
- `proveedor`
- `client`
- `empleado`

Reglas relevantes:

- `institucion` usa `institucion_id`; no usa `user_companies`.
- `proveedor` y `client` requieren empresas asignadas.
- `admin`, `superadmin` y `empleado` no deben recibir asignaciones de empresa en `UserService.crear_usuario(...)`.
- Permisos granulares viven en una matriz `permisos = {modulo: {operar, autorizar}}`.
- `puede_gestionar_usuarios` distingue capacidades de superadministración.

## Portal vs Backoffice

- Login redirige por rol.
- El portal está pensado para usuarios de empresa o acceso equivalente acotado.
- El backoffice requiere verificar auth y permisos por módulo.
- Si una página nueva expone datos de empresa, confirmar si pertenece a `/portal/*` o al backoffice antes de crearla.

## Storage

- El repo ya interactúa con Supabase Storage.
- Antes de agregar uploads o deletes:
  - revisar si existe repository/servicio para archivos
  - revisar bucket y naming de ruta
  - revisar si la visibilidad debe quedar pública o privada
- Evitar duplicar acceso directo a `storage.from_(...)` desde páginas si ya hay encapsulación.

## RLS Checklist

Antes de cerrar un cambio sensible:

1. Confirmar qué cliente Supabase usa el flujo.
2. Confirmar si la autorización se valida en service/state además de RLS.
3. Confirmar que el rol y la empresa actual limitan la consulta correcta.
4. Confirmar que `SKIP_AUTH` no enmascara un fallo de autorización.
5. Si el cambio depende de políticas SQL, revisar `documentacion/RLS_VERIFICATION.md`.
