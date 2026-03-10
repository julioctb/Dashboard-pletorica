-- =============================================================================
-- Migración 051: Política de nómina por empresa, períodos calculados
--                y auditoría de creación en nóminas
--
-- Cambios:
--   - Agrega auditoría de creación (creado_por, creado_por_nombre)
--   - Cambia unicidad de periodos_nomina a rango real por empresa
--   - Activa/desactiva el módulo de nómina por empresa
--   - Extiende configuración operativa con política de nómina y contrato base
-- =============================================================================

ALTER TABLE public.empresas
    ADD COLUMN IF NOT EXISTS gestion_nomina_activa BOOLEAN NOT NULL DEFAULT FALSE;

COMMENT ON COLUMN public.empresas.gestion_nomina_activa IS
'Indica si la empresa tiene habilitado el modulo de gestion de nomina.';

CREATE INDEX IF NOT EXISTS idx_empresas_gestion_nomina_activa
    ON public.empresas (gestion_nomina_activa)
    WHERE gestion_nomina_activa = TRUE;

ALTER TABLE public.configuracion_operativa_empresa
    ADD COLUMN IF NOT EXISTS tipo_nomina periodicidad_nomina NOT NULL DEFAULT 'QUINCENAL',
    ADD COLUMN IF NOT EXISTS contrato_nomina_id INTEGER REFERENCES public.contratos(id) ON DELETE SET NULL,
    ADD COLUMN IF NOT EXISTS dia_pago_semanal SMALLINT DEFAULT 5,
    ADD COLUMN IF NOT EXISTS dia_pago_mensual SMALLINT DEFAULT 0;

ALTER TABLE public.configuracion_operativa_empresa
    ALTER COLUMN dia_pago_semanal SET DEFAULT 5,
    ALTER COLUMN dia_pago_mensual SET DEFAULT 0;

UPDATE public.configuracion_operativa_empresa
SET
    dia_pago_semanal = COALESCE(dia_pago_semanal, 5),
    dia_pago_mensual = COALESCE(dia_pago_mensual, 0)
WHERE dia_pago_semanal IS NULL
   OR dia_pago_mensual IS NULL;

ALTER TABLE public.configuracion_operativa_empresa
    DROP CONSTRAINT IF EXISTS chk_config_dia_primera_quincena,
    DROP CONSTRAINT IF EXISTS chk_config_dia_segunda_quincena;

ALTER TABLE public.configuracion_operativa_empresa
    ADD CONSTRAINT chk_config_dia_primera_quincena
    CHECK (dia_pago_primera_quincena BETWEEN 1 AND 31),
    ADD CONSTRAINT chk_config_dia_segunda_quincena
    CHECK (dia_pago_segunda_quincena BETWEEN 0 AND 31);

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'chk_config_dia_pago_semanal'
    ) THEN
        ALTER TABLE public.configuracion_operativa_empresa
            ADD CONSTRAINT chk_config_dia_pago_semanal
            CHECK (dia_pago_semanal IS NULL OR dia_pago_semanal BETWEEN 1 AND 7);
    END IF;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'chk_config_dia_pago_mensual'
    ) THEN
        ALTER TABLE public.configuracion_operativa_empresa
            ADD CONSTRAINT chk_config_dia_pago_mensual
            CHECK (dia_pago_mensual IS NULL OR dia_pago_mensual BETWEEN 0 AND 31);
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_config_operativa_contrato_nomina
    ON public.configuracion_operativa_empresa (contrato_nomina_id)
    WHERE contrato_nomina_id IS NOT NULL;

COMMENT ON COLUMN public.configuracion_operativa_empresa.tipo_nomina IS
'Periodicidad configurada para generar nominas de la empresa: semanal, quincenal o mensual.';

COMMENT ON COLUMN public.configuracion_operativa_empresa.contrato_nomina_id IS
'Contrato base que delimita plazas, incidencias y periodos de nomina de la empresa.';

COMMENT ON COLUMN public.configuracion_operativa_empresa.dia_pago_semanal IS
'Dia de pago semanal usando base 1=Lunes ... 7=Domingo.';

COMMENT ON COLUMN public.configuracion_operativa_empresa.dia_pago_mensual IS
'Dia de pago mensual (0=ultimo dia del mes, 1-31).';

COMMENT ON COLUMN public.configuracion_operativa_empresa.dia_pago_primera_quincena IS
'Dia del mes para pago de primera quincena (1-31).';

COMMENT ON COLUMN public.configuracion_operativa_empresa.dia_pago_segunda_quincena IS
'Dia del mes para pago de segunda quincena (0=ultimo dia del mes, 1-31).';

ALTER TABLE public.periodos_nomina
    ADD COLUMN IF NOT EXISTS creado_por UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    ADD COLUMN IF NOT EXISTS creado_por_nombre VARCHAR(150);

ALTER TABLE public.periodos_nomina
    DROP CONSTRAINT IF EXISTS uq_periodo_empresa_nombre;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'uq_periodo_empresa_rango'
    ) THEN
        ALTER TABLE public.periodos_nomina
            ADD CONSTRAINT uq_periodo_empresa_rango
            UNIQUE (empresa_id, fecha_inicio, fecha_fin);
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_periodos_nomina_creado_por
    ON public.periodos_nomina (creado_por)
    WHERE creado_por IS NOT NULL;

COMMENT ON COLUMN public.periodos_nomina.creado_por IS
'UUID del usuario que genero la nomina/quincena.';

COMMENT ON COLUMN public.periodos_nomina.creado_por_nombre IS
'Snapshot del nombre del usuario que genero la nomina/quincena.';
