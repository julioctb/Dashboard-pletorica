"""
Servicio de aplicación para gestión de contratos.

Patrón de manejo de errores:
- Las excepciones del repository se propagan (NotFoundError, DuplicateError, DatabaseError)
- El servicio NO captura excepciones, las deja subir al State
- Logging de errores solo para debugging, NO para control de flujo
"""
import logging
from decimal import Decimal
from typing import Dict, List, Optional
from datetime import date
from app.entities import (
    Contrato,
    ContratoCreate,
    ContratoUpdate,
    ContratoResumen,
    EstatusContrato,
)
from app.entities.contrato_item import ContratoItem, ContratoItemCreate
from app.repositories import SupabaseContratoRepository
from app.core.exceptions import BusinessRuleError
from app.services.contratos.items import ContratoItemService
from app.services.contratos.mutations import ContratoMutationService
from app.services.contratos.queries import ContratoQueryService

logger = logging.getLogger(__name__)


class ContratoService:
    """
    Servicio de aplicación para contratos.
    Orquesta las operaciones de negocio.
    """

    def __init__(self, repository=None):
        """
        Inicializa el servicio con un repository.

        Args:
            repository: Implementación del repository. Si es None, usa Supabase por defecto.
        """
        if repository is None:
            repository = SupabaseContratoRepository()
        self.repository = repository
        self._query_service = ContratoQueryService(self)
        self._mutation_service = ContratoMutationService(self)
        self._item_service = ContratoItemService(self)

    # ==========================================
    # OPERACIONES CRUD
    # ==========================================

    async def obtener_por_id(self, contrato_id: int) -> Contrato:
        """
        Obtiene un contrato por su ID.

        Args:
            contrato_id: ID del contrato

        Returns:
            Contrato encontrado

        Raises:
            NotFoundError: Si el contrato no existe
            DatabaseError: Si hay error de BD
        """
        return await self._query_service.obtener_por_id(contrato_id)

    async def obtener_por_codigo(self, codigo: str) -> Optional[Contrato]:
        """
        Obtiene un contrato por su código único.

        Args:
            codigo: Código del contrato (ej: MAN-JAR-25001)

        Returns:
            Contrato encontrado o None

        Raises:
            DatabaseError: Si hay error de BD
        """
        return await self._query_service.obtener_por_codigo(codigo)

    async def obtener_todos(
        self,
        incluir_inactivos: bool = False,
        limite: Optional[int] = None,
        offset: int = 0
    ) -> List[Contrato]:
        """
        Obtiene todos los contratos con paginación.

        Args:
            incluir_inactivos: Si True, incluye contratos cancelados/vencidos
            limite: Número máximo de resultados (None = 100 por defecto)
            offset: Número de registros a saltar

        Returns:
            Lista de contratos

        Raises:
            DatabaseError: Si hay error de BD
        """
        return await self._query_service.obtener_todos(incluir_inactivos, limite, offset)

    async def obtener_resumen_contratos(
        self,
        incluir_inactivos: bool = False,
        limite: Optional[int] = 50,
        offset: int = 0
    ) -> List[ContratoResumen]:
        """
        Obtiene un resumen de todos los contratos de forma eficiente.

        Args:
            incluir_inactivos: Si True, incluye contratos cancelados/vencidos
            limite: Número máximo de resultados (default 50 para UI)
            offset: Número de registros a saltar

        Returns:
            Lista de resúmenes de contratos

        Raises:
            DatabaseError: Si hay error de BD
        """
        return await self._query_service.obtener_resumen_contratos(
            incluir_inactivos,
            limite,
            offset,
        )

    async def obtener_por_empresa(
        self,
        empresa_id: int,
        incluir_inactivos: bool = False
    ) -> List[Contrato]:
        """
        Obtiene todos los contratos de una empresa.

        Args:
            empresa_id: ID de la empresa
            incluir_inactivos: Si True, incluye cancelados/vencidos

        Returns:
            Lista de contratos de la empresa

        Raises:
            DatabaseError: Si hay error de BD
        """
        return await self._query_service.obtener_por_empresa(empresa_id, incluir_inactivos)

    async def obtener_por_tipo_servicio(
        self,
        tipo_servicio_id: int,
        incluir_inactivos: bool = False
    ) -> List[Contrato]:
        """
        Obtiene todos los contratos de un tipo de servicio.

        Args:
            tipo_servicio_id: ID del tipo de servicio
            incluir_inactivos: Si True, incluye cancelados/vencidos

        Returns:
            Lista de contratos del tipo de servicio

        Raises:
            DatabaseError: Si hay error de BD
        """
        return await self._query_service.obtener_por_tipo_servicio(
            tipo_servicio_id,
            incluir_inactivos,
        )

    async def buscar_por_texto(self, termino: str, limite: int = 10) -> List[Contrato]:
        """
        Busca contratos por código o folio BUAP.

        Args:
            termino: Término de búsqueda (mínimo 2 caracteres)
            limite: Número máximo de resultados

        Returns:
            Lista de contratos que coinciden

        Raises:
            DatabaseError: Si hay error de BD
        """
        return await self._query_service.buscar_por_texto(termino, limite)

    async def buscar_con_filtros(
        self,
        texto: Optional[str] = None,
        empresa_id: Optional[int] = None,
        tipo_servicio_id: Optional[int] = None,
        estatus: Optional[str] = None,
        modalidad: Optional[str] = None,
        fecha_inicio_desde: Optional[date] = None,
        fecha_inicio_hasta: Optional[date] = None,
        incluir_inactivos: bool = False,
        limite: int = 50,
        offset: int = 0
    ) -> List[ContratoResumen]:
        """
        Busca contratos con filtros combinados.

        Args:
            texto: Término de búsqueda (mínimo 2 caracteres)
            empresa_id: Filtrar por empresa
            tipo_servicio_id: Filtrar por tipo de servicio
            estatus: Filtrar por estatus
            modalidad: Filtrar por modalidad de adjudicación
            fecha_inicio_desde: Fecha de inicio mínima
            fecha_inicio_hasta: Fecha de inicio máxima
            incluir_inactivos: Si incluir cancelados/vencidos
            limite: Número máximo de resultados
            offset: Registros a saltar

        Returns:
            Lista de resúmenes de contratos

        Raises:
            DatabaseError: Si hay error de BD
        """
        return await self._query_service.buscar_con_filtros(
            texto=texto,
            empresa_id=empresa_id,
            tipo_servicio_id=tipo_servicio_id,
            estatus=estatus,
            modalidad=modalidad,
            fecha_inicio_desde=fecha_inicio_desde,
            fecha_inicio_hasta=fecha_inicio_hasta,
            incluir_inactivos=incluir_inactivos,
            limite=limite,
            offset=offset,
        )

    async def obtener_con_personal(
        self,
        solo_activos: bool = True,
        limite: int = 50
    ) -> List[ContratoResumen]:
        """
        Obtiene contratos que tienen personal (tiene_personal = True).

        Útil para el módulo de Plazas donde se necesita seleccionar
        un contrato para asignar plazas.

        Args:
            solo_activos: Si True, solo retorna contratos ACTIVOS o BORRADOR
            limite: Número máximo de resultados

        Returns:
            Lista de resúmenes de contratos con personal
        """
        return await self._query_service.obtener_con_personal(solo_activos, limite)

    # ==========================================
    # OPERACIONES DE CREACIÓN
    # ==========================================

    async def crear(self, contrato_create: ContratoCreate) -> Contrato:
        """
        Crea un nuevo contrato.

        Args:
            contrato_create: Datos del contrato a crear

        Returns:
            Contrato creado con ID asignado

        Raises:
            DuplicateError: Si el código ya existe
            ValidationError: Si los datos no son válidos
            DatabaseError: Si hay error de BD
        """
        return await self._mutation_service.crear(contrato_create)

    async def crear_con_codigo_auto(
        self,
        contrato_create: ContratoCreate,
        codigo_empresa: str,
        clave_servicio: str
    ) -> Contrato:
        """
        Crea un nuevo contrato generando el código automáticamente.

        El código tiene formato: [EMPRESA]-[SERVICIO]-[AÑO][CONSECUTIVO]
        Ejemplo: MAN-JAR-25001

        Args:
            contrato_create: Datos del contrato (código será sobrescrito)
            codigo_empresa: Código corto de la empresa (3 letras)
            clave_servicio: Clave del tipo de servicio (2-5 letras)

        Returns:
            Contrato creado con código autogenerado

        Raises:
            DuplicateError: Si el código generado ya existe (muy improbable)
            ValidationError: Si los datos no son válidos
            DatabaseError: Si hay error de BD
        """
        return await self._mutation_service.crear_con_codigo_auto(
            contrato_create,
            codigo_empresa,
            clave_servicio,
        )

    async def generar_codigo_contrato(
        self,
        codigo_empresa: str,
        clave_servicio: str,
        anio: int
    ) -> str:
        """
        Genera un código único para un nuevo contrato.

        Formato: [EMPRESA]-[SERVICIO]-[AÑO][CONSECUTIVO]
        Ejemplo: MAN-JAR-25001

        Args:
            codigo_empresa: Código corto de la empresa (3 letras)
            clave_servicio: Clave del tipo de servicio (2-5 letras)
            anio: Año del contrato

        Returns:
            Código único generado

        Raises:
            DatabaseError: Si hay error al obtener consecutivo
        """
        return await self._mutation_service.generar_codigo_contrato(
            codigo_empresa,
            clave_servicio,
            anio,
        )

    # ==========================================
    # OPERACIONES DE ACTUALIZACIÓN
    # ==========================================

    async def actualizar(self, contrato_id: int, contrato_update: ContratoUpdate) -> Contrato:
        """
        Actualiza un contrato existente.

        Args:
            contrato_id: ID del contrato a actualizar
            contrato_update: Datos a actualizar

        Returns:
            Contrato actualizado

        Raises:
            NotFoundError: Si el contrato no existe
            BusinessRuleError: Si el contrato no puede modificarse
            ValidationError: Si los datos no son válidos
            DatabaseError: Si hay error de BD
        """
        return await self._mutation_service.actualizar(contrato_id, contrato_update)

    # ==========================================
    # OPERACIONES DE CAMBIO DE ESTATUS
    # ==========================================

    async def activar(self, contrato_id: int) -> Contrato:
        """
        Activa un contrato (cambia de BORRADOR a ACTIVO).

        Args:
            contrato_id: ID del contrato

        Returns:
            Contrato activado

        Raises:
            NotFoundError: Si el contrato no existe
            BusinessRuleError: Si no puede activarse
            DatabaseError: Si hay error de BD
        """
        return await self._mutation_service.activar(contrato_id)

    async def suspender(self, contrato_id: int) -> Contrato:
        """
        Suspende un contrato activo.

        Args:
            contrato_id: ID del contrato

        Returns:
            Contrato suspendido

        Raises:
            NotFoundError: Si el contrato no existe
            BusinessRuleError: Si no puede suspenderse
            DatabaseError: Si hay error de BD
        """
        return await self._mutation_service.suspender(contrato_id)

    async def reactivar(self, contrato_id: int) -> Contrato:
        """
        Reactiva un contrato suspendido.

        Args:
            contrato_id: ID del contrato

        Returns:
            Contrato reactivado

        Raises:
            NotFoundError: Si el contrato no existe
            BusinessRuleError: Si no puede reactivarse
            DatabaseError: Si hay error de BD
        """
        return await self._mutation_service.reactivar(contrato_id)

    async def cancelar(self, contrato_id: int) -> Contrato:
        """
        Cancela un contrato (soft delete).

        Args:
            contrato_id: ID del contrato

        Returns:
            Contrato cancelado

        Raises:
            NotFoundError: Si el contrato no existe
            BusinessRuleError: Si ya está cancelado
            DatabaseError: Si hay error de BD
        """
        return await self._mutation_service.cancelar(contrato_id)

    async def eliminar(self, contrato_id: int) -> bool:
        """
        Elimina (cancela) un contrato.

        Args:
            contrato_id: ID del contrato

        Returns:
            True si se eliminó exitosamente

        Raises:
            DatabaseError: Si hay error de BD
        """
        return await self._mutation_service.eliminar(contrato_id)

    # ==========================================
    # CONSULTAS ESPECIALIZADAS
    # ==========================================

    async def obtener_vigentes(self) -> List[Contrato]:
        """
        Obtiene contratos activos y dentro de su periodo de vigencia.

        Returns:
            Lista de contratos vigentes

        Raises:
            DatabaseError: Si hay error de BD
        """
        return await self._query_service.obtener_vigentes()

    async def obtener_por_vencer(self, dias: int = 30) -> List[Contrato]:
        """
        Obtiene contratos que vencen en los próximos N días.

        Args:
            dias: Número de días hacia adelante (default 30)

        Returns:
            Lista de contratos por vencer

        Raises:
            DatabaseError: Si hay error de BD
        """
        return await self._query_service.obtener_por_vencer(dias)

    async def existe_codigo(self, codigo: str, excluir_id: Optional[int] = None) -> bool:
        """
        Verifica si existe un código de contrato.

        Args:
            codigo: Código a verificar
            excluir_id: ID a excluir (para ediciones)

        Returns:
            True si el código ya existe
        """
        return await self._query_service.existe_codigo(codigo, excluir_id)

    # ==========================================
    # CREACIÓN DESDE REQUISICIÓN
    # ==========================================

    async def crear_desde_requisicion(
        self,
        requisicion_id: int,
        contrato_create: ContratoCreate,
        codigo_empresa: str,
        clave_servicio: str,
        items_contrato: Optional[List[ContratoItemCreate]] = None,
    ) -> Contrato:
        """
        Crea un contrato vinculado a una requisición.

        1. Valida que la requisición esté en estado ADJUDICADA
        2. Crea el contrato con requisicion_id
        3. Copia items si se proporcionan (para ADQUISICION)
        4. Marca la requisición como CONTRATADA

        Args:
            requisicion_id: ID de la requisición origen
            contrato_create: Datos del contrato a crear
            codigo_empresa: Código corto de la empresa (3 letras)
            clave_servicio: Clave del tipo de servicio
            items_contrato: Items con precios para ADQUISICION

        Returns:
            Contrato creado

        Raises:
            BusinessRuleError: Si la requisición no está en estado ADJUDICADA
            DuplicateError: Si el código ya existe
            DatabaseError: Si hay error de BD
        """
        return await self._item_service.crear_desde_requisicion(
            requisicion_id=requisicion_id,
            contrato_create=contrato_create,
            codigo_empresa=codigo_empresa,
            clave_servicio=clave_servicio,
            items_contrato=items_contrato,
        )

    # ==========================================
    # CONTRATO ITEMS
    # ==========================================

    async def obtener_items(self, contrato_id: int) -> List[ContratoItem]:
        """Obtiene todos los items de un contrato."""
        return await self._item_service.obtener_items(contrato_id)

    async def copiar_items_desde_requisicion(
        self,
        contrato_id: int,
        requisicion_items: list,
        precios: Dict[int, Decimal],
    ) -> List[ContratoItem]:
        """
        Copia items desde una requisición a un contrato con precios definidos.

        Args:
            contrato_id: ID del contrato destino
            requisicion_items: Items de la requisición origen
            precios: Dict {requisicion_item_id: precio_unitario}

        Returns:
            Lista de items creados en el contrato
        """
        return await self._item_service.copiar_items_desde_requisicion(
            contrato_id,
            requisicion_items,
            precios,
        )


# Instancia global del servicio (singleton)
contrato_service = ContratoService()
