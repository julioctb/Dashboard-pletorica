-- =============================================================================
-- Migration 068: Fix estatus empleado - requiere plaza asignada
-- =============================================================================
-- Fase 1 del refactor: empleado solo ACTIVO si tiene plaza asignada
--
-- Problema: el trigger de historial marca ACTIVO aunque no haya plaza,
-- porque considera cualquier registro de historial activo (incluido ALTA sin plaza).
--
-- Solucion: el trigger ahora exige plaza_id IS NOT NULL para marcar ACTIVO.
-- =============================================================================

BEGIN;

-- 1. Reemplazar la funcion del trigger para exigir plaza
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
        SELECT 1 FROM information_schema.columns c
        WHERE c.table_schema = 'public'
          AND c.table_name = 'historial_laboral'
          AND c.column_name = 'estatus'
    ) INTO v_tiene_col_estatus;

    IF v_tiene_col_estatus THEN
        SELECT EXISTS (
            SELECT 1 FROM public.historial_laboral hl
            WHERE hl.empleado_id = v_empleado_id
              AND hl.fecha_fin IS NULL
              AND hl.estatus = 'ACTIVA'
              AND hl.plaza_id IS NOT NULL
        ) INTO v_tiene_plaza_activa;
    ELSE
        SELECT EXISTS (
            SELECT 1 FROM public.historial_laboral hl
            WHERE hl.empleado_id = v_empleado_id
              AND hl.fecha_fin IS NULL
              AND hl.plaza_id IS NOT NULL
        ) INTO v_tiene_plaza_activa;
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

-- El trigger se queda igual; solo actualizamos la funcion.
-- No es necesario recrear el trigger porque ya existe.

-- 2. Reparacion one-shot: empleados que quedaron ACTIVO sin plaza vigente
UPDATE public.empleados e
SET estatus = 'INACTIVO'::public.estatus_empleado,
    fecha_actualizacion = NOW()
WHERE e.estatus = 'ACTIVO'::public.estatus_empleado
  AND NOT EXISTS (
      SELECT 1 FROM public.historial_laboral hl
      WHERE hl.empleado_id = e.id
        AND hl.fecha_fin IS NULL
        AND (hl.estatus = 'ACTIVA' OR NOT EXISTS (
            SELECT 1 FROM information_schema.columns c
            WHERE c.table_schema = 'public'
              AND c.table_name = 'historial_laboral'
              AND c.column_name = 'estatus'
        ))
        AND hl.plaza_id IS NOT NULL
  )
  AND NOT EXISTS (
      SELECT 1 FROM public.plazas pl
      WHERE pl.empleado_id = e.id
        AND pl.estatus = 'OCUPADA'::public.estatus_plaza
  );

-- 3. Eliminar registros de historial que no tienen plaza y bloquean la baja
-- Estos registros ALTA sin plaza crean falsos positivos de actividad
UPDATE public.historial_laboral
SET fecha_fin = fecha_inicio
WHERE tipo_movimiento = 'ALTA'
  AND plaza_id IS NULL
  AND fecha_fin IS NULL
  AND EXISTS (
      SELECT 1 FROM public.historial_laboral hl2
      WHERE hl2.empleado_id = historial_laboral.empleado_id
        AND hl2.fecha_fin IS NULL
        AND hl2.plaza_id IS NOT NULL
        AND hl2.id > historial_laboral.id
  );

COMMIT;

COMMENT ON FUNCTION public.actualizar_estatus_empleado_desde_historial() IS
'Trigger que sincroniza estatus de empleado desde historial_laboral. '
'Requiere plaza_id IS NOT NULL para marcar ACTIVO.';