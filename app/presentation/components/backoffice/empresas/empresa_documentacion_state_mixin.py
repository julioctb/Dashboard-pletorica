"""Mixin compartido para páginas de documentación anual de empresas."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import List

import reflex as rx

from app.domain.models.empresa_documento import (
    EmpresaDocumentoCreate,
    EmpresaDocumentoRequisitoCreate,
)
from app.modules.application import archivo_service, empresa_documento_service, empresa_service


EMPRESA_DOCUMENTACION_UPLOAD_ID = "empresa_documentacion_upload"


class EmpresaDocumentacionStateMixin:
    """Contrato compartido entre backoffice y portal."""

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

    def set_form_link_expira_local(self, value: str):
        self.form_link_expira_local = value or ""

    def set_form_documento_personalizado_nombre(self, value: str):
        self.form_documento_personalizado_nombre = value or ""

    def set_form_documento_personalizado_ayuda(self, value: str):
        self.form_documento_personalizado_ayuda = value or ""

    def set_form_documento_personalizado_es_obligatorio(self, value: bool):
        self.form_documento_personalizado_es_obligatorio = bool(value)

    def set_form_documento_personalizado_es_anual(self, value: bool):
        self.form_documento_personalizado_es_anual = bool(value)

    @staticmethod
    def _tz_local():
        return datetime.now().astimezone().tzinfo or timezone.utc

    @classmethod
    def _default_expira_local(cls) -> str:
        ahora_local = datetime.now(cls._tz_local()) + timedelta(days=7)
        return ahora_local.replace(second=0, microsecond=0).strftime("%Y-%m-%dT%H:%M")

    def _asegurar_form_link_default(self):
        if not self.form_link_expira_local:
            self.form_link_expira_local = self._default_expira_local()

    def _empresa_documentacion_company_id(self) -> int:
        raise NotImplementedError

    @staticmethod
    def _build_upload_guidance(documento: dict) -> str:
        """Compone ayuda contextual para distinguir carga anual vs documento vigente."""
        ayuda_base = str(documento.get("ayuda", "") or "").strip()
        es_anual = bool(documento.get("es_anual", True))

        contexto = (
            "Este documento corresponde al año seleccionado. Si estás cargando un nuevo "
            "ejercicio, sube aquí la versión de ese año."
            if es_anual
            else "Este documento se reutiliza entre años hasta que cambie. Reemplázalo "
            "solo si hubo actualización del representante, del acta o del documento vigente."
        )

        return " ".join(parte for parte in [ayuda_base, contexto] if parte).strip()

    async def _fetch_documentacion_empresa(self):
        empresa_id = self._empresa_documentacion_company_id()
        if not empresa_id:
            self.documentacion_empresa = {}
            self.checklist_documentos = []
            self.share_link_activo = {}
            self.documentos_requeridos = 0
            self.documentos_subidos_requeridos = 0
            self.porcentaje_completitud = 0
            return

        self._asegurar_form_link_default()

        empresa = await empresa_service.obtener_por_id(empresa_id)
        expediente = await empresa_documento_service.obtener_expediente_empresa(
            empresa_id,
            self.anio_seleccionado,
        )
        share = await empresa_documento_service.obtener_share_link_activo(
            empresa_id,
            self.anio_seleccionado,
        )

        self.documentacion_empresa = empresa.model_dump(mode="json")
        self.checklist_documentos = expediente["documentos"]
        self.documentos_requeridos = expediente["documentos_requeridos"]
        self.documentos_subidos_requeridos = expediente["documentos_subidos_requeridos"]
        self.porcentaje_completitud = expediente["porcentaje_completitud"]
        self.share_link_activo = share.model_dump(mode="json") if share else {}

    async def cambiar_anio_documentacion(self, value: str):
        try:
            self.anio_seleccionado = int(value) if value else datetime.now().year
        except (TypeError, ValueError):
            self.anio_seleccionado = datetime.now().year

        self.share_link_generado = ""
        async for _ in self._recargar_datos(self._fetch_documentacion_empresa):
            yield

    def abrir_modal_subir(self, documento: dict):
        self.tipo_documento_subiendo = str(documento.get("tipo_documento", ""))
        self.requisito_id_subiendo = int(documento.get("requisito_id") or 0)
        self.nombre_documento_subiendo = str(documento.get("tipo_documento_label", "Documento"))
        self.ayuda_documento_subiendo = self._build_upload_guidance(documento)
        self.mostrar_modal_subir = True

    def cerrar_modal_subir(self):
        self.mostrar_modal_subir = False
        self.tipo_documento_subiendo = ""
        self.requisito_id_subiendo = 0
        self.nombre_documento_subiendo = ""
        self.ayuda_documento_subiendo = ""

    def abrir_modal_documento_personalizado(self):
        self.form_documento_personalizado_nombre = ""
        self.form_documento_personalizado_ayuda = ""
        self.form_documento_personalizado_es_obligatorio = False
        self.form_documento_personalizado_es_anual = True
        self.mostrar_modal_documento_personalizado = True

    def cerrar_modal_documento_personalizado(self):
        self.mostrar_modal_documento_personalizado = False
        self.form_documento_personalizado_nombre = ""
        self.form_documento_personalizado_ayuda = ""
        self.form_documento_personalizado_es_obligatorio = False
        self.form_documento_personalizado_es_anual = True

    async def handle_upload_documento_empresa(self, files: list[rx.UploadFile]):
        if not files or not self.tipo_documento_subiendo:
            return rx.toast.error("Selecciona un PDF para subir")

        empresa_id = self._empresa_documentacion_company_id()
        if not empresa_id:
            return rx.toast.error("No se encontró la empresa del expediente")

        self.subiendo_archivo = True
        try:
            file = files[0]
            contenido = await file.read()
            nombre = file.filename or "documento.pdf"
            tipo_mime = file.content_type or "application/pdf"

            datos = EmpresaDocumentoCreate(
                empresa_id=empresa_id,
                anio=self.anio_seleccionado,
                tipo_documento=self.tipo_documento_subiendo,
                requisito_id=self.requisito_id_subiendo or None,
                subido_por=self.obtener_uuid_usuario_actual(),
            )
            await empresa_documento_service.subir_documento(
                datos=datos,
                contenido=contenido,
                nombre_archivo=nombre,
                tipo_mime=tipo_mime,
            )

            self.cerrar_modal_subir()
            await self._fetch_documentacion_empresa()
            return rx.toast.success("Documento actualizado")
        except Exception as e:
            return self.manejar_error_con_toast(e, "subiendo documento")
        finally:
            self.subiendo_archivo = False

    async def crear_documento_personalizado(self):
        empresa_id = self._empresa_documentacion_company_id()
        if not empresa_id:
            return rx.toast.error("No se encontró la empresa del expediente")

        nombre = (self.form_documento_personalizado_nombre or "").strip()
        if len(nombre) < 3:
            return rx.toast.error("Escribe un nombre válido para el documento")

        self.guardando_documento_personalizado = True
        try:
            datos = EmpresaDocumentoRequisitoCreate(
                empresa_id=empresa_id,
                nombre=nombre,
                ayuda=(self.form_documento_personalizado_ayuda or "").strip() or None,
                es_obligatorio=self.form_documento_personalizado_es_obligatorio,
                es_anual=self.form_documento_personalizado_es_anual,
            )
            await empresa_documento_service.crear_requisito_personalizado(datos)
            self.cerrar_modal_documento_personalizado()
            await self._fetch_documentacion_empresa()
            return rx.toast.success("Documento adicional creado")
        except Exception as e:
            return self.manejar_error_con_toast(e, "creando documento adicional")
        finally:
            self.guardando_documento_personalizado = False

    async def ver_documento_empresa(self, documento: dict):
        archivo_id = documento.get("archivo_id")
        if not archivo_id:
            return rx.toast.error("Este documento aún no tiene archivo")

        try:
            url = await archivo_service.obtener_url_temporal(int(archivo_id))
            return rx.redirect(url, is_external=True)
        except Exception as e:
            return self.manejar_error_con_toast(e, "abriendo documento")

    async def descargar_documento_empresa(self, documento: dict):
        return await self.ver_documento_empresa(documento)

    async def generar_link_compartible_empresa(self):
        empresa_id = self._empresa_documentacion_company_id()
        if not empresa_id:
            return rx.toast.error("No se encontró la empresa del expediente")

        if not self.form_link_expira_local:
            return rx.toast.error("Selecciona la fecha y hora de expiración")

        try:
            fecha_local = datetime.fromisoformat(self.form_link_expira_local)
            fecha_utc = fecha_local.replace(
                tzinfo=self._tz_local(),
            ).astimezone(timezone.utc)

            resultado = await empresa_documento_service.generar_share_link(
                empresa_id,
                self.anio_seleccionado,
                fecha_utc,
                created_by=self.obtener_uuid_usuario_actual(),
            )

            self.share_link_activo = resultado["share_link"].model_dump(mode="json")
            self.share_link_generado = resultado["share_path"]
            return rx.toast.success("Link compartible generado")
        except Exception as e:
            return self.manejar_error_con_toast(e, "generando link compartible")

    async def revocar_link_compartible_empresa(self):
        empresa_id = self._empresa_documentacion_company_id()
        if not empresa_id:
            return rx.toast.error("No se encontró la empresa del expediente")

        try:
            await empresa_documento_service.revocar_share_link(
                empresa_id,
                self.anio_seleccionado,
                revoked_by=self.obtener_uuid_usuario_actual(),
            )
            self.share_link_activo = {}
            self.share_link_generado = ""
            return rx.toast.success("Link compartible revocado")
        except Exception as e:
            return self.manejar_error_con_toast(e, "revocando link compartible")

    @rx.var
    def opciones_anio_documentacion(self) -> list[dict]:
        actual = datetime.now().year
        return [
            {"label": str(anio), "value": str(anio)}
            for anio in range(actual + 1, actual - 5, -1)
        ]

    @rx.var
    def nombre_empresa_documentacion(self) -> str:
        return str(self.documentacion_empresa.get("nombre_comercial", "Empresa"))

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
    def hay_link_compartible_activo(self) -> bool:
        return bool(self.share_link_activo)

    @rx.var
    def link_compartible_expira_texto(self) -> str:
        if not self.share_link_activo:
            return ""
        return str(self.share_link_activo.get("expires_at", ""))

    @rx.var
    def tiene_link_generado_copiable(self) -> bool:
        return self.share_link_generado != ""
