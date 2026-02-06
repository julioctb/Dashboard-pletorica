-- ============================================================================
-- Migration: Create Entregables Tables
-- Fecha: 2026-02-05
-- Descripción: Crea las tablas para el módulo de entregables.
--              - contrato_tipo_entregable: Configuración de tipos por contrato
--              - entregables: Registro operativo de entregables por período
--              - entregable_detalle_personal: Resumen de personal por categoría
-- Depende de: contratos, contrato_categorias, pagos, auth.users
-- ============================================================================

-- ============================================================================
-- 1. CREAR TIPOS ENUM
-- ============================================================================

-- Tipo de entregable según formato de archivo permitido
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'tipo_entregable') THEN
        CREATE TYPE tipo_entregable AS ENUM (
            'FOTOGRAFICO',      -- JPG, PNG, PDF (evidencia visual)
            'REPORTE',          -- PDF (informes de actividades)
            'LISTADO',          -- XLS, XLSX, CSV (se parsea y valida)
            'DOCUMENTAL'        -- PDF (documentos oficiales)
        );
    END IF;
END $$;

-- Periodicidad de entrega
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'periodicidad_entregable') THEN
        CREATE TYPE periodicidad_entregable AS ENUM (
            'MENSUAL',
            'QUINCENAL',
            'UNICO'             -- Un solo entregable para todo el contrato
        );
    END IF;
END $$;

-- Estados del ciclo de vida de un entregable
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'estatus_entregable') THEN
        CREATE TYPE estatus_entregable AS ENUM (
            'PENDIENTE',        -- Período habilitado, esperando entrega
            'EN_REVISION',      -- Cliente subió archivos, pasó validaciones
            'APROBADO',         -- BUAP aprobó, se creó pago
            'RECHAZADO'         -- Requiere corrección
        );
    END IF;
END $$;

-- Estados del pago (se usa en modificación de tabla pagos)
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'estatus_pago') THEN
        CREATE TYPE estatus_pago AS ENUM (
            'PENDIENTE',        -- Entregable aprobado, esperando factura
            'EN_PROCESO',       -- Factura subida, esperando pago
            'PAGADO'            -- Pago realizado
        );
    END IF;
END $$;


-- ============================================================================
-- 2. CREAR TABLA: contrato_tipo_entregable (configuración)
-- ============================================================================
-- Define qué tipos de entregable requiere cada contrato y con qué periodicidad.
-- Se configura al crear/editar el contrato.

CREATE TABLE IF NOT EXISTS public.contrato_tipo_entregable (
    id                  SERIAL PRIMARY KEY,
    contrato_id         INTEGER NOT NULL,
    tipo_entregable     tipo_entregable NOT NULL,
    periodicidad        periodicidad_entregable NOT NULL DEFAULT 'MENSUAL',
    requerido           BOOLEAN NOT NULL DEFAULT TRUE,
    descripcion         VARCHAR(200),
    instrucciones       VARCHAR(1000),
    fecha_creacion      TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    fecha_actualizacion TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- FK
    CONSTRAINT fk_cte_contrato FOREIGN KEY (contrato_id)
        REFERENCES public.contratos(id) ON DELETE CASCADE,

    -- Un contrato no puede tener el mismo tipo de entregable dos veces
    CONSTRAINT uk_contrato_tipo_entregable UNIQUE (contrato_id, tipo_entregable)
);

-- Comentarios de documentación
COMMENT ON TABLE public.contrato_tipo_entregable IS
'Configuración de tipos de entregable por contrato.
Define qué debe entregar la empresa proveedora y con qué periodicidad.
Ejemplo: Contrato de limpieza requiere FOTOGRAFICO (mensual) + LISTADO (mensual)';

COMMENT ON COLUMN public.contrato_tipo_entregable.tipo_entregable IS
'Tipo: FOTOGRAFICO (fotos), REPORTE (PDF), LISTADO (Excel/CSV), DOCUMENTAL (PDF)';

COMMENT ON COLUMN public.contrato_tipo_entregable.periodicidad IS
'MENSUAL, QUINCENAL, o UNICO (un solo entregable al final del contrato)';

COMMENT ON COLUMN public.contrato_tipo_entregable.requerido IS
'TRUE = obligatorio para aprobar el período. FALSE = opcional';

COMMENT ON COLUMN public.contrato_tipo_entregable.descripcion IS
'Nombre personalizado. Ej: "Fotos de limpieza", "Lista de personal"';

COMMENT ON COLUMN public.contrato_tipo_entregable.instrucciones IS
'Instrucciones específicas para el cliente sobre qué debe incluir';


