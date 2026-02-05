-- ============================================================================
-- Migration: Create Empresas Table
-- Fecha: 2026-01-31
-- Descripción: Crea la tabla base de empresas (proveedores de servicios a BUAP).
--              Esta es la tabla fundamental del sistema - todas las demás dependen de ella.
-- ============================================================================

-- ============================================================================
-- 1. Crear tipos ENUM
-- ============================================================================

-- Tipo de empresa
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'tipo_empresa_enum') THEN
        CREATE TYPE tipo_empresa_enum AS ENUM ('NOMINA', 'MANTENIMIENTO');
    END IF;
END $$;

-- Estatus de empresa
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'estatus_empresa_enum') THEN
        CREATE TYPE estatus_empresa_enum AS ENUM ('ACTIVO', 'INACTIVO', 'SUSPENDIDO');
    END IF;
END $$;

-- ============================================================================
-- 2. Crear tabla de empresas
-- ============================================================================
CREATE TABLE IF NOT EXISTS public.empresas (
    -- Identificación
    id SERIAL PRIMARY KEY,
    nombre_comercial VARCHAR(100) NOT NULL,
    razon_social VARCHAR(100) NOT NULL,
    tipo_empresa tipo_empresa_enum NOT NULL,
    rfc VARCHAR(13) NOT NULL,

    -- Contacto
    direccion VARCHAR(200) DEFAULT NULL,
    codigo_postal VARCHAR(5) DEFAULT NULL,
    telefono VARCHAR(15) DEFAULT NULL,
    email VARCHAR(100) DEFAULT NULL,
    pagina_web VARCHAR(100) DEFAULT NULL,

    -- Datos fiscales/IMSS
    registro_patronal VARCHAR(15) DEFAULT NULL,
    prima_riesgo DECIMAL(7,5) DEFAULT NULL,

    -- Código corto (autogenerado)
    codigo_corto VARCHAR(3) DEFAULT NULL,

    -- Estado
    estatus estatus_empresa_enum NOT NULL DEFAULT 'ACTIVO',
    notas TEXT DEFAULT NULL,

    -- Auditoría
    fecha_creacion TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    fecha_actualizacion TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Restricciones de unicidad
    CONSTRAINT uk_empresas_rfc UNIQUE (rfc),
    CONSTRAINT uk_empresas_codigo_corto UNIQUE (codigo_corto),

    -- Validaciones
    CONSTRAINT chk_empresas_nombre_comercial CHECK (LENGTH(TRIM(nombre_comercial)) >= 2),
    CONSTRAINT chk_empresas_razon_social CHECK (LENGTH(TRIM(razon_social)) >= 2),
    CONSTRAINT chk_empresas_rfc_formato CHECK (
        rfc ~ '^[A-Z&Ñ]{3,4}[0-9]{6}[A-V1-9][A-Z1-9][0-9A]$'
    ),
    CONSTRAINT chk_empresas_codigo_postal CHECK (
        codigo_postal IS NULL OR codigo_postal ~ '^[0-9]{5}$'
    ),
    CONSTRAINT chk_empresas_telefono CHECK (
        telefono IS NULL OR (LENGTH(REGEXP_REPLACE(telefono, '[^0-9]', '', 'g')) = 10)
    ),
    CONSTRAINT chk_empresas_prima_riesgo CHECK (
        prima_riesgo IS NULL OR (prima_riesgo >= 0.005 AND prima_riesgo <= 0.15)
    ),
    CONSTRAINT chk_empresas_codigo_corto CHECK (
        codigo_corto IS NULL OR (LENGTH(codigo_corto) = 3 AND codigo_corto ~ '^[A-Z0-9]{3}$')
    ),
    CONSTRAINT chk_empresas_notas CHECK (
        notas IS NULL OR LENGTH(notas) <= 1000
    )
);

-- ============================================================================
-- 3. Comentarios de documentación
-- ============================================================================
COMMENT ON TABLE public.empresas IS
'Empresas proveedoras de servicios a BUAP (nómina, mantenimiento, suministros).
Tabla base del sistema - contratos, empleados y plazas dependen de ella.
El código_corto (3 letras) se usa en códigos de contrato: MAN-JAR-25001';

COMMENT ON COLUMN public.empresas.nombre_comercial IS
'Nombre comercial de la empresa (ej: "Mantiser")';

