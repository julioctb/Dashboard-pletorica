-- ============================================================================
-- Migration: Relacionar plazas con sedes
-- Fecha: 2026-03-08
-- Descripcion:
--   - agrega sede_id a plazas
--   - crea FK e indice para asignacion de plazas a sedes
-- ============================================================================

BEGIN;

ALTER TABLE public.plazas
    ADD COLUMN IF NOT EXISTS sede_id INTEGER;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'fk_plazas_sede'
    ) THEN
        ALTER TABLE public.plazas
            ADD CONSTRAINT fk_plazas_sede
            FOREIGN KEY (sede_id) REFERENCES public.sedes(id) ON DELETE RESTRICT;
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_plazas_sede_id
    ON public.plazas USING btree (sede_id)
    WHERE sede_id IS NOT NULL;

COMMENT ON COLUMN public.plazas.sede_id IS
'FK opcional a sedes - la plaza debe asignarse a una sede antes de ocuparse';

COMMIT;
