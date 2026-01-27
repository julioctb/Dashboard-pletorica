"""
Servicio generico para gestion de archivos del sistema.

Orquesta compresion, almacenamiento en Supabase Storage,
y registro en base de datos. Generico para cualquier modulo.

Patron de errores:
- ArchivoValidationError: Validacion de formato, tamano o cantidad
- Las excepciones del repository se propagan (NotFoundError, DatabaseError)
"""

import logging
from pathlib import Path
from typing import List, Optional
from uuid import uuid4

from app.core.compresores import GhostscriptCompressor, ImagenCompressor
from app.core.config.archivos_config import ArchivosConfig
from app.core.exceptions import ApplicationError
from app.entities.archivo import (
    ArchivoSistema,
    ArchivoSistemaUpdate,
    ArchivoUploadResponse,
    EntidadArchivo,
    OrigenArchivo,
    TipoArchivo,
)
from app.repositories.archivo_repository import SupabaseArchivoRepository

logger = logging.getLogger(__name__)


class ArchivoValidationError(ApplicationError):
    """Error de validacion de archivo (formato, tamano, cantidad)."""

    pass


class ArchivoService:
    """
    Servicio generico para gestion de archivos del sistema.

    Maneja compresion, upload a Storage, registro en BD y eliminacion.
    """

    def __init__(self, repository=None):
        if repository is None:
            repository = SupabaseArchivoRepository()
        self.repository = repository

        from app.database import db_manager

        self.supabase = db_manager.get_client()

    # ==========================================
    # VALIDACIONES
    # ==========================================

    def _validar_tipo_mime(
        self, tipo_mime: str, origen: OrigenArchivo
    ) -> None:
        """Valida que el tipo MIME este permitido."""
        if tipo_mime not in ArchivosConfig.FORMATOS_PERMITIDOS:
            raise ArchivoValidationError(
                f"Formato no permitido: {tipo_mime}. "
                f"Formatos validos: {', '.join(ArchivosConfig.FORMATOS_PERMITIDOS)}"
            )

    def _validar_tamanio(self, tamanio: int, es_imagen: bool) -> None:
        """Valida el tamano del archivo."""
        if es_imagen:
            limite = ArchivosConfig.WEB_TAMANIO_MAX_IMAGEN_ORIGINAL
            tipo = "imagen"
        else:
            limite = ArchivosConfig.WEB_TAMANIO_MAX_PDF
            tipo = "PDF"

        if tamanio > limite:
            limite_mb = limite / (1024 * 1024)
            tamanio_mb = tamanio / (1024 * 1024)
            raise ArchivoValidationError(
                f"El {tipo} excede el limite de {limite_mb:.0f} MB "
                f"(tamano: {tamanio_mb:.1f} MB)"
            )

    async def _validar_cantidad(
        self,
        entidad_tipo: EntidadArchivo,
        entidad_id: int,
    ) -> None:
        """Valida que no se exceda el limite de archivos."""
        cantidad = await self.repository.contar_archivos(
            entidad_tipo, entidad_id
        )
        tipo_valor = (
            entidad_tipo.value
            if isinstance(entidad_tipo, EntidadArchivo)
            else entidad_tipo
        )
        limite = ArchivosConfig.get_max_archivos(tipo_valor)

        if cantidad >= limite:
            raise ArchivoValidationError(
                f"Se alcanzo el limite de {limite} archivos para {tipo_valor}"
            )

    # ==========================================
    # PROCESAMIENTO
    # ==========================================

    def _procesar_imagen(
        self, contenido: bytes, nombre: str
    ) -> tuple[bytes, dict]:
        """Procesa y comprime una imagen a WebP."""
        if not ImagenCompressor.validar_imagen(contenido):
            raise ArchivoValidationError(
                "El archivo no es una imagen valida"
            )

        extension = Path(nombre).suffix
        return ImagenCompressor.comprimir_imagen(contenido, extension)

    def _procesar_pdf(self, contenido: bytes) -> tuple[bytes, dict]:
        """Procesa y comprime un PDF."""
        if not GhostscriptCompressor.validar_pdf(contenido):
            raise ArchivoValidationError("El archivo no es un PDF valido")

        contenido_final, metadata = (
            GhostscriptCompressor.comprimir_si_necesario(contenido)
        )

        if len(contenido_final) > ArchivosConfig.WEB_TAMANIO_MAX_PDF:
            raise ArchivoValidationError(
                "El PDF excede el limite incluso despues de comprimir. "
                "Por favor, reduzca el tamano manualmente."
            )

        return contenido_final, metadata

    def _generar_nombre_storage(
        self, nombre_original: str, es_imagen: bool
    ) -> str:
        """Genera nombre unico para storage."""
        extension = ".webp" if es_imagen else Path(nombre_original).suffix
        return f"{uuid4().hex}{extension}"

    # ==========================================
    # OPERACIONES CRUD
    # ==========================================

    async def subir_archivo(
        self,
        contenido: bytes,
        nombre_original: str,
        tipo_mime: str,
        entidad_tipo: EntidadArchivo,
        entidad_id: int,
        identificador_ruta: str,
        tipo_archivo: TipoArchivo,
        descripcion: Optional[str] = None,
        orden: int = 0,
        sub_identificador: Optional[str] = None,
        origen: OrigenArchivo = OrigenArchivo.WEB,
    ) -> ArchivoUploadResponse:
        """
        Sube un archivo al sistema (comprime, almacena, registra).

        Args:
            contenido: Bytes del archivo
            nombre_original: Nombre original del archivo
            tipo_mime: Tipo MIME del archivo
            entidad_tipo: Tipo de entidad (REQUISICION, REPORTE, etc.)
            entidad_id: ID de la entidad
            identificador_ruta: Identificador para la ruta (ej: REQ-SA-2025-0001)
            tipo_archivo: Clasificacion (IMAGEN, DOCUMENTO, etc.)
            descripcion: Descripcion opcional
            orden: Orden para multiples archivos
            sub_identificador: Para items/actividades (ej: numero de item)
            origen: WEB o MOVIL

        Returns:
            ArchivoUploadResponse con archivo creado y metadata de compresion.

        Raises:
            ArchivoValidationError: Si el archivo no pasa validaciones
            DatabaseError: Si hay error de BD o Storage
        """
        # Validaciones
        self._validar_tipo_mime(tipo_mime, origen)
        es_imagen = tipo_mime in ArchivosConfig.FORMATOS_IMAGEN
        self._validar_tamanio(len(contenido), es_imagen)
        await self._validar_cantidad(entidad_tipo, entidad_id)

        # Procesar (comprimir)
        tamanio_original = len(contenido)

        if es_imagen:
            contenido_final, metadata = self._procesar_imagen(
                contenido, nombre_original
            )
            tipo_mime_final = "image/webp"
        else:
            contenido_final, metadata = self._procesar_pdf(contenido)
            tipo_mime_final = "application/pdf"

        # Generar ruta en Storage
        nombre_storage = self._generar_nombre_storage(
            nombre_original, es_imagen
        )
        tipo_valor = (
            entidad_tipo.value
            if isinstance(entidad_tipo, EntidadArchivo)
            else entidad_tipo
        )
        ruta_storage = ArchivosConfig.get_ruta_storage(
            tipo_valor,
            identificador_ruta,
            nombre_storage,
            sub_identificador,
        )

        # Subir a Supabase Storage
        try:
            self.supabase.storage.from_(ArchivosConfig.BUCKET_NAME).upload(
                path=ruta_storage,
                file=contenido_final,
                file_options={"content-type": tipo_mime_final},
            )
        except Exception as e:
            logger.error(f"Error subiendo archivo a Storage: {e}")
            raise ArchivoValidationError(
                f"Error al subir archivo al almacenamiento: {str(e)}"
            )

        # Crear registro en BD
        archivo = await self.repository.crear(
            entidad_tipo=tipo_valor,
            entidad_id=entidad_id,
            nombre_original=nombre_original,
            nombre_storage=nombre_storage,
            ruta_storage=ruta_storage,
            tipo_mime=tipo_mime_final,
            tamanio_bytes=len(contenido_final),
            tipo_archivo=(
                tipo_archivo.value
                if isinstance(tipo_archivo, TipoArchivo)
                else tipo_archivo
            ),
            descripcion=descripcion,
            orden=orden,
            tamanio_original_bytes=tamanio_original,
            fue_comprimido=metadata.get("comprimido", False),
            formato_original=metadata.get("formato_original"),
            origen=(
                origen.value
                if isinstance(origen, OrigenArchivo)
                else origen
            ),
        )

        return ArchivoUploadResponse(
            archivo=archivo,
            metadata_compresion=metadata,
        )

    async def obtener_archivo(
        self, archivo_id: int
    ) -> Optional[ArchivoSistema]:
        """
        Obtiene un archivo por ID.

        Raises:
            NotFoundError: Si el archivo no existe
            DatabaseError: Si hay error de BD
        """
        return await self.repository.obtener_por_id(archivo_id)

    async def obtener_archivos_entidad(
        self,
        entidad_tipo: EntidadArchivo,
        entidad_id: int,
    ) -> List[ArchivoSistema]:
        """
        Obtiene todos los archivos de una entidad.

        Raises:
            DatabaseError: Si hay error de BD
        """
        return await self.repository.obtener_por_entidad(
            entidad_tipo, entidad_id
        )

    async def obtener_url_temporal(
        self,
        archivo_id: int,
        expiracion_segundos: int = 3600,
    ) -> str:
        """
        Genera URL temporal firmada para un archivo (1 hora por defecto).

        Raises:
            NotFoundError: Si el archivo no existe
            ArchivoValidationError: Si falla la generacion de URL
        """
        archivo = await self.repository.obtener_por_id(archivo_id)

        try:
            response = self.supabase.storage.from_(
                ArchivosConfig.BUCKET_NAME
            ).create_signed_url(
                path=archivo.ruta_storage,
                expires_in=expiracion_segundos,
            )
            return response["signedURL"]
        except Exception as e:
            logger.error(f"Error generando URL temporal: {e}")
            raise ArchivoValidationError(
                f"Error al generar URL del archivo: {str(e)}"
            )

    async def actualizar_archivo(
        self,
        archivo_id: int,
        data: ArchivoSistemaUpdate,
    ) -> ArchivoSistema:
        """
        Actualiza metadata de un archivo.

        Raises:
            NotFoundError: Si el archivo no existe
            DatabaseError: Si hay error de BD
        """
        return await self.repository.actualizar(archivo_id, data)

    async def eliminar_archivo(self, archivo_id: int) -> bool:
        """
        Elimina un archivo (Storage + BD).

        Raises:
            NotFoundError: Si el archivo no existe
            DatabaseError: Si hay error de BD
        """
        archivo = await self.repository.obtener_por_id(archivo_id)

        # Eliminar de Storage
        try:
            self.supabase.storage.from_(ArchivosConfig.BUCKET_NAME).remove(
                [archivo.ruta_storage]
            )
        except Exception as e:
            logger.warning(
                f"Error eliminando archivo de Storage ({archivo.ruta_storage}): {e}"
            )

        return await self.repository.eliminar(archivo_id)

    async def eliminar_archivos_entidad(
        self,
        entidad_tipo: EntidadArchivo,
        entidad_id: int,
    ) -> int:
        """
        Elimina todos los archivos de una entidad (Storage + BD).

        Returns:
            Cantidad de archivos eliminados.

        Raises:
            DatabaseError: Si hay error de BD
        """
        archivos = await self.repository.obtener_por_entidad(
            entidad_tipo, entidad_id
        )

        if archivos:
            rutas = [a.ruta_storage for a in archivos]
            try:
                self.supabase.storage.from_(
                    ArchivosConfig.BUCKET_NAME
                ).remove(rutas)
            except Exception as e:
                logger.warning(
                    f"Error eliminando archivos de Storage: {e}"
                )

        return await self.repository.eliminar_por_entidad(
            entidad_tipo, entidad_id
        )

    # ==========================================
    # UTILIDADES
    # ==========================================

    def verificar_sistema(self) -> dict:
        """Verifica estado de las dependencias del sistema de archivos."""
        gs_disponible = GhostscriptCompressor.esta_disponible()
        gs_version = (
            GhostscriptCompressor.obtener_version()
            if gs_disponible
            else None
        )

        return {
            "ghostscript": {
                "disponible": gs_disponible,
                "version": gs_version,
            },
            "pillow": {
                "disponible": True,
            },
            "storage_bucket": ArchivosConfig.BUCKET_NAME,
        }


# Singleton
archivo_service = ArchivoService()
