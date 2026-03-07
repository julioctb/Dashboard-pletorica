"""
State para el detalle de expediente dentro de empleados del portal.
"""
from typing import List, Optional

import reflex as rx

from app.core.exceptions import (
    BusinessRuleError,
    NotFoundError,
    ValidationError,
)
from app.presentation.portal.state.portal_state import PortalState
from app.services import empleado_service
from app.services.archivo_service import archivo_service
from app.services.empleado_documento_service import empleado_documento_service
from app.services.onboarding_service import onboarding_service


class ExpedientesState(PortalState):
    """State para el detalle de expediente de un empleado."""

    empleado_seleccionado: dict = {}
    documentos_empleado: List[dict] = []
    expediente_status: dict = {}
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

    @rx.var
    def tipos_documento_disponibles(self) -> list[dict]:
        """Lista de tipos de documento para el selector."""
        from app.core.enums import TipoDocumentoEmpleado

        return [
            {"value": t.value, "label": t.descripcion}
            for t in TipoDocumentoEmpleado
        ]

    @rx.var
    def documentos_expediente_lista(self) -> List[dict]:
        """Lista completa de documentos para mostrar faltantes y cargados."""
        from app.core.enums import TipoDocumentoEmpleado

        docs_por_tipo = {
            doc.get("tipo_documento"): doc for doc in self.documentos_empleado
        }

        lista = []
        for tipo in TipoDocumentoEmpleado:
            doc_existente = docs_por_tipo.get(tipo.value, {})
            lista.append({
                **doc_existente,
                "tipo_documento": tipo.value,
                "tipo_documento_label": tipo.descripcion,
                "obligatorio": tipo.es_obligatorio,
                "subido": bool(doc_existente),
            })

        return lista

    @rx.var
    def nombre_empleado_seleccionado(self) -> str:
        """Nombre del empleado seleccionado."""
        return self.empleado_seleccionado.get("nombre_completo", "")

    @rx.var
    def clave_empleado_seleccionado(self) -> str:
        """Clave del empleado seleccionado."""
        return self.empleado_seleccionado.get("clave", "")

    @rx.var
    def preview_es_imagen(self) -> bool:
        return self.preview_tipo_mime.startswith("image/")

    @rx.var
    def preview_es_pdf(self) -> bool:
        return self.preview_tipo_mime == "application/pdf"

    @rx.var
    def porcentaje_expediente(self) -> int:
        """Porcentaje de completado del expediente."""
        return int(self.expediente_status.get("porcentaje_completado", 0))

    @rx.var
    def total_docs_requeridos(self) -> int:
        return self.expediente_status.get("documentos_requeridos", 0)

    @rx.var
    def total_docs_aprobados(self) -> int:
        return self.expediente_status.get("documentos_aprobados", 0)

    @rx.var
    def total_docs_pendientes(self) -> int:
        return self.expediente_status.get("pendientes", 0)

    @rx.var
    def total_docs_rechazados(self) -> int:
        return self.expediente_status.get("documentos_rechazados", 0)

    def _obtener_empleado_id_query(self) -> Optional[int]:
        """Obtiene el empleado_id de la URL si viene informado."""
        query_params = self.router_data.get("query", {}) or {}
        empleado_id = query_params.get("empleado_id")
        if not empleado_id:
            return None

        try:
            return int(empleado_id)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _serializar_empleado_detalle(empleado) -> dict:
        """Convierte la entidad a un resumen serializable para el state."""
        return {
            "id": empleado.id,
            "clave": empleado.clave,
            "nombre_completo": empleado.nombre_completo(),
            "empresa_id": empleado.empresa_id,
        }

    def _limpiar_detalle_expediente(self):
        """Limpia el detalle del expediente."""
        self.empleado_seleccionado = {}
        self.documentos_empleado = []
        self.expediente_status = {}
        self.tipo_documento_subiendo = ""
        self.subiendo_archivo = False
        self.cerrar_modal_preview()

    async def _cargar_expediente_desde_query(self):
        """Carga el expediente usando el empleado_id en query params."""
        empleado_id = self._obtener_empleado_id_query()
        if not empleado_id:
            self._limpiar_detalle_expediente()
            return

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
        """Monta el detalle de expediente bajo el modulo de empleados."""
        resultado = await self.on_mount_portal()
        if resultado:
            self.loading = False
            yield resultado
            return
        if not self.mostrar_seccion_rrhh or not self.es_rrhh:
            yield rx.redirect("/portal")
            return

        async for _ in self._montar_pagina(self._cargar_expediente_desde_query):
            yield

        if not self.empleado_seleccionado:
            yield rx.redirect("/portal/empleados", replace=True)

    async def ver_expediente(self, emp: dict):
        """Carga el detalle del expediente de un empleado."""
        self.empleado_seleccionado = emp

        try:
            docs = await empleado_documento_service.obtener_documentos_empleado(
                empleado_id=emp["id"],
                solo_vigentes=True,
            )
            self.documentos_empleado = [
                d.model_dump(mode="json") for d in docs
            ]

            expediente = await onboarding_service.obtener_expediente(emp["id"])
            self.expediente_status = expediente.model_dump(mode="json")

        except Exception as e:
            self.mostrar_mensaje(f"Error cargando expediente: {e}", "error")
            self.documentos_empleado = []
            self.expediente_status = {}

    @rx.event
    def volver_a_empleados(self):
        """Regresa al listado principal de empleados."""
        self._limpiar_detalle_expediente()
        return rx.redirect("/portal/empleados", replace=True)

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
        if not files or not self.tipo_documento_subiendo:
            return

        if not self.empleado_seleccionado:
            return rx.toast.error("No hay empleado seleccionado")

        empleado_id = self.empleado_seleccionado.get("id")
        if not empleado_id:
            return rx.toast.error("Error: No se pudo obtener el ID del empleado")

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

            await self.ver_expediente(self.empleado_seleccionado)
            self.tipo_documento_subiendo = ""

            return rx.toast.success("Documento subido y aprobado")

        except (BusinessRuleError, ValidationError) as e:
            return rx.toast.error(str(e))
        except Exception as e:
            return self.manejar_error_con_toast(e, "subiendo documento")
        finally:
            self.subiendo_archivo = False

    async def aprobar_documento(self, doc: dict):
        """Aprueba un documento."""
        self.saving = True
        try:
            revisado_por = self.obtener_uuid_usuario_actual()
            if not revisado_por:
                return rx.toast.error("No se pudo identificar al usuario revisor")

            await empleado_documento_service.aprobar_documento(
                documento_id=doc["id"],
                revisado_por=revisado_por,
            )

            await self.ver_expediente(self.empleado_seleccionado)
            return rx.toast.success("Documento aprobado")

        except BusinessRuleError as e:
            return rx.toast.error(str(e))
        except Exception as e:
            return self.manejar_error_con_toast(e, "aprobando documento")
        finally:
            self.saving = False

    def abrir_modal_rechazo(self, doc: dict):
        """Abre el modal de rechazo para un documento."""
        self.documento_rechazando_id = doc["id"]
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
        """Confirma el rechazo del documento."""
        if not self.form_observacion_rechazo or len(self.form_observacion_rechazo.strip()) < 5:
            self.error_observacion = "La observacion debe tener al menos 5 caracteres"
            return rx.toast.error("Ingrese una observacion valida")

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
            await self.ver_expediente(self.empleado_seleccionado)
            return rx.toast.success("Documento rechazado")

        except (BusinessRuleError, ValidationError) as e:
            return rx.toast.error(str(e))
        except Exception as e:
            return self.manejar_error_con_toast(e, "rechazando documento")
        finally:
            self.saving = False
