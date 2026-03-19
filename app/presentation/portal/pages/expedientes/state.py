"""State para la pagina dedicada de expediente documental de empleados."""

from typing import List, Optional

import reflex as rx

from app.core.exceptions import BusinessRuleError, NotFoundError, ValidationError
from app.core.text_utils import capitalizar_palabras, obtener_iniciales
from app.presentation.portal.state.portal_state import PortalState
from app.services import empleado_service
from app.services.archivo_service import archivo_service
from app.services.empleado_documento_service import empleado_documento_service
from app.services.onboarding_service import onboarding_service

UPLOAD_ID_EXPEDIENTE = "upload_doc_expediente_rrhh"


class ExpedientesState(PortalState):
    """State de la pagina de expediente documental."""

    empleado_id: str = ""
    empleado: dict = {}
    documentos_empleado: List[dict] = []
    documentos_obligatorios: List[dict] = []
    documentos_opcionales: List[dict] = []

    total_requeridos: int = 0
    total_aprobados: int = 0
    total_pendientes: int = 0
    total_rechazados: int = 0
    progreso_porcentaje: int = 0

    expediente_status: dict = {}

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

    def set_form_observacion_rechazo(self, value: str):
        self.form_observacion_rechazo = value

    def set_tipo_documento_subiendo(self, value: str):
        self.tipo_documento_subiendo = value

    def set_mostrar_modal_subir(self, value: bool):
        self.mostrar_modal_subir = bool(value)

    @rx.var
    def tipos_documento_disponibles(self) -> list[dict]:
        """Lista de tipos de documento para selector de carga."""
        from app.core.enums import TipoDocumentoEmpleado

        return [{"value": t.value, "label": t.descripcion} for t in TipoDocumentoEmpleado]

    @rx.var
    def nombre_empleado_ui(self) -> str:
        """Nombre de empleado normalizado en Title Case."""
        return capitalizar_palabras(str(self.empleado.get("nombre_completo", "") or ""))

    @rx.var
    def iniciales_empleado(self) -> str:
        """Iniciales para avatar."""
        return obtener_iniciales(self.nombre_empleado_ui, max_palabras=2, fallback="?")

    @rx.var
    def clave_empleado(self) -> str:
        return str(self.empleado.get("clave", "") or "")

    @rx.var
    def estatus_empleado(self) -> str:
        raw = str(
            self.empleado.get("estatus_personal")
            or self.empleado.get("estatus")
            or ""
        )
        return raw

    @rx.var
    def estatus_empleado_label(self) -> str:
        mapping = {
            "ACTIVO": "Activo",
            "EN_ALTA": "En alta",
            "EN_BAJA": "En baja",
            "INACTIVO": "Inactivo",
            "SUSPENDIDO": "Suspendido",
        }
        raw = self.estatus_empleado
        if not raw:
            return "En alta"
        return mapping.get(raw, capitalizar_palabras(raw.replace("_", " ")))

    @rx.var
    def breadcrumb_items(self) -> list[dict]:
        return [
            {"texto": "Empleados", "href": "/portal/empleados"},
            {
                "texto": self.nombre_empleado_ui if self.nombre_empleado_ui else "Empleado",
                "href": "/portal/empleados",
            },
            {"texto": "Expediente", "href": ""},
        ]

    @rx.var
    def preview_es_imagen(self) -> bool:
        return self.preview_tipo_mime.startswith("image/")

    @rx.var
    def preview_es_pdf(self) -> bool:
        return self.preview_tipo_mime == "application/pdf"

    @rx.var
    def total_documentos_obligatorios(self) -> int:
        return len(self.documentos_obligatorios)

    @rx.var
    def total_documentos_opcionales(self) -> int:
        return len(self.documentos_opcionales)

    @rx.var
    def documentos_expediente_lista(self) -> list[dict]:
        """Lista total para compatibilidad con usos existentes."""
        return [*self.documentos_obligatorios, *self.documentos_opcionales]

    def _obtener_empleado_id_ruta(self) -> Optional[int]:
        """Obtiene empleado_id desde ruta dinamica y mantiene fallback legacy."""
        router_data = self.router_data or {}

        posibles_ids = [
            getattr(self, "id", ""),
            getattr(self, "empleado_id", ""),
            (router_data.get("params", {}) or {}).get("id", ""),
            (router_data.get("path_params", {}) or {}).get("id", ""),
            (router_data.get("kwargs", {}) or {}).get("id", ""),
        ]

        # Compatibilidad con enlace legacy basado en query param.
        posibles_ids.append((router_data.get("query", {}) or {}).get("empleado_id", ""))

        for raw_id in posibles_ids:
            try:
                empleado_id = int(raw_id)
                if empleado_id > 0:
                    return empleado_id
            except (TypeError, ValueError):
                continue

        return None

    @staticmethod
    def _serializar_empleado_detalle(empleado) -> dict:
        """Convierte entidad de empleado a diccionario serializable para UI."""
        return {
            "id": empleado.id,
            "clave": empleado.clave,
            "nombre_completo": empleado.nombre_completo(),
            "empresa_id": empleado.empresa_id,
            "estatus_personal": str(getattr(empleado, "estatus", "") or ""),
        }

    def _limpiar_detalle_expediente(self):
        """Limpia estado de expediente para evitar residuos entre navegaciones."""
        self.empleado_id = ""
        self.empleado = {}
        self.documentos_empleado = []
        self.documentos_obligatorios = []
        self.documentos_opcionales = []
        self.expediente_status = {}

        self.total_requeridos = 0
        self.total_aprobados = 0
        self.total_pendientes = 0
        self.total_rechazados = 0
        self.progreso_porcentaje = 0

        self.mostrar_modal_subir = False
        self.tipo_documento_subiendo = ""
        self.subiendo_archivo = False

        self.cerrar_modal_preview()
        self.cerrar_modal_rechazo()

    def _recalcular_documentos(self):
        """Construye el checklist completo y separa obligatorios/opcionales."""
        from app.core.enums import TipoDocumentoEmpleado

        docs_por_tipo = {
            str(doc.get("tipo_documento") or ""): doc for doc in self.documentos_empleado
        }

        lista_completa: list[dict] = []
        for tipo in TipoDocumentoEmpleado:
            doc_existente = docs_por_tipo.get(tipo.value, {}) or {}
            subido = bool(doc_existente.get("id") or doc_existente.get("archivo_id"))

            lista_completa.append(
                {
                    **doc_existente,
                    "tipo_documento": tipo.value,
                    "tipo_documento_label": tipo.descripcion,
                    "obligatorio": tipo.es_obligatorio,
                    "subido": subido,
                    "estatus": str(doc_existente.get("estatus") or ""),
                    "version_texto": (
                        f"v{int(doc_existente.get('version', 1) or 1)}"
                        if subido
                        else "—"
                    ),
                }
            )

        self.documentos_obligatorios = [d for d in lista_completa if d.get("obligatorio", False)]
        self.documentos_opcionales = [d for d in lista_completa if not d.get("obligatorio", False)]

        self.total_requeridos = int(
            self.expediente_status.get("documentos_requeridos", len(self.documentos_obligatorios))
            or 0
        )
        self.total_aprobados = int(self.expediente_status.get("documentos_aprobados", 0) or 0)
        self.total_pendientes = int(self.expediente_status.get("pendientes", 0) or 0)
        self.total_rechazados = int(
            self.expediente_status.get("documentos_rechazados", 0) or 0
        )

        if not self.expediente_status:
            self.total_aprobados = sum(
                1 for doc in self.documentos_obligatorios if doc.get("estatus") == "APROBADO"
            )
            self.total_pendientes = sum(
                1
                for doc in self.documentos_obligatorios
                if doc.get("estatus") == "PENDIENTE_REVISION"
            )
            self.total_rechazados = sum(
                1 for doc in self.documentos_obligatorios if doc.get("estatus") == "RECHAZADO"
            )

        porcentaje_calculado = 0
        if self.total_requeridos > 0:
            porcentaje_calculado = int((self.total_aprobados / self.total_requeridos) * 100)

        porcentaje_fuente = int(self.expediente_status.get("porcentaje_completado", porcentaje_calculado) or 0)
        self.progreso_porcentaje = max(0, min(100, porcentaje_fuente))

    async def _cargar_expediente_desde_ruta(self):
        """Carga empleado y expediente usando el ID de la ruta dinámica."""
        empleado_id = self._obtener_empleado_id_ruta()
        if not empleado_id:
            self._limpiar_detalle_expediente()
            return

        self.empleado_id = str(empleado_id)

        try:
            empleado = await empleado_service.obtener_por_id(empleado_id)
        except NotFoundError:
            self._limpiar_detalle_expediente()
            return
        except Exception as e:
            self.mostrar_mensaje(f"Error cargando empleado: {e}", "error")
            self._limpiar_detalle_expediente()
            return

        if not empleado.id or empleado.empresa_id != self.id_empresa_actual:
            self._limpiar_detalle_expediente()
            return

        await self.ver_expediente(self._serializar_empleado_detalle(empleado))

    async def on_mount_expedientes(self):
        """Monta la pagina de expediente de empleado dentro del modulo RRHH."""
        resultado = await self.on_mount_portal()
        if resultado:
            self.loading = False
            yield resultado
            return

        if not self.mostrar_seccion_rrhh or not self.puede_acceder_rrhh:
            yield rx.redirect("/portal")
            return

        async for _ in self._montar_pagina(self._cargar_expediente_desde_ruta):
            yield

        if not self.empleado:
            yield rx.redirect("/portal/empleados", replace=True)

    async def ver_expediente(self, emp: dict):
        """Carga detalle del expediente de un empleado."""
        if not isinstance(emp, dict):
            return

        self.empleado = dict(emp)
        empleado_id = int(self.empleado.get("id") or 0)
        if empleado_id <= 0:
            self._limpiar_detalle_expediente()
            return

        self.empleado_id = str(empleado_id)

        try:
            docs = await empleado_documento_service.obtener_documentos_empleado(
                empleado_id=empleado_id,
                solo_vigentes=True,
            )
            self.documentos_empleado = [d.model_dump(mode="json") for d in docs]

            expediente = await onboarding_service.obtener_expediente(empleado_id)
            self.expediente_status = expediente.model_dump(mode="json")

            self._recalcular_documentos()

        except Exception as e:
            self.mostrar_mensaje(f"Error cargando expediente: {e}", "error")
            self.documentos_empleado = []
            self.expediente_status = {}
            self._recalcular_documentos()

    @rx.event
    def volver_a_empleados(self):
        """Regresa al listado principal de empleados."""
        return rx.redirect("/portal/empleados", replace=True)

    @rx.event
    def abrir_panel_expediente(self, emp: dict):
        """Compatibilidad: redirige a la nueva ruta dedicada del expediente."""
        if not isinstance(emp, dict):
            return rx.toast.error("Empleado invalido")

        empleado_id = int(emp.get("id") or 0)
        if empleado_id <= 0:
            return rx.toast.error("No se pudo identificar al empleado")

        return rx.redirect(f"/portal/empleados/{empleado_id}/expediente")

    @rx.event
    def abrir_modal_subir(self):
        """Abre modal de subida sin tipo preseleccionado."""
        self.mostrar_modal_subir = True
        self.tipo_documento_subiendo = ""
        return rx.clear_selected_files(UPLOAD_ID_EXPEDIENTE)

    @rx.event
    def abrir_subir(self, tipo_documento: str):
        """Abre modal de subida preseleccionando el tipo solicitado."""
        self.tipo_documento_subiendo = str(tipo_documento or "")
        self.mostrar_modal_subir = True
        return rx.clear_selected_files(UPLOAD_ID_EXPEDIENTE)

    @rx.event
    def cerrar_modal_subir(self):
        """Cierra modal de subida y limpia selección temporal."""
        self.mostrar_modal_subir = False
        self.tipo_documento_subiendo = ""
        self.subiendo_archivo = False
        return rx.clear_selected_files(UPLOAD_ID_EXPEDIENTE)

    async def ver_documento(self, doc: dict):
        """Obtiene URL temporal del archivo y abre modal de vista previa."""
        archivo_id = doc.get("archivo_id")
        if not archivo_id:
            return rx.toast.error("Este documento no tiene archivo asociado")

        try:
            archivo = await archivo_service.obtener_archivo(int(archivo_id))
            url = await archivo_service.obtener_url_temporal(int(archivo_id))
            if not url:
                return rx.toast.error("No se pudo obtener el archivo")

            self.preview_url = url
            self.preview_tipo_mime = archivo.tipo_mime if archivo else ""
            self.preview_nombre_archivo = (
                doc.get("nombre_archivo")
                or (archivo.nombre_original if archivo else "")
                or "Documento"
            )
            self.mostrar_modal_preview = True
        except Exception as e:
            return self.manejar_error_con_toast(e, "abriendo documento")

    async def descargar_documento(self, doc: dict):
        """Obtiene URL temporal y dispara descarga/abertura en navegador."""
        archivo_id = doc.get("archivo_id")
        if not archivo_id:
            return rx.toast.error("Este documento no tiene archivo asociado")

        try:
            url = await archivo_service.obtener_url_temporal(int(archivo_id))
            if not url:
                return rx.toast.error("No se pudo obtener el archivo")
            return rx.redirect(url)
        except Exception as e:
            return self.manejar_error_con_toast(e, "descargando documento")

    def cerrar_modal_preview(self):
        """Cierra el modal de vista previa."""
        self.mostrar_modal_preview = False
        self.preview_url = ""
        self.preview_tipo_mime = ""
        self.preview_nombre_archivo = ""

    async def handle_upload_documento(self, files: list[rx.UploadFile]):
        """
        Sube un documento al expediente del empleado seleccionado.

        Auto-aprueba porque quien sube es RRHH y registra trazabilidad
        en revisado_por y fecha_revision.
        """
        if not files:
            return

        if not self.tipo_documento_subiendo:
            return rx.toast.error("Seleccione el tipo de documento")

        empleado_id = int(self.empleado.get("id") or 0)
        if empleado_id <= 0:
            return rx.toast.error("No se pudo obtener el ID del empleado")

        self.subiendo_archivo = True
        try:
            from app.entities.empleado_documento import EmpleadoDocumentoCreate

            for file in files:
                upload_data = await file.read()
                nombre = file.filename or "documento"
                tipo_mime = file.content_type or "application/octet-stream"

                datos = EmpleadoDocumentoCreate(
                    empleado_id=empleado_id,
                    tipo_documento=self.tipo_documento_subiendo,
                    subido_por=self.obtener_uuid_usuario_actual(),
                )

                await empleado_documento_service.subir_documento(
                    datos=datos,
                    contenido=upload_data,
                    nombre_archivo=nombre,
                    tipo_mime=tipo_mime,
                    auto_aprobar=True,
                )

            await self.ver_expediente(self.empleado)
            self.tipo_documento_subiendo = ""
            self.mostrar_modal_subir = False

            return rx.toast.success("Documento subido y aprobado")

        except (BusinessRuleError, ValidationError) as e:
            return rx.toast.error(str(e))
        except Exception as e:
            return self.manejar_error_con_toast(e, "subiendo documento")
        finally:
            self.subiendo_archivo = False

    async def aprobar_documento(self, doc: dict):
        """Aprueba un documento pendiente."""
        self.saving = True
        try:
            revisado_por = self.obtener_uuid_usuario_actual()
            if not revisado_por:
                return rx.toast.error("No se pudo identificar al usuario revisor")

            await empleado_documento_service.aprobar_documento(
                documento_id=doc["id"],
                revisado_por=revisado_por,
            )

            await self.ver_expediente(self.empleado)
            return rx.toast.success("Documento aprobado")

        except BusinessRuleError as e:
            return rx.toast.error(str(e))
        except Exception as e:
            return self.manejar_error_con_toast(e, "aprobando documento")
        finally:
            self.saving = False

    def abrir_modal_rechazo(self, doc: dict):
        """Abre el modal de rechazo para un documento pendiente."""
        self.documento_rechazando_id = int(doc.get("id") or 0)
        self.form_observacion_rechazo = ""
        self.error_observacion = ""
        self.mostrar_modal_rechazo = True

    def cerrar_modal_rechazo(self):
        """Cierra el modal de rechazo."""
        self.mostrar_modal_rechazo = False
        self.documento_rechazando_id = 0
        self.form_observacion_rechazo = ""
        self.error_observacion = ""

    async def confirmar_rechazo(self):
        """Confirma rechazo del documento y recarga el expediente."""
        if not self.form_observacion_rechazo or len(self.form_observacion_rechazo.strip()) < 5:
            self.error_observacion = "La observacion debe tener al menos 5 caracteres"
            return rx.toast.error("Ingrese una observacion valida")

        if self.documento_rechazando_id <= 0:
            return rx.toast.error("No se identifico el documento a rechazar")

        self.saving = True
        try:
            revisado_por = self.obtener_uuid_usuario_actual()
            if not revisado_por:
                return rx.toast.error("No se pudo identificar al usuario revisor")

            await empleado_documento_service.rechazar_documento(
                documento_id=self.documento_rechazando_id,
                revisado_por=revisado_por,
                observacion=self.form_observacion_rechazo.strip(),
            )

            self.cerrar_modal_rechazo()
            await self.ver_expediente(self.empleado)
            return rx.toast.success("Documento rechazado")

        except (BusinessRuleError, ValidationError) as e:
            return rx.toast.error(str(e))
        except Exception as e:
            return self.manejar_error_con_toast(e, "rechazando documento")
        finally:
            self.saving = False
