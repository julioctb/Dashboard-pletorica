-- ============================================================================
-- MIGRACION 063: LIQUIDADO como estatus + relacion padre-hijo entre contratos
-- ============================================================================
-- Objetivos:
--   1. Agregar el valor 'LIQUIDADO' al enum de estatus de contratos.
--      Semantica: cierre definitivo del contrato. Ya no admite entregables,
--      nomina nueva ni extensiones. Coexiste con 'VENCIDO' (vigencia terminada
--      pero admite tramites pendientes).
--
--   2. Agregar la columna `contrato_padre_id` para soportar extensiones:
--      una extension es un nuevo contrato que hereda la configuracion de uno
--      previo. Se vincula al padre mediante esta FK.
--      - NULL: contrato original.
--      - NOT NULL: extension del contrato referenciado.
--
-- Nota defensiva: el enum puede llamarse `estatus_contrato_enum` (nombre
-- declarado en `003_create_contratos.sql`) o `estatus_contrato` (si la base
-- fue modificada posteriormente). Este script intenta ambos nombres.
--
-- Nota: 'CERRADO' existia como valor legado del enum y fue eliminado del
-- codigo Python (EstatusContrato ya no lo expone). En bases recientes creadas
-- desde cero a partir de `003_create_contratos.sql` el enum tampoco lo tiene.
-- Si tu base aun contiene el valor CERRADO en el enum por haberse creado con
-- una version previa, queda como valor "dangling" inocuo: nada en el codigo
-- lo escribe y el UI no lo ofrece como opcion.
-- ============================================================================

-- 1. Agregar LIQUIDADO al enum, detectando dinamicamente el nombre real.
DO $$
DECLARE
    enum_name TEXT;
BEGIN
    -- Buscar el enum que contiene 'BORRADOR' (firma del enum de estatus_contrato).
    SELECT t.typname
    INTO enum_name
    FROM pg_type t
    JOIN pg_enum e ON e.enumtypid = t.oid
    WHERE e.enumlabel = 'BORRADOR'
      AND t.typname LIKE 'estatus_contrato%'
    LIMIT 1;

    IF enum_name IS NULL THEN
        RAISE EXCEPTION 'No se encontro un enum de estatus_contrato en la base';
    END IF;

    -- Verificar si LIQUIDADO ya existe en ese enum.
    IF NOT EXISTS (
        SELECT 1
        FROM pg_type t
        JOIN pg_enum e ON e.enumtypid = t.oid
        WHERE t.typname = enum_name
          AND e.enumlabel = 'LIQUIDADO'
    ) THEN
        EXECUTE format('ALTER TYPE %I ADD VALUE %L', enum_name, 'LIQUIDADO');
        RAISE NOTICE 'Agregado LIQUIDADO al enum %', enum_name;
    ELSE
        RAISE NOTICE 'LIQUIDADO ya existe en el enum %', enum_name;
    END IF;
END $$;

-- 2. Agregar columna contrato_padre_id (idempotente)
ALTER TABLE public.contratos
    ADD COLUMN IF NOT EXISTS contrato_padre_id INTEGER NULL
        REFERENCES public.contratos(id) ON DELETE SET NULL;

COMMENT ON COLUMN public.contratos.contrato_padre_id IS
'FK al contrato del cual este es una extension. NULL si el contrato es el original. '
'Las extensiones solo se crean a partir de contratos VENCIDOS.';

-- Indice para lookups de hijos por padre.
CREATE INDEX IF NOT EXISTS idx_contratos_padre
    ON public.contratos (contrato_padre_id)
    WHERE contrato_padre_id IS NOT NULL;

-- ============================================================================
-- RECORDATORIO IMPORTANTE para aplicar esta migracion
-- ============================================================================
-- En PostgreSQL, ALTER TYPE ... ADD VALUE **no puede ejecutarse dentro de una
-- transaccion que despues use ese valor en la misma sesion**. Si Supabase
-- corre todo en una transaccion, el nuevo valor LIQUIDADO solo sera visible en
-- conexiones nuevas.
--
-- Si despues de aplicar esta migracion sigues viendo el error:
--     "invalid input value for enum estatus_contrato: LIQUIDADO"
-- reinicia el pool de conexiones (o el servicio de la app) para que Supabase
-- abra conexiones nuevas que vean el enum actualizado.
-- ============================================================================
