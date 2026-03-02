-- =============================================================================
-- Migration 041: Crear modulo de asistencias
-- =============================================================================
-- Fecha: 2026-03-02
-- Descripcion: Crea la estructura base del modulo de asistencias para horarios
--              contractuales, asignacion de supervisores por sede, jornadas de
--              captura, incidencias por excepcion y registros consolidados.
--              Deja preparada la base para modelo supervisado y autoregistro.
-- Dependencias: 000_create_empresas, 003_create_contratos,
--               007_create_empleados_table, 012_create_archivo_sistema,
--               014_create_sedes_tables, 015_create_user_auth_tables,
--               035_extend_empleados_onboarding, 040_create_bajas_empleado
-- =============================================================================

-- =============================================================================
-- 1. Crear ENUMs
-- =============================================================================

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_type WHERE typname = 'estatus_jornada_enum'
    ) THEN
        CREATE TYPE public.estatus_jornada_enum AS ENUM (
            'ABIERTA',
            'CERRADA',
            'CONSOLIDADA'
        );
    END IF;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_type WHERE typname = 'tipo_incidencia_enum'
    ) THEN
        CREATE TYPE public.tipo_incidencia_enum AS ENUM (
            'FALTA',
            'FALTA_JUSTIFICADA',
            'RETARDO',
            'SALIDA_ANTICIPADA',
            'HORA_EXTRA',
            'PERMISO_CON_GOCE',
            'PERMISO_SIN_GOCE',
            'INCAPACIDAD_ENFERMEDAD',
            'INCAPACIDAD_RIESGO_TRABAJO',
            'INCAPACIDAD_MATERNIDAD',
            'VACACIONES',
            'DIA_FESTIVO',
            'COMISION',
            'OTRO'
        );
    END IF;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_type WHERE typname = 'origen_incidencia_enum'
    ) THEN
        CREATE TYPE public.origen_incidencia_enum AS ENUM (
            'SUPERVISOR',
            'RH',
            'AUTOREGISTRO'
        );
    END IF;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_type WHERE typname = 'tipo_registro_asistencia_enum'
    ) THEN
        CREATE TYPE public.tipo_registro_asistencia_enum AS ENUM (
            'ASISTENCIA',
            'FALTA',
            'FALTA_JUSTIFICADA',
            'RETARDO',
            'SALIDA_ANTICIPADA',
            'HORA_EXTRA',
            'PERMISO_CON_GOCE',
            'PERMISO_SIN_GOCE',
            'INCAPACIDAD_ENFERMEDAD',
            'INCAPACIDAD_RIESGO_TRABAJO',
            'INCAPACIDAD_MATERNIDAD',
            'VACACIONES',
            'DIA_FESTIVO',
            'COMISION',
            'OTRO'
        );
    END IF;
END $$;

COMMENT ON TYPE public.estatus_jornada_enum IS
'Estados de jornada: ABIERTA = jornada iniciada y editable; CERRADA = supervisor confirmo cierre y se dispara consolidacion; CONSOLIDADA = registros finales generados y jornada concluida.';

COMMENT ON TYPE public.tipo_incidencia_enum IS
'Tipos de incidencia de asistencia: FALTA = inasistencia sin justificar; FALTA_JUSTIFICADA = inasistencia aceptada; RETARDO = llegada posterior a la tolerancia; SALIDA_ANTICIPADA = salida antes del horario; HORA_EXTRA = tiempo adicional laborado; PERMISO_CON_GOCE = ausencia autorizada con pago; PERMISO_SIN_GOCE = ausencia autorizada sin pago; INCAPACIDAD_ENFERMEDAD = incapacidad IMSS por enfermedad general; INCAPACIDAD_RIESGO_TRABAJO = incapacidad IMSS por riesgo laboral; INCAPACIDAD_MATERNIDAD = incapacidad IMSS por maternidad; VACACIONES = periodo vacacional autorizado; DIA_FESTIVO = dia festivo oficial; COMISION = servicio o actividad fuera de sede habitual; OTRO = incidencia no catalogada.';

COMMENT ON TYPE public.origen_incidencia_enum IS
'Origen de la incidencia: SUPERVISOR = capturada durante la jornada; RH = precargada por Recursos Humanos; AUTOREGISTRO = capturada por el propio empleado en modalidad futura.';

COMMENT ON TYPE public.tipo_registro_asistencia_enum IS
'Resultado final del dia laboral: ASISTENCIA = jornada normal sin excepciones; el resto de valores replica tipo_incidencia_enum para identificar faltas, retardos, permisos, incapacidades, vacaciones, festivos, comisiones u otros supuestos que impactan nomina.';

-- =============================================================================
-- 2. Crear tabla horarios
-- =============================================================================

