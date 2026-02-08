-- ============================================================================
-- Migration: Permitir numero_requisicion NULL para borradores
-- Fecha: 2026-02-07
-- Descripcion: Los borradores no reciben numero hasta que se envian.
--              Se cambia NOT NULL a nullable y se usa partial unique index
--              para que solo se aplique unicidad cuando hay numero asignado.
-- ============================================================================

-- 1. Quitar constraint NOT NULL
ALTER TABLE requisicion
    ALTER COLUMN numero_requisicion DROP NOT NULL;

-- 2. Quitar el UNIQUE constraint original
ALTER TABLE requisicion
    DROP CONSTRAINT IF EXISTS requisicion_numero_requisicion_key;

-- 3. Poner NULL donde hay string vacio (limpieza)
UPDATE requisicion
    SET numero_requisicion = NULL
    WHERE numero_requisicion = '';

-- 4. Crear partial unique index (solo para valores no-NULL)
CREATE UNIQUE INDEX IF NOT EXISTS idx_requisicion_numero_unique
    ON requisicion (numero_requisicion)
    WHERE numero_requisicion IS NOT NULL;

-- 5. Actualizar default
ALTER TABLE requisicion
    ALTER COLUMN numero_requisicion SET DEFAULT NULL;

-- ============================================================================
-- Rollback
-- ============================================================================
-- DROP INDEX IF EXISTS idx_requisicion_numero_unique;
-- UPDATE requisicion SET numero_requisicion = 'REQ-TEMP-' || id WHERE numero_requisicion IS NULL;
-- ALTER TABLE requisicion ALTER COLUMN numero_requisicion SET NOT NULL;
-- ALTER TABLE requisicion ADD CONSTRAINT requisicion_numero_requisicion_key UNIQUE (numero_requisicion);
