-- ============================================================================
-- Migration: Refactor a modelo plazas-first
-- Fecha: 2026-03-08
-- Descripción:
--   - contratos guarda cantidades totales de plazas
--   - plazas depende directamente de contrato + categoría opcional
--   - entregable_detalle_personal referencia categoría directamente
--   - contrato_categorias deja de ser parte del flujo activo
-- ============================================================================

BEGIN;

-- ============================================================================
-- 1. contratos: cantidades totales de plazas
-- ============================================================================
ALTER TABLE public.contratos
    ADD COLUMN IF NOT EXISTS cantidad_plazas_minima INTEGER NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS cantidad_plazas_maxima INTEGER NOT NULL DEFAULT 0;

ALTER TABLE public.contratos
    DROP CONSTRAINT IF EXISTS chk_contratos_plazas_totales;

ALTER TABLE public.contratos
    ADD CONSTRAINT chk_contratos_plazas_totales
    CHECK (cantidad_plazas_maxima >= cantidad_plazas_minima);

UPDATE public.contratos c
SET
    cantidad_plazas_minima = src.total_minimo,
    cantidad_plazas_maxima = src.total_maximo
FROM (
    SELECT
        contrato_id,
        COALESCE(SUM(cantidad_minima), 0) AS total_minimo,
        COALESCE(SUM(cantidad_maxima), 0) AS total_maximo
    FROM public.contrato_categorias
    GROUP BY contrato_id
) src
WHERE c.id = src.contrato_id;

-- ============================================================================
-- 2. plazas: dependencia directa de contrato y categoría opcional
-- ============================================================================
ALTER TABLE public.plazas
    ADD COLUMN IF NOT EXISTS contrato_id INTEGER,
    ADD COLUMN IF NOT EXISTS categoria_puesto_id INTEGER;

UPDATE public.plazas p
SET
    contrato_id = cc.contrato_id,
    categoria_puesto_id = cc.categoria_puesto_id
FROM public.contrato_categorias cc
WHERE p.contrato_categoria_id = cc.id
  AND (p.contrato_id IS NULL OR p.categoria_puesto_id IS NULL);

ALTER TABLE public.plazas
    ALTER COLUMN contrato_id SET NOT NULL;

ALTER TABLE public.plazas
    DROP CONSTRAINT IF EXISTS uk_plaza_numero;

DROP INDEX IF EXISTS idx_plazas_contrato_categoria;
DROP INDEX IF EXISTS idx_plazas_categoria_estatus;
DROP INDEX IF EXISTS idx_plazas_numero;
DROP INDEX IF EXISTS idx_plazas_contrato_categoria_id;

ALTER TABLE public.plazas
    DROP COLUMN IF EXISTS contrato_categoria_id CASCADE;

ALTER TABLE public.plazas
    ADD CONSTRAINT fk_plazas_contrato
        FOREIGN KEY (contrato_id) REFERENCES public.contratos(id) ON DELETE CASCADE;

ALTER TABLE public.plazas
    ADD CONSTRAINT fk_plazas_categoria_puesto
        FOREIGN KEY (categoria_puesto_id) REFERENCES public.categorias_puesto(id) ON DELETE RESTRICT;

ALTER TABLE public.plazas
    ADD CONSTRAINT uk_plaza_numero UNIQUE (contrato_id, numero_plaza);

CREATE INDEX IF NOT EXISTS idx_plazas_contrato_id
    ON public.plazas USING btree (contrato_id);

CREATE INDEX IF NOT EXISTS idx_plazas_categoria_puesto_id
    ON public.plazas USING btree (categoria_puesto_id)
    WHERE categoria_puesto_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_plazas_contrato_estatus
    ON public.plazas USING btree (contrato_id, estatus);

CREATE INDEX IF NOT EXISTS idx_plazas_contrato_categoria_estatus
    ON public.plazas USING btree (contrato_id, categoria_puesto_id, estatus)
    WHERE categoria_puesto_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_plazas_numero
    ON public.plazas USING btree (contrato_id, numero_plaza);

COMMENT ON COLUMN public.plazas.contrato_id IS
'FK a contratos - define a qué contrato pertenece la plaza';

COMMENT ON COLUMN public.plazas.categoria_puesto_id IS
'FK opcional a categorias_puesto - NULL mientras la plaza no esté categorizada';

COMMENT ON COLUMN public.plazas.numero_plaza IS
'Número secuencial de la plaza dentro del contrato (1, 2, 3...)';

-- ============================================================================
-- 3. entregable_detalle_personal: referencia directa a categoría
-- ============================================================================
ALTER TABLE public.entregable_detalle_personal
    ADD COLUMN IF NOT EXISTS categoria_puesto_id INTEGER;

UPDATE public.entregable_detalle_personal edp
SET categoria_puesto_id = cc.categoria_puesto_id
FROM public.contrato_categorias cc
WHERE edp.contrato_categoria_id = cc.id
  AND edp.categoria_puesto_id IS NULL;

ALTER TABLE public.entregable_detalle_personal
    ALTER COLUMN categoria_puesto_id SET NOT NULL;

ALTER TABLE public.entregable_detalle_personal
    DROP CONSTRAINT IF EXISTS uk_detalle_categoria;

DROP INDEX IF EXISTS idx_entregable_detalle_personal_contrato_categoria;

ALTER TABLE public.entregable_detalle_personal
    DROP COLUMN IF EXISTS contrato_categoria_id CASCADE;

ALTER TABLE public.entregable_detalle_personal
    ADD CONSTRAINT fk_edp_categoria_puesto
        FOREIGN KEY (categoria_puesto_id) REFERENCES public.categorias_puesto(id) ON DELETE RESTRICT;

ALTER TABLE public.entregable_detalle_personal
    ADD CONSTRAINT uk_detalle_categoria UNIQUE (entregable_id, categoria_puesto_id);

CREATE INDEX IF NOT EXISTS idx_edp_categoria_puesto
    ON public.entregable_detalle_personal (categoria_puesto_id);

-- ============================================================================
-- 4. contrato_categorias fuera de uso
-- ============================================================================
DROP TABLE IF EXISTS public.contrato_categorias CASCADE;

COMMIT;
