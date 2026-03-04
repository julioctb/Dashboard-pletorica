-- =============================================================================
-- Migration 045: Crear módulo cotizador
-- =============================================================================
-- Fecha: 2026-03-04
-- Descripcion: Crea estructura completa del módulo cotizador:
--              configuracion_fiscal_empresa (1:1), cotizaciones, partidas,
--              categorías por partida, conceptos y valores de la matriz.
-- Dependencias: 000_create_empresas, 002_create_categorias_puesto,
--               003_create_contratos, 015_create_user_auth_tables
-- Autor: Sistema
-- =============================================================================

-- =============================================================================
-- 1. ENUMs
-- =============================================================================

DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'estatus_cotizacion_enum') THEN
        CREATE TYPE estatus_cotizacion_enum AS ENUM (
            'BORRADOR', 'PREPARADA', 'ENVIADA', 'APROBADA', 'RECHAZADA'
        );
    END IF;
END $$;

DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'estatus_partida_cotizacion_enum') THEN
        CREATE TYPE estatus_partida_cotizacion_enum AS ENUM (
            'PENDIENTE', 'ACEPTADA', 'NO_ASIGNADA', 'CONVERTIDA'
        );
    END IF;
END $$;

DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'tipo_concepto_cotizacion_enum') THEN
        CREATE TYPE tipo_concepto_cotizacion_enum AS ENUM ('PATRONAL', 'INDIRECTO');
    END IF;
END $$;

DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'tipo_valor_concepto_enum') THEN
        CREATE TYPE tipo_valor_concepto_enum AS ENUM ('FIJO', 'PORCENTAJE');
    END IF;
END $$;

-- =============================================================================
-- 2. TABLA: configuracion_fiscal_empresa (1:1 con empresas)
-- =============================================================================

CREATE TABLE IF NOT EXISTS public.configuracion_fiscal_empresa (
    id                          SERIAL PRIMARY KEY,
    empresa_id                  INTEGER NOT NULL
                                    REFERENCES public.empresas(id) ON DELETE CASCADE,

    -- Parámetros para CalculadoraCostoPatronal
    prima_riesgo                DECIMAL(7,5)  NOT NULL DEFAULT 0.005,
    factor_integracion          DECIMAL(8,6)  DEFAULT NULL,
    dias_aguinaldo              INTEGER       NOT NULL DEFAULT 15,
    prima_vacacional            DECIMAL(4,2)  NOT NULL DEFAULT 0.25,
    aplicar_art_36              BOOLEAN       NOT NULL DEFAULT true,
    zona_frontera               BOOLEAN       NOT NULL DEFAULT false,
    estado_isn                  VARCHAR(50)   NOT NULL DEFAULT 'Puebla',

    -- Representante legal (pre-relleno en cotizaciones)
    representante_legal_nombre  VARCHAR(200)  DEFAULT NULL,
    representante_legal_cargo   VARCHAR(100)  DEFAULT 'Representante Legal',

    -- Auditoría
    fecha_creacion              TIMESTAMPTZ   DEFAULT NOW(),
    fecha_actualizacion         TIMESTAMPTZ   DEFAULT NOW(),

    CONSTRAINT uq_config_fiscal_empresa   UNIQUE (empresa_id),
    CONSTRAINT chk_prima_riesgo           CHECK (prima_riesgo BETWEEN 0.005 AND 0.15),
    CONSTRAINT chk_dias_aguinaldo         CHECK (dias_aguinaldo >= 15),
    CONSTRAINT chk_prima_vacacional       CHECK (prima_vacacional >= 0.25)
);

COMMENT ON TABLE  public.configuracion_fiscal_empresa IS 'Parámetros fiscales/patronales por empresa (1:1). Alimenta al motor CalculadoraCostoPatronal.';
COMMENT ON COLUMN public.configuracion_fiscal_empresa.prima_riesgo IS 'Prima de riesgo de trabajo IMSS. Rango legal: 0.005–0.15.';
COMMENT ON COLUMN public.configuracion_fiscal_empresa.factor_integracion IS 'Factor de integración IMSS. NULL = cálculo automático con fórmula legal.';
COMMENT ON COLUMN public.configuracion_fiscal_empresa.dias_aguinaldo IS 'Días de aguinaldo (mínimo legal: 15).';
COMMENT ON COLUMN public.configuracion_fiscal_empresa.prima_vacacional IS 'Prima vacacional (mínimo legal: 0.25 = 25%).';
COMMENT ON COLUMN public.configuracion_fiscal_empresa.aplicar_art_36 IS 'Si true, el patrón absorbe cuota obrera IMSS (Art. 36 LSS).';
COMMENT ON COLUMN public.configuracion_fiscal_empresa.zona_frontera IS 'True para zona fronteriza norte (salario mínimo diferenciado).';
COMMENT ON COLUMN public.configuracion_fiscal_empresa.estado_isn IS 'Estado para tasa ISN. Ej: "Puebla", "Ciudad de Mexico".';

