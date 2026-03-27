"""Repositorio Supabase para incapacidades y certificados."""

from __future__ import annotations

import logging
from datetime import date
from typing import Optional

from app.core.exceptions import DatabaseError

logger = logging.getLogger(__name__)


class SupabaseIncapacidadRepository:
    """Acceso a datos de incapacidades, certificados y sincronización operativa."""

    def __init__(self, db_manager=None):
        if db_manager is None:
            from app.database import db_manager as default_db
            db_manager = default_db

        self.supabase = db_manager.get_client()
        self.tabla = "incapacidades"
        self.tabla_certificados = "certificados_incapacidad"

    async def crear_incapacidad(self, data: dict) -> dict:
        try:
            result = self.supabase.table(self.tabla).insert(data).execute()
            return result.data[0] if result.data else {}
        except Exception as exc:
            logger.error("Error creando incapacidad: %s", exc)
            raise DatabaseError(f"Error creando incapacidad: {exc}")

    async def crear_certificado(self, data: dict) -> dict:
        try:
            result = self.supabase.table(self.tabla_certificados).insert(data).execute()
            return result.data[0] if result.data else {}
        except Exception as exc:
            logger.error("Error creando certificado de incapacidad: %s", exc)
            raise DatabaseError(f"Error creando certificado de incapacidad: {exc}")

    async def obtener_por_id(self, incapacidad_id: int) -> Optional[dict]:
        try:
            result = (
                self.supabase.table(self.tabla)
                .select(
                    "*,"
                    "empleados(id,uuid,clave,nombre,apellido_paterno,apellido_materno),"
                    "plazas(id,contrato_id,categorias_puesto:categoria_puesto_id(nombre),sedes:sede_id(nombre,codigo)),"
                    "certificados_incapacidad(*)"
                )
                .eq("id", incapacidad_id)
                .limit(1)
                .execute()
            )
            return result.data[0] if result.data else None
        except Exception as exc:
            logger.error("Error obteniendo incapacidad %s: %s", incapacidad_id, exc)
            raise DatabaseError(f"Error obteniendo incapacidad: {exc}")

    async def listar_por_empleado(self, empleado_id: int) -> list[dict]:
        try:
            result = (
                self.supabase.table(self.tabla)
                .select(
                    "*,"
                    "empleados(id,uuid,clave,nombre,apellido_paterno,apellido_materno),"
                    "plazas(id,contrato_id,categorias_puesto:categoria_puesto_id(nombre),sedes:sede_id(nombre,codigo)),"
                    "certificados_incapacidad(id,folio_imss,fecha_inicio,fecha_fin,dias_certificado,tipo_certificado,archivo_id)"
                )
                .eq("empleado_id", empleado_id)
                .order("fecha_inicio", desc=True)
                .execute()
            )
            return result.data or []
        except Exception as exc:
            logger.error("Error listando incapacidades de empleado %s: %s", empleado_id, exc)
            raise DatabaseError(f"Error listando incapacidades por empleado: {exc}")

    async def listar_por_empresa(self, empresa_id: int) -> list[dict]:
        try:
            result = (
                self.supabase.table(self.tabla)
                .select(
                    "*,"
                    "empleados(id,uuid,clave,nombre,apellido_paterno,apellido_materno),"
                    "plazas(id,contrato_id,categorias_puesto:categoria_puesto_id(nombre),sedes:sede_id(nombre,codigo)),"
                    "certificados_incapacidad(id,folio_imss,fecha_inicio,fecha_fin,dias_certificado,tipo_certificado,archivo_id)"
                )
                .eq("empresa_id", empresa_id)
                .order("fecha_inicio", desc=True)
                .execute()
            )
            return result.data or []
        except Exception as exc:
            logger.error("Error listando incapacidades de empresa %s: %s", empresa_id, exc)
            raise DatabaseError(f"Error listando incapacidades por empresa: {exc}")

    async def listar_activas_por_empresa(self, empresa_id: int) -> list[dict]:
        try:
            result = (
                self.supabase.table(self.tabla)
                .select(
                    "*,"
                    "empleados(id,uuid,clave,nombre,apellido_paterno,apellido_materno),"
                    "plazas(id,contrato_id,categorias_puesto:categoria_puesto_id(nombre),sedes:sede_id(nombre,codigo)),"
                    "certificados_incapacidad(id,folio_imss,fecha_inicio,fecha_fin,dias_certificado,tipo_certificado,archivo_id)"
                )
                .eq("empresa_id", empresa_id)
                .eq("estatus", "ACTIVA")
                .order("fecha_inicio", desc=True)
                .execute()
            )
            return result.data or []
        except Exception as exc:
            logger.error("Error listando incapacidades activas de empresa %s: %s", empresa_id, exc)
            raise DatabaseError(f"Error listando incapacidades activas: {exc}")

    async def obtener_activa_por_plaza(self, plaza_id: int) -> Optional[dict]:
        try:
            result = (
                self.supabase.table(self.tabla)
                .select(
                    "*,"
                    "empleados(id,uuid,clave,nombre,apellido_paterno,apellido_materno),"
                    "plazas(id,contrato_id,categorias_puesto:categoria_puesto_id(nombre),sedes:sede_id(nombre,codigo)),"
                    "certificados_incapacidad(id,folio_imss,fecha_inicio,fecha_fin,dias_certificado,tipo_certificado,archivo_id)"
                )
                .eq("plaza_id", plaza_id)
                .eq("estatus", "ACTIVA")
                .order("fecha_inicio", desc=True)
                .limit(1)
                .execute()
            )
            return result.data[0] if result.data else None
        except Exception as exc:
            logger.error("Error obteniendo incapacidad activa de plaza %s: %s", plaza_id, exc)
            raise DatabaseError(f"Error obteniendo incapacidad activa por plaza: {exc}")

    async def actualizar_estatus(
        self,
        incapacidad_id: int,
        estatus: str,
        fecha_fin_real: Optional[date] = None,
    ) -> dict:
        payload = {"estatus": estatus}
        if fecha_fin_real is not None:
            payload["fecha_fin_real"] = fecha_fin_real.isoformat()
        try:
            result = (
                self.supabase.table(self.tabla)
                .update(payload)
                .eq("id", incapacidad_id)
                .execute()
            )
            return result.data[0] if result.data else {}
        except Exception as exc:
            logger.error("Error actualizando estatus de incapacidad %s: %s", incapacidad_id, exc)
            raise DatabaseError(f"Error actualizando estatus de incapacidad: {exc}")

    async def actualizar_fecha_fin_estimada(
        self,
        incapacidad_id: int,
        fecha_fin_estimada: date,
    ) -> dict:
        try:
            result = (
                self.supabase.table(self.tabla)
                .update({"fecha_fin_estimada": fecha_fin_estimada.isoformat()})
                .eq("id", incapacidad_id)
                .execute()
            )
            return result.data[0] if result.data else {}
        except Exception as exc:
            logger.error(
                "Error actualizando fecha fin estimada de incapacidad %s: %s",
                incapacidad_id,
                exc,
            )
            raise DatabaseError(f"Error actualizando fecha fin estimada: {exc}")

    async def contar_por_empresa(self, empresa_id: int) -> dict:
        try:
            activas = (
                self.supabase.table(self.tabla)
                .select("id", count="exact")
                .eq("empresa_id", empresa_id)
                .eq("estatus", "ACTIVA")
                .execute()
            )
            vencidas = (
                self.supabase.table(self.tabla)
                .select("id", count="exact")
                .eq("empresa_id", empresa_id)
                .eq("estatus", "VENCIDA")
                .execute()
            )
            total = (
                self.supabase.table(self.tabla)
                .select("id", count="exact")
                .eq("empresa_id", empresa_id)
                .execute()
            )
            return {
                "activas": int(activas.count or 0),
                "vencidas": int(vencidas.count or 0),
                "total": int(total.count or 0),
            }
        except Exception as exc:
            logger.error("Error contando incapacidades de empresa %s: %s", empresa_id, exc)
            raise DatabaseError(f"Error contando incapacidades por empresa: {exc}")

    async def obtener_abierta_por_empleado(self, empleado_id: int) -> Optional[dict]:
        try:
            result = (
                self.supabase.table(self.tabla)
                .select(
                    "*,"
                    "empleados(id,uuid,clave,nombre,apellido_paterno,apellido_materno),"
                    "plazas(id,contrato_id,categorias_puesto:categoria_puesto_id(nombre),sedes:sede_id(nombre,codigo)),"
                    "certificados_incapacidad(id,folio_imss,fecha_inicio,fecha_fin,dias_certificado,tipo_certificado,archivo_id)"
                )
                .eq("empleado_id", empleado_id)
                .neq("estatus", "CERRADA")
                .order("fecha_inicio", desc=True)
                .limit(1)
                .execute()
            )
            return result.data[0] if result.data else None
        except Exception as exc:
            logger.error(
                "Error obteniendo incapacidad abierta de empleado %s: %s",
                empleado_id,
                exc,
            )
            raise DatabaseError(f"Error obteniendo incapacidad abierta del empleado: {exc}")

    async def obtener_contexto_plaza(self, plaza_id: int) -> Optional[dict]:
        try:
            result = (
                self.supabase.table("plazas")
                .select(
                    "id,empleado_id,contrato_id,sede_id,categoria_puesto_id,"
                    "categorias_puesto:categoria_puesto_id(nombre),"
                    "sedes:sede_id(nombre,codigo)"
                )
                .eq("id", plaza_id)
                .limit(1)
                .execute()
            )
            if not result.data:
                return None
            row = result.data[0]
            return {
                **row,
                "categoria_nombre": (row.get("categorias_puesto") or {}).get("nombre"),
                "sede_nombre": (row.get("sedes") or {}).get("nombre"),
            }
        except Exception as exc:
            logger.error("Error obteniendo contexto de plaza %s: %s", plaza_id, exc)
            raise DatabaseError(f"Error obteniendo contexto de plaza: {exc}")

    async def obtener_contexto_laboral_empleado(self, empleado_id: int) -> Optional[dict]:
        try:
            activo = (
                self.supabase.table("historial_laboral")
                .select(
                    "plaza_id,"
                    "plazas("
                    "id,contrato_id,sede_id,categoria_puesto_id,"
                    "categorias_puesto:categoria_puesto_id(nombre),"
                    "sedes:sede_id(nombre,codigo)"
                    ")"
                )
                .eq("empleado_id", empleado_id)
                .is_("fecha_fin", "null")
                .order("fecha_inicio", desc=True)
                .limit(1)
                .execute()
            )
            if activo.data:
                row = activo.data[0]
                plaza = row.get("plazas") or {}
                return {
                    "plaza_id": row.get("plaza_id") or plaza.get("id"),
                    "contrato_id": plaza.get("contrato_id"),
                    "sede_id": plaza.get("sede_id"),
                    "categoria_puesto_id": plaza.get("categoria_puesto_id"),
                    "categoria_nombre": (plaza.get("categorias_puesto") or {}).get("nombre"),
                    "sede_nombre": (plaza.get("sedes") or {}).get("nombre"),
                }

            plaza = (
                self.supabase.table("plazas")
                .select(
                    "id,contrato_id,sede_id,categoria_puesto_id,"
                    "categorias_puesto:categoria_puesto_id(nombre),"
                    "sedes:sede_id(nombre,codigo)"
                )
                .eq("empleado_id", empleado_id)
                .eq("estatus", "OCUPADA")
                .order("fecha_inicio", desc=True)
                .limit(1)
                .execute()
            )
            if plaza.data:
                row = plaza.data[0]
                return {
                    **row,
                    "categoria_nombre": (row.get("categorias_puesto") or {}).get("nombre"),
                    "sede_nombre": (row.get("sedes") or {}).get("nombre"),
                }
            return None
        except Exception as exc:
            logger.error("Error obteniendo contexto laboral de empleado %s: %s", empleado_id, exc)
            raise DatabaseError(f"Error obteniendo contexto laboral del empleado: {exc}")

    async def obtener_incidencia_asistencia(
        self,
        empleado_id: int,
        fecha: date,
    ) -> Optional[dict]:
        try:
            result = (
                self.supabase.table("incidencias_asistencia")
                .select("*")
                .eq("empleado_id", empleado_id)
                .eq("fecha", fecha.isoformat())
                .limit(1)
                .execute()
            )
            return result.data[0] if result.data else None
        except Exception as exc:
            logger.error(
                "Error obteniendo incidencia de asistencia empleado=%s fecha=%s: %s",
                empleado_id,
                fecha,
                exc,
            )
            raise DatabaseError(f"Error obteniendo incidencia de asistencia: {exc}")

    async def upsert_incidencia_asistencia(self, data: dict) -> dict:
        try:
            result = (
                self.supabase.table("incidencias_asistencia")
                .upsert(data, on_conflict="empleado_id,fecha")
                .execute()
            )
            return result.data[0] if result.data else {}
        except Exception as exc:
            logger.error("Error sincronizando incidencia de asistencia: %s", exc)
            raise DatabaseError(f"Error sincronizando incidencia de asistencia: {exc}")

    async def obtener_registro_asistencia(
        self,
        empleado_id: int,
        fecha: date,
    ) -> Optional[dict]:
        try:
            result = (
                self.supabase.table("registros_asistencia")
                .select("*")
                .eq("empleado_id", empleado_id)
                .eq("fecha", fecha.isoformat())
                .limit(1)
                .execute()
            )
            return result.data[0] if result.data else None
        except Exception as exc:
            logger.error(
                "Error obteniendo registro de asistencia empleado=%s fecha=%s: %s",
                empleado_id,
                fecha,
                exc,
            )
            raise DatabaseError(f"Error obteniendo registro de asistencia: {exc}")

    async def upsert_registro_asistencia(self, data: dict) -> dict:
        try:
            result = (
                self.supabase.table("registros_asistencia")
                .upsert(data, on_conflict="empleado_id,fecha")
                .execute()
            )
            return result.data[0] if result.data else {}
        except Exception as exc:
            logger.error("Error sincronizando registro de asistencia: %s", exc)
            raise DatabaseError(f"Error sincronizando registro de asistencia: {exc}")
