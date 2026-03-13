-- ============================================================================
-- Migration 056: Requisitos personalizados y documentos persistentes de empresa
-- ============================================================================

-- 1. Requisitos configurables por empresa
CREATE TABLE IF NOT EXISTS public.empresa_documento_requisitos (
    id SERIAL PRIMARY KEY,
    empresa_id INTEGER NOT NULL REFERENCES public.empresas(id) ON DELETE CASCADE,
    codigo VARCHAR(80) NOT NULL,
    nombre VARCHAR(160) NOT NULL,
    ayuda VARCHAR(500),
    es_obligatorio BOOLEAN NOT NULL DEFAULT FALSE,
    es_anual BOOLEAN NOT NULL DEFAULT TRUE,
    orden INTEGER NOT NULL DEFAULT 100,
    activo BOOLEAN NOT NULL DEFAULT TRUE,
    fecha_creacion TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    fecha_actualizacion TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_empresa_documento_requisitos_codigo UNIQUE (empresa_id, codigo),
    CONSTRAINT chk_empresa_documento_requisitos_orden CHECK (orden BETWEEN 1 AND 9999)
);

CREATE INDEX IF NOT EXISTS idx_empresa_documento_requisitos_empresa
    ON public.empresa_documento_requisitos (empresa_id, activo, orden);

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger
        WHERE tgname = 'set_fecha_actualizacion_empresa_documento_requisitos'
    ) THEN
        CREATE TRIGGER set_fecha_actualizacion_empresa_documento_requisitos
            BEFORE UPDATE ON public.empresa_documento_requisitos
            FOR EACH ROW
            EXECUTE FUNCTION update_fecha_actualizacion();
    END IF;
END $$;


-- 2. Referencia opcional a requisito personalizado en documentos cargados
ALTER TABLE public.empresa_documentos
    ADD COLUMN IF NOT EXISTS requisito_id INTEGER;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'empresa_documentos_requisito_id_fkey'
    ) THEN
        ALTER TABLE public.empresa_documentos
            ADD CONSTRAINT empresa_documentos_requisito_id_fkey
            FOREIGN KEY (requisito_id)
            REFERENCES public.empresa_documento_requisitos(id)
            ON DELETE CASCADE;
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_empresa_documentos_requisito
    ON public.empresa_documentos (requisito_id)
    WHERE requisito_id IS NOT NULL;


-- 3. Ajustar unicidad para permitir varios documentos adicionales por año
DROP INDEX IF EXISTS idx_empresa_documentos_vigente_unico;

CREATE UNIQUE INDEX IF NOT EXISTS idx_empresa_documentos_vigente_unico
    ON public.empresa_documentos (
        empresa_id,
        anio,
        tipo_documento,
        COALESCE(requisito_id, 0)
    )
    WHERE es_vigente = TRUE;


-- 4. Ampliar catálogo permitido de tipos de documento
ALTER TABLE public.empresa_documentos
    DROP CONSTRAINT IF EXISTS chk_empresa_documentos_tipo;

ALTER TABLE public.empresa_documentos
    ADD CONSTRAINT chk_empresa_documentos_tipo CHECK (tipo_documento IN (
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
        'MANIFESTACION_69B_CFF',
        'MANIFESTACION_77_LAASSP',
        'MANIFESTACION_69B_77',
        'DECLARACION_ANUAL',
        'ACUSE_DECLARACION_ANUAL',
        'DECLARACION_MENSUAL',
        'ACUSE_DECLARACION_MENSUAL',
        'CURRICULUM_EMPRESARIAL',
        'FACTURAS_CONTRATOS',
        'COMPRANET',
        'COTIZACION',
        'DOCUMENTO_ADICIONAL'
    ));


-- 5. RLS para requisitos personalizados
ALTER TABLE public.empresa_documento_requisitos ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS empresa_documento_requisitos_select_policy ON public.empresa_documento_requisitos;
CREATE POLICY empresa_documento_requisitos_select_policy
ON public.empresa_documento_requisitos FOR SELECT
USING (
    is_admin()
    OR empresa_id = ANY(get_user_companies())
);

DROP POLICY IF EXISTS empresa_documento_requisitos_insert_policy ON public.empresa_documento_requisitos;
CREATE POLICY empresa_documento_requisitos_insert_policy
ON public.empresa_documento_requisitos FOR INSERT
WITH CHECK (
    is_admin()
    OR empresa_id = ANY(get_user_companies())
);

DROP POLICY IF EXISTS empresa_documento_requisitos_update_policy ON public.empresa_documento_requisitos;
CREATE POLICY empresa_documento_requisitos_update_policy
ON public.empresa_documento_requisitos FOR UPDATE
USING (
    is_admin()
    OR empresa_id = ANY(get_user_companies())
);

DROP POLICY IF EXISTS empresa_documento_requisitos_delete_policy ON public.empresa_documento_requisitos;
CREATE POLICY empresa_documento_requisitos_delete_policy
ON public.empresa_documento_requisitos FOR DELETE
USING (is_admin());
