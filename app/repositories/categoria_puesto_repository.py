"""
Repositorio de Categorías de Puesto - Interface y implementación para Supabase.

Nota: La clave es única DENTRO del tipo_servicio, no global.

Patrón de manejo de errores:
- NotFoundError: Cuando no se encuentra un recurso
- DuplicateError: Cuando se viola unicidad (clave duplicada en el mismo tipo)
- DatabaseError: Errores de conexión o infraestructura
"""
from abc import ABC, abstractmethod
from typing import List, Optional
import logging

from app.entities.categoria_puesto import CategoriaPuesto
from app.core.exceptions import NotFoundError, DuplicateError, DatabaseError

logger = logging.getLogger(__name__)


class ICategoriaPuestoRepository(ABC):
    """Interface del repositorio de categorías de puesto"""

    @abstractmethod
    async def obtener_por_id(self, categoria_id: int) -> CategoriaPuesto:
        """Obtiene una categoría por su ID"""
        pass

    @abstractmethod
    async def obtener_por_tipo_servicio(
        self,
        tipo_servicio_id: int,
        incluir_inactivas: bool = False
    ) -> List[CategoriaPuesto]:
        """Obtiene todas las categorías de un tipo de servicio"""
        pass

    @abstractmethod
    async def obtener_todas(
        self,
        incluir_inactivas: bool = False,
        limite: Optional[int] = None,
        offset: int = 0
    ) -> List[CategoriaPuesto]:
        """Obtiene todas las categorías con paginación"""
        pass

    @abstractmethod
    async def crear(self, categoria: CategoriaPuesto) -> CategoriaPuesto:
        """Crea una nueva categoría"""
        pass

    @abstractmethod
    async def actualizar(self, categoria: CategoriaPuesto) -> CategoriaPuesto:
        """Actualiza una categoría existente"""
        pass

    @abstractmethod
    async def eliminar(self, categoria_id: int) -> bool:
        """Elimina (soft delete) una categoría"""
        pass

    @abstractmethod
    async def existe_clave_en_tipo(
        self,
        tipo_servicio_id: int,
        clave: str,
        excluir_id: Optional[int] = None
    ) -> bool:
        """Verifica si existe una clave dentro del tipo de servicio"""
        pass


