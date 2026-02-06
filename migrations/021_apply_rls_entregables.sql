-- ============================================================================
-- Migration: Apply RLS to Entregables Tables
-- Fecha: 2026-02-05
-- Descripción: Aplica Row Level Security a las tablas de entregables.
--              - Admin ve todo, puede escribir todo
--              - Client ve/escribe solo entregables de contratos de sus empresas
-- Depende de: 017_create_entregables_tables.sql, funciones is_admin() y get_user_companies()
-- ============================================================================

-- ============================================================================
-- 1. CONTRATO_TIPO_ENTREGABLE (Configuración)
-- ============================================================================
-- Relación: contrato_id -> contratos.empresa_id
-- Admin puede todo, client solo lectura de contratos de sus empresas

ALTER TABLE public.contrato_tipo_entregable ENABLE ROW LEVEL SECURITY;

-- SELECT: Admin ve todos, client solo de contratos de sus empresas
DROP POLICY IF EXISTS "cte_select" ON public.contrato_tipo_entregable;
CREATE POLICY "cte_select"
ON public.contrato_tipo_entregable FOR SELECT
USING (
    is_admin()
    OR contrato_id IN (
        SELECT id FROM public.contratos
        WHERE empresa_id = ANY(get_user_companies())
    )
);

-- INSERT: Solo admin (configuración se hace desde admin)
DROP POLICY IF EXISTS "cte_insert" ON public.contrato_tipo_entregable;
CREATE POLICY "cte_insert"
ON public.contrato_tipo_entregable FOR INSERT
WITH CHECK (is_admin());

-- UPDATE: Solo admin
DROP POLICY IF EXISTS "cte_update" ON public.contrato_tipo_entregable;
CREATE POLICY "cte_update"
ON public.contrato_tipo_entregable FOR UPDATE
USING (is_admin());

-- DELETE: Solo admin
DROP POLICY IF EXISTS "cte_delete" ON public.contrato_tipo_entregable;
CREATE POLICY "cte_delete"
ON public.contrato_tipo_entregable FOR DELETE
USING (is_admin());


-- ============================================================================
-- 2. ENTREGABLES (Operativa principal)
-- ============================================================================
-- Relación: contrato_id -> contratos.empresa_id
-- Admin puede todo
-- Client puede ver y crear/actualizar entregables de contratos de sus empresas

ALTER TABLE public.entregables ENABLE ROW LEVEL SECURITY;

-- SELECT: Admin ve todos, client solo de contratos de sus empresas
DROP POLICY IF EXISTS "entregables_select" ON public.entregables;
CREATE POLICY "entregables_select"
ON public.entregables FOR SELECT
USING (
    is_admin()
    OR contrato_id IN (
        SELECT id FROM public.contratos
        WHERE empresa_id = ANY(get_user_companies())
    )
);

-- INSERT: Admin puede crear cualquiera, client solo de sus contratos
-- (Los períodos se generan automáticamente, pero el client puede "entregar")
DROP POLICY IF EXISTS "entregables_insert" ON public.entregables;
CREATE POLICY "entregables_insert"
ON public.entregables FOR INSERT
WITH CHECK (
    is_admin()
    OR contrato_id IN (
        SELECT id FROM public.contratos
        WHERE empresa_id = ANY(get_user_companies())
    )
);

-- UPDATE: Admin puede actualizar todo, client solo puede actualizar
-- entregables de sus contratos que estén en estatus PENDIENTE o RECHAZADO
DROP POLICY IF EXISTS "entregables_update" ON public.entregables;
CREATE POLICY "entregables_update"
ON public.entregables FOR UPDATE
USING (
    is_admin()
    OR (
        contrato_id IN (
            SELECT id FROM public.contratos
            WHERE empresa_id = ANY(get_user_companies())
        )
        AND estatus IN ('PENDIENTE', 'RECHAZADO')
    )
);

-- DELETE: Solo admin
DROP POLICY IF EXISTS "entregables_delete" ON public.entregables;
CREATE POLICY "entregables_delete"
ON public.entregables FOR DELETE
USING (is_admin());


-- ============================================================================
-- 3. ENTREGABLE_DETALLE_PERSONAL (Detalle por categoría)
-- ============================================================================
-- Relación indirecta: entregable_id -> entregables.contrato_id -> contratos.empresa_id
-- Admin puede todo, client puede ver y crear de sus entregables

ALTER TABLE public.entregable_detalle_personal ENABLE ROW LEVEL SECURITY;

-- SELECT: Admin ve todos, client via entregable -> contrato -> empresa
DROP POLICY IF EXISTS "edp_select" ON public.entregable_detalle_personal;
CREATE POLICY "edp_select"
ON public.entregable_detalle_personal FOR SELECT
USING (
    is_admin()
    OR entregable_id IN (
        SELECT e.id FROM public.entregables e
        JOIN public.contratos c ON e.contrato_id = c.id
        WHERE c.empresa_id = ANY(get_user_companies())
    )
);

-- INSERT: Admin o client de ese entregable
DROP POLICY IF EXISTS "edp_insert" ON public.entregable_detalle_personal;
CREATE POLICY "edp_insert"
ON public.entregable_detalle_personal FOR INSERT
WITH CHECK (
    is_admin()
    OR entregable_id IN (
        SELECT e.id FROM public.entregables e
        JOIN public.contratos c ON e.contrato_id = c.id
        WHERE c.empresa_id = ANY(get_user_companies())
    )
);

-- UPDATE: Admin o client (si el entregable está en estado editable)
DROP POLICY IF EXISTS "edp_update" ON public.entregable_detalle_personal;
CREATE POLICY "edp_update"
ON public.entregable_detalle_personal FOR UPDATE
USING (
    is_admin()
    OR entregable_id IN (
        SELECT e.id FROM public.entregables e
        JOIN public.contratos c ON e.contrato_id = c.id
        WHERE c.empresa_id = ANY(get_user_companies())
        AND e.estatus IN ('PENDIENTE', 'RECHAZADO')
    )
);

-- DELETE: Solo admin
DROP POLICY IF EXISTS "edp_delete" ON public.entregable_detalle_personal;
CREATE POLICY "edp_delete"
ON public.entregable_detalle_personal FOR DELETE
USING (is_admin());


-- ============================================================================
-- 4. FIN DE MIGRACIÓN
-- ============================================================================
