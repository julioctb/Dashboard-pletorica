-- ============================================================================
-- Migration: Create Empleados Table
-- Fecha: 2025-01-21
-- Descripción: Crea la tabla de empleados para gestionar trabajadores de los
--              proveedores que prestan servicios a BUAP.
--              El CURP es el identificador único real (gobierno mexicano).
--              La clave (B25-00001) es para uso operativo interno.
-- ============================================================================

-- ============================================================================
-- 1. Crear tipos ENUM
-- ============================================================================

-- Estatus de empleado
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'estatus_empleado') THEN
        CREATE TYPE estatus_empleado AS ENUM (
            'ACTIVO',
            'INACTIVO',
            'SUSPENDIDO'
        );
    END IF;
END $$;

-- Género del empleado
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'genero_empleado') THEN
        CREATE TYPE genero_empleado AS ENUM (
            'MASCULINO',
            'FEMENINO'
        );
    END IF;
END $$;

-- Motivo de baja
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'motivo_baja') THEN
        CREATE TYPE motivo_baja AS ENUM (
            'RENUNCIA',
            'DESPIDO',
            'FIN_CONTRATO',
            'JUBILACION',
            'FALLECIMIENTO',
            'OTRO'
        );
    END IF;
END $$;

-- ============================================================================
-- 2. Crear tabla de empleados
-- ============================================================================
CREATE TABLE IF NOT EXISTS public.empleados (
    -- Identificación interna
    id SERIAL PRIMARY KEY,
    clave VARCHAR(10) NOT NULL,
    empresa_id INTEGER NOT NULL REFERENCES public.empresas(id) ON DELETE RESTRICT,

    -- Identificación oficial (gobierno mexicano)
    curp VARCHAR(18) NOT NULL,
    rfc VARCHAR(13) DEFAULT NULL,
    nss VARCHAR(11) DEFAULT NULL,

    -- Datos personales
    nombre VARCHAR(100) NOT NULL,
    apellido_paterno VARCHAR(100) NOT NULL,
    apellido_materno VARCHAR(100) DEFAULT NULL,
    fecha_nacimiento DATE DEFAULT NULL,
    genero genero_empleado DEFAULT NULL,

    -- Contacto
    telefono VARCHAR(10) DEFAULT NULL,
    email VARCHAR(100) DEFAULT NULL,
    direccion TEXT DEFAULT NULL,
    contacto_emergencia VARCHAR(200) DEFAULT NULL,

    -- Estado laboral
    estatus estatus_empleado NOT NULL DEFAULT 'ACTIVO',
    fecha_ingreso DATE NOT NULL DEFAULT CURRENT_DATE,
    fecha_baja DATE DEFAULT NULL,
    motivo_baja motivo_baja DEFAULT NULL,

    -- Notas
    notas TEXT DEFAULT NULL,

    -- Auditoría
    fecha_creacion TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    fecha_actualizacion TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Restricciones de unicidad
    CONSTRAINT uk_empleados_clave UNIQUE (clave),
    CONSTRAINT uk_empleados_curp UNIQUE (curp),

    -- Validaciones
    CONSTRAINT chk_empleados_fechas CHECK (
        fecha_baja IS NULL OR fecha_baja >= fecha_ingreso
    ),
    CONSTRAINT chk_empleados_curp_formato CHECK (
        curp ~ '^[A-Z]{4}[0-9]{6}[HM][A-Z]{5}[0-9A-Z][0-9]$'
    ),
    CONSTRAINT chk_empleados_clave_formato CHECK (
        clave ~ '^B[0-9]{2}-[0-9]{5}$'
    )
);

-- ============================================================================
-- 3. Comentarios de documentación
-- ============================================================================
COMMENT ON TABLE public.empleados IS
'Trabajadores de proveedores que prestan servicios a BUAP.
El CURP es el identificador único real (gobierno mexicano).
La clave (B25-00001) es para uso operativo interno y nunca cambia.
El empleado puede cambiar de empresa (proveedor) manteniendo su clave e historial.';

COMMENT ON COLUMN public.empleados.clave IS
'Clave permanente única del empleado: B25-00001 (B + año + consecutivo)';

COMMENT ON COLUMN public.empleados.empresa_id IS
'FK a empresas - proveedor actual del empleado (puede cambiar)';

COMMENT ON COLUMN public.empleados.curp IS
'CURP - Clave Única de Registro de Población. Identificador único del gobierno mexicano. 18 caracteres.';

COMMENT ON COLUMN public.empleados.rfc IS
'RFC persona física. 13 caracteres.';

COMMENT ON COLUMN public.empleados.nss IS
'Número de Seguro Social IMSS. 11 dígitos.';

COMMENT ON COLUMN public.empleados.fecha_ingreso IS
'Fecha de ingreso al sistema (no necesariamente a la empresa actual)';

COMMENT ON COLUMN public.empleados.fecha_baja IS
'Fecha de baja del sistema (solo si estatus = INACTIVO)';

COMMENT ON COLUMN public.empleados.motivo_baja IS
'Motivo de la baja: RENUNCIA, DESPIDO, FIN_CONTRATO, JUBILACION, FALLECIMIENTO, OTRO';

