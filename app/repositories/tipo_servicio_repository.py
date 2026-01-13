"""
Repositorio de Tipos de Servicio - Interface y implementación para Supabase.

Patrón de manejo de errores:
- NotFoundError: Cuando no se encuentra un recurso
- DuplicateError: Cuando se viola unicidad (ej: clave duplicada)
- DatabaseError: Errores de conexión o infraestructura
- Propagar otras excepciones hacia arriba
"""
from abc import ABC, abstractmethod
from typing import List, Optional
import logging

from app.entities import TipoServicio
from app.core.exceptions import NotFoundError, DuplicateError, DatabaseError

logger = logging.getLogger(__name__)


class ITipoServicioRepository(ABC):
    """Interface del repositorio de tipos de servicio - define el contrato"""

    @abstractmethod
    async def obtener_por_id(self, tipo_id: int) -> TipoServicio:
        """Obtiene un tipo de servicio por su ID"""
        pass

    @abstractmethod
    async def obtener_por_clave(self, clave: str) -> Optional[TipoServicio]:
        """Obtiene un tipo de servicio por su clave"""
        pass

    @abstractmethod
    async def obtener_todas(
        self,
        incluir_inactivas: bool = False,
        limite: Optional[int] = None,
        offset: int = 0
    ) -> List[TipoServicio]:
        """
        Obtiene todos los tipos de servicio con soporte de paginación.

        Args:
            incluir_inactivas: Si True, incluye tipos inactivos
            limite: Número máximo de resultados (None = sin límite)
            offset: Número de registros a saltar (para paginación)
        """
        pass

    @abstractmethod
    async def crear(self, tipo: TipoServicio) -> TipoServicio:
        """Crea un nuevo tipo de servicio"""
        pass

    @abstractmethod
    async def actualizar(self, tipo: TipoServicio) -> TipoServicio:
        """Actualiza un tipo de servicio existente"""
        pass

    @abstractmethod
    async def eliminar(self, tipo_id: int) -> bool:
        """Elimina (inactiva) un tipo de servicio"""
        pass

    @abstractmethod
    async def existe_clave(self, clave: str, excluir_id: Optional[int] = None) -> bool:
        """Verifica si existe una clave en la base de datos"""
        pass

    @abstractmethod
    async def buscar_por_texto(self, termino: str, limite: int = 10) -> List[TipoServicio]:
        """Busca tipos por nombre o clave"""
        pass

    @abstractmethod
    async def contar(self, incluir_inactivas: bool = False) -> int:
        """Cuenta el total de tipos de servicio"""
        pass


