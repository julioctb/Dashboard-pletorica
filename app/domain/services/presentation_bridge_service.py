"""Service helpers to keep presentation states database-agnostic."""

from __future__ import annotations

from app.database import db_manager


class PresentationBridgeService:
    """Wraps legacy direct Supabase operations used by UI states."""

    @staticmethod
    def _supabase():
        return db_manager.get_client()

    @staticmethod
    async def fetch_historial_laboral_rows(empleado_id: int) -> list[dict]:
        supabase = PresentationBridgeService._supabase()
        result = (
            supabase.table("historial_laboral")
            .select("id,empleado_id,plaza_id,tipo_movimiento,fecha_inicio,fecha_fin,notas")
            .eq("empleado_id", empleado_id)
            .order("fecha_inicio", desc=True)
            .execute()
        )
        return result.data or []

    @staticmethod
    async def fetch_plazas_lookup(plaza_ids: list[int]) -> dict[int, dict]:
        if not plaza_ids:
            return {}
        supabase = PresentationBridgeService._supabase()
        result = (
            supabase.table("plazas")
            .select(
                "id,numero_plaza,"
                "categorias_puesto:categoria_puesto_id(nombre),"
                "sedes:sede_id(nombre,codigo)"
            )
            .in_("id", plaza_ids)
            .execute()
        )
        return {int(plaza.get("id") or 0): plaza for plaza in (result.data or [])}

    @staticmethod
    async def fetch_incidencias_asistencia(empleado_id: int, limit: int = 2000) -> list[dict]:
        supabase = PresentationBridgeService._supabase()
        result = (
            supabase.table("incidencias_asistencia")
            .select("tipo_incidencia,fecha")
            .eq("empleado_id", empleado_id)
            .order("fecha", desc=True)
            .limit(limit)
            .execute()
        )
        return result.data or []

    @staticmethod
    async def replace_storage_pdf(storage_path: str, payload: bytes) -> str:
        supabase = PresentationBridgeService._supabase()
        try:
            supabase.storage.from_("archivos").remove([storage_path])
        except Exception:
            pass
        supabase.storage.from_("archivos").upload(
            storage_path,
            payload,
            file_options={"content-type": "application/pdf"},
        )
        return supabase.storage.from_("archivos").get_public_url(storage_path)

    @staticmethod
    async def fetch_nomina_empleado_ids(periodo_id: int) -> list[int]:
        supabase = PresentationBridgeService._supabase()
        result = (
            supabase.table("nominas_empleado")
            .select("id")
            .eq("periodo_id", periodo_id)
            .execute()
        )
        return [row["id"] for row in (result.data or [])]

    @staticmethod
    async def fetch_deducciones_movimientos(nomina_empleado_ids: list[int]) -> list[dict]:
        if not nomina_empleado_ids:
            return []
        supabase = PresentationBridgeService._supabase()
        result = (
            supabase.table("nomina_movimientos")
            .select("monto, conceptos_nomina(clave)")
            .in_("nomina_empleado_id", nomina_empleado_ids)
            .eq("tipo", "DEDUCCION")
            .execute()
        )
        return result.data or []

    @staticmethod
    async def fetch_descuentos_rrhh(nomina_empleado_id: int) -> list[dict]:
        supabase = PresentationBridgeService._supabase()
        result = (
            supabase.table("nomina_movimientos")
            .select(
                "id, monto, notas, concepto_id, es_automatico, "
                "conceptos_nomina(nombre, clave)"
            )
            .eq("nomina_empleado_id", nomina_empleado_id)
            .eq("origen", "RRHH")
            .execute()
        )
        return result.data or []

    @staticmethod
    async def find_concepto_nomina_id_by_clave(clave: str) -> int | None:
        supabase = PresentationBridgeService._supabase()
        result = supabase.table("conceptos_nomina").select("id").eq("clave", clave).execute()
        if not result.data:
            return None
        return result.data[0].get("id")

    @staticmethod
    async def upsert_descuento_rrhh(
        nomina_empleado_id: int,
        concepto_id: int,
        monto: float,
        notas: str | None,
    ) -> None:
        supabase = PresentationBridgeService._supabase()
        existente = (
            supabase.table("nomina_movimientos")
            .select("id")
            .eq("nomina_empleado_id", nomina_empleado_id)
            .eq("concepto_id", concepto_id)
            .eq("origen", "RRHH")
            .limit(1)
            .execute()
        )
        payload = {
            "monto": monto,
            "notas": notas,
            "es_automatico": False,
        }
        if existente.data:
            (
                supabase.table("nomina_movimientos")
                .update(payload)
                .eq("id", existente.data[0]["id"])
                .execute()
            )
            return
        supabase.table("nomina_movimientos").insert(
            {
                "nomina_empleado_id": nomina_empleado_id,
                "concepto_id": concepto_id,
                "tipo": "DEDUCCION",
                "origen": "RRHH",
                "monto_gravable": 0.0,
                "monto_exento": 0.0,
                **payload,
            }
        ).execute()

    @staticmethod
    async def delete_descuento_rrhh(movimiento_id: int) -> None:
        supabase = PresentationBridgeService._supabase()
        (
            supabase.table("nomina_movimientos")
            .delete()
            .eq("id", movimiento_id)
            .eq("origen", "RRHH")
            .execute()
        )

    @staticmethod
    async def insert_bono_contabilidad(
        nomina_empleado_id: int,
        concepto_id: int,
        monto: float,
        notas: str | None,
    ) -> None:
        supabase = PresentationBridgeService._supabase()
        supabase.table("nomina_movimientos").insert(
            {
                "nomina_empleado_id": nomina_empleado_id,
                "concepto_id": concepto_id,
                "tipo": "PERCEPCION",
                "origen": "CONTABILIDAD",
                "monto": monto,
                "monto_gravable": monto,
                "monto_exento": 0.0,
                "es_automatico": False,
                "notas": notas,
            }
        ).execute()

    @staticmethod
    async def upload_xlsx_signed_url(storage_path: str, contenido: bytes) -> str:
        supabase = PresentationBridgeService._supabase()
        content_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        try:
            supabase.storage.from_("archivos").upload(
                storage_path,
                contenido,
                {"content-type": content_type, "upsert": "true"},
            )
        except Exception:
            supabase.storage.from_("archivos").update(
                storage_path,
                contenido,
                {"content-type": content_type},
            )
        result = supabase.storage.from_("archivos").create_signed_url(storage_path, 86400)
        if isinstance(result, dict):
            return result.get("signedURL") or result.get("signedUrl", "")
        return ""

    @staticmethod
    async def fetch_periodos_nomina_empresa(empresa_id: int) -> list[dict]:
        supabase = PresentationBridgeService._supabase()
        result = (
            supabase.table("periodos_nomina")
            .select("id, nombre, estatus, fecha_inicio")
            .eq("empresa_id", empresa_id)
            .order("fecha_inicio", desc=True)
            .execute()
        )
        return result.data or []

    @staticmethod
    async def delete_contrato_tipo_entregable(tipo_id: int) -> None:
        supabase = PresentationBridgeService._supabase()
        supabase.table("contrato_tipo_entregable").delete().eq("id", tipo_id).execute()


presentation_bridge_service = PresentationBridgeService()


__all__ = ["PresentationBridgeService", "presentation_bridge_service"]
