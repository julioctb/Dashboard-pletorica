"""State público para links compartibles del expediente anual de empresa."""

from datetime import datetime
from typing import List

import reflex as rx

from app.presentation.components.shared.base_state import BaseState
from app.services import archivo_service, empresa_documento_service


class EmpresaDocumentacionShareState(BaseState):
    """Vista pública en solo lectura para un expediente anual compartido."""

    documentacion_empresa: dict = {}
    checklist_documentos: List[dict] = []
    anio_seleccionado: int = datetime.now().year
    documentos_requeridos: int = 0
    documentos_subidos_requeridos: int = 0
    porcentaje_completitud: int = 0

    async def on_mount_empresa_documentacion_share(self):
        async for _ in self._montar_pagina(self._fetch_share_documentacion):
            yield

    async def _fetch_share_documentacion(self):
        token = (self.share_token or "").strip()
        if not token:
            self.documentacion_empresa = {}
            self.checklist_documentos = []
            self.mostrar_mensaje("El enlace compartido es inválido", "error")
            return

        try:
            resultado = await empresa_documento_service.resolver_share_token(token)
            self.documentacion_empresa = resultado["empresa"]
            self.anio_seleccionado = int(resultado["anio"])
            self.checklist_documentos = resultado["documentos"]
            self.documentos_requeridos = int(resultado["documentos_requeridos"])
            self.documentos_subidos_requeridos = int(resultado["documentos_subidos_requeridos"])
            self.porcentaje_completitud = int(resultado["porcentaje_completitud"])
        except Exception as e:
            self.documentacion_empresa = {}
            self.checklist_documentos = []
            self.documentos_requeridos = 0
            self.documentos_subidos_requeridos = 0
            self.porcentaje_completitud = 0
            self.manejar_error(e, "cargando expediente compartido")

    async def ver_documento_empresa(self, documento: dict):
        archivo_id = documento.get("archivo_id")
        if not archivo_id:
            return rx.toast.error("Este documento no tiene PDF disponible")
        try:
            url = await archivo_service.obtener_url_temporal(int(archivo_id))
            return rx.redirect(url, is_external=True)
        except Exception as e:
            return self.manejar_error_con_toast(e, "abriendo documento")

    async def descargar_documento_empresa(self, documento: dict):
        return await self.ver_documento_empresa(documento)

    @rx.var
    def nombre_empresa_documentacion(self) -> str:
        return str(self.documentacion_empresa.get("nombre_comercial", "Expediente compartido"))

    @rx.var
    def rfc_empresa_documentacion(self) -> str:
        return str(self.documentacion_empresa.get("rfc", ""))

    @rx.var
    def codigo_empresa_documentacion(self) -> str:
        return str(self.documentacion_empresa.get("codigo_corto", ""))

    @rx.var
    def empresa_documentacion_identificador(self) -> str:
        codigo = str(self.documentacion_empresa.get("codigo_corto", "") or "")
        rfc = str(self.documentacion_empresa.get("rfc", "") or "")
        if codigo and rfc:
            return f"{codigo} · {rfc}"
        return codigo or rfc

    @rx.var
    def tiene_documentacion_cargada(self) -> bool:
        return bool(self.documentacion_empresa)
