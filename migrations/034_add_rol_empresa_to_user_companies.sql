-- ============================================================================
-- Migration: 034_add_rol_empresa_to_user_companies.sql
-- Fecha: 2026-02-23
-- Descripcion: Permisos granulares por empresa para pivot SaaS.
--   - Columna rol_empresa en user_companies (rol del usuario en CADA empresa)
--   - Actualiza constraint de user_profiles.rol para incluir 'superadmin' y 'empleado'
--   - NO migra roles existentes (admin sigue siendo admin por compatibilidad)
-- ============================================================================

-- 1. Agregar columna rol_empresa a user_companies
ALTER TABLE public.user_companies
  ADD COLUMN IF NOT EXISTS rol_empresa VARCHAR(30) NOT NULL DEFAULT 'lectura';

COMMENT ON COLUMN public.user_companies.rol_empresa IS
  'Rol del usuario en esta empresa: admin_empresa, rrhh, operaciones, contabilidad, lectura, validador_externo, empleado';

-- 2. Constraint de valores validos para rol_empresa
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'user_companies_rol_empresa_check'
    ) THEN
        ALTER TABLE public.user_companies
          ADD CONSTRAINT user_companies_rol_empresa_check
          CHECK (rol_empresa IN (
            'admin_empresa',
            'rrhh',
            'operaciones',
            'contabilidad',
            'lectura',
            'validador_externo',
            'empleado'
          ));
    END IF;
END $$;

-- 3. Indice en rol_empresa para queries frecuentes
CREATE INDEX IF NOT EXISTS idx_user_companies_rol_empresa
  ON public.user_companies (rol_empresa);

-- 4. Actualizar constraint de user_profiles.rol para incluir nuevos valores
--    Primero dropeamos el constraint existente y recreamos con los nuevos valores
DO $$
BEGIN
    -- Buscar y eliminar constraint CHECK existente en columna rol
    IF EXISTS (
        SELECT 1 FROM pg_constraint c
        JOIN pg_attribute a ON a.attnum = ANY(c.conkey) AND a.attrelid = c.conrelid
        WHERE c.conrelid = 'public.user_profiles'::regclass
          AND c.contype = 'c'
          AND a.attname = 'rol'
    ) THEN
        EXECUTE (
            SELECT 'ALTER TABLE public.user_profiles DROP CONSTRAINT ' || c.conname
            FROM pg_constraint c
            JOIN pg_attribute a ON a.attnum = ANY(c.conkey) AND a.attrelid = c.conrelid
            WHERE c.conrelid = 'public.user_profiles'::regclass
              AND c.contype = 'c'
              AND a.attname = 'rol'
            LIMIT 1
        );
    END IF;

    -- Recrear con valores ampliados
    ALTER TABLE public.user_profiles
      ADD CONSTRAINT user_profiles_rol_check
      CHECK (rol IN ('superadmin', 'admin', 'client', 'empleado'));
END $$;

COMMENT ON COLUMN public.user_profiles.rol IS
  'Rol global: superadmin (plataforma), admin (compat=superadmin), client (permisos en user_companies), empleado (autoservicio)';

-- 5. NO se migran datos existentes.
--    Los admins actuales conservan rol='admin' (es_admin y es_superadmin los reconocen).
--    Los clientes existentes conservan rol_empresa='lectura' (default).
--    Asignar rol_empresa manualmente segun necesidad:
--
--    UPDATE public.user_companies
--    SET rol_empresa = 'admin_empresa'
--    WHERE user_id = '<UUID_DEL_CLIENTE>' AND empresa_id = <ID_EMPRESA>;


-- ============================================================================
-- POST-MIGRACION
-- ============================================================================
-- Verificar que la migracion fue exitosa:
-- SELECT up.id, up.rol, uc.empresa_id, uc.rol_empresa
-- FROM user_profiles up
-- LEFT JOIN user_companies uc ON up.id = uc.user_id
-- ORDER BY up.rol, uc.rol_empresa;


-- ============================================================================
-- Rollback (if you need to revert)
-- ============================================================================
-- -- 1. Quitar columna rol_empresa (cascade elimina constraint e indice)
-- ALTER TABLE public.user_companies DROP COLUMN IF EXISTS rol_empresa;
--
-- -- 2. Restaurar constraint original de rol
-- ALTER TABLE public.user_profiles DROP CONSTRAINT IF EXISTS user_profiles_rol_check;
-- ALTER TABLE public.user_profiles
--   ADD CONSTRAINT user_profiles_rol_check CHECK (rol IN ('admin', 'client'));
