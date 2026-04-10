-- ============================================================================
-- MIGRACION 062: costo_contractual en contrato_categorias
-- ============================================================================
-- Objetivo:
--   - Agregar costo_contractual (lo que la empresa cobra al cliente por
--     persona/mes). Es distinto de costo_unitario / sueldo_base (lo que
--     la empresa paga al trabajador).
--   - cantidad_maxima = 0 pasa a significar "contrato abierto / sin tope"
--     (min_plazas/max_plazas en la UI de portal).
-- ============================================================================

ALTER TABLE public.contrato_categorias
    ADD COLUMN IF NOT EXISTS costo_contractual NUMERIC(12, 2);

COMMENT ON COLUMN public.contrato_categorias.costo_contractual IS
'Monto mensual que la empresa cobra al cliente por cada persona en la categoria. '
'NULL si aun no se ha definido. Se usa para calcular el margen frente al costo empresa.';

-- Relajar la restriccion min <= max si existe, para permitir max = 0 como "abierto".
DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'chk_contrato_categorias_cantidades'
    ) THEN
        ALTER TABLE public.contrato_categorias
            DROP CONSTRAINT chk_contrato_categorias_cantidades;
    END IF;
END $$;

ALTER TABLE public.contrato_categorias
    ADD CONSTRAINT chk_contrato_categorias_cantidades
    CHECK (
        cantidad_minima >= 0
        AND cantidad_maxima >= 0
        AND (cantidad_maxima = 0 OR cantidad_maxima >= cantidad_minima)
    );
