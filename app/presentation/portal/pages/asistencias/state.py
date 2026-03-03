"""
State del modulo de asistencias del portal de operaciones.
"""
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import List

import reflex as rx

from app.core.enums import Estatus, TipoIncidencia
from app.core.exceptions import BusinessRuleError, NotFoundError
from app.entities.asistencia import (
    HorarioCreate,
    IncidenciaAsistenciaCreate,
    JornadaAsistenciaCreate,
    SupervisorSedeCreate,
)
from app.presentation.portal.state.portal_state import PortalState
from app.services.asistencia_service import asistencia_service

DIAS_SEMANA = [
    ("lunes", "Lunes"),
    ("martes", "Martes"),
    ("miercoles", "Miercoles"),
    ("jueves", "Jueves"),
    ("viernes", "Viernes"),
    ("sabado", "Sabado"),
    ("domingo", "Domingo"),
]

HORARIO_DIAS_BASE = {
    "lunes": {"entrada": "07:00", "salida": "15:00"},
    "martes": {"entrada": "07:00", "salida": "15:00"},
    "miercoles": {"entrada": "07:00", "salida": "15:00"},
    "jueves": {"entrada": "07:00", "salida": "15:00"},
    "viernes": {"entrada": "07:00", "salida": "15:00"},
    "sabado": {"entrada": "07:00", "salida": "12:00"},
    "domingo": None,
}


def _horario_dias_default() -> dict:
    return {
        dia: (config.copy() if isinstance(config, dict) else None)
        for dia, config in HORARIO_DIAS_BASE.items()
    }


