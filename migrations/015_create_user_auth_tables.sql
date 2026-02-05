-- ============================================================================
-- Migración 013: Sistema de autenticación de usuarios
-- ============================================================================
-- Ejecutar en Supabase SQL Editor
--
-- Esta migración crea la infraestructura para autenticación multi-empresa:
-- 1. Tabla user_profiles: Extiende auth.users con datos de la aplicación
-- 2. Tabla user_companies: Relación muchos-a-muchos usuario-empresa
-- 3. Funciones helper para RLS: get_user_companies(), is_admin()
-- 4. Trigger: Auto-crea profile cuando Supabase Auth registra un usuario
-- 5. Políticas RLS: Control de acceso a nivel de fila
--
-- IMPORTANTE: Ejecutar DESPUÉS de tener la tabla 'empresas' creada
-- ============================================================================


-- ============================================================================
-- SECCIÓN 1: TABLA user_profiles
-- ============================================================================
-- Extiende la tabla auth.users de Supabase con datos específicos de nuestra app.
-- Usamos el mismo UUID de auth.users como PK para relación 1:1 directa.
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.user_profiles (
    -- PK que referencia a auth.users (relación 1:1)
    -- Cuando Supabase Auth crea un usuario, el trigger crea el profile con el mismo ID
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    
    -- Rol en el sistema: 'admin' (personal BUAP) o 'client' (usuario de empresa proveedora)
    -- DEFAULT 'client' porque es el caso más común (menos privilegios por defecto)
    rol VARCHAR(20) NOT NULL DEFAULT 'client'
        CONSTRAINT chk_user_profiles_rol CHECK (rol IN ('admin', 'client')),
    
    -- Nombre completo del usuario (requerido para identificación)
    nombre_completo VARCHAR(150) NOT NULL,
    
    -- Teléfono en formato mexicano (10 dígitos) o NULL si no se proporciona
    -- El CHECK valida que si hay valor, sean exactamente 10 dígitos
    telefono VARCHAR(10)
        CONSTRAINT chk_user_profiles_telefono CHECK (
            telefono IS NULL OR telefono ~ '^\d{10}$'
        ),
    
    -- Permite desactivar usuarios sin eliminarlos (soft delete pattern)
    -- Útil para auditoría y para poder reactivar si es necesario
    activo BOOLEAN NOT NULL DEFAULT true,
    
    -- Se actualiza cada vez que el usuario inicia sesión
    -- Útil para detectar cuentas inactivas o para auditoría de seguridad
    ultimo_acceso TIMESTAMP WITH TIME ZONE,
    
    -- Auditoría estándar (consistente con otras tablas del sistema)
    fecha_creacion TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    fecha_actualizacion TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Comentarios de documentación para la tabla y columnas
COMMENT ON TABLE public.user_profiles IS 
    'Perfiles de usuario que extienden auth.users con datos de la aplicación';
COMMENT ON COLUMN public.user_profiles.id IS 
    'UUID del usuario en auth.users (relación 1:1)';
COMMENT ON COLUMN public.user_profiles.rol IS 
    'Rol del usuario: admin (BUAP) o client (empresa proveedora)';
COMMENT ON COLUMN public.user_profiles.activo IS 
    'false permite desactivar sin eliminar (soft delete)';


-- ============================================================================
-- SECCIÓN 2: TABLA user_companies
-- ============================================================================
-- Tabla intermedia para la relación muchos-a-muchos entre usuarios y empresas.
-- Un usuario puede pertenecer a múltiples empresas (ej: admin que supervisa varias).
-- Una empresa puede tener múltiples usuarios (ej: varios empleados con acceso).
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.user_companies (
    id SERIAL PRIMARY KEY,
    
    -- FK al perfil del usuario
    -- ON DELETE CASCADE: Si se elimina el profile, se eliminan sus asociaciones
    user_id UUID NOT NULL REFERENCES public.user_profiles(id) ON DELETE CASCADE,
    
    -- FK a la empresa
    -- ON DELETE CASCADE: Si se elimina la empresa, se eliminan las asociaciones
    empresa_id INTEGER NOT NULL REFERENCES public.empresas(id) ON DELETE CASCADE,
    
    -- Indica cuál empresa mostrar por defecto al hacer login
    -- Solo UNA empresa puede ser principal por usuario (ver índice único abajo)
    es_principal BOOLEAN NOT NULL DEFAULT false,
    
    -- Cuándo se creó esta asociación (auditoría)
    fecha_creacion TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    
    -- Un usuario no puede estar asociado dos veces a la misma empresa
    CONSTRAINT uk_user_companies_user_empresa UNIQUE (user_id, empresa_id)
);

-- Índice único parcial: Solo puede existir UNA fila con es_principal=true por usuario
-- Esto es más eficiente que un trigger y PostgreSQL lo garantiza a nivel de BD
CREATE UNIQUE INDEX idx_user_companies_principal 
    ON public.user_companies (user_id) 
    WHERE es_principal = true;

-- Índices para optimizar queries frecuentes
CREATE INDEX idx_user_companies_user_id ON public.user_companies(user_id);
CREATE INDEX idx_user_companies_empresa_id ON public.user_companies(empresa_id);

COMMENT ON TABLE public.user_companies IS 
    'Relación muchos-a-muchos entre usuarios y empresas';
COMMENT ON COLUMN public.user_companies.es_principal IS 
    'Empresa que se muestra por defecto al login (solo una por usuario)';


-- ============================================================================
-- SECCIÓN 3: TRIGGERS DE AUDITORÍA
-- ============================================================================
-- Reutilizamos la función existente update_fecha_actualizacion para mantener
-- actualizado el campo fecha_actualizacion automáticamente.
-- ============================================================================

-- Trigger para user_profiles (usa función existente)
CREATE TRIGGER trg_user_profiles_fecha_actualizacion
    BEFORE UPDATE ON public.user_profiles
    FOR EACH ROW
    EXECUTE FUNCTION public.update_fecha_actualizacion();


-- ============================================================================
-- SECCIÓN 4: FUNCIONES HELPER PARA RLS
-- ============================================================================
-- Estas funciones encapsulan la lógica de autorización para uso en políticas RLS.
-- Al estar en funciones separadas:
-- 1. Las políticas son más legibles
-- 2. La lógica se puede modificar sin cambiar las políticas
-- 3. PostgreSQL puede cachear resultados (marcadas como STABLE)
-- ============================================================================

-- Función: Obtener IDs de empresas del usuario actual
-- Retorna array vacío si no está autenticado o no tiene empresas asignadas
CREATE OR REPLACE FUNCTION public.get_user_companies()
RETURNS INTEGER[]
LANGUAGE sql
STABLE          -- Indica que la función retorna el mismo resultado para los mismos
SECURITY DEFINER -- inputs dentro de una transacción (permite optimización)
SET search_path = public
AS $$
    SELECT COALESCE(
        ARRAY_AGG(empresa_id),
        ARRAY[]::INTEGER[]  -- Array vacío si no hay resultados
    )
    FROM public.user_companies
    WHERE user_id = auth.uid();  -- auth.uid() retorna el UUID del usuario autenticado
$$;

COMMENT ON FUNCTION public.get_user_companies() IS 
    'Retorna array de empresa_id a las que el usuario actual tiene acceso';


-- Función: Verificar si el usuario actual es admin
-- Retorna false si no está autenticado o si es client
CREATE OR REPLACE FUNCTION public.is_admin()
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
          AND activo = true  -- Un admin inactivo no tiene privilegios de admin
    );
