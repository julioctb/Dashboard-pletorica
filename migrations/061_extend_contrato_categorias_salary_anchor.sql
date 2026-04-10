-- ============================================================================
-- MIGRACION 061: Extender contrato_categorias con sueldo ancla por categoria
-- ============================================================================
-- Objetivo:
--   - guardar el nombre visible contractual de la categoria
--   - almacenar el sueldo capturado por el usuario y su tipo (BRUTO / NETO)
--   - mantener compatibilidad con costo_unitario como bruto operativo legado
-- ============================================================================

ALTER TABLE public.contrato_categorias
    ADD COLUMN IF NOT EXISTS nombre VARCHAR(120);

ALTER TABLE public.contrato_categorias
    ADD COLUMN IF NOT EXISTS sueldo_base NUMERIC(12, 2);

ALTER TABLE public.contrato_categorias
    ADD COLUMN IF NOT EXISTS tipo_sueldo VARCHAR(10) NOT NULL DEFAULT 'BRUTO';

UPDATE public.contrato_categorias cc
SET nombre = cp.nombre
FROM public.categorias_puesto cp
WHERE cc.categoria_puesto_id = cp.id
  AND COALESCE(TRIM(cc.nombre), '') = '';

UPDATE public.contrato_categorias
SET sueldo_base = costo_unitario
WHERE sueldo_base IS NULL
  AND costo_unitario IS NOT NULL;

UPDATE public.contrato_categorias
SET tipo_sueldo = 'BRUTO'
WHERE COALESCE(TRIM(tipo_sueldo), '') = '';

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'chk_contrato_categorias_tipo_sueldo'
    ) THEN
        ALTER TABLE public.contrato_categorias
            ADD CONSTRAINT chk_contrato_categorias_tipo_sueldo
            CHECK (tipo_sueldo IN ('BRUTO', 'NETO'));
    END IF;
END $$;

COMMENT ON COLUMN public.contrato_categorias.nombre IS
'Nombre visible de la categoria dentro del contrato. Puede diferir del catalogo.';

COMMENT ON COLUMN public.contrato_categorias.sueldo_base IS
'Sueldo capturado por el usuario; representa el ancla segun tipo_sueldo.';

COMMENT ON COLUMN public.contrato_categorias.tipo_sueldo IS
'Indica si sueldo_base fue capturado como BRUTO o NETO.';
