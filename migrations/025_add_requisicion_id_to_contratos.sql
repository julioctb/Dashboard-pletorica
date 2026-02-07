-- ============================================================================
-- Migration: Add requisicion_id to Contratos
-- Fecha: 2026-02-06
-- Descripcion: Vincula contratos con su requisicion de origen.
--              NULLABLE para no romper contratos existentes (legacy).
--              La regla NOT NULL se aplica a nivel de aplicacion para
--              nuevos contratos.
-- ============================================================================

-- 1. Agregar columna FK a requisicion
ALTER TABLE contratos
    ADD COLUMN IF NOT EXISTS requisicion_id INTEGER REFERENCES requisicion(id);

-- 2. Indice para consultas por requisicion
CREATE INDEX IF NOT EXISTS idx_contratos_requisicion_id
ON contratos(requisicion_id);

-- 3. Comentarios de documentacion
COMMENT ON COLUMN contratos.requisicion_id IS
    'FK a la requisicion que origino este contrato. NULL solo para contratos legacy.';

-- ============================================================================
-- Rollback (if you need to revert)
-- ============================================================================
-- DROP INDEX IF EXISTS idx_contratos_requisicion_id;
-- ALTER TABLE contratos DROP COLUMN IF EXISTS requisicion_id;
