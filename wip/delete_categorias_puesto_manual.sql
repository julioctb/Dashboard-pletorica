-- Borrado manual de categorias_puesto.
--
-- Este script limpia primero referencias que bloquean el DELETE por FKs RESTRICT:
-- - plazas.categoria_puesto_id              (se pone en NULL)
-- - contrato_categorias.categoria_puesto_id (DELETE)
-- - cotizacion_partida_categorias           (DELETE)
-- - entregable_detalle_personal             (DELETE)
--
-- Puedes borrar:
-- - TODAS las categorias (v_tipo_servicio_clave := NULL)
-- - solo las de un tipo de servicio (ej. v_tipo_servicio_clave := 'JAR')

BEGIN;

DO $$
DECLARE
    v_tipo_servicio_clave TEXT := NULL; -- NULL = todas
    v_categoria_ids INTEGER[];
    v_total INTEGER := 0;
BEGIN
    SELECT ARRAY_AGG(cp.id ORDER BY cp.id)
    INTO v_categoria_ids
    FROM public.categorias_puesto cp
    JOIN public.tipos_servicio ts ON ts.id = cp.tipo_servicio_id
    WHERE v_tipo_servicio_clave IS NULL
       OR ts.clave = v_tipo_servicio_clave;

    IF v_categoria_ids IS NULL OR ARRAY_LENGTH(v_categoria_ids, 1) IS NULL THEN
        RAISE NOTICE 'No hay categorias_puesto para el filtro actual.';
        RETURN;
    END IF;

    v_total := ARRAY_LENGTH(v_categoria_ids, 1);
    RAISE NOTICE 'Categorias objetivo: %', v_total;

    -- 1) Cotizador (si existe)
    IF to_regclass('public.cotizacion_partida_categorias') IS NOT NULL THEN
        DELETE FROM public.cotizacion_partida_categorias
        WHERE categoria_puesto_id = ANY(v_categoria_ids);
    END IF;

    -- 2) Entregables detalle personal (si existe)
    IF to_regclass('public.entregable_detalle_personal') IS NOT NULL THEN
        DELETE FROM public.entregable_detalle_personal
        WHERE categoria_puesto_id = ANY(v_categoria_ids);
    END IF;

    -- 3) Planeacion por contrato (si existe)
    IF to_regclass('public.contrato_categorias') IS NOT NULL THEN
        DELETE FROM public.contrato_categorias
        WHERE categoria_puesto_id = ANY(v_categoria_ids);
    END IF;

    -- 4) Plazas: liberar categoria para permitir borrado de catalogo
    IF to_regclass('public.plazas') IS NOT NULL THEN
        IF EXISTS (
            SELECT 1
            FROM information_schema.columns
            WHERE table_schema = 'public'
              AND table_name = 'plazas'
              AND column_name = 'categoria_puesto_id'
        ) THEN
            UPDATE public.plazas
            SET categoria_puesto_id = NULL
            WHERE categoria_puesto_id = ANY(v_categoria_ids);
        END IF;
    END IF;

    -- 5) Catalogo de categorias
    DELETE FROM public.categorias_puesto
    WHERE id = ANY(v_categoria_ids);
END $$;

-- Verificacion
SELECT
    ts.clave AS tipo_servicio_clave,
    ts.nombre AS tipo_servicio_nombre,
    COUNT(cp.id) AS categorias_restantes
FROM public.tipos_servicio ts
LEFT JOIN public.categorias_puesto cp
    ON cp.tipo_servicio_id = ts.id
GROUP BY ts.id, ts.clave, ts.nombre
ORDER BY ts.nombre;

COMMIT;
