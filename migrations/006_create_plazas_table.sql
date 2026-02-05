-- ============================================================================
-- Migration: Create Plazas Table
-- Fecha: 2025-01-20
-- Descripción: Crea la tabla de plazas para gestionar puestos individuales
--              dentro de las relaciones contrato-categoría.
-- ============================================================================

-- ============================================================================
-- 1. Crear tipo ENUM para estatus de plaza
-- ============================================================================
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'estatus_plaza') THEN
        CREATE TYPE estatus_plaza AS ENUM (
            'VACANTE',
            'OCUPADA',
            'SUSPENDIDA',
            'CANCELADA'
        );
    END IF;
END $$;

-- ============================================================================
-- 2. Crear tabla de plazas
-- ============================================================================
CREATE TABLE IF NOT EXISTS public.plazas (
    -- Identificación
    id SERIAL PRIMARY KEY,
    contrato_categoria_id INTEGER NOT NULL REFERENCES public.contrato_categorias(id),
    numero_plaza INTEGER NOT NULL,
    codigo VARCHAR(50) DEFAULT '',

    -- Relación con empleado (null si está vacante)
    -- TODO: Agregar FK cuando exista la tabla empleados
    -- empleado_id INTEGER REFERENCES public.empleados(id),
    empleado_id INTEGER DEFAULT NULL,

    -- Vigencia
    fecha_inicio DATE NOT NULL,
    fecha_fin DATE DEFAULT NULL,

    -- Salario
    salario_mensual DECIMAL(12, 2) NOT NULL DEFAULT 0,

    -- Estado
    estatus estatus_plaza NOT NULL DEFAULT 'VACANTE',

    -- Observaciones
    notas TEXT DEFAULT NULL,

    -- Auditoría
    fecha_creacion TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    fecha_actualizacion TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Restricción única: no puede haber dos plazas con el mismo número en la misma categoría
    CONSTRAINT uk_plaza_numero UNIQUE (contrato_categoria_id, numero_plaza)
);

-- ============================================================================
-- 3. Comentarios de documentación
-- ============================================================================
COMMENT ON TABLE public.plazas IS
'Plazas individuales dentro de cada relación contrato-categoría.
Cada plaza puede estar vacante, ocupada por un empleado, suspendida o cancelada.';

COMMENT ON COLUMN public.plazas.contrato_categoria_id IS
'FK a contrato_categorias - define a qué categoría del contrato pertenece';

COMMENT ON COLUMN public.plazas.numero_plaza IS
'Número secuencial de la plaza dentro de la categoría (1, 2, 3...)';

COMMENT ON COLUMN public.plazas.codigo IS
'Código único legible de la plaza (ej: JAR-001, SUP-003)';

COMMENT ON COLUMN public.plazas.empleado_id IS
'ID del empleado asignado (null si está vacante). TODO: Agregar FK cuando exista tabla empleados';

COMMENT ON COLUMN public.plazas.salario_mensual IS
'Salario mensual específico de esta plaza';

COMMENT ON COLUMN public.plazas.estatus IS
'Estado: VACANTE, OCUPADA, SUSPENDIDA, CANCELADA';

-- ============================================================================
-- 4. Índices de rendimiento
-- ============================================================================

-- Índice para búsqueda por contrato_categoria_id (muy frecuente)
CREATE INDEX IF NOT EXISTS idx_plazas_contrato_categoria
ON public.plazas USING btree (contrato_categoria_id);

-- Índice para búsqueda por empleado_id
CREATE INDEX IF NOT EXISTS idx_plazas_empleado
ON public.plazas USING btree (empleado_id)
WHERE empleado_id IS NOT NULL;

-- Índice para filtrar por estatus
CREATE INDEX IF NOT EXISTS idx_plazas_estatus
ON public.plazas USING btree (estatus);

-- Índice compuesto para filtros comunes (contrato_categoria + estatus)
CREATE INDEX IF NOT EXISTS idx_plazas_categoria_estatus
ON public.plazas USING btree (contrato_categoria_id, estatus);

-- Índice para ordenamiento por número de plaza
CREATE INDEX IF NOT EXISTS idx_plazas_numero
ON public.plazas USING btree (contrato_categoria_id, numero_plaza);

-- Índice para búsqueda por código (case-insensitive)
CREATE INDEX IF NOT EXISTS idx_plazas_codigo_lower
ON public.plazas USING btree (LOWER(codigo))
WHERE codigo IS NOT NULL AND codigo != '';

-- ============================================================================
-- 5. Trigger para actualizar fecha_actualizacion
-- ============================================================================
CREATE OR REPLACE FUNCTION update_plazas_fecha_actualizacion()
RETURNS TRIGGER AS $$
BEGIN
    NEW.fecha_actualizacion = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_plazas_fecha_actualizacion ON public.plazas;

CREATE TRIGGER trg_plazas_fecha_actualizacion
    BEFORE UPDATE ON public.plazas
    FOR EACH ROW
    EXECUTE FUNCTION update_plazas_fecha_actualizacion();

-- ============================================================================
-- 6. Row Level Security (RLS) - Habilitar si se requiere
-- ============================================================================
-- ALTER TABLE public.plazas ENABLE ROW LEVEL SECURITY;

-- Política para usuarios autenticados
-- CREATE POLICY "Usuarios autenticados pueden ver plazas"
-- ON public.plazas FOR SELECT
-- TO authenticated
-- USING (true);

-- CREATE POLICY "Usuarios autenticados pueden insertar plazas"
-- ON public.plazas FOR INSERT
-- TO authenticated
-- WITH CHECK (true);

-- CREATE POLICY "Usuarios autenticados pueden actualizar plazas"
-- ON public.plazas FOR UPDATE
-- TO authenticated
-- USING (true);

-- ============================================================================
-- Verificación de la migración
-- ============================================================================
-- SELECT
--     column_name,
--     data_type,
--     is_nullable,
--     column_default
-- FROM information_schema.columns
-- WHERE table_name = 'plazas'
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
-- WHERE tablename = 'plazas'
-- ORDER BY indexname;

-- ============================================================================
-- Agregar FK a empleados (ejecutar cuando exista la tabla)
-- ============================================================================
-- ALTER TABLE public.plazas
-- ADD CONSTRAINT fk_plazas_empleado
-- FOREIGN KEY (empleado_id) REFERENCES public.empleados(id);

-- ============================================================================
-- Rollback (si necesitas revertir la migración)
-- ============================================================================
-- DROP TRIGGER IF EXISTS trg_plazas_fecha_actualizacion ON public.plazas;
-- DROP FUNCTION IF EXISTS update_plazas_fecha_actualizacion();
-- DROP TABLE IF EXISTS public.plazas;
-- DROP TYPE IF EXISTS estatus_plaza;
