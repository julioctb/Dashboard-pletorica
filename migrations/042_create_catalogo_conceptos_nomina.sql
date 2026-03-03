-- =============================================================================
-- Migración 042: Catálogo de Conceptos de Nómina
--
-- Crea las tablas del sistema de conceptos de nómina:
--   - conceptos_nomina: catálogo global sincronizado desde Python
--   - conceptos_nomina_empresa: configuración por empresa
--
-- Fuentes legales: SAT CFDI Nómina 4.0, LISR, LSS, LFT
-- Ejecutar en: Supabase Dashboard → SQL Editor
-- Idempotente: Sí (IF NOT EXISTS / ON CONFLICT)
-- =============================================================================

-- =============================================================================
-- 1. ENUMs
-- =============================================================================

DO $$ BEGIN
    CREATE TYPE tipo_concepto_nomina AS ENUM (
        'PERCEPCION',
        'DEDUCCION',
        'OTRO_PAGO'
    );
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    CREATE TYPE tratamiento_isr_enum AS ENUM (
        'GRAVABLE',
        'EXENTO',
        'PARCIALMENTE_EXENTO',
        'NO_APLICA'
    );
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    CREATE TYPE origen_captura_nomina AS ENUM (
        'SISTEMA',
        'RRHH',
        'CONTABILIDAD'
    );
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    CREATE TYPE categoria_concepto_nomina AS ENUM (
        'SUELDO',
        'TIEMPO_EXTRA',
        'PRESTACIONES',
        'BONOS',
        'SEGURIDAD_SOCIAL',
        'IMPUESTOS',
        'CREDITOS',
        'OTROS'
    );
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

-- =============================================================================
-- 2. Tabla: conceptos_nomina (catálogo global)
-- =============================================================================

