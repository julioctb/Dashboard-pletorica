-- ============================================================================
-- Migration: Restaurar contrato_categorias como tabla de planeacion
-- Fecha: 2026-03-08
-- Descripcion:
--   - restaura public.contrato_categorias despues del refactor plazas-first
--   - desacopla la tabla del flujo estructural de plazas
--   - conserva el desglose minimo/maximo por categoria dentro del contrato
-- ============================================================================

BEGIN;

CREATE TABLE IF NOT EXISTS public.contrato_categorias (
    id SERIAL PRIMARY KEY,
    contrato_id INTEGER NOT NULL REFERENCES public.contratos(id) ON DELETE CASCADE,
    categoria_puesto_id INTEGER NOT NULL REFERENCES public.categorias_puesto(id) ON DELETE RESTRICT,
    cantidad_minima INTEGER NOT NULL DEFAULT 0,
    cantidad_maxima INTEGER NOT NULL DEFAULT 0,
    costo_unitario NUMERIC(10, 2) NULL,
    notas VARCHAR(1000) NULL,
    fecha_creacion TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    fecha_actualizacion TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uk_contrato_categorias_contrato_categoria UNIQUE (contrato_id, categoria_puesto_id),
    CONSTRAINT chk_contrato_categorias_cantidad_minima CHECK (cantidad_minima >= 0),
    CONSTRAINT chk_contrato_categorias_cantidad_maxima CHECK (cantidad_maxima >= 0),
    CONSTRAINT chk_contrato_categorias_cantidades CHECK (cantidad_maxima >= cantidad_minima),
    CONSTRAINT chk_contrato_categorias_costo CHECK (costo_unitario IS NULL OR costo_unitario >= 0)
);

COMMENT ON TABLE public.contrato_categorias IS
'Desglose planeado de plazas/personal por categoria dentro de un contrato. No vuelve a ser la FK estructural de plazas.';

COMMENT ON COLUMN public.contrato_categorias.contrato_id IS
'Contrato al que pertenece el desglose.';

COMMENT ON COLUMN public.contrato_categorias.categoria_puesto_id IS
'Categoria de puesto permitida dentro del contrato.';

COMMENT ON COLUMN public.contrato_categorias.cantidad_minima IS
'Cantidad minima comprometida para la categoria.';

COMMENT ON COLUMN public.contrato_categorias.cantidad_maxima IS
'Cantidad maxima autorizada para la categoria.';

CREATE UNIQUE INDEX IF NOT EXISTS idx_contrato_categorias_contrato_categoria
    ON public.contrato_categorias (contrato_id, categoria_puesto_id);

CREATE INDEX IF NOT EXISTS idx_contrato_categorias_contrato_id
    ON public.contrato_categorias (contrato_id);

CREATE INDEX IF NOT EXISTS idx_contrato_categorias_categoria_id
    ON public.contrato_categorias (categoria_puesto_id);

CREATE OR REPLACE FUNCTION update_contrato_categorias_fecha_actualizacion()
RETURNS TRIGGER AS $$
BEGIN
    NEW.fecha_actualizacion = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_contrato_categorias_fecha_actualizacion
    ON public.contrato_categorias;

CREATE TRIGGER trg_contrato_categorias_fecha_actualizacion
    BEFORE UPDATE ON public.contrato_categorias
    FOR EACH ROW
    EXECUTE FUNCTION update_contrato_categorias_fecha_actualizacion();

COMMIT;
