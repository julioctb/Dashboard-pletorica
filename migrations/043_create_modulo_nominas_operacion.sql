-- =============================================================================
-- Migración 043: Módulo Nóminas Operación
--
-- Crea las tablas del flujo operativo de nómina:
--   - periodos_nomina: contenedor principal por empresa/período
--   - nominas_empleado: recibo individual por empleado
--   - nomina_movimientos: desglose de conceptos por recibo
--
-- Prerequisito: 042_create_catalogo_conceptos_nomina.sql
-- Ejecutar en: Supabase Dashboard → SQL Editor
-- Idempotente: Sí (IF NOT EXISTS)
-- =============================================================================

-- =============================================================================
-- 1. ENUMs
-- =============================================================================

DO $$ BEGIN
    CREATE TYPE estatus_periodo_nomina AS ENUM (
        'BORRADOR',
        'EN_PREPARACION_RRHH',
        'ENVIADO_A_CONTABILIDAD',
        'EN_PROCESO_CONTABILIDAD',
        'CALCULADO',
        'CERRADO'
    );
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    CREATE TYPE periodicidad_nomina AS ENUM (
        'SEMANAL',
        'QUINCENAL',
        'MENSUAL'
    );
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    CREATE TYPE origen_movimiento_nomina AS ENUM (
        'SISTEMA',
        'RRHH',
        'CONTABILIDAD'
    );
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    CREATE TYPE estatus_nomina_empleado AS ENUM (
        'PENDIENTE',
        'EN_PROCESO',
        'CALCULADO',
        'APROBADO'
    );
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

-- =============================================================================
-- 2. Tabla: periodos_nomina
-- =============================================================================

CREATE TABLE IF NOT EXISTS public.periodos_nomina (
    id              SERIAL PRIMARY KEY,

    -- Relaciones
    empresa_id      INTEGER NOT NULL REFERENCES public.empresas(id)   ON DELETE CASCADE,
    contrato_id     INTEGER          REFERENCES public.contratos(id)  ON DELETE SET NULL,

    -- Identificación
    nombre          VARCHAR(100) NOT NULL,
    periodicidad    periodicidad_nomina NOT NULL DEFAULT 'QUINCENAL',

    -- Fechas del período
    fecha_inicio    DATE NOT NULL,
    fecha_fin       DATE NOT NULL,
    fecha_pago      DATE,

    -- Workflow
    estatus         estatus_periodo_nomina NOT NULL DEFAULT 'BORRADOR',

    -- Totales (recalculados al calcular/cerrar)
    total_percepciones  DECIMAL(14,2) NOT NULL DEFAULT 0,
    total_deducciones   DECIMAL(14,2) NOT NULL DEFAULT 0,
    total_otros_pagos   DECIMAL(14,2) NOT NULL DEFAULT 0,
    total_neto          DECIMAL(14,2) NOT NULL DEFAULT 0,
    total_empleados     INTEGER       NOT NULL DEFAULT 0,

    -- Workflow — auditoría de transiciones
    enviado_contabilidad_por    UUID,
    enviado_contabilidad_fecha  TIMESTAMPTZ,
    cerrado_por                 UUID,
    fecha_cierre                TIMESTAMPTZ,

    notas           TEXT,

    -- Auditoría
    fecha_creacion      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    fecha_actualizacion TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Constraints
    CONSTRAINT chk_periodo_fechas         CHECK (fecha_fin >= fecha_inicio),
    CONSTRAINT chk_periodo_fecha_pago     CHECK (fecha_pago IS NULL OR fecha_pago >= fecha_inicio),
    CONSTRAINT chk_periodo_total_perc     CHECK (total_percepciones >= 0),
    CONSTRAINT chk_periodo_total_ded      CHECK (total_deducciones >= 0),
    CONSTRAINT chk_periodo_total_otros    CHECK (total_otros_pagos >= 0),
    CONSTRAINT chk_periodo_total_neto     CHECK (total_neto >= 0),
    CONSTRAINT chk_periodo_total_emp      CHECK (total_empleados >= 0),
    CONSTRAINT uq_periodo_empresa_nombre  UNIQUE (empresa_id, nombre)
);

COMMENT ON TABLE  public.periodos_nomina IS 'Contenedor principal de un ciclo de pago. Agrupa los recibos individuales de todos los empleados de una empresa.';
COMMENT ON COLUMN public.periodos_nomina.contrato_id    IS 'Contrato al que pertenece el período. NULL = nómina independiente de contrato.';
COMMENT ON COLUMN public.periodos_nomina.total_neto     IS 'Suma de netos individuales. Se recalcula al cerrar el período.';
COMMENT ON COLUMN public.periodos_nomina.total_empleados IS 'Conteo de nóminas individuales asociadas.';

-- =============================================================================
-- 3. Tabla: nominas_empleado
-- =============================================================================

