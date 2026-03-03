"""
State para la pagina Expedientes del portal.

Vista lista de empleados en onboarding + vista detalle de expediente.
"""
import reflex as rx
from typing import List, Optional

from app.presentation.constants import FILTRO_TODOS
from app.presentation.portal.state.portal_state import PortalState
from app.services.archivo_service import archivo_service
from app.services.onboarding_service import onboarding_service
from app.services.empleado_documento_service import empleado_documento_service
from app.core.exceptions import (
    DatabaseError,
    NotFoundError,
    BusinessRuleError,
    ValidationError,
)
from app.core.ui_options import OPCIONES_ESTATUS_ONBOARDING_EXPEDIENTES


class ExpedientesState(PortalState):
    """State para la pagina de expedientes del portal."""

    # ========================
    # LISTA DE EMPLEADOS
    # ========================
    empleados_expedientes: List[dict] = []
    total_expedientes: int = 0
    filtro_estatus_expediente: str = FILTRO_TODOS

    # ========================
    # DETALLE EXPEDIENTE
    # ========================
    mostrando_detalle: bool = False
    empleado_seleccionado: dict = {}
    documentos_empleado: List[dict] = []
    expediente_status: dict = {}
    tipo_documento_subiendo: str = ""
    subiendo_archivo: bool = False
    mostrar_modal_preview: bool = False
    preview_url: str = ""
    preview_tipo_mime: str = ""
    preview_nombre_archivo: str = ""

    # ========================
    # MODAL RECHAZO
    # ========================
    mostrar_modal_rechazo: bool = False
    documento_rechazando_id: int = 0
    form_observacion_rechazo: str = ""
    error_observacion: str = ""

    # ========================
    # SETTERS
    # ========================
    def set_filtro_estatus_expediente(self, value: str):
        self.filtro_estatus_expediente = value

    def set_form_observacion_rechazo(self, value: str):
        self.form_observacion_rechazo = value

    def set_tipo_documento_subiendo(self, value: str):
        self.tipo_documento_subiendo = value

    # ========================
    # COMPUTED VARS
    # ========================
    @rx.var
    def empleados_expedientes_filtrados(self) -> List[dict]:
        """Filtra empleados por estatus de onboarding."""
        if not self.filtro_estatus_expediente or self.filtro_estatus_expediente == FILTRO_TODOS:
            return self.empleados_expedientes
        return [
            e for e in self.empleados_expedientes
            if e.get("estatus_onboarding") == self.filtro_estatus_expediente
        ]

    @rx.var
    def total_expedientes_filtrados(self) -> int:
        """Total visible en la tabla tras aplicar el filtro de estatus."""
        return len(self.empleados_expedientes_filtrados)

    @rx.var
    def opciones_estatus_expediente(self) -> List[dict]:
        """Opciones para filtro de estatus."""
        return OPCIONES_ESTATUS_ONBOARDING_EXPEDIENTES

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

    # ========================
    # MONTAJE
    # ========================
    async def on_mount_expedientes(self):
        resultado = await self.on_mount_portal()
        if resultado:
            self.loading = False
            yield resultado
            return
        if not self.mostrar_seccion_rrhh or not self.es_rrhh:
            yield rx.redirect("/portal")
            return
        async for _ in self._montar_pagina(self._fetch_empleados_expedientes):
            yield

    # ========================
    # CARGA DE DATOS
    # ========================
    async def _fetch_empleados_expedientes(self):
        """Carga empleados para gestion de expedientes."""
        if not self.id_empresa_actual:
            return

        try:
            empleados = await onboarding_service.obtener_empleados_para_expedientes(
                empresa_id=self.id_empresa_actual,
                estatus_filtro=(
                    self.filtro_estatus_expediente
                    if self.filtro_estatus_expediente != FILTRO_TODOS
                    else None
                ),
            )
            self.empleados_expedientes = empleados
            self.total_expedientes = len(empleados)
        except DatabaseError as e:
            self.mostrar_mensaje(f"Error cargando expedientes: {e}", "error")
            self.empleados_expedientes = []
            self.total_expedientes = 0
        except Exception as e:
            self.mostrar_mensaje(f"Error inesperado: {e}", "error")
            self.empleados_expedientes = []
            self.total_expedientes = 0

    async def recargar_expedientes(self):
        """Recarga con skeleton."""
        async for _ in self._recargar_datos(self._fetch_empleados_expedientes):
            yield

    # ========================
    # DETALLE EXPEDIENTE
    # ========================
    async def ver_expediente(self, emp: dict):
        """Abre el detalle del expediente de un empleado."""
        self.empleado_seleccionado = emp
        self.mostrando_detalle = True

        try:
            # Cargar documentos
            docs = await empleado_documento_service.obtener_documentos_empleado(
                empleado_id=emp["id"],
                solo_vigentes=True,
            )
            self.documentos_empleado = [
                d.model_dump(mode='json') for d in docs
            ]

            # Cargar status del expediente
            expediente = await onboarding_service.obtener_expediente(emp["id"])
            self.expediente_status = expediente.model_dump(mode='json')

        except Exception as e:
            self.mostrar_mensaje(f"Error cargando expediente: {e}", "error")
            self.documentos_empleado = []
            self.expediente_status = {}

    def volver_a_lista(self):
        """Vuelve a la lista de empleados."""
        self.mostrando_detalle = False
        self.empleado_seleccionado = {}
        self.documentos_empleado = []
        self.expediente_status = {}
        self.tipo_documento_subiendo = ""
        self.subiendo_archivo = False
        self.cerrar_modal_preview()

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

    # ========================
    # SUBIR DOCUMENTO
    # ========================
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

    # ========================
    # APROBAR DOCUMENTO
    # ========================
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

            # Recargar expediente
            await self.ver_expediente(self.empleado_seleccionado)
            return rx.toast.success("Documento aprobado")

        except BusinessRuleError as e:
            return rx.toast.error(str(e))
        except Exception as e:
            return self.manejar_error_con_toast(e, "aprobando documento")
        finally:
            self.saving = False

    # ========================
    # RECHAZAR DOCUMENTO
    # ========================
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
            # Recargar expediente
            await self.ver_expediente(self.empleado_seleccionado)
            return rx.toast.success("Documento rechazado")

        except (BusinessRuleError, ValidationError) as e:
            return rx.toast.error(str(e))
        except Exception as e:
            return self.manejar_error_con_toast(e, "rechazando documento")
        finally:
            self.saving = False
