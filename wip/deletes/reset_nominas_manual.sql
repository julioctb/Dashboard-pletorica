-- Script manual para reiniciar nóminas operativas.
--
-- Fuente de verdad del esquema:
-- - public.periodos_nomina
-- - public.nominas_empleado
-- - public.nomina_movimientos
-- - tablas relacionadas por cascada desde periodos_nomina
--
-- Nota:
-- `public.nomina_movimientos.nomina_empleado_id` tiene `ON DELETE CASCADE`,
-- así que al borrar de `public.nominas_empleado` también se borran sus movimientos.
-- `public.nominas_empleado.periodo_id` tiene `ON DELETE CASCADE`,
-- así que al borrar de `public.periodos_nomina` también se borran los recibos,
-- movimientos y layouts de dispersión ligados a esos períodos.

-- ============================================================================
-- A. RECOMENDADO: reiniciar un período específico
-- Cambia 123 por el ID real de `public.periodos_nomina`.
-- ============================================================================

BEGIN;

DO $$
DECLARE
    v_periodo_id integer := 123;
    v_estatus text;
BEGIN
    SELECT estatus::text
    INTO v_estatus
    FROM public.periodos_nomina
    WHERE id = v_periodo_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'No existe el período de nómina con id=%', v_periodo_id;
    END IF;

    IF v_estatus NOT IN ('BORRADOR', 'EN_PREPARACION_RRHH') THEN
        RAISE EXCEPTION
            'El período % está en estatus % y no debería reiniciarse manualmente. Devuélvelo a RRHH primero.',
            v_periodo_id,
            v_estatus;
    END IF;

    DELETE FROM public.nominas_empleado
    WHERE periodo_id = v_periodo_id;

    UPDATE public.periodos_nomina
    SET total_percepciones = 0,
        total_deducciones = 0,
        total_otros_pagos = 0,
        total_neto = 0,
        total_empleados = 0,
        fecha_actualizacion = NOW()
    WHERE id = v_periodo_id;
END $$;

SELECT
    id,
    nombre,
    estatus,
    total_empleados,
    total_neto
FROM public.periodos_nomina
WHERE id = 123;

COMMIT;

-- ============================================================================
-- B. OPCIONAL: limpiar TODOS los recibos de nómina de TODOS los períodos
-- Descomenta solo si de verdad quieres vaciar toda la operación de nómina.
-- ============================================================================

-- BEGIN;
--
-- DELETE FROM public.nominas_empleado;
--
-- UPDATE public.periodos_nomina
-- SET total_percepciones = 0,
--     total_deducciones = 0,
--     total_otros_pagos = 0,
--     total_neto = 0,
--     total_empleados = 0,
--     fecha_actualizacion = NOW();
--
-- COMMIT;

-- ============================================================================
-- C. START FROM ZERO: borrar TODOS los períodos de nómina y todo lo relacionado
-- Esto deja el módulo de nómina operativo completamente vacío.
-- ============================================================================

-- BEGIN;
--
-- TRUNCATE TABLE public.periodos_nomina RESTART IDENTITY CASCADE;
--
-- COMMIT;