CREATE TABLE IF NOT EXISTS public.nominas_empleado (
    id              SERIAL PRIMARY KEY,

    -- Relaciones
    periodo_id      INTEGER NOT NULL REFERENCES public.periodos_nomina(id)  ON DELETE CASCADE,
    empleado_id     INTEGER NOT NULL REFERENCES public.empleados(id)         ON DELETE RESTRICT,
    empresa_id      INTEGER NOT NULL REFERENCES public.empresas(id)          ON DELETE CASCADE,

    estatus         estatus_nomina_empleado NOT NULL DEFAULT 'PENDIENTE',

    -- Snapshot de salario (independiente de cambios posteriores)
    salario_diario              DECIMAL(10,2) NOT NULL,
    salario_diario_integrado    DECIMAL(10,2),

    -- Asistencia del período
    dias_periodo        INTEGER       NOT NULL DEFAULT 0,
    dias_trabajados     INTEGER       NOT NULL DEFAULT 0,
    dias_faltas         INTEGER       NOT NULL DEFAULT 0,
    dias_incapacidad    INTEGER       NOT NULL DEFAULT 0,
    dias_vacaciones     INTEGER       NOT NULL DEFAULT 0,
    horas_extra_dobles  DECIMAL(5,2)  NOT NULL DEFAULT 0,
    horas_extra_triples DECIMAL(5,2)  NOT NULL DEFAULT 0,
    domingos_trabajados INTEGER       NOT NULL DEFAULT 0,

    -- Totales (agregados desde nomina_movimientos)
    total_percepciones  DECIMAL(12,2) NOT NULL DEFAULT 0,
    total_deducciones   DECIMAL(12,2) NOT NULL DEFAULT 0,
    total_otros_pagos   DECIMAL(12,2) NOT NULL DEFAULT 0,
    total_neto          DECIMAL(12,2) NOT NULL DEFAULT 0,

    -- Datos bancarios (snapshot)
    banco_destino   VARCHAR(100),
    clabe_destino   VARCHAR(18),

    notas           TEXT,

    -- Auditoría
    fecha_creacion      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    fecha_actualizacion TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Constraints
    CONSTRAINT uq_nomina_periodo_empleado    UNIQUE (periodo_id, empleado_id),
    CONSTRAINT chk_nomina_salario            CHECK (salario_diario > 0),
    CONSTRAINT chk_nomina_sdi               CHECK (salario_diario_integrado IS NULL OR salario_diario_integrado >= 0),
    CONSTRAINT chk_nomina_dias_periodo      CHECK (dias_periodo >= 0),
    CONSTRAINT chk_nomina_dias_trabajados   CHECK (dias_trabajados >= 0),
    CONSTRAINT chk_nomina_dias_faltas       CHECK (dias_faltas >= 0),
    CONSTRAINT chk_nomina_dias_incapacidad  CHECK (dias_incapacidad >= 0),
    CONSTRAINT chk_nomina_dias_vacaciones   CHECK (dias_vacaciones >= 0),
    CONSTRAINT chk_nomina_he_dobles         CHECK (horas_extra_dobles >= 0),
    CONSTRAINT chk_nomina_he_triples        CHECK (horas_extra_triples >= 0),
    CONSTRAINT chk_nomina_domingos          CHECK (domingos_trabajados >= 0),
    CONSTRAINT chk_nomina_total_perc        CHECK (total_percepciones >= 0),
    CONSTRAINT chk_nomina_total_ded         CHECK (total_deducciones >= 0),
    CONSTRAINT chk_nomina_total_otros       CHECK (total_otros_pagos >= 0),
    CONSTRAINT chk_nomina_total_neto        CHECK (total_neto >= 0)
);

COMMENT ON TABLE  public.nominas_empleado IS 'Recibo de nómina individual. Un registro por empleado por período.';
COMMENT ON COLUMN public.nominas_empleado.salario_diario         IS 'Snapshot del salario diario al momento de crear la nómina.';
COMMENT ON COLUMN public.nominas_empleado.salario_diario_integrado IS 'Snapshot del SDI (Salario Diario Integrado = SBC).';

-- =============================================================================
-- 4. Tabla: nomina_movimientos
-- =============================================================================

CREATE TABLE IF NOT EXISTS public.nomina_movimientos (
    id                  SERIAL PRIMARY KEY,

    -- Relaciones
    nomina_empleado_id  INTEGER NOT NULL REFERENCES public.nominas_empleado(id)  ON DELETE CASCADE,
    concepto_id         INTEGER NOT NULL REFERENCES public.conceptos_nomina(id)  ON DELETE RESTRICT,

    -- Clasificación (redundante de conceptos_nomina para performance en consultas)
    tipo                tipo_concepto_nomina     NOT NULL,
    origen              origen_movimiento_nomina NOT NULL DEFAULT 'SISTEMA',

    -- Montos (siempre positivos; tipo determina si suma o resta)
    monto               DECIMAL(12,2) NOT NULL,
    monto_gravable      DECIMAL(12,2) NOT NULL DEFAULT 0,
    monto_exento        DECIMAL(12,2) NOT NULL DEFAULT 0,

    es_automatico       BOOLEAN NOT NULL DEFAULT TRUE,
    notas               VARCHAR(255),
    registrado_por      UUID,

    -- Auditoría
    fecha_creacion      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    fecha_actualizacion TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Constraints
    CONSTRAINT chk_mov_monto            CHECK (monto >= 0),
    CONSTRAINT chk_mov_monto_gravable   CHECK (monto_gravable >= 0),
    CONSTRAINT chk_mov_monto_exento     CHECK (monto_exento >= 0)
);

