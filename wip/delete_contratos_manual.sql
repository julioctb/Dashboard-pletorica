-- Borrado manual de contratos.
--
-- Incluye limpieza previa de tablas con FK ON DELETE RESTRICT:
-- - public.entregables
-- - public.pagos
--
-- Uso:
-- 1) Para borrar contratos de una empresa (recomendado):
--    - deja v_borrar_todos = FALSE
--    - ajusta v_empresa_nombre_like
-- 2) Para borrar TODOS los contratos:
--    - cambia v_borrar_todos = TRUE

BEGIN;

DO $$
DECLARE
    v_borrar_todos BOOLEAN := FALSE;
    v_empresa_nombre_like TEXT := '%pletorica%';
    v_empresa_id INTEGER;
    v_matches INTEGER := 0;
    v_contrato_ids INTEGER[];
    v_total_contratos INTEGER := 0;
BEGIN
    IF v_borrar_todos THEN
        SELECT ARRAY_AGG(id ORDER BY id)
        INTO v_contrato_ids
        FROM public.contratos;
    ELSE
        SELECT COUNT(*), MIN(id)
        INTO v_matches, v_empresa_id
        FROM public.empresas
        WHERE LOWER(nombre_comercial) LIKE LOWER(v_empresa_nombre_like);

        IF v_matches = 0 THEN
            RAISE EXCEPTION
                'No se encontro empresa con nombre_comercial LIKE %',
                v_empresa_nombre_like;
        END IF;

        IF v_matches > 1 THEN
            RAISE EXCEPTION
                'Se encontraron % empresas con nombre_comercial LIKE %. Ajusta el filtro.',
                v_matches,
                v_empresa_nombre_like;
        END IF;

        SELECT ARRAY_AGG(id ORDER BY id)
        INTO v_contrato_ids
        FROM public.contratos
        WHERE empresa_id = v_empresa_id;
    END IF;

    IF v_contrato_ids IS NULL OR ARRAY_LENGTH(v_contrato_ids, 1) IS NULL THEN
        RAISE NOTICE 'No hay contratos para borrar con el filtro actual.';
        RETURN;
    END IF;

    v_total_contratos := ARRAY_LENGTH(v_contrato_ids, 1);
    RAISE NOTICE 'Contratos objetivo: %', v_total_contratos;

    -- 1) Dependencias RESTRICT
    IF to_regclass('public.entregables') IS NOT NULL THEN
        DELETE FROM public.entregables
        WHERE contrato_id = ANY(v_contrato_ids);
    END IF;

    IF to_regclass('public.pagos') IS NOT NULL THEN
        DELETE FROM public.pagos
        WHERE contrato_id = ANY(v_contrato_ids);
    END IF;

    -- 2) Contratos
    -- El resto de dependencias cae por CASCADE o SET NULL:
    -- plazas, contrato_categorias, contrato_item, horarios, jornadas,
    -- registros_asistencia, cotizacion_partidas.contrato_id (SET NULL), etc.
    DELETE FROM public.contratos
    WHERE id = ANY(v_contrato_ids);
END $$;

-- Verificacion rapida
SELECT
    e.id AS empresa_id,
    e.nombre_comercial,
    COUNT(c.id) AS contratos_restantes
FROM public.empresas e
LEFT JOIN public.contratos c
    ON c.empresa_id = e.id
GROUP BY e.id, e.nombre_comercial
ORDER BY e.nombre_comercial;

COMMIT;
