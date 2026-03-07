-- =============================================================================
-- Migración 047: Rediseño del módulo Cotizador
-- Soporta dos tipos de cotización: PRODUCTOS_SERVICIOS y PERSONAL
-- Agrega tabla cotizacion_items para items en 3 niveles (perfil, partida, global)
-- =============================================================================

-- 1. Crear enums nuevos
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'tipo_cotizacion_enum') THEN
        CREATE TYPE tipo_cotizacion_enum AS ENUM ('PRODUCTOS_SERVICIOS', 'PERSONAL');
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'tipo_sueldo_enum') THEN
        CREATE TYPE tipo_sueldo_enum AS ENUM ('NETO', 'BRUTO');
    END IF;
END$$;

-- 2. Alterar tabla cotizaciones
ALTER TABLE cotizaciones
    ADD COLUMN IF NOT EXISTS tipo tipo_cotizacion_enum NOT NULL DEFAULT 'PERSONAL',
    ADD COLUMN IF NOT EXISTS aplicar_iva BOOLEAN DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS cantidad_meses INTEGER DEFAULT 1 CHECK (cantidad_meses >= 1);

-- Fechas de período se vuelven opcionales (se usan al convertir a contrato)
ALTER TABLE cotizaciones
    ALTER COLUMN fecha_inicio_periodo DROP NOT NULL,
    ALTER COLUMN fecha_fin_periodo DROP NOT NULL;

-- 3. Alterar tabla cotizacion_partida_categorias
ALTER TABLE cotizacion_partida_categorias
    ADD COLUMN IF NOT EXISTS tipo_sueldo tipo_sueldo_enum DEFAULT 'BRUTO';

-- 4. Crear tabla cotizacion_items (line items para todos los niveles)
CREATE TABLE IF NOT EXISTS cotizacion_items (
    id SERIAL PRIMARY KEY,
    cotizacion_id INTEGER NOT NULL REFERENCES cotizaciones(id) ON DELETE CASCADE,
    partida_id INTEGER REFERENCES cotizacion_partidas(id) ON DELETE CASCADE,
    partida_categoria_id INTEGER REFERENCES cotizacion_partida_categorias(id) ON DELETE CASCADE,
    numero INTEGER NOT NULL,
    cantidad DECIMAL(12,2) NOT NULL DEFAULT 1,
    descripcion VARCHAR(500) NOT NULL,
    precio_unitario DECIMAL(12,2) NOT NULL DEFAULT 0,
    importe DECIMAL(12,2) NOT NULL DEFAULT 0,
    es_autogenerado BOOLEAN DEFAULT FALSE,
    fecha_creacion TIMESTAMPTZ DEFAULT NOW(),

    -- Scope rules:
    -- partida_categoria_id NOT NULL → perfil-level (PERSONAL)
    -- partida_id NOT NULL, partida_categoria_id NULL → partida-level (ambos tipos)
    -- ambos NULL → global-level (aplica a toda la cotización)
    CONSTRAINT chk_scope CHECK (
        (partida_categoria_id IS NOT NULL AND partida_id IS NOT NULL) OR
        (partida_categoria_id IS NULL)
    )
);

CREATE INDEX IF NOT EXISTS idx_cotizacion_items_cotizacion ON cotizacion_items(cotizacion_id);
CREATE INDEX IF NOT EXISTS idx_cotizacion_items_partida ON cotizacion_items(partida_id);
CREATE INDEX IF NOT EXISTS idx_cotizacion_items_categoria ON cotizacion_items(partida_categoria_id);

-- 5. RLS para cotizacion_items (replica patrón de cotizacion_conceptos)
ALTER TABLE cotizacion_items ENABLE ROW LEVEL SECURITY;

CREATE POLICY "cotizacion_items_select_policy"
    ON cotizacion_items FOR SELECT
    USING (true);

CREATE POLICY "cotizacion_items_insert_policy"
    ON cotizacion_items FOR INSERT
    WITH CHECK (true);

CREATE POLICY "cotizacion_items_update_policy"
    ON cotizacion_items FOR UPDATE
    USING (true);

CREATE POLICY "cotizacion_items_delete_policy"
    ON cotizacion_items FOR DELETE
    USING (true);
