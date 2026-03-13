"""State portal para la documentación anual de la empresa activa."""

from datetime import datetime
from typing import List

import reflex as rx

from app.presentation.components.empresas.empresa_documentacion_state_mixin import (
    EmpresaDocumentacionStateMixin,
)
from app.presentation.portal.state.portal_state import PortalState


class DocumentacionEmpresaPortalState(EmpresaDocumentacionStateMixin, PortalState):
    """Expediente anual en el portal de la empresa proveedora."""

    # Reflex necesita que estas vars vivan en el State concreto para exponerlas
    # como Vars reactivas al compilar la página.
    documentacion_empresa: dict = {}
    checklist_documentos: List[dict] = []
    anio_seleccionado: int = datetime.now().year
    documentos_requeridos: int = 0
    documentos_subidos_requeridos: int = 0
    porcentaje_completitud: int = 0

    share_link_activo: dict = {}
    share_link_generado: str = ""
    form_link_expira_local: str = ""

    mostrar_modal_subir: bool = False
    tipo_documento_subiendo: str = ""
    requisito_id_subiendo: int = 0
    nombre_documento_subiendo: str = ""
    ayuda_documento_subiendo: str = ""
    subiendo_archivo: bool = False

    mostrar_modal_documento_personalizado: bool = False
    form_documento_personalizado_nombre: str = ""
    form_documento_personalizado_ayuda: str = ""
    form_documento_personalizado_es_obligatorio: bool = False
    form_documento_personalizado_es_anual: bool = True
    guardando_documento_personalizado: bool = False

    def _empresa_documentacion_company_id(self) -> int:
        return self.id_empresa_actual

    def set_form_link_expira_local(self, value: str):
        return EmpresaDocumentacionStateMixin.set_form_link_expira_local(self, value)

    def set_form_documento_personalizado_nombre(self, value: str):
        return EmpresaDocumentacionStateMixin.set_form_documento_personalizado_nombre(self, value)

    def set_form_documento_personalizado_ayuda(self, value: str):
        return EmpresaDocumentacionStateMixin.set_form_documento_personalizado_ayuda(self, value)

    def set_form_documento_personalizado_es_obligatorio(self, value: bool):
        return EmpresaDocumentacionStateMixin.set_form_documento_personalizado_es_obligatorio(
            self, value
        )

    def set_form_documento_personalizado_es_anual(self, value: bool):
        return EmpresaDocumentacionStateMixin.set_form_documento_personalizado_es_anual(
            self, value
        )

    def abrir_modal_subir(self, documento: dict):
        return EmpresaDocumentacionStateMixin.abrir_modal_subir(self, documento)

    def cerrar_modal_subir(self):
        return EmpresaDocumentacionStateMixin.cerrar_modal_subir(self)

    def abrir_modal_documento_personalizado(self):
        return EmpresaDocumentacionStateMixin.abrir_modal_documento_personalizado(self)

    def cerrar_modal_documento_personalizado(self):
        return EmpresaDocumentacionStateMixin.cerrar_modal_documento_personalizado(self)

    async def cambiar_anio_documentacion(self, value: str):
        async for _ in EmpresaDocumentacionStateMixin.cambiar_anio_documentacion(self, value):
            yield

    async def handle_upload_documento_empresa(self, files: list[rx.UploadFile]):
        return await EmpresaDocumentacionStateMixin.handle_upload_documento_empresa(self, files)

    async def crear_documento_personalizado(self):
        return await EmpresaDocumentacionStateMixin.crear_documento_personalizado(self)

    async def ver_documento_empresa(self, documento: dict):
        return await EmpresaDocumentacionStateMixin.ver_documento_empresa(self, documento)

    async def descargar_documento_empresa(self, documento: dict):
        return await EmpresaDocumentacionStateMixin.descargar_documento_empresa(self, documento)

    async def generar_link_compartible_empresa(self):
        return await EmpresaDocumentacionStateMixin.generar_link_compartible_empresa(self)

    async def revocar_link_compartible_empresa(self):
        return await EmpresaDocumentacionStateMixin.revocar_link_compartible_empresa(self)

    async def on_mount_documentacion_empresa_portal(self):
        resultado = await self.on_mount_portal()
        if resultado:
            self.loading = False
            yield resultado
            return

        if not self.es_admin_empresa:
            yield rx.redirect("/portal/mi-empresa")
            return

        async for _ in self._montar_pagina(self._fetch_documentacion_empresa):
            yield
