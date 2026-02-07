-- ============================================================================
-- Migration: Add Audit Fields to Requisicion
-- Fecha: 2026-02-06
-- Descripcion: Agrega campos de auditoria (creado_por, aprobado_por,
--              fecha_aprobacion) a la tabla requisicion para tracking
--              de quien crea y aprueba cada requisicion.
-- ============================================================================

-- 1. Agregar columnas de auditoria
ALTER TABLE requisicion
    ADD COLUMN IF NOT EXISTS creado_por UUID REFERENCES auth.users(id),
    ADD COLUMN IF NOT EXISTS aprobado_por UUID REFERENCES auth.users(id),
    ADD COLUMN IF NOT EXISTS fecha_aprobacion TIMESTAMPTZ;

-- 2. Indices para consultas por usuario
CREATE INDEX IF NOT EXISTS idx_requisicion_creado_por
ON requisicion(creado_por);

CREATE INDEX IF NOT EXISTS idx_requisicion_aprobado_por
ON requisicion(aprobado_por);

-- 3. Comentarios de documentacion
COMMENT ON COLUMN requisicion.creado_por IS
    'UUID del usuario que creo la requisicion. FK a auth.users.';

COMMENT ON COLUMN requisicion.aprobado_por IS
    'UUID del usuario que aprobo la requisicion. Debe ser diferente a creado_por. FK a auth.users.';

COMMENT ON COLUMN requisicion.fecha_aprobacion IS
    'Fecha y hora en que se aprobo la requisicion.';

-- ============================================================================
-- Rollback (if you need to revert)
-- ============================================================================
-- DROP INDEX IF EXISTS idx_requisicion_aprobado_por;
-- DROP INDEX IF EXISTS idx_requisicion_creado_por;
-- ALTER TABLE requisicion
--     DROP COLUMN IF EXISTS fecha_aprobacion,
--     DROP COLUMN IF EXISTS aprobado_por,
--     DROP COLUMN IF EXISTS creado_por;
