"""Subservicio del panel operativo/RH de asistencias."""

from __future__ import annotations

import logging
from datetime import date
from typing import TYPE_CHECKING, Optional
from uuid import UUID

from app.core.enums import Estatus, EstatusContrato, EstatusJornada, RolEmpresa
from app.core.exceptions import DatabaseError
from app.entities.asistencia import EmpleadoAsistenciaEsperado, Horario, IncidenciaAsistencia, JornadaAsistencia, RegistroAsistencia
from app.services.contrato_service import contrato_service
from app.services.empleado_service import empleado_service
from app.services.plaza_service import plaza_service

if TYPE_CHECKING:
    from app.services.asistencia_service import AsistenciaService


logger = logging.getLogger(__name__)


class AsistenciaPanelService:
    """Carga paneles y catalogos de consulta del modulo."""

    def __init__(self, root: "AsistenciaService"):
        self.root = root

    async def obtener_contratos_operacion(self, empresa_id: int) -> list[dict]:
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
                        "fecha_fin": contrato.fecha_fin.isoformat() if contrato.fecha_fin else "",
                    }
                )
            return resultado
        except Exception as exc:
            logger.error("Error obteniendo contratos de operacion: %s", exc)
            raise DatabaseError(f"Error obteniendo contratos de operacion: {exc}")

    async def obtener_panel_operacion(
        self,
        empresa_id: int,
        contrato_id: int,
        user_id: str,
        fecha: date,
    ) -> dict:
        contexto = await self._resolver_contexto_usuario(empresa_id, user_id, fecha)
        horario = await self.root.obtener_horario_activo(empresa_id, contrato_id)
        jornada = await self.root._obtener_jornada_contextual(
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
        incidencias = await self.root._obtener_incidencias_fecha(
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
        horario = await self.root.obtener_horario_activo(empresa_id, contrato_id)
        jornada = await self.root._obtener_jornada_contextual(
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
        incidencias = await self.root._obtener_incidencias_fecha(
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

    async def resolver_contexto_usuario(
        self,
        empresa_id: int,
        user_id: str,
        fecha: date,
    ) -> dict:
        supervisor = None
        supervisor_id = None
        if user_id:
            try:
                supervisor = await empleado_service.obtener_por_user_id(UUID(str(user_id)))
            except Exception as exc:
                logger.debug("No se pudo resolver empleado supervisor: %s", exc)
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

    async def obtener_sedes_supervision(
        self,
        empresa_id: int,
        supervisor_id: int,
        fecha: date,
    ) -> list[dict]:
        try:
            result = (
                self.root.supabase.table("supervisor_sedes")
                .select("sede_id, fecha_inicio, fecha_fin, sedes:sede_id(id, codigo, nombre)")
                .eq("empresa_id", empresa_id)
                .eq("supervisor_id", supervisor_id)
                .eq("activo", True)
                .execute()
            )
            sedes = []
            for item in result.data or []:
                fecha_inicio = date.fromisoformat(item["fecha_inicio"])
                fecha_fin = date.fromisoformat(item["fecha_fin"]) if item.get("fecha_fin") else None
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
        except Exception as exc:
            logger.error("Error obteniendo sedes de supervision: %s", exc)
            raise DatabaseError(f"Error obteniendo sedes de supervision: {exc}")

    async def obtener_empleados_esperados(
        self,
        empresa_id: int,
        contrato_id: int,
        supervisor_id: Optional[int],
        fecha: date,
    ) -> list[EmpleadoAsistenciaEsperado]:
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
                self.root.supabase.table("empleados")
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
        except Exception as exc:
            logger.error("Error obteniendo empleados esperados: %s", exc)
            raise DatabaseError(f"Error obteniendo empleados esperados: {exc}")

    async def obtener_supervisores_disponibles(self, empresa_id: int) -> list[dict]:
        try:
            roles_result = (
                self.root.supabase.table("user_companies")
                .select("user_id, rol_empresa")
                .eq("empresa_id", empresa_id)
                .in_(
                    "rol_empresa",
                    [RolEmpresa.OPERACIONES.value, RolEmpresa.ADMIN_EMPRESA.value],
                )
                .execute()
            )
            user_ids = [item["user_id"] for item in (roles_result.data or []) if item.get("user_id")]

            query = (
                self.root.supabase.table("empleados")
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
                        "nombre": self.root._nombre_empleado(item),
                    }
                )
            supervisores.sort(key=lambda item: (item["nombre"], item["clave"]))
            return supervisores
        except Exception as exc:
            logger.error("Error obteniendo supervisores disponibles: %s", exc)
            raise DatabaseError(f"Error obteniendo supervisores disponibles: {exc}")

    async def obtener_catalogo_sedes(self) -> list[dict]:
        try:
            result = (
                self.root.supabase.table("sedes")
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
        except Exception as exc:
            logger.error("Error obteniendo catalogo de sedes: %s", exc)
            raise DatabaseError(f"Error obteniendo catalogo de sedes: {exc}")

    async def obtener_sedes_map(self, sede_ids: list[int]) -> dict[int, dict]:
        if not sede_ids:
            return {}
        try:
            result = self.root.supabase.table("sedes").select("id, codigo, nombre").in_("id", sede_ids).execute()
            return {
                item["id"]: {
                    "codigo": item.get("codigo", ""),
                    "nombre": item.get("nombre", ""),
                }
                for item in (result.data or [])
            }
        except Exception as exc:
            logger.error("Error obteniendo sedes: %s", exc)
            raise DatabaseError(f"Error obteniendo sedes: {exc}")

    async def construir_panel_asistencia(
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
        incidencias_map = {item.empleado_id: item for item in incidencias}
        registros_map: dict[int, RegistroAsistencia] = {}

        if (
            incluir_registros_consolidados
            and jornada
            and self.root._enum_value(jornada.estatus) == EstatusJornada.CONSOLIDADA.value
            and empleados
        ):
            registros = await self.root._obtener_registros_jornada(jornada.id)
            registros_map = {item.empleado_id: item for item in registros}

        filas = [
            self.construir_fila_panel_asistencia(
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
            "horario": self.root._serializar_modelo(horario),
            "jornada": self.root._serializar_modelo(jornada),
            "empleados": filas,
            "incidencias": self.root._serializar_modelos(incidencias),
            "total_empleados": len(filas),
            "total_incidencias": len(incidencias),
        }

    def construir_fila_panel_asistencia(
        self,
        empleado: EmpleadoAsistenciaEsperado,
        *,
        incidencia: Optional[IncidenciaAsistencia],
        registro: Optional[RegistroAsistencia],
        jornada: Optional[JornadaAsistencia],
        usar_estado_jornada: bool,
    ) -> dict:
        fila = empleado.model_dump(mode="json")

        if incidencia:
            fila["incidencia_id"] = incidencia.id
            fila["tipo_incidencia"] = self.root._enum_value(incidencia.tipo_incidencia)
            fila["resultado_dia"] = self.root._enum_value(incidencia.tipo_incidencia)
            fila["minutos_retardo"] = incidencia.minutos_retardo
            fila["horas_extra"] = float(incidencia.horas_extra or 0)
            fila["motivo"] = incidencia.motivo or ""
            fila["origen"] = self.root._enum_value(incidencia.origen)
            return fila

        if registro:
            fila["registro_id"] = registro.id
            fila["resultado_dia"] = self.root._enum_value(registro.tipo_registro)
            fila["minutos_retardo"] = registro.minutos_retardo
            fila["horas_extra"] = float(registro.horas_extra or 0)
            fila["es_consolidado"] = registro.es_consolidado
            return fila

        if usar_estado_jornada and jornada:
            estatus_jornada = self.root._enum_value(jornada.estatus)
            if estatus_jornada == EstatusJornada.ABIERTA.value:
                fila["resultado_dia"] = "SIN_NOVEDAD"
                return fila
            if estatus_jornada == EstatusJornada.CERRADA.value:
                fila["resultado_dia"] = "CERRADA"
                return fila

        fila["resultado_dia"] = "PENDIENTE"
        return fila

    async def _resolver_contexto_usuario(self, empresa_id: int, user_id: str, fecha: date) -> dict:
        return await self.resolver_contexto_usuario(empresa_id, user_id, fecha)

    async def _obtener_sedes_supervision(self, empresa_id: int, supervisor_id: int, fecha: date) -> list[dict]:
        return await self.obtener_sedes_supervision(empresa_id, supervisor_id, fecha)

    async def _obtener_empleados_esperados(
        self,
        empresa_id: int,
        contrato_id: int,
        supervisor_id: Optional[int],
        fecha: date,
    ) -> list[EmpleadoAsistenciaEsperado]:
        return await self.obtener_empleados_esperados(empresa_id, contrato_id, supervisor_id, fecha)

    async def _obtener_sedes_map(self, sede_ids: list[int]) -> dict[int, dict]:
        return await self.obtener_sedes_map(sede_ids)

    async def _construir_panel_asistencia(self, **kwargs) -> dict:
        return await self.construir_panel_asistencia(**kwargs)
