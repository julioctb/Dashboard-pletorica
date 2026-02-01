-- ============================================================================
-- Migration: 016_apply_rls_business_tables.sql
-- Fecha: 2025-02-01
-- Descripcion: Aplica Row Level Security a tablas de negocio para
--              aislamiento de datos por empresa/tenant
--
-- Prerrequisitos:
--   - Migracion 015 ejecutada (user_profiles, user_companies, funciones helper)
--   - Funciones is_admin() y get_user_companies() disponibles
--
-- Tablas afectadas:
--   1. empresas           (FK directa: id)
--   2. empleados          (FK directa: empresa_id)
--   3. contratos          (FK directa: empresa_id)
--   4. requisicion        (FK directa: empresa_id)
--   5. contrato_categorias (FK indirecta: contrato -> empresa)
--   6. plazas             (FK indirecta: contrato_categoria -> contrato -> empresa)
--   7. historial_laboral  (FK indirecta: empleado -> empresa)
--   8. tipos_servicio     (Catalogo global)
--   9. categorias_puesto  (Catalogo global)
--  10. lugar_entrega      (Catalogo global)
--  11. archivo_sistema    (Polimorfica: entidad_tipo + entidad_id)
--
-- Patron de acceso:
--   - Admin: acceso total a todos los registros
--   - Client: solo registros de empresas asignadas via user_companies
--   - No autenticado: sin acceso
--
-- Funciones helper utilizadas (creadas en migracion 015):
--   - is_admin()            -> BOOLEAN (STABLE SECURITY DEFINER)
--   - get_user_companies()  -> INTEGER[] (STABLE SECURITY DEFINER)
-- ============================================================================


-- ============================================================================
-- 1. EMPRESAS
-- ============================================================================
-- Relacion: id ES el empresa_id
-- Admin ve todas, client solo las asignadas en user_companies

ALTER TABLE public.empresas ENABLE ROW LEVEL SECURITY;

-- SELECT: Admin ve todas, client solo sus empresas asignadas
DROP POLICY IF EXISTS "empresas_select" ON public.empresas;
CREATE POLICY "empresas_select"
ON public.empresas FOR SELECT
USING (
    is_admin()
    OR id = ANY(get_user_companies())
);

-- INSERT: Solo admin puede crear empresas
DROP POLICY IF EXISTS "empresas_insert" ON public.empresas;
CREATE POLICY "empresas_insert"
ON public.empresas FOR INSERT
WITH CHECK (is_admin());

-- UPDATE: Solo admin puede modificar empresas
DROP POLICY IF EXISTS "empresas_update" ON public.empresas;
CREATE POLICY "empresas_update"
ON public.empresas FOR UPDATE
USING (is_admin());

-- DELETE: Solo admin puede eliminar empresas
DROP POLICY IF EXISTS "empresas_delete" ON public.empresas;
CREATE POLICY "empresas_delete"
ON public.empresas FOR DELETE
USING (is_admin());


-- ============================================================================
-- 2. EMPLEADOS
-- ============================================================================
-- Relacion: empresa_id (FK directa a empresas)
-- Admin ve todos, client ve empleados de sus empresas
-- Client puede crear/editar empleados de sus empresas

ALTER TABLE public.empleados ENABLE ROW LEVEL SECURITY;

-- SELECT: Admin ve todos, client solo de sus empresas
DROP POLICY IF EXISTS "empleados_select" ON public.empleados;
CREATE POLICY "empleados_select"
ON public.empleados FOR SELECT
USING (
    is_admin()
    OR empresa_id = ANY(get_user_companies())
);

-- INSERT: Admin o client de esa empresa
DROP POLICY IF EXISTS "empleados_insert" ON public.empleados;
CREATE POLICY "empleados_insert"
ON public.empleados FOR INSERT
WITH CHECK (
    is_admin()
    OR empresa_id = ANY(get_user_companies())
);

-- UPDATE: Admin o client de esa empresa
DROP POLICY IF EXISTS "empleados_update" ON public.empleados;
CREATE POLICY "empleados_update"
ON public.empleados FOR UPDATE
USING (
    is_admin()
    OR empresa_id = ANY(get_user_companies())
);