-- =============================================================================
-- 3. TABLA: cotizaciones
-- =============================================================================

CREATE TABLE IF NOT EXISTS public.cotizaciones (
    id                      SERIAL PRIMARY KEY,
    codigo                  VARCHAR(30)  NOT NULL,
    empresa_id              INTEGER      NOT NULL
                                REFERENCES public.empresas(id) ON DELETE CASCADE,

    -- Versionamiento
    version                 INTEGER      NOT NULL DEFAULT 1,
    cotizacion_origen_id    INTEGER      REFERENCES public.cotizaciones(id) ON DELETE SET NULL,

    -- Destinatario
    destinatario_nombre     VARCHAR(200) DEFAULT NULL,
    destinatario_cargo      VARCHAR(200) DEFAULT NULL,

    -- Período
    fecha_inicio_periodo    DATE         NOT NULL,
    fecha_fin_periodo       DATE         NOT NULL,

    -- Configuración de visualización
    mostrar_desglose        BOOLEAN      NOT NULL DEFAULT false,

    -- Representante legal (campo libre, pre-llenado desde config)
    representante_legal     VARCHAR(200) DEFAULT NULL,

    -- Estado
    estatus                 estatus_cotizacion_enum NOT NULL DEFAULT 'BORRADOR',
    notas                   TEXT         DEFAULT NULL,

    -- Auditoría
    created_by              UUID         REFERENCES auth.users(id) ON DELETE SET NULL,
    fecha_creacion          TIMESTAMPTZ  DEFAULT NOW(),
    fecha_actualizacion     TIMESTAMPTZ  DEFAULT NOW(),

    CONSTRAINT uq_cotizacion_codigo  UNIQUE (codigo),
    CONSTRAINT chk_cotizacion_fechas CHECK (fecha_fin_periodo > fecha_inicio_periodo),
    CONSTRAINT chk_cotizacion_version CHECK (version >= 1)
);

COMMENT ON TABLE  public.cotizaciones IS 'Cotizaciones de servicios. Cada cotización puede tener múltiples partidas.';
COMMENT ON COLUMN public.cotizaciones.codigo IS 'Código único autogenerado: COT-[EMPRESA]-[AÑO][SEQ]. Ej: COT-MAN-26001.';
COMMENT ON COLUMN public.cotizaciones.version IS 'Versión de la cotización. Incrementa al crear nueva versión.';
COMMENT ON COLUMN public.cotizaciones.cotizacion_origen_id IS 'FK a cotización original al versionar.';
COMMENT ON COLUMN public.cotizaciones.mostrar_desglose IS 'Si true, PDF incluye tabla de desglose de conceptos.';

-- =============================================================================
-- 4. TABLA: cotizacion_partidas
-- =============================================================================

CREATE TABLE IF NOT EXISTS public.cotizacion_partidas (
    id              SERIAL PRIMARY KEY,
    cotizacion_id   INTEGER NOT NULL REFERENCES public.cotizaciones(id) ON DELETE CASCADE,
    numero_partida  INTEGER NOT NULL,

    estatus_partida estatus_partida_cotizacion_enum NOT NULL DEFAULT 'PENDIENTE',
    contrato_id     INTEGER REFERENCES public.contratos(id) ON DELETE SET NULL,
    notas           TEXT    DEFAULT NULL,

    fecha_creacion  TIMESTAMPTZ DEFAULT NOW(),

    CONSTRAINT uq_partida_por_cotizacion UNIQUE (cotizacion_id, numero_partida),
    CONSTRAINT chk_numero_partida CHECK (numero_partida >= 1)
);

COMMENT ON TABLE  public.cotizacion_partidas IS 'Partidas (lotes) de una cotización. Cada partida se puede convertir a contrato.';
COMMENT ON COLUMN public.cotizacion_partidas.numero_partida IS 'Número de partida dentro de la cotización (1-N, autoincrementado).';
COMMENT ON COLUMN public.cotizacion_partidas.contrato_id IS 'FK al contrato generado al convertir esta partida.';

