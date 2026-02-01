-- ============================================================================
-- Migración: Crear tabla historial_laboral
-- Descripción: Registro histórico de asignaciones de empleados a plazas
-- Fecha: 2025-01-21
-- ============================================================================

-- 1. Crear enums
CREATE TYPE estatus_historial AS ENUM ('ACTIVA', 'FINALIZADA', 'CANCELADA');
CREATE TYPE motivo_fin_historial AS ENUM (
    'RENUNCIA', 'DESPIDO', 'FIN_CONTRATO',
    'CAMBIO_PLAZA', 'SUSPENSION', 'FALLECIMIENTO', 'OTRO'
);

-- 2. Crear tabla
CREATE TABLE historial_laboral (
    id SERIAL PRIMARY KEY,
    plaza_id INTEGER NOT NULL REFERENCES plazas(id) ON DELETE RESTRICT,
    empleado_id INTEGER NOT NULL REFERENCES empleados(id) ON DELETE RESTRICT,
    fecha_inicio DATE NOT NULL,
    fecha_fin DATE,
    motivo_fin motivo_fin_historial,
    estatus estatus_historial NOT NULL DEFAULT 'ACTIVA',
    notas TEXT,
    fecha_creacion TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    fecha_actualizacion TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Validaciones
    CONSTRAINT chk_fechas_historial CHECK (fecha_fin IS NULL OR fecha_fin >= fecha_inicio),
    CONSTRAINT chk_motivo_fin CHECK (
        (estatus = 'ACTIVA' AND fecha_fin IS NULL AND motivo_fin IS NULL) OR
        (estatus != 'ACTIVA')
    )
);

-- 3. Índices para búsquedas frecuentes
CREATE INDEX idx_historial_plaza ON historial_laboral(plaza_id);
CREATE INDEX idx_historial_empleado ON historial_laboral(empleado_id);
CREATE INDEX idx_historial_estatus ON historial_laboral(estatus);
CREATE INDEX idx_historial_fechas ON historial_laboral(fecha_inicio, fecha_fin);

-- 4. Constraint: Solo una asignación activa por plaza
CREATE UNIQUE INDEX idx_historial_activa_plaza
ON historial_laboral(plaza_id)
WHERE estatus = 'ACTIVA';

-- 5. Constraint: Solo una asignación activa por empleado
CREATE UNIQUE INDEX idx_historial_activa_empleado
ON historial_laboral(empleado_id)
WHERE estatus = 'ACTIVA';

-- 6. Trigger para actualizar fecha_actualizacion
CREATE TRIGGER tr_historial_laboral_updated
    BEFORE UPDATE ON historial_laboral
    FOR EACH ROW
    EXECUTE FUNCTION update_fecha_actualizacion();

-- 7. Comentarios de documentación
COMMENT ON TABLE historial_laboral IS 'Registro histórico de asignaciones de empleados a plazas';
COMMENT ON COLUMN historial_laboral.plaza_id IS 'Plaza asignada al empleado';
COMMENT ON COLUMN historial_laboral.empleado_id IS 'Empleado asignado a la plaza';
COMMENT ON COLUMN historial_laboral.fecha_inicio IS 'Fecha de inicio de la asignación';
COMMENT ON COLUMN historial_laboral.fecha_fin IS 'Fecha de fin (NULL = asignación activa)';
COMMENT ON COLUMN historial_laboral.motivo_fin IS 'Razón por la que terminó la asignación';
COMMENT ON COLUMN historial_laboral.estatus IS 'ACTIVA = vigente, FINALIZADA = terminó normalmente, CANCELADA = anulada';
COMMENT ON COLUMN historial_laboral.notas IS 'Observaciones adicionales';
