"""
Repositorio de Áreas de Servicio - Interface y implementación para Supabase.

Patrón de manejo de errores:
- NotFoundError: Cuando no se encuentra un recurso
- DuplicateError: Cuando se viola unicidad (ej: clave duplicada)
- DatabaseError: Errores de conexión o infraestructura
- Propagar otras excepciones hacia arriba
"""
from abc import ABC, abstractmethod
from typing import List, Optional
import logging

from app.entities import AreaServicio
from app.core.exceptions import NotFoundError, DuplicateError, DatabaseError

logger = logging.getLogger(__name__)


class IAreaServicioRepository(ABC):
    """Interface del repositorio de áreas de servicio - define el contrato"""

    @abstractmethod
    async def obtener_por_id(self, area_id: int) -> AreaServicio:
        """Obtiene un área de servicio por su ID"""
        pass

    @abstractmethod
    async def obtener_por_clave(self, clave: str) -> Optional[AreaServicio]:
        """Obtiene un área de servicio por su clave"""
        pass

    @abstractmethod
    async def obtener_todas(
        self,
        incluir_inactivas: bool = False,
        limite: Optional[int] = None,
        offset: int = 0
    ) -> List[AreaServicio]:
        """
        Obtiene todas las áreas de servicio con soporte de paginación.

        Args:
            incluir_inactivas: Si True, incluye áreas inactivas
            limite: Número máximo de resultados (None = sin límite)
            offset: Número de registros a saltar (para paginación)
        """
        pass

    @abstractmethod
    async def crear(self, area: AreaServicio) -> AreaServicio:
        """Crea una nueva área de servicio"""
        pass

    @abstractmethod
    async def actualizar(self, area: AreaServicio) -> AreaServicio:
        """Actualiza un área de servicio existente"""
        pass

    @abstractmethod
    async def eliminar(self, area_id: int) -> bool:
        """Elimina (inactiva) un área de servicio"""
        pass

    @abstractmethod
    async def existe_clave(self, clave: str, excluir_id: Optional[int] = None) -> bool:
        """Verifica si existe una clave en la base de datos"""
        pass

    @abstractmethod
    async def buscar_por_texto(self, termino: str, limite: int = 10) -> List[AreaServicio]:
        """Busca áreas por nombre o clave"""
        pass

    @abstractmethod
    async def contar(self, incluir_inactivas: bool = False) -> int:
        """Cuenta el total de áreas de servicio"""
        pass


