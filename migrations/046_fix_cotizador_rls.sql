-- =============================================================================
-- Migration 046: Endurecer RLS del módulo cotizador
-- =============================================================================
-- Fecha: 2026-03-04
-- Descripcion: Reemplaza las politicas abiertas del cotizador por reglas
--              basadas en empresa del usuario y service_role.
-- Dependencias: 015_create_user_auth_tables, 045_create_modulo_cotizador
-- Autor: Sistema
-- =============================================================================

-- =============================================================================
-- 1. HELPERS DE ACCESO
-- =============================================================================

CREATE OR REPLACE FUNCTION public.cotizador_empresa_access(target_empresa_id INTEGER)
RETURNS BOOLEAN
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = public
AS $$
    SELECT is_admin() OR target_empresa_id = ANY(get_user_companies());
$$;

CREATE OR REPLACE FUNCTION public.cotizador_can_access_cotizacion(target_cotizacion_id INTEGER)
RETURNS BOOLEAN
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = public
AS $$
    SELECT EXISTS (
        SELECT 1
        FROM public.cotizaciones c
        WHERE c.id = target_cotizacion_id
          AND cotizador_empresa_access(c.empresa_id)
    );
$$;

CREATE OR REPLACE FUNCTION public.cotizador_can_access_partida(target_partida_id INTEGER)
RETURNS BOOLEAN
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = public
AS $$
    SELECT EXISTS (
        SELECT 1
        FROM public.cotizacion_partidas p
        WHERE p.id = target_partida_id
          AND cotizador_can_access_cotizacion(p.cotizacion_id)
    );
$$;

CREATE OR REPLACE FUNCTION public.cotizador_can_access_partida_categoria(target_partida_categoria_id INTEGER)
RETURNS BOOLEAN
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = public
AS $$
    SELECT EXISTS (
        SELECT 1
        FROM public.cotizacion_partida_categorias pc
        WHERE pc.id = target_partida_categoria_id
          AND cotizador_can_access_partida(pc.partida_id)
    );
$$;

CREATE OR REPLACE FUNCTION public.cotizador_can_access_concepto(target_concepto_id INTEGER)
RETURNS BOOLEAN
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = public
AS $$
    SELECT EXISTS (
        SELECT 1
        FROM public.cotizacion_conceptos cc
        WHERE cc.id = target_concepto_id
          AND cotizador_can_access_partida(cc.partida_id)
    );
$$;

-- =============================================================================
-- 2. ASEGURAR RLS ENCENDIDO
-- =============================================================================

ALTER TABLE public.configuracion_fiscal_empresa ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.cotizaciones ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.cotizacion_partidas ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.cotizacion_partida_categorias ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.cotizacion_conceptos ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.cotizacion_concepto_valores ENABLE ROW LEVEL SECURITY;

-- =============================================================================
-- 3. LIMPIEZA DE POLITICAS PREVIAS
-- =============================================================================

DROP POLICY IF EXISTS "configuracion_fiscal_empresa_select_policy" ON public.configuracion_fiscal_empresa;
DROP POLICY IF EXISTS "configuracion_fiscal_empresa_write_policy" ON public.configuracion_fiscal_empresa;
DROP POLICY IF EXISTS config_fiscal_service_all ON public.configuracion_fiscal_empresa;
DROP POLICY IF EXISTS config_fiscal_select ON public.configuracion_fiscal_empresa;
DROP POLICY IF EXISTS config_fiscal_insert ON public.configuracion_fiscal_empresa;
DROP POLICY IF EXISTS config_fiscal_update ON public.configuracion_fiscal_empresa;
DROP POLICY IF EXISTS config_fiscal_delete ON public.configuracion_fiscal_empresa;

DROP POLICY IF EXISTS "cotizaciones_select_policy" ON public.cotizaciones;
DROP POLICY IF EXISTS "cotizaciones_write_policy" ON public.cotizaciones;
DROP POLICY IF EXISTS cotizaciones_service_all ON public.cotizaciones;
DROP POLICY IF EXISTS cotizaciones_select ON public.cotizaciones;
DROP POLICY IF EXISTS cotizaciones_insert ON public.cotizaciones;
DROP POLICY IF EXISTS cotizaciones_update ON public.cotizaciones;
DROP POLICY IF EXISTS cotizaciones_delete ON public.cotizaciones;

