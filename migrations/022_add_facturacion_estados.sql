-- ============================================================================
-- Migration: Add Facturacion States to Entregables
-- Fecha: 2026-02-06
-- Descripcion: Agrega nuevos valores al enum estatus_entregable para el
--              flujo de prefactura/factura/pago, y columnas adicionales
--              a la tabla entregables.
-- Depende de: 019_create_entregables_tables.sql
-- ============================================================================

-- 1. Agregar nuevos valores al enum estatus_entregable
ALTER TYPE estatus_entregable ADD VALUE IF NOT EXISTS 'PREFACTURA_ENVIADA';
ALTER TYPE estatus_entregable ADD VALUE IF NOT EXISTS 'PREFACTURA_RECHAZADA';
ALTER TYPE estatus_entregable ADD VALUE IF NOT EXISTS 'PREFACTURA_APROBADA';
ALTER TYPE estatus_entregable ADD VALUE IF NOT EXISTS 'FACTURADO';
ALTER TYPE estatus_entregable ADD VALUE IF NOT EXISTS 'PAGADO';

-- 2. Agregar columnas para flujo de facturacion
ALTER TABLE public.entregables
ADD COLUMN IF NOT EXISTS observaciones_prefactura VARCHAR(2000),
ADD COLUMN IF NOT EXISTS fecha_prefactura TIMESTAMP WITH TIME ZONE,
ADD COLUMN IF NOT EXISTS fecha_factura TIMESTAMP WITH TIME ZONE,
ADD COLUMN IF NOT EXISTS fecha_pago_registrado TIMESTAMP WITH TIME ZONE,
ADD COLUMN IF NOT EXISTS folio_fiscal VARCHAR(100),
ADD COLUMN IF NOT EXISTS referencia_pago VARCHAR(200);

-- 3. Indice para busquedas por estatus (mejora performance en dashboard)
CREATE INDEX IF NOT EXISTS idx_entregables_estatus
ON public.entregables (estatus);

-- 4. Comentarios
COMMENT ON COLUMN public.entregables.observaciones_prefactura IS 'Observaciones de BUAP al rechazar prefactura';
COMMENT ON COLUMN public.entregables.fecha_prefactura IS 'Fecha en que se envio la prefactura';
COMMENT ON COLUMN public.entregables.fecha_factura IS 'Fecha en que se envio la factura definitiva';
COMMENT ON COLUMN public.entregables.fecha_pago_registrado IS 'Fecha en que BUAP registro el pago';
COMMENT ON COLUMN public.entregables.folio_fiscal IS 'UUID/folio fiscal del CFDI';
COMMENT ON COLUMN public.entregables.referencia_pago IS 'Referencia bancaria del pago';

-- ============================================================================
-- Rollback (if you need to revert)
-- ============================================================================
-- NOTA: ALTER TYPE ... DROP VALUE no existe en PostgreSQL.
-- Para revertir los valores del enum se requiere recrear el tipo.
-- Las columnas se pueden eliminar con:
-- ALTER TABLE public.entregables
--   DROP COLUMN IF EXISTS observaciones_prefactura,
--   DROP COLUMN IF EXISTS fecha_prefactura,
--   DROP COLUMN IF EXISTS fecha_factura,
--   DROP COLUMN IF EXISTS fecha_pago_registrado,
--   DROP COLUMN IF EXISTS folio_fiscal,
--   DROP COLUMN IF EXISTS referencia_pago;
-- DROP INDEX IF EXISTS idx_entregables_estatus;
