-- =============================================================================
-- Migration 070: Sincronizar estatus desde plaza_actual_id
-- =============================================================================
-- Fase 3 del refactor: fuente unica de verdad para estatus basada en plaza_actual_id
--
-- Objetivo: el estatus se deriva exclusivamente de plaza_actual_id.
-- El trigger de historial delegara a esta logica o quedara deshabilitado.
-- =============================================================================

BEGIN;

-- 1. Funcion de sincronizacion de estatus desde plaza_actual_id
-- Esta es la unica fuente de verdad para el estatus laboral base
CREATE OR REPLACE FUNCTION public.sync_estatus_empleado_desde_plaza()
RETURNS TRIGGER AS $$
BEGIN
    -- Solo reaccionar a cambios en plaza_actual_id o estatus del empleado
    IF TG_OP = 'UPDATE' AND (
        OLD.plaza_actual_id IS NOT DISTINCT FROM NEW.plaza_actual_id
    ) THEN
        RETURN NEW;
    END IF;

    -- Calcular nuevo estatus basado en plaza_actual_id
    UPDATE public.empleados
    SET estatus = CASE
            WHEN NEW.plaza_actual_id IS NOT NULL THEN 'ACTIVO'::public.estatus_empleado
            ELSE 'INACTIVO'::public.estatus_empleado
        END,
        fecha_actualizacion = NOW()
    WHERE id = NEW.id
      AND COALESCE(estatus::text, '') NOT IN ('BAJA', 'SUSPENDIDO');

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 2. Trigger sobre empleados para sincronizar estatus cuando cambia plaza_actual_id
DROP TRIGGER IF EXISTS trg_sync_estatus_desde_plaza ON public.empleados;
CREATE TRIGGER trg_sync_estatus_desde_plaza
AFTER UPDATE OF plaza_actual_id ON public.empleados
FOR EACH ROW
WHEN (OLD.plaza_actual_id IS DISTINCT FROM NEW.plaza_actual_id)
EXECUTE FUNCTION public.sync_estatus_empleado_desde_plaza();

-- 3. Deshabilitar el trigger viejo de historial para evitar conflictos
-- El historial queda solo como bitacora, no decide estatus
DROP TRIGGER IF EXISTS trg_actualizar_estatus_empleado ON public.historial_laboral;

-- 4. Sincronizar todos los empleados que tienen plaza pero estatus desalineado
UPDATE public.empleados e
SET estatus = 'ACTIVO'::public.estatus_empleado,
    fecha_actualizacion = NOW()
WHERE e.plaza_actual_id IS NOT NULL
  AND e.estatus = 'INACTIVO'::public.estatus_empleado
  AND COALESCE(e.estatus::text, '') NOT IN ('BAJA', 'SUSPENDIDO');

-- 5. Asegurar que los que no tienen plaza esten en INACTIVO
UPDATE public.empleados e
SET estatus = 'INACTIVO'::public.estatus_empleado,
    fecha_actualizacion = NOW()
WHERE e.plaza_actual_id IS NULL
  AND e.estatus = 'ACTIVO'::public.estatus_empleado
  AND COALESCE(e.estatus::text, '') NOT IN ('BAJA', 'SUSPENDIDO');

COMMENT ON FUNCTION public.sync_estatus_empleado_desde_plaza() IS
'Sincroniza el estatus del empleado segun plaza_actual_id.
ACTIVO si tiene plaza, INACTIVO si no tiene.
No sobreescribe BAJA ni SUSPENDIDO.';

COMMENT ON TRIGGER trg_sync_estatus_desde_plaza ON public.empleados IS
'Trigger que mantiene estatus laboral actualizado segun plaza_actual_id.
Es la fuente unica de verdad para el estado activo/inactivo.';

COMMIT;