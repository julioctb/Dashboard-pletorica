-- ============================================================================
-- Migration: 065_harden_auth_metadata_and_private_helpers.sql
-- Descripcion:
--   - Evita confiar en raw_user_meta_data para campos de autorizacion
--   - Mueve helpers privilegiados a esquema privado
--   - Mantiene wrappers publicos estables para no romper politicas existentes
-- ============================================================================

CREATE SCHEMA IF NOT EXISTS private;

REVOKE ALL ON SCHEMA private FROM PUBLIC;
GRANT USAGE ON SCHEMA private TO anon, authenticated, service_role;


-- ==========================================================================
-- Helpers privados para RLS / autorizacion
-- ==========================================================================

CREATE OR REPLACE FUNCTION private.get_user_companies()
RETURNS INTEGER[]
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = public
AS $$
    SELECT COALESCE(
        ARRAY_AGG(empresa_id),
        ARRAY[]::INTEGER[]
    )
    FROM public.user_companies
    WHERE user_id = auth.uid();
$$;

CREATE OR REPLACE FUNCTION private.is_admin()
RETURNS BOOLEAN
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = public
AS $$
    SELECT EXISTS (
        SELECT 1
        FROM public.user_profiles
        WHERE id = auth.uid()
          AND rol = 'admin'
          AND activo = true
    );
$$;

CREATE OR REPLACE FUNCTION private.can_access_archivo(
    p_entidad_tipo VARCHAR,
    p_entidad_id INTEGER
)
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
                  AND id = ANY(private.get_user_companies())
            )
            WHEN 'REQUISICION' THEN EXISTS (
                SELECT 1 FROM public.requisicion
                WHERE id = p_entidad_id
                  AND empresa_id = ANY(private.get_user_companies())
            )
            WHEN 'REQUISICION_ITEM' THEN EXISTS (
                SELECT 1
                FROM public.requisicion_item ri
                JOIN public.requisicion r ON ri.requisicion_id = r.id
                WHERE ri.id = p_entidad_id
                  AND r.empresa_id = ANY(private.get_user_companies())
            )
            WHEN 'CONTRATO' THEN EXISTS (
                SELECT 1 FROM public.contratos
                WHERE id = p_entidad_id
                  AND empresa_id = ANY(private.get_user_companies())
            )
            WHEN 'EMPLEADO' THEN EXISTS (
                SELECT 1 FROM public.empleados
                WHERE id = p_entidad_id
                  AND empresa_id = ANY(private.get_user_companies())
            )
            WHEN 'ENTREGABLE' THEN EXISTS (
                SELECT 1
                FROM public.entregables e
                JOIN public.contratos c ON e.contrato_id = c.id
                WHERE e.id = p_entidad_id
                  AND c.empresa_id = ANY(private.get_user_companies())
            )
            WHEN 'PAGO' THEN EXISTS (
                SELECT 1
                FROM public.pagos p
                JOIN public.contratos c ON p.contrato_id = c.id
                WHERE p.id = p_entidad_id
                  AND c.empresa_id = ANY(private.get_user_companies())
            )
            WHEN 'REPORTE' THEN false
            WHEN 'REPORTE_ACTIVIDAD' THEN false
            ELSE false
        END;
$$;

CREATE OR REPLACE FUNCTION private.handle_new_user()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
    v_nombre_completo VARCHAR(150);
    v_telefono VARCHAR(10);
BEGIN
    v_nombre_completo := COALESCE(
        NEW.raw_user_meta_data->>'nombre_completo',
        NEW.raw_user_meta_data->>'full_name',
        'Usuario sin nombre'
    );

    v_telefono := NEW.raw_user_meta_data->>'telefono';
    IF v_telefono IS NOT NULL AND v_telefono !~ '^\d{10}$' THEN
        v_telefono := NULL;
    END IF;

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
        'client',
        v_nombre_completo,
        v_telefono,
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

GRANT EXECUTE ON FUNCTION private.get_user_companies() TO anon, authenticated, service_role;
GRANT EXECUTE ON FUNCTION private.is_admin() TO anon, authenticated, service_role;
GRANT EXECUTE ON FUNCTION private.can_access_archivo(VARCHAR, INTEGER) TO anon, authenticated, service_role;


-- ==========================================================================
-- Wrappers publicos sin privilegios especiales para compatibilidad
-- ==========================================================================

CREATE OR REPLACE FUNCTION public.get_user_companies()
RETURNS INTEGER[]
LANGUAGE sql
STABLE
SET search_path = public, private
AS $$
    SELECT private.get_user_companies();
$$;

CREATE OR REPLACE FUNCTION public.is_admin()
RETURNS BOOLEAN
LANGUAGE sql
STABLE
SET search_path = public, private
AS $$
    SELECT private.is_admin();
$$;

CREATE OR REPLACE FUNCTION public.can_access_archivo(
    p_entidad_tipo VARCHAR,
    p_entidad_id INTEGER
)
RETURNS BOOLEAN
LANGUAGE sql
STABLE
SET search_path = public, private
AS $$
    SELECT private.can_access_archivo(p_entidad_tipo, p_entidad_id);
$$;


-- ==========================================================================
-- Reasignar trigger de auth.users al helper privado endurecido
-- ==========================================================================

DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW
    EXECUTE FUNCTION private.handle_new_user();
