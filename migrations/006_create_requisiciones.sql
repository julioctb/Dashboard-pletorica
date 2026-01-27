-- ============================================================================
-- Migracion 006: Crear tablas para el modulo de Requisiciones
-- ============================================================================
-- Ejecutar en Supabase SQL Editor
-- ============================================================================

-- 1. Tabla de configuracion de requisiciones
CREATE TABLE IF NOT EXISTS configuracion_requisicion (
    id SERIAL PRIMARY KEY,
    clave VARCHAR(50) NOT NULL UNIQUE,
    valor VARCHAR(255) NOT NULL DEFAULT '',
    descripcion VARCHAR(255),
    grupo VARCHAR(50) NOT NULL DEFAULT 'AREA_REQUIRENTE',
    orden INTEGER NOT NULL DEFAULT 0,
    activo BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 2. Tabla principal de requisiciones
CREATE TABLE IF NOT EXISTS requisicion (
    id SERIAL PRIMARY KEY,
    numero_requisicion VARCHAR(20) NOT NULL UNIQUE,
    fecha_elaboracion DATE NOT NULL DEFAULT CURRENT_DATE,
    estado VARCHAR(20) NOT NULL DEFAULT 'BORRADOR',
    tipo_contratacion VARCHAR(20) NOT NULL,

    -- Objeto de la contratacion
    objeto_contratacion TEXT NOT NULL,
    justificacion TEXT,

    -- Area requirente
    dependencia_requirente VARCHAR(255) NOT NULL,
    domicilio VARCHAR(255),
    titular_nombre VARCHAR(150) NOT NULL,
    titular_cargo VARCHAR(150),
    titular_telefono VARCHAR(20),
    titular_email VARCHAR(100),
    coordinador_nombre VARCHAR(150),
    coordinador_telefono VARCHAR(20),
    coordinador_email VARCHAR(100),
    asesor_nombre VARCHAR(150),
    asesor_telefono VARCHAR(20),
    asesor_email VARCHAR(100),

    -- Bien/Servicio
    lugar_entrega VARCHAR(255),
    fecha_entrega_inicio DATE,
    fecha_entrega_fin DATE,
    condiciones_entrega TEXT,
    tipo_garantia VARCHAR(100),
    garantia_vigencia VARCHAR(100),
    requisitos_proveedor TEXT,
    forma_pago VARCHAR(100),
    requiere_anticipo BOOLEAN NOT NULL DEFAULT FALSE,
    requiere_muestras BOOLEAN NOT NULL DEFAULT FALSE,
    requiere_visita BOOLEAN NOT NULL DEFAULT FALSE,

    -- PDI
    pdi_eje VARCHAR(255),
    pdi_objetivo VARCHAR(255),
    pdi_estrategia VARCHAR(255),
    pdi_meta VARCHAR(255),

    -- Otros
    existencia_almacen VARCHAR(100),
    observaciones TEXT,

    -- Firmas
    validacion_asesor VARCHAR(150),
    elabora_nombre VARCHAR(150),
    elabora_cargo VARCHAR(150),
    solicita_nombre VARCHAR(150),
    solicita_cargo VARCHAR(150),

    -- Adjudicacion
    empresa_id INTEGER REFERENCES empresa(id),
    fecha_adjudicacion DATE,
    empresa_nombre VARCHAR(255),

    -- Contrato asociado
    contrato_id INTEGER REFERENCES contrato(id),

    -- Auditoria
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 3. Tabla de items de requisicion
CREATE TABLE IF NOT EXISTS requisicion_item (
    id SERIAL PRIMARY KEY,
    requisicion_id INTEGER NOT NULL REFERENCES requisicion(id) ON DELETE CASCADE,
    numero_item INTEGER NOT NULL DEFAULT 1,
    unidad_medida VARCHAR(50) NOT NULL DEFAULT 'Pieza',
    cantidad DECIMAL(12, 4) NOT NULL DEFAULT 1,
    descripcion TEXT NOT NULL,
    precio_unitario_estimado DECIMAL(14, 2),
    subtotal_estimado DECIMAL(14, 2),
    especificaciones_tecnicas TEXT,
    referencia_visual_url VARCHAR(500),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 4. Tabla de partidas presupuestales
CREATE TABLE IF NOT EXISTS requisicion_partida (
    id SERIAL PRIMARY KEY,
    requisicion_id INTEGER NOT NULL REFERENCES requisicion(id) ON DELETE CASCADE,
    partida_presupuestaria VARCHAR(100) NOT NULL,
    area_destino VARCHAR(150),
    origen_recurso VARCHAR(150),
    oficio_suficiencia VARCHAR(100),
    presupuesto_autorizado DECIMAL(14, 2) NOT NULL DEFAULT 0,
    descripcion TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================================
-- INDICES
-- ============================================================================

-- Requisicion
CREATE INDEX idx_requisicion_estado ON requisicion(estado);
CREATE INDEX idx_requisicion_tipo ON requisicion(tipo_contratacion);
CREATE INDEX idx_requisicion_fecha ON requisicion(fecha_elaboracion DESC);
CREATE INDEX idx_requisicion_empresa ON requisicion(empresa_id);
CREATE INDEX idx_requisicion_numero_lower ON requisicion(LOWER(numero_requisicion));
CREATE INDEX idx_requisicion_dependencia_lower ON requisicion(LOWER(dependencia_requirente));

-- Items
CREATE INDEX idx_requisicion_item_requisicion ON requisicion_item(requisicion_id);

-- Partidas
CREATE INDEX idx_requisicion_partida_requisicion ON requisicion_partida(requisicion_id);

-- Configuracion
CREATE INDEX idx_configuracion_req_grupo ON configuracion_requisicion(grupo);
CREATE INDEX idx_configuracion_req_clave ON configuracion_requisicion(clave);

-- ============================================================================
-- DATOS INICIALES DE CONFIGURACION
-- ============================================================================

INSERT INTO configuracion_requisicion (clave, valor, descripcion, grupo, orden) VALUES
    -- Area Requirente
    ('dependencia_requirente', 'Direccion de Servicios', 'Nombre de la dependencia requirente', 'AREA_REQUIRENTE', 1),
    ('domicilio', '4 Sur 104, Centro, 72000 Puebla, Pue.', 'Domicilio de la dependencia', 'AREA_REQUIRENTE', 2),
    ('titular_nombre', '', 'Nombre del titular de la dependencia', 'AREA_REQUIRENTE', 3),
    ('titular_cargo', 'Director de Servicios', 'Cargo del titular', 'AREA_REQUIRENTE', 4),
    ('titular_telefono', '', 'Telefono del titular', 'AREA_REQUIRENTE', 5),
    ('titular_email', '', 'Email del titular', 'AREA_REQUIRENTE', 6),
    ('coordinador_nombre', '', 'Nombre del coordinador', 'AREA_REQUIRENTE', 7),
    ('coordinador_telefono', '', 'Telefono del coordinador', 'AREA_REQUIRENTE', 8),
    ('coordinador_email', '', 'Email del coordinador', 'AREA_REQUIRENTE', 9),
    ('asesor_nombre', '', 'Nombre del asesor tecnico', 'AREA_REQUIRENTE', 10),
    ('asesor_telefono', '', 'Telefono del asesor', 'AREA_REQUIRENTE', 11),
    ('asesor_email', '', 'Email del asesor', 'AREA_REQUIRENTE', 12),
    ('lugar_entrega', 'Almacen Central BUAP', 'Lugar de entrega por defecto', 'ENTREGA', 13),
    -- Firmas
    ('validacion_asesor', '', 'Validacion del asesor tecnico', 'FIRMAS', 14),
    ('elabora_nombre', '', 'Nombre de quien elabora', 'FIRMAS', 15),
    ('elabora_cargo', '', 'Cargo de quien elabora', 'FIRMAS', 16),
    ('solicita_nombre', '', 'Nombre de quien solicita', 'FIRMAS', 17),
    ('solicita_cargo', '', 'Cargo de quien solicita', 'FIRMAS', 18)
ON CONFLICT (clave) DO NOTHING;

-- ============================================================================
-- Agregar columna requisicion_id a contrato (relacion inversa)
-- ============================================================================
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'contrato' AND column_name = 'requisicion_id'
    ) THEN
        ALTER TABLE contrato ADD COLUMN requisicion_id INTEGER REFERENCES requisicion(id);
        CREATE INDEX idx_contrato_requisicion ON contrato(requisicion_id);
    END IF;
END
$$;