-- ============================================================================
-- 3. CREAR TABLA: entregables (operativa principal)
-- ============================================================================
-- Un registro por cada período de entrega. El "paquete" que la empresa sube
-- y BUAP aprueba/rechaza.

CREATE TABLE IF NOT EXISTS public.entregables (
    id                      SERIAL PRIMARY KEY,
    contrato_id             INTEGER NOT NULL,
    periodo_inicio          DATE NOT NULL,
    periodo_fin             DATE NOT NULL,
    numero_periodo          INTEGER NOT NULL,
    estatus                 estatus_entregable NOT NULL DEFAULT 'PENDIENTE',
    
    -- Fechas del flujo
    fecha_entrega           TIMESTAMP WITH TIME ZONE,
    fecha_revision          TIMESTAMP WITH TIME ZONE,
    revisado_por            UUID,
    
    -- Rechazo
    observaciones_rechazo   TEXT,
    
    -- Montos
    monto_calculado         DECIMAL(15,2),
    monto_aprobado          DECIMAL(15,2),
    
    -- Relación con pago (se llena al aprobar)
    pago_id                 INTEGER,
    
    -- Auditoría
    fecha_creacion          TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    fecha_actualizacion     TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- FKs
    CONSTRAINT fk_entregables_contrato FOREIGN KEY (contrato_id)
        REFERENCES public.contratos(id) ON DELETE RESTRICT,
    
    CONSTRAINT fk_entregables_revisado_por FOREIGN KEY (revisado_por)
        REFERENCES auth.users(id) ON DELETE SET NULL,
    
    CONSTRAINT fk_entregables_pago FOREIGN KEY (pago_id)
        REFERENCES public.pagos(id) ON DELETE SET NULL,

    -- Restricciones
    CONSTRAINT uk_entregable_periodo UNIQUE (contrato_id, numero_periodo),
    CONSTRAINT chk_periodo_valido CHECK (periodo_fin >= periodo_inicio),
    CONSTRAINT chk_numero_periodo CHECK (numero_periodo > 0),
    CONSTRAINT chk_monto_calculado CHECK (monto_calculado IS NULL OR monto_calculado >= 0),
    CONSTRAINT chk_monto_aprobado CHECK (monto_aprobado IS NULL OR monto_aprobado >= 0)
);

-- Comentarios de documentación
COMMENT ON TABLE public.entregables IS
'Registro operativo de entregables por período.
Cada registro representa un "paquete" de entrega que incluye todos los tipos
configurados para el contrato (fotos, reportes, listados, etc.)
Los períodos se generan automáticamente según la periodicidad del contrato.';

COMMENT ON COLUMN public.entregables.periodo_inicio IS
'Fecha de inicio del período. Calculado según periodicidad y vigencia del contrato';

COMMENT ON COLUMN public.entregables.periodo_fin IS
'Fecha de fin del período. Calculado según periodicidad y vigencia del contrato';

COMMENT ON COLUMN public.entregables.numero_periodo IS
'Consecutivo dentro del contrato: 1, 2, 3...';

COMMENT ON COLUMN public.entregables.estatus IS
'PENDIENTE → EN_REVISION → APROBADO/RECHAZADO';

COMMENT ON COLUMN public.entregables.fecha_entrega IS
'Timestamp de cuando la empresa subió los archivos';

COMMENT ON COLUMN public.entregables.fecha_revision IS
'Timestamp de cuando BUAP revisó (aprobó o rechazó)';

COMMENT ON COLUMN public.entregables.revisado_por IS
'UUID del usuario BUAP que realizó la revisión';

COMMENT ON COLUMN public.entregables.observaciones_rechazo IS
'Motivo del rechazo. Se limpia si el cliente corrige y vuelve a enviar';

COMMENT ON COLUMN public.entregables.monto_calculado IS
'Monto calculado automáticamente según detalle de personal y tarifas';

COMMENT ON COLUMN public.entregables.monto_aprobado IS
'Monto final aprobado por BUAP (puede diferir del calculado)';

COMMENT ON COLUMN public.entregables.pago_id IS
'FK al pago creado cuando se aprueba el entregable';


-- ============================================================================
-- 4. CREAR TABLA: entregable_detalle_personal (resumen por categoría)
-- ============================================================================
-- Solo para contratos con personal (tiene_personal = TRUE).
-- Resume cuántos empleados de cada categoría se reportaron y validaron.