DROP POLICY IF EXISTS "cotizacion_partidas_select_policy" ON public.cotizacion_partidas;
DROP POLICY IF EXISTS "cotizacion_partidas_write_policy" ON public.cotizacion_partidas;
DROP POLICY IF EXISTS cotizacion_partidas_service_all ON public.cotizacion_partidas;
DROP POLICY IF EXISTS cotizacion_partidas_select ON public.cotizacion_partidas;
DROP POLICY IF EXISTS cotizacion_partidas_insert ON public.cotizacion_partidas;
DROP POLICY IF EXISTS cotizacion_partidas_update ON public.cotizacion_partidas;
DROP POLICY IF EXISTS cotizacion_partidas_delete ON public.cotizacion_partidas;

DROP POLICY IF EXISTS "cotizacion_partida_categorias_select_policy" ON public.cotizacion_partida_categorias;
DROP POLICY IF EXISTS "cotizacion_partida_categorias_write_policy" ON public.cotizacion_partida_categorias;
DROP POLICY IF EXISTS cotizacion_partida_categorias_service_all ON public.cotizacion_partida_categorias;
DROP POLICY IF EXISTS cotizacion_partida_categorias_select ON public.cotizacion_partida_categorias;
DROP POLICY IF EXISTS cotizacion_partida_categorias_insert ON public.cotizacion_partida_categorias;
DROP POLICY IF EXISTS cotizacion_partida_categorias_update ON public.cotizacion_partida_categorias;
DROP POLICY IF EXISTS cotizacion_partida_categorias_delete ON public.cotizacion_partida_categorias;

DROP POLICY IF EXISTS "cotizacion_conceptos_select_policy" ON public.cotizacion_conceptos;
DROP POLICY IF EXISTS "cotizacion_conceptos_write_policy" ON public.cotizacion_conceptos;
DROP POLICY IF EXISTS cotizacion_conceptos_service_all ON public.cotizacion_conceptos;
DROP POLICY IF EXISTS cotizacion_conceptos_select ON public.cotizacion_conceptos;
DROP POLICY IF EXISTS cotizacion_conceptos_insert ON public.cotizacion_conceptos;
DROP POLICY IF EXISTS cotizacion_conceptos_update ON public.cotizacion_conceptos;
DROP POLICY IF EXISTS cotizacion_conceptos_delete ON public.cotizacion_conceptos;

DROP POLICY IF EXISTS "cotizacion_concepto_valores_select_policy" ON public.cotizacion_concepto_valores;
DROP POLICY IF EXISTS "cotizacion_concepto_valores_write_policy" ON public.cotizacion_concepto_valores;
DROP POLICY IF EXISTS cotizacion_concepto_valores_service_all ON public.cotizacion_concepto_valores;
DROP POLICY IF EXISTS cotizacion_concepto_valores_select ON public.cotizacion_concepto_valores;
DROP POLICY IF EXISTS cotizacion_concepto_valores_insert ON public.cotizacion_concepto_valores;
DROP POLICY IF EXISTS cotizacion_concepto_valores_update ON public.cotizacion_concepto_valores;
DROP POLICY IF EXISTS cotizacion_concepto_valores_delete ON public.cotizacion_concepto_valores;

-- =============================================================================
-- 4. POLITICAS NUEVAS
-- =============================================================================

CREATE POLICY config_fiscal_service_all ON public.configuracion_fiscal_empresa
    FOR ALL TO service_role USING (true) WITH CHECK (true);

CREATE POLICY config_fiscal_select ON public.configuracion_fiscal_empresa
    FOR SELECT TO authenticated
    USING (cotizador_empresa_access(empresa_id));

CREATE POLICY config_fiscal_insert ON public.configuracion_fiscal_empresa
    FOR INSERT TO authenticated
    WITH CHECK (cotizador_empresa_access(empresa_id));

CREATE POLICY config_fiscal_update ON public.configuracion_fiscal_empresa
    FOR UPDATE TO authenticated
    USING (cotizador_empresa_access(empresa_id))
    WITH CHECK (cotizador_empresa_access(empresa_id));

CREATE POLICY config_fiscal_delete ON public.configuracion_fiscal_empresa
    FOR DELETE TO authenticated
    USING (cotizador_empresa_access(empresa_id));

CREATE POLICY cotizaciones_service_all ON public.cotizaciones
    FOR ALL TO service_role USING (true) WITH CHECK (true);

