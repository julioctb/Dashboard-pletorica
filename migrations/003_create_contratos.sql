-- ============================================================================
-- Migration: Create Contratos Table
-- Fecha: 2026-01-31
-- Descripción: Crea la tabla de contratos de servicio entre empresas y BUAP.
--              Cada contrato tiene código autogenerado: MAN-JAR-25001
--              Depende de: empresas, tipos_servicio
-- ============================================================================

-- ============================================================================
-- 1. Crear tipos ENUM
-- ============================================================================

-- Tipo de contrato
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'tipo_contrato_enum') THEN
        CREATE TYPE tipo_contrato_enum AS ENUM ('ADQUISICION', 'SERVICIOS');
    END IF;
END $$;

-- Modalidad de adjudicación
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'modalidad_adjudicacion_enum') THEN
        CREATE TYPE modalidad_adjudicacion_enum AS ENUM (
            'INVITACION_3',
            'ADJUDICACION_DIRECTA',
            'LICITACION_PUBLICA'
        );
    END IF;
END $$;

-- Tipo de duración
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'tipo_duracion_enum') THEN
        CREATE TYPE tipo_duracion_enum AS ENUM (
            'TIEMPO_DETERMINADO',
            'TIEMPO_INDEFINIDO',
            'OBRA_DETERMINADA'
        );
    END IF;
END $$;

-- Estatus del contrato
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'estatus_contrato_enum') THEN
        CREATE TYPE estatus_contrato_enum AS ENUM (
            'BORRADOR',
            'ACTIVO',
            'SUSPENDIDO',
            'VENCIDO',
            'CANCELADO',
            'CERRADO'
        );
    END IF;
END $$;

-- ============================================================================
-- 2. Crear tabla de contratos
-- ============================================================================
CREATE TABLE IF NOT EXISTS public.contratos (
    -- Identificación
    id SERIAL PRIMARY KEY,
    empresa_id INTEGER NOT NULL REFERENCES public.empresas(id) ON DELETE RESTRICT,
    tipo_servicio_id INTEGER DEFAULT NULL REFERENCES public.tipos_servicio(id) ON DELETE RESTRICT,

    -- Código único autogenerado
    codigo VARCHAR(20) NOT NULL,

    -- Folio oficial de BUAP
    numero_folio_buap VARCHAR(50) DEFAULT NULL,

    -- Tipo, modalidad y duración
    tipo_contrato tipo_contrato_enum NOT NULL,
    modalidad_adjudicacion modalidad_adjudicacion_enum NOT NULL,
    tipo_duracion tipo_duracion_enum DEFAULT NULL,

    -- Vigencia
    fecha_inicio DATE NOT NULL,
    fecha_fin DATE DEFAULT NULL,

    -- Descripción
    descripcion_objeto TEXT DEFAULT NULL,

    -- Montos
    monto_minimo DECIMAL(15,2) DEFAULT NULL,
    monto_maximo DECIMAL(15,2) DEFAULT NULL,
    incluye_iva BOOLEAN NOT NULL DEFAULT FALSE,

    -- Detalles presupuestarios
    origen_recurso VARCHAR(200) DEFAULT NULL,
    segmento_asignacion VARCHAR(100) DEFAULT NULL,
    sede_campus VARCHAR(200) DEFAULT NULL,

    -- Póliza
    requiere_poliza BOOLEAN NOT NULL DEFAULT FALSE,
    poliza_detalle VARCHAR(200) DEFAULT NULL,

    -- Configuración
    tiene_personal BOOLEAN NOT NULL DEFAULT TRUE,

    -- Estado
    estatus estatus_contrato_enum NOT NULL DEFAULT 'BORRADOR',
    notas TEXT DEFAULT NULL,

    -- Auditoría
    fecha_creacion TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    fecha_actualizacion TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Restricciones de unicidad
    CONSTRAINT uk_contratos_codigo UNIQUE (codigo),

    -- Validaciones de fechas
    CONSTRAINT chk_contratos_fecha_fin CHECK (
        fecha_fin IS NULL OR fecha_fin >= fecha_inicio
    ),

    -- Validaciones de montos
    CONSTRAINT chk_contratos_monto_minimo CHECK (
        monto_minimo IS NULL OR monto_minimo >= 0
    ),
    CONSTRAINT chk_contratos_monto_maximo CHECK (
        monto_maximo IS NULL OR monto_maximo >= 0
    ),
    CONSTRAINT chk_contratos_montos CHECK (
        monto_minimo IS NULL OR monto_maximo IS NULL OR monto_maximo >= monto_minimo
    ),

    -- Validaciones lógicas
    CONSTRAINT chk_contratos_descripcion CHECK (
        descripcion_objeto IS NULL OR LENGTH(TRIM(descripcion_objeto)) <= 2000
    ),
    CONSTRAINT chk_contratos_notas CHECK (
        notas IS NULL OR LENGTH(notas) <= 2000
    )
);

-- ============================================================================
-- 3. Comentarios de documentación
-- ============================================================================
COMMENT ON TABLE public.contratos IS
'Contratos de servicio entre empresas proveedoras y BUAP.
El código se autogenera con formato: [EMPRESA]-[SERVICIO]-[AÑO][CONSECUTIVO]
Ejemplo: MAN-JAR-25001 (Mantiser, Jardinería, 2025, contrato 001)';

COMMENT ON COLUMN public.contratos.empresa_id IS
'FK a la empresa proveedora del servicio';

COMMENT ON COLUMN public.contratos.tipo_servicio_id IS
'FK al tipo de servicio. Requerido para tipo_contrato=SERVICIOS, opcional para ADQUISICION';

