-- ============================================================================
-- Migration: Ampliar campos de texto en requisicion
-- Fecha: 2026-02-07
-- Descripcion: Varios campos de requisicion tenian VARCHAR(100) que es
--              insuficiente para texto descriptivo. Se amplian.
-- ============================================================================

ALTER TABLE requisicion
    ALTER COLUMN tipo_garantia TYPE VARCHAR(500),
    ALTER COLUMN forma_pago TYPE VARCHAR(500),
    ALTER COLUMN garantia_vigencia TYPE VARCHAR(255),
    ALTER COLUMN existencia_almacen TYPE VARCHAR(255);

-- ============================================================================
-- Rollback
-- ============================================================================
-- ALTER TABLE requisicion
--     ALTER COLUMN tipo_garantia TYPE VARCHAR(100),
--     ALTER COLUMN forma_pago TYPE VARCHAR(100),
--     ALTER COLUMN garantia_vigencia TYPE VARCHAR(100),
--     ALTER COLUMN existencia_almacen TYPE VARCHAR(100);
