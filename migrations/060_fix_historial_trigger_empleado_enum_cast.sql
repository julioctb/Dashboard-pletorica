-- ============================================================================
-- Migration 060: Fix cast de enum en trigger de historial_laboral
-- Fecha: 2026-04-09
-- ============================================================================

BEGIN;

CREATE OR REPLACE FUNCTION public.actualizar_estatus_empleado_desde_historial()
RETURNS TRIGGER AS $$
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
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_actualizar_estatus_empleado ON public.historial_laboral;

CREATE TRIGGER trg_actualizar_estatus_empleado
AFTER INSERT OR UPDATE OR DELETE ON public.historial_laboral
FOR EACH ROW
EXECUTE FUNCTION public.actualizar_estatus_empleado_desde_historial();

COMMIT;
