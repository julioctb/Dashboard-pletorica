-- ============================================================================
-- Migration 055: Documentación anual de empresas + links compartibles
-- ============================================================================
-- Descripción:
--   - Agrega EMPRESA al sistema polimórfico de archivo_sistema
--   - Crea empresa_documentos con versionado por empresa + año + tipo
--   - Crea empresa_documento_share_links para compartir expedientes anuales
--   - Actualiza can_access_archivo(...) para soportar archivos ligados a empresa
-- ============================================================================

-- 1. Extender enum entidad_archivo
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_enum
        WHERE enumlabel = 'EMPRESA'
          AND enumtypid = (SELECT oid FROM pg_type WHERE typname = 'entidad_archivo')
    ) THEN
        ALTER TYPE entidad_archivo ADD VALUE IF NOT EXISTS 'EMPRESA';
    END IF;
EXCEPTION
    WHEN others THEN
        NULL;
END $$;


-- 2. Tabla de documentos anuales de empresa
CREATE TABLE IF NOT EXISTS public.empresa_documentos (
    id SERIAL PRIMARY KEY,
    empresa_id INTEGER NOT NULL REFERENCES public.empresas(id) ON DELETE CASCADE,
    anio INTEGER NOT NULL,
    tipo_documento VARCHAR(60) NOT NULL,
    archivo_id INTEGER REFERENCES public.archivo_sistema(id) ON DELETE SET NULL,
    nombre_archivo VARCHAR(255),
    version INTEGER NOT NULL DEFAULT 1,
    es_vigente BOOLEAN NOT NULL DEFAULT TRUE,
    subido_por UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    fecha_creacion TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    fecha_actualizacion TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT chk_empresa_documentos_anio CHECK (anio BETWEEN 2000 AND 2100),
    CONSTRAINT chk_empresa_documentos_version CHECK (version >= 1),
    CONSTRAINT chk_empresa_documentos_tipo CHECK (tipo_documento IN (
        'ACTA_CONSTITUTIVA',
        'IDENTIFICACION_OFICIAL',
        'CONSTANCIA_SITUACION_FISCAL',
        'COMPROBANTE_DOMICILIO',
        'OPINION_CUMPLIMIENTO_SAT',
        'OPINION_POSITIVA_IMSS',
        'ADEUDO_INFONAVIT',
        'NO_ADEUDO_ESTADO',
        'PADRON_PROVEEDORES_BUAP',
        'REPSE',
        'MANIFESTACION_69B_77',
        'DECLARACION_ANUAL',
        'ACUSE_DECLARACION_ANUAL',
        'DECLARACION_MENSUAL',
        'ACUSE_DECLARACION_MENSUAL',
        'CURRICULUM_EMPRESARIAL',
        'FACTURAS_CONTRATOS',
        'COMPRANET',
        'COTIZACION'
    ))
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_empresa_documentos_vigente_unico
    ON public.empresa_documentos (empresa_id, anio, tipo_documento)
    WHERE es_vigente = TRUE;

CREATE INDEX IF NOT EXISTS idx_empresa_documentos_empresa_anio
    ON public.empresa_documentos (empresa_id, anio);

CREATE INDEX IF NOT EXISTS idx_empresa_documentos_tipo
    ON public.empresa_documentos (tipo_documento);

CREATE INDEX IF NOT EXISTS idx_empresa_documentos_archivo
    ON public.empresa_documentos (archivo_id)
    WHERE archivo_id IS NOT NULL;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger
        WHERE tgname = 'set_fecha_actualizacion_empresa_documentos'
    ) THEN
        CREATE TRIGGER set_fecha_actualizacion_empresa_documentos
            BEFORE UPDATE ON public.empresa_documentos
            FOR EACH ROW
            EXECUTE FUNCTION update_fecha_actualizacion();
    END IF;
END $$;

COMMENT ON TABLE public.empresa_documentos IS
'Expediente anual de documentos de proveedores. Conserva historial por tipo con una versión vigente por año.';

COMMENT ON COLUMN public.empresa_documentos.anio IS
'Año calendario del expediente documental (ej. 2026).';

COMMENT ON COLUMN public.empresa_documentos.tipo_documento IS
'Tipo de documento del checklist anual de empresa.';


-- 3. Tabla de links compartibles
CREATE TABLE IF NOT EXISTS public.empresa_documento_share_links (
    id SERIAL PRIMARY KEY,
    empresa_id INTEGER NOT NULL REFERENCES public.empresas(id) ON DELETE CASCADE,
    anio INTEGER NOT NULL,
    token_hash VARCHAR(64) NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    created_by UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    revoked_at TIMESTAMPTZ,
    revoked_by UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT chk_empresa_doc_share_anio CHECK (anio BETWEEN 2000 AND 2100),
    CONSTRAINT chk_empresa_doc_share_expiry CHECK (expires_at > created_at)
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_empresa_doc_share_token_hash
    ON public.empresa_documento_share_links (token_hash);

CREATE UNIQUE INDEX IF NOT EXISTS idx_empresa_doc_share_activo_unico
    ON public.empresa_documento_share_links (empresa_id, anio)
    WHERE revoked_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_empresa_doc_share_empresa_anio
    ON public.empresa_documento_share_links (empresa_id, anio);

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger
        WHERE tgname = 'set_fecha_actualizacion_empresa_doc_share_links'
    ) THEN
        CREATE TRIGGER set_fecha_actualizacion_empresa_doc_share_links
            BEFORE UPDATE ON public.empresa_documento_share_links
            FOR EACH ROW
            EXECUTE FUNCTION update_fecha_actualizacion();
    END IF;
