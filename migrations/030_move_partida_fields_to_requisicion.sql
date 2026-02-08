-- ============================================================================
-- Migration: Move partida fields to requisicion table
-- Fecha: 2026-02-07
-- Descripcion: Los campos partida_presupuestaria, origen_recurso y
--              oficio_suficiencia son 1 por requisicion, no necesitan tabla
--              separada. Se mueven a la tabla requisicion y se elimina
--              requisicion_partida. Se truncan datos existentes.
-- ============================================================================

-- 1. Agregar campos a requisicion
ALTER TABLE requisicion
    ADD COLUMN IF NOT EXISTS partida_presupuestaria VARCHAR(100),
    ADD COLUMN IF NOT EXISTS origen_recurso VARCHAR(200),
    ADD COLUMN IF NOT EXISTS oficio_suficiencia VARCHAR(200);

COMMENT ON COLUMN requisicion.partida_presupuestaria IS
    'Codigo de partida presupuestal (ej: 33901)';
COMMENT ON COLUMN requisicion.origen_recurso IS
    'Origen del recurso presupuestal';
COMMENT ON COLUMN requisicion.oficio_suficiencia IS
    'Numero de oficio de suficiencia presupuestal';

-- 2. Truncar datos existentes (requisicion_item depende de requisicion via FK CASCADE)
TRUNCATE TABLE requisicion CASCADE;

-- 3. Eliminar tabla requisicion_partida
DROP TABLE IF EXISTS requisicion_partida;

-- ============================================================================
-- Rollback
-- ============================================================================
-- ALTER TABLE requisicion DROP COLUMN IF EXISTS partida_presupuestaria;
-- ALTER TABLE requisicion DROP COLUMN IF EXISTS origen_recurso;
-- ALTER TABLE requisicion DROP COLUMN IF EXISTS oficio_suficiencia;
-- (Recrear requisicion_partida desde migration 006 si es necesario)