-- DELETE: Solo admin
DROP POLICY IF EXISTS "empleados_delete" ON public.empleados;
CREATE POLICY "empleados_delete"
ON public.empleados FOR DELETE
USING (is_admin());


-- ============================================================================
-- 3. CONTRATOS
-- ============================================================================
-- Relacion: empresa_id (FK directa a empresas)
-- Admin ve todos, client ve contratos de sus empresas
-- Solo admin puede crear/modificar/eliminar contratos

ALTER TABLE public.contratos ENABLE ROW LEVEL SECURITY;

-- SELECT: Admin ve todos, client solo de sus empresas
DROP POLICY IF EXISTS "contratos_select" ON public.contratos;
CREATE POLICY "contratos_select"
ON public.contratos FOR SELECT
USING (
    is_admin()
    OR empresa_id = ANY(get_user_companies())
);

-- INSERT: Solo admin
DROP POLICY IF EXISTS "contratos_insert" ON public.contratos;
CREATE POLICY "contratos_insert"
ON public.contratos FOR INSERT
WITH CHECK (is_admin());

-- UPDATE: Solo admin
DROP POLICY IF EXISTS "contratos_update" ON public.contratos;
CREATE POLICY "contratos_update"
ON public.contratos FOR UPDATE
USING (is_admin());

-- DELETE: Solo admin
DROP POLICY IF EXISTS "contratos_delete" ON public.contratos;
CREATE POLICY "contratos_delete"
ON public.contratos FOR DELETE
USING (is_admin());


-- ============================================================================
-- 4. REQUISICION
-- ============================================================================
-- Relacion: empresa_id (FK directa a empresas, nullable)
-- Admin ve todas, client solo de sus empresas
-- Client puede crear/editar requisiciones de sus empresas

ALTER TABLE public.requisicion ENABLE ROW LEVEL SECURITY;

-- SELECT: Admin ve todas, client solo de sus empresas
DROP POLICY IF EXISTS "requisicion_select" ON public.requisicion;
CREATE POLICY "requisicion_select"
ON public.requisicion FOR SELECT
USING (
    is_admin()
    OR empresa_id = ANY(get_user_companies())
);

-- INSERT: Admin o client de esa empresa
DROP POLICY IF EXISTS "requisicion_insert" ON public.requisicion;
CREATE POLICY "requisicion_insert"
ON public.requisicion FOR INSERT
WITH CHECK (
    is_admin()
    OR empresa_id = ANY(get_user_companies())
);

-- UPDATE: Admin o client de esa empresa
DROP POLICY IF EXISTS "requisicion_update" ON public.requisicion;
CREATE POLICY "requisicion_update"
ON public.requisicion FOR UPDATE
USING (
    is_admin()
    OR empresa_id = ANY(get_user_companies())
);

-- DELETE: Solo admin
DROP POLICY IF EXISTS "requisicion_delete" ON public.requisicion;
CREATE POLICY "requisicion_delete"
ON public.requisicion FOR DELETE
USING (is_admin());


-- ============================================================================
-- 5. CONTRATO_CATEGORIAS
-- ============================================================================
-- Relacion indirecta: contrato_categorias -> contratos.empresa_id
-- Admin ve todas, client ve las de contratos de sus empresas
-- Solo admin puede escribir

ALTER TABLE public.contrato_categorias ENABLE ROW LEVEL SECURITY;

-- SELECT: Admin ve todas, client via contrato -> empresa
DROP POLICY IF EXISTS "contrato_categorias_select" ON public.contrato_categorias;
CREATE POLICY "contrato_categorias_select"
ON public.contrato_categorias FOR SELECT
USING (
    is_admin()
    OR contrato_id IN (
        SELECT id FROM public.contratos
        WHERE empresa_id = ANY(get_user_companies())
    )
);

-- INSERT: Solo admin
DROP POLICY IF EXISTS "contrato_categorias_insert" ON public.contrato_categorias;
CREATE POLICY "contrato_categorias_insert"
ON public.contrato_categorias FOR INSERT
WITH CHECK (is_admin());