-- =============================================================================
-- 5. TABLA: cotizacion_partida_categorias
-- =============================================================================

CREATE TABLE IF NOT EXISTS public.cotizacion_partida_categorias (
    id                          SERIAL PRIMARY KEY,
    partida_id                  INTEGER  NOT NULL REFERENCES public.cotizacion_partidas(id) ON DELETE CASCADE,
    categoria_puesto_id         INTEGER  NOT NULL REFERENCES public.categorias_puesto(id) ON DELETE RESTRICT,

    cantidad_minima             INTEGER      NOT NULL DEFAULT 0,
    cantidad_maxima             INTEGER      NOT NULL DEFAULT 0,
    salario_base_mensual        DECIMAL(12,2) NOT NULL,

    -- Costo patronal (del motor de cálculo)
    costo_patronal_calculado    DECIMAL(12,2) NOT NULL DEFAULT 0,
    costo_patronal_editado      DECIMAL(12,2) DEFAULT NULL,
    fue_editado_manualmente     BOOLEAN       NOT NULL DEFAULT false,

    -- Precio unitario final (suma de columna en la matriz, sin IVA)
    precio_unitario_final       DECIMAL(12,2) NOT NULL DEFAULT 0,

    fecha_creacion              TIMESTAMPTZ  DEFAULT NOW(),

    CONSTRAINT uq_categoria_por_partida UNIQUE (partida_id, categoria_puesto_id),
    CONSTRAINT chk_cantidades           CHECK (cantidad_maxima >= cantidad_minima),
    CONSTRAINT chk_cantidad_minima      CHECK (cantidad_minima >= 0),
    CONSTRAINT chk_salario_base         CHECK (salario_base_mensual > 0)
);

COMMENT ON TABLE  public.cotizacion_partida_categorias IS 'Categorías de personal por partida con cantidades y costos.';
COMMENT ON COLUMN public.cotizacion_partida_categorias.costo_patronal_calculado IS 'Resultado del motor CalculadoraCostoPatronal (referencia).';
COMMENT ON COLUMN public.cotizacion_partida_categorias.costo_patronal_editado IS 'Valor manual cuando fue_editado_manualmente=true.';
COMMENT ON COLUMN public.cotizacion_partida_categorias.precio_unitario_final IS 'Suma de todos los valores de la columna en la matriz (sin IVA).';

-- =============================================================================
-- 6. TABLA: cotizacion_conceptos
-- =============================================================================

CREATE TABLE IF NOT EXISTS public.cotizacion_conceptos (
    id              SERIAL PRIMARY KEY,
    partida_id      INTEGER NOT NULL REFERENCES public.cotizacion_partidas(id) ON DELETE CASCADE,

    nombre          VARCHAR(200) NOT NULL,
    tipo_concepto   tipo_concepto_cotizacion_enum NOT NULL DEFAULT 'INDIRECTO',
    tipo_valor      tipo_valor_concepto_enum      NOT NULL DEFAULT 'FIJO',
    orden           INTEGER NOT NULL DEFAULT 0,
    es_autogenerado BOOLEAN NOT NULL DEFAULT false,

    fecha_creacion  TIMESTAMPTZ DEFAULT NOW(),

    CONSTRAINT uq_concepto_orden_partida UNIQUE (partida_id, orden)
);

COMMENT ON TABLE  public.cotizacion_conceptos IS 'Filas de la matriz de costos. PATRONAL=autogeneradas por motor; INDIRECTO=gastos del usuario.';
COMMENT ON COLUMN public.cotizacion_conceptos.orden IS 'Orden de aparición en la matriz. PATRONAL ocupan 1-9, INDIRECTO desde 10.';
COMMENT ON COLUMN public.cotizacion_conceptos.es_autogenerado IS 'True si fue creado automáticamente por calcular_costo_patronal.';

-- =============================================================================
-- 7. TABLA: cotizacion_concepto_valores
-- =============================================================================

CREATE TABLE IF NOT EXISTS public.cotizacion_concepto_valores (
    id                      SERIAL PRIMARY KEY,
    concepto_id             INTEGER NOT NULL REFERENCES public.cotizacion_conceptos(id) ON DELETE CASCADE,
    partida_categoria_id    INTEGER NOT NULL REFERENCES public.cotizacion_partida_categorias(id) ON DELETE CASCADE,

    valor_pesos             DECIMAL(12,2) NOT NULL DEFAULT 0,

    CONSTRAINT uq_valor_concepto_categoria UNIQUE (concepto_id, partida_categoria_id)
);

