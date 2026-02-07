-- ============================================================================
-- Migration: Create Notificaciones Table
-- Fecha: 2026-02-06
-- Descripcion: Sistema de notificaciones persistente para el flujo de
--              facturacion y otros eventos del sistema.
-- Depende de: 015_create_user_auth_tables.sql (auth.users)
-- ============================================================================

-- 1. Crear tabla de notificaciones
CREATE TABLE IF NOT EXISTS public.notificaciones (
    id SERIAL PRIMARY KEY,
    usuario_id UUID REFERENCES auth.users(id),
    empresa_id INTEGER REFERENCES public.empresas(id),
    titulo VARCHAR(200) NOT NULL,
    mensaje VARCHAR(1000) NOT NULL,
    tipo VARCHAR(50) NOT NULL,
    entidad_tipo VARCHAR(50),
    entidad_id INTEGER,
    leida BOOLEAN DEFAULT FALSE,
    fecha_creacion TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2. Indices para consultas frecuentes
CREATE INDEX IF NOT EXISTS idx_notificaciones_usuario
ON public.notificaciones (usuario_id, leida);

CREATE INDEX IF NOT EXISTS idx_notificaciones_empresa
ON public.notificaciones (empresa_id, leida);

CREATE INDEX IF NOT EXISTS idx_notificaciones_fecha
ON public.notificaciones (fecha_creacion DESC);

-- 3. Comentarios
COMMENT ON TABLE public.notificaciones IS 'Notificaciones del sistema para usuarios (admin y clientes)';
COMMENT ON COLUMN public.notificaciones.usuario_id IS 'UUID del usuario destinatario (puede ser NULL si es por empresa)';
COMMENT ON COLUMN public.notificaciones.empresa_id IS 'ID de la empresa destinataria (para notificaciones a todos los usuarios de una empresa)';
COMMENT ON COLUMN public.notificaciones.tipo IS 'Tipo de notificacion: entregable_aprobado, prefactura_rechazada, factura_recibida, pago_registrado, etc.';
COMMENT ON COLUMN public.notificaciones.entidad_tipo IS 'Tipo de entidad relacionada: ENTREGABLE, PAGO, etc.';
COMMENT ON COLUMN public.notificaciones.entidad_id IS 'ID de la entidad relacionada';

-- 4. RLS (Row Level Security)
ALTER TABLE public.notificaciones ENABLE ROW LEVEL SECURITY;

-- Admin ve todas las notificaciones
CREATE POLICY notificaciones_admin_select ON public.notificaciones
    FOR SELECT TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM public.user_profiles
            WHERE user_profiles.user_id = auth.uid()
            AND user_profiles.rol = 'admin'
        )
    );

-- Admin puede insertar notificaciones
CREATE POLICY notificaciones_admin_insert ON public.notificaciones
    FOR INSERT TO authenticated
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM public.user_profiles
            WHERE user_profiles.user_id = auth.uid()
            AND user_profiles.rol = 'admin'
        )
    );

-- Cliente ve sus propias notificaciones (por usuario_id o por empresa_id)
CREATE POLICY notificaciones_client_select ON public.notificaciones
    FOR SELECT TO authenticated
    USING (
        usuario_id = auth.uid()
        OR empresa_id IN (
            SELECT empresa_id FROM public.user_companies
            WHERE user_id = auth.uid()
        )
    );

-- Cualquier usuario autenticado puede marcar como leida sus notificaciones
CREATE POLICY notificaciones_update_leida ON public.notificaciones
    FOR UPDATE TO authenticated
    USING (
        usuario_id = auth.uid()
        OR empresa_id IN (
            SELECT empresa_id FROM public.user_companies
            WHERE user_id = auth.uid()
        )
    )
    WITH CHECK (
        usuario_id = auth.uid()
        OR empresa_id IN (
            SELECT empresa_id FROM public.user_companies
            WHERE user_id = auth.uid()
        )
    );

-- Service role bypass (para que el backend pueda insertar sin restriccion)
CREATE POLICY notificaciones_service_all ON public.notificaciones
    FOR ALL TO service_role
    USING (true)
    WITH CHECK (true);

-- ============================================================================
-- Rollback (if you need to revert)
-- ============================================================================
-- DROP POLICY IF EXISTS notificaciones_service_all ON public.notificaciones;
-- DROP POLICY IF EXISTS notificaciones_update_leida ON public.notificaciones;
-- DROP POLICY IF EXISTS notificaciones_client_select ON public.notificaciones;
-- DROP POLICY IF EXISTS notificaciones_admin_insert ON public.notificaciones;
-- DROP POLICY IF EXISTS notificaciones_admin_select ON public.notificaciones;
-- DROP TABLE IF EXISTS public.notificaciones;
