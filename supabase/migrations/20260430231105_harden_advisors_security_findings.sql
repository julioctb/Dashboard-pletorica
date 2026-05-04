BEGIN;

-- ============================================================================
-- 1. Hardening de funciones reportadas por advisors
-- ============================================================================

CREATE OR REPLACE FUNCTION public.calcular_subtotal_contrato_item()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = public
AS $$
BEGIN
    NEW.subtotal = NEW.cantidad * NEW.precio_unitario;
    RETURN NEW;
END;
$$;

CREATE OR REPLACE FUNCTION public.set_fecha_actualizacion()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = public
AS $$
BEGIN
    NEW.fecha_actualizacion = NOW();
    RETURN NEW;
END;
$$;

CREATE OR REPLACE FUNCTION public.update_fecha_actualizacion()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = public
AS $$
BEGIN
    NEW.fecha_actualizacion = NOW();
    RETURN NEW;
END;
$$;

CREATE OR REPLACE FUNCTION public.update_contrato_categorias_fecha_actualizacion()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = public
AS $$
BEGIN
    NEW.fecha_actualizacion = NOW();
    RETURN NEW;
END;
$$;

CREATE OR REPLACE FUNCTION public.actualizar_estatus_empleado_desde_historial()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = public
AS $$
DECLARE
    v_empleado_id INTEGER;
    v_tiene_plaza_activa BOOLEAN;
    v_tiene_col_estatus BOOLEAN;
BEGIN
    v_empleado_id := COALESCE(NEW.empleado_id, OLD.empleado_id);

    IF v_empleado_id IS NULL THEN
        RETURN COALESCE(NEW, OLD);
    END IF;

    SELECT EXISTS (
        SELECT 1
        FROM information_schema.columns c
        WHERE c.table_schema = 'public'
          AND c.table_name = 'historial_laboral'
          AND c.column_name = 'estatus'
    )
    INTO v_tiene_col_estatus;

    IF v_tiene_col_estatus THEN
        SELECT EXISTS (
            SELECT 1
            FROM public.historial_laboral hl
            WHERE hl.empleado_id = v_empleado_id
              AND hl.fecha_fin IS NULL
              AND hl.estatus = 'ACTIVA'
        )
        INTO v_tiene_plaza_activa;
    ELSE
        SELECT EXISTS (
            SELECT 1
            FROM public.historial_laboral hl
            WHERE hl.empleado_id = v_empleado_id
              AND hl.fecha_fin IS NULL
        )
        INTO v_tiene_plaza_activa;
    END IF;

    UPDATE public.empleados
    SET estatus = CASE
        WHEN v_tiene_plaza_activa THEN 'ACTIVO'::public.estatus_empleado
        ELSE 'INACTIVO'::public.estatus_empleado
    END,
    fecha_actualizacion = NOW()
    WHERE id = v_empleado_id
      AND COALESCE(estatus::text, '') NOT IN ('BAJA', 'SUSPENDIDO');

    RETURN COALESCE(NEW, OLD);
END;
$$;


-- ============================================================================
-- 2. Cerrar exposición de SECURITY DEFINER en schema public
-- ============================================================================

DROP FUNCTION IF EXISTS public.handle_new_user();

CREATE SCHEMA IF NOT EXISTS private;

CREATE OR REPLACE FUNCTION private.cotizador_empresa_access(target_empresa_id INTEGER)
RETURNS BOOLEAN
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = public
AS $$
    SELECT public.is_admin() OR target_empresa_id = ANY(public.get_user_companies());
$$;

CREATE OR REPLACE FUNCTION private.cotizador_can_access_cotizacion(target_cotizacion_id INTEGER)
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
          AND private.cotizador_empresa_access(c.empresa_id)
    );
$$;

CREATE OR REPLACE FUNCTION private.cotizador_can_access_partida(target_partida_id INTEGER)
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
          AND private.cotizador_can_access_cotizacion(p.cotizacion_id)
    );
$$;

CREATE OR REPLACE FUNCTION private.cotizador_can_access_partida_categoria(target_partida_categoria_id INTEGER)
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
          AND private.cotizador_can_access_partida(pc.partida_id)
    );
$$;

CREATE OR REPLACE FUNCTION private.cotizador_can_access_concepto(target_concepto_id INTEGER)
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
          AND private.cotizador_can_access_partida(cc.partida_id)
    );
$$;