CREATE TABLE IF NOT EXISTS public.entregable_detalle_personal (
    id                      SERIAL PRIMARY KEY,
    entregable_id           INTEGER NOT NULL,
    contrato_categoria_id   INTEGER NOT NULL,
    cantidad_reportada      INTEGER NOT NULL DEFAULT 0,
    cantidad_validada       INTEGER NOT NULL DEFAULT 0,
    tarifa_unitaria         DECIMAL(10,2) NOT NULL,
    subtotal                DECIMAL(15,2) NOT NULL,
    fecha_creacion          TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- FKs
    CONSTRAINT fk_edp_entregable FOREIGN KEY (entregable_id)
        REFERENCES public.entregables(id) ON DELETE CASCADE,
    
    CONSTRAINT fk_edp_contrato_categoria FOREIGN KEY (contrato_categoria_id)
        REFERENCES public.contrato_categorias(id) ON DELETE RESTRICT,

    -- Un entregable no puede tener la misma categoría dos veces
    CONSTRAINT uk_detalle_categoria UNIQUE (entregable_id, contrato_categoria_id),
    
    -- Validaciones
    CONSTRAINT chk_cantidad_reportada CHECK (cantidad_reportada >= 0),
    CONSTRAINT chk_cantidad_validada CHECK (cantidad_validada >= 0),
    CONSTRAINT chk_tarifa_unitaria CHECK (tarifa_unitaria >= 0),
    CONSTRAINT chk_subtotal CHECK (subtotal >= 0)
);

-- Comentarios de documentación
COMMENT ON TABLE public.entregable_detalle_personal IS
'Detalle de personal reportado por categoría en cada entregable.
Se genera al parsear el archivo LISTADO (CSV/XLS) que sube el cliente.
El subtotal se calcula como cantidad_validada × tarifa_unitaria.';

COMMENT ON COLUMN public.entregable_detalle_personal.cantidad_reportada IS
'Cantidad de empleados que el cliente reportó en el archivo';

COMMENT ON COLUMN public.entregable_detalle_personal.cantidad_validada IS
'Cantidad que el sistema validó (existen en BD y pertenecen a la empresa)';

COMMENT ON COLUMN public.entregable_detalle_personal.tarifa_unitaria IS
'Copia del costo_unitario de contrato_categorias al momento de crear el detalle';

COMMENT ON COLUMN public.entregable_detalle_personal.subtotal IS
'cantidad_validada × tarifa_unitaria';


-- ============================================================================
-- 5. ÍNDICES DE RENDIMIENTO
-- ============================================================================

-- contrato_tipo_entregable
CREATE INDEX IF NOT EXISTS idx_cte_contrato
ON public.contrato_tipo_entregable (contrato_id);

-- entregables: búsquedas frecuentes
CREATE INDEX IF NOT EXISTS idx_entregables_contrato
ON public.entregables (contrato_id);

CREATE INDEX IF NOT EXISTS idx_entregables_estatus
ON public.entregables (estatus);

CREATE INDEX IF NOT EXISTS idx_entregables_contrato_estatus
ON public.entregables (contrato_id, estatus);

CREATE INDEX IF NOT EXISTS idx_entregables_periodo
ON public.entregables (periodo_inicio, periodo_fin);

CREATE INDEX IF NOT EXISTS idx_entregables_pago
ON public.entregables (pago_id)
WHERE pago_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_entregables_fecha_creacion
ON public.entregables (fecha_creacion DESC);

-- Para alertas: entregables en revisión ordenados por fecha
CREATE INDEX IF NOT EXISTS idx_entregables_en_revision
ON public.entregables (fecha_entrega DESC)
WHERE estatus = 'EN_REVISION';

-- entregable_detalle_personal
CREATE INDEX IF NOT EXISTS idx_edp_entregable
ON public.entregable_detalle_personal (entregable_id);

CREATE INDEX IF NOT EXISTS idx_edp_categoria
ON public.entregable_detalle_personal (contrato_categoria_id);


-- ============================================================================
-- 6. TRIGGERS
-- ============================================================================

-- Trigger para actualizar fecha_actualizacion en contrato_tipo_entregable
CREATE TRIGGER tr_contrato_tipo_entregable_updated
    BEFORE UPDATE ON public.contrato_tipo_entregable
    FOR EACH ROW
    EXECUTE FUNCTION update_fecha_actualizacion();

-- Trigger para actualizar fecha_actualizacion en entregables
CREATE TRIGGER tr_entregables_updated
    BEFORE UPDATE ON public.entregables
    FOR EACH ROW
    EXECUTE FUNCTION update_fecha_actualizacion();


-- ============================================================================
-- 7. FIN DE MIGRACIÓN
-- ============================================================================
