-- ============================================================================
-- Migration: Create Categorias Puesto Table
-- Fecha: 2026-01-31
-- Descripción: Crea la tabla de categorías de puesto dentro de cada tipo de servicio.
--              Ejemplo: Jardinería tiene JARA (Jardinero A), JARB (Jardinero B), SUP (Supervisor)
--              Depende de: tipos_servicio
-- ============================================================================

-- ============================================================================
-- 1. Crear tabla de categorias_puesto
-- ============================================================================
CREATE TABLE IF NOT EXISTS public.categorias_puesto (
    -- Identificación
    id SERIAL PRIMARY KEY,
    tipo_servicio_id INTEGER NOT NULL REFERENCES public.tipos_servicio(id) ON DELETE RESTRICT,
    clave VARCHAR(5) NOT NULL,
    nombre VARCHAR(50) NOT NULL,
    descripcion VARCHAR(500) DEFAULT NULL,

    -- Orden de visualización
    orden INTEGER NOT NULL DEFAULT 0,

    -- Estado
    estatus estatus_enum NOT NULL DEFAULT 'ACTIVO',

    -- Auditoría
    fecha_creacion TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    fecha_actualizacion TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Restricciones de unicidad
    CONSTRAINT uk_categorias_tipo_clave UNIQUE (tipo_servicio_id, clave),

    -- Validaciones
    CONSTRAINT chk_categorias_clave_formato CHECK (
        clave ~ '^[A-Z]{2,5}$'
    ),
    CONSTRAINT chk_categorias_nombre CHECK (
        LENGTH(TRIM(nombre)) >= 2 AND LENGTH(TRIM(nombre)) <= 50
    ),
    CONSTRAINT chk_categorias_orden CHECK (orden >= 0)
);

-- ============================================================================
-- 2. Comentarios de documentación
-- ============================================================================
COMMENT ON TABLE public.categorias_puesto IS
'Categorías de puesto dentro de cada tipo de servicio.
Ejemplo: Jardinería (JAR) tiene JARA, JARB, SUP.
La clave es única DENTRO de cada tipo de servicio (puede haber JARA en Jardinería y JARA en Limpieza).';

COMMENT ON COLUMN public.categorias_puesto.tipo_servicio_id IS
'FK al tipo de servicio (Jardinería, Limpieza, etc.)';

COMMENT ON COLUMN public.categorias_puesto.clave IS
'Clave única dentro del tipo de servicio (2-5 letras mayúsculas: JARA, JARB, SUP)';

COMMENT ON COLUMN public.categorias_puesto.nombre IS
'Nombre descriptivo de la categoría (ej: Jardinero A, Jardinero B, Supervisor)';

COMMENT ON COLUMN public.categorias_puesto.orden IS
'Orden de visualización (0 = primero). Usado en listas y selects.';

-- ============================================================================
-- 3. Índices de rendimiento
-- ============================================================================

-- Índice único compuesto (tipo_servicio_id, clave)
CREATE UNIQUE INDEX IF NOT EXISTS idx_categorias_tipo_clave
ON public.categorias_puesto (tipo_servicio_id, clave);

-- Índice para FK (joins rápidos con tipos_servicio)
CREATE INDEX IF NOT EXISTS idx_categorias_tipo_servicio_id
ON public.categorias_puesto (tipo_servicio_id);

-- Índice compuesto para ordenamiento (tipo + orden)
CREATE INDEX IF NOT EXISTS idx_categorias_tipo_orden
ON public.categorias_puesto (tipo_servicio_id, orden);

-- Índice para búsqueda por nombre (case-insensitive)
CREATE INDEX IF NOT EXISTS idx_categorias_nombre_lower
ON public.categorias_puesto USING btree (LOWER(nombre));

-- Índice para filtro por estatus
CREATE INDEX IF NOT EXISTS idx_categorias_estatus
ON public.categorias_puesto (estatus);

-- ============================================================================
-- 4. Trigger para actualizar fecha_actualizacion
-- ============================================================================
CREATE OR REPLACE FUNCTION update_categorias_puesto_fecha_actualizacion()
RETURNS TRIGGER AS $$
BEGIN
    NEW.fecha_actualizacion = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_categorias_puesto_fecha_actualizacion ON public.categorias_puesto;

CREATE TRIGGER trg_categorias_puesto_fecha_actualizacion
    BEFORE UPDATE ON public.categorias_puesto
    FOR EACH ROW
    EXECUTE FUNCTION update_categorias_puesto_fecha_actualizacion();

-- ============================================================================
-- 5. Datos de catálogo inicial (opcional)
-- ============================================================================
-- Insertar categorías para Jardinería (asumiendo que JAR tiene id=1)
DO $$
DECLARE
    jar_id INTEGER;
BEGIN
    -- Obtener ID de Jardinería
    SELECT id INTO jar_id FROM public.tipos_servicio WHERE clave = 'JAR';

    IF jar_id IS NOT NULL THEN
        INSERT INTO public.categorias_puesto (tipo_servicio_id, clave, nombre, descripcion, orden, estatus) VALUES
            (jar_id, 'JARA', 'Jardinero A', 'Jardinero categoría A', 0, 'ACTIVO'),
            (jar_id, 'JARB', 'Jardinero B', 'Jardinero categoría B', 1, 'ACTIVO'),
            (jar_id, 'SUP', 'Supervisor', 'Supervisor de jardinería', 2, 'ACTIVO')
        ON CONFLICT (tipo_servicio_id, clave) DO NOTHING;
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
-- WHERE table_name = 'categorias_puesto'
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
-- WHERE tablename = 'categorias_puesto'
-- ORDER BY indexname;

-- ============================================================================
-- Verificar datos con JOIN
-- ============================================================================
-- SELECT
--     c.id,
--     t.nombre AS tipo_servicio,
--     c.clave,
--     c.nombre,
--     c.orden,
--     c.estatus
-- FROM public.categorias_puesto c
-- JOIN public.tipos_servicio t ON c.tipo_servicio_id = t.id
-- ORDER BY t.nombre, c.orden;

-- ============================================================================
-- Rollback (si necesitas revertir la migración)
-- ============================================================================
-- DROP TRIGGER IF EXISTS trg_categorias_puesto_fecha_actualizacion ON public.categorias_puesto;
-- DROP FUNCTION IF EXISTS update_categorias_puesto_fecha_actualizacion();
-- DROP TABLE IF EXISTS public.categorias_puesto CASCADE;
