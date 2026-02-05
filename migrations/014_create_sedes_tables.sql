-- ============================================================================
-- Migration: Create Sedes & Contactos BUAP Tables
-- Fecha: 2026-02-01
-- Descripcion: Crea las tablas de sedes BUAP (catálogo jerárquico de
--              ubicaciones) y contactos BUAP (personas asociadas a sedes).
--              Soporta jerarquía organizacional y ubicación física como
--              conceptos independientes mediante FKs auto-referenciales.
-- ============================================================================

-- ============================================================================
-- 1. Crear tipos ENUM
-- ============================================================================

-- Tipo de sede
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'tipo_sede_enum') THEN
        CREATE TYPE tipo_sede_enum AS ENUM (
            'CAMPUS',
            'COMPLEJO_REGIONAL',
            'FACULTAD',
            'PREPARATORIA',
            'INSTITUTO',
            'HOSPITAL',
            'CENTRO',
            'BIBLIOTECA',
            'LIBRERIA',
            'MUSEO',
            'EDIFICIO',
            'DIRECCION',
            'COORDINACION',
            'SECRETARIA',
            'VICERRECTORIA',
            'PROYECTO',
            'UNIDAD',
            'OTRO'
        );
    END IF;
END $$;

-- Nivel de contacto
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'nivel_contacto_enum') THEN
        CREATE TYPE nivel_contacto_enum AS ENUM (
            'DIRECTOR',
            'SUBDIRECTOR',
            'COORDINADOR',
            'JEFE_DEPARTAMENTO',
            'ADMINISTRATIVO',
            'OPERATIVO',
            'OTRO'
        );
    END IF;
END $$;

-- Reutilizar estatus genérico si ya existe, sino crearlo
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'estatus_generico') THEN
        CREATE TYPE estatus_generico AS ENUM ('ACTIVO', 'INACTIVO');
    END IF;
END $$;


-- ============================================================================
-- 2. Crear tabla sedes
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.sedes (
    id                  SERIAL PRIMARY KEY,
    codigo              VARCHAR(20) NOT NULL,
    nombre              VARCHAR(150) NOT NULL,
    nombre_corto        VARCHAR(50),
    tipo_sede           VARCHAR(30) NOT NULL,
    es_ubicacion_fisica BOOLEAN NOT NULL DEFAULT TRUE,
    sede_padre_id       INTEGER,
    ubicacion_fisica_id INTEGER,
    direccion           TEXT,
    notas               TEXT,
    estatus             VARCHAR(10) NOT NULL DEFAULT 'ACTIVO',
    fecha_creacion      TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    fecha_actualizacion TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Constraints
    CONSTRAINT uk_sedes_codigo UNIQUE (codigo),
    CONSTRAINT fk_sedes_padre FOREIGN KEY (sede_padre_id)
        REFERENCES public.sedes(id) ON DELETE SET NULL,
    CONSTRAINT fk_sedes_ubicacion_fisica FOREIGN KEY (ubicacion_fisica_id)
        REFERENCES public.sedes(id) ON DELETE SET NULL,
    CONSTRAINT chk_sedes_no_auto_padre CHECK (sede_padre_id != id),
    CONSTRAINT chk_sedes_no_auto_ubicacion CHECK (ubicacion_fisica_id != id),
    CONSTRAINT chk_sedes_ubicacion_coherencia CHECK (
        NOT (es_ubicacion_fisica = TRUE AND ubicacion_fisica_id IS NOT NULL)
    )
);

-- Comentarios de documentación
COMMENT ON TABLE public.sedes IS 'Catálogo jerárquico de sedes BUAP: campus, facultades, edificios, direcciones, etc.';
COMMENT ON COLUMN public.sedes.codigo IS 'Código único tipado: PREFIJO-CLAVE (ej: CAM-CU, FAC-MED)';
COMMENT ON COLUMN public.sedes.es_ubicacion_fisica IS 'TRUE si tiene espacio físico propio (campus, edificio). FALSE si es unidad administrativa';
COMMENT ON COLUMN public.sedes.sede_padre_id IS 'Jerarquía organizacional: ¿dentro de qué zona/campus está?';
COMMENT ON COLUMN public.sedes.ubicacion_fisica_id IS 'Ubicación física: ¿dónde está mi oficina si NO tengo edificio propio?';


-- ============================================================================
-- 3. Crear tabla contactos_buap
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.contactos_buap (
    id                  SERIAL PRIMARY KEY,
    sede_id             INTEGER NOT NULL,
    nombre              VARCHAR(150) NOT NULL,
    cargo               VARCHAR(100),
    nivel               VARCHAR(30),
    telefono            VARCHAR(10),
    extension           VARCHAR(10),
    email               VARCHAR(100),
    es_principal        BOOLEAN NOT NULL DEFAULT FALSE,
    notas               TEXT,
    estatus             VARCHAR(10) NOT NULL DEFAULT 'ACTIVO',
    fecha_creacion      TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    fecha_actualizacion TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Constraints
    CONSTRAINT fk_contactos_buap_sede FOREIGN KEY (sede_id)
        REFERENCES public.sedes(id) ON DELETE CASCADE
);