CREATE POLICY cotizaciones_select ON public.cotizaciones
    FOR SELECT TO authenticated
    USING (cotizador_empresa_access(empresa_id));

CREATE POLICY cotizaciones_insert ON public.cotizaciones
    FOR INSERT TO authenticated
    WITH CHECK (cotizador_empresa_access(empresa_id));

CREATE POLICY cotizaciones_update ON public.cotizaciones
    FOR UPDATE TO authenticated
    USING (cotizador_empresa_access(empresa_id))
    WITH CHECK (cotizador_empresa_access(empresa_id));

CREATE POLICY cotizaciones_delete ON public.cotizaciones
    FOR DELETE TO authenticated
    USING (cotizador_empresa_access(empresa_id));

CREATE POLICY cotizacion_partidas_service_all ON public.cotizacion_partidas
    FOR ALL TO service_role USING (true) WITH CHECK (true);

CREATE POLICY cotizacion_partidas_select ON public.cotizacion_partidas
    FOR SELECT TO authenticated
    USING (cotizador_can_access_cotizacion(cotizacion_id));

CREATE POLICY cotizacion_partidas_insert ON public.cotizacion_partidas
    FOR INSERT TO authenticated
    WITH CHECK (cotizador_can_access_cotizacion(cotizacion_id));

CREATE POLICY cotizacion_partidas_update ON public.cotizacion_partidas
    FOR UPDATE TO authenticated
    USING (cotizador_can_access_cotizacion(cotizacion_id))
    WITH CHECK (cotizador_can_access_cotizacion(cotizacion_id));

CREATE POLICY cotizacion_partidas_delete ON public.cotizacion_partidas
    FOR DELETE TO authenticated
    USING (cotizador_can_access_cotizacion(cotizacion_id));

CREATE POLICY cotizacion_partida_categorias_service_all ON public.cotizacion_partida_categorias
    FOR ALL TO service_role USING (true) WITH CHECK (true);

CREATE POLICY cotizacion_partida_categorias_select ON public.cotizacion_partida_categorias
    FOR SELECT TO authenticated
    USING (cotizador_can_access_partida(partida_id));

CREATE POLICY cotizacion_partida_categorias_insert ON public.cotizacion_partida_categorias
    FOR INSERT TO authenticated
    WITH CHECK (cotizador_can_access_partida(partida_id));

CREATE POLICY cotizacion_partida_categorias_update ON public.cotizacion_partida_categorias
    FOR UPDATE TO authenticated
    USING (cotizador_can_access_partida(partida_id))
    WITH CHECK (cotizador_can_access_partida(partida_id));

CREATE POLICY cotizacion_partida_categorias_delete ON public.cotizacion_partida_categorias
    FOR DELETE TO authenticated
    USING (cotizador_can_access_partida(partida_id));

CREATE POLICY cotizacion_conceptos_service_all ON public.cotizacion_conceptos
    FOR ALL TO service_role USING (true) WITH CHECK (true);

CREATE POLICY cotizacion_conceptos_select ON public.cotizacion_conceptos
    FOR SELECT TO authenticated
    USING (cotizador_can_access_partida(partida_id));

CREATE POLICY cotizacion_conceptos_insert ON public.cotizacion_conceptos
    FOR INSERT TO authenticated
    WITH CHECK (cotizador_can_access_partida(partida_id));

CREATE POLICY cotizacion_conceptos_update ON public.cotizacion_conceptos
    FOR UPDATE TO authenticated
    USING (cotizador_can_access_partida(partida_id))
    WITH CHECK (cotizador_can_access_partida(partida_id));

CREATE POLICY cotizacion_conceptos_delete ON public.cotizacion_conceptos
    FOR DELETE TO authenticated
    USING (cotizador_can_access_partida(partida_id));

CREATE POLICY cotizacion_concepto_valores_service_all ON public.cotizacion_concepto_valores
    FOR ALL TO service_role USING (true) WITH CHECK (true);

CREATE POLICY cotizacion_concepto_valores_select ON public.cotizacion_concepto_valores
    FOR SELECT TO authenticated
    USING (
        cotizador_can_access_concepto(concepto_id)
        AND cotizador_can_access_partida_categoria(partida_categoria_id)
    );

