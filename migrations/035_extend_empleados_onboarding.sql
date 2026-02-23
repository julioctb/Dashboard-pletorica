-- =============================================================================
-- Migration 035: Extender tabla empleados para onboarding SaaS
-- =============================================================================
-- Descripcion: Agrega columnas de datos bancarios, onboarding, autoservicio
--              y vinculacion con auth.users y sedes.
-- Dependencias: 007_create_empleados_table, 014_create_sedes_tables,
--               015_create_user_auth_tables
-- =============================================================================

-- 1. Columnas bancarias
ALTER TABLE public.empleados
    ADD COLUMN IF NOT EXISTS cuenta_bancaria VARCHAR(18),
    ADD COLUMN IF NOT EXISTS banco VARCHAR(100),
    ADD COLUMN IF NOT EXISTS clabe_interbancaria VARCHAR(18);

-- 2. Datos de nacimiento / RENAPO
ALTER TABLE public.empleados
    ADD COLUMN IF NOT EXISTS entidad_nacimiento VARCHAR(100),
    ADD COLUMN IF NOT EXISTS renapo_validado BOOLEAN DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS renapo_fecha_validacion TIMESTAMPTZ;

-- 3. Estatus onboarding
ALTER TABLE public.empleados
    ADD COLUMN IF NOT EXISTS estatus_onboarding VARCHAR(30) DEFAULT 'REGISTRADO';

-- 4. Vinculacion con auth.users (autoservicio)
ALTER TABLE public.empleados
    ADD COLUMN IF NOT EXISTS user_id UUID,
    ADD COLUMN IF NOT EXISTS requiere_cambio_password BOOLEAN DEFAULT TRUE,
    ADD COLUMN IF NOT EXISTS fecha_primer_acceso TIMESTAMPTZ;

-- 5. Vinculacion con sede
ALTER TABLE public.empleados
    ADD COLUMN IF NOT EXISTS sede_id INTEGER;

-- =============================================================================
-- CONSTRAINTS
-- =============================================================================

-- CHECK estatus_onboarding (7 valores)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'chk_empleados_estatus_onboarding'
    ) THEN
        ALTER TABLE public.empleados
            ADD CONSTRAINT chk_empleados_estatus_onboarding
            CHECK (estatus_onboarding IN (
                'REGISTRADO', 'DATOS_PENDIENTES', 'DOCUMENTOS_PENDIENTES',
                'EN_REVISION', 'APROBADO', 'RECHAZADO', 'ACTIVO_COMPLETO'
            ));
    END IF;
END $$;

-- CHECK formato CLABE (18 digitos)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'chk_empleados_clabe_formato'
    ) THEN
        ALTER TABLE public.empleados
            ADD CONSTRAINT chk_empleados_clabe_formato
            CHECK (clabe_interbancaria IS NULL OR clabe_interbancaria ~ '^\d{18}$');
    END IF;
END $$;

-- CHECK formato cuenta_bancaria (10-18 digitos)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'chk_empleados_cuenta_bancaria_formato'
    ) THEN
        ALTER TABLE public.empleados
            ADD CONSTRAINT chk_empleados_cuenta_bancaria_formato
            CHECK (cuenta_bancaria IS NULL OR cuenta_bancaria ~ '^\d{10,18}$');
    END IF;
END $$;

-- FK user_id -> auth.users
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'fk_empleados_user_id'
    ) THEN
        ALTER TABLE public.empleados
            ADD CONSTRAINT fk_empleados_user_id
            FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE SET NULL;
    END IF;
END $$;

-- FK sede_id -> sedes
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'fk_empleados_sede_id'
    ) THEN
        ALTER TABLE public.empleados
            ADD CONSTRAINT fk_empleados_sede_id
            FOREIGN KEY (sede_id) REFERENCES public.sedes(id) ON DELETE SET NULL;
    END IF;
END $$;

-- =============================================================================
-- INDICES
-- =============================================================================

CREATE INDEX IF NOT EXISTS idx_empleados_user_id
    ON public.empleados(user_id) WHERE user_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_empleados_sede_id
    ON public.empleados(sede_id) WHERE sede_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_empleados_estatus_onboarding
    ON public.empleados(estatus_onboarding);

CREATE INDEX IF NOT EXISTS idx_empleados_empresa_onboarding
    ON public.empleados(empresa_id, estatus_onboarding);

-- =============================================================================
-- COMMENTS
-- =============================================================================

COMMENT ON COLUMN public.empleados.cuenta_bancaria IS 'Numero de cuenta bancaria (10-18 digitos)';
COMMENT ON COLUMN public.empleados.banco IS 'Nombre del banco';
COMMENT ON COLUMN public.empleados.clabe_interbancaria IS 'CLABE interbancaria (18 digitos)';
COMMENT ON COLUMN public.empleados.entidad_nacimiento IS 'Entidad federativa de nacimiento';
COMMENT ON COLUMN public.empleados.renapo_validado IS 'Si el CURP fue validado contra RENAPO';
COMMENT ON COLUMN public.empleados.renapo_fecha_validacion IS 'Fecha de la ultima validacion RENAPO';
COMMENT ON COLUMN public.empleados.estatus_onboarding IS 'Estado del proceso de onboarding del empleado';
COMMENT ON COLUMN public.empleados.user_id IS 'UUID del usuario auth.users para autoservicio';
COMMENT ON COLUMN public.empleados.requiere_cambio_password IS 'Si el empleado debe cambiar password en primer acceso';
COMMENT ON COLUMN public.empleados.fecha_primer_acceso IS 'Fecha/hora del primer acceso del empleado';
COMMENT ON COLUMN public.empleados.sede_id IS 'Sede donde trabaja el empleado';

-- =============================================================================
-- Rollback (comentado)
-- =============================================================================
-- ALTER TABLE public.empleados
--     DROP COLUMN IF EXISTS cuenta_bancaria,
--     DROP COLUMN IF EXISTS banco,
--     DROP COLUMN IF EXISTS clabe_interbancaria,
--     DROP COLUMN IF EXISTS entidad_nacimiento,
--     DROP COLUMN IF EXISTS renapo_validado,
--     DROP COLUMN IF EXISTS renapo_fecha_validacion,
--     DROP COLUMN IF EXISTS estatus_onboarding,
--     DROP COLUMN IF EXISTS user_id,
--     DROP COLUMN IF EXISTS requiere_cambio_password,
--     DROP COLUMN IF EXISTS fecha_primer_acceso,
--     DROP COLUMN IF EXISTS sede_id;