CREATE OR REPLACE FUNCTION public.cotizador_empresa_access(target_empresa_id INTEGER)
RETURNS BOOLEAN
LANGUAGE sql
STABLE
SET search_path = public, private
AS $$
    SELECT private.cotizador_empresa_access(target_empresa_id);
$$;

CREATE OR REPLACE FUNCTION public.cotizador_can_access_cotizacion(target_cotizacion_id INTEGER)
RETURNS BOOLEAN
LANGUAGE sql
STABLE
SET search_path = public, private
AS $$
    SELECT private.cotizador_can_access_cotizacion(target_cotizacion_id);
$$;

CREATE OR REPLACE FUNCTION public.cotizador_can_access_partida(target_partida_id INTEGER)
RETURNS BOOLEAN
LANGUAGE sql
STABLE
SET search_path = public, private
AS $$
    SELECT private.cotizador_can_access_partida(target_partida_id);
$$;

CREATE OR REPLACE FUNCTION public.cotizador_can_access_partida_categoria(target_partida_categoria_id INTEGER)
RETURNS BOOLEAN
LANGUAGE sql
STABLE
SET search_path = public, private
AS $$
    SELECT private.cotizador_can_access_partida_categoria(target_partida_categoria_id);
$$;

CREATE OR REPLACE FUNCTION public.cotizador_can_access_concepto(target_concepto_id INTEGER)
RETURNS BOOLEAN
LANGUAGE sql
STABLE
SET search_path = public, private
AS $$
    SELECT private.cotizador_can_access_concepto(target_concepto_id);
$$;


-- ============================================================================
-- 3. Habilitar RLS donde falta y endurecer políticas abiertas
-- ============================================================================

