-- -------------------------------------------------------------
-- TablePlus 6.7.0(634)
--
-- https://tableplus.com/
--
-- Database: postgres
-- Generation Time: 2025-09-12 11:56:03.8530
-- -------------------------------------------------------------


DROP TABLE IF EXISTS "public"."empresas";
-- Sequence and defined type
CREATE SEQUENCE IF NOT EXISTS empresas_id_seq;

-- Table Definition
CREATE TABLE "public"."empresas" (
    "id" int4 NOT NULL DEFAULT nextval('empresas_id_seq'::regclass),
    "nombre_comercial" varchar(100) NOT NULL,
    "razon_social" varchar(100) NOT NULL,
    "tipo_empresa" varchar(15) NOT NULL CHECK ((tipo_empresa)::text = ANY ((ARRAY['MANTENIMIENTO'::character varying, 'NOMINA'::character varying])::text[])),
    "rfc" varchar(13) NOT NULL,
    "direccion" varchar(200),
    "codigo_postal" varchar(5),
    "telefono" varchar(15),
    "email" varchar(100),
    "pagina_web" varchar(100),
    "estatus" varchar(10) DEFAULT 'ACTIVO'::character varying CHECK ((estatus)::text = ANY ((ARRAY['ACTIVO'::character varying, 'INACTIVO'::character varying, 'SUSPENDIDO'::character varying])::text[])),
    "fecha_creacion" timestamptz DEFAULT now(),
    "notas" text,
    PRIMARY KEY ("id")
);

INSERT INTO "public"."empresas" ("id", "nombre_comercial", "razon_social", "tipo_empresa", "rfc", "direccion", "codigo_postal", "telefono", "email", "pagina_web", "estatus", "fecha_creacion", "notas") VALUES
(2, 'PLETORICA', 'PLETORICA SERVICIOS DE NOMINA S.A. DE C.V.', 'NOMINA', 'PLE123456789', 'AV. PRINCIPAL 123, COL. CENTRO', '72000', '222-555-0100', 'contacto@pletorica.com.mx', 'https://pletorica.com.mx', 'ACTIVO', '2025-09-12 02:16:23.215407+00', 'NUESTRA EMPRESA DE SERVICIOS DE NOMINA'),
(3, 'MANTISER', 'MANTISER SERVICIOS DE MANTENIMIENTO S.A. DE C.V.', 'MANTENIMIENTO', 'MAN987654321', 'CALLE JARDINERIA 456, COL. VERDE', '72100', '222-555-0200', 'info@mantiser.com.mx', 'https://mantiser.com.mx', 'ACTIVO', '2025-09-12 02:16:23.215407+00', 'EMPRESA DE MANTENIMIENTO DEL PRIMO');



-- Indices
CREATE UNIQUE INDEX empresas_rfc_key ON public.empresas USING btree (rfc);
CREATE INDEX idx_empresas_rfc ON public.empresas USING btree (rfc);
CREATE INDEX idx_empresas_tipo ON public.empresas USING btree (tipo_empresa);
CREATE INDEX idx_empresas_estatus ON public.empresas USING btree (estatus);
