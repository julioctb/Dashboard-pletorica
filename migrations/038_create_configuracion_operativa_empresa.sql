-- =============================================================================
-- Migration 038: Crear tabla configuracion_operativa_empresa
-- =============================================================================
-- Descripcion: Configuracion operativa 1:1 con empresas. Controla parametros
--              de pago y bloqueo de cuentas bancarias.
-- Dependencias: 000_create_empresas
-- =============================================================================

-- 1. Crear tabla
CREATE TABLE IF NOT EXISTS public.configuracion_operativa_empresa (
    id SERIAL PRIMARY KEY,
    empresa_id INTEGER NOT NULL REFERENCES public.empresas(id) ON DELETE CASCADE,

    -- Bloqueo de cuenta bancaria antes de pago
    dias_bloqueo_cuenta_antes_pago INTEGER NOT NULL DEFAULT 3,

    -- Dias de pago de quincenas
    dia_pago_primera_quincena INTEGER NOT NULL DEFAULT 15,
    dia_pago_segunda_quincena INTEGER NOT NULL DEFAULT 0,

    -- Auditoria
    fecha_creacion TIMESTAMPTZ DEFAULT NOW(),
    fecha_actualizacion TIMESTAMPTZ DEFAULT NOW(),

    -- =================================================================
    -- CONSTRAINTS
    -- =================================================================

    -- Una config por empresa
    CONSTRAINT uq_config_operativa_empresa UNIQUE (empresa_id),

    -- Rangos validos
    CONSTRAINT chk_config_dias_bloqueo CHECK (
        dias_bloqueo_cuenta_antes_pago BETWEEN 1 AND 10
    ),
    CONSTRAINT chk_config_dia_primera_quincena CHECK (
        dia_pago_primera_quincena BETWEEN 1 AND 28
    ),
    CONSTRAINT chk_config_dia_segunda_quincena CHECK (
        dia_pago_segunda_quincena BETWEEN 0 AND 28
    )
);

-- 2. Indice
CREATE INDEX IF NOT EXISTS idx_config_operativa_empresa
    ON public.configuracion_operativa_empresa(empresa_id);

-- 3. Trigger fecha_actualizacion
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger
        WHERE tgname = 'set_fecha_actualizacion_config_operativa'
    ) THEN
        CREATE TRIGGER set_fecha_actualizacion_config_operativa
            BEFORE UPDATE ON public.configuracion_operativa_empresa
            FOR EACH ROW
            EXECUTE FUNCTION update_fecha_actualizacion();
    END IF;
END $$;

-- 4. Comments
COMMENT ON TABLE public.configuracion_operativa_empresa IS 'Configuracion operativa por empresa (1:1)';
COMMENT ON COLUMN public.configuracion_operativa_empresa.dias_bloqueo_cuenta_antes_pago IS 'Dias antes del pago en que se bloquean cambios bancarios (1-10)';
COMMENT ON COLUMN public.configuracion_operativa_empresa.dia_pago_primera_quincena IS 'Dia del mes para pago de primera quincena (1-28)';
COMMENT ON COLUMN public.configuracion_operativa_empresa.dia_pago_segunda_quincena IS 'Dia del mes para pago de segunda quincena (0=ultimo dia del mes, 1-28)';

-- =============================================================================
-- Rollback (comentado)
-- =============================================================================
-- DROP TABLE IF EXISTS public.configuracion_operativa_empresa;