DO $$
BEGIN
    IF to_regclass('public.pagos') IS NOT NULL THEN
        ALTER TABLE public.pagos ENABLE ROW LEVEL SECURITY;
        DROP POLICY IF EXISTS pagos_select ON public.pagos;
        DROP POLICY IF EXISTS pagos_insert ON public.pagos;
        DROP POLICY IF EXISTS pagos_update ON public.pagos;
        DROP POLICY IF EXISTS pagos_delete ON public.pagos;
        CREATE POLICY pagos_select ON public.pagos FOR SELECT USING (
            (SELECT public.is_admin())
            OR contrato_id IN (
                SELECT c.id FROM public.contratos c
                WHERE c.empresa_id = ANY(public.get_user_companies())
            )
        );
        CREATE POLICY pagos_insert ON public.pagos FOR INSERT WITH CHECK ((SELECT public.is_admin()));
        CREATE POLICY pagos_update ON public.pagos FOR UPDATE USING ((SELECT public.is_admin())) WITH CHECK ((SELECT public.is_admin()));
        CREATE POLICY pagos_delete ON public.pagos FOR DELETE USING ((SELECT public.is_admin()));
    END IF;

    IF to_regclass('public.empleado_descuentos_recurrentes') IS NOT NULL THEN
        ALTER TABLE public.empleado_descuentos_recurrentes ENABLE ROW LEVEL SECURITY;
        DROP POLICY IF EXISTS edr_select ON public.empleado_descuentos_recurrentes;
        DROP POLICY IF EXISTS edr_insert ON public.empleado_descuentos_recurrentes;
        DROP POLICY IF EXISTS edr_update ON public.empleado_descuentos_recurrentes;
        DROP POLICY IF EXISTS edr_delete ON public.empleado_descuentos_recurrentes;
        CREATE POLICY edr_select ON public.empleado_descuentos_recurrentes FOR SELECT USING (
            (SELECT public.is_admin())
            OR empleado_id IN (
                SELECT e.id FROM public.empleados e
                WHERE e.empresa_id = ANY(public.get_user_companies())
            )
        );
        CREATE POLICY edr_insert ON public.empleado_descuentos_recurrentes FOR INSERT WITH CHECK ((SELECT public.is_admin()));
        CREATE POLICY edr_update ON public.empleado_descuentos_recurrentes FOR UPDATE USING ((SELECT public.is_admin())) WITH CHECK ((SELECT public.is_admin()));
        CREATE POLICY edr_delete ON public.empleado_descuentos_recurrentes FOR DELETE USING ((SELECT public.is_admin()));
    END IF;

    IF to_regclass('public.configuracion_requisicion') IS NOT NULL THEN
        ALTER TABLE public.configuracion_requisicion ENABLE ROW LEVEL SECURITY;
        DROP POLICY IF EXISTS configuracion_requisicion_select ON public.configuracion_requisicion;
        DROP POLICY IF EXISTS configuracion_requisicion_insert ON public.configuracion_requisicion;
        DROP POLICY IF EXISTS configuracion_requisicion_update ON public.configuracion_requisicion;
        DROP POLICY IF EXISTS configuracion_requisicion_delete ON public.configuracion_requisicion;
        CREATE POLICY configuracion_requisicion_select ON public.configuracion_requisicion FOR SELECT USING ((SELECT auth.uid()) IS NOT NULL);
        CREATE POLICY configuracion_requisicion_insert ON public.configuracion_requisicion FOR INSERT WITH CHECK ((SELECT public.is_admin()));
        CREATE POLICY configuracion_requisicion_update ON public.configuracion_requisicion FOR UPDATE USING ((SELECT public.is_admin())) WITH CHECK ((SELECT public.is_admin()));
        CREATE POLICY configuracion_requisicion_delete ON public.configuracion_requisicion FOR DELETE USING ((SELECT public.is_admin()));
    END IF;

    IF to_regclass('public.configuracion_operativa_empresa') IS NOT NULL THEN
        ALTER TABLE public.configuracion_operativa_empresa ENABLE ROW LEVEL SECURITY;
        DROP POLICY IF EXISTS config_operativa_select ON public.configuracion_operativa_empresa;
        DROP POLICY IF EXISTS config_operativa_insert ON public.configuracion_operativa_empresa;
        DROP POLICY IF EXISTS config_operativa_update ON public.configuracion_operativa_empresa;
        DROP POLICY IF EXISTS config_operativa_delete ON public.configuracion_operativa_empresa;
        CREATE POLICY config_operativa_select ON public.configuracion_operativa_empresa FOR SELECT USING (
            (SELECT public.is_admin())
            OR empresa_id = ANY(public.get_user_companies())
        );
        CREATE POLICY config_operativa_insert ON public.configuracion_operativa_empresa FOR INSERT WITH CHECK ((SELECT public.is_admin()));
        CREATE POLICY config_operativa_update ON public.configuracion_operativa_empresa FOR UPDATE USING ((SELECT public.is_admin())) WITH CHECK ((SELECT public.is_admin()));
        CREATE POLICY config_operativa_delete ON public.configuracion_operativa_empresa FOR DELETE USING ((SELECT public.is_admin()));
    END IF;

    IF to_regclass('public.configuracion_bancos_empresa') IS NOT NULL THEN
        ALTER TABLE public.configuracion_bancos_empresa ENABLE ROW LEVEL SECURITY;
        DROP POLICY IF EXISTS config_bancos_select ON public.configuracion_bancos_empresa;
        DROP POLICY IF EXISTS config_bancos_insert ON public.configuracion_bancos_empresa;
        DROP POLICY IF EXISTS config_bancos_update ON public.configuracion_bancos_empresa;
        DROP POLICY IF EXISTS config_bancos_delete ON public.configuracion_bancos_empresa;
        CREATE POLICY config_bancos_select ON public.configuracion_bancos_empresa FOR SELECT USING (
            (SELECT public.is_admin())
            OR empresa_id = ANY(public.get_user_companies())
        );
        CREATE POLICY config_bancos_insert ON public.configuracion_bancos_empresa FOR INSERT WITH CHECK ((SELECT public.is_admin()));
        CREATE POLICY config_bancos_update ON public.configuracion_bancos_empresa FOR UPDATE USING ((SELECT public.is_admin())) WITH CHECK ((SELECT public.is_admin()));
        CREATE POLICY config_bancos_delete ON public.configuracion_bancos_empresa FOR DELETE USING ((SELECT public.is_admin()));
    END IF;

    IF to_regclass('public.dispersion_layouts') IS NOT NULL THEN
        ALTER TABLE public.dispersion_layouts ENABLE ROW LEVEL SECURITY;
        DROP POLICY IF EXISTS dispersion_layouts_select ON public.dispersion_layouts;
        DROP POLICY IF EXISTS dispersion_layouts_insert ON public.dispersion_layouts;
        DROP POLICY IF EXISTS dispersion_layouts_update ON public.dispersion_layouts;
        DROP POLICY IF EXISTS dispersion_layouts_delete ON public.dispersion_layouts;
        CREATE POLICY dispersion_layouts_select ON public.dispersion_layouts FOR SELECT USING (
            (SELECT public.is_admin())
            OR empresa_id = ANY(public.get_user_companies())
        );
        CREATE POLICY dispersion_layouts_insert ON public.dispersion_layouts FOR INSERT WITH CHECK ((SELECT public.is_admin()));
        CREATE POLICY dispersion_layouts_update ON public.dispersion_layouts FOR UPDATE USING ((SELECT public.is_admin())) WITH CHECK ((SELECT public.is_admin()));
        CREATE POLICY dispersion_layouts_delete ON public.dispersion_layouts FOR DELETE USING ((SELECT public.is_admin()));
    END IF;

    IF to_regclass('public.periodos_nomina') IS NOT NULL THEN
        ALTER TABLE public.periodos_nomina ENABLE ROW LEVEL SECURITY;
        DROP POLICY IF EXISTS periodos_nomina_select ON public.periodos_nomina;
        DROP POLICY IF EXISTS periodos_nomina_insert ON public.periodos_nomina;
        DROP POLICY IF EXISTS periodos_nomina_update ON public.periodos_nomina;
        DROP POLICY IF EXISTS periodos_nomina_delete ON public.periodos_nomina;
        CREATE POLICY periodos_nomina_select ON public.periodos_nomina FOR SELECT USING (
            (SELECT public.is_admin())
            OR empresa_id = ANY(public.get_user_companies())
        );
        CREATE POLICY periodos_nomina_insert ON public.periodos_nomina FOR INSERT WITH CHECK ((SELECT public.is_admin()));
        CREATE POLICY periodos_nomina_update ON public.periodos_nomina FOR UPDATE USING ((SELECT public.is_admin())) WITH CHECK ((SELECT public.is_admin()));
        CREATE POLICY periodos_nomina_delete ON public.periodos_nomina FOR DELETE USING ((SELECT public.is_admin()));
    END IF;

    IF to_regclass('public.nominas_empleado') IS NOT NULL THEN
        ALTER TABLE public.nominas_empleado ENABLE ROW LEVEL SECURITY;
        DROP POLICY IF EXISTS nominas_empleado_select ON public.nominas_empleado;
        DROP POLICY IF EXISTS nominas_empleado_insert ON public.nominas_empleado;
        DROP POLICY IF EXISTS nominas_empleado_update ON public.nominas_empleado;
        DROP POLICY IF EXISTS nominas_empleado_delete ON public.nominas_empleado;
        CREATE POLICY nominas_empleado_select ON public.nominas_empleado FOR SELECT USING (
            (SELECT public.is_admin())
            OR empresa_id = ANY(public.get_user_companies())
        );
        CREATE POLICY nominas_empleado_insert ON public.nominas_empleado FOR INSERT WITH CHECK ((SELECT public.is_admin()));
        CREATE POLICY nominas_empleado_update ON public.nominas_empleado FOR UPDATE USING ((SELECT public.is_admin())) WITH CHECK ((SELECT public.is_admin()));
        CREATE POLICY nominas_empleado_delete ON public.nominas_empleado FOR DELETE USING ((SELECT public.is_admin()));
    END IF;

    IF to_regclass('public.nomina_movimientos') IS NOT NULL THEN
        ALTER TABLE public.nomina_movimientos ENABLE ROW LEVEL SECURITY;
        DROP POLICY IF EXISTS nomina_movimientos_select ON public.nomina_movimientos;
        DROP POLICY IF EXISTS nomina_movimientos_insert ON public.nomina_movimientos;
        DROP POLICY IF EXISTS nomina_movimientos_update ON public.nomina_movimientos;
        DROP POLICY IF EXISTS nomina_movimientos_delete ON public.nomina_movimientos;
        CREATE POLICY nomina_movimientos_select ON public.nomina_movimientos FOR SELECT USING (
            (SELECT public.is_admin())
            OR nomina_empleado_id IN (
                SELECT ne.id FROM public.nominas_empleado ne
                WHERE ne.empresa_id = ANY(public.get_user_companies())
            )
        );
        CREATE POLICY nomina_movimientos_insert ON public.nomina_movimientos FOR INSERT WITH CHECK ((SELECT public.is_admin()));
        CREATE POLICY nomina_movimientos_update ON public.nomina_movimientos FOR UPDATE USING ((SELECT public.is_admin())) WITH CHECK ((SELECT public.is_admin()));
        CREATE POLICY nomina_movimientos_delete ON public.nomina_movimientos FOR DELETE USING ((SELECT public.is_admin()));
    END IF;

    IF to_regclass('public.conceptos_nomina') IS NOT NULL THEN
        ALTER TABLE public.conceptos_nomina ENABLE ROW LEVEL SECURITY;
        DROP POLICY IF EXISTS conceptos_nomina_select ON public.conceptos_nomina;
        DROP POLICY IF EXISTS conceptos_nomina_insert ON public.conceptos_nomina;
        DROP POLICY IF EXISTS conceptos_nomina_update ON public.conceptos_nomina;
        DROP POLICY IF EXISTS conceptos_nomina_delete ON public.conceptos_nomina;
        CREATE POLICY conceptos_nomina_select ON public.conceptos_nomina FOR SELECT USING ((SELECT auth.uid()) IS NOT NULL);
        CREATE POLICY conceptos_nomina_insert ON public.conceptos_nomina FOR INSERT WITH CHECK ((SELECT public.is_admin()));
        CREATE POLICY conceptos_nomina_update ON public.conceptos_nomina FOR UPDATE USING ((SELECT public.is_admin())) WITH CHECK ((SELECT public.is_admin()));
        CREATE POLICY conceptos_nomina_delete ON public.conceptos_nomina FOR DELETE USING ((SELECT public.is_admin()));
    END IF;

    IF to_regclass('public.conceptos_nomina_empresa') IS NOT NULL THEN
        ALTER TABLE public.conceptos_nomina_empresa ENABLE ROW LEVEL SECURITY;
        DROP POLICY IF EXISTS conceptos_nomina_empresa_select ON public.conceptos_nomina_empresa;
        DROP POLICY IF EXISTS conceptos_nomina_empresa_insert ON public.conceptos_nomina_empresa;
        DROP POLICY IF EXISTS conceptos_nomina_empresa_update ON public.conceptos_nomina_empresa;
        DROP POLICY IF EXISTS conceptos_nomina_empresa_delete ON public.conceptos_nomina_empresa;
        CREATE POLICY conceptos_nomina_empresa_select ON public.conceptos_nomina_empresa FOR SELECT USING (
            (SELECT public.is_admin())
            OR empresa_id = ANY(public.get_user_companies())
        );
        CREATE POLICY conceptos_nomina_empresa_insert ON public.conceptos_nomina_empresa FOR INSERT WITH CHECK ((SELECT public.is_admin()));
        CREATE POLICY conceptos_nomina_empresa_update ON public.conceptos_nomina_empresa FOR UPDATE USING ((SELECT public.is_admin())) WITH CHECK ((SELECT public.is_admin()));
        CREATE POLICY conceptos_nomina_empresa_delete ON public.conceptos_nomina_empresa FOR DELETE USING ((SELECT public.is_admin()));
    END IF;

    IF to_regclass('public.requisicion_item') IS NOT NULL THEN
        ALTER TABLE public.requisicion_item ENABLE ROW LEVEL SECURITY;
        DROP POLICY IF EXISTS requisicion_item_select ON public.requisicion_item;
        DROP POLICY IF EXISTS requisicion_item_insert ON public.requisicion_item;
        DROP POLICY IF EXISTS requisicion_item_update ON public.requisicion_item;
        DROP POLICY IF EXISTS requisicion_item_delete ON public.requisicion_item;
        CREATE POLICY requisicion_item_select ON public.requisicion_item FOR SELECT USING (
            (SELECT public.is_admin())
            OR requisicion_id IN (
                SELECT r.id FROM public.requisicion r
                WHERE r.empresa_id = ANY(public.get_user_companies())
            )
        );
        CREATE POLICY requisicion_item_insert ON public.requisicion_item FOR INSERT WITH CHECK ((SELECT public.is_admin()));
        CREATE POLICY requisicion_item_update ON public.requisicion_item FOR UPDATE USING ((SELECT public.is_admin())) WITH CHECK ((SELECT public.is_admin()));
        CREATE POLICY requisicion_item_delete ON public.requisicion_item FOR DELETE USING ((SELECT public.is_admin()));
    END IF;

    IF to_regclass('public.contrato_item') IS NOT NULL THEN
        ALTER TABLE public.contrato_item ENABLE ROW LEVEL SECURITY;
        DROP POLICY IF EXISTS contrato_item_select ON public.contrato_item;
        DROP POLICY IF EXISTS contrato_item_insert ON public.contrato_item;
        DROP POLICY IF EXISTS contrato_item_update ON public.contrato_item;
        DROP POLICY IF EXISTS contrato_item_delete ON public.contrato_item;
        CREATE POLICY contrato_item_select ON public.contrato_item FOR SELECT USING (
            (SELECT public.is_admin())
            OR contrato_id IN (
                SELECT c.id FROM public.contratos c
                WHERE c.empresa_id = ANY(public.get_user_companies())
            )
        );
        CREATE POLICY contrato_item_insert ON public.contrato_item FOR INSERT WITH CHECK ((SELECT public.is_admin()));
        CREATE POLICY contrato_item_update ON public.contrato_item FOR UPDATE USING ((SELECT public.is_admin())) WITH CHECK ((SELECT public.is_admin()));
        CREATE POLICY contrato_item_delete ON public.contrato_item FOR DELETE USING ((SELECT public.is_admin()));
    END IF;

    IF to_regclass('public.contrato_categorias') IS NOT NULL THEN
        ALTER TABLE public.contrato_categorias ENABLE ROW LEVEL SECURITY;
        DROP POLICY IF EXISTS contrato_categorias_select ON public.contrato_categorias;
        DROP POLICY IF EXISTS contrato_categorias_insert ON public.contrato_categorias;
        DROP POLICY IF EXISTS contrato_categorias_update ON public.contrato_categorias;
        DROP POLICY IF EXISTS contrato_categorias_delete ON public.contrato_categorias;
        CREATE POLICY contrato_categorias_select ON public.contrato_categorias FOR SELECT USING (
            (SELECT public.is_admin())
            OR contrato_id IN (
                SELECT c.id FROM public.contratos c
                WHERE c.empresa_id = ANY(public.get_user_companies())
            )
        );
        CREATE POLICY contrato_categorias_insert ON public.contrato_categorias FOR INSERT WITH CHECK ((SELECT public.is_admin()));
        CREATE POLICY contrato_categorias_update ON public.contrato_categorias FOR UPDATE USING ((SELECT public.is_admin())) WITH CHECK ((SELECT public.is_admin()));
        CREATE POLICY contrato_categorias_delete ON public.contrato_categorias FOR DELETE USING ((SELECT public.is_admin()));
    END IF;

    IF to_regclass('public.sedes') IS NOT NULL THEN
        ALTER TABLE public.sedes ENABLE ROW LEVEL SECURITY;
        DROP POLICY IF EXISTS "Permitir lectura de sedes" ON public.sedes;
        DROP POLICY IF EXISTS "Permitir escritura de sedes" ON public.sedes;
        CREATE POLICY sedes_select ON public.sedes FOR SELECT USING ((SELECT auth.uid()) IS NOT NULL);
        CREATE POLICY sedes_insert ON public.sedes FOR INSERT WITH CHECK ((SELECT public.is_admin()));
        CREATE POLICY sedes_update ON public.sedes FOR UPDATE USING ((SELECT public.is_admin())) WITH CHECK ((SELECT public.is_admin()));
        CREATE POLICY sedes_delete ON public.sedes FOR DELETE USING ((SELECT public.is_admin()));
    END IF;

    IF to_regclass('public.contactos_buap') IS NOT NULL THEN
        ALTER TABLE public.contactos_buap ENABLE ROW LEVEL SECURITY;
        DROP POLICY IF EXISTS "Permitir lectura de contactos_buap" ON public.contactos_buap;
        DROP POLICY IF EXISTS "Permitir escritura de contactos_buap" ON public.contactos_buap;
        CREATE POLICY contactos_buap_select ON public.contactos_buap FOR SELECT USING ((SELECT auth.uid()) IS NOT NULL);
        CREATE POLICY contactos_buap_insert ON public.contactos_buap FOR INSERT WITH CHECK ((SELECT public.is_admin()));
        CREATE POLICY contactos_buap_update ON public.contactos_buap FOR UPDATE USING ((SELECT public.is_admin())) WITH CHECK ((SELECT public.is_admin()));
        CREATE POLICY contactos_buap_delete ON public.contactos_buap FOR DELETE USING ((SELECT public.is_admin()));
    END IF;

    IF to_regclass('public.horarios') IS NOT NULL THEN
        ALTER TABLE public.horarios ENABLE ROW LEVEL SECURITY;
        DROP POLICY IF EXISTS horarios_select_policy ON public.horarios;
        DROP POLICY IF EXISTS horarios_write_policy ON public.horarios;
        CREATE POLICY horarios_select ON public.horarios FOR SELECT USING (
            (SELECT public.is_admin())
            OR empresa_id = ANY(public.get_user_companies())
        );
        CREATE POLICY horarios_insert ON public.horarios FOR INSERT WITH CHECK ((SELECT public.is_admin()));
        CREATE POLICY horarios_update ON public.horarios FOR UPDATE USING ((SELECT public.is_admin())) WITH CHECK ((SELECT public.is_admin()));
        CREATE POLICY horarios_delete ON public.horarios FOR DELETE USING ((SELECT public.is_admin()));
    END IF;

    IF to_regclass('public.supervisor_sedes') IS NOT NULL THEN
        ALTER TABLE public.supervisor_sedes ENABLE ROW LEVEL SECURITY;
        DROP POLICY IF EXISTS supervisor_sedes_select_policy ON public.supervisor_sedes;
        DROP POLICY IF EXISTS supervisor_sedes_write_policy ON public.supervisor_sedes;
        CREATE POLICY supervisor_sedes_select ON public.supervisor_sedes FOR SELECT USING (
            (SELECT public.is_admin())
            OR empresa_id = ANY(public.get_user_companies())
        );
        CREATE POLICY supervisor_sedes_insert ON public.supervisor_sedes FOR INSERT WITH CHECK ((SELECT public.is_admin()));
        CREATE POLICY supervisor_sedes_update ON public.supervisor_sedes FOR UPDATE USING ((SELECT public.is_admin())) WITH CHECK ((SELECT public.is_admin()));
        CREATE POLICY supervisor_sedes_delete ON public.supervisor_sedes FOR DELETE USING ((SELECT public.is_admin()));
    END IF;

    IF to_regclass('public.jornadas') IS NOT NULL THEN
        ALTER TABLE public.jornadas ENABLE ROW LEVEL SECURITY;
        DROP POLICY IF EXISTS jornadas_select_policy ON public.jornadas;
        DROP POLICY IF EXISTS jornadas_write_policy ON public.jornadas;
        CREATE POLICY jornadas_select ON public.jornadas FOR SELECT USING (
            (SELECT public.is_admin())
            OR empresa_id = ANY(public.get_user_companies())
        );
        CREATE POLICY jornadas_insert ON public.jornadas FOR INSERT WITH CHECK ((SELECT public.is_admin()));
        CREATE POLICY jornadas_update ON public.jornadas FOR UPDATE USING ((SELECT public.is_admin())) WITH CHECK ((SELECT public.is_admin()));
        CREATE POLICY jornadas_delete ON public.jornadas FOR DELETE USING ((SELECT public.is_admin()));
    END IF;

    IF to_regclass('public.incidencias_asistencia') IS NOT NULL THEN
        ALTER TABLE public.incidencias_asistencia ENABLE ROW LEVEL SECURITY;
        DROP POLICY IF EXISTS incidencias_asistencia_select_policy ON public.incidencias_asistencia;
        DROP POLICY IF EXISTS incidencias_asistencia_write_policy ON public.incidencias_asistencia;
        CREATE POLICY incidencias_asistencia_select ON public.incidencias_asistencia FOR SELECT USING (
            (SELECT public.is_admin())
            OR empresa_id = ANY(public.get_user_companies())
        );
        CREATE POLICY incidencias_asistencia_insert ON public.incidencias_asistencia FOR INSERT WITH CHECK ((SELECT public.is_admin()));
        CREATE POLICY incidencias_asistencia_update ON public.incidencias_asistencia FOR UPDATE USING ((SELECT public.is_admin())) WITH CHECK ((SELECT public.is_admin()));
        CREATE POLICY incidencias_asistencia_delete ON public.incidencias_asistencia FOR DELETE USING ((SELECT public.is_admin()));
    END IF;

    IF to_regclass('public.registros_asistencia') IS NOT NULL THEN
        ALTER TABLE public.registros_asistencia ENABLE ROW LEVEL SECURITY;
        DROP POLICY IF EXISTS registros_asistencia_select_policy ON public.registros_asistencia;
        DROP POLICY IF EXISTS registros_asistencia_write_policy ON public.registros_asistencia;
        CREATE POLICY registros_asistencia_select ON public.registros_asistencia FOR SELECT USING (
            (SELECT public.is_admin())
            OR empresa_id = ANY(public.get_user_companies())
        );
        CREATE POLICY registros_asistencia_insert ON public.registros_asistencia FOR INSERT WITH CHECK ((SELECT public.is_admin()));
        CREATE POLICY registros_asistencia_update ON public.registros_asistencia FOR UPDATE USING ((SELECT public.is_admin())) WITH CHECK ((SELECT public.is_admin()));
        CREATE POLICY registros_asistencia_delete ON public.registros_asistencia FOR DELETE USING ((SELECT public.is_admin()));
    END IF;

    IF to_regclass('public.incapacidades') IS NOT NULL THEN
        ALTER TABLE public.incapacidades ENABLE ROW LEVEL SECURITY;
        DROP POLICY IF EXISTS incapacidades_select_policy ON public.incapacidades;
        DROP POLICY IF EXISTS incapacidades_write_policy ON public.incapacidades;
        CREATE POLICY incapacidades_select ON public.incapacidades FOR SELECT USING (
            (SELECT public.is_admin())
            OR empresa_id = ANY(public.get_user_companies())
        );
        CREATE POLICY incapacidades_insert ON public.incapacidades FOR INSERT WITH CHECK ((SELECT public.is_admin()));
        CREATE POLICY incapacidades_update ON public.incapacidades FOR UPDATE USING ((SELECT public.is_admin())) WITH CHECK ((SELECT public.is_admin()));
        CREATE POLICY incapacidades_delete ON public.incapacidades FOR DELETE USING ((SELECT public.is_admin()));
    END IF;

    IF to_regclass('public.certificados_incapacidad') IS NOT NULL THEN
        ALTER TABLE public.certificados_incapacidad ENABLE ROW LEVEL SECURITY;
        DROP POLICY IF EXISTS certificados_incapacidad_select_policy ON public.certificados_incapacidad;
        DROP POLICY IF EXISTS certificados_incapacidad_write_policy ON public.certificados_incapacidad;
        CREATE POLICY certificados_incapacidad_select ON public.certificados_incapacidad FOR SELECT USING (
            (SELECT public.is_admin())
            OR incapacidad_id IN (
                SELECT i.id FROM public.incapacidades i
                WHERE i.empresa_id = ANY(public.get_user_companies())
            )
        );
        CREATE POLICY certificados_incapacidad_insert ON public.certificados_incapacidad FOR INSERT WITH CHECK ((SELECT public.is_admin()));
        CREATE POLICY certificados_incapacidad_update ON public.certificados_incapacidad FOR UPDATE USING ((SELECT public.is_admin())) WITH CHECK ((SELECT public.is_admin()));
        CREATE POLICY certificados_incapacidad_delete ON public.certificados_incapacidad FOR DELETE USING ((SELECT public.is_admin()));
    END IF;

    IF to_regclass('public.cotizacion_items') IS NOT NULL THEN
        ALTER TABLE public.cotizacion_items ENABLE ROW LEVEL SECURITY;
        DROP POLICY IF EXISTS cotizacion_items_select_policy ON public.cotizacion_items;
        DROP POLICY IF EXISTS cotizacion_items_insert_policy ON public.cotizacion_items;
        DROP POLICY IF EXISTS cotizacion_items_update_policy ON public.cotizacion_items;
        DROP POLICY IF EXISTS cotizacion_items_delete_policy ON public.cotizacion_items;
        CREATE POLICY cotizacion_items_select_policy ON public.cotizacion_items FOR SELECT TO authenticated USING (
            public.cotizador_can_access_cotizacion(cotizacion_id)
        );
        CREATE POLICY cotizacion_items_insert_policy ON public.cotizacion_items FOR INSERT TO authenticated WITH CHECK (
            public.cotizador_can_access_cotizacion(cotizacion_id)
        );
        CREATE POLICY cotizacion_items_update_policy ON public.cotizacion_items FOR UPDATE TO authenticated USING (
            public.cotizador_can_access_cotizacion(cotizacion_id)
        ) WITH CHECK (
            public.cotizador_can_access_cotizacion(cotizacion_id)
        );
        CREATE POLICY cotizacion_items_delete_policy ON public.cotizacion_items FOR DELETE TO authenticated USING (
            public.cotizador_can_access_cotizacion(cotizacion_id)
        );
    END IF;
END $$;


-- ============================================================================
-- 4. Reducir superficie de ejecución pública innecesaria
-- ============================================================================

DO $$
BEGIN
    IF to_regprocedure('public.calcular_subtotal_contrato_item()') IS NOT NULL THEN
        REVOKE EXECUTE ON FUNCTION public.calcular_subtotal_contrato_item() FROM anon;
    END IF;
    IF to_regprocedure('public.update_contrato_categorias_fecha_actualizacion()') IS NOT NULL THEN
        REVOKE EXECUTE ON FUNCTION public.update_contrato_categorias_fecha_actualizacion() FROM anon;
    END IF;
    IF to_regprocedure('public.actualizar_estatus_empleado_desde_historial()') IS NOT NULL THEN
        REVOKE EXECUTE ON FUNCTION public.actualizar_estatus_empleado_desde_historial() FROM anon;
    END IF;
END $$;

COMMIT;
