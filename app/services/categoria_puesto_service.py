"""
Servicio de aplicacion para gestion de Categorias de Puesto.

Patron de manejo de errores:
- NotFoundError: Cuando no se encuentra un recurso
- DuplicateError: Cuando se viola unicidad (clave duplicada en el mismo tipo)
- DatabaseError: Errores de conexion o infraestructura
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
from app.repositories import SupabaseCategoriaPuestoRepository
from app.core.exceptions import DuplicateError, BusinessRuleError

logger = logging.getLogger(__name__)


class CategoriaPuestoService:
    """
    Servicio de aplicacion para categorias de puesto.
    Orquesta las operaciones de negocio delegando acceso a datos al repositorio.
    """

    def __init__(self):
        self.repository = SupabaseCategoriaPuestoRepository()

    # ==========================================
    # OPERACIONES DE LECTURA
    # ==========================================

    async def obtener_por_id(self, categoria_id: int) -> CategoriaPuesto:
        """
        Obtiene una categoria por su ID.

        Raises:
            NotFoundError: Si la categoria no existe
            DatabaseError: Si hay error de BD
        """
        return await self.repository.obtener_por_id(categoria_id)

    async def obtener_por_tipo_servicio(
        self,
        tipo_servicio_id: int,
        incluir_inactivas: bool = False
    ) -> List[CategoriaPuesto]:
        """
        Obtiene todas las categorias de un tipo de servicio.

        Raises:
            DatabaseError: Si hay error de BD
        """
        return await self.repository.obtener_por_tipo_servicio(tipo_servicio_id, incluir_inactivas)

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
        return await self.repository.obtener_todas(incluir_inactivas, limite, offset)

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
        if not termino or len(termino.strip()) < 2:
            return []

        return await self.repository.buscar(termino, tipo_servicio_id, limite)

    # ==========================================
    # OPERACIONES DE ESCRITURA
    # ==========================================

    async def crear(self, categoria_create: CategoriaPuestoCreate) -> CategoriaPuesto:
        """
        Crea una nueva categoria de puesto.

        Raises:
            DuplicateError: Si la clave ya existe en el tipo de servicio
            DatabaseError: Si hay error de BD
        """
        categoria = CategoriaPuesto(**categoria_create.model_dump())

        logger.info(
            f"Creando categoria: {categoria.clave} - {categoria.nombre} "
            f"(tipo_servicio_id={categoria.tipo_servicio_id})"
        )

        return await self.repository.crear(categoria)

    async def actualizar(
        self,
        categoria_id: int,
        categoria_update: CategoriaPuestoUpdate
    ) -> CategoriaPuesto:
        """
        Actualiza una categoria existente.

        Raises:
            NotFoundError: Si la categoria no existe
            DuplicateError: Si la nueva clave ya existe en el tipo de servicio
            DatabaseError: Si hay error de BD
        """
        categoria_actual = await self.repository.obtener_por_id(categoria_id)

        datos_actualizados = categoria_update.model_dump(exclude_unset=True)

        for campo, valor in datos_actualizados.items():
            if valor is not None:
                setattr(categoria_actual, campo, valor)

        logger.info(f"Actualizando categoria ID {categoria_id}")

        # Verificar clave duplicada (excluyendo registro actual)
        if await self.repository.existe_clave_en_tipo(
            categoria_actual.tipo_servicio_id,
            categoria_actual.clave,
            excluir_id=categoria_actual.id
        ):
            raise DuplicateError(
                f"La clave '{categoria_actual.clave}' ya existe en este tipo de servicio",
                field="clave",
                value=categoria_actual.clave
            )

        return await self.repository.actualizar(categoria_actual)

    async def eliminar(self, categoria_id: int) -> bool:
        """
        Elimina (desactiva) una categoria.

        Raises:
            NotFoundError: Si la categoria no existe
            BusinessRuleError: Si tiene empleados asociados (futuro)
            DatabaseError: Si hay error de BD
        """
        categoria = await self.repository.obtener_por_id(categoria_id)

        await self._validar_puede_eliminar(categoria)

        logger.info(f"Eliminando (desactivando) categoria: {categoria.clave}")

        return await self.repository.eliminar(categoria_id)

    async def activar(self, categoria_id: int) -> CategoriaPuesto:
        """
        Activa una categoria que estaba inactiva.

        Raises:
            NotFoundError: Si la categoria no existe
            BusinessRuleError: Si ya esta activa
            DatabaseError: Si hay error de BD
        """
        categoria = await self.repository.obtener_por_id(categoria_id)

        if categoria.estatus == Estatus.ACTIVO:
            raise BusinessRuleError("La categoria ya esta activa")

        categoria.estatus = Estatus.ACTIVO

        logger.info(f"Activando categoria: {categoria.clave}")

        return await self.repository.actualizar(categoria)

    # ==========================================
    # VALIDACIONES DE NEGOCIO (privadas)
    # ==========================================

    async def _validar_puede_eliminar(self, categoria: CategoriaPuesto) -> None:
        """
        Valida si una categoria puede ser eliminada.
        """
        # TODO: Cuando exista el modulo de empleados:
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
        return await self.repository.existe_clave_en_tipo(tipo_servicio_id, clave, excluir_id)


# ==========================================
# SINGLETON
# ==========================================

categoria_puesto_service = CategoriaPuestoService()