class AsistenciasState(PortalState):
    """State para captura de asistencias y configuracion operativa."""

    contratos_disponibles: list[dict] = []
    contrato_seleccionado_id: int = 0
    fecha_operacion: str = date.today().isoformat()
    panel_activo: str = "operacion"

    supervisor_actual: dict = {}
    sedes_supervision: list[dict] = []
    horario_activo: dict = {}
    jornada_actual: dict = {}
    empleados_jornada: list[dict] = []
    incidencias_jornada: list[dict] = []

    horarios_configuracion: list[dict] = []
    asignaciones_supervision: list[dict] = []
    supervisores_disponibles: list[dict] = []
    sedes_catalogo: list[dict] = []

    modal_incidencia_abierto: bool = False
    empleado_seleccionado: dict = {}
    form_tipo_incidencia: str = TipoIncidencia.FALTA.value
    form_minutos_retardo: str = "0"
    form_horas_extra: str = "0"
    form_motivo: str = ""

    modal_horario_abierto: bool = False
    horario_editando_id: int = 0
    form_horario_nombre: str = ""
    form_horario_descripcion: str = ""
    form_horario_tolerancia_entrada: str = "10"
    form_horario_tolerancia_salida: str = "0"
    form_horario_activo: bool = True
    form_horario_dias_laborales: dict = _horario_dias_default()

    modal_supervision_abierto: bool = False
    supervision_editando_id: int = 0
    form_supervision_supervisor_id: str = ""
    form_supervision_sede_id: str = ""
    form_supervision_fecha_inicio: str = date.today().isoformat()
    form_supervision_fecha_fin: str = ""
    form_supervision_activo: bool = True
    form_supervision_notas: str = ""

    @rx.var
    def empleados_filtrados(self) -> List[dict]:
        if not self.filtro_busqueda:
            return self.empleados_jornada
        termino = self.filtro_busqueda.lower()
        return [
            item
            for item in self.empleados_jornada
            if termino in item.get("clave", "").lower()
            or termino in item.get("nombre_completo", "").lower()
            or termino in item.get("sede_nombre", "").lower()
            or termino in item.get("categoria_nombre", "").lower()
        ]

    @rx.var
    def horarios_filtrados(self) -> List[dict]:
        if not self.filtro_busqueda:
            return self.horarios_configuracion
        termino = self.filtro_busqueda.lower()
        return [
            item
            for item in self.horarios_configuracion
            if termino in item.get("nombre", "").lower()
            or termino in (item.get("descripcion") or "").lower()
            or termino in item.get("dias_resumen", "").lower()
        ]

    @rx.var
    def asignaciones_filtradas(self) -> List[dict]:
        if not self.filtro_busqueda:
            return self.asignaciones_supervision
        termino = self.filtro_busqueda.lower()
        return [
            item
            for item in self.asignaciones_supervision
            if termino in item.get("supervisor_nombre", "").lower()
            or termino in item.get("supervisor_clave", "").lower()
            or termino in item.get("sede_nombre", "").lower()
            or termino in item.get("sede_codigo", "").lower()
            or termino in (item.get("notas") or "").lower()
        ]

    @rx.var
    def total_empleados_jornada(self) -> int:
        return len(self.empleados_jornada)

    @rx.var
    def total_incidencias(self) -> int:
        return len(self.incidencias_jornada)

    @rx.var
    def total_sedes_supervision(self) -> int:
        return len(self.sedes_supervision)

    @rx.var
    def total_horarios_configuracion(self) -> int:
        return len(self.horarios_configuracion)

    @rx.var
    def total_horarios_activos(self) -> int:
        return len([item for item in self.horarios_configuracion if item.get("es_horario_activo")])

    @rx.var
    def total_asignaciones_supervision(self) -> int:
        return len(self.asignaciones_supervision)

    @rx.var
    def total_asignaciones_activas(self) -> int:
        return len([item for item in self.asignaciones_supervision if item.get("activo")])

    @rx.var
    def puede_precargar_rrhh(self) -> bool:
        return self.es_rrhh or self.es_admin_empresa

    @rx.var
    def puede_operar_jornada(self) -> bool:
        return self.es_operaciones or self.es_admin_empresa

    @rx.var
    def puede_configurar_catalogos(self) -> bool:
        return self.es_rrhh or self.es_admin_empresa

    @rx.var
    def mostrar_selector_panel(self) -> bool:
        return (
            self.puede_operar_jornada
            or self.puede_precargar_rrhh
            or self.puede_configurar_catalogos
        )

    @rx.var
    def panel_es_operacion(self) -> bool:
        return self.panel_activo == "operacion"

    @rx.var
    def panel_es_rrhh(self) -> bool:
        return self.panel_activo == "rrhh"

    @rx.var
    def panel_es_configuracion(self) -> bool:
        return self.panel_activo == "configuracion"

    @rx.var
    def nombre_jornada(self) -> str:
        if not self.jornada_actual:
            return "Sin jornada"
        return self.jornada_actual.get("estatus", "Sin jornada")

    @rx.var
    def tiene_jornada_abierta(self) -> bool:
        return self.jornada_actual.get("estatus", "") == "ABIERTA"

    @rx.var
    def puede_abrir_jornada(self) -> bool:
        return (
            self.panel_es_operacion
            and self.puede_operar_jornada
            and self.contrato_seleccionado_id > 0
            and not self.jornada_actual
        )

    @rx.var
    def puede_cerrar_jornada(self) -> bool:
        return (
            self.panel_es_operacion
            and self.puede_operar_jornada
            and self.jornada_actual.get("estatus", "") == "ABIERTA"
        )

    @rx.var
    def puede_editar_incidencias(self) -> bool:
        if self.panel_es_configuracion:
            return False
        if self.panel_es_rrhh:
            return self.puede_precargar_rrhh
        return self.tiene_jornada_abierta and self.puede_operar_jornada

    @rx.var
    def descripcion_horario(self) -> str:
        if not self.horario_activo:
            return "Sin horario activo"
        nombre = self.horario_activo.get("nombre", "")
        tolerancia = self.horario_activo.get("tolerancia_entrada_min", 0)
        return f"{nombre} · Tolerancia {tolerancia} min"

    @rx.var
    def titulo_supervision(self) -> str:
        if self.panel_es_configuracion:
            return "Configuracion operativa"
        if self.panel_es_rrhh:
            return "Precargas de RH"
        if self.supervisor_actual:
            return self.supervisor_actual.get("nombre", "Supervisor")
        return "Vista operativa"

    @rx.var
    def texto_contexto_panel(self) -> str:
        if self.panel_es_configuracion:
            return (
                "Administra horarios por contrato y asignaciones supervisor-sede "
                "sin salir del modulo de asistencias."
            )
        if self.panel_es_rrhh:
            return (
                "RH puede precargar incidencias sin abrir jornada. "
                "Las novedades apareceran automaticamente al supervisor y en la consolidacion."
            )
        return (
            "Operacion registra novedades durante la jornada y al cierre se consolidan "
            "asistencias e incidencias del dia."
        )

    @rx.var
    def titulo_modal_incidencia(self) -> str:
        if self.panel_es_rrhh:
            return "Precargar incidencia RH"
        return "Registrar incidencia"

    @rx.var
    def texto_guardar_incidencia(self) -> str:
        if self.panel_es_rrhh:
            return "Guardar precarga"
        return "Guardar incidencia"

    @rx.var
    def titulo_modal_horario(self) -> str:
        return "Editar horario" if self.horario_editando_id else "Nuevo horario"

    @rx.var
    def texto_guardar_horario(self) -> str:
        return "Actualizar horario" if self.horario_editando_id else "Crear horario"

    @rx.var
    def titulo_modal_supervision(self) -> str:
        return (
            "Editar asignacion supervisor-sede"
            if self.supervision_editando_id
            else "Nueva asignacion supervisor-sede"
        )

    @rx.var
    def texto_guardar_supervision(self) -> str:
        return (
            "Actualizar asignacion"
            if self.supervision_editando_id
            else "Crear asignacion"
        )

    @rx.var
    def placeholder_busqueda(self) -> str:
        if self.panel_es_configuracion:
            return "Buscar horario, supervisor o sede..."
        return "Buscar empleado, sede o categoria..."

    @rx.var
    def form_horario_dias_ui(self) -> List[dict]:
        filas = []
        for clave, etiqueta in DIAS_SEMANA:
            config = self.form_horario_dias_laborales.get(clave)
            filas.append(
                {
                    "clave": clave,
                    "label": etiqueta,
                    "habilitado": bool(config),
                    "entrada": config.get("entrada", "") if config else "",
                    "salida": config.get("salida", "") if config else "",
                }
            )
        return filas

    async def on_mount_asistencias(self):
        """Carga inicial del modulo."""
        resultado = await self.on_mount_portal()
        if resultado:
            self.loading = False
            yield resultado
            return
        if not self.mostrar_seccion_rrhh or not (
            self.es_operaciones or self.es_rrhh or self.es_admin_empresa
        ):
            yield rx.redirect("/portal")
            return
        async for _ in self._montar_pagina(self._cargar_contexto_inicial):
            yield

    async def _cargar_contexto_inicial(self):
        if not self.id_empresa_actual:
            return
        if self.puede_precargar_rrhh and not self.puede_operar_jornada:
            self.panel_activo = "rrhh"
        elif self.puede_operar_jornada:
            self.panel_activo = "operacion"
        elif self.puede_configurar_catalogos:
            self.panel_activo = "configuracion"

        self.contratos_disponibles = await asistencia_service.obtener_contratos_operacion(
            self.id_empresa_actual
        )
        if not self.contrato_seleccionado_id and self.contratos_disponibles:
            self.contrato_seleccionado_id = int(self.contratos_disponibles[0]["id"])
        await self._cargar_panel()

    async def _cargar_panel(self):
        if not self.id_empresa_actual or not self.contrato_seleccionado_id:
            self._limpiar_panel_operativo()
            self._limpiar_panel_configuracion()
            return

        if self.panel_es_configuracion:
            configuracion = await asistencia_service.obtener_configuracion_asistencias(
                empresa_id=self.id_empresa_actual,
                contrato_id=self.contrato_seleccionado_id,
            )
            self._limpiar_panel_operativo()
            self.horarios_configuracion = configuracion.get("horarios", [])
            self.asignaciones_supervision = configuracion.get("asignaciones", [])
            self.supervisores_disponibles = configuracion.get("supervisores", [])
            self.sedes_catalogo = configuracion.get("sedes", [])
            return

        self._limpiar_panel_configuracion()
        if self.panel_es_rrhh:
            panel = await asistencia_service.obtener_panel_rrhh(
                empresa_id=self.id_empresa_actual,
                contrato_id=self.contrato_seleccionado_id,
                fecha=self._fecha_actual(),
            )
        else:
            panel = await asistencia_service.obtener_panel_operacion(
                empresa_id=self.id_empresa_actual,
                contrato_id=self.contrato_seleccionado_id,
                user_id=self.id_usuario,
                fecha=self._fecha_actual(),
            )
        self.supervisor_actual = panel.get("supervisor", {})
        self.sedes_supervision = panel.get("sedes_supervision", [])
        self.horario_activo = panel.get("horario", {})
        self.jornada_actual = panel.get("jornada", {})
        self.empleados_jornada = panel.get("empleados", [])
        self.incidencias_jornada = panel.get("incidencias", [])

    async def cambiar_panel_activo(self, value: str):
        """Alterna entre paneles del modulo."""
        if value not in ("operacion", "rrhh", "configuracion"):
            return
        if value == "rrhh" and not self.puede_precargar_rrhh:
            return
        if value == "operacion" and not self.puede_operar_jornada:
            return
        if value == "configuracion" and not self.puede_configurar_catalogos:
            return
        self.panel_activo = value
        await self._cargar_panel()

    async def recargar_panel(self):
        """Recarga datos del panel."""
        async for _ in self._recargar_datos(self._cargar_panel):
            yield

    async def cambiar_contrato(self, value: str):
        """Selecciona contrato y recarga."""
        try:
            self.contrato_seleccionado_id = int(value) if value else 0
        except (TypeError, ValueError):
            self.contrato_seleccionado_id = 0
        await self._cargar_panel()

    async def cambiar_fecha_operacion(self, value: str):
        """Actualiza fecha de operacion."""
        self.fecha_operacion = value or date.today().isoformat()
        await self._cargar_panel()

    async def abrir_jornada(self):
        """Abre la jornada del dia para el contrato actual."""
        self.saving = True
        try:
            await asistencia_service.abrir_jornada(
                JornadaAsistenciaCreate(
                    empresa_id=self.id_empresa_actual,
                    contrato_id=self.contrato_seleccionado_id,
                    fecha=self._fecha_actual(),
                ),
                user_id=self.id_usuario,
            )
            await self._cargar_panel()
            return rx.toast.success("Jornada abierta")
        except Exception as e:
            return self.manejar_error_con_toast(e, "abriendo jornada")
        finally:
            self.saving = False

    async def cerrar_jornada(self):
        """Cierra y consolida la jornada del dia."""
        self.saving = True
        try:
            await asistencia_service.cerrar_jornada(
                empresa_id=self.id_empresa_actual,
                contrato_id=self.contrato_seleccionado_id,
                user_id=self.id_usuario,
                fecha=self._fecha_actual(),
            )
            await self._cargar_panel()
            return rx.toast.success("Jornada consolidada")
        except Exception as e:
            return self.manejar_error_con_toast(e, "cerrando jornada")
        finally:
            self.saving = False

    def abrir_modal_incidencia(self, empleado: dict):
        """Prepara modal para crear o editar incidencia."""
        self.empleado_seleccionado = empleado
        self.form_tipo_incidencia = empleado.get("tipo_incidencia") or TipoIncidencia.FALTA.value
        self.form_minutos_retardo = str(empleado.get("minutos_retardo", 0) or 0)
        self.form_horas_extra = str(empleado.get("horas_extra", 0) or 0)
        self.form_motivo = empleado.get("motivo", "") or ""
        self.modal_incidencia_abierto = True

    def cerrar_modal_incidencia(self):
        """Cierra modal y limpia seleccion."""
        self.modal_incidencia_abierto = False
        self.empleado_seleccionado = {}
        self.form_tipo_incidencia = TipoIncidencia.FALTA.value
        self.form_minutos_retardo = "0"
        self.form_horas_extra = "0"
        self.form_motivo = ""

    def set_form_tipo_incidencia(self, value: str):
        self.form_tipo_incidencia = value

    def set_form_minutos_retardo(self, value: str):
        self.form_minutos_retardo = value or "0"

    def set_form_horas_extra(self, value: str):
        self.form_horas_extra = value or "0"

    def set_form_motivo(self, value: str):
        self.form_motivo = value

    async def guardar_incidencia(self):
        """Persistencia de incidencia desde modal."""
        if not self.empleado_seleccionado:
            return rx.toast.error("Selecciona un empleado")
        self.saving = True
        try:
            datos = IncidenciaAsistenciaCreate(
                empleado_id=int(self.empleado_seleccionado["empleado_id"]),
                empresa_id=self.id_empresa_actual,
                fecha=self._fecha_actual(),
                tipo_incidencia=TipoIncidencia(self.form_tipo_incidencia),
                minutos_retardo=self._parse_int(self.form_minutos_retardo),
                horas_extra=self._parse_decimal(self.form_horas_extra),
                motivo=(self.form_motivo or "").strip() or None,
            )
            if self.panel_es_rrhh:
                await asistencia_service.guardar_precarga_rh(
                    empresa_id=self.id_empresa_actual,
                    contrato_id=self.contrato_seleccionado_id,
                    user_id=self.id_usuario,
                    fecha=self._fecha_actual(),
                    datos=datos,
                )
            else:
                await asistencia_service.guardar_incidencia(
                    empresa_id=self.id_empresa_actual,
                    contrato_id=self.contrato_seleccionado_id,
                    user_id=self.id_usuario,
                    fecha=self._fecha_actual(),
                    datos=datos,
                )
            self.cerrar_modal_incidencia()
            await self._cargar_panel()
            return rx.toast.success(
                "Precarga RH guardada" if self.panel_es_rrhh else "Incidencia guardada"
            )
        except (BusinessRuleError, ValueError, InvalidOperation) as e:
            return rx.toast.error(str(e))
        except Exception as e:
            return self.manejar_error_con_toast(e, "guardando incidencia")
        finally:
            self.saving = False

    async def limpiar_incidencia(self, empleado: dict):
        """Elimina incidencia de un empleado para la fecha."""
        self.saving = True
        try:
            if self.panel_es_rrhh:
                await asistencia_service.eliminar_precarga_rh(
                    empresa_id=self.id_empresa_actual,
                    contrato_id=self.contrato_seleccionado_id,
                    empleado_id=int(empleado["empleado_id"]),
                    fecha=self._fecha_actual(),
                )
            else:
                await asistencia_service.eliminar_incidencia(
                    empresa_id=self.id_empresa_actual,
                    contrato_id=self.contrato_seleccionado_id,
                    user_id=self.id_usuario,
                    empleado_id=int(empleado["empleado_id"]),
                    fecha=self._fecha_actual(),
                )
            await self._cargar_panel()
            return rx.toast.success(
                "Precarga RH eliminada" if self.panel_es_rrhh else "Incidencia eliminada"
            )
        except (BusinessRuleError, NotFoundError) as e:
            return rx.toast.error(str(e))
        except Exception as e:
            return self.manejar_error_con_toast(e, "eliminando incidencia")
        finally:
            self.saving = False

    def abrir_modal_horario_crear(self):
        """Abre modal para crear horario."""
        self.horario_editando_id = 0
        self.form_horario_nombre = ""
        self.form_horario_descripcion = ""
        self.form_horario_tolerancia_entrada = "10"
        self.form_horario_tolerancia_salida = "0"
        self.form_horario_activo = True
        self.form_horario_dias_laborales = _horario_dias_default()
        self.modal_horario_abierto = True

    def abrir_modal_horario_editar(self, horario: dict):
        """Abre modal para editar horario existente."""
        self.horario_editando_id = int(horario.get("id", 0) or 0)
        self.form_horario_nombre = horario.get("nombre", "") or ""
        self.form_horario_descripcion = horario.get("descripcion", "") or ""
        self.form_horario_tolerancia_entrada = str(
            horario.get("tolerancia_entrada_min", 10) or 10
        )
        self.form_horario_tolerancia_salida = str(
            horario.get("tolerancia_salida_min", 0) or 0
        )
        self.form_horario_activo = bool(horario.get("es_horario_activo"))
        self.form_horario_dias_laborales = self._normalizar_form_dias(
            horario.get("dias_laborales")
        )
        self.modal_horario_abierto = True

    def cerrar_modal_horario(self):
        """Cierra modal de horario."""
        self.modal_horario_abierto = False
        self.horario_editando_id = 0
        self.form_horario_nombre = ""
        self.form_horario_descripcion = ""
        self.form_horario_tolerancia_entrada = "10"
        self.form_horario_tolerancia_salida = "0"
        self.form_horario_activo = True
        self.form_horario_dias_laborales = _horario_dias_default()

    def set_form_horario_nombre(self, value: str):
        self.form_horario_nombre = value

    def set_form_horario_descripcion(self, value: str):
        self.form_horario_descripcion = value

    def set_form_horario_tolerancia_entrada(self, value: str):
        self.form_horario_tolerancia_entrada = value or "0"

    def set_form_horario_tolerancia_salida(self, value: str):
        self.form_horario_tolerancia_salida = value or "0"

    def set_form_horario_activo(self, value: bool):
        self.form_horario_activo = bool(value)

    def set_form_horario_dia_habilitado(self, dia: str, value: bool):
        dias = self._normalizar_form_dias(self.form_horario_dias_laborales)
        if value:
            dias[dia] = (HORARIO_DIAS_BASE.get(dia) or {"entrada": "07:00", "salida": "15:00"}).copy()
        else:
            dias[dia] = None
        self.form_horario_dias_laborales = dias

    def set_form_horario_dia_hora(self, dia: str, campo: str, value: str):
        dias = self._normalizar_form_dias(self.form_horario_dias_laborales)
        actual = dias.get(dia) or {"entrada": "", "salida": ""}
        actual[campo] = value
        dias[dia] = actual
        self.form_horario_dias_laborales = dias

    async def guardar_horario(self):
        """Crea o actualiza un horario del contrato."""
        if not self.contrato_seleccionado_id:
            return rx.toast.error("Selecciona un contrato antes de guardar el horario")
        self.saving = True
        try:
            datos = HorarioCreate(
                empresa_id=self.id_empresa_actual,
                contrato_id=self.contrato_seleccionado_id,
                nombre=(self.form_horario_nombre or "").strip(),
                descripcion=(self.form_horario_descripcion or "").strip() or None,
                dias_laborales=self.form_horario_dias_laborales,
                tolerancia_entrada_min=self._parse_int(self.form_horario_tolerancia_entrada),
                tolerancia_salida_min=self._parse_int(self.form_horario_tolerancia_salida),
                es_horario_activo=self.form_horario_activo,
                estatus=(
                    Estatus.ACTIVO if self.form_horario_activo else Estatus.INACTIVO
                ),
            )
            await asistencia_service.guardar_horario(self.horario_editando_id or None, datos)
            self.cerrar_modal_horario()
            await self._cargar_panel()
            return rx.toast.success("Horario guardado")
        except (BusinessRuleError, ValueError) as e:
            return rx.toast.error(str(e))
        except Exception as e:
            return self.manejar_error_con_toast(e, "guardando horario")
        finally:
            self.saving = False

    async def desactivar_horario(self, horario_id: int):
        """Desactiva un horario del contrato."""
        self.saving = True
        try:
            await asistencia_service.desactivar_horario(
                empresa_id=self.id_empresa_actual,
                horario_id=horario_id,
            )
            await self._cargar_panel()
            return rx.toast.success("Horario desactivado")
        except Exception as e:
            return self.manejar_error_con_toast(e, "desactivando horario")
        finally:
            self.saving = False

    def abrir_modal_supervision_crear(self):
        """Abre modal para crear asignacion supervisor-sede."""
        self.supervision_editando_id = 0
        self.form_supervision_supervisor_id = ""
        self.form_supervision_sede_id = ""
        self.form_supervision_fecha_inicio = date.today().isoformat()
        self.form_supervision_fecha_fin = ""
        self.form_supervision_activo = True
        self.form_supervision_notas = ""
        self.modal_supervision_abierto = True

    def abrir_modal_supervision_editar(self, asignacion: dict):
        """Abre modal para editar asignacion supervisor-sede."""
        self.supervision_editando_id = int(asignacion.get("id", 0) or 0)
        self.form_supervision_supervisor_id = str(asignacion.get("supervisor_id", "") or "")
        self.form_supervision_sede_id = str(asignacion.get("sede_id", "") or "")
        self.form_supervision_fecha_inicio = asignacion.get("fecha_inicio", "") or date.today().isoformat()
        self.form_supervision_fecha_fin = asignacion.get("fecha_fin", "") or ""
        self.form_supervision_activo = bool(asignacion.get("activo"))
        self.form_supervision_notas = asignacion.get("notas", "") or ""
        self.modal_supervision_abierto = True

    def cerrar_modal_supervision(self):
        """Cierra modal de asignacion supervisor-sede."""
        self.modal_supervision_abierto = False
        self.supervision_editando_id = 0
        self.form_supervision_supervisor_id = ""
        self.form_supervision_sede_id = ""
        self.form_supervision_fecha_inicio = date.today().isoformat()
        self.form_supervision_fecha_fin = ""
        self.form_supervision_activo = True
        self.form_supervision_notas = ""

    def set_form_supervision_supervisor_id(self, value: str):
        self.form_supervision_supervisor_id = value

    def set_form_supervision_sede_id(self, value: str):
        self.form_supervision_sede_id = value

    def set_form_supervision_fecha_inicio(self, value: str):
        self.form_supervision_fecha_inicio = value or date.today().isoformat()

    def set_form_supervision_fecha_fin(self, value: str):
        self.form_supervision_fecha_fin = value or ""

    def set_form_supervision_activo(self, value: bool):
        self.form_supervision_activo = bool(value)

    def set_form_supervision_notas(self, value: str):
        self.form_supervision_notas = value

    async def guardar_supervision(self):
        """Crea o actualiza una asignacion supervisor-sede."""
        self.saving = True
        try:
            datos = SupervisorSedeCreate(
                empresa_id=self.id_empresa_actual,
                supervisor_id=int(self.form_supervision_supervisor_id or 0),
                sede_id=int(self.form_supervision_sede_id or 0),
                fecha_inicio=date.fromisoformat(self.form_supervision_fecha_inicio),
                fecha_fin=(
                    date.fromisoformat(self.form_supervision_fecha_fin)
                    if self.form_supervision_fecha_fin
                    else None
                ),
                activo=self.form_supervision_activo,
                notas=(self.form_supervision_notas or "").strip() or None,
            )
            await asistencia_service.guardar_supervision(
                self.supervision_editando_id or None,
                datos,
            )
            self.cerrar_modal_supervision()
            await self._cargar_panel()
            return rx.toast.success("Asignacion guardada")
        except (BusinessRuleError, ValueError) as e:
            return rx.toast.error(str(e))
        except Exception as e:
            return self.manejar_error_con_toast(e, "guardando asignacion")
        finally:
            self.saving = False

    async def desactivar_supervision(self, asignacion_id: int):
        """Desactiva una asignacion supervisor-sede."""
        self.saving = True
        try:
            await asistencia_service.desactivar_supervision(
                empresa_id=self.id_empresa_actual,
                asignacion_id=asignacion_id,
            )
            await self._cargar_panel()
            return rx.toast.success("Asignacion desactivada")
        except Exception as e:
            return self.manejar_error_con_toast(e, "desactivando asignacion")
        finally:
            self.saving = False

    def _limpiar_panel_operativo(self):
        self.supervisor_actual = {}
        self.sedes_supervision = []
        self.horario_activo = {}
        self.jornada_actual = {}
        self.empleados_jornada = []
        self.incidencias_jornada = []

    def _limpiar_panel_configuracion(self):
        self.horarios_configuracion = []
        self.asignaciones_supervision = []
        self.supervisores_disponibles = []
        self.sedes_catalogo = []

    @staticmethod
    def _normalizar_form_dias(dias: dict | None) -> dict:
        base = _horario_dias_default()
        for dia, config in (dias or {}).items():
            base[dia] = config.copy() if isinstance(config, dict) else None
        return base

    @staticmethod
    def _parse_int(value: str) -> int:
        try:
            return int(value or "0")
        except (TypeError, ValueError):
            return 0

    @staticmethod
    def _parse_decimal(value: str) -> Decimal:
        return Decimal(str(value or "0"))

    def _fecha_actual(self) -> date:
        return date.fromisoformat(self.fecha_operacion)
