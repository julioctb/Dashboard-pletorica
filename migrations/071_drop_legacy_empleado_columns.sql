-- =============================================================================
-- Migration 071: Eliminar columnas legacy de empleados
-- =============================================================================
-- Estas columnas ya no son fuente de verdad:
-- - sede_id: se deriva de plaza_actual_id -> plazas.sede_id
-- - fecha_baja/motivo_baja: se derivan de bajas_empleado
-- =============================================================================

BEGIN;

ALTER TABLE public.empleados
    DROP COLUMN IF EXISTS sede_id,
    DROP COLUMN IF EXISTS fecha_baja,
    DROP COLUMN IF EXISTS motivo_baja;

COMMIT;