END $$;

COMMENT ON TABLE public.empresa_documento_share_links IS
'Links compartibles a expedientes anuales de documentación de empresas. El token se guarda hasheado.';


-- 4. RLS para tablas nuevas
ALTER TABLE public.empresa_documentos ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.empresa_documento_share_links ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS empresa_documentos_select_policy ON public.empresa_documentos;
CREATE POLICY empresa_documentos_select_policy
ON public.empresa_documentos FOR SELECT
USING (
    is_admin()
    OR empresa_id = ANY(get_user_companies())
);

DROP POLICY IF EXISTS empresa_documentos_insert_policy ON public.empresa_documentos;
CREATE POLICY empresa_documentos_insert_policy
ON public.empresa_documentos FOR INSERT
WITH CHECK (
    is_admin()
    OR empresa_id = ANY(get_user_companies())
);

DROP POLICY IF EXISTS empresa_documentos_update_policy ON public.empresa_documentos;
CREATE POLICY empresa_documentos_update_policy
ON public.empresa_documentos FOR UPDATE
USING (
    is_admin()
    OR empresa_id = ANY(get_user_companies())
);

DROP POLICY IF EXISTS empresa_documentos_delete_policy ON public.empresa_documentos;
CREATE POLICY empresa_documentos_delete_policy
ON public.empresa_documentos FOR DELETE
USING (is_admin());

DROP POLICY IF EXISTS empresa_doc_share_select_policy ON public.empresa_documento_share_links;
CREATE POLICY empresa_doc_share_select_policy
ON public.empresa_documento_share_links FOR SELECT
USING (
    is_admin()
    OR empresa_id = ANY(get_user_companies())
);

DROP POLICY IF EXISTS empresa_doc_share_insert_policy ON public.empresa_documento_share_links;
CREATE POLICY empresa_doc_share_insert_policy
ON public.empresa_documento_share_links FOR INSERT
WITH CHECK (
    is_admin()
    OR empresa_id = ANY(get_user_companies())
);

DROP POLICY IF EXISTS empresa_doc_share_update_policy ON public.empresa_documento_share_links;
CREATE POLICY empresa_doc_share_update_policy
ON public.empresa_documento_share_links FOR UPDATE
USING (
    is_admin()
    OR empresa_id = ANY(get_user_companies())
);

DROP POLICY IF EXISTS empresa_doc_share_delete_policy ON public.empresa_documento_share_links;
CREATE POLICY empresa_doc_share_delete_policy
ON public.empresa_documento_share_links FOR DELETE
USING (is_admin());


-- 5. Actualizar helper de acceso a archivo_sistema
CREATE OR REPLACE FUNCTION public.can_access_archivo(p_entidad_tipo VARCHAR, p_entidad_id INTEGER)
RETURNS BOOLEAN
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = public
AS $$
    SELECT
        CASE p_entidad_tipo
            WHEN 'EMPRESA' THEN EXISTS (
                SELECT 1 FROM public.empresas
                WHERE id = p_entidad_id
                  AND id = ANY(get_user_companies())
            )
            WHEN 'REQUISICION' THEN EXISTS (
                SELECT 1 FROM public.requisicion
                WHERE id = p_entidad_id
                  AND empresa_id = ANY(get_user_companies())
            )
            WHEN 'REQUISICION_ITEM' THEN EXISTS (
                SELECT 1
                FROM public.requisicion_item ri
                JOIN public.requisicion r ON ri.requisicion_id = r.id
                WHERE ri.id = p_entidad_id
                  AND r.empresa_id = ANY(get_user_companies())
            )
            WHEN 'CONTRATO' THEN EXISTS (
                SELECT 1 FROM public.contratos
                WHERE id = p_entidad_id
                  AND empresa_id = ANY(get_user_companies())
            )
            WHEN 'EMPLEADO' THEN EXISTS (
                SELECT 1 FROM public.empleados
                WHERE id = p_entidad_id
                  AND empresa_id = ANY(get_user_companies())
            )
            WHEN 'ENTREGABLE' THEN EXISTS (
                SELECT 1
                FROM public.entregables e
                JOIN public.contratos c ON e.contrato_id = c.id
                WHERE e.id = p_entidad_id
                  AND c.empresa_id = ANY(get_user_companies())
            )
            WHEN 'PAGO' THEN EXISTS (
                SELECT 1
                FROM public.pagos p
                JOIN public.contratos c ON p.contrato_id = c.id
                WHERE p.id = p_entidad_id
                  AND c.empresa_id = ANY(get_user_companies())
            )
            WHEN 'REPORTE' THEN false
            WHEN 'REPORTE_ACTIVIDAD' THEN false
            ELSE false
        END;
$$;