-- UPDATE: Solo admin
DROP POLICY IF EXISTS "contrato_categorias_update" ON public.contrato_categorias;
CREATE POLICY "contrato_categorias_update"
ON public.contrato_categorias FOR UPDATE
USING (is_admin());

-- DELETE: Solo admin
DROP POLICY IF EXISTS "contrato_categorias_delete" ON public.contrato_categorias;
CREATE POLICY "contrato_categorias_delete"
ON public.contrato_categorias FOR DELETE
USING (is_admin());


-- ============================================================================
-- 6. PLAZAS
-- ============================================================================
-- Relacion indirecta (2 niveles):
--   plazas.contrato_categoria_id -> contrato_categorias.contrato_id -> contratos.empresa_id
-- Admin ve todas, client ve las de contratos de sus empresas
-- Solo admin puede escribir (asignacion de empleado via service_role)

ALTER TABLE public.plazas ENABLE ROW LEVEL SECURITY;

-- SELECT: Admin ve todas, client via contrato_categoria -> contrato -> empresa
DROP POLICY IF EXISTS "plazas_select" ON public.plazas;
CREATE POLICY "plazas_select"
ON public.plazas FOR SELECT
USING (
    is_admin()
    OR contrato_categoria_id IN (
        SELECT cc.id
        FROM public.contrato_categorias cc
        JOIN public.contratos c ON cc.contrato_id = c.id
        WHERE c.empresa_id = ANY(get_user_companies())
    )
);

-- INSERT: Solo admin
DROP POLICY IF EXISTS "plazas_insert" ON public.plazas;
CREATE POLICY "plazas_insert"
ON public.plazas FOR INSERT
WITH CHECK (is_admin());

-- UPDATE: Solo admin (asignacion de empleado se hace via service_role key)
DROP POLICY IF EXISTS "plazas_update" ON public.plazas;
CREATE POLICY "plazas_update"
ON public.plazas FOR UPDATE
USING (is_admin());

-- DELETE: Solo admin
DROP POLICY IF EXISTS "plazas_delete" ON public.plazas;
CREATE POLICY "plazas_delete"
ON public.plazas FOR DELETE
USING (is_admin());


-- ============================================================================
-- 7. HISTORIAL_LABORAL
-- ============================================================================
-- Relacion indirecta: historial_laboral.empleado_id -> empleados.empresa_id
-- Admin ve todo, client ve historial de empleados de sus empresas
-- Solo admin/sistema puede escribir

ALTER TABLE public.historial_laboral ENABLE ROW LEVEL SECURITY;

-- SELECT: Admin ve todo, client via empleado -> empresa
DROP POLICY IF EXISTS "historial_laboral_select" ON public.historial_laboral;
CREATE POLICY "historial_laboral_select"
ON public.historial_laboral FOR SELECT
USING (
    is_admin()
    OR empleado_id IN (
        SELECT id FROM public.empleados
        WHERE empresa_id = ANY(get_user_companies())
    )
);

-- INSERT: Solo admin (sistema usa service_role)
DROP POLICY IF EXISTS "historial_laboral_insert" ON public.historial_laboral;
CREATE POLICY "historial_laboral_insert"
ON public.historial_laboral FOR INSERT
WITH CHECK (is_admin());

-- UPDATE: Solo admin
DROP POLICY IF EXISTS "historial_laboral_update" ON public.historial_laboral;
CREATE POLICY "historial_laboral_update"
ON public.historial_laboral FOR UPDATE
USING (is_admin());

-- DELETE: Solo admin
DROP POLICY IF EXISTS "historial_laboral_delete" ON public.historial_laboral;
CREATE POLICY "historial_laboral_delete"
ON public.historial_laboral FOR DELETE
USING (is_admin());


-- ============================================================================
-- 8. CATALOGOS GLOBALES
-- ============================================================================
-- tipos_servicio, categorias_puesto, lugar_entrega
-- Cualquier usuario autenticado puede leer, solo admin puede escribir

-- --- tipos_servicio ---