CREATE TABLE IF NOT EXISTS public.horarios (
    id SERIAL PRIMARY KEY,
    empresa_id INTEGER NOT NULL,
    contrato_id INTEGER NOT NULL,
    nombre VARCHAR(100) NOT NULL,
    descripcion TEXT,
    dias_laborales JSONB NOT NULL,
    tolerancia_entrada_min INTEGER NOT NULL DEFAULT 10,
    tolerancia_salida_min INTEGER NOT NULL DEFAULT 0,
    es_horario_activo BOOLEAN NOT NULL DEFAULT TRUE,
    estatus VARCHAR(10) NOT NULL DEFAULT 'ACTIVO',
    fecha_creacion TIMESTAMPTZ DEFAULT NOW(),
    fecha_actualizacion TIMESTAMPTZ DEFAULT NOW(),

    CONSTRAINT fk_horarios_empresa
        FOREIGN KEY (empresa_id) REFERENCES public.empresas(id) ON DELETE CASCADE,
    CONSTRAINT fk_horarios_contrato
        FOREIGN KEY (contrato_id) REFERENCES public.contratos(id) ON DELETE CASCADE,
    CONSTRAINT chk_horarios_tolerancia_entrada
        CHECK (tolerancia_entrada_min BETWEEN 0 AND 60),
    CONSTRAINT chk_horarios_tolerancia_salida
        CHECK (tolerancia_salida_min BETWEEN 0 AND 60),
    CONSTRAINT chk_horarios_dias_laborales
        CHECK (
            dias_laborales IS NOT NULL
            AND jsonb_typeof(dias_laborales) = 'object'
        )
);

COMMENT ON TABLE public.horarios IS 'Horarios contractuales reutilizables por contrato; definen dias laborables, horas base y tolerancias de asistencia.';
COMMENT ON COLUMN public.horarios.empresa_id IS 'Empresa propietaria del contrato y del horario operativo.';
COMMENT ON COLUMN public.horarios.contrato_id IS 'Contrato al que aplica el horario base del personal.';
COMMENT ON COLUMN public.horarios.nombre IS 'Nombre operativo del horario para distinguir vigencias o cambios contractuales.';
COMMENT ON COLUMN public.horarios.descripcion IS 'Contexto adicional del horario, turnos o consideraciones operativas.';
COMMENT ON COLUMN public.horarios.dias_laborales IS 'JSONB por dia con horas de entrada y salida; permite dias no laborables con valor null.';
COMMENT ON COLUMN public.horarios.tolerancia_entrada_min IS 'Minutos de gracia antes de considerar retardo.';
COMMENT ON COLUMN public.horarios.tolerancia_salida_min IS 'Minutos permitidos antes de considerar salida anticipada.';
COMMENT ON COLUMN public.horarios.es_horario_activo IS 'Marca el horario vigente dentro del contrato cuando existen versiones historicas.';
COMMENT ON COLUMN public.horarios.estatus IS 'Estatus operativo del horario para control administrativo.';
COMMENT ON COLUMN public.horarios.fecha_creacion IS 'Fecha de alta del horario contractual.';
COMMENT ON COLUMN public.horarios.fecha_actualizacion IS 'Ultima actualizacion del horario contractual.';

CREATE INDEX IF NOT EXISTS idx_horarios_empresa
    ON public.horarios(empresa_id);

CREATE INDEX IF NOT EXISTS idx_horarios_contrato
    ON public.horarios(contrato_id);

CREATE INDEX IF NOT EXISTS idx_horarios_activo
    ON public.horarios(empresa_id, contrato_id)
    WHERE es_horario_activo = TRUE;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger
        WHERE tgname = 'set_fecha_actualizacion_horarios'
    ) THEN
        CREATE TRIGGER set_fecha_actualizacion_horarios
            BEFORE UPDATE ON public.horarios
            FOR EACH ROW
            EXECUTE FUNCTION update_fecha_actualizacion();
    END IF;
END $$;

-- =============================================================================
-- 3. Crear tabla supervisor_sedes
-- =============================================================================

CREATE TABLE IF NOT EXISTS public.supervisor_sedes (
    id SERIAL PRIMARY KEY,
    supervisor_id INTEGER NOT NULL,
    sede_id INTEGER NOT NULL,
    empresa_id INTEGER NOT NULL,
    fecha_inicio DATE NOT NULL DEFAULT CURRENT_DATE,
    fecha_fin DATE,
    activo BOOLEAN NOT NULL DEFAULT TRUE,
    notas TEXT,
    fecha_creacion TIMESTAMPTZ DEFAULT NOW(),
    fecha_actualizacion TIMESTAMPTZ DEFAULT NOW(),

    CONSTRAINT fk_supervisor_sedes_supervisor
        FOREIGN KEY (supervisor_id) REFERENCES public.empleados(id) ON DELETE CASCADE,
    CONSTRAINT fk_supervisor_sedes_sede
        FOREIGN KEY (sede_id) REFERENCES public.sedes(id) ON DELETE CASCADE,
    CONSTRAINT fk_supervisor_sedes_empresa
        FOREIGN KEY (empresa_id) REFERENCES public.empresas(id) ON DELETE CASCADE,
    CONSTRAINT chk_supervisor_sedes_fechas
        CHECK (fecha_fin IS NULL OR fecha_fin >= fecha_inicio)
);

