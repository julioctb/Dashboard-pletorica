"""
Servicio de aplicación para gestión de Entregables.

Orquesta la lógica de negocio para:
- Generación automática de períodos (lazy, al consultar)
- Flujo de entrega: PENDIENTE → EN_REVISION → APROBADO/RECHAZADO
- Cálculo de montos según detalle de personal
- Creación automática de pagos al aprobar

Patrón de manejo de errores (igual que otros servicios):
- Las excepciones del repository se propagan al State
- El servicio agrega BusinessRuleError para validaciones de negocio
- Logging solo para debugging
"""

import logging
from calendar import monthrange
from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional, Tuple
from uuid import UUID

from app.core.enums import (
    EstatusEntregable,
    EstatusContrato,
    PeriodicidadEntregable,
    EstatusPago,
)
from app.core.exceptions import (
    BusinessRuleError,
    DatabaseError,
    NotFoundError,
)
from app.entities.entregable import (
    Entregable,
    EntregableCreate,
    EntregableUpdate,
    EntregableResumen,
    EntregableDetallePersonal,
    EntregableDetallePersonalCreate,
    EntregableDetallePersonalResumen,
    ResumenEntregablesContrato,
    AlertaEntregables,
    ContratoTipoEntregable,
    ContratoTipoEntregableCreate,
)
from app.repositories.entregable_repository import SupabaseEntregableRepository

logger = logging.getLogger(__name__)


