-- ============================================================================
-- Migration: Create Tipos Servicio Table
-- Fecha: 2026-01-31
-- Descripción: Crea la tabla de catálogo de tipos de servicio (Jardinería,
--              Limpieza, Mantenimiento, etc.). Tabla global independiente.
-- ============================================================================

-- ============================================================================
-- 1. Crear tipos ENUM (si no existen)
-- ============================================================================

-- Estatus genérico (compartido con otras tablas)
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'estatus_enum') THEN
        CREATE TYPE estatus_enum AS ENUM ('ACTIVO', 'INACTIVO');
    END IF;
END $$;

-- ============================================================================
-- 2. Crear tabla de tipos_servicio
-- ============================================================================
CREATE TABLE IF NOT EXISTS public.tipos_servicio (
    -- Identificación
    id SERIAL PRIMARY KEY,
    clave VARCHAR(5) NOT NULL,
    nombre VARCHAR(50) NOT NULL,
    descripcion VARCHAR(500) DEFAULT NULL,

    -- Estado
    estatus estatus_enum NOT NULL DEFAULT 'ACTIVO',

    -- Auditoría
    fecha_creacion TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    fecha_actualizacion TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Restricciones de unicidad
    CONSTRAINT uk_tipos_servicio_clave UNIQUE (clave),

    -- Validaciones
    CONSTRAINT chk_tipos_servicio_clave_formato CHECK (
        clave ~ '^[A-Z]{2,5}$'
    ),
    CONSTRAINT chk_tipos_servicio_nombre CHECK (
        LENGTH(TRIM(nombre)) >= 2 AND LENGTH(TRIM(nombre)) <= 50
    )
);

-- ============================================================================
-- 3. Comentarios de documentación
-- ============================================================================
COMMENT ON TABLE public.tipos_servicio IS
'Catálogo global de tipos de servicio (Jardinería, Limpieza, Mantenimiento, etc.).
Usado en contratos para clasificar el tipo de servicio prestado.
Independiente de empresas - un tipo puede ser usado por múltiples empresas.';

COMMENT ON COLUMN public.tipos_servicio.clave IS
'Clave única de 2-5 letras mayúsculas (ej: JAR, LIM, MTO)';

COMMENT ON COLUMN public.tipos_servicio.nombre IS
'Nombre descriptivo del tipo de servicio (ej: Jardinería, Limpieza)';

COMMENT ON COLUMN public.tipos_servicio.descripcion IS
'Descripción extendida del tipo de servicio (opcional, hasta 500 chars)';

-- ============================================================================
-- 4. Índices de rendimiento
-- ============================================================================

-- Índice único para clave (ya cubierto por UNIQUE constraint)
CREATE UNIQUE INDEX IF NOT EXISTS idx_tipos_servicio_clave
ON public.tipos_servicio (clave);

-- Índice para búsqueda por nombre (case-insensitive)
CREATE INDEX IF NOT EXISTS idx_tipos_servicio_nombre_lower
ON public.tipos_servicio USING btree (LOWER(nombre));

-- Índice para filtro por estatus
CREATE INDEX IF NOT EXISTS idx_tipos_servicio_estatus
ON public.tipos_servicio (estatus);

-- ============================================================================
-- 5. Trigger para actualizar fecha_actualizacion
-- ============================================================================
CREATE OR REPLACE FUNCTION update_tipos_servicio_fecha_actualizacion()
RETURNS TRIGGER AS $$
BEGIN
    NEW.fecha_actualizacion = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_tipos_servicio_fecha_actualizacion ON public.tipos_servicio;

CREATE TRIGGER trg_tipos_servicio_fecha_actualizacion
    BEFORE UPDATE ON public.tipos_servicio
    FOR EACH ROW
    EXECUTE FUNCTION update_tipos_servicio_fecha_actualizacion();

-- ============================================================================
-- 6. Datos de catálogo inicial (opcional)
-- ============================================================================
-- Insertar tipos de servicio comunes
INSERT INTO public.tipos_servicio (clave, nombre, descripcion, estatus) VALUES
    ('JAR', 'Jardinería', 'Servicios de mantenimiento de jardines y áreas verdes', 'ACTIVO'),
    ('LIM', 'Limpieza', 'Servicios de limpieza de instalaciones', 'ACTIVO'),
    ('MTO', 'Mantenimiento', 'Mantenimiento general de instalaciones', 'ACTIVO'),
    ('SEG', 'Seguridad', 'Servicios de seguridad y vigilancia', 'ACTIVO'),
    ('ALI', 'Alimentos', 'Servicios de cafetería y alimentos', 'ACTIVO')
ON CONFLICT (clave) DO NOTHING;

-- ============================================================================
-- Verificación de la migración
-- ============================================================================
-- SELECT
--     column_name,
--     data_type,
--     is_nullable,
--     column_default
-- FROM information_schema.columns
-- WHERE table_name = 'tipos_servicio'
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
-- WHERE tablename = 'tipos_servicio'
-- ORDER BY indexname;

-- ============================================================================
-- Verificar datos insertados
-- ============================================================================
-- SELECT * FROM public.tipos_servicio ORDER BY nombre;

-- ============================================================================
-- Rollback (si necesitas revertir la migración)
-- ============================================================================
-- DROP TRIGGER IF EXISTS trg_tipos_servicio_fecha_actualizacion ON public.tipos_servicio;
-- DROP FUNCTION IF EXISTS update_tipos_servicio_fecha_actualizacion();
-- DROP TABLE IF EXISTS public.tipos_servicio CASCADE;
-- DROP TYPE IF EXISTS estatus_enum;
