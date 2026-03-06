"""Fachada principal del modulo de asistencias."""
import logging
from datetime import date
from typing import Optional

from app.core.enums import (
    Estatus,
)
from app.core.exceptions import BusinessRuleError
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
from app.services.asistencias.config import AsistenciaConfigService
from app.services.asistencias.incidencias import AsistenciaIncidenciaService
from app.services.asistencias.jornadas import AsistenciaJornadaService
from app.services.asistencias.panel import AsistenciaPanelService

logger = logging.getLogger(__name__)


class AsistenciaService:
    """Fachada estable para el modulo de asistencias."""

    def __init__(self):
        self.supabase = db_manager.get_client()
        self._panel_service = AsistenciaPanelService(self)
        self._config_service = AsistenciaConfigService(self)
        self._jornada_service = AsistenciaJornadaService(self)
        self._incidencia_service = AsistenciaIncidenciaService(self)

    async def obtener_contratos_operacion(self, empresa_id: int) -> list[dict]:
        return await self._panel_service.obtener_contratos_operacion(empresa_id)

    async def obtener_panel_operacion(
        self,
        empresa_id: int,
        contrato_id: int,
        user_id: str,
        fecha: date,
    ) -> dict:
        return await self._panel_service.obtener_panel_operacion(
            empresa_id=empresa_id,
            contrato_id=contrato_id,
            user_id=user_id,
            fecha=fecha,
        )

    async def obtener_panel_rrhh(
        self,
        empresa_id: int,
        contrato_id: int,
        fecha: date,
    ) -> dict:
        return await self._panel_service.obtener_panel_rrhh(
            empresa_id=empresa_id,
            contrato_id=contrato_id,
            fecha=fecha,
        )

    async def obtener_horario_activo(
        self,
        empresa_id: int,
        contrato_id: int,
    ) -> Optional[Horario]:
        return await self._config_service.obtener_horario_activo(empresa_id, contrato_id)

    async def obtener_configuracion_asistencias(
        self,
        empresa_id: int,
        contrato_id: int,
    ) -> dict:
        return await self._config_service.obtener_configuracion_asistencias(empresa_id, contrato_id)

    async def guardar_horario(
        self,
        horario_id: Optional[int],
        datos: HorarioCreate,
    ) -> Horario:
        return await self._config_service.guardar_horario(horario_id, datos)

    async def desactivar_horario(self, empresa_id: int, horario_id: int) -> bool:
        return await self._config_service.desactivar_horario(empresa_id, horario_id)

    async def guardar_supervision(
        self,
        asignacion_id: Optional[int],
        datos: SupervisorSedeCreate,
    ) -> dict:
        return await self._config_service.guardar_supervision(asignacion_id, datos)

    async def desactivar_supervision(
        self,
        empresa_id: int,
        asignacion_id: int,
        fecha_fin: Optional[date] = None,
    ) -> bool:
        return await self._config_service.desactivar_supervision(empresa_id, asignacion_id, fecha_fin)

    async def abrir_jornada(
        self,
        datos: JornadaAsistenciaCreate,
        user_id: str,
    ) -> JornadaAsistencia:
        return await self._jornada_service.abrir_jornada(datos, user_id)

    async def guardar_incidencia(
        self,
        empresa_id: int,
        contrato_id: int,
        user_id: str,
        fecha: date,
        datos: IncidenciaAsistenciaCreate,
    ) -> IncidenciaAsistencia:
        return await self._incidencia_service.guardar_incidencia(
            empresa_id=empresa_id,
            contrato_id=contrato_id,
            user_id=user_id,
            fecha=fecha,
            datos=datos,
        )

    async def guardar_precarga_rh(
        self,
        empresa_id: int,
        contrato_id: int,
        user_id: str,
        fecha: date,
        datos: IncidenciaAsistenciaCreate,
    ) -> IncidenciaAsistencia:
        return await self._incidencia_service.guardar_precarga_rh(
            empresa_id=empresa_id,
            contrato_id=contrato_id,
            user_id=user_id,
            fecha=fecha,
            datos=datos,
        )

    async def eliminar_incidencia(
        self,
        empresa_id: int,
        contrato_id: int,
        user_id: str,
        empleado_id: int,
        fecha: date,
    ) -> bool:
        return await self._incidencia_service.eliminar_incidencia(
            empresa_id=empresa_id,
            contrato_id=contrato_id,
            user_id=user_id,
            empleado_id=empleado_id,
            fecha=fecha,
        )

    async def eliminar_precarga_rh(
        self,
        empresa_id: int,
        contrato_id: int,
        empleado_id: int,
        fecha: date,
    ) -> bool:
        return await self._incidencia_service.eliminar_precarga_rh(
            empresa_id=empresa_id,
            contrato_id=contrato_id,
            empleado_id=empleado_id,
            fecha=fecha,
        )

    async def cerrar_jornada(
        self,
        empresa_id: int,
        contrato_id: int,
        user_id: str,
        fecha: date,
    ) -> JornadaAsistencia:
        return await self._jornada_service.cerrar_jornada(
            empresa_id=empresa_id,
            contrato_id=contrato_id,
            user_id=user_id,
            fecha=fecha,
        )

    async def _obtener_sedes_supervision(
        self,
        empresa_id: int,
        supervisor_id: int,
        fecha: date,
    ) -> list[dict]:
        return await self._panel_service.obtener_sedes_supervision(empresa_id, supervisor_id, fecha)

    async def _obtener_empleados_esperados(
        self,
        empresa_id: int,
        contrato_id: int,
        supervisor_id: Optional[int],
        fecha: date,
    ) -> list[EmpleadoAsistenciaEsperado]:
        return await self._panel_service.obtener_empleados_esperados(
            empresa_id=empresa_id,
            contrato_id=contrato_id,
            supervisor_id=supervisor_id,
            fecha=fecha,
        )

    async def _obtener_supervisores_disponibles(self, empresa_id: int) -> list[dict]:
        return await self._panel_service.obtener_supervisores_disponibles(empresa_id)

    async def _obtener_catalogo_sedes(self) -> list[dict]:
        return await self._panel_service.obtener_catalogo_sedes()

    async def _obtener_sedes_map(self, sede_ids: list[int]) -> dict[int, dict]:
        return await self._panel_service.obtener_sedes_map(sede_ids)

    async def _validar_supervisor_empresa(self, empresa_id: int, supervisor_id: int) -> None:
        await self._config_service.validar_supervisor_empresa(empresa_id, supervisor_id)

    async def _validar_sede_existe(self, sede_id: int) -> None:
        await self._config_service.validar_sede_existe(sede_id)

    async def _validar_supervision_duplicada(
        self,
        empresa_id: int,
        supervisor_id: int,
        sede_id: int,
        asignacion_id: Optional[int],
        activo: bool,
    ) -> None:
        await self._config_service.validar_supervision_duplicada(
            empresa_id=empresa_id,
            supervisor_id=supervisor_id,
            sede_id=sede_id,
            asignacion_id=asignacion_id,
            activo=activo,
        )

    async def _validar_empleado_en_contrato(
        self,
        empresa_id: int,
        contrato_id: int,
        empleado_id: int,
        fecha: date,
    ) -> None:
        await self._jornada_service.validar_empleado_en_contrato(
            empresa_id=empresa_id,
            contrato_id=contrato_id,
            empleado_id=empleado_id,
            fecha=fecha,
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
        return await self._panel_service.construir_panel_asistencia(
            supervisor=supervisor,
            sedes_supervision=sedes_supervision,
            horario=horario,
            jornada=jornada,
            empleados=empleados,
            incidencias=incidencias,
            incluir_registros_consolidados=incluir_registros_consolidados,
            usar_estado_jornada=usar_estado_jornada,
        )

    def _construir_fila_panel_asistencia(
        self,
        empleado: EmpleadoAsistenciaEsperado,
        *,
        incidencia: Optional[IncidenciaAsistencia],
        registro: Optional[RegistroAsistencia],
        jornada: Optional[JornadaAsistencia],
        usar_estado_jornada: bool,
    ) -> dict:
        return self._panel_service.construir_fila_panel_asistencia(
            empleado,
            incidencia=incidencia,
            registro=registro,
            jornada=jornada,
            usar_estado_jornada=usar_estado_jornada,
        )

    async def _obtener_jornada_contextual(
        self,
        empresa_id: int,
        contrato_id: int,
        fecha: date,
        supervisor_id: Optional[int],
    ) -> Optional[JornadaAsistencia]:
        return await self._jornada_service.obtener_jornada_contextual(
            empresa_id=empresa_id,
            contrato_id=contrato_id,
            fecha=fecha,
            supervisor_id=supervisor_id,
        )

    async def _obtener_jornada_existente_supervisor(
        self,
        empresa_id: int,
        fecha: date,
        supervisor_id: Optional[int],
    ) -> Optional[JornadaAsistencia]:
        return await self._jornada_service.obtener_jornada_existente_supervisor(
            empresa_id=empresa_id,
            fecha=fecha,
            supervisor_id=supervisor_id,
        )

    async def _buscar_jornada(
        self,
        *,
        empresa_id: int,
        fecha: date,
        supervisor_id: Optional[int],
        contrato_id: Optional[int],
    ) -> Optional[JornadaAsistencia]:
        return await self._jornada_service.buscar_jornada(
            empresa_id=empresa_id,
            fecha=fecha,
            supervisor_id=supervisor_id,
            contrato_id=contrato_id,
        )

    async def _obtener_incidencias_fecha(
        self,
        empresa_id: int,
        fecha: date,
        employee_ids: list[int],
    ) -> list[IncidenciaAsistencia]:
        return await self._incidencia_service.obtener_incidencias_fecha(empresa_id, fecha, employee_ids)

    async def _obtener_incidencia_empleado(
        self,
        empleado_id: int,
        fecha: date,
    ) -> Optional[IncidenciaAsistencia]:
        return await self._incidencia_service.obtener_incidencia_empleado(empleado_id, fecha)

    async def _obtener_registros_jornada(self, jornada_id: int) -> list[RegistroAsistencia]:
        return await self._jornada_service.obtener_registros_jornada(jornada_id)

    async def _sincronizar_totales_jornada(self, jornada_id: int) -> None:
        await self._jornada_service.sincronizar_totales_jornada(jornada_id)

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

    def _construir_payload_incidencia(self, **kwargs) -> dict:
        return self._incidencia_service.construir_payload_incidencia(**kwargs)

    def _validar_valores_incidencia(self, datos: IncidenciaAsistenciaCreate) -> None:
        self._incidencia_service.validar_valores_incidencia(datos)

    async def _resolver_contexto_usuario(self, empresa_id: int, user_id: str, fecha: date) -> dict:
        return await self._panel_service.resolver_contexto_usuario(empresa_id, user_id, fecha)


asistencia_service = AsistenciaService()
