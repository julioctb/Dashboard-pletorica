-- ============================================================================
-- Migration: Create Pagos Table
-- Fecha: 2026-01-31
-- Descripción: Crea la tabla de pagos asociados a contratos.
--              Registra los pagos realizados a empresas proveedoras.
--              Depende de: contratos
-- ============================================================================

-- ============================================================================
-- 1. Crear tabla de pagos
-- ============================================================================
CREATE TABLE IF NOT EXISTS public.pagos (
    -- Identificación
    id SERIAL PRIMARY KEY,
    contrato_id INTEGER NOT NULL REFERENCES public.contratos(id) ON DELETE RESTRICT,

    -- Datos del pago
    fecha_pago DATE NOT NULL,
    monto DECIMAL(15,2) NOT NULL,
    concepto VARCHAR(500) NOT NULL,

    -- Referencias documentales
    numero_factura VARCHAR(50) DEFAULT NULL,
    comprobante VARCHAR(200) DEFAULT NULL,

    -- Notas
    notas VARCHAR(1000) DEFAULT NULL,

    -- Auditoría
    fecha_creacion TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    fecha_actualizacion TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Validaciones
    CONSTRAINT chk_pagos_monto CHECK (monto >= 0),
    CONSTRAINT chk_pagos_concepto CHECK (
        concepto IS NOT NULL AND LENGTH(TRIM(concepto)) > 0
    )
);

-- ============================================================================
-- 2. Comentarios de documentación
-- ============================================================================
COMMENT ON TABLE public.pagos IS
'Pagos realizados a empresas proveedoras por contratos de servicio.
Permite llevar control del monto total pagado vs monto contratado.';

COMMENT ON COLUMN public.pagos.contrato_id IS
'FK al contrato asociado a este pago';

COMMENT ON COLUMN public.pagos.fecha_pago IS
'Fecha en que se realizó el pago';

COMMENT ON COLUMN public.pagos.monto IS
'Monto del pago (debe ser >= 0)';

COMMENT ON COLUMN public.pagos.concepto IS
'Concepto o descripción del pago (1-500 caracteres, requerido)';

COMMENT ON COLUMN public.pagos.numero_factura IS
'Número de factura asociada al pago (opcional)';

COMMENT ON COLUMN public.pagos.comprobante IS
'Referencia o URL del comprobante de pago (opcional)';

-- ============================================================================
-- 3. Índices de rendimiento
-- ============================================================================

-- Índice para FK (joins frecuentes con contratos)
CREATE INDEX IF NOT EXISTS idx_pagos_contrato_id
ON public.pagos (contrato_id);

-- Índice para búsqueda por fecha
CREATE INDEX IF NOT EXISTS idx_pagos_fecha_pago
ON public.pagos (fecha_pago DESC);

-- Índice compuesto para filtros comunes (contrato + fecha)
CREATE INDEX IF NOT EXISTS idx_pagos_contrato_fecha
ON public.pagos (contrato_id, fecha_pago DESC);

-- Índice para búsqueda por factura
CREATE INDEX IF NOT EXISTS idx_pagos_numero_factura
ON public.pagos (numero_factura) WHERE numero_factura IS NOT NULL;

-- Índice para ordenamiento por fecha de creación
CREATE INDEX IF NOT EXISTS idx_pagos_fecha_creacion
ON public.pagos USING btree (fecha_creacion DESC);

-- ============================================================================
-- 4. Trigger para actualizar fecha_actualizacion
-- ============================================================================
CREATE OR REPLACE FUNCTION update_pagos_fecha_actualizacion()
RETURNS TRIGGER AS $$
BEGIN
    NEW.fecha_actualizacion = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_pagos_fecha_actualizacion ON public.pagos;

CREATE TRIGGER trg_pagos_fecha_actualizacion
    BEFORE UPDATE ON public.pagos
    FOR EACH ROW
    EXECUTE FUNCTION update_pagos_fecha_actualizacion();

-- ============================================================================
-- Verificación de la migración
-- ============================================================================
-- SELECT
--     column_name,
--     data_type,
--     is_nullable,
--     column_default
-- FROM information_schema.columns
-- WHERE table_name = 'pagos'
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
-- WHERE tablename = 'pagos'
-- ORDER BY indexname;

-- ============================================================================
-- Consulta útil: Total pagado por contrato
-- ============================================================================
-- SELECT
--     c.codigo AS contrato,
--     c.monto_maximo,
--     COALESCE(SUM(p.monto), 0) AS total_pagado,
--     c.monto_maximo - COALESCE(SUM(p.monto), 0) AS saldo_disponible
-- FROM public.contratos c
-- LEFT JOIN public.pagos p ON c.id = p.contrato_id
-- WHERE c.estatus = 'ACTIVO'
-- GROUP BY c.id, c.codigo, c.monto_maximo
-- ORDER BY c.codigo;

-- ============================================================================
-- Ejemplo de datos de prueba
-- ============================================================================
-- INSERT INTO public.pagos (
--     contrato_id, fecha_pago, monto, concepto, numero_factura
-- ) VALUES (
--     1, '2025-01-15', 125000.00, 'Pago mensual enero 2025', 'F-2025-001'
-- );

-- ============================================================================
-- Rollback (si necesitas revertir la migración)
-- ============================================================================
-- DROP TRIGGER IF EXISTS trg_pagos_fecha_actualizacion ON public.pagos;
-- DROP FUNCTION IF EXISTS update_pagos_fecha_actualizacion();
-- DROP TABLE IF EXISTS public.pagos CASCADE;
