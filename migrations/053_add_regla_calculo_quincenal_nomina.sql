-- =============================================================================
-- Migración 053: Regla de cálculo quincenal para nómina
--
-- Cambios:
--   - Agrega regla de cálculo quincenal en configuración operativa
--   - Agrega snapshot de la regla en periodos_nomina
--   - Backfill de configuraciones existentes a MIXTA
-- =============================================================================

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_type
        WHERE typname = 'regla_calculo_quincenal_nomina'
    ) THEN
        CREATE TYPE public.regla_calculo_quincenal_nomina AS ENUM ('REAL', 'MIXTA');
    END IF;
END $$;

ALTER TABLE public.configuracion_operativa_empresa
    ADD COLUMN IF NOT EXISTS regla_calculo_quincenal public.regla_calculo_quincenal_nomina;

ALTER TABLE public.configuracion_operativa_empresa
    ALTER COLUMN regla_calculo_quincenal SET DEFAULT 'MIXTA';

UPDATE public.configuracion_operativa_empresa
SET regla_calculo_quincenal = COALESCE(regla_calculo_quincenal, 'MIXTA')
WHERE regla_calculo_quincenal IS NULL;

ALTER TABLE public.configuracion_operativa_empresa
    ALTER COLUMN regla_calculo_quincenal SET NOT NULL;

COMMENT ON COLUMN public.configuracion_operativa_empresa.regla_calculo_quincenal IS
'Regla de calculo para nomina quincenal: REAL (por dias pagables) o MIXTA (base fija quincenal con descuentos reales).';

ALTER TABLE public.periodos_nomina
    ADD COLUMN IF NOT EXISTS regla_calculo_quincenal public.regla_calculo_quincenal_nomina;

COMMENT ON COLUMN public.periodos_nomina.regla_calculo_quincenal IS
'Snapshot de la regla de calculo quincenal usada por el periodo al momento de generarse o recalcularse.';
