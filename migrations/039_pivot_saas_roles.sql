-- ============================================================================
-- Migration: 039_pivot_saas_roles.sql
-- Fecha: 2026-02-23
-- Descripcion: Pivot SaaS completo de permisos.
--   1. Crea tabla instituciones (catalogo de clientes institucionales)
--   2. Crea tabla instituciones_empresas (que empresas supervisa cada institucion)
--   3. Agrega institucion_id a user_profiles (solo para rol='institucion')
--   4. Actualiza constraints de user_profiles.rol (nuevos valores SaaS)
--   5. Actualiza constraints de user_companies.rol_empresa (sin gestor_institucional)
--   6. Migra datos existentes de clients a admin_empresa
-- Dependencias: 034_add_rol_empresa_to_user_companies
-- ============================================================================

-- ============================================================================
-- 1. Crear tabla instituciones
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.instituciones (
    id          SERIAL PRIMARY KEY,
    nombre      VARCHAR(200) NOT NULL,
    codigo      VARCHAR(20) NOT NULL UNIQUE,
    activo      BOOLEAN NOT NULL DEFAULT TRUE,
    fecha_creacion      TIMESTAMPTZ DEFAULT NOW(),
    fecha_actualizacion TIMESTAMPTZ DEFAULT NOW()
);

COMMENT ON TABLE public.instituciones IS
  'Catalogo de instituciones cliente (BUAP, Gobierno, etc.) que supervisan empresas proveedoras';
COMMENT ON COLUMN public.instituciones.codigo IS
  'Codigo corto unico (ej: BUAP, GOB-PUE)';

-- Trigger fecha_actualizacion
CREATE OR REPLACE TRIGGER trigger_instituciones_fecha_actualizacion
    BEFORE UPDATE ON public.instituciones
    FOR EACH ROW
    EXECUTE FUNCTION update_fecha_actualizacion();

-- Indices
CREATE INDEX IF NOT EXISTS idx_instituciones_codigo
    ON public.instituciones(codigo);
CREATE INDEX IF NOT EXISTS idx_instituciones_activo
    ON public.instituciones(activo);

-- Seed: BUAP como primera institucion
INSERT INTO public.instituciones (nombre, codigo)
VALUES ('Benemerita Universidad Autonoma de Puebla', 'BUAP')
ON CONFLICT (codigo) DO NOTHING;

-- ============================================================================
-- 2. Crear tabla instituciones_empresas (join table)
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.instituciones_empresas (
    id              SERIAL PRIMARY KEY,
    institucion_id  INTEGER NOT NULL REFERENCES public.instituciones(id) ON DELETE CASCADE,
    empresa_id      INTEGER NOT NULL REFERENCES public.empresas(id) ON DELETE CASCADE,
    fecha_creacion  TIMESTAMPTZ DEFAULT NOW(),

    -- Un registro unico por par institucion-empresa
    CONSTRAINT uq_institucion_empresa UNIQUE (institucion_id, empresa_id)
);

COMMENT ON TABLE public.instituciones_empresas IS
  'Relacion N:M entre instituciones y empresas. Define que empresas supervisa cada institucion.';

-- Indices
CREATE INDEX IF NOT EXISTS idx_instituciones_empresas_institucion
    ON public.instituciones_empresas(institucion_id);
CREATE INDEX IF NOT EXISTS idx_instituciones_empresas_empresa
    ON public.instituciones_empresas(empresa_id);

-- Seed: Asignar todas las empresas activas a BUAP
INSERT INTO public.instituciones_empresas (institucion_id, empresa_id)
SELECT
    (SELECT id FROM public.instituciones WHERE codigo = 'BUAP'),
    e.id
FROM public.empresas e
WHERE e.estatus = 'ACTIVO'
ON CONFLICT (institucion_id, empresa_id) DO NOTHING;

-- ============================================================================
-- 3. Agregar institucion_id a user_profiles
-- ============================================================================

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public'
        AND table_name = 'user_profiles'
        AND column_name = 'institucion_id'
    ) THEN
        ALTER TABLE public.user_profiles
            ADD COLUMN institucion_id INTEGER
            REFERENCES public.instituciones(id) ON DELETE SET NULL;
    END IF;
END $$;

COMMENT ON COLUMN public.user_profiles.institucion_id IS
  'FK a instituciones. Solo aplica cuando rol=institucion. NULL para otros roles.';

CREATE INDEX IF NOT EXISTS idx_user_profiles_institucion_id
    ON public.user_profiles(institucion_id)
    WHERE institucion_id IS NOT NULL;

-- ============================================================================
-- 4. Actualizar constraint de user_profiles.rol
-- ============================================================================

DO $$
BEGIN
    -- Eliminar constraint existente
    IF EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'user_profiles_rol_check'
        AND conrelid = 'public.user_profiles'::regclass
    ) THEN
        ALTER TABLE public.user_profiles DROP CONSTRAINT user_profiles_rol_check;
    END IF;

    -- Recrear con valores completos del pivot SaaS
    ALTER TABLE public.user_profiles
      ADD CONSTRAINT user_profiles_rol_check
      CHECK (rol IN (
        'superadmin',    -- Dueno de la plataforma SaaS
        'admin',         -- Compatibilidad (equivale a superadmin)
        'institucion',   -- Personal de institucion cliente (requiere institucion_id)
        'proveedor',     -- Personal de empresa proveedora (usa user_companies)
        'client',        -- Compatibilidad (equivale a proveedor)
        'empleado'       -- Trabajador con autoservicio
      ));
END $$;

COMMENT ON COLUMN public.user_profiles.rol IS
  'Tipo de organizacion: superadmin/admin (plataforma), institucion (requiere institucion_id), proveedor/client (empresa via user_companies), empleado (autoservicio)';

