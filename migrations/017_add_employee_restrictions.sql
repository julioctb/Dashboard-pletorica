-- ============================================================================
-- Migration: Add Employee Restrictions System
-- Fecha: 2026-02-01
-- Descripcion: Agrega campos de restriccion a empleados y crea tabla de log
--              para auditar restricciones/liberaciones de empleados.
--
-- Contexto: BUAP puede bloquear empleados problematicos (robo, fraude,
--           abandono) para que NINGUNA empresa proveedora pueda darlos de alta.
-- ============================================================================

-- ============================================================================
-- 1. AGREGAR CAMPOS DE RESTRICCION A TABLA EMPLEADOS
-- ============================================================================

ALTER TABLE public.empleados
ADD COLUMN IF NOT EXISTS is_restricted BOOLEAN NOT NULL DEFAULT false,
ADD COLUMN IF NOT EXISTS restriction_reason VARCHAR(500),
ADD COLUMN IF NOT EXISTS restricted_at TIMESTAMP WITH TIME ZONE,
ADD COLUMN IF NOT EXISTS restricted_by UUID REFERENCES public.user_profiles(id);

-- Indice parcial para consultas de empleados restringidos
CREATE INDEX IF NOT EXISTS idx_empleados_restricted
ON public.empleados(is_restricted)
WHERE is_restricted = true;

-- Constraint: integridad de datos de restriccion
-- Si restringido: DEBE tener razon, fecha y admin
-- Si no restringido: NO debe tener razon, fecha ni admin
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'chk_empleados_restriccion'
    ) THEN
        ALTER TABLE public.empleados
        ADD CONSTRAINT chk_empleados_restriccion CHECK (
            (is_restricted = false AND restriction_reason IS NULL AND restricted_at IS NULL AND restricted_by IS NULL)
            OR
            (is_restricted = true AND restriction_reason IS NOT NULL AND restricted_at IS NOT NULL AND restricted_by IS NOT NULL)
        );
    END IF;
END $$;

-- Comentarios
COMMENT ON COLUMN public.empleados.is_restricted IS
'true = empleado bloqueado por BUAP, no puede ser dado de alta por ninguna empresa';
COMMENT ON COLUMN public.empleados.restriction_reason IS
'Motivo de la restriccion. Solo visible para administradores BUAP';
COMMENT ON COLUMN public.empleados.restricted_at IS
'Fecha y hora en que se aplico la restriccion';
COMMENT ON COLUMN public.empleados.restricted_by IS
'UUID del usuario admin que aplico la restriccion';

-- ============================================================================
-- 2. CREAR TABLA DE HISTORIAL DE RESTRICCIONES
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.empleado_restricciones_log (
    id SERIAL PRIMARY KEY,
    empleado_id INTEGER NOT NULL REFERENCES public.empleados(id) ON DELETE RESTRICT,

    -- Tipo de accion
    accion VARCHAR(20) NOT NULL CHECK (accion IN ('RESTRICCION', 'LIBERACION')),

    -- Motivo (obligatorio siempre)
    motivo VARCHAR(500) NOT NULL,

    -- Cuando y quien
    fecha TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    ejecutado_por UUID NOT NULL REFERENCES public.user_profiles(id),

    -- Observaciones adicionales
    notas TEXT,

    -- Auditoria
    fecha_creacion TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indices
CREATE INDEX IF NOT EXISTS idx_restricciones_log_empleado
ON public.empleado_restricciones_log(empleado_id);

CREATE INDEX IF NOT EXISTS idx_restricciones_log_fecha
ON public.empleado_restricciones_log(fecha DESC);

-- Comentarios
COMMENT ON TABLE public.empleado_restricciones_log IS
'Historial de restricciones y liberaciones de empleados. Tabla INMUTABLE para auditoria.';
COMMENT ON COLUMN public.empleado_restricciones_log.accion IS
'RESTRICCION = empleado bloqueado, LIBERACION = empleado desbloqueado';
COMMENT ON COLUMN public.empleado_restricciones_log.motivo IS
'Razon de la accion. Para restriccion: causa del bloqueo. Para liberacion: justificacion.';

-- ============================================================================
-- 3. POLITICAS RLS PARA TABLA DE LOG
-- ============================================================================

ALTER TABLE public.empleado_restricciones_log ENABLE ROW LEVEL SECURITY;

-- SELECT: Solo admins pueden ver el historial
DROP POLICY IF EXISTS "restricciones_log_select" ON public.empleado_restricciones_log;
CREATE POLICY "restricciones_log_select"
ON public.empleado_restricciones_log FOR SELECT
USING (is_admin());

-- INSERT: Solo admins pueden insertar
DROP POLICY IF EXISTS "restricciones_log_insert" ON public.empleado_restricciones_log;
CREATE POLICY "restricciones_log_insert"
ON public.empleado_restricciones_log FOR INSERT
WITH CHECK (is_admin());

-- UPDATE: Nadie puede modificar el historial (inmutable)
DROP POLICY IF EXISTS "restricciones_log_no_update" ON public.empleado_restricciones_log;
CREATE POLICY "restricciones_log_no_update"
ON public.empleado_restricciones_log FOR UPDATE
USING (false);

-- DELETE: Nadie puede eliminar del historial (inmutable)
DROP POLICY IF EXISTS "restricciones_log_no_delete" ON public.empleado_restricciones_log;
CREATE POLICY "restricciones_log_no_delete"
ON public.empleado_restricciones_log FOR DELETE
USING (false);

-- ============================================================================
-- 4. VERIFICACION
-- ============================================================================

-- Verificar columnas agregadas a empleados
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public'
        AND table_name = 'empleados'
        AND column_name = 'is_restricted'
    ) THEN
        RAISE EXCEPTION 'Columna is_restricted no fue creada';
    END IF;
END $$;

-- Verificar tabla de log creada
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.tables
        WHERE table_schema = 'public'
        AND table_name = 'empleado_restricciones_log'
    ) THEN
        RAISE EXCEPTION 'Tabla empleado_restricciones_log no fue creada';
    END IF;
END $$;

-- ============================================================================
-- Rollback (si necesitas revertir)
-- ============================================================================
-- DROP POLICY IF EXISTS "restricciones_log_no_delete" ON public.empleado_restricciones_log;
-- DROP POLICY IF EXISTS "restricciones_log_no_update" ON public.empleado_restricciones_log;
-- DROP POLICY IF EXISTS "restricciones_log_insert" ON public.empleado_restricciones_log;
-- DROP POLICY IF EXISTS "restricciones_log_select" ON public.empleado_restricciones_log;
-- DROP TABLE IF EXISTS public.empleado_restricciones_log;
-- ALTER TABLE public.empleados DROP CONSTRAINT IF EXISTS chk_empleados_restriccion;
-- ALTER TABLE public.empleados DROP COLUMN IF EXISTS restricted_by;
-- ALTER TABLE public.empleados DROP COLUMN IF EXISTS restricted_at;
-- ALTER TABLE public.empleados DROP COLUMN IF EXISTS restriction_reason;
-- ALTER TABLE public.empleados DROP COLUMN IF EXISTS is_restricted;
