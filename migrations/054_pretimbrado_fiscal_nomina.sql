-- =============================================================================
-- Migración 054: Pre-timbrado fiscal para nómina
--
-- Cambios:
--   - Agrega jornada y factor proporcional a plazas
--   - Agrega snapshots fiscales y readiness a nominas_empleado
--   - Agrega readiness consolidado y snapshot fiscal a periodos_nomina
-- =============================================================================

BEGIN;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_type
        WHERE typname = 'tipo_jornada_plaza'
    ) THEN
        CREATE TYPE public.tipo_jornada_plaza AS ENUM (
            'COMPLETA',
            'MEDIA_JORNADA',
            'POR_HORAS'
        );
    END IF;
END $$;

ALTER TABLE public.plazas
    ADD COLUMN IF NOT EXISTS tipo_jornada public.tipo_jornada_plaza,
    ADD COLUMN IF NOT EXISTS factor_jornada DECIMAL(4,2);

UPDATE public.plazas
SET
    tipo_jornada = COALESCE(tipo_jornada, 'COMPLETA'),
    factor_jornada = COALESCE(factor_jornada, 1.00)
WHERE tipo_jornada IS NULL
   OR factor_jornada IS NULL;

ALTER TABLE public.plazas
    ALTER COLUMN tipo_jornada SET DEFAULT 'COMPLETA',
    ALTER COLUMN tipo_jornada SET NOT NULL,
    ALTER COLUMN factor_jornada SET DEFAULT 1.00,
    ALTER COLUMN factor_jornada SET NOT NULL;

ALTER TABLE public.plazas
    DROP CONSTRAINT IF EXISTS chk_plazas_factor_jornada;

ALTER TABLE public.plazas
    ADD CONSTRAINT chk_plazas_factor_jornada
    CHECK (factor_jornada > 0 AND factor_jornada <= 1);

COMMENT ON COLUMN public.plazas.tipo_jornada IS
'Tipo de jornada de la plaza: completa, media jornada o por horas.';

COMMENT ON COLUMN public.plazas.factor_jornada IS
'Factor proporcional de la jornada. 1.00 = completa, 0.50 = media jornada.';

ALTER TABLE public.nominas_empleado
    ADD COLUMN IF NOT EXISTS tipo_jornada public.tipo_jornada_plaza,
    ADD COLUMN IF NOT EXISTS factor_jornada DECIMAL(4,2),
    ADD COLUMN IF NOT EXISTS salario_minimo_diario_aplicable DECIMAL(10,2) NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS es_salario_minimo_art36 BOOLEAN NOT NULL DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS imss_obrero_absorbido DECIMAL(12,2) NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS listo_para_timbrar BOOLEAN NOT NULL DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS observaciones_fiscales JSONB NOT NULL DEFAULT '[]'::jsonb;

UPDATE public.nominas_empleado
SET
    tipo_jornada = COALESCE(tipo_jornada, 'COMPLETA'),
    factor_jornada = COALESCE(factor_jornada, 1.00),
    observaciones_fiscales = COALESCE(observaciones_fiscales, '[]'::jsonb),
    listo_para_timbrar = CASE
        WHEN estatus = 'APROBADO' THEN TRUE
        ELSE listo_para_timbrar
    END
WHERE tipo_jornada IS NULL
   OR factor_jornada IS NULL
   OR observaciones_fiscales IS NULL;

ALTER TABLE public.nominas_empleado
    ALTER COLUMN tipo_jornada SET DEFAULT 'COMPLETA',
    ALTER COLUMN tipo_jornada SET NOT NULL,
    ALTER COLUMN factor_jornada SET DEFAULT 1.00,
    ALTER COLUMN factor_jornada SET NOT NULL;

ALTER TABLE public.nominas_empleado
    DROP CONSTRAINT IF EXISTS chk_nomina_factor_jornada;

ALTER TABLE public.nominas_empleado
    ADD CONSTRAINT chk_nomina_factor_jornada
    CHECK (factor_jornada > 0 AND factor_jornada <= 1);

COMMENT ON COLUMN public.nominas_empleado.tipo_jornada IS
'Snapshot de la jornada vigente de la plaza al generar la nómina.';

