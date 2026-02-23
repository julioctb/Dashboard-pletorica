-- =============================================================================
-- Migration 036: Crear tabla empleado_documentos
-- =============================================================================
-- Descripcion: Documentos de expediente de empleados con flujo de validacion
--              y versionamiento. Soporta INE, comprobante domicilio, caratula
--              bancaria, CURP, RFC, NSS, acta nacimiento, estudios, foto.
-- Dependencias: 007_create_empleados_table, 012_create_archivo_sistema,
--               015_create_user_auth_tables
-- =============================================================================

-- 1. Crear tabla
CREATE TABLE IF NOT EXISTS public.empleado_documentos (
    id SERIAL PRIMARY KEY,
    empleado_id INTEGER NOT NULL REFERENCES public.empleados(id) ON DELETE CASCADE,

    -- Tipo y archivo
    tipo_documento VARCHAR(30) NOT NULL,
    archivo_id INTEGER REFERENCES public.archivo_sistema(id) ON DELETE SET NULL,
    nombre_archivo VARCHAR(255),

    -- Flujo de validacion
    estatus VARCHAR(20) NOT NULL DEFAULT 'PENDIENTE_REVISION',
    observacion_rechazo TEXT,
    revisado_por UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    fecha_revision TIMESTAMPTZ,

    -- Versionamiento
    version INTEGER NOT NULL DEFAULT 1,
    es_vigente BOOLEAN NOT NULL DEFAULT TRUE,

    -- Auditoria
    subido_por UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    fecha_creacion TIMESTAMPTZ DEFAULT NOW(),
    fecha_actualizacion TIMESTAMPTZ DEFAULT NOW(),

    -- =================================================================
    -- CHECKS
    -- =================================================================

    -- tipo_documento: 10 valores validos
    CONSTRAINT chk_empleado_docs_tipo CHECK (tipo_documento IN (
        'INE', 'COMPROBANTE_DOMICILIO', 'CARATULA_BANCARIA',
        'CURP_DOCUMENTO', 'RFC_DOCUMENTO', 'NSS_DOCUMENTO',
        'ACTA_NACIMIENTO', 'COMPROBANTE_ESTUDIOS', 'FOTOGRAFIA', 'OTRO'
    )),

    -- estatus: 3 valores validos
    CONSTRAINT chk_empleado_docs_estatus CHECK (estatus IN (
        'PENDIENTE_REVISION', 'APROBADO', 'RECHAZADO'
    )),

    -- Coherencia: rechazo requiere observacion
    CONSTRAINT chk_empleado_docs_rechazo_observacion CHECK (
        estatus != 'RECHAZADO' OR observacion_rechazo IS NOT NULL
    ),

    -- Coherencia: revision (aprobado/rechazado) requiere revisado_por
    CONSTRAINT chk_empleado_docs_revision CHECK (
        estatus = 'PENDIENTE_REVISION' OR revisado_por IS NOT NULL
    )
);

-- 2. Partial unique index: un documento vigente por tipo por empleado
CREATE UNIQUE INDEX IF NOT EXISTS idx_empleado_docs_vigente_unico
    ON public.empleado_documentos(empleado_id, tipo_documento)
    WHERE es_vigente = TRUE;

-- 3. Indices de busqueda
CREATE INDEX IF NOT EXISTS idx_empleado_docs_empleado
    ON public.empleado_documentos(empleado_id);

CREATE INDEX IF NOT EXISTS idx_empleado_docs_estatus
    ON public.empleado_documentos(estatus);

CREATE INDEX IF NOT EXISTS idx_empleado_docs_tipo
    ON public.empleado_documentos(tipo_documento);

CREATE INDEX IF NOT EXISTS idx_empleado_docs_empleado_vigente
    ON public.empleado_documentos(empleado_id, es_vigente)
    WHERE es_vigente = TRUE;

