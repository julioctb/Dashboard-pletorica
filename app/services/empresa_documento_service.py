"""Servicio para la documentación anual de empresas."""

from __future__ import annotations

import hashlib
import logging
import re
import secrets
import unicodedata
from datetime import datetime, timezone
from typing import Any, Optional

from app.core.enums import TipoDocumentoEmpresa
from app.core.exceptions import (
    BusinessRuleError,
    DatabaseError,
    NotFoundError,
    ValidationError,
)
from app.database import db_manager
from app.entities.archivo import EntidadArchivo, TipoArchivo
from app.entities.empresa_documento import (
    EmpresaDocumento,
    EmpresaDocumentoCreate,
    EmpresaDocumentoRequisito,
    EmpresaDocumentoRequisitoCreate,
    EmpresaDocumentoResumen,
    EmpresaDocumentoShareLink,
)
from app.services.archivo_service import archivo_service
from app.services.empresa_service import empresa_service

logger = logging.getLogger(__name__)


class EmpresaDocumentoService:
    """Gestiona checklist anual, versionado y links compartibles."""

    def __init__(self):
        self.supabase = db_manager.get_client()
        self.tabla_documentos = "empresa_documentos"
        self.tabla_share_links = "empresa_documento_share_links"
        self.tabla_requisitos = "empresa_documento_requisitos"

    @staticmethod
    def _ahora_utc() -> datetime:
        return datetime.now(timezone.utc)

    @staticmethod
    def _hash_token(token: str) -> str:
        return hashlib.sha256(token.encode("utf-8")).hexdigest()

    @staticmethod
    def _validar_anio(anio: int) -> None:
        if anio < 2000 or anio > 2100:
            raise ValidationError("El año seleccionado es inválido")

    @staticmethod
    def _coerce_tipo(tipo_documento: str | TipoDocumentoEmpresa) -> TipoDocumentoEmpresa:
        if isinstance(tipo_documento, TipoDocumentoEmpresa):
            return tipo_documento
        return TipoDocumentoEmpresa(tipo_documento)

    @staticmethod
    def _serializar_share_path(token: str) -> str:
        return f"/share/empresa-documentacion/{token}"

    @staticmethod
    def _documento_key(tipo_documento: str, requisito_id: int | None = None) -> tuple[str, int]:
        return tipo_documento, int(requisito_id or 0)

    @staticmethod
    def _slugify_requisito(texto: str) -> str:
        texto_ascii = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode("ascii")
        texto_ascii = re.sub(r"[^A-Za-z0-9]+", "_", texto_ascii.upper()).strip("_")
        return texto_ascii[:40] or "DOCUMENTO"

    @staticmethod
    def _apply_requisito_filter(query, requisito_id: int | None):
        if requisito_id:
            return query.eq("requisito_id", int(requisito_id))
        return query.is_("requisito_id", "null")

    async def crear_requisito_personalizado(
        self,
        datos: EmpresaDocumentoRequisitoCreate,
    ) -> EmpresaDocumentoRequisito:
        """Crea un requisito configurable por empresa para documentos extra."""
        nombre = (datos.nombre or "").strip()
        if len(nombre) < 3:
            raise ValidationError("El nombre del documento adicional es obligatorio")

        ayuda = (datos.ayuda or "").strip() or None

        try:
            ultimo = (
                self.supabase.table(self.tabla_requisitos)
                .select("orden")
                .eq("empresa_id", datos.empresa_id)
                .order("orden", desc=True)
                .limit(1)
                .execute()
            )
            siguiente_orden = 100
            if ultimo.data:
                siguiente_orden = int(ultimo.data[0]["orden"]) + 1

            codigo = (
                f"DOC_{datos.empresa_id}_{siguiente_orden}_{self._slugify_requisito(nombre)}"
            )[:80]

            payload = {
                "empresa_id": datos.empresa_id,
                "codigo": codigo,
                "nombre": nombre,
                "ayuda": ayuda,
                "es_obligatorio": bool(datos.es_obligatorio),
                "es_anual": bool(datos.es_anual),
                "orden": siguiente_orden,
                "activo": True,
            }
            result = self.supabase.table(self.tabla_requisitos).insert(payload).execute()
            if not result.data:
                raise DatabaseError("No se pudo crear el documento adicional")
            return EmpresaDocumentoRequisito(**result.data[0])
        except (ValidationError, DatabaseError):
            raise
        except Exception as e:
            logger.error("Error creando requisito personalizado de empresa: %s", e)
            raise DatabaseError(f"Error creando documento adicional: {e}")

    async def obtener_requisitos_personalizados(
        self,
        empresa_id: int,
        *,
        solo_activos: bool = True,
    ) -> list[EmpresaDocumentoRequisito]:
        """Obtiene los documentos adicionales configurados por empresa."""
        try:
            query = (
                self.supabase.table(self.tabla_requisitos)
                .select("*")
                .eq("empresa_id", empresa_id)
                .order("orden")
                .order("nombre")
            )
            if solo_activos:
                query = query.eq("activo", True)
            result = query.execute()
            return [EmpresaDocumentoRequisito(**row) for row in (result.data or [])]
        except Exception as e:
            logger.error("Error obteniendo requisitos personalizados empresa %s: %s", empresa_id, e)
            raise DatabaseError(f"Error obteniendo documentos adicionales: {e}")

    async def _resolver_regla_documento(
        self,
        empresa_id: int,
        tipo: TipoDocumentoEmpresa,
        requisito_id: int | None = None,
    ) -> tuple[str, bool, int | None]:
        """Resuelve etiqueta, anualidad y requisito aplicable para el upload."""
        if tipo == TipoDocumentoEmpresa.DOCUMENTO_ADICIONAL:
            if not requisito_id:
                raise ValidationError("Selecciona el documento adicional que deseas subir")
            requisitos = await self.obtener_requisitos_personalizados(empresa_id)
            requisito = next((req for req in requisitos if req.id == int(requisito_id)), None)
            if requisito is None:
                raise ValidationError("El documento adicional ya no existe o está inactivo")
            return requisito.nombre, bool(requisito.es_anual), requisito.id

        return tipo.descripcion, bool(tipo.es_anual), None

    async def subir_documento(
        self,
        datos: EmpresaDocumentoCreate,
        contenido: bytes,
        nombre_archivo: str,
        tipo_mime: str,
    ) -> EmpresaDocumento:
        """Sube un PDF y crea una nueva versión vigente para empresa + tipo."""

        self._validar_anio(datos.anio)
        tipo = self._coerce_tipo(datos.tipo_documento)
        descripcion_documento, es_anual, requisito_id = await self._resolver_regla_documento(
            datos.empresa_id,
            tipo,
            datos.requisito_id,
        )

        try:
            archivo_resp = await archivo_service.subir_archivo(
                contenido=contenido,
                nombre_original=nombre_archivo,
                tipo_mime=tipo_mime,
                entidad_tipo=EntidadArchivo.EMPRESA,
                entidad_id=datos.empresa_id,
                identificador_ruta=f"{datos.empresa_id}/{datos.anio}",
                sub_identificador=(
                    f"requisito_{requisito_id}" if requisito_id else tipo.value
                ),
                tipo_archivo=TipoArchivo.DOCUMENTO,
                descripcion=(
                    f"{descripcion_documento} - empresa {datos.empresa_id} - año {datos.anio}"
                ),
            )

            update_query = (
                self.supabase.table(self.tabla_documentos)
                .update({"es_vigente": False})
                .eq("empresa_id", datos.empresa_id)
                .eq("tipo_documento", tipo.value)
                .eq("es_vigente", True)
            )
            update_query = self._apply_requisito_filter(update_query, requisito_id)
            if es_anual:
                update_query = update_query.eq("anio", datos.anio)
            update_query.execute()

            version_query = (
                self.supabase.table(self.tabla_documentos)
                .select("version")
                .eq("empresa_id", datos.empresa_id)
                .eq("tipo_documento", tipo.value)
            )
            version_query = self._apply_requisito_filter(version_query, requisito_id)
            if es_anual:
                version_query = version_query.eq("anio", datos.anio)
            version_result = version_query.order("version", desc=True).limit(1).execute()

            nueva_version = 1
            if version_result.data:
                nueva_version = int(version_result.data[0]["version"]) + 1

            payload = {
                "empresa_id": datos.empresa_id,
                "anio": datos.anio,
                "tipo_documento": tipo.value,
                "requisito_id": requisito_id,
                "archivo_id": archivo_resp.archivo.id,
                "nombre_archivo": nombre_archivo,
                "version": nueva_version,
                "es_vigente": True,
                "subido_por": str(datos.subido_por) if datos.subido_por else None,
            }
            result = self.supabase.table(self.tabla_documentos).insert(payload).execute()
            if not result.data:
                raise DatabaseError("No se pudo registrar el documento de empresa")

            return EmpresaDocumento(**result.data[0])
        except (DatabaseError, ValidationError):
            raise
        except Exception as e:
            logger.error("Error subiendo documento de empresa: %s", e)
            raise DatabaseError(f"Error subiendo documento de empresa: {e}")

    async def obtener_documentos_empresa(
        self,
        empresa_id: int,
        anio: int,
        *,
        solo_vigentes: bool = True,
    ) -> list[EmpresaDocumento]:
        """Obtiene documentos cargados de una empresa en un año específico."""
        self._validar_anio(anio)
        try:
            query = (
                self.supabase.table(self.tabla_documentos)
                .select("*")
                .eq("empresa_id", empresa_id)
                .eq("anio", anio)
                .order("tipo_documento")
                .order("requisito_id")
                .order("version", desc=True)
            )
            if solo_vigentes:
                query = query.eq("es_vigente", True)
            result = query.execute()
            return [EmpresaDocumento(**row) for row in (result.data or [])]
        except Exception as e:
            logger.error("Error obteniendo documentos de empresa %s/%s: %s", empresa_id, anio, e)
            raise DatabaseError(f"Error obteniendo documentos de empresa: {e}")

    async def obtener_documentos_empresa_hasta_anio(
        self,
        empresa_id: int,
        anio: int,
        *,
        solo_vigentes: bool = True,
    ) -> list[EmpresaDocumento]:
        """Obtiene documentos de empresa cargados hasta un año dado."""
        self._validar_anio(anio)
        try:
            query = (
                self.supabase.table(self.tabla_documentos)
                .select("*")
                .eq("empresa_id", empresa_id)
                .lte("anio", anio)
                .order("tipo_documento")
                .order("requisito_id")
                .order("anio", desc=True)
                .order("version", desc=True)
            )
            if solo_vigentes:
                query = query.eq("es_vigente", True)
            result = query.execute()
            return [EmpresaDocumento(**row) for row in (result.data or [])]
        except Exception as e:
            logger.error("Error obteniendo documentos vigentes hasta %s/%s: %s", empresa_id, anio, e)
            raise DatabaseError(f"Error obteniendo documentos de empresa: {e}")

    async def obtener_expediente_empresa(self, empresa_id: int, anio: int) -> dict[str, Any]:
        """Retorna checklist serializable con métricas de completitud."""
        self._validar_anio(anio)
        documentos = await self.obtener_documentos_empresa_hasta_anio(
            empresa_id,
            anio,
            solo_vigentes=True,
        )
        requisitos_personalizados = await self.obtener_requisitos_personalizados(empresa_id)

        documentos_exactos: dict[tuple[str, int], EmpresaDocumento] = {}
        documentos_vigentes: dict[tuple[str, int], EmpresaDocumento] = {}

        for documento in documentos:
            key = self._documento_key(documento.tipo_documento, documento.requisito_id)
            documentos_vigentes.setdefault(key, documento)
            if documento.anio == anio:
                documentos_exactos.setdefault(key, documento)

        definiciones_base = sorted(
            [tipo for tipo in TipoDocumentoEmpresa if tipo.es_visible_en_checklist],
            key=lambda tipo: tipo.numero,
        )

        checklist: list[dict[str, Any]] = []
        total_requeridos = 0
        subidos_requeridos = 0

        for tipo in definiciones_base:
            key = self._documento_key(tipo.value, None)
            doc = documentos_exactos.get(key) if tipo.es_anual else documentos_vigentes.get(key)
            obligatorio = tipo.es_obligatorio
            if obligatorio:
                total_requeridos += 1
                if doc:
                    subidos_requeridos += 1

            origen_documento_texto = ""
            if doc and not tipo.es_anual and doc.anio != anio:
                origen_documento_texto = f"Vigente desde {doc.anio}"

            resumen = EmpresaDocumentoResumen(
                id=doc.id if doc else None,
                empresa_id=empresa_id,
                anio=anio,
                numero=len(checklist) + 1,
                tipo_documento=tipo.value,
                requisito_id=None,
                tipo_documento_label=tipo.etiqueta(anio),
                ayuda=tipo.ayuda(anio),
                obligatorio=obligatorio,
                es_anual=tipo.es_anual,
                es_personalizado=False,
                estatus="Subido" if doc else ("No aplica" if not obligatorio else "Pendiente"),
                subido=bool(doc),
                archivo_id=doc.archivo_id if doc else None,
                nombre_archivo=(doc.nombre_archivo or "PDF cargado") if doc else "",
                version=doc.version if doc else 0,
                anio_documento=doc.anio if doc else None,
                origen_documento_texto=origen_documento_texto,
                fecha_creacion=doc.fecha_creacion if doc else None,
            )
            checklist.append(resumen.model_dump(mode="json"))

        for requisito in requisitos_personalizados:
            key = self._documento_key(TipoDocumentoEmpresa.DOCUMENTO_ADICIONAL.value, requisito.id)
            doc = (
                documentos_exactos.get(key)
                if requisito.es_anual
                else documentos_vigentes.get(key)
            )
            obligatorio = bool(requisito.es_obligatorio)
            if obligatorio:
                total_requeridos += 1
                if doc:
                    subidos_requeridos += 1

            origen_documento_texto = ""
            if doc and not requisito.es_anual and doc.anio != anio:
                origen_documento_texto = f"Vigente desde {doc.anio}"

            resumen = EmpresaDocumentoResumen(
                id=doc.id if doc else None,
                empresa_id=empresa_id,
                anio=anio,
                numero=len(checklist) + 1,
                tipo_documento=TipoDocumentoEmpresa.DOCUMENTO_ADICIONAL.value,
                requisito_id=requisito.id,
                tipo_documento_label=requisito.nombre,
                ayuda=requisito.ayuda or "Documento adicional definido para esta empresa.",
                obligatorio=obligatorio,
                es_anual=bool(requisito.es_anual),
                es_personalizado=True,
                estatus="Subido" if doc else ("No aplica" if not obligatorio else "Pendiente"),
                subido=bool(doc),
                archivo_id=doc.archivo_id if doc else None,
                nombre_archivo=(doc.nombre_archivo or "PDF cargado") if doc else "",
                version=doc.version if doc else 0,
                anio_documento=doc.anio if doc else None,
                origen_documento_texto=origen_documento_texto,
                fecha_creacion=doc.fecha_creacion if doc else None,
            )
            checklist.append(resumen.model_dump(mode="json"))

        porcentaje = int((subidos_requeridos / total_requeridos) * 100) if total_requeridos else 0
        return {
            "empresa_id": empresa_id,
            "anio": anio,
            "documentos": checklist,
            "documentos_requeridos": total_requeridos,
            "documentos_subidos_requeridos": subidos_requeridos,
            "porcentaje_completitud": porcentaje,
        }

    async def obtener_share_link_activo(
        self,
        empresa_id: int,
        anio: int,
    ) -> Optional[EmpresaDocumentoShareLink]:
        """Obtiene el link compartible no expirado de un expediente."""
        self._validar_anio(anio)
        ahora = self._ahora_utc().isoformat()
        try:
            result = (
                self.supabase.table(self.tabla_share_links)
                .select("*")
                .eq("empresa_id", empresa_id)
                .eq("anio", anio)
                .is_("revoked_at", "null")
                .gt("expires_at", ahora)
                .order("created_at", desc=True)
                .limit(1)
                .execute()
            )
            if not result.data:
                return None
            return EmpresaDocumentoShareLink(**result.data[0])
        except Exception as e:
            logger.error("Error obteniendo link activo empresa %s/%s: %s", empresa_id, anio, e)
            raise DatabaseError(f"Error obteniendo link compartible: {e}")

    async def generar_share_link(
        self,
        empresa_id: int,
        anio: int,
        expires_at: datetime,
        *,
        created_by=None,
    ) -> dict[str, Any]:
        """Genera un nuevo link compartible y revoca el anterior si existía."""
        self._validar_anio(anio)

        if expires_at.tzinfo is None:
            raise ValidationError("La fecha de expiración debe incluir zona horaria")
        expires_at_utc = expires_at.astimezone(timezone.utc)
        if expires_at_utc <= self._ahora_utc():
            raise ValidationError("La fecha de expiración debe ser futura")

        await self.revocar_share_link(empresa_id, anio, revoked_by=created_by)

        token = secrets.token_urlsafe(32)
        token_hash = self._hash_token(token)
        payload = {
            "empresa_id": empresa_id,
            "anio": anio,
            "token_hash": token_hash,
            "expires_at": expires_at_utc.isoformat(),
            "created_by": str(created_by) if created_by else None,
        }

        try:
            result = self.supabase.table(self.tabla_share_links).insert(payload).execute()
            if not result.data:
                raise DatabaseError("No se pudo crear el link compartible")
            share = EmpresaDocumentoShareLink(**result.data[0])
            return {
                "share_link": share,
                "share_token": token,
                "share_path": self._serializar_share_path(token),
            }
        except (DatabaseError, ValidationError):
            raise
        except Exception as e:
            logger.error("Error generando link compartible empresa %s/%s: %s", empresa_id, anio, e)
            raise DatabaseError(f"Error generando link compartible: {e}")

    async def revocar_share_link(
        self,
        empresa_id: int,
        anio: int,
        *,
        revoked_by=None,
    ) -> int:
        """Revoca links activos para empresa + año."""
        self._validar_anio(anio)
        payload = {
            "revoked_at": self._ahora_utc().isoformat(),
            "revoked_by": str(revoked_by) if revoked_by else None,
        }
        try:
            result = (
                self.supabase.table(self.tabla_share_links)
                .update(payload)
                .eq("empresa_id", empresa_id)
                .eq("anio", anio)
                .is_("revoked_at", "null")
                .execute()
            )
            return len(result.data or [])
        except Exception as e:
            logger.error("Error revocando links de empresa %s/%s: %s", empresa_id, anio, e)
            raise DatabaseError(f"Error revocando link compartible: {e}")

    async def resolver_share_token(self, share_token: str) -> dict[str, Any]:
        """Resuelve un token público y retorna expediente serializable."""
        token = (share_token or "").strip()
        if not token:
            raise NotFoundError("El enlace compartido es inválido")

        token_hash = self._hash_token(token)
        try:
            result = (
                self.supabase.table(self.tabla_share_links)
                .select("*")
                .eq("token_hash", token_hash)
                .is_("revoked_at", "null")
                .limit(1)
                .execute()
            )
            if not result.data:
                raise NotFoundError("El enlace compartido no existe o ya fue revocado")

            share = EmpresaDocumentoShareLink(**result.data[0])
            if share.expires_at <= self._ahora_utc():
                raise BusinessRuleError("El enlace compartido ha expirado")

            empresa = await empresa_service.obtener_por_id(share.empresa_id)
            expediente = await self.obtener_expediente_empresa(share.empresa_id, share.anio)

            return {
                "share": share.model_dump(mode="json"),
                "empresa": {
                    "id": empresa.id,
                    "nombre_comercial": empresa.nombre_comercial,
                    "razon_social": empresa.razon_social,
                    "rfc": empresa.rfc,
                    "codigo_corto": empresa.codigo_corto,
                },
                **expediente,
            }
        except (NotFoundError, BusinessRuleError, DatabaseError):
            raise
        except Exception as e:
            logger.error("Error resolviendo token compartido: %s", e)
            raise DatabaseError(f"Error resolviendo enlace compartido: {e}")


empresa_documento_service = EmpresaDocumentoService()
