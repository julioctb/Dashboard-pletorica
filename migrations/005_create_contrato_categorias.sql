-- ============================================================================
-- Migration: Create Contrato Categorias Table
-- Fecha: 2026-01-31
-- Descripción: Crea la tabla intermedia contrato-categorías de puesto.
--              Especifica cantidades mínimas/máximas de personal por categoría en cada contrato.
--              Ejemplo: Contrato MAN-JAR-25001 tiene 50-70 JARA, 10-15 JARB, 3-5 SUP
--              Depende de: contratos, categorias_puesto
-- ============================================================================

-- ============================================================================
-- 1. Crear tabla de contrato_categorias
-- ============================================================================
CREATE TABLE IF NOT EXISTS public.contrato_categorias (
    -- Identificación
    id SERIAL PRIMARY KEY,
    contrato_id INTEGER NOT NULL REFERENCES public.contratos(id) ON DELETE CASCADE,
    categoria_puesto_id INTEGER NOT NULL REFERENCES public.categorias_puesto(id) ON DELETE RESTRICT,

    -- Cantidades de personal
    cantidad_minima INTEGER NOT NULL,
    cantidad_maxima INTEGER NOT NULL,

    -- Costo
    costo_unitario DECIMAL(10,2) DEFAULT NULL,

    -- Notas
    notas VARCHAR(1000) DEFAULT NULL,

    -- Auditoría
    fecha_creacion TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    fecha_actualizacion TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Restricciones de unicidad
    CONSTRAINT uk_contrato_categorias_contrato_categoria UNIQUE (contrato_id, categoria_puesto_id),

    -- Validaciones
    CONSTRAINT chk_contrato_categorias_cantidad_minima CHECK (cantidad_minima >= 0),
    CONSTRAINT chk_contrato_categorias_cantidad_maxima CHECK (cantidad_maxima >= 0),
    CONSTRAINT chk_contrato_categorias_cantidades CHECK (cantidad_maxima >= cantidad_minima),
    CONSTRAINT chk_contrato_categorias_costo CHECK (
        costo_unitario IS NULL OR costo_unitario >= 0
    )
);

-- ============================================================================
-- 2. Comentarios de documentación
-- ============================================================================
COMMENT ON TABLE public.contrato_categorias IS
'Tabla intermedia que especifica las cantidades de personal por categoría en cada contrato.
Ejemplo: Contrato MAN-JAR-25001 requiere:
  - Jardinero A (JARA): mínimo 50, máximo 70 personas
  - Jardinero B (JARB): mínimo 10, máximo 15 personas
  - Supervisor (SUP): mínimo 3, máximo 5 personas';

COMMENT ON COLUMN public.contrato_categorias.contrato_id IS
'FK al contrato. ON DELETE CASCADE porque si se elimina el contrato, se eliminan las categorías asociadas.';

COMMENT ON COLUMN public.contrato_categorias.categoria_puesto_id IS
'FK a la categoría de puesto. ON DELETE RESTRICT porque no se puede eliminar categoría usada en contrato.';

COMMENT ON COLUMN public.contrato_categorias.cantidad_minima IS
'Cantidad mínima de personal comprometida en el contrato (>= 0)';

COMMENT ON COLUMN public.contrato_categorias.cantidad_maxima IS
'Cantidad máxima de personal autorizada en el contrato (>= cantidad_minima)';

COMMENT ON COLUMN public.contrato_categorias.costo_unitario IS
'Costo por persona/mes (opcional, >= 0)';

-- ============================================================================
-- 3. Índices de rendimiento
-- ============================================================================

-- Índice único compuesto (una categoría por contrato)
CREATE UNIQUE INDEX IF NOT EXISTS idx_contrato_categorias_contrato_categoria
ON public.contrato_categorias (contrato_id, categoria_puesto_id);

-- Índices para FKs (joins frecuentes)
CREATE INDEX IF NOT EXISTS idx_contrato_categorias_contrato_id
ON public.contrato_categorias (contrato_id);

CREATE INDEX IF NOT EXISTS idx_contrato_categorias_categoria_id
ON public.contrato_categorias (categoria_puesto_id);

