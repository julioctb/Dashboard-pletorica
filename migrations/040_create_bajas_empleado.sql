-- =============================================================================
-- Migration 040: Crear tabla bajas_empleado
-- =============================================================================
-- Descripcion: Proceso de baja de empleados con seguimiento de liquidacion.
--   Trackea el ciclo: registro -> comunicacion BUAP (opcional) -> liquidacion -> cierre.
--   Los plazos de liquidacion (15 dias habiles) son los unicos con alerta real.
-- Dependencias: 007_create_empleados_table, 006_create_plazas_table,
--               000_create_empresas, 015_create_user_auth_tables
-- =============================================================================

-- 1. Enum: estatus del proceso de baja
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'estatus_baja') THEN
        CREATE TYPE estatus_baja AS ENUM (
            'INICIADA',
            'COMUNICADA',
            'LIQUIDADA',
            'CERRADA',
            'CANCELADA'
        );
    END IF;
END $$;

-- 2. Enum: estatus de la liquidacion/finiquito
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'estatus_liquidacion') THEN
        CREATE TYPE estatus_liquidacion AS ENUM (
            'NO_APLICA',
            'PENDIENTE',
            'EN_PROCESO',
            'ENTREGADA'
        );
    END IF;
END $$;

-- 3. Tabla principal
CREATE TABLE IF NOT EXISTS public.bajas_empleado (
    id SERIAL PRIMARY KEY,

    -- Relaciones
    empleado_id INTEGER NOT NULL REFERENCES public.empleados(id) ON DELETE RESTRICT,
    empresa_id INTEGER NOT NULL REFERENCES public.empresas(id) ON DELETE RESTRICT,
    plaza_id INTEGER REFERENCES public.plazas(id) ON DELETE SET NULL,

    -- Motivo (reutiliza enum existente motivo_baja de migration 007)
    motivo motivo_baja NOT NULL,
    notas TEXT,

    -- Fechas del proceso
    fecha_registro DATE NOT NULL DEFAULT CURRENT_DATE,
    fecha_efectiva DATE NOT NULL,

    -- Comunicacion a BUAP (tracking opcional, sin deadline estricto)
    fecha_comunicacion_buap DATE,

    -- Liquidacion/finiquito (UNICO plazo con alerta real: 15 dias habiles)
    fecha_limite_liquidacion DATE NOT NULL,
    estatus_liquidacion estatus_liquidacion NOT NULL DEFAULT 'PENDIENTE',

    -- Sustitucion (dato informativo - BUAP decide y busca personal)
    requiere_sustitucion BOOLEAN DEFAULT NULL,

    -- Estado del proceso
    estatus estatus_baja NOT NULL DEFAULT 'INICIADA',

    -- Auditoria
    registrado_por UUID NOT NULL REFERENCES auth.users(id) ON DELETE SET NULL,
    fecha_creacion TIMESTAMPTZ DEFAULT NOW(),
    fecha_actualizacion TIMESTAMPTZ DEFAULT NOW(),

    -- =================================================================
    -- CONSTRAINTS
    -- =================================================================

    -- fecha_efectiva >= fecha_registro
    CONSTRAINT chk_baja_fechas CHECK (
        fecha_efectiva >= fecha_registro
    ),

    -- Si esta comunicada o mas avanzada, debe tener fecha_comunicacion_buap
    CONSTRAINT chk_baja_comunicada CHECK (
        estatus NOT IN ('COMUNICADA', 'LIQUIDADA', 'CERRADA')
        OR fecha_comunicacion_buap IS NOT NULL
        OR estatus IN ('LIQUIDADA', 'CERRADA')
    )
);

-- 4. Indices
CREATE INDEX IF NOT EXISTS idx_bajas_empleado
    ON public.bajas_empleado(empleado_id);

CREATE INDEX IF NOT EXISTS idx_bajas_empresa
    ON public.bajas_empleado(empresa_id);

CREATE INDEX IF NOT EXISTS idx_bajas_estatus
    ON public.bajas_empleado(estatus);

-- Indice para alertas: bajas activas con plazo de liquidacion
CREATE INDEX IF NOT EXISTS idx_bajas_alertas
    ON public.bajas_empleado(estatus, fecha_limite_liquidacion)
    WHERE estatus IN ('INICIADA', 'COMUNICADA');

-- Solo una baja activa por empleado
CREATE UNIQUE INDEX IF NOT EXISTS idx_bajas_activa_empleado
    ON public.bajas_empleado(empleado_id)
    WHERE estatus NOT IN ('CERRADA', 'CANCELADA');

-- 5. Trigger para fecha_actualizacion
CREATE TRIGGER tr_bajas_empleado_updated
    BEFORE UPDATE ON public.bajas_empleado
    FOR EACH ROW
    EXECUTE FUNCTION update_fecha_actualizacion();