COMMENT ON TABLE public.supervisor_sedes IS 'Asignacion territorial de supervisores a sedes; define que plantilla puede gestionar cada supervisor.';
COMMENT ON COLUMN public.supervisor_sedes.supervisor_id IS 'Empleado que supervisa una o mas sedes dentro de la empresa.';
COMMENT ON COLUMN public.supervisor_sedes.sede_id IS 'Sede asignada al supervisor para captura y seguimiento de asistencia.';
COMMENT ON COLUMN public.supervisor_sedes.empresa_id IS 'Empresa a la que pertenecen supervisor y sede asignada.';
COMMENT ON COLUMN public.supervisor_sedes.fecha_inicio IS 'Inicio de vigencia de la asignacion de sede al supervisor.';
COMMENT ON COLUMN public.supervisor_sedes.fecha_fin IS 'Fin de vigencia de la asignacion; NULL indica asignacion activa.';
COMMENT ON COLUMN public.supervisor_sedes.activo IS 'Bandera operativa para identificar la asignacion vigente sin borrar historial.';
COMMENT ON COLUMN public.supervisor_sedes.notas IS 'Observaciones sobre cobertura, rotaciones o alcances de la supervision.';
COMMENT ON COLUMN public.supervisor_sedes.fecha_creacion IS 'Fecha de alta de la asignacion supervisor-sede.';
COMMENT ON COLUMN public.supervisor_sedes.fecha_actualizacion IS 'Ultima actualizacion de la asignacion supervisor-sede.';

CREATE UNIQUE INDEX IF NOT EXISTS uq_supervisor_sedes_supervisor_sede_activa
    ON public.supervisor_sedes(supervisor_id, sede_id)
    WHERE activo = TRUE;

CREATE INDEX IF NOT EXISTS idx_supervisor_sedes_supervisor
    ON public.supervisor_sedes(supervisor_id)
    WHERE activo = TRUE;

CREATE INDEX IF NOT EXISTS idx_supervisor_sedes_sede
    ON public.supervisor_sedes(sede_id)
    WHERE activo = TRUE;

CREATE INDEX IF NOT EXISTS idx_supervisor_sedes_empresa
    ON public.supervisor_sedes(empresa_id);

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger
        WHERE tgname = 'set_fecha_actualizacion_supervisor_sedes'
    ) THEN
        CREATE TRIGGER set_fecha_actualizacion_supervisor_sedes
            BEFORE UPDATE ON public.supervisor_sedes
            FOR EACH ROW
            EXECUTE FUNCTION update_fecha_actualizacion();
    END IF;
END $$;

-- =============================================================================
-- 4. Crear tabla jornadas
-- =============================================================================

CREATE TABLE IF NOT EXISTS public.jornadas (
    id SERIAL PRIMARY KEY,
    empresa_id INTEGER NOT NULL,
    contrato_id INTEGER NOT NULL,
    horario_id INTEGER,
    supervisor_id INTEGER,
    fecha DATE NOT NULL,
    estatus VARCHAR(20) NOT NULL DEFAULT 'ABIERTA',
    empleados_esperados INTEGER NOT NULL DEFAULT 0,
    novedades_registradas INTEGER NOT NULL DEFAULT 0,
    notas TEXT,
    abierta_por UUID,
    cerrada_por UUID,
    fecha_apertura TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    fecha_cierre TIMESTAMPTZ,
    fecha_creacion TIMESTAMPTZ DEFAULT NOW(),
    fecha_actualizacion TIMESTAMPTZ DEFAULT NOW(),

    CONSTRAINT fk_jornadas_empresa
        FOREIGN KEY (empresa_id) REFERENCES public.empresas(id) ON DELETE CASCADE,
    CONSTRAINT fk_jornadas_contrato
        FOREIGN KEY (contrato_id) REFERENCES public.contratos(id) ON DELETE CASCADE,
    CONSTRAINT fk_jornadas_horario
        FOREIGN KEY (horario_id) REFERENCES public.horarios(id) ON DELETE SET NULL,
    CONSTRAINT fk_jornadas_supervisor
        FOREIGN KEY (supervisor_id) REFERENCES public.empleados(id) ON DELETE SET NULL,
    CONSTRAINT fk_jornadas_abierta_por
        FOREIGN KEY (abierta_por) REFERENCES auth.users(id) ON DELETE SET NULL,
    CONSTRAINT fk_jornadas_cerrada_por
        FOREIGN KEY (cerrada_por) REFERENCES auth.users(id) ON DELETE SET NULL,
    CONSTRAINT chk_jornadas_estatus
        CHECK (estatus IN ('ABIERTA', 'CERRADA', 'CONSOLIDADA')),
    CONSTRAINT chk_jornadas_empleados_esperados
        CHECK (empleados_esperados >= 0),
    CONSTRAINT chk_jornadas_novedades
        CHECK (novedades_registradas >= 0),
    CONSTRAINT chk_jornadas_cierre
        CHECK (
            (estatus = 'ABIERTA' AND fecha_cierre IS NULL)
            OR (estatus != 'ABIERTA')
        )
);

