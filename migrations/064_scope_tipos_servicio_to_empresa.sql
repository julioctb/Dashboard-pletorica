-- ============================================================================
-- Migration: Scope tipos_servicio to empresa
-- Fecha: 2026-04-10
-- Descripción: prepara el catálogo de tipos de servicio para que cada empresa
--              pueda administrar sus propios tipos desde el portal.
-- ============================================================================

ALTER TABLE public.tipos_servicio
ADD COLUMN IF NOT EXISTS empresa_id INTEGER REFERENCES public.empresas(id) ON DELETE RESTRICT;

ALTER TABLE public.tipos_servicio
ADD COLUMN IF NOT EXISTS origen VARCHAR(15);

UPDATE public.tipos_servicio
SET origen = 'EMPRESA'
WHERE origen IS NULL;

ALTER TABLE public.tipos_servicio
ALTER COLUMN origen SET DEFAULT 'EMPRESA';

ALTER TABLE public.tipos_servicio
ALTER COLUMN origen SET NOT NULL;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'chk_tipos_servicio_origen'
    ) THEN
        ALTER TABLE public.tipos_servicio
        ADD CONSTRAINT chk_tipos_servicio_origen
        CHECK (origen IN ('EMPRESA', 'INSTITUCION'));
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_tipos_servicio_empresa_origen_estatus
ON public.tipos_servicio (empresa_id, origen, estatus);

CREATE UNIQUE INDEX IF NOT EXISTS idx_tipos_servicio_empresa_nombre_origen
ON public.tipos_servicio (empresa_id, LOWER(nombre), origen)
WHERE empresa_id IS NOT NULL;
