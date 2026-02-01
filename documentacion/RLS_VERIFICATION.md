# RLS Verification Guide

Guia para verificar que Row Level Security esta funcionando correctamente
despues de ejecutar la migracion `016_apply_rls_business_tables.sql`.

## 1. Verificar que RLS esta habilitado

Ejecutar en **Supabase SQL Editor**:

```sql
SELECT
    tablename,
    rowsecurity AS rls_enabled
FROM pg_tables
WHERE schemaname = 'public'
AND tablename IN (
    'empresas', 'empleados', 'contratos', 'requisicion',
    'contrato_categorias', 'plazas', 'historial_laboral',
    'tipos_servicio', 'categorias_puesto', 'lugar_entrega',
    'archivo_sistema',
    'user_profiles', 'user_companies',
    'sedes', 'contactos_buap'
)
ORDER BY tablename;
```

**Resultado esperado:** Todas las tablas deben mostrar `rls_enabled = true`.

## 2. Listar politicas creadas

```sql
SELECT
    tablename,
    policyname,
    cmd,
    permissive
FROM pg_policies
WHERE schemaname = 'public'
ORDER BY tablename, cmd;
```

**Resultado esperado:** 4 politicas por tabla de negocio (SELECT, INSERT, UPDATE, DELETE).

Conteo esperado por tabla:

| Tabla | Politicas |
|-------|-----------|
| empresas | 4 |
| empleados | 4 |
| contratos | 4 |
| requisicion | 4 |
| contrato_categorias | 4 |
| plazas | 4 |
| historial_laboral | 4 |
| tipos_servicio | 4 |
| categorias_puesto | 4 |
| lugar_entrega | 4 |
| archivo_sistema | 4 |
| user_profiles | 4 |
| user_companies | 4 |
| sedes | 2 (permisivo) |
| contactos_buap | 2 (permisivo) |

## 3. Probar acceso por rol

### Preparacion: Crear usuarios de prueba

```sql
-- 1. Crear usuario admin en Supabase Auth (Dashboard > Authentication > Users)
--    Email: admin-test@buap.mx / Password: Test1234!

-- 2. Crear usuario client en Supabase Auth
--    Email: client-test@empresa.mx / Password: Test1234!

-- 3. Asignar perfiles (ejecutar con service_role o como superuser)
INSERT INTO public.user_profiles (id, rol, nombre_completo, activo)
VALUES
    ('<UUID_ADMIN>', 'admin', 'Admin Test', true),
    ('<UUID_CLIENT>', 'client', 'Client Test', true);

-- 4. Asignar empresa al client (asumiendo empresa con id=1)
INSERT INTO public.user_companies (user_id, empresa_id, es_principal)
VALUES ('<UUID_CLIENT>', 1, true);
```

### Test A: Admin ve todas las empresas

```sql
-- Ejecutar como admin (usar el JWT del admin en Supabase)
-- O simular con set_config:

-- En SQL Editor como superuser:
SELECT set_config('request.jwt.claim.sub', '<UUID_ADMIN>', true);

-- Debe retornar TODAS las empresas
SELECT count(*) FROM empresas;
```

### Test B: Client ve solo sus empresas

```sql
-- Simular como client:
SELECT set_config('request.jwt.claim.sub', '<UUID_CLIENT>', true);

-- Debe retornar solo empresas asignadas al client
SELECT count(*) FROM empresas;
-- Esperado: 1 (solo la empresa con id=1)
```

### Test C: Client no puede insertar en tablas de solo-admin

```sql
-- Como client, intentar crear un contrato
-- Debe fallar con error de RLS
INSERT INTO contratos (codigo, empresa_id, tipo_servicio_id, fecha_inicio)
VALUES ('TEST-001', 1, 1, '2025-01-01');
-- Esperado: ERROR - new row violates row-level security policy
```

### Test D: Client puede insertar empleados de su empresa

```sql
-- Como client con empresa_id=1
INSERT INTO empleados (clave, empresa_id, curp, nombre, apellido_paterno)
VALUES ('T25-00001', 1, 'TESTCURP12345678', 'Test', 'Empleado');
-- Esperado: OK (empresa_id=1 esta en sus empresas)

-- Intentar insertar en otra empresa
INSERT INTO empleados (clave, empresa_id, curp, nombre, apellido_paterno)
VALUES ('T25-00002', 999, 'TESTCURP99999999', 'Otro', 'Empleado');
-- Esperado: ERROR - new row violates row-level security policy
```

### Test E: Catalogos accesibles para todos los autenticados

```sql
-- Como client:
SELECT count(*) FROM tipos_servicio;
-- Esperado: retorna todos los registros

-- Intentar insertar
INSERT INTO tipos_servicio (nombre) VALUES ('Test');
-- Esperado: ERROR (solo admin)
```

### Test F: Archivos segun entidad

```sql
-- Como client con empresa_id=1:
-- Si hay una requisicion de empresa 1 con archivos adjuntos
SELECT a.*
FROM archivo_sistema a
WHERE a.entidad_tipo = 'REQUISICION';
-- Esperado: solo archivos de requisiciones de empresa 1

-- Archivos de tipo REPORTE
SELECT * FROM archivo_sistema WHERE entidad_tipo = 'REPORTE';
-- Esperado: 0 filas (REPORTE solo visible para admin)
```