COMMENT ON TABLE public.jornadas IS 'Sesiones diarias de captura de asistencia por supervisor o por modalidad de autoregistro.';
COMMENT ON COLUMN public.jornadas.empresa_id IS 'Empresa para la que se captura la jornada diaria.';
COMMENT ON COLUMN public.jornadas.contrato_id IS 'Contrato operativo cuya plantilla se espera atender en la fecha.';
COMMENT ON COLUMN public.jornadas.horario_id IS 'Horario contractual utilizado como referencia para retardos, salidas y consolidacion.';
COMMENT ON COLUMN public.jornadas.supervisor_id IS 'Supervisor responsable de la captura; NULL en modalidad futura de autoregistro.';
COMMENT ON COLUMN public.jornadas.fecha IS 'Fecha calendario de la jornada de asistencia.';
COMMENT ON COLUMN public.jornadas.estatus IS 'Estado de la jornada: ABIERTA, CERRADA o CONSOLIDADA.';
COMMENT ON COLUMN public.jornadas.empleados_esperados IS 'Total de empleados esperados para esa jornada antes de consolidar.';
COMMENT ON COLUMN public.jornadas.novedades_registradas IS 'Numero de incidencias capturadas por excepcion durante la jornada.';
COMMENT ON COLUMN public.jornadas.notas IS 'Observaciones generales del supervisor al abrir o cerrar la jornada.';
COMMENT ON COLUMN public.jornadas.abierta_por IS 'Usuario de auth que inicio la jornada en el sistema.';
COMMENT ON COLUMN public.jornadas.cerrada_por IS 'Usuario de auth que cerro la jornada y confirmo la consolidacion.';
COMMENT ON COLUMN public.jornadas.fecha_apertura IS 'Momento en que se abrio la jornada para captura.';
COMMENT ON COLUMN public.jornadas.fecha_cierre IS 'Momento en que la jornada fue cerrada por el supervisor.';
COMMENT ON COLUMN public.jornadas.fecha_creacion IS 'Fecha de creacion del registro de jornada.';
COMMENT ON COLUMN public.jornadas.fecha_actualizacion IS 'Ultima actualizacion del registro de jornada.';

CREATE INDEX IF NOT EXISTS idx_jornadas_empresa_fecha
    ON public.jornadas(empresa_id, fecha);

CREATE INDEX IF NOT EXISTS idx_jornadas_supervisor_fecha
    ON public.jornadas(supervisor_id, fecha);

CREATE INDEX IF NOT EXISTS idx_jornadas_contrato
    ON public.jornadas(contrato_id);

CREATE INDEX IF NOT EXISTS idx_jornadas_estatus
    ON public.jornadas(estatus)
    WHERE estatus != 'CONSOLIDADA';

CREATE UNIQUE INDEX IF NOT EXISTS uq_jornadas_supervisor_fecha
    ON public.jornadas(supervisor_id, fecha)
    WHERE supervisor_id IS NOT NULL;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger
        WHERE tgname = 'set_fecha_actualizacion_jornadas'
    ) THEN
        CREATE TRIGGER set_fecha_actualizacion_jornadas
            BEFORE UPDATE ON public.jornadas
            FOR EACH ROW
            EXECUTE FUNCTION update_fecha_actualizacion();
    END IF;
END $$;

-- =============================================================================
-- 5. Crear tabla incidencias_asistencia
-- =============================================================================

