"""
State para la pagina Expedientes del portal.

Vista lista de empleados en onboarding + vista detalle de expediente.
"""
import reflex as rx
from typing import List, Optional

from app.presentation.portal.state.portal_state import PortalState
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
    filtro_estatus_expediente: str = ""

    # ========================
    # DETALLE EXPEDIENTE
    # ========================
    mostrando_detalle: bool = False
    empleado_seleccionado: dict = {}
    documentos_empleado: List[dict] = []
    expediente_status: dict = {}

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

    # ========================
    # COMPUTED VARS
    # ========================
    @rx.var
    def empleados_expedientes_filtrados(self) -> List[dict]:
        """Filtra empleados por estatus de onboarding."""
        if not self.filtro_estatus_expediente or self.filtro_estatus_expediente == "TODOS":
            return self.empleados_expedientes
        return [
            e for e in self.empleados_expedientes
            if e.get("estatus_onboarding") == self.filtro_estatus_expediente
        ]

    @rx.var
    def opciones_estatus_expediente(self) -> List[dict]:
        """Opciones para filtro de estatus."""
        return OPCIONES_ESTATUS_ONBOARDING_EXPEDIENTES

    @rx.var
    def nombre_empleado_seleccionado(self) -> str:
        """Nombre del empleado seleccionado."""
        return self.empleado_seleccionado.get("nombre_completo", "")

    @rx.var
    def clave_empleado_seleccionado(self) -> str:
        """Clave del empleado seleccionado."""
        return self.empleado_seleccionado.get("clave", "")

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
        if not self.es_rrhh:
            yield rx.redirect("/portal")
            return
        async for _ in self._montar_pagina(self._fetch_empleados_expedientes):
            yield

    # ========================
    # CARGA DE DATOS
    # ========================
    async def _fetch_empleados_expedientes(self):
        """Carga empleados con estatus de onboarding."""
        if not self.id_empresa_actual:
            return

        try:
            empleados = await onboarding_service.obtener_empleados_onboarding(
                empresa_id=self.id_empresa_actual,
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

    # ========================
    # APROBAR DOCUMENTO
    # ========================
    async def aprobar_documento(self, doc: dict):
        """Aprueba un documento."""
        self.saving = True
        try:
            from uuid import UUID
            revisado_por = UUID('00000000-0000-0000-0000-000000000000')
            if self.usuario_actual:
                uid = self.usuario_actual.get('id')
                if uid:
                    revisado_por = UUID(str(uid))

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
            from uuid import UUID
            revisado_por = UUID('00000000-0000-0000-0000-000000000000')
            if self.usuario_actual:
                uid = self.usuario_actual.get('id')
                if uid:
                    revisado_por = UUID(str(uid))

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
