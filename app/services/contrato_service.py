"""
Servicio de aplicación para gestión de contratos.

Patrón de manejo de errores:
- Las excepciones del repository se propagan (NotFoundError, DuplicateError, DatabaseError)
- El servicio NO captura excepciones, las deja subir al State
- Logging de errores solo para debugging, NO para control de flujo
"""
import logging
from typing import List, Optional
from datetime import date
from decimal import Decimal

from app.entities import (
    Contrato,
    ContratoCreate,
    ContratoUpdate,
    ContratoResumen,
    EstatusContrato,
    ModalidadAdjudicacion,
    TipoDuracion,
)
from app.repositories import SupabaseContratoRepository
from app.core.exceptions import NotFoundError, DuplicateError, DatabaseError, BusinessRuleError

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
        return await self.repository.obtener_por_id(contrato_id)

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
        return await self.repository.obtener_por_codigo(codigo)

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
        return await self.repository.obtener_todos(incluir_inactivos, limite, offset)

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
        contratos = await self.repository.obtener_todos(incluir_inactivos, limite, offset)
        return [ContratoResumen.from_contrato(c) for c in contratos]

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
        return await self.repository.obtener_por_empresa(empresa_id, incluir_inactivos)

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
        return await self.repository.obtener_por_tipo_servicio(tipo_servicio_id, incluir_inactivos)

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
        if not termino or len(termino) < 2:
            return []
        return await self.repository.buscar_por_texto(termino, limite)

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
        if texto and len(texto.strip()) < 2:
            texto = None

        contratos = await self.repository.buscar_con_filtros(
            texto=texto,
            empresa_id=empresa_id,
            tipo_servicio_id=tipo_servicio_id,
            estatus=estatus,
            modalidad=modalidad,
            fecha_inicio_desde=fecha_inicio_desde,
            fecha_inicio_hasta=fecha_inicio_hasta,
            incluir_inactivos=incluir_inactivos,
            limite=limite,
            offset=offset
        )
        return [ContratoResumen.from_contrato(c) for c in contratos]

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
        # Convertir a Contrato
        contrato = Contrato(**contrato_create.model_dump())

        # Delegar al repository
        return await self.repository.crear(contrato)

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
        # Generar código único
        codigo = await self.generar_codigo_contrato(
            codigo_empresa,
            clave_servicio,
            contrato_create.fecha_inicio.year
        )

        # Crear contrato con código generado
        datos = contrato_create.model_dump()
        datos['codigo'] = codigo
        contrato = Contrato(**datos)

        return await self.repository.crear(contrato)

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
        consecutivo = await self.repository.obtener_siguiente_consecutivo(
            codigo_empresa,
            clave_servicio,
            anio
        )
        return Contrato.generar_codigo(codigo_empresa, clave_servicio, anio, consecutivo)

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
        # Obtener contrato actual
        contrato_actual = await self.repository.obtener_por_id(contrato_id)

        # Verificar si puede modificarse
        if not contrato_actual.puede_modificarse():
            raise BusinessRuleError(
                f"No se puede modificar un contrato en estado {contrato_actual.estatus}"
            )

        # Aplicar actualizaciones
        datos_actualizados = contrato_actual.model_dump()
        for campo, valor in contrato_update.model_dump(exclude_unset=True).items():
            if valor is not None:
                datos_actualizados[campo] = valor

        # Crear contrato modificado (valida automáticamente)
        contrato_modificado = Contrato(**datos_actualizados)

        return await self.repository.actualizar(contrato_modificado)

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
        contrato = await self.repository.obtener_por_id(contrato_id)

        if not contrato.puede_activarse():
            raise BusinessRuleError(
                f"No se puede activar un contrato en estado {contrato.estatus}"
            )

        return await self.repository.cambiar_estatus(contrato_id, EstatusContrato.ACTIVO)

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
        contrato = await self.repository.obtener_por_id(contrato_id)

        if contrato.estatus != EstatusContrato.ACTIVO:
            raise BusinessRuleError("Solo se pueden suspender contratos activos")

        return await self.repository.cambiar_estatus(contrato_id, EstatusContrato.SUSPENDIDO)

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
        contrato = await self.repository.obtener_por_id(contrato_id)

        if contrato.estatus != EstatusContrato.SUSPENDIDO:
            raise BusinessRuleError("Solo se pueden reactivar contratos suspendidos")

        return await self.repository.cambiar_estatus(contrato_id, EstatusContrato.ACTIVO)

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
        contrato = await self.repository.obtener_por_id(contrato_id)

        if contrato.estatus == EstatusContrato.CANCELADO:
            raise BusinessRuleError("El contrato ya está cancelado")

        return await self.repository.cambiar_estatus(contrato_id, EstatusContrato.CANCELADO)

    async def marcar_vencido(self, contrato_id: int) -> Contrato:
        """
        Marca un contrato como vencido.

        Args:
            contrato_id: ID del contrato

        Returns:
            Contrato marcado como vencido

        Raises:
            NotFoundError: Si el contrato no existe
            BusinessRuleError: Si no puede marcarse como vencido
            DatabaseError: Si hay error de BD
        """
        contrato = await self.repository.obtener_por_id(contrato_id)

        if contrato.estatus != EstatusContrato.ACTIVO:
            raise BusinessRuleError("Solo se pueden marcar como vencidos contratos activos")

        return await self.repository.cambiar_estatus(contrato_id, EstatusContrato.VENCIDO)

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
        return await self.repository.eliminar(contrato_id)

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
        return await self.repository.obtener_vigentes()

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
        return await self.repository.obtener_por_vencer(dias)

    async def existe_codigo(self, codigo: str, excluir_id: Optional[int] = None) -> bool:
        """
        Verifica si existe un código de contrato.

        Args:
            codigo: Código a verificar
            excluir_id: ID a excluir (para ediciones)

        Returns:
            True si el código ya existe
        """
        return await self.repository.existe_codigo(codigo, excluir_id)

    # ==========================================
    # VALIDACIONES DE NEGOCIO
    # ==========================================

    def validar_montos(
        self,
        monto_minimo: Optional[Decimal],
        monto_maximo: Optional[Decimal]
    ) -> bool:
        """
        Valida que los montos sean coherentes.

        Args:
            monto_minimo: Monto mínimo
            monto_maximo: Monto máximo

        Returns:
            True si son válidos

        Raises:
            BusinessRuleError: Si los montos no son válidos
        """
        if monto_minimo and monto_maximo:
            if monto_maximo < monto_minimo:
                raise BusinessRuleError("El monto máximo no puede ser menor al monto mínimo")
        return True

    def validar_fechas(
        self,
        fecha_inicio: date,
        fecha_fin: Optional[date],
        tipo_duracion: TipoDuracion
    ) -> bool:
        """
        Valida que las fechas sean coherentes.

        Args:
            fecha_inicio: Fecha de inicio
            fecha_fin: Fecha de fin (puede ser None)
            tipo_duracion: Tipo de duración del contrato

        Returns:
            True si son válidas

        Raises:
            BusinessRuleError: Si las fechas no son válidas
        """
        if fecha_fin and fecha_fin < fecha_inicio:
            raise BusinessRuleError("La fecha de fin no puede ser anterior a la fecha de inicio")

        if tipo_duracion == TipoDuracion.TIEMPO_DETERMINADO and not fecha_fin:
            raise BusinessRuleError("Los contratos de tiempo determinado deben tener fecha de fin")

        return True


# Instancia global del servicio (singleton)
contrato_service = ContratoService()