CREATE TABLE IF NOT EXISTS public.incidencias_asistencia (
    id SERIAL PRIMARY KEY,
    jornada_id INTEGER,
    empleado_id INTEGER NOT NULL,
    empresa_id INTEGER NOT NULL,
    fecha DATE NOT NULL,
    tipo_incidencia VARCHAR(30) NOT NULL,
    minutos_retardo INTEGER DEFAULT 0,
    horas_extra DECIMAL(4,2) DEFAULT 0,
    motivo TEXT,
    documento_soporte_id INTEGER,
    origen VARCHAR(20) NOT NULL DEFAULT 'SUPERVISOR',
    registrado_por UUID,
    sede_real_id INTEGER,
    fecha_creacion TIMESTAMPTZ DEFAULT NOW(),
    fecha_actualizacion TIMESTAMPTZ DEFAULT NOW(),

    CONSTRAINT fk_incidencias_asistencia_jornada
        FOREIGN KEY (jornada_id) REFERENCES public.jornadas(id) ON DELETE CASCADE,
    CONSTRAINT fk_incidencias_asistencia_empleado
        FOREIGN KEY (empleado_id) REFERENCES public.empleados(id) ON DELETE CASCADE,
    CONSTRAINT fk_incidencias_asistencia_empresa
        FOREIGN KEY (empresa_id) REFERENCES public.empresas(id) ON DELETE CASCADE,
    CONSTRAINT fk_incidencias_asistencia_documento_soporte
        FOREIGN KEY (documento_soporte_id) REFERENCES public.archivo_sistema(id) ON DELETE SET NULL,
    CONSTRAINT fk_incidencias_asistencia_registrado_por
        FOREIGN KEY (registrado_por) REFERENCES auth.users(id) ON DELETE SET NULL,
    CONSTRAINT fk_incidencias_asistencia_sede_real
        FOREIGN KEY (sede_real_id) REFERENCES public.sedes(id) ON DELETE SET NULL,
    CONSTRAINT chk_incidencias_tipo
        CHECK (tipo_incidencia IN (
            'FALTA', 'FALTA_JUSTIFICADA', 'RETARDO', 'SALIDA_ANTICIPADA',
            'HORA_EXTRA', 'PERMISO_CON_GOCE', 'PERMISO_SIN_GOCE',
            'INCAPACIDAD_ENFERMEDAD', 'INCAPACIDAD_RIESGO_TRABAJO',
            'INCAPACIDAD_MATERNIDAD', 'VACACIONES', 'DIA_FESTIVO',
            'COMISION', 'OTRO'
        )),
    CONSTRAINT chk_incidencias_origen
        CHECK (origen IN ('SUPERVISOR', 'RH', 'AUTOREGISTRO')),
    CONSTRAINT chk_incidencias_retardo
        CHECK (minutos_retardo >= 0),
    CONSTRAINT chk_incidencias_horas_extra
        CHECK (horas_extra >= 0),
    CONSTRAINT chk_incidencias_retardo_coherencia
        CHECK (tipo_incidencia != 'RETARDO' OR minutos_retardo > 0),
    CONSTRAINT chk_incidencias_horas_extra_coherencia
        CHECK (tipo_incidencia != 'HORA_EXTRA' OR horas_extra > 0)
);

COMMENT ON TABLE public.incidencias_asistencia IS 'Incidencias registradas por excepcion para un empleado y fecha; si no existe incidencia se asume asistencia normal.';
COMMENT ON COLUMN public.incidencias_asistencia.jornada_id IS 'Jornada de captura asociada; puede ser NULL para precargas hechas por RH.';
COMMENT ON COLUMN public.incidencias_asistencia.empleado_id IS 'Empleado afectado por la incidencia registrada.';
COMMENT ON COLUMN public.incidencias_asistencia.empresa_id IS 'Empresa a la que pertenece el empleado y la incidencia.';
COMMENT ON COLUMN public.incidencias_asistencia.fecha IS 'Fecha a la que aplica la incidencia.';
COMMENT ON COLUMN public.incidencias_asistencia.tipo_incidencia IS 'Clasificacion de la incidencia que impacta asistencia y nomina.';
COMMENT ON COLUMN public.incidencias_asistencia.minutos_retardo IS 'Minutos de atraso capturados cuando la incidencia es de retardo.';
COMMENT ON COLUMN public.incidencias_asistencia.horas_extra IS 'Horas extraordinarias autorizadas o registradas para la fecha.';
COMMENT ON COLUMN public.incidencias_asistencia.motivo IS 'Detalle libre para documentar contexto, justificacion o aclaraciones.';
COMMENT ON COLUMN public.incidencias_asistencia.documento_soporte_id IS 'Archivo de soporte como incapacidad, permiso o evidencia documental.';
COMMENT ON COLUMN public.incidencias_asistencia.origen IS 'Canal que genero la incidencia: supervisor, RH o autoregistro.';
COMMENT ON COLUMN public.incidencias_asistencia.registrado_por IS 'Usuario auth que capturo o precargo la incidencia.';
COMMENT ON COLUMN public.incidencias_asistencia.sede_real_id IS 'Sede donde realmente estuvo el empleado cuando aplica comision o cambio operativo.';
COMMENT ON COLUMN public.incidencias_asistencia.fecha_creacion IS 'Fecha de creacion de la incidencia.';
COMMENT ON COLUMN public.incidencias_asistencia.fecha_actualizacion IS 'Ultima actualizacion de la incidencia.';

