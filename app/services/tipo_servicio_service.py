"""
Servicio de aplicacion para gestion de Tipos de Servicio.

Patron de manejo de errores:
- NotFoundError: Cuando no se encuentra un recurso
- DuplicateError: Cuando se viola unicidad (ej: clave duplicada)
- DatabaseError: Errores de conexion o infraestructura
- BusinessRuleError: Violaciones de reglas de negocio
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
from app.core.exceptions import BusinessRuleError

logger = logging.getLogger(__name__)


class TipoServicioService:
    """
    Servicio de aplicacion para tipos de servicio.
    Orquesta las operaciones de negocio delegando acceso a datos al repositorio.
    """

    def __init__(self):
        self.repository = SupabaseTipoServicioRepository()

    # ==========================================
    # OPERACIONES DE LECTURA
    # ==========================================

    async def obtener_por_id(self, tipo_id: int) -> TipoServicio:
        """
        Obtiene un tipo de servicio por su ID.

        Raises:
            NotFoundError: Si el tipo no existe
            DatabaseError: Si hay error de BD
        """
        return await self.repository.obtener_por_id(tipo_id)

    async def obtener_por_clave(self, clave: str) -> Optional[TipoServicio]:
        """
        Obtiene un tipo de servicio por su clave.

        Raises:
            DatabaseError: Si hay error de BD
        """
        return await self.repository.obtener_por_clave(clave)

    async def obtener_todas(
        self,
        incluir_inactivas: bool = False,
        limite: Optional[int] = None,
        offset: int = 0
    ) -> List[TipoServicio]:
        """
        Obtiene todos los tipos de servicio con paginacion.

        Raises:
            DatabaseError: Si hay error de BD
        """
        return await self.repository.obtener_todas(incluir_inactivas, limite, offset)

    async def obtener_activas(self) -> List[TipoServicio]:
        """
        Obtiene todos los tipos de servicio activos.

        Raises:
            DatabaseError: Si hay error de BD
        """
        return await self.obtener_todas(incluir_inactivas=False)

    async def buscar(self, termino: str, limite: int = 10) -> List[TipoServicio]:
        """
        Busca tipos por nombre o clave.

        Raises:
            DatabaseError: Si hay error de BD
        """
        if not termino or len(termino.strip()) < 2:
            return []

        return await self.repository.buscar_por_texto(termino.strip(), limite)

    async def contar(self, incluir_inactivas: bool = False) -> int:
        """
        Cuenta el total de tipos de servicio.

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

        Raises:
            DuplicateError: Si la clave ya existe
            DatabaseError: Si hay error de BD
        """
        tipo = TipoServicio(**tipo_create.model_dump())

        logger.info(f"Creando tipo de servicio: {tipo.clave} - {tipo.nombre}")

        return await self.repository.crear(tipo)

    async def actualizar(self, tipo_id: int, tipo_update: TipoServicioUpdate) -> TipoServicio:
        """
        Actualiza un tipo de servicio existente.

        Raises:
            NotFoundError: Si el tipo no existe
            DuplicateError: Si la nueva clave ya existe
            DatabaseError: Si hay error de BD
        """
        tipo_actual = await self.repository.obtener_por_id(tipo_id)

        datos_actualizados = tipo_update.model_dump(exclude_unset=True)

        for campo, valor in datos_actualizados.items():
            if valor is not None:
                setattr(tipo_actual, campo, valor)

        logger.info(f"Actualizando tipo de servicio ID {tipo_id}")

        # Verificar clave duplicada (excluyendo el registro actual)
        if await self.repository.existe_clave(tipo_actual.clave, excluir_id=tipo_actual.id):
            from app.core.exceptions import DuplicateError
            raise DuplicateError(
                f"La clave '{tipo_actual.clave}' ya existe en otro tipo",
                field="clave",
                value=tipo_actual.clave
            )

        return await self.repository.actualizar(tipo_actual)

    async def eliminar(self, tipo_id: int) -> bool:
        """
        Elimina (desactiva) un tipo de servicio.

        Raises:
            NotFoundError: Si el tipo no existe
            BusinessRuleError: Si tiene contratos activos
            DatabaseError: Si hay error de BD
        """
        tipo = await self.repository.obtener_por_id(tipo_id)

        await self._validar_puede_eliminar(tipo)

        logger.info(f"Eliminando (desactivando) tipo de servicio: {tipo.clave}")

        return await self.repository.eliminar(tipo_id)

    async def activar(self, tipo_id: int) -> TipoServicio:
        """
        Activa un tipo de servicio que estaba inactivo.

        Raises:
            NotFoundError: Si el tipo no existe
            BusinessRuleError: Si ya esta activo
            DatabaseError: Si hay error de BD
        """
        tipo = await self.repository.obtener_por_id(tipo_id)

        if tipo.estatus == Estatus.ACTIVO.value:
            raise BusinessRuleError("El tipo ya esta activo")

        tipo.estatus = Estatus.ACTIVO.value

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
        """
        # TODO: Cuando exista la validacion:
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

        Raises:
            DatabaseError: Si hay error de BD
        """
        return await self.repository.existe_clave(clave, excluir_id)


# ==========================================
# SINGLETON
# ==========================================

tipo_servicio_service = TipoServicioService()
