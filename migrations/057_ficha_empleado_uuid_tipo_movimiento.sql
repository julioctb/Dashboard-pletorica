-- ============================================================================
-- Migration 057: UUID en empleados + tipo_movimiento en historial_laboral
-- Fecha: 2026-03-18
-- ============================================================================

BEGIN;

-- 0) Requerido para gen_random_uuid()
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- 1) UUID en empleados para URLs seguras del portal
ALTER TABLE public.empleados
    ADD COLUMN IF NOT EXISTS uuid UUID;

UPDATE public.empleados
SET uuid = gen_random_uuid()
WHERE uuid IS NULL;

ALTER TABLE public.empleados
    ALTER COLUMN uuid SET DEFAULT gen_random_uuid(),
    ALTER COLUMN uuid SET NOT NULL;

CREATE UNIQUE INDEX IF NOT EXISTS idx_empleados_uuid
    ON public.empleados (uuid);

-- 2) Tipo de movimiento en historial_laboral
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_type
        WHERE typname = 'tipo_movimiento_historial'
    ) THEN
        CREATE TYPE public.tipo_movimiento_historial AS ENUM (
            'ALTA',
            'ASIGNACION',
            'CAMBIO_PLAZA',
            'CAMBIO_SEDE',
            'CAMBIO_CATEGORIA',
            'REINGRESO',
            'BAJA_TEMPORAL',
            'BAJA_DEFINITIVA',
            'SUSPENSION',
            'REACTIVACION',
            'BAJA'
        );
    END IF;
END $$;

DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM pg_type
        WHERE typname = 'tipo_movimiento_historial'
    ) THEN
        ALTER TYPE public.tipo_movimiento_historial ADD VALUE IF NOT EXISTS 'ALTA';
        ALTER TYPE public.tipo_movimiento_historial ADD VALUE IF NOT EXISTS 'ASIGNACION';
        ALTER TYPE public.tipo_movimiento_historial ADD VALUE IF NOT EXISTS 'CAMBIO_PLAZA';
        ALTER TYPE public.tipo_movimiento_historial ADD VALUE IF NOT EXISTS 'CAMBIO_SEDE';
        ALTER TYPE public.tipo_movimiento_historial ADD VALUE IF NOT EXISTS 'CAMBIO_CATEGORIA';
        ALTER TYPE public.tipo_movimiento_historial ADD VALUE IF NOT EXISTS 'REINGRESO';
        ALTER TYPE public.tipo_movimiento_historial ADD VALUE IF NOT EXISTS 'BAJA_TEMPORAL';
        ALTER TYPE public.tipo_movimiento_historial ADD VALUE IF NOT EXISTS 'BAJA_DEFINITIVA';
        ALTER TYPE public.tipo_movimiento_historial ADD VALUE IF NOT EXISTS 'SUSPENSION';
        ALTER TYPE public.tipo_movimiento_historial ADD VALUE IF NOT EXISTS 'REACTIVACION';
        ALTER TYPE public.tipo_movimiento_historial ADD VALUE IF NOT EXISTS 'BAJA';
    END IF;
END $$;

ALTER TABLE public.historial_laboral
    ADD COLUMN IF NOT EXISTS tipo_movimiento tipo_movimiento_historial;

UPDATE public.historial_laboral
SET tipo_movimiento = CASE
    WHEN fecha_fin IS NOT NULL AND motivo_fin IS NOT NULL THEN 'BAJA_DEFINITIVA'
    WHEN empresa_anterior_id IS NOT NULL THEN 'CAMBIO_PLAZA'
    ELSE 'ASIGNACION'
END
WHERE tipo_movimiento IS NULL;

ALTER TABLE public.historial_laboral
    ALTER COLUMN tipo_movimiento SET DEFAULT 'ASIGNACION';

CREATE INDEX IF NOT EXISTS idx_historial_laboral_empleado_fecha
    ON public.historial_laboral (empleado_id, fecha_inicio DESC);

CREATE INDEX IF NOT EXISTS idx_historial_laboral_empleado_activo
    ON public.historial_laboral (empleado_id)
    WHERE fecha_fin IS NULL AND estatus = 'ACTIVA';

-- 3) Trigger: estatus empleado basado en historial activo
CREATE OR REPLACE FUNCTION public.actualizar_estatus_empleado_desde_historial()
RETURNS TRIGGER AS $$
DECLARE
    v_empleado_id INTEGER;
    v_tiene_plaza_activa BOOLEAN;
    v_tiene_col_estatus BOOLEAN;
BEGIN
    v_empleado_id := COALESCE(NEW.empleado_id, OLD.empleado_id);

    IF v_empleado_id IS NULL THEN
        RETURN COALESCE(NEW, OLD);
    END IF;

    SELECT EXISTS (
        SELECT 1
        FROM information_schema.columns c
        WHERE c.table_schema = 'public'
          AND c.table_name = 'historial_laboral'
          AND c.column_name = 'estatus'
    )
    INTO v_tiene_col_estatus;

    IF v_tiene_col_estatus THEN
        SELECT EXISTS (
            SELECT 1
            FROM public.historial_laboral hl
            WHERE hl.empleado_id = v_empleado_id
              AND hl.fecha_fin IS NULL
              AND hl.estatus = 'ACTIVA'
        )
        INTO v_tiene_plaza_activa;
    ELSE
        -- Compatibilidad con esquemas donde historial_laboral no tiene columna estatus.
        SELECT EXISTS (
            SELECT 1
            FROM public.historial_laboral hl
            WHERE hl.empleado_id = v_empleado_id
              AND hl.fecha_fin IS NULL
        )
        INTO v_tiene_plaza_activa;
    END IF;

    -- Actualizar solo empleados que no esten en estados gestionados por otros módulos.
    -- Nota:
    -- - BAJA puede no existir en algunos entornos (estatus::text evita fallo por enum).
    -- - SUSPENDIDO se gestiona desde el flujo de suspensiones.
    UPDATE public.empleados
    SET estatus = CASE
        WHEN v_tiene_plaza_activa THEN 'ACTIVO'
        ELSE 'INACTIVO'
    END,
    fecha_actualizacion = NOW()
    WHERE id = v_empleado_id
      AND COALESCE(estatus::text, '') NOT IN ('BAJA', 'SUSPENDIDO');

    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_actualizar_estatus_empleado ON public.historial_laboral;

CREATE TRIGGER trg_actualizar_estatus_empleado
AFTER INSERT OR UPDATE OR DELETE ON public.historial_laboral
FOR EACH ROW
EXECUTE FUNCTION public.actualizar_estatus_empleado_desde_historial();

-- 4) Trigger fecha_actualizacion en historial_laboral (si existe helper global)
DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM pg_proc
        WHERE proname = 'update_fecha_actualizacion'
    ) THEN
        -- Evitar duplicar trigger si ya existe cualquier trigger (con otro nombre)
        -- que ejecute update_fecha_actualizacion() sobre historial_laboral.
        IF NOT EXISTS (
            SELECT 1
            FROM pg_trigger t
            JOIN pg_proc p ON p.oid = t.tgfoid
            WHERE t.tgrelid = 'public.historial_laboral'::regclass
              AND NOT t.tgisinternal
              AND p.proname = 'update_fecha_actualizacion'
        ) THEN
            CREATE TRIGGER set_fecha_actualizacion_historial
            BEFORE UPDATE ON public.historial_laboral
            FOR EACH ROW
            EXECUTE FUNCTION update_fecha_actualizacion();
        END IF;
    END IF;
END $$;

COMMIT;