COMMENT ON COLUMN public.contratos.codigo IS
'Código único autogenerado: MAN-JAR-25001';

COMMENT ON COLUMN public.contratos.numero_folio_buap IS
'Número de folio oficial asignado por BUAP (opcional)';

COMMENT ON COLUMN public.contratos.tipo_contrato IS
'Tipo: ADQUISICION (compra de bienes) o SERVICIOS (prestación de servicios)';

COMMENT ON COLUMN public.contratos.modalidad_adjudicacion IS
'Modalidad: INVITACION_3, ADJUDICACION_DIRECTA, LICITACION_PUBLICA';

COMMENT ON COLUMN public.contratos.tipo_duracion IS
'Duración: TIEMPO_DETERMINADO (con fecha_fin), TIEMPO_INDEFINIDO, OBRA_DETERMINADA';

COMMENT ON COLUMN public.contratos.fecha_inicio IS
'Fecha de inicio de vigencia del contrato';

COMMENT ON COLUMN public.contratos.fecha_fin IS
'Fecha de fin de vigencia (NULL si es indefinido)';

COMMENT ON COLUMN public.contratos.monto_minimo IS
'Monto mínimo comprometido en el contrato';

COMMENT ON COLUMN public.contratos.monto_maximo IS
'Monto máximo autorizado en el contrato';

COMMENT ON COLUMN public.contratos.incluye_iva IS
'TRUE si los montos incluyen IVA, FALSE si son antes de IVA';

COMMENT ON COLUMN public.contratos.tiene_personal IS
'TRUE si el contrato incluye asignación de personal (plazas)';

COMMENT ON COLUMN public.contratos.estatus IS
'Estado del contrato: BORRADOR, ACTIVO, SUSPENDIDO, VENCIDO, CANCELADO, CERRADO';

-- ============================================================================
-- 4. Índices de rendimiento
-- ============================================================================

-- Índice único para código
CREATE UNIQUE INDEX IF NOT EXISTS idx_contratos_codigo
ON public.contratos (codigo);

-- Índices para FKs (joins frecuentes)
CREATE INDEX IF NOT EXISTS idx_contratos_empresa_id
ON public.contratos (empresa_id);

CREATE INDEX IF NOT EXISTS idx_contratos_tipo_servicio_id
ON public.contratos (tipo_servicio_id);

-- Índices para filtros
CREATE INDEX IF NOT EXISTS idx_contratos_estatus
ON public.contratos (estatus);

CREATE INDEX IF NOT EXISTS idx_contratos_tipo_estatus
ON public.contratos (tipo_contrato, estatus);

CREATE INDEX IF NOT EXISTS idx_contratos_empresa_estatus
ON public.contratos (empresa_id, estatus);

-- Índice para búsqueda por vigencia
CREATE INDEX IF NOT EXISTS idx_contratos_vigencia
ON public.contratos (fecha_inicio, fecha_fin);

-- Índice para ordenamiento por fecha
CREATE INDEX IF NOT EXISTS idx_contratos_fecha_creacion
ON public.contratos USING btree (fecha_creacion DESC);

-- Índice para búsqueda por folio BUAP
CREATE INDEX IF NOT EXISTS idx_contratos_folio_buap
ON public.contratos (numero_folio_buap) WHERE numero_folio_buap IS NOT NULL;

-- ============================================================================
-- 5. Trigger para actualizar fecha_actualizacion
-- ============================================================================
CREATE OR REPLACE FUNCTION update_contratos_fecha_actualizacion()
RETURNS TRIGGER AS $$
BEGIN
    NEW.fecha_actualizacion = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_contratos_fecha_actualizacion ON public.contratos;

CREATE TRIGGER trg_contratos_fecha_actualizacion
    BEFORE UPDATE ON public.contratos
    FOR EACH ROW
    EXECUTE FUNCTION update_contratos_fecha_actualizacion();

-- ============================================================================
-- Verificación de la migración
-- ============================================================================
-- SELECT
--     column_name,
--     data_type,
--     is_nullable,
--     column_default
-- FROM information_schema.columns
-- WHERE table_name = 'contratos'
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
-- WHERE tablename = 'contratos'
-- ORDER BY indexname;

-- ============================================================================
-- Ejemplo de datos de prueba
-- ============================================================================
-- INSERT INTO public.contratos (
--     empresa_id, tipo_servicio_id, codigo, tipo_contrato,
--     modalidad_adjudicacion, tipo_duracion,
--     fecha_inicio, fecha_fin, descripcion_objeto,
--     monto_minimo, monto_maximo, estatus
-- ) VALUES (
--     1, 1, 'MAN-JAR-25001', 'SERVICIOS',
--     'INVITACION_3', 'TIEMPO_DETERMINADO',
--     '2025-01-01', '2025-12-31', 'Servicios de jardinería para campus',
--     500000.00, 750000.00, 'ACTIVO'
-- );

-- ============================================================================
-- Rollback (si necesitas revertir la migración)
-- ============================================================================
-- DROP TRIGGER IF EXISTS trg_contratos_fecha_actualizacion ON public.contratos;
-- DROP FUNCTION IF EXISTS update_contratos_fecha_actualizacion();
-- DROP TABLE IF EXISTS public.contratos CASCADE;
-- DROP TYPE IF EXISTS estatus_contrato_enum;
-- DROP TYPE IF EXISTS tipo_duracion_enum;
-- DROP TYPE IF EXISTS modalidad_adjudicacion_enum;
-- DROP TYPE IF EXISTS tipo_contrato_enum;