CREATE POLICY cotizacion_concepto_valores_insert ON public.cotizacion_concepto_valores
    FOR INSERT TO authenticated
    WITH CHECK (
        cotizador_can_access_concepto(concepto_id)
        AND cotizador_can_access_partida_categoria(partida_categoria_id)
    );

CREATE POLICY cotizacion_concepto_valores_update ON public.cotizacion_concepto_valores
    FOR UPDATE TO authenticated
    USING (
        cotizador_can_access_concepto(concepto_id)
        AND cotizador_can_access_partida_categoria(partida_categoria_id)
    )
    WITH CHECK (
        cotizador_can_access_concepto(concepto_id)
        AND cotizador_can_access_partida_categoria(partida_categoria_id)
    );

CREATE POLICY cotizacion_concepto_valores_delete ON public.cotizacion_concepto_valores
    FOR DELETE TO authenticated
    USING (
        cotizador_can_access_concepto(concepto_id)
        AND cotizador_can_access_partida_categoria(partida_categoria_id)
    );

-- =============================================================================
-- ROLLBACK MANUAL
-- =============================================================================
-- DROP POLICY IF EXISTS cotizacion_concepto_valores_delete ON public.cotizacion_concepto_valores;
-- DROP POLICY IF EXISTS cotizacion_concepto_valores_update ON public.cotizacion_concepto_valores;
-- DROP POLICY IF EXISTS cotizacion_concepto_valores_insert ON public.cotizacion_concepto_valores;
-- DROP POLICY IF EXISTS cotizacion_concepto_valores_select ON public.cotizacion_concepto_valores;
-- DROP POLICY IF EXISTS cotizacion_concepto_valores_service_all ON public.cotizacion_concepto_valores;
-- DROP POLICY IF EXISTS cotizacion_conceptos_delete ON public.cotizacion_conceptos;
-- DROP POLICY IF EXISTS cotizacion_conceptos_update ON public.cotizacion_conceptos;
-- DROP POLICY IF EXISTS cotizacion_conceptos_insert ON public.cotizacion_conceptos;
-- DROP POLICY IF EXISTS cotizacion_conceptos_select ON public.cotizacion_conceptos;
-- DROP POLICY IF EXISTS cotizacion_conceptos_service_all ON public.cotizacion_conceptos;
-- DROP POLICY IF EXISTS cotizacion_partida_categorias_delete ON public.cotizacion_partida_categorias;
-- DROP POLICY IF EXISTS cotizacion_partida_categorias_update ON public.cotizacion_partida_categorias;
-- DROP POLICY IF EXISTS cotizacion_partida_categorias_insert ON public.cotizacion_partida_categorias;
-- DROP POLICY IF EXISTS cotizacion_partida_categorias_select ON public.cotizacion_partida_categorias;
-- DROP POLICY IF EXISTS cotizacion_partida_categorias_service_all ON public.cotizacion_partida_categorias;
-- DROP POLICY IF EXISTS cotizacion_partidas_delete ON public.cotizacion_partidas;
-- DROP POLICY IF EXISTS cotizacion_partidas_update ON public.cotizacion_partidas;
-- DROP POLICY IF EXISTS cotizacion_partidas_insert ON public.cotizacion_partidas;
-- DROP POLICY IF EXISTS cotizacion_partidas_select ON public.cotizacion_partidas;
-- DROP POLICY IF EXISTS cotizacion_partidas_service_all ON public.cotizacion_partidas;
-- DROP POLICY IF EXISTS cotizaciones_delete ON public.cotizaciones;
-- DROP POLICY IF EXISTS cotizaciones_update ON public.cotizaciones;
-- DROP POLICY IF EXISTS cotizaciones_insert ON public.cotizaciones;
-- DROP POLICY IF EXISTS cotizaciones_select ON public.cotizaciones;
-- DROP POLICY IF EXISTS cotizaciones_service_all ON public.cotizaciones;
-- DROP POLICY IF EXISTS config_fiscal_delete ON public.configuracion_fiscal_empresa;
-- DROP POLICY IF EXISTS config_fiscal_update ON public.configuracion_fiscal_empresa;
-- DROP POLICY IF EXISTS config_fiscal_insert ON public.configuracion_fiscal_empresa;
-- DROP POLICY IF EXISTS config_fiscal_select ON public.configuracion_fiscal_empresa;
-- DROP POLICY IF EXISTS config_fiscal_service_all ON public.configuracion_fiscal_empresa;
