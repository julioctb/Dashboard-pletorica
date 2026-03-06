"""Subservicio de incidencias y precargas RH."""

from __future__ import annotations

import logging
from datetime import date
from decimal import Decimal
from typing import Optional, TYPE_CHECKING

from app.core.enums import EstatusJornada, OrigenIncidencia, TipoIncidencia
from app.core.exceptions import BusinessRuleError, DatabaseError
from app.entities.asistencia import IncidenciaAsistencia, IncidenciaAsistenciaCreate

if TYPE_CHECKING:
    from app.services.asistencia_service import AsistenciaService


logger = logging.getLogger(__name__)


class AsistenciaIncidenciaService:
    """Gestiona captura, precarga y eliminacion de incidencias."""

    def __init__(self, root: "AsistenciaService"):
        self.root = root

    async def guardar_incidencia(
        self,
        empresa_id: int,
        contrato_id: int,
        user_id: str,
        fecha: date,
        datos: IncidenciaAsistenciaCreate,
    ) -> IncidenciaAsistencia:
        contexto = await self.root._resolver_contexto_usuario(empresa_id, user_id, fecha)
        jornada = await self.root._obtener_jornada_contextual(
            empresa_id=empresa_id,
            contrato_id=contrato_id,
            fecha=fecha,
            supervisor_id=contexto["supervisor_id"],
        )
        if not jornada:
            raise BusinessRuleError("Primero abre la jornada del dia")
        if self.root._enum_value(jornada.estatus) != EstatusJornada.ABIERTA.value:
            raise BusinessRuleError("La jornada ya no permite registrar incidencias")
        self.validar_valores_incidencia(datos)
        payload = self.construir_payload_incidencia(
            jornada_id=jornada.id,
            empresa_id=empresa_id,
            fecha=fecha,
            datos=datos,
            registrado_por=user_id or datos.registrado_por,
            origen=datos.origen or OrigenIncidencia.SUPERVISOR,
        )
        existente = await self.obtener_incidencia_empleado(datos.empleado_id, fecha)
        try:
            if existente:
                result = (
                    self.root.supabase.table("incidencias_asistencia")
                    .update(payload)
                    .eq("id", existente.id)
                    .execute()
                )
            else:
                result = self.root.supabase.table("incidencias_asistencia").insert(payload).execute()
            if not result.data:
                raise DatabaseError("No se pudo guardar la incidencia")
            await self.root._sincronizar_totales_jornada(jornada.id)
            return IncidenciaAsistencia(**result.data[0])
        except DatabaseError:
            raise
        except Exception as exc:
            logger.error("Error guardando incidencia: %s", exc)
            raise DatabaseError(f"Error guardando incidencia: {exc}")

    async def guardar_precarga_rh(
        self,
        empresa_id: int,
        contrato_id: int,
        user_id: str,
        fecha: date,
        datos: IncidenciaAsistenciaCreate,
    ) -> IncidenciaAsistencia:
        await self.root._validar_empleado_en_contrato(
            empresa_id=empresa_id,
            contrato_id=contrato_id,
            empleado_id=datos.empleado_id,
            fecha=fecha,
        )
        self.validar_valores_incidencia(datos)

        existente = await self.obtener_incidencia_empleado(datos.empleado_id, fecha)
        if existente and (
            self.root._enum_value(existente.origen) != OrigenIncidencia.RH.value
            and existente.jornada_id is not None
        ):
            raise BusinessRuleError(
                "La incidencia ya fue capturada durante la jornada y no puede sobrescribirse desde RH"
            )

        payload = self.construir_payload_incidencia(
            jornada_id=existente.jornada_id if existente else None,
            empresa_id=empresa_id,
            fecha=fecha,
            datos=datos,
            registrado_por=user_id or datos.registrado_por,
            origen=OrigenIncidencia.RH,
        )
        try:
            if existente:
                result = (
                    self.root.supabase.table("incidencias_asistencia")
                    .update(payload)
                    .eq("id", existente.id)
                    .execute()
                )
            else:
                result = self.root.supabase.table("incidencias_asistencia").insert(payload).execute()
            if not result.data:
                raise DatabaseError("No se pudo guardar la precarga RH")
            if existente and existente.jornada_id:
                await self.root._sincronizar_totales_jornada(existente.jornada_id)
            return IncidenciaAsistencia(**result.data[0])
        except DatabaseError:
            raise
        except Exception as exc:
            logger.error("Error guardando precarga RH: %s", exc)
            raise DatabaseError(f"Error guardando precarga RH: {exc}")

    async def eliminar_incidencia(
        self,
        empresa_id: int,
        contrato_id: int,
        user_id: str,
        empleado_id: int,
        fecha: date,
    ) -> bool:
        contexto = await self.root._resolver_contexto_usuario(empresa_id, user_id, fecha)
        jornada = await self.root._obtener_jornada_contextual(
            empresa_id=empresa_id,
            contrato_id=contrato_id,
            fecha=fecha,
            supervisor_id=contexto["supervisor_id"],
        )
        if not jornada or self.root._enum_value(jornada.estatus) != EstatusJornada.ABIERTA.value:
            raise BusinessRuleError("Solo se pueden limpiar incidencias de jornadas abiertas")

        existente = await self.obtener_incidencia_empleado(empleado_id, fecha)
        if not existente:
            return True

        try:
            self.root.supabase.table("incidencias_asistencia").delete().eq("id", existente.id).execute()
            await self.root._sincronizar_totales_jornada(jornada.id)
            return True
        except Exception as exc:
            logger.error("Error eliminando incidencia: %s", exc)
            raise DatabaseError(f"Error eliminando incidencia: {exc}")

    async def eliminar_precarga_rh(
        self,
        empresa_id: int,
        contrato_id: int,
        empleado_id: int,
        fecha: date,
    ) -> bool:
        await self.root._validar_empleado_en_contrato(
            empresa_id=empresa_id,
            contrato_id=contrato_id,
            empleado_id=empleado_id,
            fecha=fecha,
        )
        existente = await self.obtener_incidencia_empleado(empleado_id, fecha)
        if not existente:
            return True
        if (
            self.root._enum_value(existente.origen) != OrigenIncidencia.RH.value
            and existente.jornada_id is not None
        ):
            raise BusinessRuleError(
                "La incidencia pertenece a la jornada operativa y debe gestionarse desde Operacion"
            )
        try:
            self.root.supabase.table("incidencias_asistencia").delete().eq("id", existente.id).execute()
            if existente.jornada_id:
                await self.root._sincronizar_totales_jornada(existente.jornada_id)
            return True
        except Exception as exc:
            logger.error("Error eliminando precarga RH: %s", exc)
            raise DatabaseError(f"Error eliminando precarga RH: {exc}")

    async def obtener_incidencias_fecha(
        self,
        empresa_id: int,
        fecha: date,
        employee_ids: list[int],
    ) -> list[IncidenciaAsistencia]:
        if not employee_ids:
            return []
        try:
            result = (
                self.root.supabase.table("incidencias_asistencia")
                .select("*")
                .eq("empresa_id", empresa_id)
                .eq("fecha", fecha.isoformat())
                .in_("empleado_id", employee_ids)
                .execute()
            )
            return [IncidenciaAsistencia(**item) for item in (result.data or [])]
        except Exception as exc:
            logger.error("Error obteniendo incidencias: %s", exc)
            raise DatabaseError(f"Error obteniendo incidencias: {exc}")

    async def obtener_incidencia_empleado(
        self,
        empleado_id: int,
        fecha: date,
    ) -> Optional[IncidenciaAsistencia]:
        try:
            result = (
                self.root.supabase.table("incidencias_asistencia")
                .select("*")
                .eq("empleado_id", empleado_id)
                .eq("fecha", fecha.isoformat())
                .limit(1)
                .execute()
            )
            return IncidenciaAsistencia(**result.data[0]) if result.data else None
        except Exception as exc:
            logger.error("Error obteniendo incidencia por empleado: %s", exc)
            raise DatabaseError(f"Error obteniendo incidencia por empleado: {exc}")

    def construir_payload_incidencia(
        self,
        *,
        jornada_id: Optional[int],
        empresa_id: int,
        fecha: date,
        datos: IncidenciaAsistenciaCreate,
        registrado_por: str,
        origen,
    ) -> dict:
        return {
            "jornada_id": jornada_id,
            "empleado_id": datos.empleado_id,
            "empresa_id": empresa_id,
            "fecha": fecha.isoformat(),
            "tipo_incidencia": self.root._enum_value(datos.tipo_incidencia),
            "minutos_retardo": int(datos.minutos_retardo or 0),
            "horas_extra": float(datos.horas_extra or 0),
            "motivo": datos.motivo,
            "origen": self.root._enum_value(origen),
            "registrado_por": registrado_por,
            "sede_real_id": datos.sede_real_id,
        }

    def validar_valores_incidencia(self, datos: IncidenciaAsistenciaCreate) -> None:
        if datos.tipo_incidencia == TipoIncidencia.RETARDO and int(datos.minutos_retardo or 0) <= 0:
            raise BusinessRuleError("Captura minutos de retardo mayores a 0")
        if datos.tipo_incidencia == TipoIncidencia.HORA_EXTRA and Decimal(str(datos.horas_extra or 0)) <= 0:
            raise BusinessRuleError("Captura horas extra mayores a 0")
