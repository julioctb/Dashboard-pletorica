-- =============================================================================
-- Migration 067: Reparar notas de historial_laboral con repr de bound method
-- =============================================================================
-- Bug: en `app/domain/services/empleados/mutations.py` se interpolaba
-- `empleado.nombre_completo` (sin parentesis) al registrar el alta laboral.
-- Como `nombre_completo` es metodo, la nota quedaba con texto del estilo:
--   "Alta de empleado: <bound method Empleado.nombre_completo of Empleado(id=234, ...)>"
-- Esta migracion reescribe esas notas usando los datos reales del empleado.
--
-- Aplicacion manual en Supabase. Idempotente: el WHERE solo afecta filas con
-- el patron del bug, asi que correrla mas de una vez no causa cambios extra.
-- =============================================================================

BEGIN;

-- 1. Conteo previo para auditoria (revisar logs antes/despues).
DO $$
DECLARE
    afectadas INTEGER;
BEGIN
    SELECT COUNT(*) INTO afectadas
    FROM public.historial_laboral
    WHERE notas LIKE 'Alta de empleado: <bound method Empleado.nombre_completo of Empleado(%';

    RAISE NOTICE 'Migration 067: filas con bound method en notas: %', afectadas;
END $$;

-- 2. Reescribir notas afectadas con el nombre real del empleado.
UPDATE public.historial_laboral hl
SET
    notas = 'Alta de empleado: ' || BTRIM(
        CONCAT_WS(' ', e.nombre, e.apellido_paterno, NULLIF(e.apellido_materno, ''))
    ),
    fecha_actualizacion = NOW()
FROM public.empleados e
WHERE hl.empleado_id = e.id
  AND hl.notas LIKE 'Alta de empleado: <bound method Empleado.nombre_completo of Empleado(%';

-- 3. Verificacion posterior: deberia regresar 0.
DO $$
DECLARE
    restantes INTEGER;
BEGIN
    SELECT COUNT(*) INTO restantes
    FROM public.historial_laboral
    WHERE notas LIKE 'Alta de empleado: <bound method Empleado.nombre_completo of Empleado(%';

    IF restantes <> 0 THEN
        RAISE EXCEPTION 'Migration 067: aun quedan % filas con bound method en notas', restantes;
    END IF;

    RAISE NOTICE 'Migration 067: limpieza completa, 0 filas restantes';
END $$;

COMMIT;
