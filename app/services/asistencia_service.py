"""
Servicio de aplicacion para el modulo de asistencias.
"""
import logging
from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from app.core.enums import (
    Estatus,
    EstatusContrato,
    EstatusJornada,
    OrigenIncidencia,
    RolEmpresa,
    TipoIncidencia,
    TipoRegistroAsistencia,
)
from app.core.exceptions import BusinessRuleError, DatabaseError, NotFoundError
from app.database import db_manager
from app.entities.asistencia import (
    EmpleadoAsistenciaEsperado,
    Horario,
    HorarioCreate,
    IncidenciaAsistencia,
    IncidenciaAsistenciaCreate,
    JornadaAsistencia,
    JornadaAsistenciaCreate,
    RegistroAsistencia,
    SupervisorSedeCreate,
)
from app.services.contrato_service import contrato_service
from app.services.empleado_service import empleado_service
from app.services.plaza_service import plaza_service

logger = logging.getLogger(__name__)


class AsistenciaService:
    """Servicio orquestador para captura y consolidacion diaria."""

    def __init__(self):
        self.supabase = db_manager.get_client()

    async def obtener_contratos_operacion(self, empresa_id: int) -> list[dict]:
        """Obtiene contratos activos con personal para el modulo."""
        try:
            contratos = await contrato_service.obtener_por_empresa(
                empresa_id,
                incluir_inactivos=False,
            )
            resultado = []
            for contrato in contratos:
                estatus = (
                    contrato.estatus.value
                    if hasattr(contrato.estatus, "value")
                    else str(contrato.estatus)
                )
                if estatus != EstatusContrato.ACTIVO.value or not contrato.tiene_personal:
                    continue
                resultado.append(
                    {
                        "id": contrato.id,
                        "codigo": contrato.codigo,
                        "descripcion": contrato.descripcion_objeto or "",
                        "fecha_inicio": contrato.fecha_inicio.isoformat(),
                        "fecha_fin": (
                            contrato.fecha_fin.isoformat() if contrato.fecha_fin else ""
                        ),
                    }
                )
            return resultado
        except Exception as e:
            logger.error("Error obteniendo contratos de operacion: %s", e)
            raise DatabaseError(f"Error obteniendo contratos de operacion: {e}")

    async def obtener_panel_operacion(
        self,
        empresa_id: int,
        contrato_id: int,
        user_id: str,
        fecha: date,
    ) -> dict:
        """Carga contexto completo de la jornada para la UI."""
        contexto = await self._resolver_contexto_usuario(empresa_id, user_id, fecha)
        horario = await self.obtener_horario_activo(empresa_id, contrato_id)
        jornada = await self._obtener_jornada_contextual(
            empresa_id=empresa_id,
            contrato_id=contrato_id,
            fecha=fecha,
            supervisor_id=contexto["supervisor_id"],
        )
        empleados = await self._obtener_empleados_esperados(
            empresa_id=empresa_id,
            contrato_id=contrato_id,
            supervisor_id=contexto["supervisor_id"],
            fecha=fecha,
        )
        incidencias = await self._obtener_incidencias_fecha(
            empresa_id,
            fecha,
            [emp.empleado_id for emp in empleados],
        )
        return await self._construir_panel_asistencia(
            supervisor=contexto["supervisor"],
            sedes_supervision=contexto["sedes_supervision"],
            horario=horario,
            jornada=jornada,
            empleados=empleados,
            incidencias=incidencias,
            incluir_registros_consolidados=True,
            usar_estado_jornada=True,
        )

    async def obtener_panel_rrhh(
        self,
        empresa_id: int,
        contrato_id: int,
        fecha: date,
    ) -> dict:
        """Carga el panel de precargas RH sin filtrar por supervisor."""
        horario = await self.obtener_horario_activo(empresa_id, contrato_id)
        jornada = await self._obtener_jornada_contextual(
            empresa_id=empresa_id,
            contrato_id=contrato_id,
            fecha=fecha,
            supervisor_id=None,
        )
        empleados = await self._obtener_empleados_esperados(
            empresa_id=empresa_id,
            contrato_id=contrato_id,
            supervisor_id=None,
            fecha=fecha,
        )
        incidencias = await self._obtener_incidencias_fecha(
            empresa_id,
            fecha,
            [emp.empleado_id for emp in empleados],
        )
        return await self._construir_panel_asistencia(
            supervisor={},
            sedes_supervision=[],
            horario=horario,
            jornada=jornada,
            empleados=empleados,
            incidencias=incidencias,
            incluir_registros_consolidados=False,
            usar_estado_jornada=False,
        )

    async def obtener_horario_activo(
        self,
        empresa_id: int,
        contrato_id: int,
    ) -> Optional[Horario]:
        """Obtiene el horario activo del contrato si existe."""
        try:
            result = (
                self.supabase.table("horarios")
                .select("*")
                .eq("empresa_id", empresa_id)
                .eq("contrato_id", contrato_id)
                .eq("es_horario_activo", True)
                .limit(1)
                .execute()
            )
            if not result.data:
                return None
            return Horario(**result.data[0])
        except Exception as e:
            logger.error("Error obteniendo horario activo: %s", e)
            raise DatabaseError(f"Error obteniendo horario activo: {e}")

    async def obtener_configuracion_asistencias(
        self,
        empresa_id: int,
        contrato_id: int,
    ) -> dict:
        """Carga catalogos operativos del modulo de asistencias."""
        try:
            horarios_result = (
                self.supabase.table("horarios")
                .select("*")
                .eq("empresa_id", empresa_id)
                .eq("contrato_id", contrato_id)
                .order("es_horario_activo", desc=True)
                .order("fecha_actualizacion", desc=True)
                .execute()
            )
            horarios = []
            for item in horarios_result.data or []:
                horario = Horario(**item)
                horario_dict = horario.model_dump(mode="json")
                horario_dict["dias_resumen"] = self._resumir_dias_laborales(
                    horario.dias_laborales
                )
                horarios.append(horario_dict)

            asignaciones_result = (
                self.supabase.table("supervisor_sedes")
                .select(
                    "id, supervisor_id, sede_id, empresa_id, fecha_inicio, fecha_fin, "
                    "activo, notas, fecha_creacion, fecha_actualizacion, "
                    "supervisor:supervisor_id(id, clave, nombre, apellido_paterno, apellido_materno), "
                    "sede:sede_id(id, codigo, nombre)"
                )
                .eq("empresa_id", empresa_id)
                .order("activo", desc=True)
                .order("fecha_inicio", desc=True)
                .execute()
            )
            asignaciones = []
            for item in asignaciones_result.data or []:
                supervisor_data = item.get("supervisor") or {}
                sede_data = item.get("sede") or {}
                asignaciones.append(
                    {
                        "id": item["id"],
                        "supervisor_id": item.get("supervisor_id"),
                        "sede_id": item.get("sede_id"),
                        "empresa_id": item.get("empresa_id"),
                        "fecha_inicio": item.get("fecha_inicio"),
                        "fecha_fin": item.get("fecha_fin") or "",
                        "activo": bool(item.get("activo")),
                        "notas": item.get("notas") or "",
                        "supervisor_clave": supervisor_data.get("clave", ""),
                        "supervisor_nombre": self._nombre_empleado(supervisor_data),
                        "sede_codigo": sede_data.get("codigo", ""),
                        "sede_nombre": sede_data.get("nombre", ""),
                    }
                )

            return {
                "horarios": horarios,
                "asignaciones": asignaciones,
                "supervisores": await self._obtener_supervisores_disponibles(empresa_id),
                "sedes": await self._obtener_catalogo_sedes(),
            }
        except DatabaseError:
            raise
        except Exception as e:
            logger.error("Error obteniendo configuracion de asistencias: %s", e)
            raise DatabaseError(f"Error obteniendo configuracion de asistencias: {e}")

    async def guardar_horario(
        self,
        horario_id: Optional[int],
        datos: HorarioCreate,
    ) -> Horario:
        """Crea o actualiza un horario del contrato."""
        dias_normalizados = self._normalizar_dias_laborales(datos.dias_laborales)
        payload = {
            "empresa_id": datos.empresa_id,
            "contrato_id": datos.contrato_id,
            "nombre": datos.nombre.strip(),
            "descripcion": (datos.descripcion or "").strip() or None,
            "dias_laborales": dias_normalizados,
            "tolerancia_entrada_min": int(datos.tolerancia_entrada_min),
            "tolerancia_salida_min": int(datos.tolerancia_salida_min),
            "es_horario_activo": bool(datos.es_horario_activo),
            "estatus": (
                Estatus.ACTIVO.value
                if datos.es_horario_activo
                else Estatus.INACTIVO.value
            ),
        }
        try:
            if datos.es_horario_activo:
                query = (
                    self.supabase.table("horarios")
                    .update(
                        {
                            "es_horario_activo": False,
                            "estatus": Estatus.INACTIVO.value,
                        }
                    )
                    .eq("empresa_id", datos.empresa_id)
                    .eq("contrato_id", datos.contrato_id)
                )
                if horario_id:
                    query = query.neq("id", horario_id)
                query.execute()

            if horario_id:
                result = (
                    self.supabase.table("horarios")
                    .update(payload)
                    .eq("id", horario_id)
                    .eq("empresa_id", datos.empresa_id)
                    .execute()
                )
            else:
                result = self.supabase.table("horarios").insert(payload).execute()

            if not result.data:
                raise DatabaseError("No se pudo guardar el horario")
            return Horario(**result.data[0])
        except DatabaseError:
            raise
        except Exception as e:
            logger.error("Error guardando horario: %s", e)
            raise DatabaseError(f"Error guardando horario: {e}")

    async def desactivar_horario(self, empresa_id: int, horario_id: int) -> bool:
        """Desactiva un horario del contrato."""
        try:
            result = (
                self.supabase.table("horarios")
                .update(
                    {
                        "es_horario_activo": False,
                        "estatus": Estatus.INACTIVO.value,
                    }
                )
                .eq("id", horario_id)
                .eq("empresa_id", empresa_id)
                .execute()
            )
            return bool(result.data)
        except Exception as e:
            logger.error("Error desactivando horario: %s", e)
            raise DatabaseError(f"Error desactivando horario: {e}")

    async def guardar_supervision(
        self,
        asignacion_id: Optional[int],
        datos: SupervisorSedeCreate,
    ) -> dict:
        """Crea o actualiza una asignacion supervisor-sede."""
        if datos.fecha_fin and datos.fecha_fin < datos.fecha_inicio:
            raise BusinessRuleError("La fecha fin no puede ser anterior a la fecha inicio")

        await self._validar_supervisor_empresa(datos.empresa_id, datos.supervisor_id)
        await self._validar_sede_existe(datos.sede_id)
        await self._validar_supervision_duplicada(
            empresa_id=datos.empresa_id,
            supervisor_id=datos.supervisor_id,
            sede_id=datos.sede_id,
            asignacion_id=asignacion_id,
            activo=datos.activo,
        )

        payload = {
            "empresa_id": datos.empresa_id,
            "supervisor_id": datos.supervisor_id,
            "sede_id": datos.sede_id,
            "fecha_inicio": datos.fecha_inicio.isoformat(),
            "fecha_fin": datos.fecha_fin.isoformat() if datos.fecha_fin else None,
            "activo": bool(datos.activo),
            "notas": (datos.notas or "").strip() or None,
        }
        try:
            if asignacion_id:
                result = (
                    self.supabase.table("supervisor_sedes")
                    .update(payload)
                    .eq("id", asignacion_id)
                    .eq("empresa_id", datos.empresa_id)
                    .execute()
                )
            else:
                result = self.supabase.table("supervisor_sedes").insert(payload).execute()

            if not result.data:
                raise DatabaseError("No se pudo guardar la asignacion de supervision")
            return result.data[0]
        except DatabaseError:
            raise
        except Exception as e:
            logger.error("Error guardando asignacion supervisor-sede: %s", e)
            raise DatabaseError(f"Error guardando asignacion supervisor-sede: {e}")

    async def desactivar_supervision(
        self,
        empresa_id: int,
        asignacion_id: int,
        fecha_fin: Optional[date] = None,
    ) -> bool:
        """Marca una asignacion supervisor-sede como inactiva."""
        try:
            result = (
                self.supabase.table("supervisor_sedes")
                .update(
                    {
                        "activo": False,
                        "fecha_fin": (fecha_fin or date.today()).isoformat(),
                    }
                )
                .eq("id", asignacion_id)
                .eq("empresa_id", empresa_id)
                .execute()
            )
            return bool(result.data)
        except Exception as e:
            logger.error("Error desactivando asignacion supervisor-sede: %s", e)
            raise DatabaseError(f"Error desactivando asignacion supervisor-sede: {e}")

    async def abrir_jornada(
        self,
        datos: JornadaAsistenciaCreate,
        user_id: str,
    ) -> JornadaAsistencia:
        """Abre una jornada diaria para captura."""
        contexto = await self._resolver_contexto_usuario(
            datos.empresa_id,
            user_id,
            datos.fecha,
        )
        jornada_existente = await self._obtener_jornada_existente_supervisor(
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

        horario = await self.obtener_horario_activo(datos.empresa_id, datos.contrato_id)
        empleados = await self._obtener_empleados_esperados(
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
            result = self.supabase.table("jornadas").insert(payload).execute()
            if not result.data:
                raise DatabaseError("No se pudo abrir la jornada")
            return JornadaAsistencia(**result.data[0])
        except DatabaseError:
            raise
        except Exception as e:
            logger.error("Error abriendo jornada: %s", e)
            raise DatabaseError(f"Error abriendo jornada: {e}")

    async def guardar_incidencia(
        self,
        empresa_id: int,
        contrato_id: int,
        user_id: str,
        fecha: date,
        datos: IncidenciaAsistenciaCreate,
    ) -> IncidenciaAsistencia:
        """Crea o actualiza una incidencia dentro de una jornada abierta."""
        contexto = await self._resolver_contexto_usuario(empresa_id, user_id, fecha)
        jornada = await self._obtener_jornada_contextual(
            empresa_id=empresa_id,
            contrato_id=contrato_id,
            fecha=fecha,
            supervisor_id=contexto["supervisor_id"],
        )
        if not jornada:
            raise BusinessRuleError("Primero abre la jornada del dia")
        if self._enum_value(jornada.estatus) != EstatusJornada.ABIERTA.value:
            raise BusinessRuleError("La jornada ya no permite registrar incidencias")
        self._validar_valores_incidencia(datos)
        payload = self._construir_payload_incidencia(
            jornada_id=jornada.id,
            empresa_id=empresa_id,
            fecha=fecha,
            datos=datos,
            registrado_por=user_id or datos.registrado_por,
            origen=datos.origen or OrigenIncidencia.SUPERVISOR,
        )
        existente = await self._obtener_incidencia_empleado(datos.empleado_id, fecha)
        try:
            if existente:
                result = (
                    self.supabase.table("incidencias_asistencia")
                    .update(payload)
                    .eq("id", existente.id)
                    .execute()
                )
            else:
                result = (
                    self.supabase.table("incidencias_asistencia")
                    .insert(payload)
                    .execute()
                )
            if not result.data:
                raise DatabaseError("No se pudo guardar la incidencia")
            await self._sincronizar_totales_jornada(jornada.id)
            return IncidenciaAsistencia(**result.data[0])
        except DatabaseError:
            raise
        except Exception as e:
            logger.error("Error guardando incidencia: %s", e)
            raise DatabaseError(f"Error guardando incidencia: {e}")

    async def guardar_precarga_rh(
        self,
        empresa_id: int,
        contrato_id: int,
        user_id: str,
        fecha: date,
        datos: IncidenciaAsistenciaCreate,
    ) -> IncidenciaAsistencia:
        """Crea o actualiza una precarga RH sin requerir jornada abierta."""
        await self._validar_empleado_en_contrato(
            empresa_id=empresa_id,
            contrato_id=contrato_id,
            empleado_id=datos.empleado_id,
            fecha=fecha,
        )
        self._validar_valores_incidencia(datos)

        existente = await self._obtener_incidencia_empleado(datos.empleado_id, fecha)
        if existente and (
            self._enum_value(existente.origen) != OrigenIncidencia.RH.value
            and existente.jornada_id is not None
        ):
            raise BusinessRuleError(
                "La incidencia ya fue capturada durante la jornada y no puede sobrescribirse desde RH"
            )

        payload = self._construir_payload_incidencia(
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
                    self.supabase.table("incidencias_asistencia")
                    .update(payload)
                    .eq("id", existente.id)
                    .execute()
                )
            else:
                result = (
                    self.supabase.table("incidencias_asistencia")
                    .insert(payload)
                    .execute()
                )
            if not result.data:
                raise DatabaseError("No se pudo guardar la precarga RH")
            if existente and existente.jornada_id:
                await self._sincronizar_totales_jornada(existente.jornada_id)
            return IncidenciaAsistencia(**result.data[0])
        except DatabaseError:
            raise
        except Exception as e:
            logger.error("Error guardando precarga RH: %s", e)
            raise DatabaseError(f"Error guardando precarga RH: {e}")

    async def eliminar_incidencia(
        self,
        empresa_id: int,
        contrato_id: int,
        user_id: str,
        empleado_id: int,
        fecha: date,
    ) -> bool:
        """Elimina una incidencia si la jornada sigue abierta."""
        contexto = await self._resolver_contexto_usuario(empresa_id, user_id, fecha)
        jornada = await self._obtener_jornada_contextual(
            empresa_id=empresa_id,
            contrato_id=contrato_id,
            fecha=fecha,
            supervisor_id=contexto["supervisor_id"],
        )
        if (
            not jornada
            or self._enum_value(jornada.estatus) != EstatusJornada.ABIERTA.value
        ):
            raise BusinessRuleError("Solo se pueden limpiar incidencias de jornadas abiertas")

        existente = await self._obtener_incidencia_empleado(empleado_id, fecha)
        if not existente:
            return True

        try:
            self.supabase.table("incidencias_asistencia").delete().eq(
                "id",
                existente.id,
            ).execute()
            await self._sincronizar_totales_jornada(jornada.id)
            return True
        except Exception as e:
            logger.error("Error eliminando incidencia: %s", e)
            raise DatabaseError(f"Error eliminando incidencia: {e}")

    async def eliminar_precarga_rh(
        self,
        empresa_id: int,
        contrato_id: int,
        empleado_id: int,
        fecha: date,
    ) -> bool:
        """Elimina una incidencia cargada por RH."""
        await self._validar_empleado_en_contrato(
            empresa_id=empresa_id,
            contrato_id=contrato_id,
            empleado_id=empleado_id,
            fecha=fecha,
        )
        existente = await self._obtener_incidencia_empleado(empleado_id, fecha)
        if not existente:
            return True
        if (
            self._enum_value(existente.origen) != OrigenIncidencia.RH.value
            and existente.jornada_id is not None
        ):
            raise BusinessRuleError(
                "La incidencia pertenece a la jornada operativa y debe gestionarse desde Operacion"
            )
        try:
            self.supabase.table("incidencias_asistencia").delete().eq(
                "id",
                existente.id,
            ).execute()
            if existente.jornada_id:
                await self._sincronizar_totales_jornada(existente.jornada_id)
            return True
        except Exception as e:
            logger.error("Error eliminando precarga RH: %s", e)
            raise DatabaseError(f"Error eliminando precarga RH: {e}")

    async def cerrar_jornada(
        self,
        empresa_id: int,
        contrato_id: int,
        user_id: str,
        fecha: date,
    ) -> JornadaAsistencia:
        """Cierra la jornada y genera registros consolidados."""
        contexto = await self._resolver_contexto_usuario(empresa_id, user_id, fecha)
        jornada = await self._obtener_jornada_contextual(
            empresa_id=empresa_id,
            contrato_id=contrato_id,
            fecha=fecha,
            supervisor_id=contexto["supervisor_id"],
        )
        if not jornada:
            raise NotFoundError("No existe una jornada abierta para cerrar")
        if self._enum_value(jornada.estatus) != EstatusJornada.ABIERTA.value:
            raise BusinessRuleError("La jornada ya fue cerrada")

        empleados = await self._obtener_empleados_esperados(
            empresa_id=empresa_id,
            contrato_id=contrato_id,
            supervisor_id=contexto["supervisor_id"],
            fecha=fecha,
        )
        incidencias = await self._obtener_incidencias_fecha(
            empresa_id,
            fecha,
            [emp.empleado_id for emp in empleados],
        )
        incidencias_map = {item.empleado_id: item for item in incidencias}

        try:
            self.supabase.table("jornadas").update(
                {
                    "estatus": EstatusJornada.CERRADA.value,
                    "cerrada_por": user_id,
                    "fecha_cierre": datetime.utcnow().isoformat(),
                }
            ).eq("id", jornada.id).execute()

            registros_payload = []
            for empleado in empleados:
                incidencia = incidencias_map.get(empleado.empleado_id)
                tipo_registro = (
                    TipoRegistroAsistencia.ASISTENCIA
                    if not incidencia
                    else TipoRegistroAsistencia(self._enum_value(incidencia.tipo_incidencia))
                )
                registros_payload.append(
                    {
                        "empleado_id": empleado.empleado_id,
                        "empresa_id": empresa_id,
                        "contrato_id": contrato_id,
                        "jornada_id": jornada.id,
                        "incidencia_id": incidencia.id if incidencia else None,
                        "fecha": fecha.isoformat(),
                        "tipo_registro": self._enum_value(tipo_registro),
                        "horas_extra": (
                            float(incidencia.horas_extra or 0) if incidencia else 0
                        ),
                        "minutos_retardo": (
                            int(incidencia.minutos_retardo or 0) if incidencia else 0
                        ),
                        "sede_real_id": (
                            incidencia.sede_real_id if incidencia else empleado.sede_id
                        ),
                        "es_consolidado": True,
                    }
                )

            registros_existentes = await self._obtener_registros_jornada(jornada.id)
            if registros_existentes:
                self.supabase.table("registros_asistencia").delete().eq(
                    "jornada_id",
                    jornada.id,
                ).execute()

            if registros_payload:
                self.supabase.table("registros_asistencia").insert(
                    registros_payload
                ).execute()

            result = self.supabase.table("jornadas").update(
                {
                    "estatus": EstatusJornada.CONSOLIDADA.value,
                    "empleados_esperados": len(empleados),
                    "novedades_registradas": len(incidencias),
                }
            ).eq("id", jornada.id).execute()
            if not result.data:
                raise DatabaseError("No se pudo consolidar la jornada")
            return JornadaAsistencia(**result.data[0])
        except DatabaseError:
            raise
        except Exception as e:
            logger.error("Error cerrando jornada: %s", e)
            raise DatabaseError(f"Error cerrando jornada: {e}")

    async def _resolver_contexto_usuario(
        self,
        empresa_id: int,
        user_id: str,
        fecha: date,
    ) -> dict:
        """Obtiene el empleado supervisor y sus sedes activas si existen."""
        supervisor = None
        supervisor_id = None
        if user_id:
            try:
                supervisor = await empleado_service.obtener_por_user_id(UUID(str(user_id)))
            except Exception as e:
                logger.debug("No se pudo resolver empleado supervisor: %s", e)
                supervisor = None
        if supervisor and supervisor.empresa_id == empresa_id:
            supervisor_id = supervisor.id

        sedes_supervision = []
        if supervisor_id:
            sedes_supervision = await self._obtener_sedes_supervision(
                empresa_id=empresa_id,
                supervisor_id=supervisor_id,
                fecha=fecha,
            )

        return {
            "supervisor_id": supervisor_id,
            "supervisor": (
                {
                    "id": supervisor.id,
                    "clave": supervisor.clave,
                    "nombre": supervisor.nombre_completo(),
                }
                if supervisor_id and supervisor
                else {}
            ),
            "sedes_supervision": sedes_supervision,
        }

    async def _obtener_sedes_supervision(
        self,
        empresa_id: int,
        supervisor_id: int,
        fecha: date,
    ) -> list[dict]:
        """Obtiene sedes activas asignadas a un supervisor."""
        try:
            result = (
                self.supabase.table("supervisor_sedes")
                .select("sede_id, fecha_inicio, fecha_fin, sedes:sede_id(id, codigo, nombre)")
                .eq("empresa_id", empresa_id)
                .eq("supervisor_id", supervisor_id)
                .eq("activo", True)
                .execute()
            )
            sedes = []
            for item in result.data or []:
                fecha_inicio = date.fromisoformat(item["fecha_inicio"])
                fecha_fin = (
                    date.fromisoformat(item["fecha_fin"]) if item.get("fecha_fin") else None
                )
                if fecha < fecha_inicio or (fecha_fin and fecha > fecha_fin):
                    continue
                sede_data = item.get("sedes") or {}
                sedes.append(
                    {
                        "id": sede_data.get("id", item.get("sede_id")),
                        "codigo": sede_data.get("codigo", ""),
                        "nombre": sede_data.get("nombre", ""),
                    }
                )
            return sedes
        except Exception as e:
            logger.error("Error obteniendo sedes de supervision: %s", e)
            raise DatabaseError(f"Error obteniendo sedes de supervision: {e}")

    async def _obtener_empleados_esperados(
        self,
        empresa_id: int,
        contrato_id: int,
        supervisor_id: Optional[int],
        fecha: date,
    ) -> list[EmpleadoAsistenciaEsperado]:
        """Deriva los empleados esperados desde plazas ocupadas y sedes."""
        try:
            plazas = await plaza_service.obtener_resumen_de_contrato(contrato_id)
            plazas_ocupadas = []
            for plaza in plazas:
                estatus = getattr(plaza.estatus, "value", plaza.estatus)
                if plaza.empleado_id and estatus == "OCUPADA":
                    plazas_ocupadas.append(plaza)

            empleado_ids = list({plaza.empleado_id for plaza in plazas_ocupadas if plaza.empleado_id})
            if not empleado_ids:
                return []

            result_emp = (
                self.supabase.table("empleados")
                .select("id, clave, curp, nombre, apellido_paterno, apellido_materno, sede_id, estatus, empresa_id")
                .in_("id", empleado_ids)
                .eq("empresa_id", empresa_id)
                .execute()
            )
            empleados_map = {item["id"]: item for item in (result_emp.data or [])}

            sedes_permitidas = None
            if supervisor_id:
                sedes_supervision = await self._obtener_sedes_supervision(
                    empresa_id=empresa_id,
                    supervisor_id=supervisor_id,
                    fecha=fecha,
                )
                sedes_permitidas = {item["id"] for item in sedes_supervision}
                if not sedes_permitidas:
                    return []

            sede_ids = {
                item.get("sede_id")
                for item in empleados_map.values()
                if item.get("sede_id") is not None
            }
            sedes_map = await self._obtener_sedes_map(list(sede_ids))

            filas = []
            for plaza in plazas_ocupadas:
                empleado = empleados_map.get(plaza.empleado_id)
                if not empleado:
                    continue
                sede_id = empleado.get("sede_id")
                if sedes_permitidas is not None and sede_id not in sedes_permitidas:
                    continue
                apellido_m = empleado.get("apellido_materno") or ""
                nombre_completo = " ".join(
                    part
                    for part in [
                        empleado.get("nombre", ""),
                        empleado.get("apellido_paterno", ""),
                        apellido_m,
                    ]
                    if part
                )
                filas.append(
                    EmpleadoAsistenciaEsperado(
                        empleado_id=empleado["id"],
                        clave=empleado.get("clave", ""),
                        nombre_completo=nombre_completo,
                        curp=empleado.get("curp", ""),
                        sede_id=sede_id,
                        sede_nombre=(sedes_map.get(sede_id) or {}).get("nombre", ""),
                        plaza_id=plaza.id,
                        plaza_codigo=plaza.codigo,
                        categoria_nombre=plaza.categoria_nombre,
                        estatus_empleado=str(empleado.get("estatus", "")),
                    )
                )

            filas.sort(key=lambda item: (item.sede_nombre, item.nombre_completo, item.clave))
            return filas
        except DatabaseError:
            raise
        except Exception as e:
            logger.error("Error obteniendo empleados esperados: %s", e)
            raise DatabaseError(f"Error obteniendo empleados esperados: {e}")

    async def _obtener_supervisores_disponibles(self, empresa_id: int) -> list[dict]:
        """Lista empleados elegibles para supervision con rol operativo."""
        try:
            roles_result = (
                self.supabase.table("user_companies")
                .select("user_id, rol_empresa")
                .eq("empresa_id", empresa_id)
                .in_(
                    "rol_empresa",
                    [
                        RolEmpresa.OPERACIONES.value,
                        RolEmpresa.ADMIN_EMPRESA.value,
                    ],
                )
                .execute()
            )
            user_ids = [item["user_id"] for item in (roles_result.data or []) if item.get("user_id")]

            query = (
                self.supabase.table("empleados")
                .select("id, clave, nombre, apellido_paterno, apellido_materno, user_id")
                .eq("empresa_id", empresa_id)
                .eq("estatus", Estatus.ACTIVO.value)
            )
            if user_ids:
                query = query.in_("user_id", user_ids)
            result = query.order("nombre").execute()

            supervisores = []
            for item in result.data or []:
                if not item.get("user_id"):
                    continue
                supervisores.append(
                    {
                        "id": item["id"],
                        "clave": item.get("clave", ""),
                        "nombre": self._nombre_empleado(item),
                    }
                )
            supervisores.sort(key=lambda item: (item["nombre"], item["clave"]))
            return supervisores
        except Exception as e:
            logger.error("Error obteniendo supervisores disponibles: %s", e)
            raise DatabaseError(f"Error obteniendo supervisores disponibles: {e}")

    async def _obtener_catalogo_sedes(self) -> list[dict]:
        """Lista de sedes activas para asignaciones de supervision."""
        try:
            result = (
                self.supabase.table("sedes")
                .select("id, codigo, nombre")
                .eq("estatus", Estatus.ACTIVO.value)
                .order("nombre")
                .execute()
            )
            return [
                {
                    "id": item["id"],
                    "codigo": item.get("codigo", ""),
                    "nombre": item.get("nombre", ""),
                }
                for item in (result.data or [])
            ]
        except Exception as e:
            logger.error("Error obteniendo catalogo de sedes: %s", e)
            raise DatabaseError(f"Error obteniendo catalogo de sedes: {e}")

    async def _obtener_sedes_map(self, sede_ids: list[int]) -> dict[int, dict]:
        if not sede_ids:
            return {}
        try:
            result = (
                self.supabase.table("sedes")
                .select("id, codigo, nombre")
                .in_("id", sede_ids)
                .execute()
            )
            return {
                item["id"]: {
                    "codigo": item.get("codigo", ""),
                    "nombre": item.get("nombre", ""),
                }
                for item in (result.data or [])
            }
        except Exception as e:
            logger.error("Error obteniendo sedes: %s", e)
            raise DatabaseError(f"Error obteniendo sedes: {e}")

    async def _validar_supervisor_empresa(self, empresa_id: int, supervisor_id: int) -> None:
        """Verifica que el supervisor pertenezca a la empresa actual."""
        try:
            result = (
                self.supabase.table("empleados")
                .select("id, empresa_id")
                .eq("id", supervisor_id)
                .eq("empresa_id", empresa_id)
                .limit(1)
                .execute()
            )
            if not result.data:
                raise BusinessRuleError("El supervisor seleccionado no pertenece a la empresa")
        except BusinessRuleError:
            raise
        except Exception as e:
            logger.error("Error validando supervisor: %s", e)
            raise DatabaseError(f"Error validando supervisor: {e}")

    async def _validar_sede_existe(self, sede_id: int) -> None:
        """Verifica que la sede exista."""
        try:
            result = (
                self.supabase.table("sedes")
                .select("id")
                .eq("id", sede_id)
                .limit(1)
                .execute()
            )
            if not result.data:
                raise BusinessRuleError("La sede seleccionada no existe")
        except BusinessRuleError:
            raise
        except Exception as e:
            logger.error("Error validando sede: %s", e)
            raise DatabaseError(f"Error validando sede: {e}")

    async def _validar_supervision_duplicada(
        self,
        empresa_id: int,
        supervisor_id: int,
        sede_id: int,
        asignacion_id: Optional[int],
        activo: bool,
    ) -> None:
        """Evita duplicados activos del mismo supervisor sobre la misma sede."""
        if not activo:
            return
        try:
            query = (
                self.supabase.table("supervisor_sedes")
                .select("id")
                .eq("empresa_id", empresa_id)
                .eq("supervisor_id", supervisor_id)
                .eq("sede_id", sede_id)
                .eq("activo", True)
            )
            if asignacion_id:
                query = query.neq("id", asignacion_id)
            result = query.limit(1).execute()
            if result.data:
                raise BusinessRuleError(
                    "Ya existe una asignacion activa de este supervisor para la sede seleccionada"
                )
        except BusinessRuleError:
            raise
        except Exception as e:
            logger.error("Error validando duplicado supervisor-sede: %s", e)
            raise DatabaseError(f"Error validando duplicado supervisor-sede: {e}")

    async def _validar_empleado_en_contrato(
        self,
        empresa_id: int,
        contrato_id: int,
        empleado_id: int,
        fecha: date,
    ) -> None:
        """Valida que el empleado pertenezca al contrato activo consultado."""
        empleados = await self._obtener_empleados_esperados(
            empresa_id=empresa_id,
            contrato_id=contrato_id,
            supervisor_id=None,
            fecha=fecha,
        )
        if empleado_id not in {item.empleado_id for item in empleados}:
            raise BusinessRuleError(
                "El empleado seleccionado no pertenece al contrato o no tiene plaza ocupada"
            )

    async def _construir_panel_asistencia(
        self,
        *,
        supervisor: dict,
        sedes_supervision: list[dict],
        horario: Optional[Horario],
        jornada: Optional[JornadaAsistencia],
        empleados: list[EmpleadoAsistenciaEsperado],
        incidencias: list[IncidenciaAsistencia],
        incluir_registros_consolidados: bool,
        usar_estado_jornada: bool,
    ) -> dict:
        """Construye el payload serializable del panel de asistencias."""
        incidencias_map = {item.empleado_id: item for item in incidencias}
        registros_map: dict[int, RegistroAsistencia] = {}

        if (
            incluir_registros_consolidados
            and jornada
            and self._enum_value(jornada.estatus) == EstatusJornada.CONSOLIDADA.value
            and empleados
        ):
            registros = await self._obtener_registros_jornada(jornada.id)
            registros_map = {item.empleado_id: item for item in registros}

        filas = [
            self._construir_fila_panel_asistencia(
                empleado,
                incidencia=incidencias_map.get(empleado.empleado_id),
                registro=registros_map.get(empleado.empleado_id),
                jornada=jornada,
                usar_estado_jornada=usar_estado_jornada,
            )
            for empleado in empleados
        ]

        return {
            "supervisor": supervisor,
            "sedes_supervision": sedes_supervision,
            "horario": self._serializar_modelo(horario),
            "jornada": self._serializar_modelo(jornada),
            "empleados": filas,
            "incidencias": self._serializar_modelos(incidencias),
            "total_empleados": len(filas),
            "total_incidencias": len(incidencias),
        }

    def _construir_fila_panel_asistencia(
        self,
        empleado: EmpleadoAsistenciaEsperado,
        *,
        incidencia: Optional[IncidenciaAsistencia],
        registro: Optional[RegistroAsistencia],
        jornada: Optional[JornadaAsistencia],
        usar_estado_jornada: bool,
    ) -> dict:
        """Enriquece la fila serializada de un empleado para el panel diario."""
        fila = empleado.model_dump(mode="json")

        if incidencia:
            fila["incidencia_id"] = incidencia.id
            fila["tipo_incidencia"] = self._enum_value(incidencia.tipo_incidencia)
            fila["resultado_dia"] = self._enum_value(incidencia.tipo_incidencia)
            fila["minutos_retardo"] = incidencia.minutos_retardo
            fila["horas_extra"] = float(incidencia.horas_extra or 0)
            fila["motivo"] = incidencia.motivo or ""
            fila["origen"] = self._enum_value(incidencia.origen)
            return fila

        if registro:
            fila["registro_id"] = registro.id
            fila["resultado_dia"] = self._enum_value(registro.tipo_registro)
            fila["minutos_retardo"] = registro.minutos_retardo
            fila["horas_extra"] = float(registro.horas_extra or 0)
            fila["es_consolidado"] = registro.es_consolidado
            return fila

        if usar_estado_jornada and jornada:
            estatus_jornada = self._enum_value(jornada.estatus)
            if estatus_jornada == EstatusJornada.ABIERTA.value:
                fila["resultado_dia"] = "SIN_NOVEDAD"
                return fila
            if estatus_jornada == EstatusJornada.CERRADA.value:
                fila["resultado_dia"] = "CERRADA"
                return fila

        fila["resultado_dia"] = "PENDIENTE"
        return fila

    async def _obtener_jornada_contextual(
        self,
        empresa_id: int,
        contrato_id: int,
        fecha: date,
        supervisor_id: Optional[int],
    ) -> Optional[JornadaAsistencia]:
        """Obtiene la jornada que aplica a la combinacion actual."""
        return await self._buscar_jornada(
            empresa_id=empresa_id,
            fecha=fecha,
            supervisor_id=supervisor_id,
            contrato_id=contrato_id,
        )

    async def _obtener_jornada_existente_supervisor(
        self,
        empresa_id: int,
        fecha: date,
        supervisor_id: Optional[int],
    ) -> Optional[JornadaAsistencia]:
        """Busca jornada existente del mismo supervisor y fecha."""
        return await self._buscar_jornada(
            empresa_id=empresa_id,
            fecha=fecha,
            supervisor_id=supervisor_id,
            contrato_id=None,
        )

    async def _buscar_jornada(
        self,
        *,
        empresa_id: int,
        fecha: date,
        supervisor_id: Optional[int],
        contrato_id: Optional[int],
    ) -> Optional[JornadaAsistencia]:
        """Busca una jornada por contexto compartido de empresa/fecha/supervisor."""
        try:
            query = (
                self.supabase.table("jornadas")
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
            if not result.data:
                return None
            return JornadaAsistencia(**result.data[0])
        except Exception as e:
            logger.error("Error obteniendo jornada: %s", e)
            raise DatabaseError(f"Error obteniendo jornada: {e}")

    async def _obtener_incidencias_fecha(
        self,
        empresa_id: int,
        fecha: date,
        employee_ids: list[int],
    ) -> list[IncidenciaAsistencia]:
        """Obtiene incidencias de una fecha para un conjunto de empleados."""
        if not employee_ids:
            return []
        try:
            result = (
                self.supabase.table("incidencias_asistencia")
                .select("*")
                .eq("empresa_id", empresa_id)
                .eq("fecha", fecha.isoformat())
                .in_("empleado_id", employee_ids)
                .execute()
            )
            return [IncidenciaAsistencia(**item) for item in (result.data or [])]
        except Exception as e:
            logger.error("Error obteniendo incidencias: %s", e)
            raise DatabaseError(f"Error obteniendo incidencias: {e}")

    async def _obtener_incidencia_empleado(
        self,
        empleado_id: int,
        fecha: date,
    ) -> Optional[IncidenciaAsistencia]:
        """Obtiene la incidencia unica del empleado en la fecha."""
        try:
            result = (
                self.supabase.table("incidencias_asistencia")
                .select("*")
                .eq("empleado_id", empleado_id)
                .eq("fecha", fecha.isoformat())
                .limit(1)
                .execute()
            )
            if not result.data:
                return None
            return IncidenciaAsistencia(**result.data[0])
        except Exception as e:
            logger.error("Error obteniendo incidencia por empleado: %s", e)
            raise DatabaseError(f"Error obteniendo incidencia por empleado: {e}")

    async def _obtener_registros_jornada(self, jornada_id: int) -> list[RegistroAsistencia]:
        """Obtiene registros consolidados de una jornada."""
        try:
            result = (
                self.supabase.table("registros_asistencia")
                .select("*")
                .eq("jornada_id", jornada_id)
                .execute()
            )
            return [RegistroAsistencia(**item) for item in (result.data or [])]
        except Exception as e:
            logger.error("Error obteniendo registros de jornada: %s", e)
            raise DatabaseError(f"Error obteniendo registros de jornada: {e}")

    async def _sincronizar_totales_jornada(self, jornada_id: int) -> None:
        """Actualiza el contador de incidencias capturadas en la jornada."""
        try:
            result = (
                self.supabase.table("incidencias_asistencia")
                .select("id", count="exact")
                .eq("jornada_id", jornada_id)
                .execute()
            )
            total = result.count or 0
            self.supabase.table("jornadas").update(
                {
                    "novedades_registradas": total,
                }
            ).eq("id", jornada_id).execute()
        except Exception as e:
            logger.warning("No se pudo sincronizar totales de jornada %s: %s", jornada_id, e)

    @staticmethod
    def _nombre_empleado(data: dict) -> str:
        return " ".join(
            part
            for part in [
                data.get("nombre", ""),
                data.get("apellido_paterno", ""),
                data.get("apellido_materno", "") or "",
            ]
            if part
        ).strip()

    @staticmethod
    def _normalizar_dias_laborales(dias_laborales: dict) -> dict:
        dias_orden = [
            "lunes",
            "martes",
            "miercoles",
            "jueves",
            "viernes",
            "sabado",
            "domingo",
        ]
        resultado = {}
        dias_habilitados = 0
        for dia in dias_orden:
            config = (dias_laborales or {}).get(dia)
            if not config:
                resultado[dia] = None
                continue
            entrada = str(config.get("entrada", "")).strip()
            salida = str(config.get("salida", "")).strip()
            if not entrada or not salida:
                raise BusinessRuleError(
                    f"Configura entrada y salida para {dia} o desactiva ese dia"
                )
            resultado[dia] = {
                "entrada": entrada,
                "salida": salida,
            }
            dias_habilitados += 1
        if dias_habilitados == 0:
            raise BusinessRuleError("Configura al menos un dia laborable en el horario")
        return resultado

    @staticmethod
    def _resumir_dias_laborales(dias_laborales: dict) -> str:
        etiquetas = [
            ("lunes", "Lun"),
            ("martes", "Mar"),
            ("miercoles", "Mie"),
            ("jueves", "Jue"),
            ("viernes", "Vie"),
            ("sabado", "Sab"),
            ("domingo", "Dom"),
        ]
        partes = []
        for dia, etiqueta in etiquetas:
            config = (dias_laborales or {}).get(dia)
            if not config:
                continue
            partes.append(f"{etiqueta} {config.get('entrada', '')}-{config.get('salida', '')}")
        return " / ".join(partes) if partes else "Sin dias laborables"

    @staticmethod
    def _enum_value(value) -> str:
        return value.value if hasattr(value, "value") else str(value)

    @staticmethod
    def _serializar_modelo(item) -> dict:
        return item.model_dump(mode="json") if item else {}

    def _serializar_modelos(self, items: list) -> list[dict]:
        return [self._serializar_modelo(item) for item in items]

    def _construir_payload_incidencia(
        self,
        *,
        jornada_id: Optional[int],
        empresa_id: int,
        fecha: date,
        datos: IncidenciaAsistenciaCreate,
        registrado_por: str,
        origen,
    ) -> dict:
        """Arma el payload persistible de una incidencia/precarga."""
        return {
            "jornada_id": jornada_id,
            "empleado_id": datos.empleado_id,
            "empresa_id": empresa_id,
            "fecha": fecha.isoformat(),
            "tipo_incidencia": self._enum_value(datos.tipo_incidencia),
            "minutos_retardo": int(datos.minutos_retardo or 0),
            "horas_extra": float(datos.horas_extra or 0),
            "motivo": datos.motivo,
            "origen": self._enum_value(origen),
            "registrado_por": registrado_por,
            "sede_real_id": datos.sede_real_id,
        }

    @staticmethod
    def _validar_valores_incidencia(datos: IncidenciaAsistenciaCreate) -> None:
        """Valida montos obligatorios por tipo de incidencia."""
        if (
            datos.tipo_incidencia == TipoIncidencia.RETARDO
            and int(datos.minutos_retardo or 0) <= 0
        ):
            raise BusinessRuleError("Captura minutos de retardo mayores a 0")
        if (
            datos.tipo_incidencia == TipoIncidencia.HORA_EXTRA
            and Decimal(str(datos.horas_extra or 0)) <= 0
        ):
            raise BusinessRuleError("Captura horas extra mayores a 0")


asistencia_service = AsistenciaService()