ALTER TABLE public.tipos_servicio ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "tipos_servicio_select" ON public.tipos_servicio;
CREATE POLICY "tipos_servicio_select"
ON public.tipos_servicio FOR SELECT
USING (auth.uid() IS NOT NULL);

DROP POLICY IF EXISTS "tipos_servicio_insert" ON public.tipos_servicio;
CREATE POLICY "tipos_servicio_insert"
ON public.tipos_servicio FOR INSERT
WITH CHECK (is_admin());

DROP POLICY IF EXISTS "tipos_servicio_update" ON public.tipos_servicio;
CREATE POLICY "tipos_servicio_update"
ON public.tipos_servicio FOR UPDATE
USING (is_admin());

DROP POLICY IF EXISTS "tipos_servicio_delete" ON public.tipos_servicio;
CREATE POLICY "tipos_servicio_delete"
ON public.tipos_servicio FOR DELETE
USING (is_admin());

-- --- categorias_puesto ---

ALTER TABLE public.categorias_puesto ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "categorias_puesto_select" ON public.categorias_puesto;
CREATE POLICY "categorias_puesto_select"
ON public.categorias_puesto FOR SELECT
USING (auth.uid() IS NOT NULL);

DROP POLICY IF EXISTS "categorias_puesto_insert" ON public.categorias_puesto;
CREATE POLICY "categorias_puesto_insert"
ON public.categorias_puesto FOR INSERT
WITH CHECK (is_admin());

DROP POLICY IF EXISTS "categorias_puesto_update" ON public.categorias_puesto;
CREATE POLICY "categorias_puesto_update"
ON public.categorias_puesto FOR UPDATE
USING (is_admin());

DROP POLICY IF EXISTS "categorias_puesto_delete" ON public.categorias_puesto;
CREATE POLICY "categorias_puesto_delete"
ON public.categorias_puesto FOR DELETE
USING (is_admin());

-- --- lugar_entrega ---

ALTER TABLE public.lugar_entrega ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "lugar_entrega_select" ON public.lugar_entrega;
CREATE POLICY "lugar_entrega_select"
ON public.lugar_entrega FOR SELECT
USING (auth.uid() IS NOT NULL);

DROP POLICY IF EXISTS "lugar_entrega_insert" ON public.lugar_entrega;
CREATE POLICY "lugar_entrega_insert"
ON public.lugar_entrega FOR INSERT
WITH CHECK (is_admin());

DROP POLICY IF EXISTS "lugar_entrega_update" ON public.lugar_entrega;
CREATE POLICY "lugar_entrega_update"
ON public.lugar_entrega FOR UPDATE
USING (is_admin());

DROP POLICY IF EXISTS "lugar_entrega_delete" ON public.lugar_entrega;
CREATE POLICY "lugar_entrega_delete"
ON public.lugar_entrega FOR DELETE
USING (is_admin());


-- ============================================================================
-- 9. ARCHIVO_SISTEMA (Polimorfica)
-- ============================================================================
-- Relacion polimorfica via entidad_tipo + entidad_id
-- La politica SELECT verifica acceso segun el tipo de entidad:
--   REQUISICION       -> requisicion.empresa_id
--   REQUISICION_ITEM  -> requisicion_item -> requisicion.empresa_id
--   CONTRATO          -> contratos.empresa_id
--   EMPLEADO          -> empleados.empresa_id
--   REPORTE           -> solo admin (sin tabla con empresa_id)
--   REPORTE_ACTIVIDAD -> solo admin (sin tabla con empresa_id)
--
-- INSERT: admin o client de la empresa correspondiente
-- UPDATE/DELETE: solo admin

ALTER TABLE public.archivo_sistema ENABLE ROW LEVEL SECURITY;

