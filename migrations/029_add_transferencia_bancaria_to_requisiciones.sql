-- ============================================================================
-- Migration: Add transferencia_bancaria to requisiciones
-- Fecha: 2026-02-07
-- Descripcion: Agrega campo booleano para indicar si el pago es por
--              transferencia bancaria (default true)
-- ============================================================================

ALTER TABLE requisiciones
    ADD COLUMN IF NOT EXISTS transferencia_bancaria BOOLEAN NOT NULL DEFAULT TRUE;

COMMENT ON COLUMN requisiciones.transferencia_bancaria IS
    'Indica si la forma de pago es por transferencia bancaria';

-- ============================================================================
-- Rollback
-- ============================================================================
-- ALTER TABLE requisiciones DROP COLUMN IF EXISTS transferencia_bancaria;