-- ============================================================================
-- 5. Actualizar constraint de user_companies.rol_empresa
--    SIN gestor_institucional (instituciones usan instituciones_empresas)
-- ============================================================================

DO $$
BEGIN
    -- Migrar datos existentes: gestor_institucional -> lectura (por si existieran)
    UPDATE public.user_companies
    SET rol_empresa = 'lectura'
    WHERE rol_empresa IN ('validador_externo', 'gestor_institucional');

    -- Eliminar constraint existente
    IF EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'user_companies_rol_empresa_check'
        AND conrelid = 'public.user_companies'::regclass
    ) THEN
        ALTER TABLE public.user_companies DROP CONSTRAINT user_companies_rol_empresa_check;
    END IF;

    -- Recrear SIN gestor_institucional (solo roles de proveedor + empleado)
    ALTER TABLE public.user_companies
      ADD CONSTRAINT user_companies_rol_empresa_check
      CHECK (rol_empresa IN (
        'admin_empresa',
        'rrhh',
        'operaciones',
        'contabilidad',
        'lectura',
        'empleado'
      ));
END $$;

COMMENT ON COLUMN public.user_companies.rol_empresa IS
  'Rol del usuario en esta empresa: admin_empresa, rrhh, operaciones, contabilidad, lectura, empleado. Usuarios institucionales NO usan esta tabla.';

-- ============================================================================
-- 6. Migrar user_companies de clients existentes a admin_empresa
-- ============================================================================

UPDATE public.user_companies uc
SET rol_empresa = 'admin_empresa'
WHERE uc.rol_empresa = 'lectura'
  AND EXISTS (
    SELECT 1 FROM public.user_profiles up
    WHERE up.id = uc.user_id
    AND up.rol = 'client'
  );

-- ============================================================================
-- 7. Indice en user_profiles.rol (si no existe)
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_user_profiles_rol
  ON public.user_profiles(rol);

-- ============================================================================
-- 8. RLS para instituciones e instituciones_empresas
-- ============================================================================

ALTER TABLE public.instituciones ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.instituciones_empresas ENABLE ROW LEVEL SECURITY;

-- instituciones: lectura para todos los autenticados, escritura solo admin
DO $$
BEGIN
    DROP POLICY IF EXISTS instituciones_select_policy ON public.instituciones;
    CREATE POLICY instituciones_select_policy ON public.instituciones
        FOR SELECT USING (true);

    DROP POLICY IF EXISTS instituciones_insert_policy ON public.instituciones;
    CREATE POLICY instituciones_insert_policy ON public.instituciones
        FOR INSERT WITH CHECK (is_admin());

    DROP POLICY IF EXISTS instituciones_update_policy ON public.instituciones;
    CREATE POLICY instituciones_update_policy ON public.instituciones
        FOR UPDATE USING (is_admin());

    DROP POLICY IF EXISTS instituciones_delete_policy ON public.instituciones;
    CREATE POLICY instituciones_delete_policy ON public.instituciones
        FOR DELETE USING (is_admin());
END $$;

-- instituciones_empresas: lectura para autenticados, escritura solo admin
DO $$
BEGIN
    DROP POLICY IF EXISTS inst_emp_select_policy ON public.instituciones_empresas;
    CREATE POLICY inst_emp_select_policy ON public.instituciones_empresas
        FOR SELECT USING (true);

    DROP POLICY IF EXISTS inst_emp_insert_policy ON public.instituciones_empresas;
    CREATE POLICY inst_emp_insert_policy ON public.instituciones_empresas
        FOR INSERT WITH CHECK (is_admin());

    DROP POLICY IF EXISTS inst_emp_update_policy ON public.instituciones_empresas;
    CREATE POLICY inst_emp_update_policy ON public.instituciones_empresas
        FOR UPDATE USING (is_admin());

    DROP POLICY IF EXISTS inst_emp_delete_policy ON public.instituciones_empresas;
    CREATE POLICY inst_emp_delete_policy ON public.instituciones_empresas
        FOR DELETE USING (is_admin());
END $$;

-- ============================================================================
-- POST-MIGRACION: Verificar
-- ============================================================================
-- SELECT i.nombre, i.codigo, COUNT(ie.empresa_id) as empresas
-- FROM instituciones i
-- LEFT JOIN instituciones_empresas ie ON i.id = ie.institucion_id
-- GROUP BY i.id;
--
-- SELECT up.id, up.nombre_completo, up.rol, up.institucion_id, uc.empresa_id, uc.rol_empresa
-- FROM user_profiles up
-- LEFT JOIN user_companies uc ON up.id = uc.user_id
-- ORDER BY up.rol, uc.rol_empresa;

-- ============================================================================
-- Rollback (comentado)
-- ============================================================================
-- DROP TABLE IF EXISTS public.instituciones_empresas;
-- DROP TABLE IF EXISTS public.instituciones;
-- ALTER TABLE public.user_profiles DROP COLUMN IF EXISTS institucion_id;
--
-- ALTER TABLE public.user_profiles DROP CONSTRAINT IF EXISTS user_profiles_rol_check;
-- ALTER TABLE public.user_profiles
--   ADD CONSTRAINT user_profiles_rol_check
--   CHECK (rol IN ('superadmin', 'admin', 'client', 'empleado'));
--
-- ALTER TABLE public.user_companies DROP CONSTRAINT IF EXISTS user_companies_rol_empresa_check;
-- ALTER TABLE public.user_companies
--   ADD CONSTRAINT user_companies_rol_empresa_check
--   CHECK (rol_empresa IN ('admin_empresa','rrhh','operaciones','contabilidad','lectura','validador_externo','empleado'));
