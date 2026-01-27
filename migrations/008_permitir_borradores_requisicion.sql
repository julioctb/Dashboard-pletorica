-- ============================================================================
-- Migracion 008: Permitir borradores en requisiciones
-- ============================================================================
-- Ejecutar en Supabase SQL Editor
--
-- Permite guardar requisiciones sin completar todos los campos requeridos.
-- Los campos se validan en la capa de presentacion (formulario_completo).
-- ============================================================================

-- Quitar NOT NULL de campos que pueden estar vacios en borradores
ALTER TABLE requisicion ALTER COLUMN tipo_contratacion DROP NOT NULL;
ALTER TABLE requisicion ALTER COLUMN objeto_contratacion DROP NOT NULL;
ALTER TABLE requisicion ALTER COLUMN dependencia_requirente DROP NOT NULL;
ALTER TABLE requisicion ALTER COLUMN titular_nombre DROP NOT NULL;

-- Cambiar campos PDI de VARCHAR(255) a TEXT (texto institucional largo)
ALTER TABLE requisicion ALTER COLUMN pdi_eje TYPE TEXT;
ALTER TABLE requisicion ALTER COLUMN pdi_objetivo TYPE TEXT;
ALTER TABLE requisicion ALTER COLUMN pdi_estrategia TYPE TEXT;
ALTER TABLE requisicion ALTER COLUMN pdi_meta TYPE TEXT;
