-- ============================================================================
-- Migration: Add inicio_desde_firma to requisiciones
-- Fecha: 2026-02-07
-- Descripcion: Agrega campo booleano para indicar si el periodo de entrega
--              inicia a partir de la firma del contrato
-- ============================================================================

ALTER TABLE requisiciones
    ADD COLUMN IF NOT EXISTS inicio_desde_firma BOOLEAN NOT NULL DEFAULT FALSE;

COMMENT ON COLUMN requisiciones.inicio_desde_firma IS
    'Si es true, el periodo inicia a partir de la firma del contrato (no usa fecha_entrega_inicio)';

-- ============================================================================
-- Rollback
-- ============================================================================
-- ALTER TABLE requisiciones DROP COLUMN IF EXISTS inicio_desde_firma;