class SupabaseTipoServicioRepository(ITipoServicioRepository):
    """Implementación del repositorio usando Supabase"""

    def __init__(self, db_manager=None):
        """
        Inicializa el repositorio con un cliente de Supabase.

        Args:
            db_manager: Gestor de base de datos. Si es None, se importa el global.
        """
        if db_manager is None:
            from app.database import db_manager as default_db
            db_manager = default_db

        self.supabase = db_manager.get_client()
        self.tabla = 'tipos_servicio'

    async def obtener_por_id(self, tipo_id: int) -> TipoServicio:
        """
        Obtiene un tipo de servicio por su ID.

        Args:
            tipo_id: ID del tipo a buscar

        Returns:
            TipoServicio encontrado

        Raises:
            NotFoundError: Si el tipo no existe
            DatabaseError: Si hay error de conexión/infraestructura
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

        Args:
            clave: Clave del tipo a buscar (ej: "JAR", "LIM")

        Returns:
            TipoServicio si existe, None si no existe

        Raises:
            DatabaseError: Si hay error de conexión/infraestructura
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
        Obtiene todos los tipos de servicio con soporte de paginación.

        Args:
            incluir_inactivas: Si True, incluye tipos inactivos
            limite: Número máximo de resultados (None = 100 por defecto)
            offset: Número de registros a saltar (para paginación)

        Returns:
            Lista de tipos de servicio (vacía si no hay resultados)

        Raises:
            DatabaseError: Si hay error de conexión/infraestructura
        """
        try:
            query = self.supabase.table(self.tabla).select('*')

            # Filtro de estatus
            if not incluir_inactivas:
                query = query.eq('estatus', 'ACTIVO')

            # Ordenamiento por nombre
            query = query.order('nombre', desc=False)

            # Paginación con límite por defecto
            if limite is None:
                limite = 100
                logger.debug("Usando límite por defecto de 100 registros")

            query = query.range(offset, offset + limite - 1)

            result = query.execute()
            return [TipoServicio(**data) for data in result.data]

        except Exception as e:
            logger.error(f"Error obteniendo tipos de servicio: {e}")
            raise DatabaseError(f"Error de base de datos al obtener tipos: {str(e)}")

    async def crear(self, tipo: TipoServicio) -> TipoServicio:
        """
        Crea un nuevo tipo de servicio.

        Args:
            tipo: TipoServicio a crear

        Returns:
            TipoServicio creado con ID asignado

        Raises:
            DuplicateError: Si la clave ya existe
            DatabaseError: Si hay error de conexión/infraestructura
        """
        try:
            # Verificar clave duplicada
            if await self.existe_clave(tipo.clave):
                raise DuplicateError(
                    f"La clave '{tipo.clave}' ya existe",
                    field="clave",
                    value=tipo.clave
                )

            # Preparar datos excluyendo campos autogenerados
            datos = tipo.model_dump(exclude={'id', 'fecha_creacion', 'fecha_actualizacion'})
            result = self.supabase.table(self.tabla).insert(datos).execute()

            if not result.data:
                raise DatabaseError("No se pudo crear el tipo de servicio (sin respuesta de BD)")

            return TipoServicio(**result.data[0])

        except DuplicateError:
            raise
        except Exception as e:
            logger.error(f"Error creando tipo de servicio: {e}")
            raise DatabaseError(f"Error de base de datos al crear tipo: {str(e)}")

    async def actualizar(self, tipo: TipoServicio) -> TipoServicio:
        """
        Actualiza un tipo de servicio existente.

        Args:
            tipo: TipoServicio con datos actualizados

        Returns:
            TipoServicio actualizado

        Raises:
            NotFoundError: Si el tipo no existe
            DuplicateError: Si la nueva clave ya existe en otro tipo
            DatabaseError: Si hay error de conexión/infraestructura
        """
        try:
            # Verificar que existe
            await self.obtener_por_id(tipo.id)

            # Verificar clave duplicada (excluyendo el registro actual)
            if await self.existe_clave(tipo.clave, excluir_id=tipo.id):
                raise DuplicateError(
                    f"La clave '{tipo.clave}' ya existe en otro tipo",
                    field="clave",
                    value=tipo.clave
                )

            # Preparar datos
            datos = tipo.model_dump(exclude={'id', 'fecha_creacion', 'fecha_actualizacion'})
            result = self.supabase.table(self.tabla).update(datos).eq('id', tipo.id).execute()

            if not result.data:
                raise NotFoundError(f"Tipo de servicio con ID {tipo.id} no encontrado")

            return TipoServicio(**result.data[0])

        except (NotFoundError, DuplicateError):
            raise
        except Exception as e:
            logger.error(f"Error actualizando tipo de servicio {tipo.id}: {e}")
            raise DatabaseError(f"Error de base de datos al actualizar tipo: {str(e)}")

    async def eliminar(self, tipo_id: int) -> bool:
        """
        Elimina (soft delete) un tipo de servicio estableciendo estatus INACTIVO.

        Args:
            tipo_id: ID del tipo a eliminar

        Returns:
            True si se eliminó correctamente

        Raises:
            NotFoundError: Si el tipo no existe
            DatabaseError: Si hay error de conexión/infraestructura
        """
        try:
            # Verificar que existe
            await self.obtener_por_id(tipo_id)

            result = self.supabase.table(self.tabla).update(
                {'estatus': 'INACTIVO'}
            ).eq('id', tipo_id).execute()

            return bool(result.data)

        except NotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error eliminando tipo de servicio {tipo_id}: {e}")
            raise DatabaseError(f"Error de base de datos al eliminar tipo: {str(e)}")

    async def existe_clave(self, clave: str, excluir_id: Optional[int] = None) -> bool:
        """
        Verifica si existe una clave en la base de datos.

        Args:
            clave: Clave a verificar
            excluir_id: ID a excluir de la búsqueda (para actualizaciones)

        Returns:
            True si la clave existe, False si no

        Raises:
            DatabaseError: Si hay error de conexión/infraestructura
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

    async def buscar_por_texto(self, termino: str, limite: int = 10) -> List[TipoServicio]:
        """
        Busca tipos de servicio por nombre o clave.

        Args:
            termino: Término de búsqueda
            limite: Número máximo de resultados (default 10)

        Returns:
            Lista de tipos que coinciden (vacía si no hay resultados)

        Raises:
            DatabaseError: Si hay error de conexión/infraestructura
        """
        try:
            termino_upper = termino.upper()

            result = self.supabase.table(self.tabla)\
                .select('*')\
                .eq('estatus', 'ACTIVO')\
                .or_(
                    f"nombre.ilike.%{termino_upper}%,"
                    f"clave.ilike.%{termino_upper}%"
                )\
                .limit(limite)\
                .execute()

            return [TipoServicio(**data) for data in result.data]

        except Exception as e:
            logger.error(f"Error buscando tipos con término '{termino}': {e}")
            raise DatabaseError(f"Error de base de datos al buscar tipos: {str(e)}")

    async def contar(self, incluir_inactivas: bool = False) -> int:
        """
        Cuenta el total de tipos de servicio.

        Args:
            incluir_inactivas: Si True, cuenta también los inactivos

        Returns:
            Número total de tipos

        Raises:
            DatabaseError: Si hay error de conexión/infraestructura
        """
        try:
            query = self.supabase.table(self.tabla).select('id', count='exact')

            if not incluir_inactivas:
                query = query.eq('estatus', 'ACTIVO')

            result = query.execute()
            return result.count if result.count else 0

        except Exception as e:
            logger.error(f"Error contando tipos de servicio: {e}")
            raise DatabaseError(f"Error de base de datos al contar tipos: {str(e)}")