COMMENT ON COLUMN public.empresas.razon_social IS
'Razón social completa (ej: "Mantiser SA de CV")';

COMMENT ON COLUMN public.empresas.tipo_empresa IS
'Tipo de empresa: NOMINA (empleados), MANTENIMIENTO (servicios)';

COMMENT ON COLUMN public.empresas.rfc IS
'RFC de la empresa (12 o 13 caracteres). Único en el sistema.';

COMMENT ON COLUMN public.empresas.registro_patronal IS
'Registro patronal IMSS formateado (14 chars con guiones)';

COMMENT ON COLUMN public.empresas.prima_riesgo IS
'Prima de riesgo IMSS (0.5% a 15%, formato decimal: 0.00525 = 0.525%)';

COMMENT ON COLUMN public.empresas.codigo_corto IS
'Código único de 3 letras/números (autogenerado). Usado en códigos de contrato.';

-- ============================================================================
-- 4. Índices de rendimiento
-- ============================================================================

-- Índices únicos (ya cubiertos por UNIQUE constraints, pero explícitos para claridad)
CREATE UNIQUE INDEX IF NOT EXISTS idx_empresas_rfc
ON public.empresas (rfc);

CREATE UNIQUE INDEX IF NOT EXISTS idx_empresas_codigo_corto
ON public.empresas (codigo_corto) WHERE codigo_corto IS NOT NULL;

-- Índices para búsqueda case-insensitive (ilike)
CREATE INDEX IF NOT EXISTS idx_empresas_nombre_comercial_lower
ON public.empresas USING btree (LOWER(nombre_comercial));

CREATE INDEX IF NOT EXISTS idx_empresas_razon_social_lower
ON public.empresas USING btree (LOWER(razon_social));

-- Índice compuesto para filtros combinados
CREATE INDEX IF NOT EXISTS idx_empresas_tipo_estatus
ON public.empresas USING btree (tipo_empresa, estatus);

-- Índice para ordenamiento por fecha (más recientes primero)
CREATE INDEX IF NOT EXISTS idx_empresas_fecha_creacion
ON public.empresas USING btree (fecha_creacion DESC);

-- ============================================================================
-- 5. Trigger para actualizar fecha_actualizacion
-- ============================================================================
CREATE OR REPLACE FUNCTION update_empresas_fecha_actualizacion()
RETURNS TRIGGER AS $$
BEGIN
    NEW.fecha_actualizacion = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_empresas_fecha_actualizacion ON public.empresas;

CREATE TRIGGER trg_empresas_fecha_actualizacion
    BEFORE UPDATE ON public.empresas
    FOR EACH ROW
    EXECUTE FUNCTION update_empresas_fecha_actualizacion();

-- ============================================================================
-- 6. Row Level Security (RLS) - Opcional
-- ============================================================================
-- ALTER TABLE public.empresas ENABLE ROW LEVEL SECURITY;

-- Política para usuarios autenticados
-- CREATE POLICY "Usuarios autenticados pueden ver empresas"
-- ON public.empresas FOR SELECT
-- TO authenticated
-- USING (true);

-- CREATE POLICY "Usuarios autenticados pueden insertar empresas"
-- ON public.empresas FOR INSERT
-- TO authenticated
-- WITH CHECK (true);

-- CREATE POLICY "Usuarios autenticados pueden actualizar empresas"
-- ON public.empresas FOR UPDATE
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
-- WHERE table_name = 'empresas'
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
-- WHERE tablename = 'empresas'
-- ORDER BY indexname;

-- ============================================================================
-- Ejemplo de datos de prueba
-- ============================================================================
-- INSERT INTO public.empresas (
--     nombre_comercial, razon_social, tipo_empresa, rfc,
--     codigo_corto, prima_riesgo
-- ) VALUES (
--     'Mantiser', 'Mantiser SA de CV', 'MANTENIMIENTO', 'MAN010101ABC',
--     'MAN', 0.00525
-- );

-- ============================================================================
-- Rollback (si necesitas revertir la migración)
-- ============================================================================
-- DROP TRIGGER IF EXISTS trg_empresas_fecha_actualizacion ON public.empresas;
-- DROP FUNCTION IF EXISTS update_empresas_fecha_actualizacion();
-- DROP TABLE IF EXISTS public.empresas CASCADE;
-- DROP TYPE IF EXISTS estatus_empresa_enum;
-- DROP TYPE IF EXISTS tipo_empresa_enum;
