"""
Repositorio de Archivos del Sistema - Implementacion para Supabase.

Maneja operaciones de base de datos y Supabase Storage para archivos.

Patron de manejo de errores:
- NotFoundError: Cuando no se encuentra un archivo
- DatabaseError: Errores de conexion o infraestructura
"""
import logging
from typing import List, Optional

from app.core.config.archivos_config import ArchivosConfig
from app.core.exceptions import DatabaseError, NotFoundError
from app.entities.archivo import (
    ArchivoSistema,
    ArchivoSistemaUpdate,
    EntidadArchivo,
)

logger = logging.getLogger(__name__)


class SupabaseArchivoRepository:
    """Implementacion del repositorio de archivos usando Supabase (BD + Storage)."""

    def __init__(self, db_manager=None):
        if db_manager is None:
            from app.database import db_manager as default_db
            db_manager = default_db

        self.supabase = db_manager.get_client()
        self.tabla = 'archivo_sistema'

    # ==========================================
    # OPERACIONES DE BASE DE DATOS
    # ==========================================

    async def contar_por_entidad(
        self,
        entidad_tipo: EntidadArchivo,
        entidad_id: int,
    ) -> int:
        """
        Cuenta los archivos de una entidad.

        Raises:
            DatabaseError: Si hay error de BD
        """
        tipo_valor = (
            entidad_tipo.value
            if isinstance(entidad_tipo, EntidadArchivo)
            else entidad_tipo
        )

        try:
            result = (
                self.supabase.table(self.tabla)
                .select("id", count="exact")
                .eq("entidad_tipo", tipo_valor)
                .eq("entidad_id", entidad_id)
                .execute()
            )
            return result.count or 0
        except Exception as e:
            logger.error(
                f"Error contando archivos de {entidad_tipo}/{entidad_id}: {e}"
            )
            raise DatabaseError(f"Error de base de datos: {str(e)}")

    async def crear(self, datos: dict) -> ArchivoSistema:
        """
        Crea un registro de archivo en la BD.

        Raises:
            DatabaseError: Si hay error de BD
        """
        try:
            result = (
                self.supabase.table(self.tabla).insert(datos).execute()
            )

            if not result.data:
                raise DatabaseError("No se pudo crear el registro de archivo")

            return ArchivoSistema(**result.data[0])
        except DatabaseError:
            raise
        except Exception as e:
            logger.error(f"Error creando archivo en BD: {e}")
            raise DatabaseError(
                f"Error de base de datos al crear archivo: {str(e)}"
            )

    async def obtener_por_id(self, archivo_id: int) -> ArchivoSistema:
        """
        Obtiene un archivo por ID.

        Raises:
            NotFoundError: Si el archivo no existe
            DatabaseError: Si hay error de BD
        """
        try:
            result = (
                self.supabase.table(self.tabla)
                .select("*")
                .eq("id", archivo_id)
                .execute()
            )

            if not result.data:
                raise NotFoundError(
                    f"Archivo con ID {archivo_id} no encontrado"
                )

            return ArchivoSistema(**result.data[0])
        except NotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error obteniendo archivo {archivo_id}: {e}")
            raise DatabaseError(f"Error de base de datos: {str(e)}")

    async def obtener_por_entidad(
        self,
        entidad_tipo: EntidadArchivo,
        entidad_id: int,
    ) -> List[ArchivoSistema]:
        """
        Obtiene todos los archivos de una entidad.

        Raises:
            DatabaseError: Si hay error de BD
        """
        try:
            tipo_valor = (
                entidad_tipo.value
                if isinstance(entidad_tipo, EntidadArchivo)
                else entidad_tipo
            )
            result = (
                self.supabase.table(self.tabla)
                .select("*")
                .eq("entidad_tipo", tipo_valor)
                .eq("entidad_id", entidad_id)
                .order("orden")
                .order("created_at")
                .execute()
            )
            return [ArchivoSistema(**data) for data in result.data]
        except Exception as e:
            logger.error(
                f"Error obteniendo archivos de {entidad_tipo}/{entidad_id}: {e}"
            )
            raise DatabaseError(f"Error de base de datos: {str(e)}")

    async def actualizar(
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
        try:
            update_data = data.model_dump(exclude_none=True)
            if not update_data:
                return await self.obtener_por_id(archivo_id)

            result = (
                self.supabase.table(self.tabla)
                .update(update_data)
                .eq("id", archivo_id)
                .execute()
            )

            if not result.data:
                raise NotFoundError(
                    f"Archivo con ID {archivo_id} no encontrado"
                )

            return ArchivoSistema(**result.data[0])
        except NotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error actualizando archivo {archivo_id}: {e}")
            raise DatabaseError(f"Error de base de datos: {str(e)}")

    async def eliminar(self, archivo_id: int) -> bool:
        """
        Elimina un registro de archivo de la BD.

        Raises:
            DatabaseError: Si hay error de BD
        """
        try:
            result = (
                self.supabase.table(self.tabla)
                .delete()
                .eq("id", archivo_id)
                .execute()
            )
            return bool(result.data)
        except Exception as e:
            logger.error(f"Error eliminando archivo {archivo_id}: {e}")
            raise DatabaseError(f"Error de base de datos: {str(e)}")

    async def eliminar_por_entidad(
        self,
        entidad_tipo: EntidadArchivo,
        entidad_id: int,
    ) -> int:
        """
        Elimina todos los registros de archivo de una entidad.

        Returns:
            Cantidad de registros eliminados.

        Raises:
            DatabaseError: Si hay error de BD
        """
        try:
            tipo_valor = (
                entidad_tipo.value
                if isinstance(entidad_tipo, EntidadArchivo)
                else entidad_tipo
            )
            result = (
                self.supabase.table(self.tabla)
                .delete()
                .eq("entidad_tipo", tipo_valor)
                .eq("entidad_id", entidad_id)
                .execute()
            )
            return len(result.data) if result.data else 0
        except Exception as e:
            logger.error(
                f"Error eliminando archivos de {entidad_tipo}/{entidad_id}: {e}"
            )
            raise DatabaseError(f"Error de base de datos: {str(e)}")

    # ==========================================
    # OPERACIONES DE STORAGE
    # ==========================================

    def subir_a_storage(
        self,
        ruta_storage: str,
        contenido: bytes,
        tipo_mime: str,
    ) -> None:
        """
        Sube un archivo a Supabase Storage.

        Raises:
            Exception: Si hay error al subir
        """
        self.supabase.storage.from_(ArchivosConfig.BUCKET_NAME).upload(
            path=ruta_storage,
            file=contenido,
            file_options={"content-type": tipo_mime},
        )

    def crear_url_temporal(
        self,
        ruta_storage: str,
        expiracion_segundos: int = 3600,
    ) -> str:
        """
        Genera URL temporal firmada para un archivo.

        Raises:
            Exception: Si hay error al generar URL
        """
        response = self.supabase.storage.from_(
            ArchivosConfig.BUCKET_NAME
        ).create_signed_url(
            path=ruta_storage,
            expires_in=expiracion_segundos,
        )
        return response["signedURL"]

    def eliminar_de_storage(self, rutas: List[str]) -> None:
        """
        Elimina archivos de Supabase Storage.

        Args:
            rutas: Lista de rutas a eliminar
        """
        self.supabase.storage.from_(
            ArchivosConfig.BUCKET_NAME
        ).remove(rutas)
