-- ============================================================================
-- Migration: 033_permisos_granulares.sql
-- Fecha: 2026-02-08
-- Descripcion: Sistema de permisos granulares por modulo para admins.
--   - Flag puede_gestionar_usuarios (super admin)
--   - JSONB permisos con matriz modulo x accion (operar/autorizar)
--   - Campos de tracking de revisiones en requisiciones y entregables
-- ============================================================================

-- 1. Agregar campos de permisos a user_profiles
ALTER TABLE public.user_profiles
  ADD COLUMN IF NOT EXISTS puede_gestionar_usuarios BOOLEAN NOT NULL DEFAULT false,
  ADD COLUMN IF NOT EXISTS permisos JSONB NOT NULL DEFAULT '{
    "requisiciones": {"operar": false, "autorizar": false},
    "entregables": {"operar": false, "autorizar": false},
    "pagos": {"operar": false, "autorizar": false},
    "contratos": {"operar": false, "autorizar": false},
    "empresas": {"operar": false, "autorizar": false},
    "empleados": {"operar": false, "autorizar": false}
  }'::jsonb;

COMMENT ON COLUMN public.user_profiles.puede_gestionar_usuarios IS
  'Si true, el admin puede crear/editar otros usuarios y asignar permisos (super admin)';
COMMENT ON COLUMN public.user_profiles.permisos IS
  'Matriz de permisos granulares: {modulo: {operar: bool, autorizar: bool}}';

-- 2. Requisiciones: tracking de revisiones (rechazo -> correccion -> reenvio)
ALTER TABLE public.requisiciones
  ADD COLUMN IF NOT EXISTS numero_revision INTEGER NOT NULL DEFAULT 0,
  ADD COLUMN IF NOT EXISTS ultimo_comentario_rechazo TEXT,
  ADD COLUMN IF NOT EXISTS rechazado_por UUID,
  ADD COLUMN IF NOT EXISTS fecha_ultimo_rechazo TIMESTAMPTZ;

COMMENT ON COLUMN public.requisiciones.numero_revision IS
  'Contador de veces que fue rechazada y corregida';
COMMENT ON COLUMN public.requisiciones.ultimo_comentario_rechazo IS
  'Comentario del ultimo rechazo (obligatorio al rechazar)';
COMMENT ON COLUMN public.requisiciones.rechazado_por IS
  'UUID del usuario que realizo el ultimo rechazo';
COMMENT ON COLUMN public.requisiciones.fecha_ultimo_rechazo IS
  'Timestamp del ultimo rechazo';

-- 3. Entregables: tracking de revisiones
ALTER TABLE public.entregables
  ADD COLUMN IF NOT EXISTS numero_revision INTEGER NOT NULL DEFAULT 0;

COMMENT ON COLUMN public.entregables.numero_revision IS
  'Contador de veces que fue rechazado y re-entregado';

-- 4. Actualizar trigger handle_new_user para incluir permisos default
--    (El trigger existente crea user_profiles al registrar un usuario en Auth)
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
    INSERT INTO public.user_profiles (
        id,
        rol,
        nombre_completo,
        telefono,
        activo,
        puede_gestionar_usuarios,
        permisos
    )
    VALUES (
        NEW.id,
        COALESCE(NEW.raw_user_meta_data->>'rol', 'client'),
        COALESCE(NEW.raw_user_meta_data->>'nombre_completo', 'Usuario'),
        NEW.raw_user_meta_data->>'telefono',
        true,
        false,
        '{
            "requisiciones": {"operar": false, "autorizar": false},
            "entregables": {"operar": false, "autorizar": false},
            "pagos": {"operar": false, "autorizar": false},
            "contratos": {"operar": false, "autorizar": false},
            "empresas": {"operar": false, "autorizar": false},
            "empleados": {"operar": false, "autorizar": false}
        }'::jsonb
    );
    RETURN NEW;
END;
$$;


-- ============================================================================
-- POST-MIGRACION: Dar permisos completos al primer admin existente
-- ============================================================================
-- IMPORTANTE: Ejecutar manualmente despues de la migracion.
-- Reemplazar '<UUID_DEL_ADMIN_ACTUAL>' con el UUID real del admin.
--
-- UPDATE public.user_profiles
-- SET puede_gestionar_usuarios = true,
--     permisos = '{
--       "requisiciones": {"operar": true, "autorizar": true},
--       "entregables": {"operar": true, "autorizar": true},
--       "pagos": {"operar": true, "autorizar": true},
--       "contratos": {"operar": true, "autorizar": true},
--       "empresas": {"operar": true, "autorizar": true},
--       "empleados": {"operar": true, "autorizar": true}
--     }'::jsonb
-- WHERE id = '<UUID_DEL_ADMIN_ACTUAL>';
-- ============================================================================


-- ============================================================================
-- Rollback (if you need to revert)
-- ============================================================================
-- ALTER TABLE public.user_profiles DROP COLUMN IF EXISTS puede_gestionar_usuarios;
-- ALTER TABLE public.user_profiles DROP COLUMN IF EXISTS permisos;
-- ALTER TABLE public.requisiciones DROP COLUMN IF EXISTS numero_revision;
-- ALTER TABLE public.requisiciones DROP COLUMN IF EXISTS ultimo_comentario_rechazo;
-- ALTER TABLE public.requisiciones DROP COLUMN IF EXISTS rechazado_por;
-- ALTER TABLE public.requisiciones DROP COLUMN IF EXISTS fecha_ultimo_rechazo;
-- ALTER TABLE public.entregables DROP COLUMN IF EXISTS numero_revision;
