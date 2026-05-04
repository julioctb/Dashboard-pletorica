BEGIN;

-- =============================================================================
-- Módulo de incapacidades
-- =============================================================================

CREATE TABLE IF NOT EXISTS public.incapacidades (
    id SERIAL PRIMARY KEY,
    empleado_id INTEGER NOT NULL
        REFERENCES public.empleados(id) ON DELETE RESTRICT,
    plaza_id INTEGER
        REFERENCES public.plazas(id) ON DELETE SET NULL,
    empresa_id INTEGER NOT NULL
        REFERENCES public.empresas(id) ON DELETE RESTRICT,
    origen VARCHAR(20) NOT NULL DEFAULT 'FORMAL'
        CHECK (origen IN ('FORMAL', 'POR_ACUERDO')),
    tipo VARCHAR(30) NOT NULL
        CHECK (tipo IN ('ENF_GENERAL', 'RIESGO_TRABAJO', 'MATERNIDAD', 'ACUERDO')),
    fecha_inicio DATE NOT NULL,
    fecha_fin_estimada DATE,
    fecha_fin_real DATE,
    estatus VARCHAR(20) NOT NULL DEFAULT 'ACTIVA'
        CHECK (estatus IN ('ACTIVA', 'VENCIDA', 'CERRADA')),
    porcentaje_pago NUMERIC(5, 2) NOT NULL DEFAULT 100.00
        CHECK (porcentaje_pago >= 0 AND porcentaje_pago <= 100),
    requiere_cobertura BOOLEAN NOT NULL DEFAULT FALSE,
    notas TEXT,
    registrado_por UUID
        REFERENCES auth.users(id) ON DELETE SET NULL,
    fecha_creacion TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    fecha_actualizacion TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_incapacidades_fechas
        CHECK (
            fecha_fin_estimada IS NULL
            OR fecha_fin_estimada >= fecha_inicio
        ),
    CONSTRAINT chk_incapacidades_fecha_fin_real
        CHECK (
            fecha_fin_real IS NULL
            OR fecha_fin_real >= fecha_inicio
        )
);

CREATE TABLE IF NOT EXISTS public.certificados_incapacidad (
    id SERIAL PRIMARY KEY,
    incapacidad_id INTEGER NOT NULL
        REFERENCES public.incapacidades(id) ON DELETE CASCADE,
    folio_imss VARCHAR(50),
    fecha_inicio DATE NOT NULL,
    fecha_fin DATE NOT NULL,
    dias_certificado INTEGER NOT NULL
        CHECK (dias_certificado > 0),
    tipo_certificado VARCHAR(20) NOT NULL DEFAULT 'INICIAL'
        CHECK (tipo_certificado IN ('INICIAL', 'SUBSECUENTE')),
    archivo_id INTEGER
        REFERENCES public.archivo_sistema(id) ON DELETE SET NULL,
    fecha_creacion TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    fecha_actualizacion TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_certificados_incapacidad_fechas
        CHECK (fecha_fin >= fecha_inicio)
);

CREATE INDEX IF NOT EXISTS idx_incapacidades_empleado
    ON public.incapacidades(empleado_id);

CREATE INDEX IF NOT EXISTS idx_incapacidades_empresa
    ON public.incapacidades(empresa_id);

CREATE INDEX IF NOT EXISTS idx_incapacidades_activas_empleado
    ON public.incapacidades(empleado_id)
    WHERE estatus = 'ACTIVA';

CREATE INDEX IF NOT EXISTS idx_incapacidades_activas_plaza
    ON public.incapacidades(plaza_id)
    WHERE plaza_id IS NOT NULL AND estatus = 'ACTIVA';

CREATE INDEX IF NOT EXISTS idx_certificados_incapacidad_incapacidad
    ON public.certificados_incapacidad(incapacidad_id);

CREATE INDEX IF NOT EXISTS idx_certificados_incapacidad_folio
    ON public.certificados_incapacidad(folio_imss)
    WHERE folio_imss IS NOT NULL;

DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM pg_proc
        WHERE proname = 'update_fecha_actualizacion'
    ) THEN
        IF NOT EXISTS (
            SELECT 1
            FROM pg_trigger t
            JOIN pg_proc p ON p.oid = t.tgfoid
            WHERE t.tgrelid = 'public.incapacidades'::regclass
              AND NOT t.tgisinternal
              AND p.proname = 'update_fecha_actualizacion'
        ) THEN
            CREATE TRIGGER set_fecha_actualizacion_incapacidades
                BEFORE UPDATE ON public.incapacidades
                FOR EACH ROW
                EXECUTE FUNCTION update_fecha_actualizacion();
        END IF;

        IF NOT EXISTS (
            SELECT 1
            FROM pg_trigger t
            JOIN pg_proc p ON p.oid = t.tgfoid
            WHERE t.tgrelid = 'public.certificados_incapacidad'::regclass
              AND NOT t.tgisinternal
              AND p.proname = 'update_fecha_actualizacion'
        ) THEN
            CREATE TRIGGER set_fecha_actualizacion_certificados_incapacidad
                BEFORE UPDATE ON public.certificados_incapacidad
                FOR EACH ROW
                EXECUTE FUNCTION update_fecha_actualizacion();
        END IF;
    END IF;
END $$;

ALTER TABLE public.incapacidades ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.certificados_incapacidad ENABLE ROW LEVEL SECURITY;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_policies
        WHERE schemaname = 'public'
          AND tablename = 'incapacidades'
          AND policyname = 'incapacidades_select_policy'
    ) THEN
        CREATE POLICY "incapacidades_select_policy" ON public.incapacidades
            FOR SELECT USING (true);
    END IF;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_policies
        WHERE schemaname = 'public'
          AND tablename = 'incapacidades'
          AND policyname = 'incapacidades_write_policy'
    ) THEN
        CREATE POLICY "incapacidades_write_policy" ON public.incapacidades
            FOR ALL USING (true) WITH CHECK (true);
    END IF;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_policies
        WHERE schemaname = 'public'
          AND tablename = 'certificados_incapacidad'
          AND policyname = 'certificados_incapacidad_select_policy'
    ) THEN
        CREATE POLICY "certificados_incapacidad_select_policy" ON public.certificados_incapacidad
            FOR SELECT USING (true);
    END IF;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_policies
        WHERE schemaname = 'public'
          AND tablename = 'certificados_incapacidad'
          AND policyname = 'certificados_incapacidad_write_policy'
    ) THEN
        CREATE POLICY "certificados_incapacidad_write_policy" ON public.certificados_incapacidad
            FOR ALL USING (true) WITH CHECK (true);
    END IF;
END $$;

COMMIT;
