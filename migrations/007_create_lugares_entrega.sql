-- ============================================================================
-- 007: Crear tabla lugar_entrega
-- ============================================================================
-- Permite configurar múltiples lugares de entrega que aparecen
-- como opciones en un select al crear requisiciones.
-- ============================================================================

CREATE TABLE IF NOT EXISTS lugar_entrega (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(200) NOT NULL,
    activo BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_lugar_entrega_activo ON lugar_entrega(activo);

-- Migrar el valor existente de configuracion_requisicion
INSERT INTO lugar_entrega (nombre)
SELECT valor FROM configuracion_requisicion
WHERE clave = 'lugar_entrega' AND valor != ''
ON CONFLICT DO NOTHING;

-- Eliminar la fila de lugar_entrega de configuracion_requisicion (ya no se usa ahí)
DELETE FROM configuracion_requisicion WHERE clave = 'lugar_entrega';
