"""
Servicio de aplicación para gestión de Áreas de Servicio.

Patrón de manejo de errores:
- Las excepciones del repository se propagan (NotFoundError, DuplicateError, DatabaseError)
- El servicio agrega validaciones de reglas de negocio (BusinessRuleError)
- Logging de errores solo para debugging, NO para control de flujo
"""
import logging
from typing import List, Optional

from app.entities import (
    AreaServicio,
    AreaServicioCreate,
    AreaServicioUpdate,
    EstatusAreaServicio,
)
from app.repositories import SupabaseAreaServicioRepository
from app.core.exceptions import NotFoundError, DuplicateError, DatabaseError, BusinessRuleError

logger = logging.getLogger(__name__)


class AreaServicioService:
    """
    Servicio de aplicación para áreas de servicio.
    Orquesta las operaciones de negocio.
    """

    def __init__(self, repository=None):
        """
        Inicializa el servicio con un repository.

        Args:
            repository: Implementación del repository. Si es None, usa Supabase por defecto.
        """
        if repository is None:
            repository = SupabaseAreaServicioRepository()
        self.repository = repository

    # ==========================================
    # OPERACIONES DE LECTURA
    # ==========================================

    async def obtener_por_id(self, area_id: int) -> AreaServicio:
        """
        Obtiene un área de servicio por su ID.

        Args:
            area_id: ID del área

        Returns:
            AreaServicio encontrada

        Raises:
            NotFoundError: Si el área no existe
            DatabaseError: Si hay error de BD
        """
        return await self.repository.obtener_por_id(area_id)

    async def obtener_por_clave(self, clave: str) -> Optional[AreaServicio]:
        """
        Obtiene un área de servicio por su clave.

        Args:
            clave: Clave del área (ej: "JAR", "LIM")

        Returns:
            AreaServicio si existe, None si no

        Raises:
            DatabaseError: Si hay error de BD
        """
        return await self.repository.obtener_por_clave(clave.upper())

    async def obtener_todas(
        self,
        incluir_inactivas: bool = False,
        limite: Optional[int] = None,
        offset: int = 0
    ) -> List[AreaServicio]:
        """
        Obtiene todas las áreas de servicio con paginación.

        Args:
            incluir_inactivas: Si True, incluye áreas inactivas
            limite: Número máximo de resultados (None = 100 por defecto)
            offset: Número de registros a saltar

        Returns:
            Lista de áreas (vacía si no hay resultados)

        Raises:
            DatabaseError: Si hay error de BD
        """
        return await self.repository.obtener_todas(incluir_inactivas, limite, offset)

    async def obtener_activas(self) -> List[AreaServicio]:
        """
        Obtiene todas las áreas de servicio activas.
        Método de conveniencia para selects/dropdowns.

        Returns:
            Lista de áreas activas ordenadas por nombre

        Raises:
            DatabaseError: Si hay error de BD
        """
        return await self.repository.obtener_todas(incluir_inactivas=False)

    async def buscar(self, termino: str, limite: int = 10) -> List[AreaServicio]:
        """
        Busca áreas por nombre o clave.

        Args:
            termino: Término de búsqueda (mínimo 1 caracter)
            limite: Número máximo de resultados

        Returns:
            Lista de áreas que coinciden

        Raises:
            DatabaseError: Si hay error de BD
        """
        if not termino or len(termino.strip()) < 1:
            return []
        
        return await self.repository.buscar_por_texto(termino.strip(), limite)

    async def contar(self, incluir_inactivas: bool = False) -> int:
        """
        Cuenta el total de áreas de servicio.

        Args:
            incluir_inactivas: Si True, cuenta también las inactivas

        Returns:
            Número total de áreas

        Raises:
            DatabaseError: Si hay error de BD
        """
        return await self.repository.contar(incluir_inactivas)

    # ==========================================
    # OPERACIONES DE ESCRITURA
    # ==========================================

    async def crear(self, area_create: AreaServicioCreate) -> AreaServicio:
        """
        Crea una nueva área de servicio.

        Args:
            area_create: Datos del área a crear

        Returns:
            AreaServicio creada con ID asignado

        Raises:
            DuplicateError: Si la clave ya existe
            DatabaseError: Si hay error de BD
        """
        # Convertir AreaServicioCreate a AreaServicio
        area = AreaServicio(**area_create.model_dump())

        logger.info(f"Creando área de servicio: {area.clave} - {area.nombre}")

        # Delegar al repository (propaga DuplicateError o DatabaseError)
        return await self.repository.crear(area)

    async def actualizar(self, area_id: int, area_update: AreaServicioUpdate) -> AreaServicio:
        """
        Actualiza un área de servicio existente.

        Args:
            area_id: ID del área a actualizar
            area_update: Datos a actualizar (solo campos con valor)

        Returns:
            AreaServicio actualizada

        Raises:
            NotFoundError: Si el área no existe
            DuplicateError: Si la nueva clave ya existe
            DatabaseError: Si hay error de BD
        """
        # Obtener área actual
        area_actual = await self.repository.obtener_por_id(area_id)

        # Aplicar cambios (solo campos que vienen en el update)
        datos_actualizados = area_update.model_dump(exclude_unset=True)
        
        for campo, valor in datos_actualizados.items():
            if valor is not None:
                setattr(area_actual, campo, valor)

        logger.info(f"Actualizando área de servicio ID {area_id}")

        # Delegar al repository
        return await self.repository.actualizar(area_actual)

    async def eliminar(self, area_id: int) -> bool:
        """
        Elimina (desactiva) un área de servicio.

        Reglas de negocio:
        - No se puede eliminar si tiene contratos activos asociados
        - (Se implementará cuando exista el módulo de contratos)

        Args:
            area_id: ID del área a eliminar

        Returns:
            True si se eliminó correctamente

        Raises:
            NotFoundError: Si el área no existe
            BusinessRuleError: Si tiene contratos activos
            DatabaseError: Si hay error de BD
        """
        # Obtener área para validar que existe
        area = await self.repository.obtener_por_id(area_id)

        # Validar reglas de negocio
        await self._validar_puede_eliminar(area)

        logger.info(f"Eliminando (desactivando) área de servicio: {area.clave}")

        return await self.repository.eliminar(area_id)

    async def activar(self, area_id: int) -> AreaServicio:
        """
        Activa un área de servicio que estaba inactiva.

        Args:
            area_id: ID del área a activar

        Returns:
            AreaServicio activada

        Raises:
            NotFoundError: Si el área no existe
            BusinessRuleError: Si ya está activa
            DatabaseError: Si hay error de BD
        """
        area = await self.repository.obtener_por_id(area_id)

        if area.estatus == EstatusAreaServicio.ACTIVO:
            raise BusinessRuleError("El área ya está activa")

        area.estatus = EstatusAreaServicio.ACTIVO

        logger.info(f"Activando área de servicio: {area.clave}")

        return await self.repository.actualizar(area)

    # ==========================================
    # VALIDACIONES DE NEGOCIO (privadas)
    # ==========================================

    async def _validar_puede_eliminar(self, area: AreaServicio) -> None:
        """
        Valida si un área puede ser eliminada.

        Reglas:
        - No debe tener contratos activos asociados

        Args:
            area: Área a validar

        Raises:
            BusinessRuleError: Si no cumple las reglas
        """
        # TODO: Cuando exista el módulo de contratos, descomentar:
        # from app.repositories import SupabaseContratoRepository
        # contrato_repo = SupabaseContratoRepository()
        # contratos = await contrato_repo.contar_por_area(area.id, solo_activos=True)
        # if contratos > 0:
        #     raise BusinessRuleError(
        #         f"No se puede eliminar el área '{area.nombre}' porque tiene {contratos} contrato(s) activo(s)"
        #     )
        pass

    async def existe_clave(self, clave: str, excluir_id: Optional[int] = None) -> bool:
        """
        Verifica si una clave ya existe.

        Args:
            clave: Clave a verificar
            excluir_id: ID a excluir (para actualizaciones)

        Returns:
            True si existe, False si no
        """
        return await self.repository.existe_clave(clave, excluir_id)


# ==========================================
# SINGLETON
# ==========================================

# Instancia global del servicio para uso en toda la aplicación
area_servicio_service = AreaServicioService()