$$;

COMMENT ON FUNCTION public.is_admin() IS 
    'Retorna true si el usuario actual tiene rol admin y está activo';


-- ============================================================================
-- SECCIÓN 5: TRIGGER DE AUTO-CREACIÓN DE PROFILE
-- ============================================================================
-- Cuando Supabase Auth crea un usuario (via signUp, invitación, o admin),
-- este trigger automáticamente crea el registro correspondiente en user_profiles.
-- 
-- Los datos se extraen de raw_user_meta_data, que se puede pasar al crear el usuario:
-- supabase.auth.admin.create_user({
--     email: "...",
--     password: "...",
--     user_metadata: { nombre_completo: "Juan Pérez", rol: "client", telefono: "5512345678" }
-- })
-- ============================================================================

CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
    v_nombre_completo VARCHAR(150);
    v_rol VARCHAR(20);
    v_telefono VARCHAR(10);
BEGIN
    -- Extraer datos del metadata (con valores por defecto si no existen)
    v_nombre_completo := COALESCE(
        NEW.raw_user_meta_data->>'nombre_completo',
        NEW.raw_user_meta_data->>'full_name',  -- Fallback por si usan inglés
        'Usuario sin nombre'
    );
    
    v_rol := COALESCE(
        NEW.raw_user_meta_data->>'rol',
        NEW.raw_user_meta_data->>'role',  -- Fallback por si usan inglés
        'client'  -- Default: menor privilegio
    );
    
    -- Validar que el rol sea válido
    IF v_rol NOT IN ('admin', 'client') THEN
        v_rol := 'client';
    END IF;
    
    -- Extraer teléfono (puede ser NULL)
    v_telefono := NEW.raw_user_meta_data->>'telefono';
    
    -- Validar formato de teléfono (10 dígitos o NULL)
    IF v_telefono IS NOT NULL AND v_telefono !~ '^\d{10}$' THEN
        v_telefono := NULL;  -- Ignorar teléfono inválido en lugar de fallar
    END IF;
    
    -- Crear el profile
    INSERT INTO public.user_profiles (id, rol, nombre_completo, telefono)
    VALUES (NEW.id, v_rol, v_nombre_completo, v_telefono);
    
    RETURN NEW;
