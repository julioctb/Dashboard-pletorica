-- ============================================================================
-- Migration 018: Add empresa_anterior_id to historial_laboral
-- Fecha: 2026-02-01
-- Descripcion: Soporte para reingresos de empleados a otra empresa.
--   Registra de cual empresa provenia el empleado al momento del reingreso.
-- ============================================================================

-- 1. Agregar columna empresa_anterior_id
ALTER TABLE public.historial_laboral
ADD COLUMN IF NOT EXISTS empresa_anterior_id INTEGER REFERENCES public.empresas(id);

-- 2. Comentario descriptivo
COMMENT ON COLUMN public.historial_laboral.empresa_anterior_id
IS 'ID de la empresa anterior del empleado en caso de reingreso (tipo_movimiento=REINGRESO)';

-- 3. Indice para consultas de reingresos
CREATE INDEX IF NOT EXISTS idx_historial_empresa_anterior
ON public.historial_laboral USING btree (empresa_anterior_id)
WHERE empresa_anterior_id IS NOT NULL;

-- 4. Indice para buscar reingresos por tipo de movimiento
CREATE INDEX IF NOT EXISTS idx_historial_tipo_movimiento
ON public.historial_laboral USING btree (tipo_movimiento)
WHERE tipo_movimiento = 'REINGRESO';

-- ============================================================================
-- Rollback (if you need to revert)
-- ============================================================================
-- DROP INDEX IF EXISTS idx_historial_tipo_movimiento;
-- DROP INDEX IF EXISTS idx_historial_empresa_anterior;
-- ALTER TABLE public.historial_laboral DROP COLUMN IF EXISTS empresa_anterior_id;