COMMENT ON TABLE  public.nomina_movimientos IS 'Desglose de conceptos de nómina por recibo individual. Una fila = un concepto aplicado.';
COMMENT ON COLUMN public.nomina_movimientos.tipo         IS 'Redundante de conceptos_nomina.tipo para evitar JOIN en consultas de totales.';
COMMENT ON COLUMN public.nomina_movimientos.monto        IS 'Siempre positivo. El tipo (PERCEPCION/DEDUCCION) determina si suma o resta al neto.';
COMMENT ON COLUMN public.nomina_movimientos.es_automatico IS 'TRUE = calculado por el sistema; FALSE = capturado manualmente por RRHH/Contabilidad.';

-- =============================================================================
-- 5. Índices
-- =============================================================================

-- periodos_nomina
CREATE INDEX IF NOT EXISTS idx_periodos_nomina_empresa
    ON public.periodos_nomina (empresa_id);

CREATE INDEX IF NOT EXISTS idx_periodos_nomina_contrato
    ON public.periodos_nomina (contrato_id)
    WHERE contrato_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_periodos_nomina_estatus
    ON public.periodos_nomina (estatus);

CREATE INDEX IF NOT EXISTS idx_periodos_nomina_empresa_estatus
    ON public.periodos_nomina (empresa_id, estatus);

CREATE INDEX IF NOT EXISTS idx_periodos_nomina_fecha_inicio
    ON public.periodos_nomina (fecha_inicio DESC);

-- nominas_empleado
CREATE INDEX IF NOT EXISTS idx_nominas_empleado_periodo
    ON public.nominas_empleado (periodo_id);

CREATE INDEX IF NOT EXISTS idx_nominas_empleado_empleado
    ON public.nominas_empleado (empleado_id);

CREATE INDEX IF NOT EXISTS idx_nominas_empleado_empresa
    ON public.nominas_empleado (empresa_id);

CREATE INDEX IF NOT EXISTS idx_nominas_empleado_estatus
    ON public.nominas_empleado (periodo_id, estatus);

-- nomina_movimientos
CREATE INDEX IF NOT EXISTS idx_nomina_movimientos_nomina
    ON public.nomina_movimientos (nomina_empleado_id);

CREATE INDEX IF NOT EXISTS idx_nomina_movimientos_concepto
    ON public.nomina_movimientos (concepto_id);

CREATE INDEX IF NOT EXISTS idx_nomina_movimientos_tipo
    ON public.nomina_movimientos (nomina_empleado_id, tipo);

-- =============================================================================
-- 6. Triggers (fecha_actualizacion)
-- =============================================================================

-- Función set_fecha_actualizacion() ya existe desde migración 042.

DROP TRIGGER IF EXISTS trg_periodos_nomina_upd ON public.periodos_nomina;
CREATE TRIGGER trg_periodos_nomina_upd
    BEFORE UPDATE ON public.periodos_nomina
    FOR EACH ROW EXECUTE FUNCTION public.set_fecha_actualizacion();

DROP TRIGGER IF EXISTS trg_nominas_empleado_upd ON public.nominas_empleado;
CREATE TRIGGER trg_nominas_empleado_upd
    BEFORE UPDATE ON public.nominas_empleado
    FOR EACH ROW EXECUTE FUNCTION public.set_fecha_actualizacion();

DROP TRIGGER IF EXISTS trg_nomina_movimientos_upd ON public.nomina_movimientos;
CREATE TRIGGER trg_nomina_movimientos_upd
    BEFORE UPDATE ON public.nomina_movimientos
    FOR EACH ROW EXECUTE FUNCTION public.set_fecha_actualizacion();

-- =============================================================================
-- 7. Seed de verificación (período de prueba — se puede eliminar en prod)
-- =============================================================================

-- (Sin seed de datos reales — los períodos los crea RRHH desde la UI)

-- =============================================================================
-- Rollback (comentado)
-- DROP TABLE IF EXISTS public.nomina_movimientos;
-- DROP TABLE IF EXISTS public.nominas_empleado;
-- DROP TABLE IF EXISTS public.periodos_nomina;
-- DROP TYPE IF EXISTS estatus_nomina_empleado;
-- DROP TYPE IF EXISTS origen_movimiento_nomina;
-- DROP TYPE IF EXISTS periodicidad_nomina;
-- DROP TYPE IF EXISTS estatus_periodo_nomina;
-- =============================================================================
