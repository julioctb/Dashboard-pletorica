-- =============================================================================
-- Migration 066: Codigo postal de empleados y fecha vigente por plaza
-- =============================================================================

ALTER TABLE public.empleados
    ADD COLUMN IF NOT EXISTS codigo_postal VARCHAR(5);

ALTER TABLE public.empleados
    DROP CONSTRAINT IF EXISTS chk_empleados_codigo_postal_formato;

ALTER TABLE public.empleados
    ADD CONSTRAINT chk_empleados_codigo_postal_formato
    CHECK (codigo_postal IS NULL OR codigo_postal ~ '^[0-9]{5}$');

ALTER TABLE public.empleados
    ALTER COLUMN fecha_ingreso_vigente DROP DEFAULT,
    ALTER COLUMN fecha_ingreso_vigente DROP NOT NULL;

ALTER TABLE public.empleados
    DROP CONSTRAINT IF EXISTS chk_empleados_fechas;

ALTER TABLE public.empleados
    ADD CONSTRAINT chk_empleados_fechas
    CHECK (
        (
            fecha_ingreso_vigente IS NULL
            OR fecha_ingreso_vigente >= fecha_ingreso
        )
        AND (
            fecha_baja IS NULL
            OR fecha_baja >= COALESCE(fecha_ingreso_vigente, fecha_ingreso)
        )
    );

COMMENT ON COLUMN public.empleados.codigo_postal IS
'Codigo postal del domicilio del empleado (5 digitos).';

COMMENT ON COLUMN public.empleados.fecha_ingreso IS
'Primer ingreso historico/institucional del empleado. No cambia en reingresos.';

COMMENT ON COLUMN public.empleados.fecha_ingreso_vigente IS
'Inicio de la asignacion laboral/plaza vigente. Se captura al asignar plaza.';
