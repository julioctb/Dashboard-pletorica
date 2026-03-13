-- =============================================================================
-- Migración 056: Aguinaldo en nómina y ciclo laboral por fin de contrato
--
-- Cambios:
--   - Separa primer ingreso histórico vs ingreso vigente del empleado
--   - Permite bajas automáticas por fin de contrato con trazabilidad
--   - Agrega períodos especiales de nómina para aguinaldo
--   - Agrega snapshots y overrides de aguinaldo en nominas_empleado
-- =============================================================================

BEGIN;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_type
        WHERE typname = 'tipo_periodo_nomina'
    ) THEN
        CREATE TYPE public.tipo_periodo_nomina AS ENUM (
            'ORDINARIA',
            'AGUINALDO'
        );
    END IF;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_type
        WHERE typname = 'modo_calculo_aguinaldo_nomina'
    ) THEN
        CREATE TYPE public.modo_calculo_aguinaldo_nomina AS ENUM (
            'AUTO',
            'MANUAL'
        );
    END IF;
END $$;

ALTER TABLE public.empleados
    ADD COLUMN IF NOT EXISTS fecha_ingreso_vigente DATE;

UPDATE public.empleados
SET fecha_ingreso_vigente = COALESCE(fecha_ingreso_vigente, fecha_ingreso, CURRENT_DATE)
WHERE fecha_ingreso_vigente IS NULL;

ALTER TABLE public.empleados
    ALTER COLUMN fecha_ingreso_vigente SET DEFAULT CURRENT_DATE,
    ALTER COLUMN fecha_ingreso_vigente SET NOT NULL;

ALTER TABLE public.empleados
    DROP CONSTRAINT IF EXISTS chk_empleados_fechas;

ALTER TABLE public.empleados
    ADD CONSTRAINT chk_empleados_fechas
    CHECK (
        fecha_ingreso_vigente >= fecha_ingreso
        AND (
            fecha_baja IS NULL
            OR fecha_baja >= fecha_ingreso_vigente
        )
    );

COMMENT ON COLUMN public.empleados.fecha_ingreso IS
'Primer ingreso histórico/institucional del empleado. No cambia en reingresos.';

COMMENT ON COLUMN public.empleados.fecha_ingreso_vigente IS
'Inicio de la relación laboral vigente. Se actualiza cuando el empleado reingresa.';

ALTER TABLE public.contratos
    ADD COLUMN IF NOT EXISTS fin_contrato_procesado_at TIMESTAMPTZ;

COMMENT ON COLUMN public.contratos.fin_contrato_procesado_at IS
'Marca idempotente del procesamiento de bajas automáticas por fin de contrato.';

ALTER TABLE public.bajas_empleado
    ALTER COLUMN registrado_por DROP NOT NULL;

ALTER TABLE public.bajas_empleado
    ADD COLUMN IF NOT EXISTS es_automatica BOOLEAN NOT NULL DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS contrato_id_origen INTEGER REFERENCES public.contratos(id) ON DELETE SET NULL;

ALTER TABLE public.bajas_empleado
    DROP CONSTRAINT IF EXISTS chk_baja_fechas;

ALTER TABLE public.bajas_empleado
    ADD CONSTRAINT chk_baja_fechas
    CHECK (
        es_automatica
        OR fecha_efectiva >= fecha_registro
    );

COMMENT ON COLUMN public.bajas_empleado.es_automatica IS
'True cuando la baja fue generada automáticamente por vencimiento de contrato.';

COMMENT ON COLUMN public.bajas_empleado.contrato_id_origen IS
'Contrato origen de la baja automática o del proceso de baja registrado.';

ALTER TABLE public.periodos_nomina
    ADD COLUMN IF NOT EXISTS tipo_periodo public.tipo_periodo_nomina,
    ADD COLUMN IF NOT EXISTS ejercicio_fiscal INTEGER,
    ADD COLUMN IF NOT EXISTS dias_aguinaldo_snapshot INTEGER;

UPDATE public.periodos_nomina
SET
    tipo_periodo = COALESCE(tipo_periodo, 'ORDINARIA'),
    ejercicio_fiscal = COALESCE(
        ejercicio_fiscal,
        EXTRACT(YEAR FROM fecha_inicio)::INTEGER
    )
WHERE tipo_periodo IS NULL
   OR ejercicio_fiscal IS NULL;

ALTER TABLE public.periodos_nomina
    ALTER COLUMN tipo_periodo SET DEFAULT 'ORDINARIA',
    ALTER COLUMN tipo_periodo SET NOT NULL,
    ALTER COLUMN ejercicio_fiscal SET NOT NULL;

ALTER TABLE public.periodos_nomina
    DROP CONSTRAINT IF EXISTS chk_periodos_nomina_dias_aguinaldo_snapshot;

ALTER TABLE public.periodos_nomina
    ADD CONSTRAINT chk_periodos_nomina_dias_aguinaldo_snapshot
    CHECK (
        dias_aguinaldo_snapshot IS NULL
        OR dias_aguinaldo_snapshot >= 15
    );

