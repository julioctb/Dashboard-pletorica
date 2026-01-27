-- ============================================================================
-- Migracion 009: Sistema de archivos generico (archivo_sistema)
-- ============================================================================
-- Ejecutar en Supabase SQL Editor
--
-- Crea tabla polimorfica para asociar archivos (imagenes/PDFs) a cualquier
-- entidad del sistema (requisiciones, items, reportes, contratos, etc.)
-- ============================================================================

-- ENUM para tipo de entidad (extensible)
CREATE TYPE entidad_archivo AS ENUM (
    'REQUISICION',
    'REQUISICION_ITEM',
    'REPORTE',
    'REPORTE_ACTIVIDAD',
    'CONTRATO',
    'EMPLEADO'
);

-- ENUM para tipo de archivo
CREATE TYPE tipo_archivo AS ENUM (
    'IMAGEN',
    'FICHA_TECNICA',
    'DOCUMENTO'
);

-- Tabla principal
CREATE TABLE archivo_sistema (
    id SERIAL PRIMARY KEY,

    -- Relacion polimorfica
    entidad_tipo entidad_archivo NOT NULL,
    entidad_id INTEGER NOT NULL,

    -- Datos del archivo
    nombre_original VARCHAR(255) NOT NULL,
    nombre_storage VARCHAR(255) NOT NULL,
    ruta_storage VARCHAR(500) NOT NULL,
    tipo_mime VARCHAR(100) NOT NULL,
    tamanio_bytes INTEGER NOT NULL,
    tipo_archivo tipo_archivo NOT NULL,

    -- Metadata
    descripcion VARCHAR(255),
    orden INTEGER DEFAULT 0,

    -- Compresion (para auditoria)
    tamanio_original_bytes INTEGER,
    fue_comprimido BOOLEAN DEFAULT false,
    formato_original VARCHAR(20),

    -- Origen del archivo
    origen VARCHAR(20) DEFAULT 'WEB',

    -- Auditoria
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by INTEGER,

    -- Constraint de unicidad
    CONSTRAINT uk_archivo_sistema UNIQUE (entidad_tipo, entidad_id, nombre_storage)
);

-- Indices
CREATE INDEX idx_archivo_sistema_entidad ON archivo_sistema(entidad_tipo, entidad_id);
CREATE INDEX idx_archivo_sistema_tipo ON archivo_sistema(tipo_archivo);
CREATE INDEX idx_archivo_sistema_created ON archivo_sistema(created_at);

-- Quitar referencia_visual_url de requisicion_item (reemplazado por archivo_sistema)
ALTER TABLE requisicion_item DROP COLUMN IF EXISTS referencia_visual_url;