CREATE INDEX IF NOT EXISTS idx_incidencias_empleado_fecha
    ON public.incidencias_asistencia(empleado_id, fecha);

CREATE INDEX IF NOT EXISTS idx_incidencias_jornada
    ON public.incidencias_asistencia(jornada_id)
    WHERE jornada_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_incidencias_empresa_fecha
    ON public.incidencias_asistencia(empresa_id, fecha);

CREATE INDEX IF NOT EXISTS idx_incidencias_tipo
    ON public.incidencias_asistencia(tipo_incidencia);

CREATE INDEX IF NOT EXISTS idx_incidencias_origen
    ON public.incidencias_asistencia(origen);

CREATE UNIQUE INDEX IF NOT EXISTS uq_incidencias_empleado_fecha
    ON public.incidencias_asistencia(empleado_id, fecha);

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger
        WHERE tgname = 'set_fecha_actualizacion_incidencias_asistencia'
    ) THEN
        CREATE TRIGGER set_fecha_actualizacion_incidencias_asistencia
            BEFORE UPDATE ON public.incidencias_asistencia
            FOR EACH ROW
            EXECUTE FUNCTION update_fecha_actualizacion();
    END IF;
END $$;

-- =============================================================================
-- 6. Crear tabla registros_asistencia
-- =============================================================================

CREATE TABLE IF NOT EXISTS public.registros_asistencia (
    id SERIAL PRIMARY KEY,
    empleado_id INTEGER NOT NULL,
    empresa_id INTEGER NOT NULL,
    contrato_id INTEGER NOT NULL,
    jornada_id INTEGER,
    incidencia_id INTEGER,
    fecha DATE NOT NULL,
    tipo_registro VARCHAR(30) NOT NULL,
    hora_entrada TIME,
    hora_salida TIME,
    horas_trabajadas DECIMAL(4,2),
    horas_extra DECIMAL(4,2) DEFAULT 0,
    minutos_retardo INTEGER DEFAULT 0,
    sede_real_id INTEGER,
    es_consolidado BOOLEAN NOT NULL DEFAULT FALSE,
    fecha_creacion TIMESTAMPTZ DEFAULT NOW(),
    fecha_actualizacion TIMESTAMPTZ DEFAULT NOW(),

    CONSTRAINT fk_registros_asistencia_empleado
        FOREIGN KEY (empleado_id) REFERENCES public.empleados(id) ON DELETE CASCADE,
    CONSTRAINT fk_registros_asistencia_empresa
        FOREIGN KEY (empresa_id) REFERENCES public.empresas(id) ON DELETE CASCADE,
    CONSTRAINT fk_registros_asistencia_contrato
        FOREIGN KEY (contrato_id) REFERENCES public.contratos(id) ON DELETE CASCADE,
    CONSTRAINT fk_registros_asistencia_jornada
        FOREIGN KEY (jornada_id) REFERENCES public.jornadas(id) ON DELETE SET NULL,
    CONSTRAINT fk_registros_asistencia_incidencia
        FOREIGN KEY (incidencia_id) REFERENCES public.incidencias_asistencia(id) ON DELETE SET NULL,
    CONSTRAINT fk_registros_asistencia_sede_real
        FOREIGN KEY (sede_real_id) REFERENCES public.sedes(id) ON DELETE SET NULL,
    CONSTRAINT chk_registros_tipo
        CHECK (tipo_registro IN (
            'ASISTENCIA', 'FALTA', 'FALTA_JUSTIFICADA', 'RETARDO',
            'SALIDA_ANTICIPADA', 'HORA_EXTRA', 'PERMISO_CON_GOCE',
            'PERMISO_SIN_GOCE', 'INCAPACIDAD_ENFERMEDAD',
            'INCAPACIDAD_RIESGO_TRABAJO', 'INCAPACIDAD_MATERNIDAD',
            'VACACIONES', 'DIA_FESTIVO', 'COMISION', 'OTRO'
        )),
    CONSTRAINT chk_registros_horas
        CHECK (horas_trabajadas IS NULL OR horas_trabajadas >= 0),
    CONSTRAINT chk_registros_horas_extra
        CHECK (horas_extra >= 0),
    CONSTRAINT chk_registros_retardo
        CHECK (minutos_retardo >= 0)
);