COMMENT ON COLUMN public.periodos_nomina.tipo_periodo IS
'Clasificación funcional del período: ordinaria o corrida especial de aguinaldo.';

COMMENT ON COLUMN public.periodos_nomina.ejercicio_fiscal IS
'Ejercicio fiscal al que pertenece el período. En ordinaria se deriva del inicio; en aguinaldo identifica la corrida anual.';

COMMENT ON COLUMN public.periodos_nomina.dias_aguinaldo_snapshot IS
'Snapshot de los días de aguinaldo configurados cuando se generó la corrida anual.';

CREATE UNIQUE INDEX IF NOT EXISTS uq_periodos_nomina_aguinaldo_empresa_ejercicio
    ON public.periodos_nomina (empresa_id, ejercicio_fiscal)
    WHERE tipo_periodo = 'AGUINALDO';

CREATE INDEX IF NOT EXISTS idx_periodos_nomina_tipo_ejercicio
    ON public.periodos_nomina (empresa_id, tipo_periodo, ejercicio_fiscal DESC);

ALTER TABLE public.nominas_empleado
    ADD COLUMN IF NOT EXISTS fecha_ingreso_vigente_aguinaldo DATE,
    ADD COLUMN IF NOT EXISTS dias_aguinaldo_snapshot INTEGER,
    ADD COLUMN IF NOT EXISTS dias_laborados_aguinaldo INTEGER NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS factor_proporcional_aguinaldo DECIMAL(8,6) NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS monto_aguinaldo_bruto DECIMAL(12,2) NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS modo_calculo_aguinaldo public.modo_calculo_aguinaldo_nomina NOT NULL DEFAULT 'AUTO',
    ADD COLUMN IF NOT EXISTS monto_aguinaldo_override DECIMAL(12,2),
    ADD COLUMN IF NOT EXISTS notas_aguinaldo_override TEXT;

ALTER TABLE public.nominas_empleado
    DROP CONSTRAINT IF EXISTS chk_nomina_dias_aguinaldo_snapshot,
    DROP CONSTRAINT IF EXISTS chk_nomina_dias_laborados_aguinaldo,
    DROP CONSTRAINT IF EXISTS chk_nomina_factor_proporcional_aguinaldo,
    DROP CONSTRAINT IF EXISTS chk_nomina_monto_aguinaldo_bruto,
    DROP CONSTRAINT IF EXISTS chk_nomina_monto_aguinaldo_override;

ALTER TABLE public.nominas_empleado
    ADD CONSTRAINT chk_nomina_dias_aguinaldo_snapshot
    CHECK (
        dias_aguinaldo_snapshot IS NULL
        OR dias_aguinaldo_snapshot >= 15
    ),
    ADD CONSTRAINT chk_nomina_dias_laborados_aguinaldo
    CHECK (dias_laborados_aguinaldo >= 0),
    ADD CONSTRAINT chk_nomina_factor_proporcional_aguinaldo
    CHECK (factor_proporcional_aguinaldo >= 0 AND factor_proporcional_aguinaldo <= 1),
    ADD CONSTRAINT chk_nomina_monto_aguinaldo_bruto
    CHECK (monto_aguinaldo_bruto >= 0),
    ADD CONSTRAINT chk_nomina_monto_aguinaldo_override
    CHECK (monto_aguinaldo_override IS NULL OR monto_aguinaldo_override >= 0);

COMMENT ON COLUMN public.nominas_empleado.fecha_ingreso_vigente_aguinaldo IS
'Snapshot de la fecha de ingreso vigente usada para el cálculo proporcional del aguinaldo.';

COMMENT ON COLUMN public.nominas_empleado.dias_aguinaldo_snapshot IS
'Snapshot de días de aguinaldo configurados para la corrida especial.';

COMMENT ON COLUMN public.nominas_empleado.dias_laborados_aguinaldo IS
'Días laborados dentro del ejercicio fiscal usados para el factor proporcional del aguinaldo.';

COMMENT ON COLUMN public.nominas_empleado.factor_proporcional_aguinaldo IS
'Factor proporcional del aguinaldo respecto al ejercicio anual completo.';

COMMENT ON COLUMN public.nominas_empleado.monto_aguinaldo_bruto IS
'Monto bruto calculado del aguinaldo antes de override manual.';

COMMENT ON COLUMN public.nominas_empleado.modo_calculo_aguinaldo IS
'AUTO usa cálculo del sistema; MANUAL usa el override capturado por Contabilidad.';

COMMENT ON COLUMN public.nominas_empleado.monto_aguinaldo_override IS
'Monto bruto capturado manualmente por Contabilidad para recalcular la corrida de aguinaldo.';

COMMENT ON COLUMN public.nominas_empleado.notas_aguinaldo_override IS
'Notas del ajuste manual de aguinaldo capturado por Contabilidad.';

CREATE INDEX IF NOT EXISTS idx_nominas_empleado_aguinaldo_periodo
    ON public.nominas_empleado (periodo_id, modo_calculo_aguinaldo);

CREATE INDEX IF NOT EXISTS idx_contratos_fin_contrato_procesado
    ON public.contratos (estatus, fecha_fin, fin_contrato_procesado_at);

COMMIT;
