-- Migration 061: Agrega CAMBIO_SALARIO al enum tipo_movimiento_historial

DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM pg_type
        WHERE typname = 'tipo_movimiento_historial'
    ) THEN
        ALTER TYPE public.tipo_movimiento_historial
        ADD VALUE IF NOT EXISTS 'CAMBIO_SALARIO';
    END IF;
END $$;
