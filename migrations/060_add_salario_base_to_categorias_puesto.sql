-- ============================================================================
-- Migration: Agregar sueldo base mensual a categorias_puesto
-- Fecha: 2026-03-21
-- Descripcion:
--   - agrega salario_base_mensual opcional a categorias_puesto
--   - permite configurar un sueldo de referencia por categoria
-- ============================================================================

BEGIN;

ALTER TABLE public.categorias_puesto
    ADD COLUMN IF NOT EXISTS salario_base_mensual DECIMAL(12,2);

ALTER TABLE public.categorias_puesto
    DROP CONSTRAINT IF EXISTS chk_categorias_salario_base_mensual;

ALTER TABLE public.categorias_puesto
    ADD CONSTRAINT chk_categorias_salario_base_mensual
    CHECK (
        salario_base_mensual IS NULL
        OR salario_base_mensual >= 0
    );

COMMENT ON COLUMN public.categorias_puesto.salario_base_mensual IS
'Sueldo base mensual sugerido para plazas de esta categoria. Se usa como referencia operativa.';

COMMIT;
