"""
Repositorio de Tipos de Servicio - Implementacion para Supabase.

Patron de manejo de errores:
- NotFoundError: Cuando no se encuentra un recurso
- DuplicateError: Cuando se viola unicidad (ej: clave duplicada)
- DatabaseError: Errores de conexion o infraestructura
"""
import logging
from typing import List, Optional

from app.entities import (
    TipoServicio,
)
from app.core.enums import Estatus
from app.core.exceptions import NotFoundError, DuplicateError, DatabaseError

logger = logging.getLogger(__name__)


class SupabaseTipoServicioRepository:
    """Implementacion del repositorio de tipos de servicio usando Supabase."""

    def __init__(self, db_manager=None):
        if db_manager is None:
            from app.database import db_manager as default_db
            db_manager = default_db

        self.supabase = db_manager.get_client()
        self.tabla = 'tipos_servicio'

    async def obtener_por_id(self, tipo_id: int) -> TipoServicio:
        """
        Obtiene un tipo de servicio por su ID.

        Raises:
            NotFoundError: Si el tipo no existe
            DatabaseError: Si hay error de BD
        """
        try:
            result = self.supabase.table(self.tabla).select('*').eq('id', tipo_id).execute()

            if not result.data:
                raise NotFoundError(f"Tipo de servicio con ID {tipo_id} no encontrado")

            return TipoServicio(**result.data[0])

        except NotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error obteniendo tipo de servicio {tipo_id}: {e}")
            raise DatabaseError(f"Error de base de datos al obtener tipo: {str(e)}")

    async def obtener_por_clave(self, clave: str) -> Optional[TipoServicio]:
        """
        Obtiene un tipo de servicio por su clave.

        Raises:
            DatabaseError: Si hay error de BD
        """
        try:
            result = self.supabase.table(self.tabla).select('*').eq('clave', clave.upper()).execute()

            if not result.data:
                return None

            return TipoServicio(**result.data[0])

        except Exception as e:
            logger.error(f"Error obteniendo tipo por clave {clave}: {e}")
            raise DatabaseError(f"Error de base de datos al obtener tipo: {str(e)}")

    async def obtener_todas(
        self,
        incluir_inactivas: bool = False,
        limite: Optional[int] = None,
        offset: int = 0
    ) -> List[TipoServicio]:
        """
        Obtiene todos los tipos de servicio con paginacion.

        Raises:
            DatabaseError: Si hay error de BD
        """
        try:
            query = self.supabase.table(self.tabla).select('*')

            if not incluir_inactivas:
                query = query.eq('estatus', Estatus.ACTIVO.value)

            query = query.order('nombre', desc=False)

            if limite is None:
                limite = 100

            query = query.range(offset, offset + limite - 1)

            result = query.execute()
            return [TipoServicio(**data) for data in result.data]

        except Exception as e:
            logger.error(f"Error obteniendo tipos de servicio: {e}")
            raise DatabaseError(f"Error de base de datos al obtener tipos: {str(e)}")

    async def buscar_por_texto(self, termino: str, limite: int = 10, offset: int = 0) -> List[TipoServicio]:
        """
        Busca tipos de servicio por nombre o clave.

        Raises:
            DatabaseError: Si hay error de BD
        """
        try:
            termino_upper = termino.upper()

            result = self.supabase.table(self.tabla)\
                .select('*')\
                .eq('estatus', Estatus.ACTIVO.value)\
                .or_(
                    f"nombre.ilike.%{termino_upper}%,"
                    f"clave.ilike.%{termino_upper}%"
                )\
                .range(offset, offset + limite - 1)\
                .execute()

            return [TipoServicio(**data) for data in result.data]

        except Exception as e:
            logger.error(f"Error buscando tipos con termino '{termino}': {e}")
            raise DatabaseError(f"Error de base de datos al buscar tipos: {str(e)}")

    async def contar(self, incluir_inactivas: bool = False) -> int:
        """
        Cuenta el total de tipos de servicio.

        Raises:
            DatabaseError: Si hay error de BD
        """
        try:
            query = self.supabase.table(self.tabla).select('id', count='exact')

            if not incluir_inactivas:
                query = query.eq('estatus', Estatus.ACTIVO.value)

            result = query.execute()
            return result.count if result.count else 0

        except Exception as e:
            logger.error(f"Error contando tipos de servicio: {e}")
            raise DatabaseError(f"Error de base de datos al contar tipos: {str(e)}")

    async def crear(self, tipo: TipoServicio) -> TipoServicio:
        """
        Crea un nuevo tipo de servicio.

        Raises:
            DuplicateError: Si la clave ya existe
            DatabaseError: Si hay error de BD
        """
        try:
            if await self.existe_clave(tipo.clave):
                raise DuplicateError(
                    f"La clave '{tipo.clave}' ya existe",
                    field="clave",
                    value=tipo.clave
                )

            datos = tipo.model_dump(exclude={'id', 'fecha_creacion', 'fecha_actualizacion'})
            result = self.supabase.table(self.tabla).insert(datos).execute()

            if not result.data:
                raise DatabaseError("No se pudo crear el tipo de servicio (sin respuesta de BD)")

            return TipoServicio(**result.data[0])

        except (DuplicateError, DatabaseError):
            raise
        except Exception as e:
            logger.error(f"Error creando tipo de servicio: {e}")
            raise DatabaseError(f"Error de base de datos al crear tipo: {str(e)}")

    async def actualizar(self, tipo: TipoServicio) -> TipoServicio:
        """
        Actualiza un tipo de servicio existente.

        Raises:
            NotFoundError: Si el tipo no existe
            DatabaseError: Si hay error de BD
        """
        try:
            datos = tipo.model_dump(exclude={'id', 'fecha_creacion', 'fecha_actualizacion'})
            result = self.supabase.table(self.tabla).update(datos).eq('id', tipo.id).execute()

            if not result.data:
                raise NotFoundError(f"Tipo de servicio con ID {tipo.id} no encontrado")

            return TipoServicio(**result.data[0])

        except NotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error actualizando tipo de servicio {tipo.id}: {e}")
            raise DatabaseError(f"Error de base de datos al actualizar tipo: {str(e)}")

    async def eliminar(self, tipo_id: int) -> bool:
        """
        Elimina (desactiva) un tipo de servicio.

        Raises:
            DatabaseError: Si hay error de BD
        """
        try:
            result = self.supabase.table(self.tabla).update(
                {'estatus': 'INACTIVO'}
            ).eq('id', tipo_id).execute()
            return bool(result.data)
        except Exception as e:
            logger.error(f"Error eliminando tipo de servicio {tipo_id}: {e}")
            raise DatabaseError(f"Error de base de datos al eliminar tipo: {str(e)}")

    async def existe_clave(self, clave: str, excluir_id: Optional[int] = None) -> bool:
        """
        Verifica si una clave ya existe.

        Raises:
            DatabaseError: Si hay error de BD
        """
        try:
            query = self.supabase.table(self.tabla).select('id').eq('clave', clave.upper())

            if excluir_id:
                query = query.neq('id', excluir_id)

            result = query.execute()
            return len(result.data) > 0

        except Exception as e:
            logger.error(f"Error verificando clave {clave}: {e}")
            raise DatabaseError(f"Error de base de datos al verificar clave: {str(e)}")