-- ============================================================================
-- 4. Trigger para actualizar fecha_actualizacion
-- ============================================================================
CREATE OR REPLACE FUNCTION update_contrato_categorias_fecha_actualizacion()
RETURNS TRIGGER AS $$
BEGIN
    NEW.fecha_actualizacion = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_contrato_categorias_fecha_actualizacion ON public.contrato_categorias;

CREATE TRIGGER trg_contrato_categorias_fecha_actualizacion
    BEFORE UPDATE ON public.contrato_categorias
    FOR EACH ROW
    EXECUTE FUNCTION update_contrato_categorias_fecha_actualizacion();

-- ============================================================================
-- 5. Agregar FK a tabla plazas (si existe)
-- ============================================================================
-- La tabla plazas tiene una FK a contrato_categorias
-- Este bloque se ejecuta solo si la tabla plazas ya existe
DO $$
BEGIN
    -- Verificar si la columna contrato_categoria_id existe en plazas
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'plazas' AND column_name = 'contrato_categoria_id'
    ) THEN
        -- Verificar si la FK ya existe
        IF NOT EXISTS (
            SELECT 1 FROM information_schema.table_constraints
            WHERE constraint_name = 'fk_plazas_contrato_categoria' AND table_name = 'plazas'
        ) THEN
            ALTER TABLE public.plazas
            ADD CONSTRAINT fk_plazas_contrato_categoria
            FOREIGN KEY (contrato_categoria_id) REFERENCES public.contrato_categorias(id)
            ON DELETE RESTRICT;

            RAISE NOTICE 'FK fk_plazas_contrato_categoria agregada a tabla plazas';
        ELSE
            RAISE NOTICE 'FK fk_plazas_contrato_categoria ya existe en tabla plazas';
        END IF;
    ELSE
        RAISE NOTICE 'Tabla plazas no existe todavía - FK se agregará en su migración';
    END IF;
END $$;

-- ============================================================================
-- Verificación de la migración
-- ============================================================================
-- SELECT
--     column_name,
--     data_type,
--     is_nullable,
--     column_default
-- FROM information_schema.columns
-- WHERE table_name = 'contrato_categorias'
-- ORDER BY ordinal_position;

-- ============================================================================
-- Verificar índices creados
-- ============================================================================
-- SELECT
--     schemaname,
--     tablename,
--     indexname,
--     indexdef
-- FROM pg_indexes
-- WHERE tablename = 'contrato_categorias'
-- ORDER BY indexname;

-- ============================================================================
-- Consulta útil: Ver contrato con todas sus categorías
-- ============================================================================
-- SELECT
--     c.codigo AS contrato,
--     t.nombre AS tipo_servicio,
--     cat.nombre AS categoria,
--     cc.cantidad_minima,
--     cc.cantidad_maxima,
--     cc.costo_unitario
-- FROM public.contrato_categorias cc
-- JOIN public.contratos c ON cc.contrato_id = c.id
-- JOIN public.categorias_puesto cat ON cc.categoria_puesto_id = cat.id
-- JOIN public.tipos_servicio t ON cat.tipo_servicio_id = t.id
-- WHERE c.codigo = 'MAN-JAR-25001'
-- ORDER BY cat.orden;

-- ============================================================================
-- Ejemplo de datos de prueba
-- ============================================================================
-- INSERT INTO public.contrato_categorias (
--     contrato_id, categoria_puesto_id,
--     cantidad_minima, cantidad_maxima, costo_unitario
-- ) VALUES
--     (1, 1, 50, 70, 8500.00),  -- Jardinero A
--     (1, 2, 10, 15, 9000.00),  -- Jardinero B
--     (1, 3, 3, 5, 12000.00);   -- Supervisor

-- ============================================================================
-- Rollback (si necesitas revertir la migración)
-- ============================================================================
-- ALTER TABLE public.plazas DROP CONSTRAINT IF EXISTS fk_plazas_contrato_categoria;
-- DROP TRIGGER IF EXISTS trg_contrato_categorias_fecha_actualizacion ON public.contrato_categorias;
-- DROP FUNCTION IF EXISTS update_contrato_categorias_fecha_actualizacion();
-- DROP TABLE IF EXISTS public.contrato_categorias CASCADE;