COMMENT ON TABLE  public.cotizacion_concepto_valores IS 'Intersección de la matriz: valor de un concepto para una categoría específica.';
COMMENT ON COLUMN public.cotizacion_concepto_valores.valor_pesos IS 'Importe en pesos para esta celda de la matriz (ya convertido si tipo_valor=PORCENTAJE).';

-- =============================================================================
-- 8. ÍNDICES
-- =============================================================================

-- configuracion_fiscal_empresa
CREATE INDEX IF NOT EXISTS idx_config_fiscal_empresa_id
    ON public.configuracion_fiscal_empresa(empresa_id);

-- cotizaciones
CREATE INDEX IF NOT EXISTS idx_cotizaciones_empresa_id
    ON public.cotizaciones(empresa_id);
CREATE INDEX IF NOT EXISTS idx_cotizaciones_empresa_estatus
    ON public.cotizaciones(empresa_id, estatus);
CREATE INDEX IF NOT EXISTS idx_cotizaciones_codigo_lower
    ON public.cotizaciones(LOWER(codigo));
CREATE INDEX IF NOT EXISTS idx_cotizaciones_origen
    ON public.cotizaciones(cotizacion_origen_id) WHERE cotizacion_origen_id IS NOT NULL;

-- cotizacion_partidas
CREATE INDEX IF NOT EXISTS idx_cotizacion_partidas_cotizacion
    ON public.cotizacion_partidas(cotizacion_id);
CREATE INDEX IF NOT EXISTS idx_cotizacion_partidas_contrato
    ON public.cotizacion_partidas(contrato_id) WHERE contrato_id IS NOT NULL;

-- cotizacion_partida_categorias
CREATE INDEX IF NOT EXISTS idx_cotizacion_partida_cat_partida
    ON public.cotizacion_partida_categorias(partida_id);
CREATE INDEX IF NOT EXISTS idx_cotizacion_partida_cat_categoria
    ON public.cotizacion_partida_categorias(categoria_puesto_id);

-- cotizacion_conceptos
CREATE INDEX IF NOT EXISTS idx_cotizacion_conceptos_partida
    ON public.cotizacion_conceptos(partida_id);
CREATE INDEX IF NOT EXISTS idx_cotizacion_conceptos_tipo
    ON public.cotizacion_conceptos(partida_id, tipo_concepto);

-- cotizacion_concepto_valores
CREATE INDEX IF NOT EXISTS idx_cotizacion_concepto_valores_concepto
    ON public.cotizacion_concepto_valores(concepto_id);
CREATE INDEX IF NOT EXISTS idx_cotizacion_concepto_valores_cat
    ON public.cotizacion_concepto_valores(partida_categoria_id);

-- =============================================================================
-- 9. TRIGGERS (fecha_actualizacion)
-- =============================================================================

DO $$ BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger
        WHERE tgname = 'trg_config_fiscal_empresa_updated_at'
    ) THEN
        CREATE TRIGGER trg_config_fiscal_empresa_updated_at
            BEFORE UPDATE ON public.configuracion_fiscal_empresa
            FOR EACH ROW EXECUTE FUNCTION update_fecha_actualizacion();
    END IF;
END $$;

DO $$ BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger
        WHERE tgname = 'trg_cotizaciones_updated_at'
    ) THEN
        CREATE TRIGGER trg_cotizaciones_updated_at
            BEFORE UPDATE ON public.cotizaciones
            FOR EACH ROW EXECUTE FUNCTION update_fecha_actualizacion();
    END IF;
END $$;

-- =============================================================================
-- 10. RLS (Row Level Security)
-- =============================================================================

CREATE OR REPLACE FUNCTION public.cotizador_empresa_access(target_empresa_id INTEGER)
RETURNS BOOLEAN
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = public
AS $$
    SELECT is_admin() OR target_empresa_id = ANY(get_user_companies());
$$;

CREATE OR REPLACE FUNCTION public.cotizador_can_access_cotizacion(target_cotizacion_id INTEGER)
RETURNS BOOLEAN
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = public
AS $$
    SELECT EXISTS (
        SELECT 1
        FROM public.cotizaciones c
        WHERE c.id = target_cotizacion_id
          AND cotizador_empresa_access(c.empresa_id)
    );
