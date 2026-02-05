"""
Repositorio de Categorias de Puesto - Implementacion para Supabase.

Patron de manejo de errores:
- NotFoundError: Cuando no se encuentra un recurso
- DuplicateError: Cuando se viola unicidad (clave duplicada en tipo)
- DatabaseError: Errores de conexion o infraestructura
"""
import logging
from typing import List, Optional

from app.entities.categoria_puesto import CategoriaPuesto
from app.core.exceptions import NotFoundError, DuplicateError, DatabaseError

logger = logging.getLogger(__name__)


class SupabaseCategoriaPuestoRepository:
    """Implementacion del repositorio de categorias de puesto usando Supabase."""

    def __init__(self, db_manager=None):
        if db_manager is None:
            from app.database import db_manager as default_db
            db_manager = default_db

        self.supabase = db_manager.get_client()
        self.tabla = 'categorias_puesto'

    async def obtener_por_id(self, categoria_id: int) -> CategoriaPuesto:
        """
        Obtiene una categoria por su ID.

        Raises:
            NotFoundError: Si la categoria no existe
            DatabaseError: Si hay error de BD
        """
        try:
            result = self.supabase.table(self.tabla).select('*').eq('id', categoria_id).execute()

            if not result.data:
                raise NotFoundError(f"Categoria de puesto con ID {categoria_id} no encontrada")

            return CategoriaPuesto(**result.data[0])

        except NotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error obteniendo categoria {categoria_id}: {e}")
            raise DatabaseError(f"Error de base de datos: {str(e)}")

    async def obtener_por_tipo_servicio(
        self,
        tipo_servicio_id: int,
        incluir_inactivas: bool = False
    ) -> List[CategoriaPuesto]:
        """
        Obtiene todas las categorias de un tipo de servicio.

        Returns:
            Lista ordenada por 'orden' y luego por 'nombre'

        Raises:
            DatabaseError: Si hay error de BD
        """
        try:
            query = self.supabase.table(self.tabla).select('*').eq('tipo_servicio_id', tipo_servicio_id)

            if not incluir_inactivas:
                query = query.eq('estatus', 'ACTIVO')

            query = query.order('orden', desc=False).order('nombre', desc=False)

            result = query.execute()
            return [CategoriaPuesto(**data) for data in result.data]

        except Exception as e:
            logger.error(f"Error obteniendo categorias del tipo {tipo_servicio_id}: {e}")
            raise DatabaseError(f"Error de base de datos: {str(e)}")

    async def obtener_todas(
        self,
        incluir_inactivas: bool = False,
        limite: Optional[int] = None,
        offset: int = 0
    ) -> List[CategoriaPuesto]:
        """
        Obtiene todas las categorias con paginacion.

        Raises:
            DatabaseError: Si hay error de BD
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
            logger.error(f"Error obteniendo categorias: {e}")
            raise DatabaseError(f"Error de base de datos: {str(e)}")

    async def buscar(
        self,
        termino: str,
        tipo_servicio_id: Optional[int] = None,
        limite: int = 10
    ) -> List[CategoriaPuesto]:
        """
        Busca categorias por nombre o clave.

        Raises:
            DatabaseError: Si hay error de BD
        """
        try:
            termino_upper = termino.strip().upper()

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
            logger.error(f"Error buscando categorias con termino '{termino}': {e}")
            raise DatabaseError(f"Error de base de datos: {str(e)}")

    async def crear(self, categoria: CategoriaPuesto) -> CategoriaPuesto:
        """
        Crea una nueva categoria de puesto.

        Raises:
            DuplicateError: Si la clave ya existe en el tipo de servicio
            DatabaseError: Si hay error de BD
        """
        try:
            if await self.existe_clave_en_tipo(categoria.tipo_servicio_id, categoria.clave):
                raise DuplicateError(
                    f"La clave '{categoria.clave}' ya existe en este tipo de servicio",
                    field="clave",
                    value=categoria.clave
                )

            datos = categoria.model_dump(exclude={'id', 'fecha_creacion', 'fecha_actualizacion'})
            result = self.supabase.table(self.tabla).insert(datos).execute()

            if not result.data:
                raise DatabaseError("No se pudo crear la categoria")

            return CategoriaPuesto(**result.data[0])

        except (DuplicateError, DatabaseError):
            raise
        except Exception as e:
            logger.error(f"Error creando categoria: {e}")
            raise DatabaseError(f"Error de base de datos: {str(e)}")

    async def actualizar(self, categoria: CategoriaPuesto) -> CategoriaPuesto:
        """
        Actualiza una categoria existente.

        Raises:
            NotFoundError: Si la categoria no existe
            DatabaseError: Si hay error de BD
        """
        try:
            datos = categoria.model_dump(exclude={'id', 'fecha_creacion', 'fecha_actualizacion'})
            result = self.supabase.table(self.tabla).update(datos).eq('id', categoria.id).execute()

            if not result.data:
                raise NotFoundError(f"Categoria con ID {categoria.id} no encontrada")

            return CategoriaPuesto(**result.data[0])

        except NotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error actualizando categoria {categoria.id}: {e}")
            raise DatabaseError(f"Error de base de datos: {str(e)}")

    async def eliminar(self, categoria_id: int) -> bool:
        """
        Elimina (desactiva) una categoria.

        Raises:
            DatabaseError: Si hay error de BD
        """
        try:
            result = self.supabase.table(self.tabla).update(
                {'estatus': 'INACTIVO'}
            ).eq('id', categoria_id).execute()

            return bool(result.data)

        except Exception as e:
            logger.error(f"Error eliminando categoria {categoria_id}: {e}")
            raise DatabaseError(f"Error de base de datos: {str(e)}")

    async def existe_clave_en_tipo(
        self,
        tipo_servicio_id: int,
        clave: str,
        excluir_id: Optional[int] = None
    ) -> bool:
        """
        Verifica si una clave ya existe en el tipo de servicio.

        Raises:
            DatabaseError: Si hay error de BD
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