## 4. Verificar que service_role bypasea RLS

```sql
-- Usar la service_role key en el client de Supabase
-- (esto es lo que hace el backend para operaciones admin)

-- Con service_role key, TODAS las filas deben ser visibles
-- independientemente del usuario
SELECT count(*) FROM empresas;  -- Todas
SELECT count(*) FROM empleados;  -- Todos
```

Nota: En el codigo Python, las operaciones que usan `db_manager.get_client()`
con la `SUPABASE_SERVICE_KEY` bypasean RLS automaticamente.

## 5. Verificar performance

```sql
-- Verificar que las politicas usan indices
EXPLAIN ANALYZE
SELECT * FROM empleados WHERE empresa_id = 1;

-- Verificar subquery de plazas (la mas compleja)
EXPLAIN ANALYZE
SELECT * FROM plazas LIMIT 10;

-- Verificar archivo_sistema con funcion polimorfica
EXPLAIN ANALYZE
SELECT * FROM archivo_sistema WHERE entidad_tipo = 'REQUISICION' LIMIT 10;
```

**Que buscar:**
- `Index Scan` o `Index Only Scan` en los planes de ejecucion
- Tiempos de ejecucion < 50ms para tablas con < 10k filas
- No deberia haber `Seq Scan` en tablas grandes

## 6. Verificar funciones helper

```sql
-- Verificar is_admin() como admin
SELECT set_config('request.jwt.claim.sub', '<UUID_ADMIN>', true);
SELECT is_admin();  -- Esperado: true

-- Verificar is_admin() como client
SELECT set_config('request.jwt.claim.sub', '<UUID_CLIENT>', true);
SELECT is_admin();  -- Esperado: false

-- Verificar get_user_companies() como client
SELECT get_user_companies();  -- Esperado: {1} (array con empresa asignada)

-- Verificar can_access_archivo()
SELECT can_access_archivo('REQUISICION', 1);  -- Depende de si requisicion 1 es de empresa 1
SELECT can_access_archivo('REPORTE', 1);  -- Esperado: false (solo admin)
```

## Troubleshooting

### "new row violates row-level security policy"

**Causa:** El usuario intenta una operacion que la politica no permite.

**Solucion:**
1. Verificar el rol del usuario: `SELECT rol FROM user_profiles WHERE id = auth.uid();`
2. Verificar empresas asignadas: `SELECT get_user_companies();`
3. Verificar que la empresa del registro esta en la lista
4. Si es operacion admin, verificar que se usa `service_role` key

### "permission denied for table X"

**Causa:** Diferente de RLS. Esto es un problema de permisos de PostgreSQL (GRANT).

**Solucion:**
```sql
GRANT SELECT, INSERT, UPDATE, DELETE ON public.{tabla} TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.{tabla} TO anon;
```

### Queries lentas despues de habilitar RLS

**Causa:** Las politicas ejecutan subqueries sin indices.

**Solucion:**
1. Ejecutar `EXPLAIN ANALYZE` en la query lenta
2. Verificar que los indices de la migracion 016 existen:
```sql
SELECT indexname, tablename
FROM pg_indexes
WHERE schemaname = 'public'
AND indexname LIKE 'idx_%'
ORDER BY tablename;
```
3. Si faltan indices, crearlos manualmente

### Client no ve datos que deberia ver

**Pasos de diagnostico:**
```sql
-- 1. Verificar que el usuario tiene perfil
SELECT * FROM user_profiles WHERE id = '<UUID>';

-- 2. Verificar que tiene empresas asignadas
SELECT * FROM user_companies WHERE user_id = '<UUID>';

-- 3. Verificar que la empresa esta activa
SELECT id, estatus FROM empresas WHERE id = <EMPRESA_ID>;

-- 4. Verificar que el dato pertenece a esa empresa
-- (ejemplo para empleados)
SELECT empresa_id FROM empleados WHERE id = <EMPLEADO_ID>;
```

### Admin no puede ver datos

**Causa probable:** El perfil del admin no tiene `rol = 'admin'` o `activo = false`.

```sql
SELECT id, rol, activo FROM user_profiles WHERE id = '<UUID>';
-- Debe mostrar: rol = 'admin', activo = true
```

### Tablas sin RLS (acceso abierto)

Las siguientes tablas NO tienen RLS habilitado y son accesibles sin restricciones:

| Tabla | FK a empresa | Riesgo |
|-------|-------------|--------|
| pagos | via contrato_id -> contratos | Medio: datos financieros visibles |
| requisicion_item | via requisicion_id -> requisicion | Bajo: items de requisicion |
| requisicion_partida | via requisicion_id -> requisicion | Bajo: partidas de requisicion |
| configuracion_requisicion | ninguna (config global) | Bajo: valores default |

Para protegerlas, crear una migracion adicional siguiendo el mismo patron
de la 016 (ver seccion 12 del SQL).