COMMENT ON TABLE public.registros_asistencia IS 'Fuente consolidada de asistencia por empleado y fecha; alimenta nomina, reportes y entregables contractuales.';
COMMENT ON COLUMN public.registros_asistencia.empleado_id IS 'Empleado del que se consolida el resultado final de asistencia.';
COMMENT ON COLUMN public.registros_asistencia.empresa_id IS 'Empresa dueña del registro consolidado.';
COMMENT ON COLUMN public.registros_asistencia.contrato_id IS 'Contrato que respalda la jornada laborada y el impacto de nomina.';
COMMENT ON COLUMN public.registros_asistencia.jornada_id IS 'Jornada que origino el registro consolidado cuando existe captura diaria.';
COMMENT ON COLUMN public.registros_asistencia.incidencia_id IS 'Incidencia fuente que explica el resultado final del dia cuando aplica.';
COMMENT ON COLUMN public.registros_asistencia.fecha IS 'Fecha laboral consolidada para calculos y entregables.';
COMMENT ON COLUMN public.registros_asistencia.tipo_registro IS 'Resultado final: ASISTENCIA normal o alguno de los tipos de incidencia.';
COMMENT ON COLUMN public.registros_asistencia.hora_entrada IS 'Hora real de entrada registrada o inferida para el dia.';
COMMENT ON COLUMN public.registros_asistencia.hora_salida IS 'Hora real de salida registrada o inferida para el dia.';
COMMENT ON COLUMN public.registros_asistencia.horas_trabajadas IS 'Horas efectivamente laboradas consideradas para control y nomina.';
COMMENT ON COLUMN public.registros_asistencia.horas_extra IS 'Horas extraordinarias consolidadas para pago o control.';
COMMENT ON COLUMN public.registros_asistencia.minutos_retardo IS 'Minutos finales de retardo consolidados para el dia.';
COMMENT ON COLUMN public.registros_asistencia.sede_real_id IS 'Sede efectiva de prestacion del servicio cuando difiere de la asignada.';
COMMENT ON COLUMN public.registros_asistencia.es_consolidado IS 'TRUE cuando el registro fue generado automaticamente al cerrar la jornada.';
COMMENT ON COLUMN public.registros_asistencia.fecha_creacion IS 'Fecha de creacion del registro consolidado.';
COMMENT ON COLUMN public.registros_asistencia.fecha_actualizacion IS 'Ultima actualizacion del registro consolidado.';

CREATE INDEX IF NOT EXISTS idx_registros_empleado_fecha
    ON public.registros_asistencia(empleado_id, fecha);

CREATE INDEX IF NOT EXISTS idx_registros_empresa_fecha
    ON public.registros_asistencia(empresa_id, fecha);

CREATE INDEX IF NOT EXISTS idx_registros_contrato_fecha
    ON public.registros_asistencia(contrato_id, fecha);

CREATE INDEX IF NOT EXISTS idx_registros_jornada
    ON public.registros_asistencia(jornada_id)
    WHERE jornada_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_registros_tipo
    ON public.registros_asistencia(tipo_registro);

CREATE INDEX IF NOT EXISTS idx_registros_sede_real
    ON public.registros_asistencia(sede_real_id)
    WHERE sede_real_id IS NOT NULL;

CREATE UNIQUE INDEX IF NOT EXISTS uq_registros_empleado_fecha
    ON public.registros_asistencia(empleado_id, fecha);

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger
        WHERE tgname = 'set_fecha_actualizacion_registros_asistencia'
    ) THEN
        CREATE TRIGGER set_fecha_actualizacion_registros_asistencia
            BEFORE UPDATE ON public.registros_asistencia
            FOR EACH ROW
            EXECUTE FUNCTION update_fecha_actualizacion();
    END IF;
END $$;

-- =============================================================================
-- 7. RLS (Row Level Security)
-- =============================================================================