-- Funcion helper para verificar acceso a archivos segun entidad
-- Evita repetir la logica CASE en multiples politicas
CREATE OR REPLACE FUNCTION can_access_archivo(p_entidad_tipo VARCHAR, p_entidad_id INTEGER)
RETURNS BOOLEAN
LANGUAGE sql
STABLE
SECURITY DEFINER
AS $$
    SELECT
        CASE p_entidad_tipo
            -- Requisicion: verificar empresa_id directamente
            WHEN 'REQUISICION' THEN EXISTS (
                SELECT 1 FROM public.requisicion
                WHERE id = p_entidad_id
                AND empresa_id = ANY(get_user_companies())
            )
            -- Requisicion Item: via requisicion -> empresa
            WHEN 'REQUISICION_ITEM' THEN EXISTS (
                SELECT 1 FROM public.requisicion_item ri
                JOIN public.requisicion r ON ri.requisicion_id = r.id
                WHERE ri.id = p_entidad_id
                AND r.empresa_id = ANY(get_user_companies())
            )
            -- Contrato: verificar empresa_id directamente
            WHEN 'CONTRATO' THEN EXISTS (
                SELECT 1 FROM public.contratos
                WHERE id = p_entidad_id
                AND empresa_id = ANY(get_user_companies())
            )
            -- Empleado: verificar empresa_id directamente
            WHEN 'EMPLEADO' THEN EXISTS (
                SELECT 1 FROM public.empleados
                WHERE id = p_entidad_id
                AND empresa_id = ANY(get_user_companies())
            )
            -- Reportes: solo admin (no tienen relacion con empresa)
            WHEN 'REPORTE' THEN false
            WHEN 'REPORTE_ACTIVIDAD' THEN false
            -- Tipo desconocido: denegar
            ELSE false
        END;
$$;

COMMENT ON FUNCTION can_access_archivo IS
'Verifica si el usuario actual puede acceder a un archivo segun su entidad relacionada. '
'Usado por las politicas RLS de archivo_sistema.';

-- SELECT: Admin ve todos, client segun entidad relacionada
DROP POLICY IF EXISTS "archivo_sistema_select" ON public.archivo_sistema;
CREATE POLICY "archivo_sistema_select"
ON public.archivo_sistema FOR SELECT
USING (
    is_admin()
    OR can_access_archivo(entidad_tipo, entidad_id)
);

-- INSERT: Admin o client segun entidad relacionada
DROP POLICY IF EXISTS "archivo_sistema_insert" ON public.archivo_sistema;
CREATE POLICY "archivo_sistema_insert"
ON public.archivo_sistema FOR INSERT
WITH CHECK (
    is_admin()
    OR can_access_archivo(entidad_tipo, entidad_id)
);

-- UPDATE: Solo admin
DROP POLICY IF EXISTS "archivo_sistema_update" ON public.archivo_sistema;
CREATE POLICY "archivo_sistema_update"
ON public.archivo_sistema FOR UPDATE
USING (is_admin());

-- DELETE: Solo admin
DROP POLICY IF EXISTS "archivo_sistema_delete" ON public.archivo_sistema;
CREATE POLICY "archivo_sistema_delete"
ON public.archivo_sistema FOR DELETE
USING (is_admin());


-- ============================================================================
-- 10. INDICES PARA PERFORMANCE DE RLS
-- ============================================================================
-- Las politicas RLS ejecutan subqueries en cada consulta.
-- Estos indices aseguran que los JOINs y filtros sean eficientes.

-- Indices en FK usados por politicas de tablas con relacion indirecta
CREATE INDEX IF NOT EXISTS idx_contrato_categorias_contrato_id
ON public.contrato_categorias (contrato_id);

CREATE INDEX IF NOT EXISTS idx_plazas_contrato_categoria_id
ON public.plazas (contrato_categoria_id);

CREATE INDEX IF NOT EXISTS idx_historial_laboral_empleado_id
ON public.historial_laboral (empleado_id);

CREATE INDEX IF NOT EXISTS idx_requisicion_item_requisicion_id
ON public.requisicion_item (requisicion_id);

-- Indices en empresa_id para tablas con FK directa
-- (probablemente ya existen, IF NOT EXISTS previene error)
CREATE INDEX IF NOT EXISTS idx_empleados_empresa_id
ON public.empleados (empresa_id);

CREATE INDEX IF NOT EXISTS idx_contratos_empresa_id
ON public.contratos (empresa_id);

