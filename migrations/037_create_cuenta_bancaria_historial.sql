-- =============================================================================
-- Migration 037: Crear tabla cuenta_bancaria_historial
-- =============================================================================
-- Descripcion: Tabla inmutable de auditoria para cambios de datos bancarios.
--              Patron similar a empleado_restricciones_log: solo INSERT.
-- Dependencias: 007_create_empleados_table, 015_create_user_auth_tables,
--               036_create_empleado_documentos
-- =============================================================================

-- 1. Crear tabla
CREATE TABLE IF NOT EXISTS public.cuenta_bancaria_historial (
    id SERIAL PRIMARY KEY,
    empleado_id INTEGER NOT NULL REFERENCES public.empleados(id) ON DELETE CASCADE,

    -- Datos bancarios capturados al momento del cambio
    cuenta_bancaria VARCHAR(18),
    banco VARCHAR(100),
    clabe_interbancaria VARCHAR(18),

    -- Auditoria
    cambiado_por UUID NOT NULL REFERENCES auth.users(id) ON DELETE SET NULL,
    ip_origen VARCHAR(45),
    fecha_cambio TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Documento soporte (caratula bancaria)
    documento_id INTEGER REFERENCES public.empleado_documentos(id) ON DELETE SET NULL,

    -- Timestamp
    fecha_creacion TIMESTAMPTZ DEFAULT NOW()
);

-- 2. Indices
CREATE INDEX IF NOT EXISTS idx_cuenta_bancaria_hist_empleado
    ON public.cuenta_bancaria_historial(empleado_id);

CREATE INDEX IF NOT EXISTS idx_cuenta_bancaria_hist_fecha
    ON public.cuenta_bancaria_historial(fecha_cambio DESC);

-- 3. Comments
COMMENT ON TABLE public.cuenta_bancaria_historial IS 'Historial inmutable de cambios de datos bancarios de empleados';
COMMENT ON COLUMN public.cuenta_bancaria_historial.ip_origen IS 'Direccion IP desde donde se realizo el cambio';
COMMENT ON COLUMN public.cuenta_bancaria_historial.documento_id IS 'Referencia a la caratula bancaria que respalda el cambio';

-- =============================================================================
-- RLS (Row Level Security)
-- =============================================================================

ALTER TABLE public.cuenta_bancaria_historial ENABLE ROW LEVEL SECURITY;

-- SELECT: solo admin
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies
        WHERE policyname = 'cuenta_bancaria_hist_select_policy'
        AND tablename = 'cuenta_bancaria_historial'
    ) THEN
        CREATE POLICY cuenta_bancaria_hist_select_policy ON public.cuenta_bancaria_historial
            FOR SELECT USING (is_admin());
    END IF;
END $$;

-- INSERT: admin o usuario de empresa vinculada
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies
        WHERE policyname = 'cuenta_bancaria_hist_insert_policy'
        AND tablename = 'cuenta_bancaria_historial'
    ) THEN
        CREATE POLICY cuenta_bancaria_hist_insert_policy ON public.cuenta_bancaria_historial
            FOR INSERT WITH CHECK (
                is_admin()
                OR EXISTS (
                    SELECT 1 FROM public.empleados e
                    WHERE e.id = cuenta_bancaria_historial.empleado_id
                    AND e.empresa_id = ANY(get_user_companies())
                )
            );
    END IF;
END $$;

-- UPDATE: nunca (tabla inmutable)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies
        WHERE policyname = 'cuenta_bancaria_hist_update_policy'
        AND tablename = 'cuenta_bancaria_historial'
    ) THEN
        CREATE POLICY cuenta_bancaria_hist_update_policy ON public.cuenta_bancaria_historial
            FOR UPDATE USING (FALSE);
    END IF;
END $$;

-- DELETE: nunca (tabla inmutable)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies
        WHERE policyname = 'cuenta_bancaria_hist_delete_policy'
        AND tablename = 'cuenta_bancaria_historial'
    ) THEN
        CREATE POLICY cuenta_bancaria_hist_delete_policy ON public.cuenta_bancaria_historial
            FOR DELETE USING (FALSE);
    END IF;
END $$;

-- =============================================================================
-- Rollback (comentado)
-- =============================================================================
-- DROP POLICY IF EXISTS cuenta_bancaria_hist_delete_policy ON public.cuenta_bancaria_historial;
-- DROP POLICY IF EXISTS cuenta_bancaria_hist_update_policy ON public.cuenta_bancaria_historial;
-- DROP POLICY IF EXISTS cuenta_bancaria_hist_insert_policy ON public.cuenta_bancaria_historial;
-- DROP POLICY IF EXISTS cuenta_bancaria_hist_select_policy ON public.cuenta_bancaria_historial;
-- DROP TABLE IF EXISTS public.cuenta_bancaria_historial;
