-- =============================================================================
-- Migración 044 — Configuración de Dispersión Bancaria
-- =============================================================================
-- Propósito:
--   1. Tabla configuracion_bancos_empresa: qué bancos usa cada empresa para pagar.
--   2. Tabla dispersion_layouts: registro de archivos generados por período/banco.
-- Rollback: ver sección al final.
-- =============================================================================

-- 1. Tabla de configuración de bancos por empresa
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.configuracion_bancos_empresa (
    id               SERIAL PRIMARY KEY,
    empresa_id       INTEGER NOT NULL
                         REFERENCES public.empresas(id) ON DELETE CASCADE,
    nombre_banco     VARCHAR(100) NOT NULL,       -- 'BANREGIO', 'HSBC', 'FONDEADORA', etc.
    formato          VARCHAR(20)  NOT NULL,       -- 'TXT_POSICIONES', 'CSV', 'TXT_CSV'
    cuenta_origen    VARCHAR(30),                 -- Cuenta débito de la empresa
    clabe_origen     VARCHAR(18),                 -- CLABE origen
    referencia_pago  VARCHAR(50),                 -- Ref. fija para estados de cuenta
    activo           BOOLEAN      NOT NULL DEFAULT TRUE,
    fecha_creacion   TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    fecha_actualizacion TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_config_banco_empresa UNIQUE (empresa_id, nombre_banco)
);

COMMENT ON TABLE public.configuracion_bancos_empresa
    IS 'Configuración bancaria por empresa para generación de layouts de dispersión.';

COMMENT ON COLUMN public.configuracion_bancos_empresa.formato
    IS 'TXT_POSICIONES = posiciones fijas Banregio; CSV = CSV estándar; TXT_CSV = delimitado HSBC.';

-- 2. Tabla de layouts generados
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.dispersion_layouts (
    id                SERIAL PRIMARY KEY,
    periodo_id        INTEGER NOT NULL
                          REFERENCES public.periodos_nomina(id) ON DELETE CASCADE,
    empresa_id        INTEGER NOT NULL
                          REFERENCES public.empresas(id) ON DELETE CASCADE,
    nombre_banco      VARCHAR(100) NOT NULL,
    nombre_archivo    VARCHAR(200) NOT NULL,
    storage_path      TEXT         NOT NULL,       -- Ruta en Supabase Storage
    total_empleados   INTEGER      NOT NULL DEFAULT 0,
    total_monto       NUMERIC(14, 2) NOT NULL DEFAULT 0,
    errores           JSONB        NOT NULL DEFAULT '[]'::jsonb,
    generado_por      UUID         REFERENCES auth.users(id),
    fecha_generacion  TIMESTAMPTZ  NOT NULL DEFAULT NOW(),

    -- Permite regenerar (upsert): el último layout por (periodo, banco) es el vigente
    CONSTRAINT uq_dispersion_layout UNIQUE (periodo_id, nombre_banco)
);

COMMENT ON TABLE public.dispersion_layouts
    IS 'Registro de archivos de dispersión bancaria generados por período.';

-- 3. Índices
-- ─────────────────────────────────────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_config_bancos_empresa
    ON public.configuracion_bancos_empresa (empresa_id, activo);

CREATE INDEX IF NOT EXISTS idx_dispersion_layouts_periodo
    ON public.dispersion_layouts (periodo_id);

CREATE INDEX IF NOT EXISTS idx_dispersion_layouts_empresa
    ON public.dispersion_layouts (empresa_id, fecha_generacion DESC);

-- 4. Trigger fecha_actualizacion para configuracion_bancos_empresa
-- ─────────────────────────────────────────────────────────────────────────────
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger
        WHERE tgname = 'set_fecha_actualizacion_config_bancos'
    ) THEN
        CREATE TRIGGER set_fecha_actualizacion_config_bancos
            BEFORE UPDATE ON public.configuracion_bancos_empresa
            FOR EACH ROW EXECUTE FUNCTION update_fecha_actualizacion();
    END IF;
END $$;

-- 5. Seed — configuración de bancos conocidos
-- ─────────────────────────────────────────────────────────────────────────────
DO $$
DECLARE
    v_mantiser_id  INTEGER;
    v_pletorica_id INTEGER;
BEGIN
    -- Buscar empresas por nombre (case-insensitive)
    SELECT id INTO v_mantiser_id
        FROM public.empresas
        WHERE nombre_comercial ILIKE '%mantiser%'
        LIMIT 1;

    SELECT id INTO v_pletorica_id
        FROM public.empresas
        WHERE nombre_comercial ILIKE '%pletórica%' OR nombre_comercial ILIKE '%pletorica%'
        LIMIT 1;

    -- Mantiser: Banregio + Fondeadora
    IF v_mantiser_id IS NOT NULL THEN
        INSERT INTO public.configuracion_bancos_empresa
            (empresa_id, nombre_banco, formato, activo)
        VALUES
            (v_mantiser_id, 'BANREGIO',   'TXT_POSICIONES', TRUE),
            (v_mantiser_id, 'FONDEADORA', 'CSV',            TRUE)
        ON CONFLICT (empresa_id, nombre_banco) DO NOTHING;
    END IF;

    -- Pletórica: HSBC + Fondeadora
    IF v_pletorica_id IS NOT NULL THEN
        INSERT INTO public.configuracion_bancos_empresa
            (empresa_id, nombre_banco, formato, activo)
        VALUES
            (v_pletorica_id, 'HSBC',       'TXT_CSV', TRUE),
            (v_pletorica_id, 'FONDEADORA', 'CSV',     TRUE)
        ON CONFLICT (empresa_id, nombre_banco) DO NOTHING;
    END IF;
END $$;

-- =============================================================================
-- ROLLBACK
-- =============================================================================
-- DROP TRIGGER IF EXISTS set_fecha_actualizacion_config_bancos ON public.configuracion_bancos_empresa;
-- DROP TABLE IF EXISTS public.dispersion_layouts;
-- DROP TABLE IF EXISTS public.configuracion_bancos_empresa;
