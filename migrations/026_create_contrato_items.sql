-- ============================================================================
-- Migration: Create contrato_item Table
-- Fecha: 2026-02-06
-- Descripcion: Items de contrato con precios requeridos, copiados desde
--              requisicion con cantidades ajustables.
--              ContratoCategoria sigue para contratos SERVICIOS (personal).
--              contrato_item es para ADQUISICION (bienes).
-- ============================================================================

-- 1. Crear tabla
CREATE TABLE IF NOT EXISTS contrato_item (
    id SERIAL PRIMARY KEY,
    contrato_id INTEGER NOT NULL REFERENCES contratos(id) ON DELETE CASCADE,
    requisicion_item_id INTEGER REFERENCES requisicion_item(id),
    numero_item INTEGER NOT NULL DEFAULT 1,
    unidad_medida VARCHAR(50) NOT NULL DEFAULT 'Pieza',
    cantidad DECIMAL(12, 4) NOT NULL DEFAULT 1,
    descripcion TEXT NOT NULL,
    precio_unitario DECIMAL(14, 2) NOT NULL,
    subtotal DECIMAL(14, 2) NOT NULL,
    especificaciones_tecnicas TEXT,
    notas TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Constraints
    CONSTRAINT chk_contrato_item_precio CHECK (precio_unitario >= 0),
    CONSTRAINT chk_contrato_item_cantidad CHECK (cantidad > 0),
    CONSTRAINT chk_contrato_item_subtotal CHECK (subtotal >= 0)
);

-- 2. Indices
CREATE INDEX IF NOT EXISTS idx_contrato_item_contrato
ON contrato_item(contrato_id);

CREATE INDEX IF NOT EXISTS idx_contrato_item_requisicion_item
ON contrato_item(requisicion_item_id);

-- 3. Trigger para actualizar subtotal automaticamente
CREATE OR REPLACE FUNCTION calcular_subtotal_contrato_item()
RETURNS TRIGGER AS $$
BEGIN
    NEW.subtotal = NEW.cantidad * NEW.precio_unitario;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_contrato_item_subtotal
    BEFORE INSERT OR UPDATE ON contrato_item
    FOR EACH ROW
    EXECUTE FUNCTION calcular_subtotal_contrato_item();

-- 4. Comentarios de documentacion
COMMENT ON TABLE contrato_item IS
    'Items de contrato con precios requeridos. Para contratos de ADQUISICION. '
    'Los items pueden copiarse de requisicion_item con cantidades/precios ajustables.';

COMMENT ON COLUMN contrato_item.requisicion_item_id IS
    'FK al item de requisicion origen. NULL si el item fue creado directamente en el contrato.';

COMMENT ON COLUMN contrato_item.precio_unitario IS
    'Precio unitario del item. Requerido (a diferencia de requisicion donde es estimado/opcional).';

-- ============================================================================
-- Rollback (if you need to revert)
-- ============================================================================
-- DROP TRIGGER IF EXISTS trg_contrato_item_subtotal ON contrato_item;
-- DROP FUNCTION IF EXISTS calcular_subtotal_contrato_item();
-- DROP TABLE IF EXISTS contrato_item;