END;
$$;

COMMENT ON FUNCTION public.handle_new_user() IS 
    'Trigger que auto-crea user_profile cuando se registra un usuario en auth.users';

-- Asociar trigger a la tabla auth.users
-- NOTA: Supabase permite triggers en auth.users desde el Dashboard
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW
    EXECUTE FUNCTION public.handle_new_user();


-- ============================================================================
-- SECCIÓN 6: HABILITAR ROW LEVEL SECURITY (RLS)
-- ============================================================================
-- RLS está deshabilitado por defecto. Al habilitarlo, TODAS las operaciones
-- son bloqueadas hasta que se definan políticas explícitas.
-- ============================================================================

ALTER TABLE public.user_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.user_companies ENABLE ROW LEVEL SECURITY;


-- ============================================================================
-- SECCIÓN 7: POLÍTICAS RLS PARA user_profiles
-- ============================================================================
-- Reglas:
-- - SELECT: Usuarios ven solo su propio perfil. Admins ven todos.
-- - UPDATE: Usuarios pueden actualizar solo su propio perfil. Admins cualquiera.
-- - INSERT: Solo el trigger del sistema (no se permite INSERT directo vía API).
-- - DELETE: Solo admins pueden eliminar perfiles.
-- ============================================================================

-- SELECT: Cada usuario ve su propio perfil, admins ven todos
CREATE POLICY "Usuarios ven su propio perfil"
    ON public.user_profiles
    FOR SELECT
    USING (
        id = auth.uid()  -- Usuario ve su propio perfil
        OR is_admin()    -- O es admin y ve todos
    );

-- UPDATE: Cada usuario actualiza su propio perfil, admins actualizan cualquiera
CREATE POLICY "Usuarios actualizan su propio perfil"
    ON public.user_profiles
    FOR UPDATE
    USING (
        id = auth.uid()
        OR is_admin()
    )
    WITH CHECK (
        id = auth.uid()
        OR is_admin()
    );

-- INSERT: Solo el sistema (trigger) puede insertar
-- Los usuarios se crean a través de Supabase Auth, no directamente
CREATE POLICY "Solo sistema puede insertar profiles"
    ON public.user_profiles
    FOR INSERT
    WITH CHECK (false);  -- Bloquea INSERT directo; el trigger usa SECURITY DEFINER

-- DELETE: Solo admins pueden eliminar perfiles
CREATE POLICY "Solo admins eliminan profiles"
    ON public.user_profiles
    FOR DELETE
    USING (is_admin());


-- ============================================================================
-- SECCIÓN 8: POLÍTICAS RLS PARA user_companies
-- ============================================================================
-- Reglas:
-- - SELECT: Usuarios ven sus propias asociaciones. Admins ven todas.
-- - INSERT/UPDATE/DELETE: Solo admins pueden gestionar asociaciones.
-- ============================================================================

-- SELECT: Cada usuario ve sus asociaciones, admins ven todas
CREATE POLICY "Usuarios ven sus propias empresas"
    ON public.user_companies
    FOR SELECT
    USING (
        user_id = auth.uid()
        OR is_admin()
    );

-- INSERT: Solo admins pueden crear asociaciones usuario-empresa
CREATE POLICY "Solo admins asignan empresas a usuarios"
    ON public.user_companies
    FOR INSERT
    WITH CHECK (is_admin());

-- UPDATE: Solo admins pueden modificar asociaciones
CREATE POLICY "Solo admins modifican asignaciones"
    ON public.user_companies
    FOR UPDATE
    USING (is_admin())
    WITH CHECK (is_admin());

