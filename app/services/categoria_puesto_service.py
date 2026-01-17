"""
Servicio de aplicación para gestión de Categorías de Puesto.

Patrón de manejo de errores:
- Las excepciones del repository se propagan (NotFoundError, DuplicateError, DatabaseError)
- El servicio agrega validaciones de reglas de negocio (BusinessRuleError)
"""
import logging
from typing import List, Optional

from app.entities.categoria_puesto import (
    CategoriaPuesto,
    CategoriaPuestoCreate,
    CategoriaPuestoUpdate,
)
from app.core.enums import Estatus
from app.repositories.categoria_puesto_repository import SupabaseCategoriaPuestoRepository
from app.core.exceptions import BusinessRuleError

logger = logging.getLogger(__name__)


class CategoriaPuestoService:
    """
    Servicio de aplicación para categorías de puesto.
    Orquesta las operaciones de negocio.
    """

    def __init__(self, repository=None):
        if repository is None:
            repository = SupabaseCategoriaPuestoRepository()
        self.repository = repository

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
        return await self.repository.obtener_por_id(categoria_id)

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
        return await self.repository.obtener_por_tipo_servicio(
            tipo_servicio_id,
            incluir_inactivas
        )

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
        return await self.repository.obtener_todas(incluir_inactivas, limite, offset)

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
        if not termino or len(termino.strip()) < 1:
            return []

        return await self.repository.buscar_por_texto(
            termino.strip(),
            tipo_servicio_id,
            limite
        )

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

        return await self.repository.crear(categoria)

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
        categoria_actual = await self.repository.obtener_por_id(categoria_id)

        datos_actualizados = categoria_update.model_dump(exclude_unset=True)

        for campo, valor in datos_actualizados.items():
            if valor is not None:
                setattr(categoria_actual, campo, valor)

        logger.info(f"Actualizando categoría ID {categoria_id}")

        return await self.repository.actualizar(categoria_actual)

    async def eliminar(self, categoria_id: int) -> bool:
        """
        Elimina (desactiva) una categoría.

        Raises:
            NotFoundError: Si la categoría no existe
            BusinessRuleError: Si tiene empleados asociados (futuro)
            DatabaseError: Si hay error de BD
        """
        categoria = await self.repository.obtener_por_id(categoria_id)

        await self._validar_puede_eliminar(categoria)

        logger.info(f"Eliminando (desactivando) categoría: {categoria.clave}")

        return await self.repository.eliminar(categoria_id)

    async def activar(self, categoria_id: int) -> CategoriaPuesto:
        """
        Activa una categoría que estaba inactiva.

        Raises:
            NotFoundError: Si la categoría no existe
            BusinessRuleError: Si ya está activa
            DatabaseError: Si hay error de BD
        """
        categoria = await self.repository.obtener_por_id(categoria_id)

        if categoria.estatus == Estatus.ACTIVO:
            raise BusinessRuleError("La categoría ya está activa")

        categoria.estatus = Estatus.ACTIVO

        logger.info(f"Activando categoría: {categoria.clave}")

        return await self.repository.actualizar(categoria)

    async def cambiar_orden(self, categoria_id: int, nuevo_orden: int) -> CategoriaPuesto:
        """
        Cambia el orden de visualización de una categoría.

        Raises:
            NotFoundError: Si la categoría no existe
            DatabaseError: Si hay error de BD
        """
        categoria = await self.repository.obtener_por_id(categoria_id)
        categoria.orden = nuevo_orden

        logger.info(f"Cambiando orden de categoría {categoria.clave} a {nuevo_orden}")

        return await self.repository.actualizar(categoria)

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
        """
        return await self.repository.existe_clave_en_tipo(
            tipo_servicio_id,
            clave,
            excluir_id
        )


# ==========================================
# SINGLETON
# ==========================================

categoria_puesto_service = CategoriaPuestoService()