CREATE INDEX IF NOT EXISTS idx_requisicion_empresa_id
ON public.requisicion (empresa_id);

-- Indice para archivo_sistema (busqueda por entidad)
CREATE INDEX IF NOT EXISTS idx_archivo_sistema_entidad
ON public.archivo_sistema (entidad_tipo, entidad_id);

-- Indice en user_companies para get_user_companies()
CREATE INDEX IF NOT EXISTS idx_user_companies_user_id
ON public.user_companies (user_id);

-- Indice en user_profiles para is_admin()
CREATE INDEX IF NOT EXISTS idx_user_profiles_rol_activo
ON public.user_profiles (id) WHERE rol = 'admin' AND activo = true;


-- ============================================================================
-- 11. QUERIES DE VERIFICACION
-- ============================================================================
-- Ejecutar despues de la migracion para confirmar que RLS esta activo.
-- Copiar y pegar en el SQL Editor de Supabase.

-- Verificar que RLS esta habilitado en todas las tablas
SELECT
    schemaname,
    tablename,
    rowsecurity
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

-- Listar todas las politicas creadas
SELECT
    schemaname,
    tablename,
    policyname,
    permissive,
    roles,
    cmd
FROM pg_policies
WHERE schemaname = 'public'
ORDER BY tablename, cmd;


-- ============================================================================
-- 12. NOTA: TABLAS SIN RLS
-- ============================================================================
-- Las siguientes tablas NO tienen RLS habilitado en esta migracion.
-- Cualquier usuario con la anon key puede acceder a ellas.
-- Considerar agregar RLS en una migracion futura:
--
--   pagos                    -> FK: contrato_id -> contratos.empresa_id
--   requisicion_item         -> FK: requisicion_id -> requisicion.empresa_id
--   requisicion_partida      -> FK: requisicion_id -> requisicion.empresa_id
--   configuracion_requisicion -> Tabla de configuracion global (solo admin)
--
-- Para protegerlas, seguir el mismo patron:
--   ALTER TABLE public.{tabla} ENABLE ROW LEVEL SECURITY;
--   CREATE POLICY "{tabla}_select" ON public.{tabla} FOR SELECT
--   USING (is_admin() OR {subquery_a_empresa});