$$;

CREATE OR REPLACE FUNCTION public.cotizador_can_access_partida(target_partida_id INTEGER)
RETURNS BOOLEAN
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = public
AS $$
    SELECT EXISTS (
        SELECT 1
        FROM public.cotizacion_partidas p
        WHERE p.id = target_partida_id
          AND cotizador_can_access_cotizacion(p.cotizacion_id)
    );
$$;

CREATE OR REPLACE FUNCTION public.cotizador_can_access_partida_categoria(target_partida_categoria_id INTEGER)
RETURNS BOOLEAN
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = public
AS $$
    SELECT EXISTS (
        SELECT 1
        FROM public.cotizacion_partida_categorias pc
        WHERE pc.id = target_partida_categoria_id
          AND cotizador_can_access_partida(pc.partida_id)
    );
$$;

CREATE OR REPLACE FUNCTION public.cotizador_can_access_concepto(target_concepto_id INTEGER)
RETURNS BOOLEAN
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = public
AS $$
    SELECT EXISTS (
        SELECT 1
        FROM public.cotizacion_conceptos cc
        WHERE cc.id = target_concepto_id
          AND cotizador_can_access_partida(cc.partida_id)
    );
$$;

ALTER TABLE public.configuracion_fiscal_empresa ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.cotizaciones ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.cotizacion_partidas ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.cotizacion_partida_categorias ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.cotizacion_conceptos ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.cotizacion_concepto_valores ENABLE ROW LEVEL SECURITY;

CREATE POLICY config_fiscal_service_all ON public.configuracion_fiscal_empresa
    FOR ALL TO service_role USING (true) WITH CHECK (true);
CREATE POLICY cotizaciones_service_all ON public.cotizaciones
    FOR ALL TO service_role USING (true) WITH CHECK (true);
CREATE POLICY cotizacion_partidas_service_all ON public.cotizacion_partidas
    FOR ALL TO service_role USING (true) WITH CHECK (true);
CREATE POLICY cotizacion_partida_categorias_service_all ON public.cotizacion_partida_categorias
    FOR ALL TO service_role USING (true) WITH CHECK (true);
CREATE POLICY cotizacion_conceptos_service_all ON public.cotizacion_conceptos
    FOR ALL TO service_role USING (true) WITH CHECK (true);
CREATE POLICY cotizacion_concepto_valores_service_all ON public.cotizacion_concepto_valores
    FOR ALL TO service_role USING (true) WITH CHECK (true);

CREATE POLICY config_fiscal_select ON public.configuracion_fiscal_empresa
    FOR SELECT TO authenticated
    USING (cotizador_empresa_access(empresa_id));
CREATE POLICY config_fiscal_insert ON public.configuracion_fiscal_empresa
    FOR INSERT TO authenticated
    WITH CHECK (cotizador_empresa_access(empresa_id));
CREATE POLICY config_fiscal_update ON public.configuracion_fiscal_empresa
    FOR UPDATE TO authenticated
    USING (cotizador_empresa_access(empresa_id))
    WITH CHECK (cotizador_empresa_access(empresa_id));
CREATE POLICY config_fiscal_delete ON public.configuracion_fiscal_empresa
    FOR DELETE TO authenticated
    USING (cotizador_empresa_access(empresa_id));

CREATE POLICY cotizaciones_select ON public.cotizaciones
    FOR SELECT TO authenticated
    USING (cotizador_empresa_access(empresa_id));
CREATE POLICY cotizaciones_insert ON public.cotizaciones
    FOR INSERT TO authenticated
    WITH CHECK (cotizador_empresa_access(empresa_id));
CREATE POLICY cotizaciones_update ON public.cotizaciones
    FOR UPDATE TO authenticated
    USING (cotizador_empresa_access(empresa_id))
    WITH CHECK (cotizador_empresa_access(empresa_id));
CREATE POLICY cotizaciones_delete ON public.cotizaciones
    FOR DELETE TO authenticated
    USING (cotizador_empresa_access(empresa_id));

CREATE POLICY cotizacion_partidas_select ON public.cotizacion_partidas
    FOR SELECT TO authenticated
    USING (cotizador_can_access_cotizacion(cotizacion_id));
CREATE POLICY cotizacion_partidas_insert ON public.cotizacion_partidas
    FOR INSERT TO authenticated
    WITH CHECK (cotizador_can_access_cotizacion(cotizacion_id));
