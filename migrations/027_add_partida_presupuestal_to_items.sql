-- ============================================================================
-- Migration: Add partida_presupuestal to requisicion_item
-- Fecha: 2026-02-07
-- Descripcion: Agrega campo partida presupuestal a items de requisicion
-- ============================================================================

ALTER TABLE requisicion_item
    ADD COLUMN IF NOT EXISTS partida_presupuestal VARCHAR(100);

COMMENT ON COLUMN requisicion_item.partida_presupuestal IS
    'Codigo de partida presupuestal asociada al item (ej: 33901)';

-- ============================================================================
-- Rollback
-- ============================================================================
-- ALTER TABLE requisicion_item DROP COLUMN IF EXISTS partida_presupuestal;