class EntregableService:
    """
    Servicio de aplicación para Entregables.
    
    Responsabilidades:
    - Generación automática de períodos según vigencia del contrato
    - Validación de reglas de negocio (transiciones de estado, montos)
    - Orquestación del flujo de aprobación
    """
    
    def __init__(self, repository: SupabaseEntregableRepository = None):
        self.repository = repository or SupabaseEntregableRepository()
    
    # =========================================================================
    # GENERACIÓN DE PERÍODOS (LAZY)
    # =========================================================================
    
    def _calcular_periodos_requeridos(
        self,
        fecha_inicio: date,
        fecha_fin: date,
        periodicidad: PeriodicidadEntregable,
        fecha_actual: date = None,
    ) -> List[Tuple[date, date, int]]:
        """
        Calcula los períodos que deberían existir hasta la fecha actual.
        Solo genera períodos que ya terminaron (fecha_fin < fecha_actual).
        
        Returns:
            Lista de tuplas (periodo_inicio, periodo_fin, numero_periodo)
        """
        if fecha_actual is None:
            fecha_actual = date.today()
        
        periodos = []
        numero = 1
        
        # Caso especial: período único
        if periodicidad == PeriodicidadEntregable.UNICO:
            if fecha_actual > fecha_fin:
                periodos.append((fecha_inicio, fecha_fin, 1))
            return periodos
        
        periodo_inicio = fecha_inicio
        
        while periodo_inicio <= fecha_fin:
            if periodicidad == PeriodicidadEntregable.MENSUAL:
                mes_inicio = periodo_inicio.replace(day=1)
                _, ultimo_dia = monthrange(mes_inicio.year, mes_inicio.month)
                mes_fin = mes_inicio.replace(day=ultimo_dia)
                
                periodo_real_inicio = max(mes_inicio, fecha_inicio)
                periodo_real_fin = min(mes_fin, fecha_fin)
                
            elif periodicidad == PeriodicidadEntregable.QUINCENAL:
                if periodo_inicio.day <= 15:
                    q_inicio = periodo_inicio.replace(day=1)
                    q_fin = periodo_inicio.replace(day=15)
                else:
                    q_inicio = periodo_inicio.replace(day=16)
                    _, ultimo_dia = monthrange(periodo_inicio.year, periodo_inicio.month)
                    q_fin = periodo_inicio.replace(day=ultimo_dia)
                
                periodo_real_inicio = max(q_inicio, fecha_inicio)
                periodo_real_fin = min(q_fin, fecha_fin)
            else:
                break
            
            # Solo agregar si el período ya terminó
            if periodo_real_fin < fecha_actual:
                periodos.append((periodo_real_inicio, periodo_real_fin, numero))
                numero += 1
            
            # Avanzar al siguiente período
            if periodicidad == PeriodicidadEntregable.MENSUAL:
                if mes_fin.month == 12:
                    periodo_inicio = date(mes_fin.year + 1, 1, 1)
                else:
                    periodo_inicio = date(mes_fin.year, mes_fin.month + 1, 1)
            
            elif periodicidad == PeriodicidadEntregable.QUINCENAL:
                if periodo_inicio.day <= 15:
                    periodo_inicio = periodo_inicio.replace(day=16)
                else:
                    if periodo_inicio.month == 12:
                        periodo_inicio = date(periodo_inicio.year + 1, 1, 1)
                    else:
                        periodo_inicio = date(periodo_inicio.year, periodo_inicio.month + 1, 1)
        
        return periodos
    
    async def _sincronizar_periodos(self, contrato_id: int) -> int:
        """
        Sincroniza los períodos de entregable para un contrato.
        Calcula qué períodos deberían existir y crea los que falten.
        
        Returns:
            Cantidad de períodos creados
        """
        # Import diferido para evitar dependencias circulares
        from app.services import contrato_service
        
        contrato = await contrato_service.obtener_por_id(contrato_id)
        
        periodicidad_str = await self.repository.obtener_periodicidad_contrato(contrato_id)
        
        if not periodicidad_str:
            return 0
        
        if contrato.estatus not in (EstatusContrato.ACTIVO, EstatusContrato.BORRADOR):
            return 0
        
        if not contrato.fecha_inicio or not contrato.fecha_fin:
            return 0
        
        periodicidad = PeriodicidadEntregable(periodicidad_str)
        
        periodos_requeridos = self._calcular_periodos_requeridos(
            fecha_inicio=contrato.fecha_inicio,
            fecha_fin=contrato.fecha_fin,
            periodicidad=periodicidad,
        )
        
        if not periodos_requeridos:
            return 0
        
        ultimo_periodo = await self.repository.obtener_ultimo_numero_periodo(contrato_id)
        
        creados = 0
        for p_inicio, p_fin, num_esperado in periodos_requeridos:
            if num_esperado <= ultimo_periodo:
                continue
            
            existente = await self.repository.obtener_por_contrato_y_periodo(
                contrato_id, num_esperado
            )
            if existente:
                continue
            
            entregable = Entregable(
                contrato_id=contrato_id,
                periodo_inicio=p_inicio,
                periodo_fin=p_fin,
                numero_periodo=num_esperado,
                estatus=EstatusEntregable.PENDIENTE,
            )
            
            await self.repository.crear(entregable)
            creados += 1
            logger.info(
                f"Creado período {num_esperado} para contrato {contrato_id}: "
                f"{p_inicio} - {p_fin}"
            )
        
        return creados
    
    # =========================================================================
    # OPERACIONES CRUD
    # =========================================================================
    
    async def obtener_por_id(self, entregable_id: int) -> Entregable:
        """
        Obtiene un entregable por su ID.
        
        Raises:
            NotFoundError: Si no existe
            DatabaseError: Si hay error de BD
        """
        return await self.repository.obtener_por_id(entregable_id)
    
    async def obtener_por_contrato(
        self,
        contrato_id: int,
        incluir_todos: bool = False,
        sincronizar: bool = True,
    ) -> List[Entregable]:
        """
        Obtiene todos los entregables de un contrato.
        Sincroniza automáticamente los períodos antes de retornar.
        """
        if sincronizar:
            await self._sincronizar_periodos(contrato_id)
        
        return await self.repository.obtener_por_contrato(contrato_id, incluir_todos)
    
    async def obtener_resumen_por_contrato(
        self,
        contrato_id: int,
        sincronizar: bool = True,
    ) -> List[EntregableResumen]:
        """Obtiene resumen de entregables con datos del contrato y empresa."""
        if sincronizar:
            await self._sincronizar_periodos(contrato_id)
        
        return await self.repository.obtener_resumen_por_contrato(contrato_id)
    
    async def obtener_estadisticas_contrato(
        self,
        contrato_id: int,
    ) -> ResumenEntregablesContrato:
        """Obtiene estadísticas de entregables para un contrato."""
        await self._sincronizar_periodos(contrato_id)
        return await self.repository.obtener_estadisticas_contrato(contrato_id)
    
    # =========================================================================
    # FLUJO DE ENTREGA (CLIENTE)
    # =========================================================================
    
    async def entregar(
        self,
        entregable_id: int,
        monto_calculado: Optional[Decimal] = None,
    ) -> Entregable:
        """
        Marca un entregable como entregado (cambia a EN_REVISION).
        El cliente llama este método después de subir todos los archivos.
        
        Raises:
            BusinessRuleError: Si no está en estado válido
        """
        entregable = await self.repository.obtener_por_id(entregable_id)
        
        if not entregable.puede_editar_cliente:
            raise BusinessRuleError(
                f"No se puede entregar un entregable en estado {entregable.estatus}. "
                f"Solo se permite entregar en estado PENDIENTE o RECHAZADO."
            )
        
        entregable.estatus = EstatusEntregable.EN_REVISION
        entregable.fecha_entrega = datetime.now()
        entregable.observaciones_rechazo = None
        
        if monto_calculado is not None:
            entregable.monto_calculado = monto_calculado
        
        entregable_actualizado = await self.repository.actualizar(entregable)
        
        logger.info(f"Entregable {entregable_id} entregado. Monto: {monto_calculado}")
        
        return entregable_actualizado
    
    # =========================================================================
    # FLUJO DE REVISIÓN (ADMIN)
    # =========================================================================
    
    async def aprobar(
        self,
        entregable_id: int,
        monto_aprobado: Decimal,
        revisado_por: UUID,
    ) -> Entregable:
        """
        Aprueba un entregable y crea el pago asociado.
        
        Raises:
            BusinessRuleError: Si no está en estado válido o monto excede límite
        """
        entregable = await self.repository.obtener_por_id(entregable_id)
        
        if not entregable.puede_revisar_admin:
            raise BusinessRuleError(
                f"No se puede aprobar un entregable en estado {entregable.estatus}. "
                f"Solo se permite aprobar en estado EN_REVISION."
            )
        
        await self._validar_monto_aprobado(entregable.contrato_id, monto_aprobado)
        
        pago = await self._crear_pago_entregable(entregable, monto_aprobado)
        
        entregable.estatus = EstatusEntregable.APROBADO
        entregable.fecha_revision = datetime.now()
        entregable.revisado_por = revisado_por
        entregable.monto_aprobado = monto_aprobado
        entregable.pago_id = pago.id
        
        entregable_actualizado = await self.repository.actualizar(entregable)
        
        logger.info(
            f"Entregable {entregable_id} aprobado. "
            f"Monto: {monto_aprobado}, Pago ID: {pago.id}"
        )
        
        return entregable_actualizado
    
    async def rechazar(
        self,
        entregable_id: int,
        observaciones: str,
        revisado_por: UUID,
    ) -> Entregable:
        """
        Rechaza un entregable con observaciones.
        
        Raises:
            BusinessRuleError: Si no está en estado válido o falta observación
        """
        entregable = await self.repository.obtener_por_id(entregable_id)
        
        if not entregable.puede_revisar_admin:
            raise BusinessRuleError(
                f"No se puede rechazar un entregable en estado {entregable.estatus}."
            )
        
        if not observaciones or not observaciones.strip():
            raise BusinessRuleError(
                "Debe proporcionar observaciones al rechazar un entregable."
            )
        
        entregable.estatus = EstatusEntregable.RECHAZADO
        entregable.fecha_revision = datetime.now()
        entregable.revisado_por = revisado_por
        entregable.observaciones_rechazo = observaciones.strip()
        
        entregable_actualizado = await self.repository.actualizar(entregable)
        
        logger.info(f"Entregable {entregable_id} rechazado: {observaciones[:50]}...")
        
        return entregable_actualizado
    
    # =========================================================================
    # ALERTAS Y DASHBOARD
    # =========================================================================

    async def obtener_alertas(
        self,
        empresa_id: Optional[int] = None,
        limite: int = 10,
    ) -> AlertaEntregables:
        """Obtiene alertas de entregables en revisión para dashboard."""
        return await self.repository.obtener_alertas(empresa_id, limite)

    async def contar_en_revision(
        self,
        empresa_id: Optional[int] = None,
    ) -> int:
        """Cuenta entregables en revisión para badge de alerta."""
        return await self.repository.contar_en_revision(empresa_id)

    # =========================================================================
    # VISTA GLOBAL (ADMIN)
    # =========================================================================

    async def obtener_global(
        self,
        estatus: Optional[str] = None,
        contrato_id: Optional[int] = None,
        limite: int = 100,
    ) -> List[EntregableResumen]:
        """
        Obtiene todos los entregables con datos de contrato y empresa.
        Usado para la vista global del admin.
        """
        return await self.repository.obtener_todos_global(estatus, contrato_id, limite)

    async def obtener_estadisticas_global(self) -> dict:
        """
        Obtiene estadísticas globales de todos los entregables.
        """
        return await self.repository.obtener_estadisticas_global()

    # =========================================================================
    # PORTAL DEL CLIENTE
    # =========================================================================

    async def obtener_por_empresa(
        self,
        empresa_id: int,
        estatus_list: Optional[List[str]] = None,
        contrato_id: Optional[int] = None,
        limite: int = 100,
    ) -> List[EntregableResumen]:
        """
        Obtiene entregables de todos los contratos de una empresa.
        Usado para la vista global del cliente en el portal.
        """
        return await self.repository.obtener_por_empresa(
            empresa_id, estatus_list, contrato_id, limite
        )

    async def obtener_estadisticas_empresa(self, empresa_id: int) -> dict:
        """
        Obtiene estadísticas de entregables para una empresa.
        """
        return await self.repository.obtener_estadisticas_empresa(empresa_id)
    
    # =========================================================================
    # DETALLE DE PERSONAL
    # =========================================================================
    
    async def obtener_detalle_personal(
        self,
        entregable_id: int,
    ) -> List[EntregableDetallePersonalResumen]:
        """Obtiene el detalle de personal de un entregable."""
        return await self.repository.obtener_detalle_personal(entregable_id)
    
    async def guardar_detalle_personal(
        self,
        entregable_id: int,
        detalles: List[EntregableDetallePersonalCreate],
    ) -> Tuple[List[EntregableDetallePersonal], Decimal]:
        """
        Guarda el detalle de personal y calcula el monto total.
        
        Returns:
            Tupla (detalles_creados, monto_total_calculado)
        """
        entregable = await self.repository.obtener_por_id(entregable_id)
        
        if not entregable.puede_editar_cliente:
            raise BusinessRuleError(
                f"No se puede modificar el detalle de un entregable en estado {entregable.estatus}."
            )
        
        await self.repository.eliminar_detalle_personal(entregable_id)
        
        creados = []
        monto_total = Decimal("0")
        
        for detalle_create in detalles:
            subtotal = Decimal(str(detalle_create.cantidad_validada)) * detalle_create.tarifa_unitaria
            
            detalle = EntregableDetallePersonal(
                entregable_id=entregable_id,
                contrato_categoria_id=detalle_create.contrato_categoria_id,
                cantidad_reportada=detalle_create.cantidad_reportada,
                cantidad_validada=detalle_create.cantidad_validada,
                tarifa_unitaria=detalle_create.tarifa_unitaria,
                subtotal=subtotal,
            )
            
            creado = await self.repository.crear_detalle_personal(detalle)
            creados.append(creado)
            monto_total += subtotal
        
        logger.info(
            f"Guardado detalle de personal para entregable {entregable_id}: "
            f"{len(creados)} categorías, monto total: {monto_total}"
        )
        
        return creados, monto_total
    
    # =========================================================================
    # CONFIGURACIÓN
    # =========================================================================
    
    async def obtener_configuracion_contrato(
        self,
        contrato_id: int,
    ) -> List[dict]:
        """Obtiene la configuración de tipos de entregable de un contrato."""
        return await self.repository.obtener_configuracion_contrato(contrato_id)
    
    async def configurar_tipo_entregable(
        self,
        config: ContratoTipoEntregableCreate,
    ) -> ContratoTipoEntregable:
        """Agrega o actualiza configuración de tipo de entregable."""
        from app.database import db_manager
        supabase = db_manager.get_client()
        
        try:
            datos = config.model_dump(mode='json')
            
            result = supabase.table('contrato_tipo_entregable')\
                .upsert(datos, on_conflict='contrato_id,tipo_entregable')\
                .execute()
            
            if not result.data:
                raise DatabaseError("No se pudo guardar la configuración")
            
            return ContratoTipoEntregable(**result.data[0])
        
        except Exception as e:
            logger.error(f"Error guardando configuración de entregable: {e}")
            raise DatabaseError(f"Error de base de datos: {str(e)}")
    
    # =========================================================================
    # MÉTODOS PRIVADOS
    # =========================================================================
    
    async def _validar_monto_aprobado(
        self,
        contrato_id: int,
        monto: Decimal,
    ) -> None:
        """Valida que el monto aprobado esté dentro de los límites del contrato."""
        from app.services import contrato_service
        
        contrato = await contrato_service.obtener_por_id(contrato_id)
        
        if contrato.monto_maximo and monto > contrato.monto_maximo:
            raise BusinessRuleError(
                f"El monto aprobado ({monto}) excede el máximo del contrato "
                f"({contrato.monto_maximo})."
            )
    
    async def _crear_pago_entregable(
        self,
        entregable: Entregable,
        monto: Decimal,
    ):
        """Crea un pago asociado al entregable aprobado."""
        from app.database import db_manager
        supabase = db_manager.get_client()
        
        concepto = f"Pago período {entregable.numero_periodo} ({entregable.periodo_texto})"
        
        datos = {
            'contrato_id': entregable.contrato_id,
            'fecha_pago': date.today().isoformat(),
            'monto': float(monto),
            'concepto': concepto,
            'estatus': EstatusPago.PENDIENTE.value,
            'entregable_id': entregable.id,
        }
        
        try:
            result = supabase.table('pagos').insert(datos).execute()
            
            if not result.data:
                raise DatabaseError("No se pudo crear el pago")
            
            class PagoSimple:
                def __init__(self, data):
                    self.id = data['id']
            
            return PagoSimple(result.data[0])
        
        except Exception as e:
            logger.error(f"Error creando pago para entregable {entregable.id}: {e}")
            raise DatabaseError(f"Error al crear pago: {str(e)}")


# =============================================================================
# SINGLETON (patrón igual que otros servicios del proyecto)
# =============================================================================

entregable_service = EntregableService()