class SupabaseAreaServicioRepository(IAreaServicioRepository):
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
        self.tabla = 'areas_servicio'

    async def obtener_por_id(self, area_id: int) -> AreaServicio:
        """
        Obtiene un área de servicio por su ID.

        Args:
            area_id: ID del área a buscar

        Returns:
            AreaServicio encontrada

        Raises:
            NotFoundError: Si el área no existe
            DatabaseError: Si hay error de conexión/infraestructura
        """
        try:
            result = self.supabase.table(self.tabla).select('*').eq('id', area_id).execute()
            
            if not result.data:
                raise NotFoundError(f"Área de servicio con ID {area_id} no encontrada")
            
            return AreaServicio(**result.data[0])
        
        except NotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error obteniendo área de servicio {area_id}: {e}")
            raise DatabaseError(f"Error de base de datos al obtener área: {str(e)}")

    async def obtener_por_clave(self, clave: str) -> Optional[AreaServicio]:
        """
        Obtiene un área de servicio por su clave.

        Args:
            clave: Clave del área a buscar (ej: "JAR", "LIM")

        Returns:
            AreaServicio si existe, None si no existe

        Raises:
            DatabaseError: Si hay error de conexión/infraestructura
        """
        try:
            result = self.supabase.table(self.tabla).select('*').eq('clave', clave.upper()).execute()
            
            if not result.data:
                return None
            
            return AreaServicio(**result.data[0])
        
        except Exception as e:
            logger.error(f"Error obteniendo área por clave {clave}: {e}")
            raise DatabaseError(f"Error de base de datos al obtener área: {str(e)}")

    async def obtener_todas(
        self,
        incluir_inactivas: bool = False,
        limite: Optional[int] = None,
        offset: int = 0
    ) -> List[AreaServicio]:
        """
        Obtiene todas las áreas de servicio con soporte de paginación.

        Args:
            incluir_inactivas: Si True, incluye áreas inactivas
            limite: Número máximo de resultados (None = 100 por defecto)
            offset: Número de registros a saltar (para paginación)

        Returns:
            Lista de áreas de servicio (vacía si no hay resultados)

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
            return [AreaServicio(**data) for data in result.data]
        
        except Exception as e:
            logger.error(f"Error obteniendo áreas de servicio: {e}")
            raise DatabaseError(f"Error de base de datos al obtener áreas: {str(e)}")

    async def crear(self, area: AreaServicio) -> AreaServicio:
        """
        Crea una nueva área de servicio.

        Args:
            area: AreaServicio a crear

        Returns:
            AreaServicio creada con ID asignado

        Raises:
            DuplicateError: Si la clave ya existe
            DatabaseError: Si hay error de conexión/infraestructura
        """
        try:
            # Verificar clave duplicada
            if await self.existe_clave(area.clave):
                raise DuplicateError(
                    f"La clave '{area.clave}' ya existe",
                    field="clave",
                    value=area.clave
                )

            # Preparar datos excluyendo campos autogenerados
            datos = area.model_dump(exclude={'id', 'fecha_creacion', 'fecha_actualizacion'})
            result = self.supabase.table(self.tabla).insert(datos).execute()

            if not result.data:
                raise DatabaseError("No se pudo crear el área de servicio (sin respuesta de BD)")

            return AreaServicio(**result.data[0])
        
        except DuplicateError:
            raise
        except Exception as e:
            logger.error(f"Error creando área de servicio: {e}")
            raise DatabaseError(f"Error de base de datos al crear área: {str(e)}")

    async def actualizar(self, area: AreaServicio) -> AreaServicio:
        """
        Actualiza un área de servicio existente.

        Args:
            area: AreaServicio con datos actualizados

        Returns:
            AreaServicio actualizada

        Raises:
            NotFoundError: Si el área no existe
            DuplicateError: Si la nueva clave ya existe en otra área
            DatabaseError: Si hay error de conexión/infraestructura
        """
        try:
            # Verificar que existe
            await self.obtener_por_id(area.id)

            # Verificar clave duplicada (excluyendo el registro actual)
            if await self.existe_clave(area.clave, excluir_id=area.id):
                raise DuplicateError(
                    f"La clave '{area.clave}' ya existe en otra área",
                    field="clave",
                    value=area.clave
                )

            # Preparar datos
            datos = area.model_dump(exclude={'id', 'fecha_creacion', 'fecha_actualizacion'})
            result = self.supabase.table(self.tabla).update(datos).eq('id', area.id).execute()

            if not result.data:
                raise NotFoundError(f"Área de servicio con ID {area.id} no encontrada")

            return AreaServicio(**result.data[0])
        
        except (NotFoundError, DuplicateError):
            raise
        except Exception as e:
            logger.error(f"Error actualizando área de servicio {area.id}: {e}")
            raise DatabaseError(f"Error de base de datos al actualizar área: {str(e)}")

    async def eliminar(self, area_id: int) -> bool:
        """
        Elimina (soft delete) un área de servicio estableciendo estatus INACTIVO.

        Args:
            area_id: ID del área a eliminar

        Returns:
            True si se eliminó correctamente

        Raises:
            NotFoundError: Si el área no existe
            DatabaseError: Si hay error de conexión/infraestructura
        """
        try:
            # Verificar que existe
            await self.obtener_por_id(area_id)

            result = self.supabase.table(self.tabla).update(
                {'estatus': 'INACTIVO'}
            ).eq('id', area_id).execute()

            return bool(result.data)
        
        except NotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error eliminando área de servicio {area_id}: {e}")
            raise DatabaseError(f"Error de base de datos al eliminar área: {str(e)}")

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

    async def buscar_por_texto(self, termino: str, limite: int = 10) -> List[AreaServicio]:
        """
        Busca áreas de servicio por nombre o clave.

        Args:
            termino: Término de búsqueda
            limite: Número máximo de resultados (default 10)

        Returns:
            Lista de áreas que coinciden (vacía si no hay resultados)

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

            return [AreaServicio(**data) for data in result.data]
        
        except Exception as e:
            logger.error(f"Error buscando áreas con término '{termino}': {e}")
            raise DatabaseError(f"Error de base de datos al buscar áreas: {str(e)}")

    async def contar(self, incluir_inactivas: bool = False) -> int:
        """
        Cuenta el total de áreas de servicio.

        Args:
            incluir_inactivas: Si True, cuenta también las inactivas

        Returns:
            Número total de áreas

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
            logger.error(f"Error contando áreas de servicio: {e}")
            raise DatabaseError(f"Error de base de datos al contar áreas: {str(e)}")