"""
Base Repository - Clase base para todos los repositorios.

Centraliza:
- Manejo de errores consistente
- Logging estandarizado
- Operaciones CRUD genéricas
- Paginación y filtros comunes

Uso:
    class MiRepository(BaseRepository[MiEntidad]):
        tabla = 'mi_tabla'
        entidad_class = MiEntidad
        entidad_nombre = 'MiEntidad'
"""
import logging
from typing import TypeVar, Generic, Type, List, Optional, Any, Dict
from abc import ABC

from app.database import db_manager
from app.core.exceptions import NotFoundError, DuplicateError, DatabaseError

logger = logging.getLogger(__name__)

# Type variable para entidades
T = TypeVar('T')


class BaseRepository(Generic[T], ABC):
    """
    Clase base abstracta para repositorios.

    Proporciona operaciones CRUD genéricas con manejo de errores
    centralizado. Los repositorios concretos deben definir:
    - tabla: nombre de la tabla en Supabase
    - entidad_class: clase Pydantic de la entidad
    - entidad_nombre: nombre legible para mensajes de error
    """

    tabla: str = ""
    entidad_class: Type[T] = None
    entidad_nombre: str = "Entidad"

    def __init__(self, db=None):
        """
        Inicializa el repositorio con conexión a Supabase.

        Args:
            db: DatabaseManager opcional (usa singleton por defecto)
        """
        if db is None:
            db = db_manager
        self.supabase = db.get_client()
        self._logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    # =========================================================================
    # OPERACIONES DE LECTURA
    # =========================================================================

    async def obtener_por_id(self, id: int) -> T:
        """
        Obtiene una entidad por su ID.

        Args:
            id: ID de la entidad

        Returns:
            Instancia de la entidad

        Raises:
            NotFoundError: Si no existe
            DatabaseError: Si hay error de BD
        """
        return await self._ejecutar_query(
            f"obtener {self.entidad_nombre} por ID",
            lambda: self._query_por_id(id),
            not_found_msg=f"{self.entidad_nombre} con ID {id} no encontrado"
        )

    def _query_por_id(self, id: int) -> T:
        """Ejecuta query por ID. Override para JOINs personalizados."""
        result = self.supabase.table(self.tabla).select('*').eq('id', id).execute()
        if not result.data:
            return None
        return self.entidad_class(**result.data[0])

    async def obtener_todos(
        self,
        limite: Optional[int] = 100,
        offset: int = 0,
        orden_campo: str = 'id',
        orden_desc: bool = True,
        filtros: Optional[Dict[str, Any]] = None
    ) -> List[T]:
        """
        Obtiene todas las entidades con paginación.

        Args:
            limite: Máximo de resultados (None = 100)
            offset: Registros a saltar
            orden_campo: Campo para ordenar
            orden_desc: True para DESC, False para ASC
            filtros: Dict de {campo: valor} para filtrar

        Returns:
            Lista de entidades

        Raises:
            DatabaseError: Si hay error de BD
        """
        return await self._ejecutar_query(
            f"obtener todos {self.entidad_nombre}",
            lambda: self._query_todos(limite, offset, orden_campo, orden_desc, filtros),
            return_list=True
        )

    def _query_todos(
        self,
        limite: Optional[int],
        offset: int,
        orden_campo: str,
        orden_desc: bool,
        filtros: Optional[Dict[str, Any]]
    ) -> List[T]:
        """Ejecuta query de listado. Override para filtros personalizados."""
        query = self.supabase.table(self.tabla).select('*')

        # Aplicar filtros
        if filtros:
            for campo, valor in filtros.items():
                if valor is not None:
                    query = query.eq(campo, valor)

        # Ordenar
        query = query.order(orden_campo, desc=orden_desc)

        # Paginar
        if limite:
            query = query.range(offset, offset + limite - 1)

        result = query.execute()
        return [self.entidad_class(**data) for data in result.data]

    async def contar(self, filtros: Optional[Dict[str, Any]] = None) -> int:
        """
        Cuenta entidades con filtros opcionales.

        Args:
            filtros: Dict de {campo: valor} para filtrar

        Returns:
            Número de entidades

        Raises:
            DatabaseError: Si hay error de BD
        """
        return await self._ejecutar_query(
            f"contar {self.entidad_nombre}",
            lambda: self._query_contar(filtros),
            return_count=True
        )

    def _query_contar(self, filtros: Optional[Dict[str, Any]]) -> int:
        """Ejecuta query de conteo."""
        query = self.supabase.table(self.tabla).select('id', count='exact')

        if filtros:
            for campo, valor in filtros.items():
                if valor is not None:
                    query = query.eq(campo, valor)

        result = query.execute()
        return result.count or 0

    async def existe(self, id: int) -> bool:
        """Verifica si existe una entidad por ID."""
        try:
            result = self.supabase.table(self.tabla).select('id').eq('id', id).execute()
            return len(result.data) > 0
        except Exception:
            return False

    # =========================================================================
    # OPERACIONES DE ESCRITURA
    # =========================================================================

    async def crear(self, entidad: T) -> T:
        """
        Crea una nueva entidad.

        Args:
            entidad: Instancia de la entidad a crear

        Returns:
            Entidad creada con ID asignado

        Raises:
            DuplicateError: Si viola constraint único
            DatabaseError: Si hay error de BD
        """
        return await self._ejecutar_query(
            f"crear {self.entidad_nombre}",
            lambda: self._insertar(entidad),
            check_duplicate=True
        )

    def _insertar(self, entidad: T) -> T:
        """Ejecuta INSERT. Override para excluir campos específicos."""
        datos = entidad.model_dump(mode='json', exclude={'id', 'fecha_creacion'})
        result = self.supabase.table(self.tabla).insert(datos).execute()
        return self.entidad_class(**result.data[0])

    async def actualizar(self, id: int, datos: Dict[str, Any]) -> T:
        """
        Actualiza una entidad existente.

        Args:
            id: ID de la entidad
            datos: Dict con campos a actualizar

        Returns:
            Entidad actualizada

        Raises:
            NotFoundError: Si no existe
            DuplicateError: Si viola constraint único
            DatabaseError: Si hay error de BD
        """
        return await self._ejecutar_query(
            f"actualizar {self.entidad_nombre}",
            lambda: self._update(id, datos),
            not_found_msg=f"{self.entidad_nombre} con ID {id} no encontrado",
            check_duplicate=True
        )

    def _update(self, id: int, datos: Dict[str, Any]) -> T:
        """Ejecuta UPDATE."""
        # Excluir campos que no deben actualizarse
        datos_limpios = {k: v for k, v in datos.items()
                        if k not in ('id', 'fecha_creacion') and v is not None}

        result = self.supabase.table(self.tabla).update(datos_limpios).eq('id', id).execute()
        if not result.data:
            return None
        return self.entidad_class(**result.data[0])

    async def eliminar(self, id: int) -> bool:
        """
        Elimina una entidad (soft delete si tiene estatus, hard delete si no).

        Args:
            id: ID de la entidad

        Returns:
            True si se eliminó

        Raises:
            NotFoundError: Si no existe
            DatabaseError: Si hay error de BD
        """
        return await self._ejecutar_query(
            f"eliminar {self.entidad_nombre}",
            lambda: self._delete(id),
            not_found_msg=f"{self.entidad_nombre} con ID {id} no encontrado"
        )

    def _delete(self, id: int) -> bool:
        """Ejecuta DELETE. Override para soft delete."""
        result = self.supabase.table(self.tabla).delete().eq('id', id).execute()
        return len(result.data) > 0

    # =========================================================================
    # BÚSQUEDA
    # =========================================================================

    async def buscar_por_texto(
        self,
        texto: str,
        campos: List[str],
        limite: int = 20
    ) -> List[T]:
        """
        Busca entidades por texto en múltiples campos (ILIKE).

        Args:
            texto: Texto a buscar
            campos: Lista de campos donde buscar
            limite: Máximo de resultados

        Returns:
            Lista de entidades que coinciden

        Raises:
            DatabaseError: Si hay error de BD
        """
        if not texto or len(texto.strip()) < 2:
            return []

        return await self._ejecutar_query(
            f"buscar {self.entidad_nombre}",
            lambda: self._query_buscar(texto, campos, limite),
            return_list=True
        )

    def _query_buscar(self, texto: str, campos: List[str], limite: int) -> List[T]:
        """Ejecuta búsqueda por texto."""
        texto_limpio = texto.strip()

        # Construir OR de ilike para cada campo
        or_conditions = ",".join([f"{campo}.ilike.%{texto_limpio}%" for campo in campos])

        result = self.supabase.table(self.tabla)\
            .select('*')\
            .or_(or_conditions)\
            .limit(limite)\
            .execute()

        return [self.entidad_class(**data) for data in result.data]

    # =========================================================================
    # MANEJO DE ERRORES CENTRALIZADO
    # =========================================================================

    async def _ejecutar_query(
        self,
        operacion: str,
        query_fn,
        not_found_msg: Optional[str] = None,
        check_duplicate: bool = False,
        return_list: bool = False,
        return_count: bool = False
    ):
        """
        Ejecuta una query con manejo de errores centralizado.

        Args:
            operacion: Descripción de la operación (para logs)
            query_fn: Función que ejecuta la query
            not_found_msg: Mensaje si no encuentra resultados
            check_duplicate: True para detectar errores de unicidad
            return_list: True si espera lista (retorna [] en error)
            return_count: True si espera conteo (retorna 0 en error)

        Returns:
            Resultado de la query

        Raises:
            NotFoundError: Si not_found_msg y no hay resultados
            DuplicateError: Si check_duplicate y viola unicidad
            DatabaseError: Para otros errores de BD
        """
        try:
            result = query_fn()

            # Verificar not found
            if result is None and not_found_msg:
                raise NotFoundError(not_found_msg)

            return result

        except NotFoundError:
            raise
        except DuplicateError:
            raise
        except Exception as e:
            error_str = str(e).lower()

            # Detectar errores de unicidad
            if check_duplicate and ('unique' in error_str or 'duplicate' in error_str):
                self._logger.warning(f"Duplicado en {operacion}: {e}")
                raise DuplicateError("Ya existe un registro con esos datos")

            # Error genérico de BD
            self._logger.error(f"Error en {operacion}: {e}")

            if return_list:
                return []
            if return_count:
                return 0

            raise DatabaseError(f"Error de base de datos al {operacion}: {str(e)}")

    # =========================================================================
    # HELPERS
    # =========================================================================

    def _aplicar_filtro_estatus(self, query, incluir_inactivos: bool, estatus_activo: str = 'ACTIVO'):
        """Aplica filtro de estatus si no incluye inactivos."""
        if not incluir_inactivos:
            return query.eq('estatus', estatus_activo)
        return query

    def _aplicar_paginacion(self, query, limite: Optional[int], offset: int):
        """Aplica paginación a la query."""
        if limite:
            return query.range(offset, offset + limite - 1)
        return query

    async def existe_campo(
        self,
        campo: str,
        valor: Any,
        excluir_id: Optional[int] = None
    ) -> bool:
        """
        Verifica si ya existe un registro con cierto valor en un campo.

        Args:
            campo: Nombre del campo (ej: 'clave', 'rfc')
            valor: Valor a buscar
            excluir_id: ID a excluir de la búsqueda (para updates)

        Returns:
            True si ya existe
        """
        return await self._ejecutar_query(
            f"verificar existencia de {campo}",
            lambda: self._query_existe_campo(campo, valor, excluir_id),
        )

    def _query_existe_campo(self, campo: str, valor: Any, excluir_id: Optional[int]) -> bool:
        """Ejecuta query de existencia por campo."""
        query = self.supabase.table(self.tabla).select('id').eq(campo, valor)
        if excluir_id:
            query = query.neq('id', excluir_id)
        result = query.execute()
        return len(result.data) > 0

    async def actualizar_entidad(self, entidad: T) -> T:
        """
        Actualiza una entidad completa (alternativa a actualizar(id, datos)).

        Útil cuando el service ya tiene la entidad modificada y quiere
        persistir todos sus campos.

        Args:
            entidad: Entidad con campos actualizados (debe tener .id)

        Returns:
            Entidad actualizada desde BD
        """
        return await self._ejecutar_query(
            f"actualizar {self.entidad_nombre}",
            lambda: self._update_entidad(entidad),
            not_found_msg=f"{self.entidad_nombre} con ID {entidad.id} no encontrado",
            check_duplicate=True
        )

    def _update_entidad(self, entidad: T) -> T:
        """Ejecuta UPDATE desde entidad completa."""
        datos = entidad.model_dump(
            mode='json',
            exclude={'id', 'fecha_creacion', 'fecha_actualizacion'}
        )
        result = self.supabase.table(self.tabla).update(datos).eq('id', entidad.id).execute()
        if not result.data:
            return None
        return self.entidad_class(**result.data[0])