class SupabaseCategoriaPuestoRepository(ICategoriaPuestoRepository):
    """Implementación del repositorio usando Supabase"""

    def __init__(self, db_manager=None):
        if db_manager is None:
            from app.database import db_manager as default_db
            db_manager = default_db

        self.supabase = db_manager.get_client()
        self.tabla = 'categorias_puesto'

    async def obtener_por_id(self, categoria_id: int) -> CategoriaPuesto:
        """
        Obtiene una categoría por su ID.

        Raises:
            NotFoundError: Si la categoría no existe
            DatabaseError: Si hay error de conexión
        """
        try:
            result = self.supabase.table(self.tabla).select('*').eq('id', categoria_id).execute()

            if not result.data:
                raise NotFoundError(f"Categoría de puesto con ID {categoria_id} no encontrada")

            return CategoriaPuesto(**result.data[0])

        except NotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error obteniendo categoría {categoria_id}: {e}")
            raise DatabaseError(f"Error de base de datos: {str(e)}")

    async def obtener_por_tipo_servicio(
        self,
        tipo_servicio_id: int,
        incluir_inactivas: bool = False
    ) -> List[CategoriaPuesto]:
        """
        Obtiene todas las categorías de un tipo de servicio.

        Returns:
            Lista ordenada por 'orden' y luego por 'nombre'
        """
        try:
            query = self.supabase.table(self.tabla).select('*').eq('tipo_servicio_id', tipo_servicio_id)

            if not incluir_inactivas:
                query = query.eq('estatus', 'ACTIVO')

            query = query.order('orden', desc=False).order('nombre', desc=False)

            result = query.execute()
            return [CategoriaPuesto(**data) for data in result.data]

        except Exception as e:
            logger.error(f"Error obteniendo categorías del tipo {tipo_servicio_id}: {e}")
            raise DatabaseError(f"Error de base de datos: {str(e)}")

    async def obtener_todas(
        self,
        incluir_inactivas: bool = False,
        limite: Optional[int] = None,
        offset: int = 0
    ) -> List[CategoriaPuesto]:
        """
        Obtiene todas las categorías con paginación.
        """
        try:
            query = self.supabase.table(self.tabla).select('*')

            if not incluir_inactivas:
                query = query.eq('estatus', 'ACTIVO')

            query = query.order('tipo_servicio_id', desc=False).order('orden', desc=False)

            if limite is None:
                limite = 100

            query = query.range(offset, offset + limite - 1)

            result = query.execute()
            return [CategoriaPuesto(**data) for data in result.data]

        except Exception as e:
            logger.error(f"Error obteniendo categorías: {e}")
            raise DatabaseError(f"Error de base de datos: {str(e)}")

    async def crear(self, categoria: CategoriaPuesto) -> CategoriaPuesto:
        """
        Crea una nueva categoría de puesto.

        Raises:
            DuplicateError: Si la clave ya existe en el tipo de servicio
            DatabaseError: Si hay error de conexión
        """
        try:
            # Verificar clave duplicada dentro del tipo
            if await self.existe_clave_en_tipo(categoria.tipo_servicio_id, categoria.clave):
                raise DuplicateError(
                    f"La clave '{categoria.clave}' ya existe en este tipo de servicio",
                    field="clave",
                    value=categoria.clave
                )

            datos = categoria.model_dump(exclude={'id', 'fecha_creacion', 'fecha_actualizacion'})
            result = self.supabase.table(self.tabla).insert(datos).execute()

            if not result.data:
                raise DatabaseError("No se pudo crear la categoría")

            return CategoriaPuesto(**result.data[0])

        except DuplicateError:
            raise
        except Exception as e:
            logger.error(f"Error creando categoría: {e}")
            raise DatabaseError(f"Error de base de datos: {str(e)}")

    async def actualizar(self, categoria: CategoriaPuesto) -> CategoriaPuesto:
        """
        Actualiza una categoría existente.

        Raises:
            NotFoundError: Si la categoría no existe
            DuplicateError: Si la clave ya existe en el tipo de servicio
            DatabaseError: Si hay error de conexión
        """
        try:
            await self.obtener_por_id(categoria.id)

            # Verificar clave duplicada (excluyendo registro actual)
            if await self.existe_clave_en_tipo(
                categoria.tipo_servicio_id,
                categoria.clave,
                excluir_id=categoria.id
            ):
                raise DuplicateError(
                    f"La clave '{categoria.clave}' ya existe en este tipo de servicio",
                    field="clave",
                    value=categoria.clave
                )

            datos = categoria.model_dump(exclude={'id', 'fecha_creacion', 'fecha_actualizacion'})
            result = self.supabase.table(self.tabla).update(datos).eq('id', categoria.id).execute()

            if not result.data:
                raise NotFoundError(f"Categoría con ID {categoria.id} no encontrada")

            return CategoriaPuesto(**result.data[0])

        except (NotFoundError, DuplicateError):
            raise
        except Exception as e:
            logger.error(f"Error actualizando categoría {categoria.id}: {e}")
            raise DatabaseError(f"Error de base de datos: {str(e)}")

    async def eliminar(self, categoria_id: int) -> bool:
        """
        Elimina (soft delete) una categoría.
        """
        try:
            await self.obtener_por_id(categoria_id)

            result = self.supabase.table(self.tabla).update(
                {'estatus': 'INACTIVO'}
            ).eq('id', categoria_id).execute()

            return bool(result.data)

        except NotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error eliminando categoría {categoria_id}: {e}")
            raise DatabaseError(f"Error de base de datos: {str(e)}")

    async def existe_clave_en_tipo(
        self,
        tipo_servicio_id: int,
        clave: str,
        excluir_id: Optional[int] = None
    ) -> bool:
        """
        Verifica si existe una clave dentro del tipo de servicio.
        """
        try:
            query = self.supabase.table(self.tabla)\
                .select('id')\
                .eq('tipo_servicio_id', tipo_servicio_id)\
                .eq('clave', clave.upper())

            if excluir_id:
                query = query.neq('id', excluir_id)

            result = query.execute()
            return len(result.data) > 0

        except Exception as e:
            logger.error(f"Error verificando clave {clave}: {e}")
            raise DatabaseError(f"Error de base de datos: {str(e)}")

    async def buscar_por_texto(
        self,
        termino: str,
        tipo_servicio_id: Optional[int] = None,
        limite: int = 10
    ) -> List[CategoriaPuesto]:
        """
        Busca categorías por nombre o clave.
        """
        try:
            termino_upper = termino.upper()

            query = self.supabase.table(self.tabla)\
                .select('*')\
                .eq('estatus', 'ACTIVO')\
                .or_(
                    f"nombre.ilike.%{termino_upper}%,"
                    f"clave.ilike.%{termino_upper}%"
                )

            if tipo_servicio_id:
                query = query.eq('tipo_servicio_id', tipo_servicio_id)

            query = query.limit(limite)
            result = query.execute()

            return [CategoriaPuesto(**data) for data in result.data]

        except Exception as e:
            logger.error(f"Error buscando categorías con término '{termino}': {e}")
            raise DatabaseError(f"Error de base de datos: {str(e)}")
