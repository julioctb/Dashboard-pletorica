-- Migración 041: Agregar columna activo a user_companies
-- Permite que admin_empresa desactive/reactive usuarios de su empresa
-- sin eliminar la relación usuario-empresa.

ALTER TABLE public.user_companies
ADD COLUMN IF NOT EXISTS activo BOOLEAN NOT NULL DEFAULT TRUE;

COMMENT ON COLUMN public.user_companies.activo IS
    'Indica si el usuario tiene acceso activo a esta empresa. '
    'False = desactivado por admin_empresa, no puede iniciar sesion en este contexto.';

CREATE INDEX IF NOT EXISTS idx_user_companies_empresa_activo
ON public.user_companies (empresa_id, activo);

-- Rollback:
-- ALTER TABLE public.user_companies DROP COLUMN IF EXISTS activo;
-- DROP INDEX IF EXISTS idx_user_companies_empresa_activo;