-- Comentarios de documentación
COMMENT ON TABLE public.contactos_buap IS 'Contactos BUAP asociados a sedes: directores, coordinadores, administrativos';
COMMENT ON COLUMN public.contactos_buap.nivel IS 'Nivel jerárquico: DIRECTOR, SUBDIRECTOR, COORDINADOR, etc.';
COMMENT ON COLUMN public.contactos_buap.es_principal IS 'Contacto principal de la sede (solo uno por sede)';
COMMENT ON COLUMN public.contactos_buap.extension IS 'Extensión telefónica interna';


-- ============================================================================
-- 4. Crear índices
-- ============================================================================

-- Sedes: búsqueda por texto (case-insensitive)
CREATE INDEX IF NOT EXISTS idx_sedes_nombre_lower
ON public.sedes USING btree (LOWER(nombre));

CREATE INDEX IF NOT EXISTS idx_sedes_nombre_corto_lower
ON public.sedes USING btree (LOWER(nombre_corto));

CREATE INDEX IF NOT EXISTS idx_sedes_codigo_lower
ON public.sedes USING btree (LOWER(codigo));

-- Sedes: filtros comunes
CREATE INDEX IF NOT EXISTS idx_sedes_tipo_estatus
ON public.sedes USING btree (tipo_sede, estatus);

CREATE INDEX IF NOT EXISTS idx_sedes_estatus
ON public.sedes USING btree (estatus);

-- Sedes: jerarquía
CREATE INDEX IF NOT EXISTS idx_sedes_padre
ON public.sedes USING btree (sede_padre_id);

CREATE INDEX IF NOT EXISTS idx_sedes_ubicacion_fisica
ON public.sedes USING btree (ubicacion_fisica_id);

-- Sedes: ordenamiento
CREATE INDEX IF NOT EXISTS idx_sedes_fecha_creacion
ON public.sedes USING btree (fecha_creacion DESC);

-- Contactos: búsqueda por sede
CREATE INDEX IF NOT EXISTS idx_contactos_buap_sede
ON public.contactos_buap USING btree (sede_id);

-- Contactos: filtro de estatus
CREATE INDEX IF NOT EXISTS idx_contactos_buap_estatus
ON public.contactos_buap USING btree (estatus);

-- Contactos: contacto principal por sede
CREATE INDEX IF NOT EXISTS idx_contactos_buap_principal
ON public.contactos_buap USING btree (sede_id, es_principal)
WHERE es_principal = TRUE;

-- Contactos: búsqueda por nombre
CREATE INDEX IF NOT EXISTS idx_contactos_buap_nombre_lower
ON public.contactos_buap USING btree (LOWER(nombre));


-- ============================================================================
-- 5. Triggers de fecha_actualizacion (reutiliza función genérica existente)
-- ============================================================================

CREATE TRIGGER tr_sedes_updated
    BEFORE UPDATE ON public.sedes
    FOR EACH ROW
    EXECUTE FUNCTION update_fecha_actualizacion();

CREATE TRIGGER tr_contactos_buap_updated
    BEFORE UPDATE ON public.contactos_buap
    FOR EACH ROW
    EXECUTE FUNCTION update_fecha_actualizacion();


-- ============================================================================
-- 6. Habilitar RLS (Row Level Security) - requerido por Supabase
-- ============================================================================

ALTER TABLE public.sedes ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.contactos_buap ENABLE ROW LEVEL SECURITY;

-- Políticas permisivas para el anon key (ajustar según necesidad)
CREATE POLICY "Permitir lectura de sedes" ON public.sedes
    FOR SELECT USING (true);
CREATE POLICY "Permitir escritura de sedes" ON public.sedes
    FOR ALL USING (true) WITH CHECK (true);

CREATE POLICY "Permitir lectura de contactos_buap" ON public.contactos_buap
    FOR SELECT USING (true);
CREATE POLICY "Permitir escritura de contactos_buap" ON public.contactos_buap
    FOR ALL USING (true) WITH CHECK (true);


-- ============================================================================
-- Rollback (si necesitas revertir)
-- ============================================================================
-- DROP POLICY IF EXISTS "Permitir escritura de contactos_buap" ON public.contactos_buap;
-- DROP POLICY IF EXISTS "Permitir lectura de contactos_buap" ON public.contactos_buap;
-- DROP POLICY IF EXISTS "Permitir escritura de sedes" ON public.sedes;
-- DROP POLICY IF EXISTS "Permitir lectura de sedes" ON public.sedes;
-- DROP TRIGGER IF EXISTS tr_contactos_buap_updated ON public.contactos_buap;
-- DROP TRIGGER IF EXISTS tr_sedes_updated ON public.sedes;
-- DROP TABLE IF EXISTS public.contactos_buap;
-- DROP TABLE IF EXISTS public.sedes;
-- DROP TYPE IF EXISTS nivel_contacto_enum;
-- DROP TYPE IF EXISTS tipo_sede_enum;
