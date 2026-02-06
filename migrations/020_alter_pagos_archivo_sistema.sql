-- ============================================================================
-- Migration: Alter Pagos & Archivo Sistema for Entregables
-- Fecha: 2026-02-05
-- Descripción: Modifica tablas existentes para soportar el flujo de entregables.
--              - pagos: Agrega estatus y relación con entregable
--              - archivo_sistema: Agrega campo categoria para distinguir propósito
-- Depende de: 017_create_entregables_tables.sql (ENUMs ya creados)
-- ============================================================================

-- ============================================================================
-- 1. MODIFICAR TABLA: pagos
-- ============================================================================
-- Agregar estatus del pago y relación opcional con entregable.
-- Los registros existentes tendrán estatus = 'PAGADO' (default) y entregable_id = NULL.

-- Agregar columna estatus (con default para registros existentes)
ALTER TABLE public.pagos 
ADD COLUMN IF NOT EXISTS estatus estatus_pago NOT NULL DEFAULT 'PAGADO';

-- Agregar columna entregable_id (nullable para pagos manuales/históricos)
ALTER TABLE public.pagos 
ADD COLUMN IF NOT EXISTS entregable_id INTEGER;

-- FK a entregables (se crea solo si la columna no tenía FK)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE constraint_name = 'fk_pagos_entregable'
    ) THEN
        ALTER TABLE public.pagos 
        ADD CONSTRAINT fk_pagos_entregable 
        FOREIGN KEY (entregable_id) 
        REFERENCES public.entregables(id) 
        ON DELETE SET NULL;
    END IF;
END $$;

-- Índice para buscar pagos por entregable
CREATE INDEX IF NOT EXISTS idx_pagos_entregable
ON public.pagos (entregable_id)
WHERE entregable_id IS NOT NULL;

-- Índice para buscar pagos por estatus
CREATE INDEX IF NOT EXISTS idx_pagos_estatus
ON public.pagos (estatus);

-- Comentarios
COMMENT ON COLUMN public.pagos.estatus IS
'Estado del pago: PENDIENTE (esperando factura), EN_PROCESO (factura subida), PAGADO';

COMMENT ON COLUMN public.pagos.entregable_id IS
'FK al entregable que originó este pago. NULL para pagos manuales o históricos';


-- ============================================================================
-- 2. MODIFICAR TABLA: archivo_sistema
-- ============================================================================
-- Agregar campo categoria para distinguir el propósito de negocio del archivo.
-- Valores: FOTOGRAFICO, REPORTE, LISTADO, DOCUMENTAL, FACTURA_PDF, FACTURA_XML

ALTER TABLE public.archivo_sistema 
ADD COLUMN IF NOT EXISTS categoria VARCHAR(50);

-- Índice para filtrar por categoria
CREATE INDEX IF NOT EXISTS idx_archivo_categoria
ON public.archivo_sistema (categoria)
WHERE categoria IS NOT NULL;

-- Comentario
COMMENT ON COLUMN public.archivo_sistema.categoria IS
'Categoría de negocio del archivo:
- FOTOGRAFICO: Evidencia fotográfica (entregables)
- REPORTE: Reportes de actividades (entregables)
- LISTADO: Listado de personal CSV/XLS (entregables)
- DOCUMENTAL: Documentos oficiales (entregables)
- FACTURA_PDF: Factura en PDF (pagos)
- FACTURA_XML: CFDI XML (pagos)
NULL para archivos sin categoría específica';


-- ============================================================================
-- 3. ACTUALIZAR ENUM EntidadArchivo (si es necesario)
-- ============================================================================
-- Nota: En PostgreSQL no se puede agregar valores a un ENUM directamente en
-- versiones anteriores a 9.1. Usamos la sintaxis segura con ALTER TYPE.

-- Agregar ENTREGABLE al enum entidad_archivo (si no existe)
DO $$
BEGIN
    -- Verificar si el valor ya existe
    IF NOT EXISTS (
        SELECT 1 FROM pg_enum 
        WHERE enumlabel = 'ENTREGABLE' 
        AND enumtypid = (SELECT oid FROM pg_type WHERE typname = 'entidad_archivo')
    ) THEN
        ALTER TYPE entidad_archivo ADD VALUE IF NOT EXISTS 'ENTREGABLE';
    END IF;
EXCEPTION
    WHEN others THEN
        -- Si falla, probablemente el tipo no existe o ya tiene el valor
        NULL;
END $$;

-- Agregar PAGO al enum entidad_archivo (si no existe)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_enum 
        WHERE enumlabel = 'PAGO' 
        AND enumtypid = (SELECT oid FROM pg_type WHERE typname = 'entidad_archivo')
    ) THEN
        ALTER TYPE entidad_archivo ADD VALUE IF NOT EXISTS 'PAGO';
    END IF;
EXCEPTION
    WHEN others THEN
        NULL;
END $$;


-- ============================================================================
-- 4. FIN DE MIGRACIÓN
-- ============================================================================