-- DELETE: Solo admins pueden eliminar asociaciones
CREATE POLICY "Solo admins eliminan asignaciones"
    ON public.user_companies
    FOR DELETE
    USING (is_admin());


-- ============================================================================
-- SECCIÓN 9: DATOS INICIALES (OPCIONAL)
-- ============================================================================
-- Descomenta este bloque para crear un usuario admin inicial de prueba.
-- IMPORTANTE: Cambia el email y genera una contraseña segura.
-- 
-- NOTA: Este INSERT debe ejecutarse DESPUÉS de crear el usuario en Supabase Auth.
-- Es más seguro crear el usuario desde el Dashboard de Supabase y dejar que
-- el trigger cree el profile automáticamente.
-- ============================================================================

/*
-- Ejemplo: Crear usuario admin manualmente (NO RECOMENDADO en producción)
-- Primero crea el usuario en Supabase Dashboard, luego actualiza su profile:

UPDATE public.user_profiles
SET rol = 'admin', nombre_completo = 'Administrador BUAP'
WHERE id = 'UUID-DEL-USUARIO-CREADO-EN-AUTH';

-- Y asigna empresas al admin:
INSERT INTO public.user_companies (user_id, empresa_id, es_principal)
VALUES 
    ('UUID-DEL-USUARIO', 1, true),   -- Empresa principal
    ('UUID-DEL-USUARIO', 2, false);  -- Empresa secundaria
*/


-- ============================================================================
-- VERIFICACIÓN DE LA MIGRACIÓN
-- ============================================================================
-- Ejecuta estas queries para verificar que todo se creó correctamente:
-- ============================================================================

/*
-- 1. Verificar tablas creadas
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
  AND table_name IN ('user_profiles', 'user_companies');

-- 2. Verificar columnas de user_profiles
SELECT column_name, data_type, is_nullable, column_default
FROM information_schema.columns
WHERE table_name = 'user_profiles'
ORDER BY ordinal_position;

-- 3. Verificar funciones helper
SELECT routine_name, routine_type
FROM information_schema.routines
WHERE routine_schema = 'public'
  AND routine_name IN ('get_user_companies', 'is_admin', 'handle_new_user');

-- 4. Verificar políticas RLS
SELECT tablename, policyname, cmd, qual
FROM pg_policies
WHERE schemaname = 'public'
  AND tablename IN ('user_profiles', 'user_companies');

-- 5. Verificar que RLS está habilitado
SELECT tablename, rowsecurity
FROM pg_tables
WHERE schemaname = 'public'
  AND tablename IN ('user_profiles', 'user_companies');

-- 6. Verificar trigger en auth.users
SELECT trigger_name, event_manipulation, action_statement
FROM information_schema.triggers
WHERE trigger_name = 'on_auth_user_created';
*/


-- ============================================================================
-- ROLLBACK (si necesitas revertir la migración)
-- ============================================================================
-- Ejecuta este bloque para eliminar todo lo creado por esta migración:
-- ============================================================================

/*
-- Eliminar políticas RLS
DROP POLICY IF EXISTS "Usuarios ven su propio perfil" ON public.user_profiles;
DROP POLICY IF EXISTS "Usuarios actualizan su propio perfil" ON public.user_profiles;
DROP POLICY IF EXISTS "Solo sistema puede insertar profiles" ON public.user_profiles;
DROP POLICY IF EXISTS "Solo admins eliminan profiles" ON public.user_profiles;
DROP POLICY IF EXISTS "Usuarios ven sus propias empresas" ON public.user_companies;
DROP POLICY IF EXISTS "Solo admins asignan empresas a usuarios" ON public.user_companies;
DROP POLICY IF EXISTS "Solo admins modifican asignaciones" ON public.user_companies;
DROP POLICY IF EXISTS "Solo admins eliminan asignaciones" ON public.user_companies;

-- Eliminar trigger
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;

-- Eliminar funciones
DROP FUNCTION IF EXISTS public.handle_new_user();
DROP FUNCTION IF EXISTS public.is_admin();
DROP FUNCTION IF EXISTS public.get_user_companies();

-- Eliminar trigger de auditoría
DROP TRIGGER IF EXISTS trg_user_profiles_fecha_actualizacion ON public.user_profiles;

-- Eliminar tablas (en orden por dependencias)
DROP TABLE IF EXISTS public.user_companies;
DROP TABLE IF EXISTS public.user_profiles;
*/
