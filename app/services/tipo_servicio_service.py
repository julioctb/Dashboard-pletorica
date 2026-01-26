"""
Servicio de aplicación para gestión de Tipos de Servicio.

Patrón de manejo de errores:
- Las excepciones del repository se propagan (NotFoundError, DuplicateError, DatabaseError)
- El servicio agrega validaciones de reglas de negocio (BusinessRuleError)
- Logging de errores solo para debugging, NO para control de flujo
"""
import logging
from typing import List, Optional

from app.entities import (
    TipoServicio,
    TipoServicioCreate,
    TipoServicioUpdate,
)
from app.core.enums import Estatus
from app.repositories import SupabaseTipoServicioRepository
from app.core.exceptions import NotFoundError, DuplicateError, DatabaseError, BusinessRuleError

logger = logging.getLogger(__name__)


class TipoServicioService:
    """
    Servicio de aplicación para tipos de servicio.
    Orquesta las operaciones de negocio.
    """

    def __init__(self, repository=None):
        """
        Inicializa el servicio con un repository.

        Args:
            repository: Implementación del repository. Si es None, usa Supabase por defecto.
        """
        if repository is None:
            repository = SupabaseTipoServicioRepository()
        self.repository = repository

    # ==========================================
    # OPERACIONES DE LECTURA
    # ==========================================

    async def obtener_por_id(self, tipo_id: int) -> TipoServicio:
        """
        Obtiene un tipo de servicio por su ID.

        Args:
            tipo_id: ID del tipo

        Returns:
            TipoServicio encontrado

        Raises:
            NotFoundError: Si el tipo no existe
            DatabaseError: Si hay error de BD
        """
        return await self.repository.obtener_por_id(tipo_id)

    async def obtener_por_clave(self, clave: str) -> Optional[TipoServicio]:
        """
        Obtiene un tipo de servicio por su clave.

        Args:
            clave: Clave del tipo (ej: "JAR", "LIM")

        Returns:
            TipoServicio si existe, None si no

        Raises:
            DatabaseError: Si hay error de BD
        """
        return await self.repository.obtener_por_clave(clave.upper())

    async def obtener_todas(
        self,
        incluir_inactivas: bool = False,
        limite: Optional[int] = None,
        offset: int = 0
    ) -> List[TipoServicio]:
        """
        Obtiene todos los tipos de servicio con paginación.

        Args:
            incluir_inactivas: Si True, incluye tipos inactivos
            limite: Número máximo de resultados (None = 100 por defecto)
            offset: Número de registros a saltar

        Returns:
            Lista de tipos (vacía si no hay resultados)

        Raises:
            DatabaseError: Si hay error de BD
        """
        return await self.repository.obtener_todas(incluir_inactivas, limite, offset)

    async def obtener_activas(self) -> List[TipoServicio]:
        """
        Obtiene todos los tipos de servicio activos.
        Método de conveniencia para selects/dropdowns.

        Returns:
            Lista de tipos activos ordenados por nombre

        Raises:
            DatabaseError: Si hay error de BD
        """
        return await self.repository.obtener_todas(incluir_inactivas=False)

    async def buscar(self, termino: str, limite: int = 10) -> List[TipoServicio]:
        """
        Busca tipos por nombre o clave.

        Args:
            termino: Término de búsqueda (mínimo 1 caracter)
            limite: Número máximo de resultados

        Returns:
            Lista de tipos que coinciden

        Raises:
            DatabaseError: Si hay error de BD
        """
        if not termino or len(termino.strip()) < 2:
            return []

        return await self.repository.buscar_por_texto(termino.strip(), limite)

    async def contar(self, incluir_inactivas: bool = False) -> int:
        """
        Cuenta el total de tipos de servicio.

        Args:
            incluir_inactivas: Si True, cuenta también los inactivos

        Returns:
            Número total de tipos

        Raises:
            DatabaseError: Si hay error de BD
        """
        return await self.repository.contar(incluir_inactivas)

    # ==========================================
    # OPERACIONES DE ESCRITURA
    # ==========================================

    async def crear(self, tipo_create: TipoServicioCreate) -> TipoServicio:
        """
        Crea un nuevo tipo de servicio.

        Args:
            tipo_create: Datos del tipo a crear

        Returns:
            TipoServicio creado con ID asignado

        Raises:
            DuplicateError: Si la clave ya existe
            DatabaseError: Si hay error de BD
        """
        # Convertir TipoServicioCreate a TipoServicio
        tipo = TipoServicio(**tipo_create.model_dump())

        logger.info(f"Creando tipo de servicio: {tipo.clave} - {tipo.nombre}")

        # Delegar al repository (propaga DuplicateError o DatabaseError)
        return await self.repository.crear(tipo)

    async def actualizar(self, tipo_id: int, tipo_update: TipoServicioUpdate) -> TipoServicio:
        """
        Actualiza un tipo de servicio existente.

        Args:
            tipo_id: ID del tipo a actualizar
            tipo_update: Datos a actualizar (solo campos con valor)

        Returns:
            TipoServicio actualizado

        Raises:
            NotFoundError: Si el tipo no existe
            DuplicateError: Si la nueva clave ya existe
            DatabaseError: Si hay error de BD
        """
        # Obtener tipo actual
        tipo_actual = await self.repository.obtener_por_id(tipo_id)

        # Aplicar cambios (solo campos que vienen en el update)
        datos_actualizados = tipo_update.model_dump(exclude_unset=True)

        for campo, valor in datos_actualizados.items():
            if valor is not None:
                setattr(tipo_actual, campo, valor)

        logger.info(f"Actualizando tipo de servicio ID {tipo_id}")

        # Delegar al repository
        return await self.repository.actualizar(tipo_actual)

    async def eliminar(self, tipo_id: int) -> bool:
        """
        Elimina (desactiva) un tipo de servicio.

        Reglas de negocio:
        - No se puede eliminar si tiene contratos activos asociados
        - (Se implementará cuando exista el módulo de contratos)

        Args:
            tipo_id: ID del tipo a eliminar

        Returns:
            True si se eliminó correctamente

        Raises:
            NotFoundError: Si el tipo no existe
            BusinessRuleError: Si tiene contratos activos
            DatabaseError: Si hay error de BD
        """
        # Obtener tipo para validar que existe
        tipo = await self.repository.obtener_por_id(tipo_id)

        # Validar reglas de negocio
        await self._validar_puede_eliminar(tipo)

        logger.info(f"Eliminando (desactivando) tipo de servicio: {tipo.clave}")

        return await self.repository.eliminar(tipo_id)

    async def activar(self, tipo_id: int) -> TipoServicio:
        """
        Activa un tipo de servicio que estaba inactivo.

        Args:
            tipo_id: ID del tipo a activar

        Returns:
            TipoServicio activado

        Raises:
            NotFoundError: Si el tipo no existe
            BusinessRuleError: Si ya está activo
            DatabaseError: Si hay error de BD
        """
        tipo = await self.repository.obtener_por_id(tipo_id)

        if tipo.estatus == Estatus.ACTIVO:
            raise BusinessRuleError("El tipo ya está activo")

        tipo.estatus = Estatus.ACTIVO

        logger.info(f"Activando tipo de servicio: {tipo.clave}")

        return await self.repository.actualizar(tipo)

    # ==========================================
    # VALIDACIONES DE NEGOCIO (privadas)
    # ==========================================

    async def _validar_puede_eliminar(self, tipo: TipoServicio) -> None:
        """
        Valida si un tipo puede ser eliminado.

        Reglas:
        - No debe tener contratos activos asociados

        Args:
            tipo: Tipo a validar

        Raises:
            BusinessRuleError: Si no cumple las reglas
        """
        # TODO: Cuando exista el módulo de contratos, descomentar:
        # from app.repositories import SupabaseContratoRepository
        # contrato_repo = SupabaseContratoRepository()
        # contratos = await contrato_repo.contar_por_tipo(tipo.id, solo_activos=True)
        # if contratos > 0:
        #     raise BusinessRuleError(
        #         f"No se puede eliminar el tipo '{tipo.nombre}' porque tiene {contratos} contrato(s) activo(s)"
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
tipo_servicio_service = TipoServicioService()