-- 6. Comentarios
COMMENT ON TABLE public.bajas_empleado
    IS 'Proceso de baja de empleados con seguimiento de liquidacion y plazos contractuales BUAP';
COMMENT ON COLUMN public.bajas_empleado.fecha_comunicacion_buap
    IS 'Fecha en que se comunico la baja a BUAP (tracking opcional, sin deadline estricto)';
COMMENT ON COLUMN public.bajas_empleado.fecha_limite_liquidacion
    IS 'fecha_efectiva + 15 dias habiles - unico plazo con alerta real';
COMMENT ON COLUMN public.bajas_empleado.requiere_sustitucion
    IS 'Dato informativo: NULL=no definido, TRUE=BUAP solicito reemplazo, FALSE=no requiere. La empresa NO busca sustituto, BUAP lo hace.';

-- 7. RLS (Row Level Security)
ALTER TABLE public.bajas_empleado ENABLE ROW LEVEL SECURITY;

-- Service role bypass
CREATE POLICY bajas_service_all ON public.bajas_empleado
    FOR ALL TO service_role USING (true) WITH CHECK (true);

-- Admin ve todas
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies
        WHERE policyname = 'bajas_admin_select' AND tablename = 'bajas_empleado'
    ) THEN
        CREATE POLICY bajas_admin_select ON public.bajas_empleado
            FOR SELECT TO authenticated
            USING (EXISTS (
                SELECT 1 FROM public.user_profiles
                WHERE user_profiles.user_id = auth.uid()
                AND user_profiles.rol IN ('admin', 'superadmin')
            ));
    END IF;
END $$;

-- Cliente ve las de su empresa
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies
        WHERE policyname = 'bajas_client_select' AND tablename = 'bajas_empleado'
    ) THEN
        CREATE POLICY bajas_client_select ON public.bajas_empleado
            FOR SELECT TO authenticated
            USING (empresa_id IN (
                SELECT empresa_id FROM public.user_companies
                WHERE user_id = auth.uid()
            ));
    END IF;
END $$;

-- Admin puede insertar/actualizar
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies
        WHERE policyname = 'bajas_admin_insert' AND tablename = 'bajas_empleado'
    ) THEN
        CREATE POLICY bajas_admin_insert ON public.bajas_empleado
            FOR INSERT TO authenticated
            WITH CHECK (EXISTS (
                SELECT 1 FROM public.user_profiles
                WHERE user_profiles.user_id = auth.uid()
                AND user_profiles.rol IN ('admin', 'superadmin')
            ));
    END IF;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies
        WHERE policyname = 'bajas_admin_update' AND tablename = 'bajas_empleado'
    ) THEN
        CREATE POLICY bajas_admin_update ON public.bajas_empleado
            FOR UPDATE TO authenticated
            USING (EXISTS (
                SELECT 1 FROM public.user_profiles
                WHERE user_profiles.user_id = auth.uid()
                AND user_profiles.rol IN ('admin', 'superadmin')
            ));
    END IF;
END $$;

-- Cliente puede insertar/actualizar las de su empresa
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies
        WHERE policyname = 'bajas_client_insert' AND tablename = 'bajas_empleado'
    ) THEN
        CREATE POLICY bajas_client_insert ON public.bajas_empleado
            FOR INSERT TO authenticated
            WITH CHECK (empresa_id IN (
                SELECT empresa_id FROM public.user_companies
                WHERE user_id = auth.uid()
            ));
    END IF;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies
        WHERE policyname = 'bajas_client_update' AND tablename = 'bajas_empleado'
    ) THEN
        CREATE POLICY bajas_client_update ON public.bajas_empleado
            FOR UPDATE TO authenticated
            USING (empresa_id IN (
                SELECT empresa_id FROM public.user_companies
                WHERE user_id = auth.uid()
            ));
    END IF;
END $$;

-- =============================================================================
-- Rollback
-- =============================================================================
-- DROP TRIGGER IF EXISTS tr_bajas_empleado_updated ON public.bajas_empleado;
-- DROP POLICY IF EXISTS bajas_client_update ON public.bajas_empleado;
-- DROP POLICY IF EXISTS bajas_client_insert ON public.bajas_empleado;
-- DROP POLICY IF EXISTS bajas_admin_update ON public.bajas_empleado;
-- DROP POLICY IF EXISTS bajas_admin_insert ON public.bajas_empleado;
-- DROP POLICY IF EXISTS bajas_client_select ON public.bajas_empleado;
-- DROP POLICY IF EXISTS bajas_admin_select ON public.bajas_empleado;
-- DROP POLICY IF EXISTS bajas_service_all ON public.bajas_empleado;
-- DROP TABLE IF EXISTS public.bajas_empleado;
-- DROP TYPE IF EXISTS estatus_liquidacion;
-- DROP TYPE IF EXISTS estatus_baja;