COMMENT ON COLUMN public.nominas_empleado.factor_jornada IS
'Snapshot del factor proporcional de jornada.';

COMMENT ON COLUMN public.nominas_empleado.salario_minimo_diario_aplicable IS
'Salario mínimo diario aplicable por fecha de pago y zona fiscal.';

COMMENT ON COLUMN public.nominas_empleado.es_salario_minimo_art36 IS
'True si la nómina califica como salario mínimo jornada completa para Art. 36 LSS.';

COMMENT ON COLUMN public.nominas_empleado.imss_obrero_absorbido IS
'Monto de IMSS obrero absorbido por el patrón cuando aplica Art. 36 LSS.';

COMMENT ON COLUMN public.nominas_empleado.listo_para_timbrar IS
'Indicador de readiness fiscal por empleado para pre-timbrado.';

COMMENT ON COLUMN public.nominas_empleado.observaciones_fiscales IS
'Lista serializada de observaciones fiscales por empleado. Cada item incluye código, mensaje y severidad.';

ALTER TABLE public.periodos_nomina
    ADD COLUMN IF NOT EXISTS zona_frontera BOOLEAN,
    ADD COLUMN IF NOT EXISTS aplicar_art_36 BOOLEAN,
    ADD COLUMN IF NOT EXISTS listo_para_timbrar BOOLEAN NOT NULL DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS total_empleados_con_observaciones_fiscales INTEGER NOT NULL DEFAULT 0;

UPDATE public.periodos_nomina pn
SET
    zona_frontera = COALESCE(
        pn.zona_frontera,
        cfe.zona_frontera,
        FALSE
    ),
    aplicar_art_36 = COALESCE(
        pn.aplicar_art_36,
        cfe.aplicar_art_36,
        TRUE
    ),
    listo_para_timbrar = CASE
        WHEN pn.estatus = 'CERRADO' THEN TRUE
        ELSE pn.listo_para_timbrar
    END,
    total_empleados_con_observaciones_fiscales = COALESCE(
        pn.total_empleados_con_observaciones_fiscales,
        0
    )
FROM public.configuracion_fiscal_empresa cfe
WHERE cfe.empresa_id = pn.empresa_id
  AND (
    pn.zona_frontera IS NULL
    OR pn.aplicar_art_36 IS NULL
  );

UPDATE public.periodos_nomina
SET
    zona_frontera = COALESCE(zona_frontera, FALSE),
    aplicar_art_36 = COALESCE(aplicar_art_36, TRUE)
WHERE zona_frontera IS NULL
   OR aplicar_art_36 IS NULL;

ALTER TABLE public.periodos_nomina
    ALTER COLUMN zona_frontera SET DEFAULT FALSE,
    ALTER COLUMN zona_frontera SET NOT NULL,
    ALTER COLUMN aplicar_art_36 SET DEFAULT TRUE,
    ALTER COLUMN aplicar_art_36 SET NOT NULL;

ALTER TABLE public.periodos_nomina
    DROP CONSTRAINT IF EXISTS chk_periodo_total_obs_fiscales;

ALTER TABLE public.periodos_nomina
    ADD CONSTRAINT chk_periodo_total_obs_fiscales
    CHECK (total_empleados_con_observaciones_fiscales >= 0);

COMMENT ON COLUMN public.periodos_nomina.zona_frontera IS
'Snapshot de la zona fiscal de salario mínimo usada por el período.';

COMMENT ON COLUMN public.periodos_nomina.aplicar_art_36 IS
'Snapshot de la configuración fiscal de absorción de IMSS obrero (Art. 36 LSS).';

COMMENT ON COLUMN public.periodos_nomina.listo_para_timbrar IS
'Indicador consolidado de readiness fiscal del período para pre-timbrado.';

COMMENT ON COLUMN public.periodos_nomina.total_empleados_con_observaciones_fiscales IS
'Cantidad de empleados del período con observaciones fiscales registradas.';

CREATE INDEX IF NOT EXISTS idx_nominas_empleado_listo_timbrar
    ON public.nominas_empleado (periodo_id, listo_para_timbrar);

CREATE INDEX IF NOT EXISTS idx_periodos_nomina_listo_timbrar
    ON public.periodos_nomina (empresa_id, listo_para_timbrar);

COMMIT;
