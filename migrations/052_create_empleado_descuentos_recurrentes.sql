-- =============================================================================
-- Migración 052: Descuentos recurrentes configurables por empleado
--
-- Cambios:
--   - Crea tabla maestra de descuentos recurrentes ligados al empleado
--   - Soporta INFONAVIT, FONACOT, PRESTAMO_EMPRESA y PENSION_ALIMENTICIA
--   - Mantiene timestamps con trigger genérico de fecha_actualizacion
-- =============================================================================

CREATE TABLE IF NOT EXISTS public.empleado_descuentos_recurrentes (
    id BIGSERIAL PRIMARY KEY,
    empleado_id INTEGER NOT NULL REFERENCES public.empleados(id) ON DELETE CASCADE,
    concepto_clave VARCHAR(50) NOT NULL,
    monto_periodico NUMERIC(12, 2) NOT NULL,
    fecha_inicio DATE NOT NULL,
    fecha_fin DATE,
    notas VARCHAR(500),
    fecha_creacion TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    fecha_actualizacion TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_empleado_descuentos_recurrentes_empleado_concepto
        UNIQUE (empleado_id, concepto_clave),
    CONSTRAINT chk_empleado_descuentos_recurrentes_concepto
        CHECK (
            concepto_clave IN (
                'DESCUENTO_INFONAVIT',
                'DESCUENTO_FONACOT',
                'PRESTAMO_EMPRESA',
                'PENSION_ALIMENTICIA'
            )
        ),
    CONSTRAINT chk_empleado_descuentos_recurrentes_monto
        CHECK (monto_periodico > 0),
    CONSTRAINT chk_empleado_descuentos_recurrentes_fechas
        CHECK (fecha_fin IS NULL OR fecha_fin >= fecha_inicio)
);

CREATE INDEX IF NOT EXISTS idx_empleado_descuentos_recurrentes_empleado
    ON public.empleado_descuentos_recurrentes (empleado_id);

CREATE INDEX IF NOT EXISTS idx_empleado_descuentos_recurrentes_vigencia
    ON public.empleado_descuentos_recurrentes (fecha_inicio, fecha_fin);

COMMENT ON TABLE public.empleado_descuentos_recurrentes IS
'Configuracion maestra de descuentos recurrentes del empleado usada como fuente de verdad para prefijar la nomina.';

COMMENT ON COLUMN public.empleado_descuentos_recurrentes.concepto_clave IS
'Clave del concepto de deduccion soportado por el perfil del empleado.';

COMMENT ON COLUMN public.empleado_descuentos_recurrentes.monto_periodico IS
'Monto fijo sugerido por periodo de nomina para el descuento recurrente.';

COMMENT ON COLUMN public.empleado_descuentos_recurrentes.fecha_inicio IS
'Inicio de vigencia del descuento recurrente. Siempre se persiste de forma explicita.';

COMMENT ON COLUMN public.empleado_descuentos_recurrentes.fecha_fin IS
'Fin de vigencia del descuento. NULL indica vigencia indefinida.';

DROP TRIGGER IF EXISTS trg_empleado_descuentos_recurrentes_upd
    ON public.empleado_descuentos_recurrentes;

CREATE TRIGGER trg_empleado_descuentos_recurrentes_upd
    BEFORE UPDATE ON public.empleado_descuentos_recurrentes
    FOR EACH ROW EXECUTE FUNCTION public.set_fecha_actualizacion();
