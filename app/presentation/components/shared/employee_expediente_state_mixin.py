"""Lógica compartida para expediente documental de empleados en el portal."""

from __future__ import annotations

import reflex as rx

from app.domain.enums import TipoDocumentoEmpleado
from app.core.exceptions import BusinessRuleError, ValidationError
from app.core.text_utils import capitalizar_palabras
from app.modules.application import archivo_service
from app.modules.application import empleado_documento_service


EMPLOYEE_EXPEDIENTE_UPLOAD_ID = "upload_doc_expediente_portal_rrhh"


class EmployeeExpedienteStateMixin:
    """Mix-in para gestionar expediente documental desde states del portal."""

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

    def _reset_expediente_documental_state(self) -> None:
        """Limpia listas, métricas y modales del expediente."""
        self.documentos_obligatorios = []
        self.documentos_opcionales = []
        self.total_requeridos = 0
        self.total_aprobados = 0
        self.total_pendientes = 0
        self.total_rechazados = 0
        self.progreso_porcentaje = 0

        self.mostrar_modal_subir = False
        self.tipo_documento_subiendo = ""
        self.subiendo_archivo = False

        self.mostrar_modal_preview = False
        self.preview_url = ""
        self.preview_tipo_mime = ""
        self.preview_nombre_archivo = ""

        self.mostrar_modal_rechazo = False
        self.documento_rechazando_id = 0
        self.form_observacion_rechazo = ""
        self.error_observacion = ""

    def _obtener_empleado_id_expediente(self) -> int:
        """Obtiene el empleado actual desde el state que consume el mixin."""
        empleado = getattr(self, "empleado", {}) or {}
        return int(empleado.get("id") or 0)

    def _construir_checklist_documentos(self, docs_dict: list[dict]) -> None:
        """Construye el checklist visual y recalcula métricas."""
        docs_por_tipo = {
            str(doc.get("tipo_documento") or ""): doc
            for doc in docs_dict
        }

        checklist: list[dict] = []
        for tipo in TipoDocumentoEmpleado:
            doc = docs_por_tipo.get(tipo.value, {}) or {}
            estatus = str(doc.get("estatus", "") or "")
            checklist.append(
                {
                    **doc,
                    "tipo_documento": tipo.value,
                    "tipo_documento_label": tipo.descripcion,
                    "obligatorio": bool(tipo.es_obligatorio),
                    "subido": bool(doc.get("id") or doc.get("archivo_id")),
                    "estatus": estatus,
                    "estatus_label": (
                        "Pendiente de revisión"
                        if estatus == "PENDIENTE_REVISION"
                        else capitalizar_palabras(estatus.replace("_", " ").lower())
                        if estatus
                        else "Sin subir"
                    ),
                    "version_texto": (
                        f"v{int(doc.get('version', 1) or 1)}"
                        if (doc.get("id") or doc.get("archivo_id"))
                        else "—"
                    ),
                }
            )

        self.documentos_obligatorios = [d for d in checklist if d.get("obligatorio")]
        self.documentos_opcionales = [d for d in checklist if not d.get("obligatorio")]

        self.total_requeridos = len(self.documentos_obligatorios)
        self.total_aprobados = sum(
            1
            for doc in self.documentos_obligatorios
            if doc.get("estatus") == "APROBADO"
        )
        self.total_rechazados = sum(
            1
            for doc in self.documentos_obligatorios
            if doc.get("estatus") == "RECHAZADO"
        )
        self.total_pendientes = max(
            0,
            self.total_requeridos - self.total_aprobados - self.total_rechazados,
        )
        self.progreso_porcentaje = (
            int((self.total_aprobados / self.total_requeridos) * 100)
            if self.total_requeridos > 0
            else 0
        )

    async def _cargar_documentos_expediente(self, empleado_id: int) -> None:
        """Carga documentos vigentes y reconstruye el checklist UI."""
        docs = await empleado_documento_service.obtener_documentos_empleado(
            empleado_id=empleado_id,
            solo_vigentes=True,
        )
        docs_dict = [doc.model_dump(mode="json") for doc in docs]
        self._construir_checklist_documentos(docs_dict)

    def set_form_observacion_rechazo(self, value: str) -> None:
        self.form_observacion_rechazo = value or ""

    def set_tipo_documento_subiendo(self, value: str) -> None:
        self.tipo_documento_subiendo = str(value or "")

    def set_mostrar_modal_subir(self, value: bool):
        self.mostrar_modal_subir = bool(value)
        if self.mostrar_modal_subir:
            return None

        self.tipo_documento_subiendo = ""
        self.subiendo_archivo = False
        return rx.clear_selected_files(EMPLOYEE_EXPEDIENTE_UPLOAD_ID)

    @rx.var
    def tipos_documento_disponibles(self) -> list[dict]:
        """Opciones visibles para el selector de documentos."""
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

    def abrir_modal_subir(self):
        """Abre modal de subida sin tipo preseleccionado."""
        self.mostrar_modal_subir = True
        self.tipo_documento_subiendo = ""
        return rx.clear_selected_files(EMPLOYEE_EXPEDIENTE_UPLOAD_ID)

    def abrir_subir(self, tipo_documento: str):
        """Abre modal de subida con un tipo preseleccionado."""
        self.tipo_documento_subiendo = str(tipo_documento or "")
        self.mostrar_modal_subir = True
        return rx.clear_selected_files(EMPLOYEE_EXPEDIENTE_UPLOAD_ID)

    def cerrar_modal_subir(self):
        """Cierra modal de subida y limpia archivos temporales."""
        self.mostrar_modal_subir = False
        self.tipo_documento_subiendo = ""
        self.subiendo_archivo = False
        return rx.clear_selected_files(EMPLOYEE_EXPEDIENTE_UPLOAD_ID)

    async def ver_documento(self, doc: dict):
        """Obtiene URL temporal y abre vista previa."""
        archivo_id = int(doc.get("archivo_id") or 0)
        if archivo_id <= 0:
            return rx.toast.error("Este documento no tiene archivo asociado")

        try:
            archivo = await archivo_service.obtener_archivo(archivo_id)
            url = await archivo_service.obtener_url_temporal(archivo_id)
            if not url:
                return rx.toast.error("No se pudo obtener el archivo")

            self.preview_url = url
            self.preview_tipo_mime = archivo.tipo_mime if archivo else ""
            self.preview_nombre_archivo = (
                str(doc.get("nombre_archivo") or "")
                or (archivo.nombre_original if archivo else "")
                or "Documento"
            )
            self.mostrar_modal_preview = True
        except Exception as exc:
            return self.manejar_error_con_toast(exc, "abriendo documento")

    async def descargar_documento(self, doc: dict):
        """Obtiene URL temporal y dispara descarga del archivo."""
        archivo_id = int(doc.get("archivo_id") or 0)
        if archivo_id <= 0:
            return rx.toast.error("Este documento no tiene archivo asociado")

        try:
            url = await archivo_service.obtener_url_temporal(archivo_id)
            if not url:
                return rx.toast.error("No se pudo obtener el archivo")
            return rx.redirect(url)
        except Exception as exc:
            return self.manejar_error_con_toast(exc, "descargando documento")

    def cerrar_modal_preview(self) -> None:
        """Cierra el modal de vista previa."""
        self.mostrar_modal_preview = False
        self.preview_url = ""
        self.preview_tipo_mime = ""
        self.preview_nombre_archivo = ""

    async def handle_upload_documento(self, files: list[rx.UploadFile]):
        """Sube documento al expediente y lo autoaprueba por tratarse de RRHH."""
        if not files:
            return None

        if not self.tipo_documento_subiendo:
            return rx.toast.error("Seleccione el tipo de documento")

        empleado_id = self._obtener_empleado_id_expediente()
        if empleado_id <= 0:
            return rx.toast.error("No se pudo identificar al empleado")

        self.subiendo_archivo = True
        try:
            from app.domain.models.empleado_documento import EmpleadoDocumentoCreate

            for file in files:
                contenido = await file.read()
                datos = EmpleadoDocumentoCreate(
                    empleado_id=empleado_id,
                    tipo_documento=self.tipo_documento_subiendo,
                    subido_por=self.obtener_uuid_usuario_actual(),
                )
                await empleado_documento_service.subir_documento(
                    datos=datos,
                    contenido=contenido,
                    nombre_archivo=file.filename or "documento",
                    tipo_mime=file.content_type or "application/octet-stream",
                    auto_aprobar=True,
                )

            await self._cargar_documentos_expediente(empleado_id)
            self.tipo_documento_subiendo = ""
            self.mostrar_modal_subir = False
            return [
                rx.clear_selected_files(EMPLOYEE_EXPEDIENTE_UPLOAD_ID),
                rx.toast.success("Documento subido y aprobado"),
            ]
        except (BusinessRuleError, ValidationError) as exc:
            return rx.toast.error(str(exc))
        except Exception as exc:
            return self.manejar_error_con_toast(exc, "subiendo documento")
        finally:
            self.subiendo_archivo = False

    async def aprobar_documento(self, doc: dict):
        """Aprueba un documento pendiente y recarga el checklist."""
        documento_id = int(doc.get("id") or 0)
        if documento_id <= 0:
            return rx.toast.error("No se pudo identificar el documento")

        self.saving = True
        try:
            revisado_por = self.obtener_uuid_usuario_actual()
            if not revisado_por:
                return rx.toast.error("No se pudo identificar al usuario revisor")

            await empleado_documento_service.aprobar_documento(
                documento_id=documento_id,
                revisado_por=revisado_por,
            )
            await self._cargar_documentos_expediente(self._obtener_empleado_id_expediente())
            return rx.toast.success("Documento aprobado")
        except BusinessRuleError as exc:
            return rx.toast.error(str(exc))
        except Exception as exc:
            return self.manejar_error_con_toast(exc, "aprobando documento")
        finally:
            self.saving = False

    def abrir_modal_rechazo(self, doc: dict) -> None:
        """Abre modal de rechazo para un documento pendiente."""
        self.documento_rechazando_id = int(doc.get("id") or 0)
        self.form_observacion_rechazo = ""
        self.error_observacion = ""
        self.mostrar_modal_rechazo = True

    def cerrar_modal_rechazo(self) -> None:
        """Cierra modal de rechazo y limpia formulario."""
        self.mostrar_modal_rechazo = False
        self.documento_rechazando_id = 0
        self.form_observacion_rechazo = ""
        self.error_observacion = ""

    async def confirmar_rechazo(self):
        """Rechaza documento con observación y recarga el checklist."""
        if len(self.form_observacion_rechazo.strip()) < 5:
            self.error_observacion = "La observación debe tener al menos 5 caracteres"
            return rx.toast.error("Ingrese una observación válida")

        if self.documento_rechazando_id <= 0:
            return rx.toast.error("No se identificó el documento a rechazar")

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
            await self._cargar_documentos_expediente(self._obtener_empleado_id_expediente())
            return rx.toast.success("Documento rechazado")
        except (BusinessRuleError, ValidationError) as exc:
            return rx.toast.error(str(exc))
        except Exception as exc:
            return self.manejar_error_con_toast(exc, "rechazando documento")
        finally:
            self.saving = False
