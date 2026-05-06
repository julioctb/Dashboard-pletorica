-- =============================================================================
-- Migration 069: Agregar plaza_actual_id a empleados
-- =============================================================================
-- Fase 2 del refactor: fuente unica de verdad para plaza vigente del empleado
--
-- Objetivo: tener una columna plaza_actual_id mantenida por trigger desde plazas.
-- Esto permite consultar rapidamente la plaza actual sin hacer subquery a plazas.
-- =============================================================================

BEGIN;

-- 1. Agregar columna plaza_actual_id
ALTER TABLE public.empleados
    ADD COLUMN IF NOT EXISTS plaza_actual_id INTEGER
        REFERENCES public.plazas(id) ON DELETE SET NULL;

-- 2. Crear indice para lecturas rapidas
CREATE INDEX IF NOT EXISTS idx_empleados_plaza_actual
    ON public.empleados(plaza_actual_id) WHERE plaza_actual_id IS NOT NULL;

COMMENT ON COLUMN public.empleados.plaza_actual_id IS
'Plaza vigente del empleado. Sincronizada por trigger desde plazas.empleado_id.
NULL cuando el empleado no tiene plaza asignada (laboralmente inactivo).';

-- 3. Backfill: poblar plaza_actual_id desde plazas existentes
UPDATE public.empleados e
SET plaza_actual_id = pl.id,
    fecha_actualizacion = NOW()
FROM public.plazas pl
WHERE pl.empleado_id = e.id
  AND pl.estatus = 'OCUPADA'::public.estatus_plaza
  AND e.plaza_actual_id IS NULL;

-- 4. Trigger para sincronizar plaza_actual_id cuando plazas.empleado_id cambia
CREATE OR REPLACE FUNCTION public.sync_empleado_plaza_actual()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        IF NEW.empleado_id IS NOT NULL THEN
            UPDATE public.empleados
            SET plaza_actual_id = NEW.id,
                fecha_actualizacion = NOW()
            WHERE id = NEW.empleado_id;
        END IF;

    ELSIF TG_OP = 'UPDATE' THEN
        IF OLD.empleado_id IS DISTINCT FROM NEW.empleado_id THEN
            -- Quitar al empleado anterior
            IF OLD.empleado_id IS NOT NULL THEN
                UPDATE public.empleados
                SET plaza_actual_id = NULL,
                    fecha_actualizacion = NOW()
                WHERE id = OLD.empleado_id AND plaza_actual_id = OLD.id;
            END IF;
            -- Asignar al nuevo
            IF NEW.empleado_id IS NOT NULL THEN
                UPDATE public.empleados
                SET plaza_actual_id = NEW.id,
                    fecha_actualizacion = NOW()
                WHERE id = NEW.empleado_id;
            END IF;
        END IF;

    ELSIF TG_OP = 'DELETE' THEN
        IF OLD.empleado_id IS NOT NULL THEN
            UPDATE public.empleados
            SET plaza_actual_id = NULL,
                fecha_actualizacion = NOW()
            WHERE id = OLD.empleado_id AND plaza_actual_id = OLD.id;
        END IF;
    END IF;

    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_sync_empleado_plaza_actual ON public.plazas;
CREATE TRIGGER trg_sync_empleado_plaza_actual
AFTER INSERT OR UPDATE OF empleado_id OR DELETE ON public.plazas
FOR EACH ROW
EXECUTE FUNCTION public.sync_empleado_plaza_actual();

-- 5. Garantizar unicidad: solo una plaza OCUPADA por empleado
-- Esto evita el caso donde dos plazas queden con el mismo empleado_id
CREATE UNIQUE INDEX IF NOT EXISTS idx_plazas_empleado_ocupada
    ON public.plazas(empleado_id)
    WHERE estatus = 'OCUPADA'::public.estatus_plaza;

COMMENT ON INDEX idx_plazas_empleado_ocupada IS
'Garantiza que un empleado solo pueda tener una plaza OCUPADA a la vez.
Previene inconsistencias en plaza_actual_id.';

COMMIT;