CREATE POLICY cotizacion_partidas_update ON public.cotizacion_partidas
    FOR UPDATE TO authenticated
    USING (cotizador_can_access_cotizacion(cotizacion_id))
    WITH CHECK (cotizador_can_access_cotizacion(cotizacion_id));
CREATE POLICY cotizacion_partidas_delete ON public.cotizacion_partidas
    FOR DELETE TO authenticated
    USING (cotizador_can_access_cotizacion(cotizacion_id));

CREATE POLICY cotizacion_partida_categorias_select ON public.cotizacion_partida_categorias
    FOR SELECT TO authenticated
    USING (cotizador_can_access_partida(partida_id));
CREATE POLICY cotizacion_partida_categorias_insert ON public.cotizacion_partida_categorias
    FOR INSERT TO authenticated
    WITH CHECK (cotizador_can_access_partida(partida_id));
CREATE POLICY cotizacion_partida_categorias_update ON public.cotizacion_partida_categorias
    FOR UPDATE TO authenticated
    USING (cotizador_can_access_partida(partida_id))
    WITH CHECK (cotizador_can_access_partida(partida_id));
CREATE POLICY cotizacion_partida_categorias_delete ON public.cotizacion_partida_categorias
    FOR DELETE TO authenticated
    USING (cotizador_can_access_partida(partida_id));

CREATE POLICY cotizacion_conceptos_select ON public.cotizacion_conceptos
    FOR SELECT TO authenticated
    USING (cotizador_can_access_partida(partida_id));
CREATE POLICY cotizacion_conceptos_insert ON public.cotizacion_conceptos
    FOR INSERT TO authenticated
    WITH CHECK (cotizador_can_access_partida(partida_id));
CREATE POLICY cotizacion_conceptos_update ON public.cotizacion_conceptos
    FOR UPDATE TO authenticated
    USING (cotizador_can_access_partida(partida_id))
    WITH CHECK (cotizador_can_access_partida(partida_id));
CREATE POLICY cotizacion_conceptos_delete ON public.cotizacion_conceptos
    FOR DELETE TO authenticated
    USING (cotizador_can_access_partida(partida_id));

CREATE POLICY cotizacion_concepto_valores_select ON public.cotizacion_concepto_valores
    FOR SELECT TO authenticated
    USING (
        cotizador_can_access_concepto(concepto_id)
        AND cotizador_can_access_partida_categoria(partida_categoria_id)
    );
CREATE POLICY cotizacion_concepto_valores_insert ON public.cotizacion_concepto_valores
    FOR INSERT TO authenticated
    WITH CHECK (
        cotizador_can_access_concepto(concepto_id)
        AND cotizador_can_access_partida_categoria(partida_categoria_id)
    );
CREATE POLICY cotizacion_concepto_valores_update ON public.cotizacion_concepto_valores
    FOR UPDATE TO authenticated
    USING (
        cotizador_can_access_concepto(concepto_id)
        AND cotizador_can_access_partida_categoria(partida_categoria_id)
    )
    WITH CHECK (
        cotizador_can_access_concepto(concepto_id)
        AND cotizador_can_access_partida_categoria(partida_categoria_id)
    );
CREATE POLICY cotizacion_concepto_valores_delete ON public.cotizacion_concepto_valores
    FOR DELETE TO authenticated
    USING (
        cotizador_can_access_concepto(concepto_id)
        AND cotizador_can_access_partida_categoria(partida_categoria_id)
    );

-- =============================================================================
-- ROLLBACK (ejecutar en orden inverso si se necesita revertir)
-- =============================================================================
-- DROP TABLE IF EXISTS public.cotizacion_concepto_valores CASCADE;
-- DROP TABLE IF EXISTS public.cotizacion_conceptos CASCADE;
-- DROP TABLE IF EXISTS public.cotizacion_partida_categorias CASCADE;
-- DROP TABLE IF EXISTS public.cotizacion_partidas CASCADE;
-- DROP TABLE IF EXISTS public.cotizaciones CASCADE;
-- DROP TABLE IF EXISTS public.configuracion_fiscal_empresa CASCADE;
-- DROP TYPE IF EXISTS tipo_valor_concepto_enum;
-- DROP TYPE IF EXISTS tipo_concepto_cotizacion_enum;
-- DROP TYPE IF EXISTS estatus_partida_cotizacion_enum;
-- DROP TYPE IF EXISTS estatus_cotizacion_enum;
