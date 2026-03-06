"""Subservicio de jornadas de asistencia."""

from __future__ import annotations

import logging
from datetime import date, datetime
from typing import Optional, TYPE_CHECKING

from app.core.enums import EstatusJornada, TipoRegistroAsistencia
from app.core.exceptions import BusinessRuleError, DatabaseError, NotFoundError
from app.entities.asistencia import JornadaAsistencia, JornadaAsistenciaCreate, RegistroAsistencia

if TYPE_CHECKING:
    from app.services.asistencia_service import AsistenciaService


logger = logging.getLogger(__name__)


class AsistenciaJornadaService:
    """Gestiona apertura, cierre y consultas de jornadas."""

    def __init__(self, root: "AsistenciaService"):
        self.root = root

    async def abrir_jornada(
        self,
        datos: JornadaAsistenciaCreate,
        user_id: str,
    ) -> JornadaAsistencia:
        contexto = await self.root._resolver_contexto_usuario(
            datos.empresa_id,
            user_id,
            datos.fecha,
        )
        jornada_existente = await self.obtener_jornada_existente_supervisor(
            empresa_id=datos.empresa_id,
            fecha=datos.fecha,
            supervisor_id=contexto["supervisor_id"],
        )
        if jornada_existente:
            if jornada_existente.contrato_id != datos.contrato_id:
                raise BusinessRuleError(
                    "Ya existe una jornada para este supervisor en la fecha seleccionada"
                )
            return jornada_existente

        horario = await self.root.obtener_horario_activo(datos.empresa_id, datos.contrato_id)
        empleados = await self.root._obtener_empleados_esperados(
            empresa_id=datos.empresa_id,
            contrato_id=datos.contrato_id,
            supervisor_id=contexto["supervisor_id"],
            fecha=datos.fecha,
        )
        payload = {
            "empresa_id": datos.empresa_id,
            "contrato_id": datos.contrato_id,
            "horario_id": horario.id if horario else datos.horario_id,
            "supervisor_id": contexto["supervisor_id"],
            "fecha": datos.fecha.isoformat(),
            "estatus": EstatusJornada.ABIERTA.value,
            "empleados_esperados": len(empleados),
            "novedades_registradas": 0,
            "notas": datos.notas,
            "abierta_por": user_id or datos.abierta_por,
        }
        try:
            result = self.root.supabase.table("jornadas").insert(payload).execute()
            if not result.data:
                raise DatabaseError("No se pudo abrir la jornada")
            return JornadaAsistencia(**result.data[0])
        except DatabaseError:
            raise
        except Exception as exc:
            logger.error("Error abriendo jornada: %s", exc)
            raise DatabaseError(f"Error abriendo jornada: {exc}")

    async def cerrar_jornada(
        self,
        empresa_id: int,
        contrato_id: int,
        user_id: str,
        fecha: date,
    ) -> JornadaAsistencia:
        contexto = await self.root._resolver_contexto_usuario(empresa_id, user_id, fecha)
        jornada = await self.obtener_jornada_contextual(
            empresa_id=empresa_id,
            contrato_id=contrato_id,
            fecha=fecha,
            supervisor_id=contexto["supervisor_id"],
        )
        if not jornada:
            raise NotFoundError("No existe una jornada abierta para cerrar")
        if self.root._enum_value(jornada.estatus) != EstatusJornada.ABIERTA.value:
            raise BusinessRuleError("La jornada ya fue cerrada")

        empleados = await self.root._obtener_empleados_esperados(
            empresa_id=empresa_id,
            contrato_id=contrato_id,
            supervisor_id=contexto["supervisor_id"],
            fecha=fecha,
        )
        incidencias = await self.root._obtener_incidencias_fecha(
            empresa_id,
            fecha,
            [emp.empleado_id for emp in empleados],
        )
        incidencias_map = {item.empleado_id: item for item in incidencias}

        try:
            (
                self.root.supabase.table("jornadas")
                .update(
                    {
                        "estatus": EstatusJornada.CERRADA.value,
                        "cerrada_por": user_id,
                        "fecha_cierre": datetime.utcnow().isoformat(),
                    }
                )
                .eq("id", jornada.id)
                .execute()
            )

            registros_payload = []
            for empleado in empleados:
                incidencia = incidencias_map.get(empleado.empleado_id)
                tipo_registro = (
                    TipoRegistroAsistencia.ASISTENCIA
                    if not incidencia
                    else TipoRegistroAsistencia(self.root._enum_value(incidencia.tipo_incidencia))
                )
                registros_payload.append(
                    {
                        "empleado_id": empleado.empleado_id,
                        "empresa_id": empresa_id,
                        "contrato_id": contrato_id,
                        "jornada_id": jornada.id,
                        "incidencia_id": incidencia.id if incidencia else None,
                        "fecha": fecha.isoformat(),
                        "tipo_registro": self.root._enum_value(tipo_registro),
                        "horas_extra": float(incidencia.horas_extra or 0) if incidencia else 0,
                        "minutos_retardo": int(incidencia.minutos_retardo or 0) if incidencia else 0,
                        "sede_real_id": incidencia.sede_real_id if incidencia else empleado.sede_id,
                        "es_consolidado": True,
                    }
                )

            registros_existentes = await self.obtener_registros_jornada(jornada.id)
            if registros_existentes:
                self.root.supabase.table("registros_asistencia").delete().eq("jornada_id", jornada.id).execute()

            if registros_payload:
                self.root.supabase.table("registros_asistencia").insert(registros_payload).execute()

            result = (
                self.root.supabase.table("jornadas")
                .update(
                    {
                        "estatus": EstatusJornada.CONSOLIDADA.value,
                        "empleados_esperados": len(empleados),
                        "novedades_registradas": len(incidencias),
                    }
                )
                .eq("id", jornada.id)
                .execute()
            )
            if not result.data:
                raise DatabaseError("No se pudo consolidar la jornada")
            return JornadaAsistencia(**result.data[0])
        except DatabaseError:
            raise
        except Exception as exc:
            logger.error("Error cerrando jornada: %s", exc)
            raise DatabaseError(f"Error cerrando jornada: {exc}")

    async def obtener_jornada_contextual(
        self,
        empresa_id: int,
        contrato_id: int,
        fecha: date,
        supervisor_id: Optional[int],
    ) -> Optional[JornadaAsistencia]:
        return await self.buscar_jornada(
            empresa_id=empresa_id,
            fecha=fecha,
            supervisor_id=supervisor_id,
            contrato_id=contrato_id,
        )

    async def obtener_jornada_existente_supervisor(
        self,
        empresa_id: int,
        fecha: date,
        supervisor_id: Optional[int],
    ) -> Optional[JornadaAsistencia]:
        return await self.buscar_jornada(
            empresa_id=empresa_id,
            fecha=fecha,
            supervisor_id=supervisor_id,
            contrato_id=None,
        )

    async def buscar_jornada(
        self,
        *,
        empresa_id: int,
        fecha: date,
        supervisor_id: Optional[int],
        contrato_id: Optional[int],
    ) -> Optional[JornadaAsistencia]:
        try:
            query = (
                self.root.supabase.table("jornadas")
                .select("*")
                .eq("empresa_id", empresa_id)
                .eq("fecha", fecha.isoformat())
            )
            if contrato_id is not None:
                query = query.eq("contrato_id", contrato_id)
            if supervisor_id is None:
                query = query.is_("supervisor_id", "null")
            else:
                query = query.eq("supervisor_id", supervisor_id)
            result = query.limit(1).execute()
            return JornadaAsistencia(**result.data[0]) if result.data else None
        except Exception as exc:
            logger.error("Error obteniendo jornada: %s", exc)
            raise DatabaseError(f"Error obteniendo jornada: {exc}")

    async def obtener_registros_jornada(self, jornada_id: int) -> list[RegistroAsistencia]:
        try:
            result = (
                self.root.supabase.table("registros_asistencia")
                .select("*")
                .eq("jornada_id", jornada_id)
                .execute()
            )
            return [RegistroAsistencia(**item) for item in (result.data or [])]
        except Exception as exc:
            logger.error("Error obteniendo registros de jornada: %s", exc)
            raise DatabaseError(f"Error obteniendo registros de jornada: {exc}")

    async def sincronizar_totales_jornada(self, jornada_id: int) -> None:
        try:
            result = (
                self.root.supabase.table("incidencias_asistencia")
                .select("id", count="exact")
                .eq("jornada_id", jornada_id)
                .execute()
            )
            total = result.count or 0
            self.root.supabase.table("jornadas").update({"novedades_registradas": total}).eq("id", jornada_id).execute()
        except Exception as exc:
            logger.warning("No se pudo sincronizar totales de jornada %s: %s", jornada_id, exc)

    async def validar_empleado_en_contrato(
        self,
        empresa_id: int,
        contrato_id: int,
        empleado_id: int,
        fecha: date,
    ) -> None:
        empleados = await self.root._obtener_empleados_esperados(
            empresa_id=empresa_id,
            contrato_id=contrato_id,
            supervisor_id=None,
            fecha=fecha,
        )
        if empleado_id not in {item.empleado_id for item in empleados}:
            raise BusinessRuleError(
                "El empleado seleccionado no pertenece al contrato o no tiene plaza ocupada"
            )