-- 4. Trigger fecha_actualizacion (reutilizar funcion existente)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger
        WHERE tgname = 'set_fecha_actualizacion_empleado_documentos'
    ) THEN
        CREATE TRIGGER set_fecha_actualizacion_empleado_documentos
            BEFORE UPDATE ON public.empleado_documentos
            FOR EACH ROW
            EXECUTE FUNCTION update_fecha_actualizacion();
    END IF;
END $$;

-- 5. Comments
COMMENT ON TABLE public.empleado_documentos IS 'Documentos del expediente de empleados con validacion y versionamiento';
COMMENT ON COLUMN public.empleado_documentos.tipo_documento IS 'Tipo: INE, COMPROBANTE_DOMICILIO, CARATULA_BANCARIA, etc.';
COMMENT ON COLUMN public.empleado_documentos.estatus IS 'Estado de revision: PENDIENTE_REVISION, APROBADO, RECHAZADO';
COMMENT ON COLUMN public.empleado_documentos.version IS 'Numero de version del documento (incrementa al resubir)';
COMMENT ON COLUMN public.empleado_documentos.es_vigente IS 'Solo un documento vigente por tipo por empleado';
COMMENT ON COLUMN public.empleado_documentos.observacion_rechazo IS 'Motivo del rechazo (requerido si rechazado)';

-- =============================================================================
-- RLS (Row Level Security)
-- =============================================================================

ALTER TABLE public.empleado_documentos ENABLE ROW LEVEL SECURITY;

-- SELECT: admin o usuario de empresa vinculada
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies
        WHERE policyname = 'empleado_docs_select_policy'
        AND tablename = 'empleado_documentos'
    ) THEN
        CREATE POLICY empleado_docs_select_policy ON public.empleado_documentos
            FOR SELECT USING (
                is_admin()
                OR EXISTS (
                    SELECT 1 FROM public.empleados e
                    WHERE e.id = empleado_documentos.empleado_id
                    AND e.empresa_id = ANY(get_user_companies())
                )
            );
    END IF;
END $$;

-- INSERT: admin o usuario de empresa vinculada
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies
        WHERE policyname = 'empleado_docs_insert_policy'
        AND tablename = 'empleado_documentos'
    ) THEN
        CREATE POLICY empleado_docs_insert_policy ON public.empleado_documentos
            FOR INSERT WITH CHECK (
                is_admin()
                OR EXISTS (
                    SELECT 1 FROM public.empleados e
                    WHERE e.id = empleado_documentos.empleado_id
                    AND e.empresa_id = ANY(get_user_companies())
                )
            );
    END IF;
END $$;

-- UPDATE: admin o usuario de empresa vinculada
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies
        WHERE policyname = 'empleado_docs_update_policy'
        AND tablename = 'empleado_documentos'
    ) THEN
        CREATE POLICY empleado_docs_update_policy ON public.empleado_documentos
            FOR UPDATE USING (
                is_admin()
                OR EXISTS (
                    SELECT 1 FROM public.empleados e
                    WHERE e.id = empleado_documentos.empleado_id
                    AND e.empresa_id = ANY(get_user_companies())
                )
            );
    END IF;
END $$;

-- DELETE: nunca (documentos se inactivan, no se borran)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies
        WHERE policyname = 'empleado_docs_delete_policy'
        AND tablename = 'empleado_documentos'
    ) THEN
        CREATE POLICY empleado_docs_delete_policy ON public.empleado_documentos
            FOR DELETE USING (FALSE);
    END IF;
END $$;

-- =============================================================================
-- Rollback (comentado)
-- =============================================================================
-- DROP POLICY IF EXISTS empleado_docs_delete_policy ON public.empleado_documentos;
-- DROP POLICY IF EXISTS empleado_docs_update_policy ON public.empleado_documentos;
-- DROP POLICY IF EXISTS empleado_docs_insert_policy ON public.empleado_documentos;
-- DROP POLICY IF EXISTS empleado_docs_select_policy ON public.empleado_documentos;
-- DROP TABLE IF EXISTS public.empleado_documentos;