-- ============================================================================
-- ROLLBACK
-- ============================================================================
-- Para revertir esta migracion, ejecutar las siguientes sentencias:
--
-- -- Eliminar funcion helper
-- DROP FUNCTION IF EXISTS can_access_archivo(VARCHAR, INTEGER);
--
-- -- Desactivar RLS y eliminar politicas (por tabla)
--
-- -- empresas
-- DROP POLICY IF EXISTS "empresas_select" ON public.empresas;
-- DROP POLICY IF EXISTS "empresas_insert" ON public.empresas;
-- DROP POLICY IF EXISTS "empresas_update" ON public.empresas;
-- DROP POLICY IF EXISTS "empresas_delete" ON public.empresas;
-- ALTER TABLE public.empresas DISABLE ROW LEVEL SECURITY;
--
-- -- empleados
-- DROP POLICY IF EXISTS "empleados_select" ON public.empleados;
-- DROP POLICY IF EXISTS "empleados_insert" ON public.empleados;
-- DROP POLICY IF EXISTS "empleados_update" ON public.empleados;
-- DROP POLICY IF EXISTS "empleados_delete" ON public.empleados;
-- ALTER TABLE public.empleados DISABLE ROW LEVEL SECURITY;
--
-- -- contratos
-- DROP POLICY IF EXISTS "contratos_select" ON public.contratos;
-- DROP POLICY IF EXISTS "contratos_insert" ON public.contratos;
-- DROP POLICY IF EXISTS "contratos_update" ON public.contratos;
-- DROP POLICY IF EXISTS "contratos_delete" ON public.contratos;
-- ALTER TABLE public.contratos DISABLE ROW LEVEL SECURITY;
--
-- -- requisicion
-- DROP POLICY IF EXISTS "requisicion_select" ON public.requisicion;
-- DROP POLICY IF EXISTS "requisicion_insert" ON public.requisicion;
-- DROP POLICY IF EXISTS "requisicion_update" ON public.requisicion;
-- DROP POLICY IF EXISTS "requisicion_delete" ON public.requisicion;
-- ALTER TABLE public.requisicion DISABLE ROW LEVEL SECURITY;
--
-- -- contrato_categorias
-- DROP POLICY IF EXISTS "contrato_categorias_select" ON public.contrato_categorias;
-- DROP POLICY IF EXISTS "contrato_categorias_insert" ON public.contrato_categorias;
-- DROP POLICY IF EXISTS "contrato_categorias_update" ON public.contrato_categorias;
-- DROP POLICY IF EXISTS "contrato_categorias_delete" ON public.contrato_categorias;
-- ALTER TABLE public.contrato_categorias DISABLE ROW LEVEL SECURITY;
--
-- -- plazas
-- DROP POLICY IF EXISTS "plazas_select" ON public.plazas;
-- DROP POLICY IF EXISTS "plazas_insert" ON public.plazas;
-- DROP POLICY IF EXISTS "plazas_update" ON public.plazas;
-- DROP POLICY IF EXISTS "plazas_delete" ON public.plazas;
-- ALTER TABLE public.plazas DISABLE ROW LEVEL SECURITY;
--
-- -- historial_laboral
-- DROP POLICY IF EXISTS "historial_laboral_select" ON public.historial_laboral;
-- DROP POLICY IF EXISTS "historial_laboral_insert" ON public.historial_laboral;
-- DROP POLICY IF EXISTS "historial_laboral_update" ON public.historial_laboral;
-- DROP POLICY IF EXISTS "historial_laboral_delete" ON public.historial_laboral;
-- ALTER TABLE public.historial_laboral DISABLE ROW LEVEL SECURITY;
--
-- -- tipos_servicio
-- DROP POLICY IF EXISTS "tipos_servicio_select" ON public.tipos_servicio;
-- DROP POLICY IF EXISTS "tipos_servicio_insert" ON public.tipos_servicio;
-- DROP POLICY IF EXISTS "tipos_servicio_update" ON public.tipos_servicio;
-- DROP POLICY IF EXISTS "tipos_servicio_delete" ON public.tipos_servicio;
-- ALTER TABLE public.tipos_servicio DISABLE ROW LEVEL SECURITY;
--
-- -- categorias_puesto
-- DROP POLICY IF EXISTS "categorias_puesto_select" ON public.categorias_puesto;
-- DROP POLICY IF EXISTS "categorias_puesto_insert" ON public.categorias_puesto;
-- DROP POLICY IF EXISTS "categorias_puesto_update" ON public.categorias_puesto;
-- DROP POLICY IF EXISTS "categorias_puesto_delete" ON public.categorias_puesto;
-- ALTER TABLE public.categorias_puesto DISABLE ROW LEVEL SECURITY;
--
-- -- lugar_entrega
-- DROP POLICY IF EXISTS "lugar_entrega_select" ON public.lugar_entrega;
-- DROP POLICY IF EXISTS "lugar_entrega_insert" ON public.lugar_entrega;
-- DROP POLICY IF EXISTS "lugar_entrega_update" ON public.lugar_entrega;
-- DROP POLICY IF EXISTS "lugar_entrega_delete" ON public.lugar_entrega;
-- ALTER TABLE public.lugar_entrega DISABLE ROW LEVEL SECURITY;
--
-- -- archivo_sistema
-- DROP POLICY IF EXISTS "archivo_sistema_select" ON public.archivo_sistema;
-- DROP POLICY IF EXISTS "archivo_sistema_insert" ON public.archivo_sistema;
-- DROP POLICY IF EXISTS "archivo_sistema_update" ON public.archivo_sistema;
-- DROP POLICY IF EXISTS "archivo_sistema_delete" ON public.archivo_sistema;
-- ALTER TABLE public.archivo_sistema DISABLE ROW LEVEL SECURITY;
--
-- -- Indices (no es necesario eliminarlos, no causan problemas)