-- ============================================================================
-- 4. Índices de rendimiento
-- ============================================================================

-- Índice para búsqueda por empresa (muy frecuente)
CREATE INDEX IF NOT EXISTS idx_empleados_empresa
ON public.empleados USING btree (empresa_id);

-- Índice para búsqueda por CURP (único, búsqueda exacta)
CREATE INDEX IF NOT EXISTS idx_empleados_curp
ON public.empleados USING btree (curp);

-- Índice para búsqueda por clave
CREATE INDEX IF NOT EXISTS idx_empleados_clave
ON public.empleados USING btree (clave);

-- Índice para filtrar por estatus
CREATE INDEX IF NOT EXISTS idx_empleados_estatus
ON public.empleados USING btree (estatus);

-- Índice compuesto para filtros comunes (empresa + estatus)
CREATE INDEX IF NOT EXISTS idx_empleados_empresa_estatus
ON public.empleados USING btree (empresa_id, estatus);

-- Índice para ordenamiento por nombre (apellidos primero)
CREATE INDEX IF NOT EXISTS idx_empleados_nombre
ON public.empleados USING btree (apellido_paterno, apellido_materno, nombre);

-- Índice para búsqueda por texto en nombre (case-insensitive)
CREATE INDEX IF NOT EXISTS idx_empleados_nombre_lower
ON public.empleados USING btree (LOWER(nombre));

CREATE INDEX IF NOT EXISTS idx_empleados_apellido_paterno_lower
ON public.empleados USING btree (LOWER(apellido_paterno));

-- Índice para búsqueda por año de clave (para generar consecutivos)
CREATE INDEX IF NOT EXISTS idx_empleados_clave_pattern
ON public.empleados USING btree (clave text_pattern_ops);

-- ============================================================================
-- 5. Trigger para actualizar fecha_actualizacion
-- ============================================================================
CREATE OR REPLACE FUNCTION update_empleados_fecha_actualizacion()
RETURNS TRIGGER AS $$
BEGIN
    NEW.fecha_actualizacion = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_empleados_fecha_actualizacion ON public.empleados;

CREATE TRIGGER trg_empleados_fecha_actualizacion
    BEFORE UPDATE ON public.empleados
    FOR EACH ROW
    EXECUTE FUNCTION update_empleados_fecha_actualizacion();

-- ============================================================================
-- 6. Agregar FK a tabla plazas (si existe)
-- ============================================================================
-- Actualizar la tabla plazas para agregar la FK a empleados
DO $$
BEGIN
    -- Verificar si la columna empleado_id existe en plazas
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'plazas' AND column_name = 'empleado_id'
    ) THEN
        -- Verificar si la FK ya existe
        IF NOT EXISTS (
            SELECT 1 FROM information_schema.table_constraints
            WHERE constraint_name = 'fk_plazas_empleado' AND table_name = 'plazas'
        ) THEN
            ALTER TABLE public.plazas
            ADD CONSTRAINT fk_plazas_empleado
            FOREIGN KEY (empleado_id) REFERENCES public.empleados(id);

            RAISE NOTICE 'FK fk_plazas_empleado agregada a tabla plazas';
        END IF;
    END IF;
END $$;

-- ============================================================================
-- 7. Row Level Security (RLS) - Habilitar si se requiere
-- ============================================================================
-- ALTER TABLE public.empleados ENABLE ROW LEVEL SECURITY;

-- Política para usuarios autenticados
-- CREATE POLICY "Usuarios autenticados pueden ver empleados"
-- ON public.empleados FOR SELECT
-- TO authenticated
-- USING (true);

-- CREATE POLICY "Usuarios autenticados pueden insertar empleados"
-- ON public.empleados FOR INSERT
-- TO authenticated
-- WITH CHECK (true);

-- CREATE POLICY "Usuarios autenticados pueden actualizar empleados"
-- ON public.empleados FOR UPDATE
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
-- WHERE table_name = 'empleados'
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
-- WHERE tablename = 'empleados'
-- ORDER BY indexname;

-- ============================================================================
-- Ejemplo de datos de prueba
-- ============================================================================
-- INSERT INTO public.empleados (
--     clave, empresa_id, curp, nombre, apellido_paterno, apellido_materno,
--     fecha_nacimiento, genero, fecha_ingreso
-- ) VALUES (
--     'B25-00001', 1, 'PEGJ850101HPLRNN09', 'JUAN', 'PÉREZ', 'GARCÍA',
--     '1985-01-01', 'MASCULINO', '2025-01-15'
-- );

-- ============================================================================
-- Rollback (si necesitas revertir la migración)
-- ============================================================================
-- ALTER TABLE public.plazas DROP CONSTRAINT IF EXISTS fk_plazas_empleado;
-- DROP TRIGGER IF EXISTS trg_empleados_fecha_actualizacion ON public.empleados;
-- DROP FUNCTION IF EXISTS update_empleados_fecha_actualizacion();
-- DROP TABLE IF EXISTS public.empleados;
-- DROP TYPE IF EXISTS motivo_baja;
-- DROP TYPE IF EXISTS genero_empleado;
-- DROP TYPE IF EXISTS estatus_empleado;