ALTER TABLE public.horarios ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.supervisor_sedes ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.jornadas ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.incidencias_asistencia ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.registros_asistencia ENABLE ROW LEVEL SECURITY;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies
        WHERE schemaname = 'public'
        AND tablename = 'horarios'
        AND policyname = 'horarios_select_policy'
    ) THEN
        CREATE POLICY "horarios_select_policy" ON public.horarios
            FOR SELECT USING (true);
    END IF;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies
        WHERE schemaname = 'public'
        AND tablename = 'horarios'
        AND policyname = 'horarios_write_policy'
    ) THEN
        CREATE POLICY "horarios_write_policy" ON public.horarios
            FOR ALL USING (true) WITH CHECK (true);
    END IF;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies
        WHERE schemaname = 'public'
        AND tablename = 'supervisor_sedes'
        AND policyname = 'supervisor_sedes_select_policy'
    ) THEN
        CREATE POLICY "supervisor_sedes_select_policy" ON public.supervisor_sedes
            FOR SELECT USING (true);
    END IF;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies
        WHERE schemaname = 'public'
        AND tablename = 'supervisor_sedes'
        AND policyname = 'supervisor_sedes_write_policy'
    ) THEN
        CREATE POLICY "supervisor_sedes_write_policy" ON public.supervisor_sedes
            FOR ALL USING (true) WITH CHECK (true);
    END IF;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies
        WHERE schemaname = 'public'
        AND tablename = 'jornadas'
        AND policyname = 'jornadas_select_policy'
    ) THEN
        CREATE POLICY "jornadas_select_policy" ON public.jornadas
            FOR SELECT USING (true);
    END IF;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies
        WHERE schemaname = 'public'
        AND tablename = 'jornadas'
        AND policyname = 'jornadas_write_policy'
    ) THEN
        CREATE POLICY "jornadas_write_policy" ON public.jornadas
            FOR ALL USING (true) WITH CHECK (true);
    END IF;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies
        WHERE schemaname = 'public'
        AND tablename = 'incidencias_asistencia'
        AND policyname = 'incidencias_asistencia_select_policy'
    ) THEN
        CREATE POLICY "incidencias_asistencia_select_policy" ON public.incidencias_asistencia
            FOR SELECT USING (true);
    END IF;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies
        WHERE schemaname = 'public'
        AND tablename = 'incidencias_asistencia'
        AND policyname = 'incidencias_asistencia_write_policy'
    ) THEN
        CREATE POLICY "incidencias_asistencia_write_policy" ON public.incidencias_asistencia
            FOR ALL USING (true) WITH CHECK (true);
    END IF;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies
        WHERE schemaname = 'public'
        AND tablename = 'registros_asistencia'
        AND policyname = 'registros_asistencia_select_policy'
    ) THEN
        CREATE POLICY "registros_asistencia_select_policy" ON public.registros_asistencia
            FOR SELECT USING (true);
    END IF;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies
        WHERE schemaname = 'public'
        AND tablename = 'registros_asistencia'
        AND policyname = 'registros_asistencia_write_policy'
    ) THEN
        CREATE POLICY "registros_asistencia_write_policy" ON public.registros_asistencia
            FOR ALL USING (true) WITH CHECK (true);
    END IF;
END $$;

-- =============================================================================
-- Rollback (comentado)
-- =============================================================================
-- DROP POLICY IF EXISTS "registros_asistencia_write_policy" ON public.registros_asistencia;
-- DROP POLICY IF EXISTS "registros_asistencia_select_policy" ON public.registros_asistencia;
-- DROP POLICY IF EXISTS "incidencias_asistencia_write_policy" ON public.incidencias_asistencia;
-- DROP POLICY IF EXISTS "incidencias_asistencia_select_policy" ON public.incidencias_asistencia;
-- DROP POLICY IF EXISTS "jornadas_write_policy" ON public.jornadas;
-- DROP POLICY IF EXISTS "jornadas_select_policy" ON public.jornadas;
-- DROP POLICY IF EXISTS "supervisor_sedes_write_policy" ON public.supervisor_sedes;
-- DROP POLICY IF EXISTS "supervisor_sedes_select_policy" ON public.supervisor_sedes;
-- DROP POLICY IF EXISTS "horarios_write_policy" ON public.horarios;
-- DROP POLICY IF EXISTS "horarios_select_policy" ON public.horarios;
-- DROP TRIGGER IF EXISTS set_fecha_actualizacion_registros_asistencia ON public.registros_asistencia;
-- DROP TRIGGER IF EXISTS set_fecha_actualizacion_incidencias_asistencia ON public.incidencias_asistencia;
-- DROP TRIGGER IF EXISTS set_fecha_actualizacion_jornadas ON public.jornadas;
-- DROP TRIGGER IF EXISTS set_fecha_actualizacion_supervisor_sedes ON public.supervisor_sedes;
-- DROP TRIGGER IF EXISTS set_fecha_actualizacion_horarios ON public.horarios;
-- DROP TABLE IF EXISTS public.registros_asistencia CASCADE;
-- DROP TABLE IF EXISTS public.incidencias_asistencia CASCADE;
-- DROP TABLE IF EXISTS public.jornadas CASCADE;
-- DROP TABLE IF EXISTS public.supervisor_sedes CASCADE;
-- DROP TABLE IF EXISTS public.horarios CASCADE;
-- DROP TYPE IF EXISTS public.tipo_registro_asistencia_enum;
-- DROP TYPE IF EXISTS public.origen_incidencia_enum;
-- DROP TYPE IF EXISTS public.tipo_incidencia_enum;
-- DROP TYPE IF EXISTS public.estatus_jornada_enum;