CREATE TABLE IF NOT EXISTS public.conceptos_nomina (
    id                  SERIAL PRIMARY KEY,

    -- Identificación
    clave               VARCHAR(30)  NOT NULL UNIQUE,
    nombre              VARCHAR(100) NOT NULL,
    descripcion         VARCHAR(500) NOT NULL DEFAULT '',

    -- Clasificación
    tipo                tipo_concepto_nomina    NOT NULL,
    clave_sat           VARCHAR(10)             NOT NULL,
    nombre_sat          VARCHAR(150)            NOT NULL DEFAULT '',
    categoria           categoria_concepto_nomina NOT NULL DEFAULT 'OTROS',

    -- Fiscal
    tratamiento_isr     tratamiento_isr_enum    NOT NULL DEFAULT 'GRAVABLE',
    integra_sbc         BOOLEAN                 NOT NULL DEFAULT TRUE,

    -- Operación
    origen_captura      origen_captura_nomina   NOT NULL DEFAULT 'SISTEMA',
    es_obligatorio      BOOLEAN                 NOT NULL DEFAULT FALSE,
    es_legal            BOOLEAN                 NOT NULL DEFAULT TRUE,
    orden_default       INTEGER                 NOT NULL DEFAULT 0,
    activo              BOOLEAN                 NOT NULL DEFAULT TRUE,

    -- Auditoría
    fecha_creacion      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    fecha_actualizacion TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE  public.conceptos_nomina IS 'Catálogo maestro de conceptos de nómina. Sincronizado desde CatalogoConceptosNomina (Python).';
COMMENT ON COLUMN public.conceptos_nomina.clave        IS 'Clave interna única, ej: SUELDO, AGUINALDO';
COMMENT ON COLUMN public.conceptos_nomina.clave_sat    IS 'Clave del catálogo SAT CFDI Nómina 4.0';
COMMENT ON COLUMN public.conceptos_nomina.es_legal     IS 'TRUE = concepto de ley; FALSE = concepto personalizado de empresa';
COMMENT ON COLUMN public.conceptos_nomina.es_obligatorio IS 'TRUE = aplica a todos los empleados de cualquier empresa';

-- =============================================================================
-- 3. Tabla: conceptos_nomina_empresa (configuración por empresa)
-- =============================================================================

CREATE TABLE IF NOT EXISTS public.conceptos_nomina_empresa (
    id                   SERIAL PRIMARY KEY,

    -- Relación
    empresa_id           INTEGER NOT NULL REFERENCES public.empresas(id) ON DELETE CASCADE,
    concepto_id          INTEGER NOT NULL REFERENCES public.conceptos_nomina(id) ON DELETE RESTRICT,

    -- Configuración de empresa
    activo               BOOLEAN     NOT NULL DEFAULT TRUE,
    nombre_personalizado VARCHAR(100),               -- NULL = usar nombre del catálogo
    orden_recibo         INTEGER     NOT NULL DEFAULT 0,

    -- Auditoría
    fecha_creacion       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    fecha_actualizacion  TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_concepto_empresa UNIQUE (empresa_id, concepto_id)
);

COMMENT ON TABLE  public.conceptos_nomina_empresa IS 'Configuración de conceptos de nómina por empresa. Indica qué conceptos están activos y en qué orden aparecen en el recibo.';
COMMENT ON COLUMN public.conceptos_nomina_empresa.nombre_personalizado IS 'Nombre alternativo para la UI. NULL = usar nombre del catálogo global.';
COMMENT ON COLUMN public.conceptos_nomina_empresa.orden_recibo         IS 'Orden de aparición en el recibo de nómina (override de orden_default del catálogo).';

-- =============================================================================
-- 4. Índices
-- =============================================================================

-- conceptos_nomina
CREATE INDEX IF NOT EXISTS idx_conceptos_nomina_tipo
    ON public.conceptos_nomina (tipo)
    WHERE activo = TRUE;

CREATE INDEX IF NOT EXISTS idx_conceptos_nomina_categoria
    ON public.conceptos_nomina (categoria)
    WHERE activo = TRUE;

CREATE INDEX IF NOT EXISTS idx_conceptos_nomina_origen
    ON public.conceptos_nomina (origen_captura);

CREATE INDEX IF NOT EXISTS idx_conceptos_nomina_obligatorio
    ON public.conceptos_nomina (es_obligatorio)
    WHERE activo = TRUE;

-- conceptos_nomina_empresa
CREATE INDEX IF NOT EXISTS idx_conceptos_nomina_empresa_empresa
    ON public.conceptos_nomina_empresa (empresa_id, activo);

CREATE INDEX IF NOT EXISTS idx_conceptos_nomina_empresa_concepto
    ON public.conceptos_nomina_empresa (concepto_id);

-- =============================================================================
-- 5. Triggers (fecha_actualizacion)
-- =============================================================================

-- Función genérica (puede ya existir en otras migraciones)
CREATE OR REPLACE FUNCTION public.set_fecha_actualizacion()
RETURNS TRIGGER AS $$
BEGIN
    NEW.fecha_actualizacion = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_conceptos_nomina_upd ON public.conceptos_nomina;
CREATE TRIGGER trg_conceptos_nomina_upd
    BEFORE UPDATE ON public.conceptos_nomina
    FOR EACH ROW EXECUTE FUNCTION public.set_fecha_actualizacion();

DROP TRIGGER IF EXISTS trg_conceptos_nomina_empresa_upd ON public.conceptos_nomina_empresa;
CREATE TRIGGER trg_conceptos_nomina_empresa_upd
    BEFORE UPDATE ON public.conceptos_nomina_empresa
    FOR EACH ROW EXECUTE FUNCTION public.set_fecha_actualizacion();

-- =============================================================================
-- 6. Seed: 19 conceptos del catálogo legal
--    ON CONFLICT (clave) DO UPDATE → idempotente, re-ejecutable
-- =============================================================================

INSERT INTO public.conceptos_nomina
    (clave, nombre, descripcion, tipo, clave_sat, nombre_sat, categoria, tratamiento_isr, integra_sbc, origen_captura, es_obligatorio, es_legal, orden_default)
VALUES
    -- PERCEPCIONES
    ('SUELDO',             'Sueldos, Salarios y Asimilados',  'Sueldo base proporcional a días trabajados',          'PERCEPCION', '001', 'Sueldos, Salarios, Rayas y Jornales',      'SUELDO',          'GRAVABLE',             TRUE,  TRUE, 1,  TRUE),
    ('HORAS_EXTRA_DOBLES', 'Horas extra dobles',              'Horas extra dobles (primeras 9 semanales)',            'PERCEPCION', '019', 'Horas extra',                              'TIEMPO_EXTRA',    'PARCIALMENTE_EXENTO',  TRUE,  TRUE, 2,  TRUE),
    ('HORAS_EXTRA_TRIPLES','Horas extra triples',             'Horas extra triples (excedente de 9 semanales)',       'PERCEPCION', '019', 'Horas extra',                              'TIEMPO_EXTRA',    'GRAVABLE',             TRUE,  TRUE, 3,  TRUE),
    ('PRIMA_DOMINICAL',    'Prima dominical',                 'Prima del 25% por trabajar en domingo',                'PERCEPCION', '020', 'Prima dominical',                          'PRESTACIONES',    'PARCIALMENTE_EXENTO',  TRUE,  TRUE, 4,  TRUE),
    ('VACACIONES',         'Vacaciones (pago)',               'Pago de días de vacaciones',                           'PERCEPCION', '001', 'Sueldos, Salarios, Rayas y Jornales',      'PRESTACIONES',    'GRAVABLE',             FALSE, TRUE, 5,  TRUE),
    ('PRIMA_VACACIONAL',   'Prima vacacional',                'Prima vacacional (mínimo 25% LFT)',                    'PERCEPCION', '021', 'Prima vacacional',                         'PRESTACIONES',    'PARCIALMENTE_EXENTO',  FALSE, TRUE, 6,  TRUE),
    ('AGUINALDO',          'Aguinaldo',                       'Aguinaldo anual (mínimo 15 días LFT)',                 'PERCEPCION', '002', 'Gratificación anual (aguinaldo)',           'PRESTACIONES',    'PARCIALMENTE_EXENTO',  FALSE, TRUE, 7,  TRUE),
    ('BONO_PRODUCTIVIDAD', 'Bono de productividad',           'Bono por cumplimiento de metas',                       'PERCEPCION', '038', 'Otros ingresos por salarios',              'BONOS',           'GRAVABLE',             TRUE,  TRUE, 10, TRUE),
    ('BONO_PUNTUALIDAD',   'Premio de puntualidad',           'Premio por puntualidad del trabajador',                'PERCEPCION', '010', 'Premios por puntualidad',                  'BONOS',           'PARCIALMENTE_EXENTO',  TRUE,  TRUE, 11, TRUE),
    ('BONO_ASISTENCIA',    'Premio de asistencia',            'Premio por asistencia del trabajador',                 'PERCEPCION', '009', 'Premios por asistencia',                   'BONOS',           'PARCIALMENTE_EXENTO',  TRUE,  TRUE, 12, TRUE),
    -- OTRO PAGO
    ('SUBSIDIO_EMPLEO',    'Subsidio para el empleo',         'Subsidio al empleo (DOF)',                             'OTRO_PAGO',  '002', 'Subsidio para el empleo',                  'OTROS',           'NO_APLICA',            FALSE, TRUE, 20, TRUE),
    -- DEDUCCIONES
    ('ISR',                'ISR (Impuesto Sobre la Renta)',   'Retención de ISR según tabla Art. 96 LISR',            'DEDUCCION',  '002', 'ISR',                                      'IMPUESTOS',       'NO_APLICA',            FALSE, TRUE, 30, TRUE),
    ('IMSS_OBRERO',        'Cuotas obreras IMSS',            'Cuotas del trabajador al IMSS',                        'DEDUCCION',  '001', 'Seguridad social',                         'SEGURIDAD_SOCIAL','NO_APLICA',            FALSE, TRUE, 31, TRUE),
    ('DESCUENTO_INFONAVIT','Amortización INFONAVIT',          'Descuento por crédito INFONAVIT',                      'DEDUCCION',  '010', 'Aportaciones para el INFONAVIT',           'CREDITOS',        'NO_APLICA',            FALSE, TRUE, 32, TRUE),
    ('DESCUENTO_FONACOT',  'Descuento FONACOT',               'Descuento por crédito FONACOT',                        'DEDUCCION',  '011', 'Descuento por créditos FONACOT',           'CREDITOS',        'NO_APLICA',            FALSE, TRUE, 33, TRUE),
    ('PRESTAMO_EMPRESA',   'Préstamos otorgados por empresa', 'Descuento por préstamo interno',                       'DEDUCCION',  '004', 'Otros',                                    'CREDITOS',        'NO_APLICA',            FALSE, TRUE, 34, TRUE),
    ('PENSION_ALIMENTICIA','Pensión alimenticia',             'Retención por orden judicial',                         'DEDUCCION',  '007', 'Pensión alimenticia',                      'CREDITOS',        'NO_APLICA',            FALSE, TRUE, 35, TRUE),
    ('DESCUENTO_FALTAS',   'Descuento por ausencia',          'Descuento proporcional por faltas',                    'DEDUCCION',  '006', 'Ausencias e incapacidades',                'OTROS',           'NO_APLICA',            FALSE, TRUE, 36, TRUE),
    ('DESCUENTO_INCAPACIDAD','Descuento por incapacidad',     'Descuento por días de incapacidad',                    'DEDUCCION',  '006', 'Ausencias e incapacidades',                'OTROS',           'NO_APLICA',            FALSE, TRUE, 37, TRUE)
ON CONFLICT (clave) DO UPDATE SET
    nombre          = EXCLUDED.nombre,
    descripcion     = EXCLUDED.descripcion,
    tipo            = EXCLUDED.tipo,
    clave_sat       = EXCLUDED.clave_sat,
    nombre_sat      = EXCLUDED.nombre_sat,
    categoria       = EXCLUDED.categoria,
    tratamiento_isr = EXCLUDED.tratamiento_isr,
    integra_sbc     = EXCLUDED.integra_sbc,
    origen_captura  = EXCLUDED.origen_captura,
    es_legal        = EXCLUDED.es_legal,
    orden_default   = EXCLUDED.orden_default,
    fecha_actualizacion = NOW();

-- =============================================================================
-- Rollback (comentado)
-- DROP TABLE IF EXISTS public.conceptos_nomina_empresa;
-- DROP TABLE IF EXISTS public.conceptos_nomina;
-- DROP TYPE IF EXISTS categoria_concepto_nomina;
-- DROP TYPE IF EXISTS origen_captura_nomina;
-- DROP TYPE IF EXISTS tratamiento_isr_enum;
-- DROP TYPE IF EXISTS tipo_concepto_nomina;
-- =============================================================================
