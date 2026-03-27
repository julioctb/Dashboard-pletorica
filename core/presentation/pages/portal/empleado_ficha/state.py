"""State para la ficha de empleado en el portal de clientes."""

from datetime import date
import logging
from typing import Optional

import reflex as rx

from core.modules.empleados.domain.enums import TipoDocumentoEmpleado, TipoMovimientoHistorial
from core.core.text_utils import (
    capitalizar_palabras,
    formatear_fecha,
    formatear_telefono,
    normalizar_email,
    normalizar_mayusculas,
    obtener_iniciales,
)
from core.database import db_manager
from core.modules.empleados.application import empleado_service, historial_laboral_service
from core.presentation.components.shared import EmployeeExpedienteStateMixin
from core.presentation.pages.portal.state.portal_state import PortalState
from core.domain.services import (
    asistencia_service,
    categoria_puesto_service,
    contrato_service,
    plaza_service,
    sede_service,
)

logger = logging.getLogger(__name__)


class EmpleadoFichaState(PortalState, EmployeeExpedienteStateMixin):
    """State para la ficha detallada de un empleado en el portal."""

    empleado_uuid: str = ""
    empleado: dict = {}
    empleado_cargado: bool = False
    error: str = ""

    plaza_actual: dict = {}
    tiene_plaza: bool = False

    documentos_obligatorios: list[dict] = []
    documentos_opcionales: list[dict] = []
    total_requeridos: int = 0
    total_aprobados: int = 0
    total_pendientes: int = 0
    total_rechazados: int = 0
    progreso_porcentaje: int = 0

    mostrar_modal_subir: bool = False
    tipo_documento_subiendo: str = ""
    subiendo_archivo: bool = False

    mostrar_modal_preview: bool = False
    preview_url: str = ""
    preview_tipo_mime: str = ""
    preview_nombre_archivo: str = ""

    mostrar_modal_rechazo: bool = False
    documento_rechazando_id: int = 0
    form_observacion_rechazo: str = ""
    error_observacion: str = ""

    historial: list[dict] = []
    historial_reciente: list[dict] = []

    faltas_mes: int = 0
    faltas_totales: int = 0
    incapacidades: int = 0
    horario: str = "—"
    tipo_pago: str = "—"

    tab_activa: str = "resumen"

    def _limpiar_ficha(self) -> None:
        self.empleado_uuid = ""
        self.empleado = {}
        self.empleado_cargado = False
        self.error = ""
        self.plaza_actual = {}
        self.tiene_plaza = False
        self._reset_expediente_documental_state()
        self.historial = []
        self.historial_reciente = []
        self.faltas_mes = 0
        self.faltas_totales = 0
        self.incapacidades = 0
        self.horario = "—"
        self.tipo_pago = "—"
        self.tab_activa = "resumen"

    def _ruta_actual(self) -> str:
        """Obtiene la ruta actual sin query string."""
        try:
            path = str(getattr(getattr(self.router, "url", None), "path", "") or "").strip()
        except Exception:
            path = ""

        if not path:
            router_data = self.router_data or {}
            path = str(
                router_data.get("asPath")
                or router_data.get("pathname")
                or "",
            ).strip()

        return path.split("?", maxsplit=1)[0]

    def _es_ruta_listado_empleados(self) -> bool:
        """Indica si el state se está evaluando sobre el listado base."""
        return self._ruta_actual() == "/portal/empleados"

    def _es_ruta_ficha_empleado(self) -> bool:
        """Indica si la ruta actual corresponde a la ficha dinámica."""
        ruta_actual = self._ruta_actual()
        if ruta_actual.startswith("/portal/empleados/"):
            return True

        router_data = self.router_data or {}
        pathname = str(router_data.get("pathname", "") or "").strip()
        return pathname == "/portal/empleados/[id]"

    def _obtener_uuid_ruta(self) -> str:
        """Obtiene el uuid/id desde el parámetro dinámico de ruta [id]."""
        uuid = ""

        # 1. DynamicRouteVar inyectado por Reflex desde la ruta [id].
        try:
            raw = getattr(self, "id", None)
            if raw is not None and callable(raw) is False:
                uuid = str(raw).strip()
                logger.debug("[ficha] id via DynamicRouteVar: %r", uuid)
        except Exception:
            uuid = ""

        # 2. Fallback: query params (Next.js almacena route params aquí).
        if not uuid:
            router_data = self.router_data or {}
            posibles_ids = [
                (router_data.get("query", {}) or {}).get("id", ""),
                (router_data.get("params", {}) or {}).get("id", ""),
                (router_data.get("path_params", {}) or {}).get("id", ""),
                (router_data.get("kwargs", {}) or {}).get("id", ""),
            ]
            for raw_id in posibles_ids:
                uuid = str(raw_id or "").strip()
                if uuid:
                    logger.debug("[ficha] id via router_data: %r", uuid)
                    break

        # 3. Fallback: parsear segmento de URL directamente.
        if not uuid and self._es_ruta_ficha_empleado():
            try:
                path = self._ruta_actual()
                parts = [segmento for segmento in path.strip("/").split("/") if segmento]
                if (
                    len(parts) >= 3
                    and parts[0] == "portal"
                    and parts[1] == "empleados"
                ):
                    uuid = str(parts[2] or "").strip()
                    logger.debug("[ficha] id via URL path: %r", uuid)
            except Exception:
                uuid = ""

        if not uuid:
            if self._es_ruta_listado_empleados():
                logger.debug("[ficha] State evaluado en listado base; no se requiere id de ruta.")
            else:
                logger.warning(
                    "[ficha] No se pudo extraer id de ruta. router_data keys=%s, url=%s",
                    list((self.router_data or {}).keys()),
                    self._ruta_actual() or "N/A",
                )

        return uuid

    def set_tab(self, valor: str):
        """Cambia la tab activa."""
        self.tab_activa = valor or "resumen"

    @rx.var
    def tipos_documento_disponibles(self) -> list[dict]:
        """Opciones de documento para selects del expediente."""
        return [
            {"value": tipo.value, "label": tipo.descripcion}
            for tipo in TipoDocumentoEmpleado
        ]

    @rx.var
    def preview_es_imagen(self) -> bool:
        return self.preview_tipo_mime.startswith("image/")

    @rx.var
    def preview_es_pdf(self) -> bool:
        return self.preview_tipo_mime == "application/pdf"

    @rx.var
    def documentos_expediente_lista(self) -> list[dict]:
        return [*self.documentos_obligatorios, *self.documentos_opcionales]

    def set_form_observacion_rechazo(self, value: str) -> None:
        EmployeeExpedienteStateMixin.set_form_observacion_rechazo(self, value)

    def set_tipo_documento_subiendo(self, value: str) -> None:
        EmployeeExpedienteStateMixin.set_tipo_documento_subiendo(self, value)

    def set_mostrar_modal_subir(self, value: bool):
        return EmployeeExpedienteStateMixin.set_mostrar_modal_subir(self, value)

    def abrir_modal_subir(self):
        return EmployeeExpedienteStateMixin.abrir_modal_subir(self)

    def abrir_subir(self, tipo_documento: str):
        return EmployeeExpedienteStateMixin.abrir_subir(self, tipo_documento)

    def cerrar_modal_subir(self):
        return EmployeeExpedienteStateMixin.cerrar_modal_subir(self)

    async def ver_documento(self, doc: dict):
        return await EmployeeExpedienteStateMixin.ver_documento(self, doc)

    async def descargar_documento(self, doc: dict):
        return await EmployeeExpedienteStateMixin.descargar_documento(self, doc)

    def cerrar_modal_preview(self) -> None:
        EmployeeExpedienteStateMixin.cerrar_modal_preview(self)

    async def handle_upload_documento(self, files: list[rx.UploadFile]):
        return await EmployeeExpedienteStateMixin.handle_upload_documento(self, files)

    async def aprobar_documento(self, doc: dict):
        return await EmployeeExpedienteStateMixin.aprobar_documento(self, doc)

    def abrir_modal_rechazo(self, doc: dict) -> None:
        EmployeeExpedienteStateMixin.abrir_modal_rechazo(self, doc)

    def cerrar_modal_rechazo(self) -> None:
        EmployeeExpedienteStateMixin.cerrar_modal_rechazo(self)

    async def confirmar_rechazo(self):
        return await EmployeeExpedienteStateMixin.confirmar_rechazo(self)

    async def on_mount_empleado_ficha(self):
        """Monta la ficha validando contexto de portal."""
        if self._es_ruta_listado_empleados():
            logger.debug("[ficha] on_mount omitido fuera de ruta detalle: %s", self._ruta_actual())
            return

        resultado = await self.on_mount_portal()
        if resultado:
            self.loading = False
            yield resultado
            return

        puede_ver_ficha = (
            self.puede_acceder_rrhh
            or self.puede_registrar_personal
            or self.es_contabilidad
            or self.es_institucion
        )
        if not (self.mostrar_seccion_rrhh or self.es_contabilidad) or not puede_ver_ficha:
            yield rx.redirect("/portal")
            return

        async for _ in self._montar_pagina(self.cargar_ficha):
            yield

        if self.empleado_cargado:
            empleado_id = int(self.empleado.get("id") or 0)
            if empleado_id > 0:
                from core.presentation.pages.portal.incapacidades import IncapacidadState

                yield IncapacidadState.cargar_por_empleado(empleado_id)

        if not self.error and not self.empleado_cargado:
            yield rx.redirect("/portal/empleados", replace=True)

    async def cargar_ficha(self):
        """Carga datos agregados de la ficha del empleado.

        No gestiona self.loading — _montar_pagina se encarga.
        """
        self.error = ""
        self.empleado_cargado = False

        try:
            empleado_uuid = self._obtener_uuid_ruta()
            logger.info("[ficha] uuid obtenido: %r", empleado_uuid)
            if not empleado_uuid:
                self.error = "No se proporcionó identificador de empleado."
                return

            await self._cargar_empleado(empleado_uuid)
            if not self.empleado_cargado:
                return

            empleado_id = int(self.empleado.get("id") or 0)
            if empleado_id <= 0:
                self.error = "No se pudo resolver el empleado solicitado."
                return

            await self._cargar_plaza_actual(empleado_id)
            await self._cargar_documentos_expediente(empleado_id)
            await self._cargar_historial(empleado_id)
            await self._cargar_asistencias(empleado_id)
        except Exception as e:
            logger.error("[ficha] Error cargando ficha: %s", e, exc_info=True)
            self.error = f"Error al cargar la ficha: {str(e)}"

    async def _cargar_empleado(self, empleado_uuid: str):
        """Carga empleado por UUID con validación de empresa activa."""
        self._limpiar_ficha()
        self.empleado_uuid = empleado_uuid

        empleado = await empleado_service.obtener_por_uuid(empleado_uuid)
        if not empleado and str(empleado_uuid).isdigit():
            try:
                empleado = await empleado_service.obtener_por_id(int(empleado_uuid))
            except Exception:
                empleado = None

        if not empleado:
            self.error = "Empleado no encontrado."
            return

        if (
            self.id_empresa_actual
            and int(empleado.empresa_id or 0) != int(self.id_empresa_actual or 0)
        ):
            self.error = "No tienes acceso a este empleado."
            return

        genero = str(empleado.genero or "")
        if genero:
            genero = capitalizar_palabras(genero.replace("_", " ").lower())

        entidad_nacimiento = capitalizar_palabras(str(empleado.entidad_nacimiento or ""))
        nombre = capitalizar_palabras(str(empleado.nombre or ""))
        apellido_paterno = capitalizar_palabras(str(empleado.apellido_paterno or ""))
        apellido_materno = capitalizar_palabras(str(empleado.apellido_materno or ""))

        self.empleado = {
            "id": empleado.id,
            "uuid": str(empleado.uuid) if empleado.uuid else empleado_uuid,
            "clave": str(empleado.clave or ""),
            "nombre": nombre,
            "apellido_paterno": apellido_paterno,
            "apellido_materno": apellido_materno,
            "curp": normalizar_mayusculas(empleado.curp),
            "rfc": normalizar_mayusculas(str(empleado.rfc or "")),
            "nss": normalizar_mayusculas(str(empleado.nss or "")),
            "email": normalizar_email(str(empleado.email or "")),
            "telefono": formatear_telefono(str(empleado.telefono or "")),
            "direccion": str(empleado.direccion or ""),
            "contacto_emergencia": str(empleado.contacto_emergencia or ""),
            "fecha_nacimiento": formatear_fecha(empleado.fecha_nacimiento, valor_vacio="—"),
            "fecha_ingreso": formatear_fecha(empleado.fecha_ingreso, valor_vacio="—"),
            "fecha_ingreso_vigente": formatear_fecha(
                empleado.fecha_ingreso_vigente,
                valor_vacio="—",
            ),
            "estatus": str(empleado.estatus or "INACTIVO"),
            "genero": genero or "—",
            "entidad_nacimiento": entidad_nacimiento or "—",
            "renapo_validado": bool(empleado.renapo_validado),
            "banco": str(empleado.banco or ""),
            "cuenta_bancaria": str(empleado.cuenta_bancaria or ""),
            "clabe_interbancaria": str(empleado.clabe_interbancaria or ""),
            "tipo_pago": str(getattr(empleado, "tipo_pago", "") or ""),
        }
        self.empleado_cargado = True

    async def _cargar_plaza_actual(self, empleado_id: int):
        """Carga la plaza activa del empleado (si existe)."""
        self.plaza_actual = {}
        self.tiene_plaza = False

        registro_activo = await historial_laboral_service.obtener_registro_activo(empleado_id)
        plaza_id = int(getattr(registro_activo, "plaza_id", 0) or 0)
        if plaza_id <= 0:
            plaza_id = await self._resolver_plaza_activa_por_ocupacion(empleado_id)
        if plaza_id <= 0:
            return

        plaza = await plaza_service.obtener_por_id(plaza_id)

        contrato_codigo = "—"
        vigencia_texto = "Sin vigencia"
        contrato_id = int(plaza.contrato_id or 0)
        if contrato_id > 0:
            try:
                contrato = await contrato_service.obtener_por_id(contrato_id)
                contrato_codigo = str(contrato.codigo or "—")
                contrato_inicio = formatear_fecha(contrato.fecha_inicio, valor_vacio="—")
                contrato_fin = formatear_fecha(contrato.fecha_fin, valor_vacio="—")
                if str(contrato_fin).strip() in {"", "—"}:
                    vigencia_texto = f"Desde {contrato_inicio}"
                else:
                    vigencia_texto = f"{contrato_inicio} a {contrato_fin}"
            except Exception:
                contrato_codigo = "—"
                vigencia_texto = "Sin vigencia"

        categoria_nombre = "Sin categoría"
        if plaza.categoria_puesto_id:
            try:
                categoria = await categoria_puesto_service.obtener_por_id(plaza.categoria_puesto_id)
                categoria_nombre = capitalizar_palabras(str(categoria.nombre or ""))
            except Exception:
                categoria_nombre = "Sin categoría"

        sede_nombre = "Sin sede"
        sede_codigo = ""
        if plaza.sede_id:
            try:
                sede = await sede_service.obtener_por_id(plaza.sede_id)
                sede_nombre = normalizar_mayusculas(str(sede.nombre or ""))
                sede_codigo = normalizar_mayusculas(str(sede.codigo or ""))
            except Exception:
                sede_nombre = "Sin sede"
                sede_codigo = ""

        tipo_movimiento = str(getattr(registro_activo, "tipo_movimiento", "") or "")
        tipo_movimiento_label = (
            TipoMovimientoHistorial.get_label(tipo_movimiento)
            if tipo_movimiento
            else "Asignación"
        )

        self.plaza_actual = {
            "historial_id": int(getattr(registro_activo, "id", 0) or 0),
            "plaza_id": plaza.id,
            "contrato_id": contrato_id,
            "numero_plaza": plaza.numero_plaza,
            "plaza_texto": (
                f"Plaza #{int(plaza.numero_plaza or 0)}"
                if plaza.numero_plaza is not None
                else "Plaza sin número"
            ),
            "numero_contrato": contrato_codigo,
            "vigencia_texto": vigencia_texto,
            "categoria_nombre": categoria_nombre,
            "sede_nombre": sede_nombre,
            "sede_codigo": sede_codigo,
            "fecha_inicio": formatear_fecha(
                getattr(registro_activo, "fecha_inicio", None) or plaza.fecha_inicio,
                valor_vacio="—",
            ),
            "tipo_movimiento": tipo_movimiento,
            "tipo_movimiento_label": tipo_movimiento_label,
        }
        self.tiene_plaza = True

    async def _resolver_plaza_activa_por_ocupacion(self, empleado_id: int) -> int:
        """Fallback para fichas con historial incompleto pero plaza ocupada en portal."""
        empresa_id = int(self.id_empresa_actual or 0)
        if empresa_id <= 0:
            return 0

        try:
            plazas_ocupadas = await plaza_service.obtener_resumen_ocupadas_por_empresa(
                empresa_id,
            )
        except Exception as exc:
            logger.warning(
                "[ficha] No se pudo resolver plaza ocupada por fallback para empleado %s: %s",
                empleado_id,
                exc,
            )
            return 0

        for plaza in plazas_ocupadas:
            if int(getattr(plaza, "empleado_id", 0) or 0) != int(empleado_id or 0):
                continue
            return int(getattr(plaza, "id", 0) or 0)
        return 0

    async def _cargar_historial(self, empleado_id: int):
        """Carga historial completo del empleado y resumen reciente."""
        supabase = db_manager.get_client()
        result = (
            supabase.table("historial_laboral")
            .select("id,empleado_id,plaza_id,tipo_movimiento,fecha_inicio,fecha_fin,notas")
            .eq("empleado_id", empleado_id)
            .order("fecha_inicio", desc=True)
            .execute()
        )
        rows = result.data or []

        plaza_ids = sorted(
            {
                int(row.get("plaza_id") or 0)
                for row in rows
                if int(row.get("plaza_id") or 0) > 0
            }
        )
        plazas_map: dict[int, dict] = {}
        if plaza_ids:
            plazas_resp = (
                supabase.table("plazas")
                .select(
                    "id,numero_plaza,"
                    "categorias_puesto:categoria_puesto_id(nombre),"
                    "sedes:sede_id(nombre,codigo)"
                )
                .in_("id", plaza_ids)
                .execute()
            )
            for plaza in plazas_resp.data or []:
                plazas_map[int(plaza.get("id") or 0)] = plaza

        historial_normalizado: list[dict] = []
        for row in rows:
            plaza_id = int(row.get("plaza_id") or 0)
            plaza = plazas_map.get(plaza_id, {}) if plaza_id > 0 else {}
            categoria = (plaza.get("categorias_puesto") or {}).get("nombre", "")
            sede = (plaza.get("sedes") or {}).get("nombre", "")
            sede_codigo = normalizar_mayusculas((plaza.get("sedes") or {}).get("codigo", ""))
            tipo_raw = str(row.get("tipo_movimiento") or "")

            if tipo_raw and tipo_raw in TipoMovimientoHistorial.__members__:
                tipo_label = TipoMovimientoHistorial.get_label(tipo_raw)
            elif tipo_raw:
                tipo_label = capitalizar_palabras(tipo_raw.replace("_", " ").lower())
            else:
                tipo_label = "Movimiento"

            descripcion_partes = []
            numero_plaza = plaza.get("numero_plaza")
            if numero_plaza is not None:
                descripcion_partes.append(f"Plaza #{numero_plaza}")
            if categoria:
                descripcion_partes.append(capitalizar_palabras(str(categoria)))
            if sede:
                sede_texto = normalizar_mayusculas(str(sede))
                if sede_codigo:
                    sede_texto = f"{sede_texto} ({sede_codigo})"
                descripcion_partes.append(sede_texto)

            descripcion = " · ".join(descripcion_partes) if descripcion_partes else "Sin plaza asignada"

            historial_normalizado.append(
                {
                    "id": int(row.get("id") or 0),
                    "tipo_movimiento": tipo_raw,
                    "tipo_label": tipo_label,
                    "fecha_inicio": row.get("fecha_inicio"),
                    "fecha_fin": row.get("fecha_fin"),
                    "fecha_texto": formatear_fecha(row.get("fecha_inicio"), valor_vacio="—"),
                    "descripcion": descripcion,
                    "notas": str(row.get("notas") or ""),
                }
            )

        self.historial = historial_normalizado
        self.historial_reciente = historial_normalizado[:3]

    async def _cargar_asistencias(self, empleado_id: int):
        """Carga métricas de incidencias y horario laboral."""
        self.faltas_mes = 0
        self.faltas_totales = 0
        self.incapacidades = 0
        self.horario = "—"
        self.tipo_pago = "—"

        supabase = db_manager.get_client()
        result = (
            supabase.table("incidencias_asistencia")
            .select("tipo_incidencia,fecha")
            .eq("empleado_id", empleado_id)
            .order("fecha", desc=True)
            .limit(2000)
            .execute()
        )
        incidencias = result.data or []

        hoy = date.today()
        inicio_mes = hoy.replace(day=1)
        if hoy.month == 12:
            inicio_mes_siguiente = date(hoy.year + 1, 1, 1)
        else:
            inicio_mes_siguiente = date(hoy.year, hoy.month + 1, 1)

        faltas = {"FALTA", "FALTA_JUSTIFICADA"}
        self.faltas_totales = sum(
            1 for inc in incidencias if str(inc.get("tipo_incidencia") or "") in faltas
        )
        self.faltas_mes = sum(
            1
            for inc in incidencias
            if str(inc.get("tipo_incidencia") or "") in faltas
            and str(inc.get("fecha") or "") >= inicio_mes.isoformat()
            and str(inc.get("fecha") or "") < inicio_mes_siguiente.isoformat()
        )
        self.incapacidades = sum(
            1
            for inc in incidencias
            if str(inc.get("tipo_incidencia") or "").startswith("INCAPACIDAD")
        )

        contrato_id = int(self.plaza_actual.get("contrato_id") or 0)
        if contrato_id > 0 and self.id_empresa_actual:
            try:
                horario_activo = await asistencia_service.obtener_horario_activo(
                    empresa_id=int(self.id_empresa_actual),
                    contrato_id=contrato_id,
                )
                if horario_activo and horario_activo.dias_laborales:
                    # Reutiliza el formateador central del módulo de asistencias.
                    self.horario = asistencia_service._resumir_dias_laborales(  # noqa: SLF001
                        horario_activo.dias_laborales
                    )
                elif horario_activo:
                    self.horario = str(horario_activo.nombre or "—")
            except Exception:
                self.horario = "—"

        tipo_pago = str(self.empleado.get("tipo_pago", "") or "").strip()
        # TODO: confirmar fuente definitiva de tipo_pago en el dominio de nómina.
        self.tipo_pago = capitalizar_palabras(tipo_pago.lower()) if tipo_pago else "—"

    @rx.var
    def nombre_completo(self) -> str:
        """Nombre completo del empleado."""
        if not self.empleado:
            return ""
        return " ".join(
            [
                str(self.empleado.get("nombre", "") or "").strip(),
                str(self.empleado.get("apellido_paterno", "") or "").strip(),
                str(self.empleado.get("apellido_materno", "") or "").strip(),
            ]
        ).strip()

    @rx.var
    def iniciales(self) -> str:
        """Iniciales para avatar."""
        return obtener_iniciales(self.nombre_completo, max_palabras=2, fallback="")

    @rx.var
    def estatus_empleado(self) -> str:
        """Estatus actual del empleado."""
        return str(self.empleado.get("estatus", "INACTIVO") or "INACTIVO")

    @rx.var
    def breadcrumb_items(self) -> list[dict]:
        """Items del breadcrumb dinámico."""
        items = [
            {"texto": "Portal", "href": "/portal"},
            {"texto": "Empleados", "href": "/portal/empleados"},
        ]
        if self.nombre_completo:
            items.append({"texto": self.nombre_completo, "href": ""})
        return items

    @rx.var
    def tiene_historial(self) -> bool:
        """Indica si existe historial laboral."""
        return len(self.historial) > 0
