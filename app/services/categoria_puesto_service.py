"""
Servicio de aplicación para gestión de Categorías de Puesto.

Accede directamente a Supabase (sin repositorio intermedio).

Patrón de manejo de errores:
- NotFoundError: Cuando no se encuentra un recurso
- DuplicateError: Cuando se viola unicidad (clave duplicada en el mismo tipo)
- DatabaseError: Errores de conexión o infraestructura
- BusinessRuleError: Violaciones de reglas de negocio
"""
import logging
from typing import List, Optional

from app.entities.categoria_puesto import (
    CategoriaPuesto,
    CategoriaPuestoCreate,
    CategoriaPuestoUpdate,
)
from app.core.enums import Estatus
from app.database import db_manager
from app.core.exceptions import NotFoundError, DuplicateError, DatabaseError, BusinessRuleError

logger = logging.getLogger(__name__)


class CategoriaPuestoService:
    """
    Servicio de aplicación para categorías de puesto.
    Orquesta las operaciones de negocio con acceso directo a Supabase.
    """

    def __init__(self):
        self.supabase = db_manager.get_client()
        self.tabla = 'categorias_puesto'

    # ==========================================
    # OPERACIONES DE LECTURA
    # ==========================================

    async def obtener_por_id(self, categoria_id: int) -> CategoriaPuesto:
        """
        Obtiene una categoría por su ID.

        Raises:
            NotFoundError: Si la categoría no existe
            DatabaseError: Si hay error de BD
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
            logger.error(f"Error obteniendo categorías: {e}")
            raise DatabaseError(f"Error de base de datos: {str(e)}")

    async def buscar(
        self,
        termino: str,
        tipo_servicio_id: Optional[int] = None,
        limite: int = 10
    ) -> List[CategoriaPuesto]:
        """
        Busca categorías por nombre o clave.

        Args:
            termino: Término de búsqueda
            tipo_servicio_id: Filtrar por tipo de servicio (opcional)
            limite: Número máximo de resultados

        Raises:
            DatabaseError: Si hay error de BD
        """
        if not termino or len(termino.strip()) < 2:
            return []

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
            logger.error(f"Error buscando categorías con término '{termino}': {e}")
            raise DatabaseError(f"Error de base de datos: {str(e)}")

    # ==========================================
    # OPERACIONES DE ESCRITURA
    # ==========================================

    async def crear(self, categoria_create: CategoriaPuestoCreate) -> CategoriaPuesto:
        """
        Crea una nueva categoría de puesto.

        Raises:
            DuplicateError: Si la clave ya existe en el tipo de servicio
            DatabaseError: Si hay error de BD
        """
        categoria = CategoriaPuesto(**categoria_create.model_dump())

        logger.info(
            f"Creando categoría: {categoria.clave} - {categoria.nombre} "
            f"(tipo_servicio_id={categoria.tipo_servicio_id})"
        )

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

        except (DuplicateError, DatabaseError):
            raise
        except Exception as e:
            logger.error(f"Error creando categoría: {e}")
            raise DatabaseError(f"Error de base de datos: {str(e)}")

    async def actualizar(
        self,
        categoria_id: int,
        categoria_update: CategoriaPuestoUpdate
    ) -> CategoriaPuesto:
        """
        Actualiza una categoría existente.

        Raises:
            NotFoundError: Si la categoría no existe
            DuplicateError: Si la nueva clave ya existe en el tipo de servicio
            DatabaseError: Si hay error de BD
        """
        categoria_actual = await self.obtener_por_id(categoria_id)

        datos_actualizados = categoria_update.model_dump(exclude_unset=True)

        for campo, valor in datos_actualizados.items():
            if valor is not None:
                setattr(categoria_actual, campo, valor)

        logger.info(f"Actualizando categoría ID {categoria_id}")

        try:
            # Verificar clave duplicada (excluyendo registro actual)
            if await self.existe_clave_en_tipo(
                categoria_actual.tipo_servicio_id,
                categoria_actual.clave,
                excluir_id=categoria_actual.id
            ):
                raise DuplicateError(
                    f"La clave '{categoria_actual.clave}' ya existe en este tipo de servicio",
                    field="clave",
                    value=categoria_actual.clave
                )

            datos = categoria_actual.model_dump(exclude={'id', 'fecha_creacion', 'fecha_actualizacion'})
            result = self.supabase.table(self.tabla).update(datos).eq('id', categoria_actual.id).execute()

            if not result.data:
                raise NotFoundError(f"Categoría con ID {categoria_actual.id} no encontrada")

            return CategoriaPuesto(**result.data[0])

        except (NotFoundError, DuplicateError, DatabaseError):
            raise
        except Exception as e:
            logger.error(f"Error actualizando categoría {categoria_id}: {e}")
            raise DatabaseError(f"Error de base de datos: {str(e)}")

    async def eliminar(self, categoria_id: int) -> bool:
        """
        Elimina (desactiva) una categoría.

        Raises:
            NotFoundError: Si la categoría no existe
            BusinessRuleError: Si tiene empleados asociados (futuro)
            DatabaseError: Si hay error de BD
        """
        categoria = await self.obtener_por_id(categoria_id)

        await self._validar_puede_eliminar(categoria)

        logger.info(f"Eliminando (desactivando) categoría: {categoria.clave}")

        try:
            result = self.supabase.table(self.tabla).update(
                {'estatus': 'INACTIVO'}
            ).eq('id', categoria_id).execute()

            return bool(result.data)

        except Exception as e:
            logger.error(f"Error eliminando categoría {categoria_id}: {e}")
            raise DatabaseError(f"Error de base de datos: {str(e)}")

    async def activar(self, categoria_id: int) -> CategoriaPuesto:
        """
        Activa una categoría que estaba inactiva.

        Raises:
            NotFoundError: Si la categoría no existe
            BusinessRuleError: Si ya está activa
            DatabaseError: Si hay error de BD
        """
        categoria = await self.obtener_por_id(categoria_id)

        if categoria.estatus == Estatus.ACTIVO:
            raise BusinessRuleError("La categoría ya está activa")

        categoria.estatus = Estatus.ACTIVO

        logger.info(f"Activando categoría: {categoria.clave}")

        try:
            datos = categoria.model_dump(exclude={'id', 'fecha_creacion', 'fecha_actualizacion'})
            result = self.supabase.table(self.tabla).update(datos).eq('id', categoria.id).execute()

            if not result.data:
                raise NotFoundError(f"Categoría con ID {categoria.id} no encontrada")

            return CategoriaPuesto(**result.data[0])

        except (NotFoundError, DatabaseError):
            raise
        except Exception as e:
            logger.error(f"Error activando categoría {categoria.id}: {e}")
            raise DatabaseError(f"Error de base de datos: {str(e)}")

    # ==========================================
    # VALIDACIONES DE NEGOCIO (privadas)
    # ==========================================

    async def _validar_puede_eliminar(self, categoria: CategoriaPuesto) -> None:
        """
        Valida si una categoría puede ser eliminada.

        Reglas:
        - No debe tener empleados activos asociados (futuro)
        """
        # TODO: Cuando exista el módulo de empleados:
        # from app.repositories import SupabaseEmpleadoRepository
        # empleado_repo = SupabaseEmpleadoRepository()
        # empleados = await empleado_repo.contar_por_categoria(categoria.id, solo_activos=True)
        # if empleados > 0:
        #     raise BusinessRuleError(
        #         f"No se puede eliminar '{categoria.nombre}' porque tiene {empleados} empleado(s)"
        #     )
        pass

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


# ==========================================
# SINGLETON
# ==========================================

categoria_puesto_service = CategoriaPuestoService()
