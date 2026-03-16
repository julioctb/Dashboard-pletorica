-- Borrado manual de empleados y contratos de Pletórica.
--
-- Objetivo:
-- - borrar empleados de la empresa Pletórica
-- - borrar contratos de la empresa Pletórica
-- - borrar datos del cotizador de la empresa Pletórica
-- - limpiar primero tablas hijas con FK RESTRICT para evitar errores
--
-- Importante:
-- - este script NO borra la fila de `public.empresas`
-- - sí borra períodos de nómina de la empresa para liberar `nominas_empleado`
-- - si tienes varias empresas que coincidan con "Pletorica/Pletórica", el script aborta

BEGIN;

DO $$
DECLARE
    v_empresa_id INTEGER;
    v_matches INTEGER;
BEGIN
    SELECT COUNT(*), MIN(id)
    INTO v_matches, v_empresa_id
    FROM public.empresas
    WHERE nombre_comercial ILIKE '%pletórica%'
       OR nombre_comercial ILIKE '%pletorica%';

    IF v_matches = 0 THEN
        RAISE EXCEPTION 'No se encontró una empresa Pletórica/Pletorica en public.empresas';
    END IF;

    IF v_matches > 1 THEN
        RAISE EXCEPTION 'Se encontraron % empresas que coinciden con Pletórica/Pletorica. Filtra por id antes de ejecutar.', v_matches;
    END IF;

    RAISE NOTICE 'Borrando datos de empresa_id=%', v_empresa_id;

    -- 1. Nómina operativa de la empresa
    -- periodos_nomina -> nominas_empleado -> nomina_movimientos (cascade)
    DELETE FROM public.periodos_nomina
    WHERE empresa_id = v_empresa_id;

    -- 2. Cotizador
    -- cotizaciones -> partidas -> categorias/conceptos/valores (cascade)
    DELETE FROM public.cotizaciones
    WHERE empresa_id = v_empresa_id;

    DELETE FROM public.configuracion_fiscal_empresa
    WHERE empresa_id = v_empresa_id;

    -- 3. Dependencias RESTRICT de empleados
    DELETE FROM public.empleado_restricciones_log
    WHERE empleado_id IN (
        SELECT id
        FROM public.empleados
        WHERE empresa_id = v_empresa_id
    );

    DELETE FROM public.bajas_empleado
    WHERE empresa_id = v_empresa_id
       OR empleado_id IN (
            SELECT id
            FROM public.empleados
            WHERE empresa_id = v_empresa_id
       );

    DELETE FROM public.historial_laboral
    WHERE empleado_id IN (
        SELECT id
        FROM public.empleados
        WHERE empresa_id = v_empresa_id
    );

    -- 4. Liberar asignaciones directas antes de borrar empleados
    UPDATE public.plazas
    SET empleado_id = NULL
    WHERE empleado_id IN (
        SELECT id
        FROM public.empleados
        WHERE empresa_id = v_empresa_id
    );

    -- 5. Dependencias RESTRICT de contratos
    DELETE FROM public.entregables
    WHERE contrato_id IN (
        SELECT id
        FROM public.contratos
        WHERE empresa_id = v_empresa_id
    );

    DELETE FROM public.pagos
    WHERE contrato_id IN (
        SELECT id
        FROM public.contratos
        WHERE empresa_id = v_empresa_id
    );

    -- 6. Empleados
    -- El resto de dependencias cae por cascade:
    -- empleado_documentos, cuenta_bancaria_historial,
    -- empleado_descuentos_recurrentes, incidencias, registros, supervisor_sedes, etc.
    DELETE FROM public.empleados
    WHERE empresa_id = v_empresa_id;

    -- 7. Contratos
    -- El resto de dependencias cae por cascade:
    -- plazas, contrato_categorias, contrato_item, horarios, jornadas, etc.
    DELETE FROM public.contratos
    WHERE empresa_id = v_empresa_id;
END $$;

-- Verificación rápida
SELECT
    e.id AS empresa_id,
    e.nombre_comercial,
    (
        SELECT COUNT(*)
        FROM public.empleados emp
        WHERE emp.empresa_id = e.id
    ) AS empleados_restantes,
    (
        SELECT COUNT(*)
        FROM public.contratos c
        WHERE c.empresa_id = e.id
    ) AS contratos_restantes,
    (
        SELECT COUNT(*)
        FROM public.cotizaciones cot
        WHERE cot.empresa_id = e.id
    ) AS cotizaciones_restantes,
    (
        SELECT COUNT(*)
        FROM public.configuracion_fiscal_empresa cfe
        WHERE cfe.empresa_id = e.id
    ) AS config_fiscal_restante
FROM public.empresas e
WHERE e.nombre_comercial ILIKE '%pletórica%'
   OR e.nombre_comercial ILIKE '%pletorica%';

COMMIT;
