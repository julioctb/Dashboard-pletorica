"""
Servicio de aplicación para gestión de pagos de contratos.

Patrón de manejo de errores:
- Las excepciones del repository se propagan (NotFoundError, DatabaseError)
- El servicio NO captura excepciones, las deja subir al State
"""
import logging
from typing import List, Optional
from datetime import date
from decimal import Decimal

from app.entities import (
    Pago,
    PagoCreate,
    PagoUpdate,
    PagoResumen,
    ResumenPagosContrato,
    EstatusContrato,
)
from app.repositories import SupabasePagoRepository, SupabaseContratoRepository
from app.core.exceptions import NotFoundError, DatabaseError, BusinessRuleError

logger = logging.getLogger(__name__)


class PagoService:
    """
    Servicio de aplicación para pagos.
    Orquesta las operaciones de negocio.
    """

    def __init__(self, repository=None, contrato_repository=None):
        """
        Inicializa el servicio con repositories.

        Args:
            repository: Implementación del repository de pagos.
            contrato_repository: Implementación del repository de contratos.
        """
        if repository is None:
            repository = SupabasePagoRepository()
        if contrato_repository is None:
            contrato_repository = SupabaseContratoRepository()

        self.repository = repository
        self.contrato_repository = contrato_repository

    # ==========================================
    # OPERACIONES CRUD
    # ==========================================

    async def obtener_por_id(self, pago_id: int) -> Pago:
        """
        Obtiene un pago por su ID.

        Args:
            pago_id: ID del pago

        Returns:
            Pago encontrado

        Raises:
            NotFoundError: Si el pago no existe
            DatabaseError: Si hay error de BD
        """
        return await self.repository.obtener_por_id(pago_id)

    async def obtener_por_contrato(
        self,
        contrato_id: int,
        limite: Optional[int] = None,
        offset: int = 0
    ) -> List[Pago]:
        """
        Obtiene todos los pagos de un contrato.

        Args:
            contrato_id: ID del contrato
            limite: Número máximo de resultados
            offset: Registros a saltar

        Returns:
            Lista de pagos del contrato

        Raises:
            DatabaseError: Si hay error de BD
        """
        return await self.repository.obtener_por_contrato(contrato_id, limite, offset)

    async def crear(self, pago_create: PagoCreate) -> Pago:
        """
        Crea un nuevo pago.

        Args:
            pago_create: Datos del pago a crear

        Returns:
            Pago creado con ID asignado

        Raises:
            NotFoundError: Si el contrato no existe
            BusinessRuleError: Si el contrato no puede recibir pagos
            DatabaseError: Si hay error de BD
        """
        # Verificar que el contrato existe y puede recibir pagos
        contrato = await self.contrato_repository.obtener_por_id(pago_create.contrato_id)

        if contrato.estatus not in [EstatusContrato.ACTIVO, EstatusContrato.BORRADOR]:
            raise BusinessRuleError(
                f"No se pueden registrar pagos en un contrato con estatus {contrato.estatus}"
            )

        # Crear el pago
        pago = Pago(**pago_create.model_dump())
        return await self.repository.crear(pago)

    async def actualizar(self, pago_id: int, pago_update: PagoUpdate) -> Pago:
        """
        Actualiza un pago existente.

        Args:
            pago_id: ID del pago a actualizar
            pago_update: Datos a actualizar

        Returns:
            Pago actualizado

        Raises:
            NotFoundError: Si el pago no existe
            DatabaseError: Si hay error de BD
        """
        pago_actual = await self.repository.obtener_por_id(pago_id)

        # Aplicar actualizaciones
        datos_actualizados = pago_actual.model_dump()
        for campo, valor in pago_update.model_dump(exclude_unset=True).items():
            if valor is not None:
                datos_actualizados[campo] = valor

        pago_modificado = Pago(**datos_actualizados)
        return await self.repository.actualizar(pago_modificado)

    async def eliminar(self, pago_id: int) -> bool:
        """
        Elimina un pago.

        Args:
            pago_id: ID del pago a eliminar

        Returns:
            True si se eliminó exitosamente

        Raises:
            NotFoundError: Si el pago no existe
            DatabaseError: Si hay error de BD
        """
        # Verificar que existe
        await self.repository.obtener_por_id(pago_id)
        return await self.repository.eliminar(pago_id)

    # ==========================================
    # RESUMEN DE PAGOS
    # ==========================================

    async def obtener_resumen_pagos_contrato(self, contrato_id: int) -> ResumenPagosContrato:
        """
        Obtiene el resumen de pagos de un contrato.

        Args:
            contrato_id: ID del contrato

        Returns:
            Resumen con totales, saldo pendiente y porcentaje

        Raises:
            NotFoundError: Si el contrato no existe
            DatabaseError: Si hay error de BD
        """
        # Obtener contrato
        contrato = await self.contrato_repository.obtener_por_id(contrato_id)

        # Obtener datos de pagos
        total_pagado = await self.repository.obtener_total_pagado(contrato_id)
        cantidad_pagos = await self.repository.contar_pagos(contrato_id)
        ultimo_pago = await self.repository.obtener_ultimo_pago(contrato_id)

        # Calcular saldo pendiente y porcentaje
        monto_maximo = contrato.monto_maximo or Decimal("0")
        saldo_pendiente = max(monto_maximo - total_pagado, Decimal("0"))

        if monto_maximo > 0:
            porcentaje = (total_pagado / monto_maximo) * 100
        else:
            porcentaje = Decimal("0")

        return ResumenPagosContrato(
            contrato_id=contrato_id,
            codigo_contrato=contrato.codigo,
            monto_maximo=monto_maximo,
            total_pagado=total_pagado,
            saldo_pendiente=saldo_pendiente,
            porcentaje_pagado=round(porcentaje, 2),
            cantidad_pagos=cantidad_pagos,
            ultimo_pago=ultimo_pago.fecha_pago if ultimo_pago else None
        )

    async def verificar_contrato_pagado(self, contrato_id: int) -> bool:
        """
        Verifica si un contrato está completamente pagado.

        Args:
            contrato_id: ID del contrato

        Returns:
            True si el contrato está completamente pagado
        """
        resumen = await self.obtener_resumen_pagos_contrato(contrato_id)
        return resumen.esta_pagado

    # ==========================================
    # OPERACIONES DE CIERRE
    # ==========================================

    async def cerrar_contrato(self, contrato_id: int, forzar: bool = False) -> bool:
        """
        Cierra un contrato si está completamente pagado.

        Args:
            contrato_id: ID del contrato
            forzar: Si True, cierra aunque no esté completamente pagado

        Returns:
            True si se cerró exitosamente

        Raises:
            NotFoundError: Si el contrato no existe
            BusinessRuleError: Si no está pagado y no se fuerza
            DatabaseError: Si hay error de BD
        """
        contrato = await self.contrato_repository.obtener_por_id(contrato_id)

        if contrato.estatus == EstatusContrato.CERRADO:
            raise BusinessRuleError("El contrato ya está cerrado")

        if contrato.estatus not in [EstatusContrato.ACTIVO, EstatusContrato.VENCIDO]:
            raise BusinessRuleError(
                f"Solo se pueden cerrar contratos activos o vencidos (actual: {contrato.estatus})"
            )

        if not forzar:
            esta_pagado = await self.verificar_contrato_pagado(contrato_id)
            if not esta_pagado:
                resumen = await self.obtener_resumen_pagos_contrato(contrato_id)
                raise BusinessRuleError(
                    f"El contrato tiene saldo pendiente de ${resumen.saldo_pendiente}. "
                    "Use forzar=True para cerrar de todas formas."
                )

        # Cambiar estatus a CERRADO
        await self.contrato_repository.cambiar_estatus(contrato_id, EstatusContrato.CERRADO)
        return True

    # ==========================================
    # CONSULTAS ADICIONALES
    # ==========================================

    async def buscar_por_rango_fechas(
        self,
        contrato_id: int,
        fecha_desde: Optional[date] = None,
        fecha_hasta: Optional[date] = None
    ) -> List[Pago]:
        """
        Busca pagos de un contrato en un rango de fechas.

        Args:
            contrato_id: ID del contrato
            fecha_desde: Fecha inicial
            fecha_hasta: Fecha final

        Returns:
            Lista de pagos en el rango

        Raises:
            DatabaseError: Si hay error de BD
        """
        return await self.repository.buscar_por_rango_fechas(
            contrato_id, fecha_desde, fecha_hasta
        )

    async def obtener_resumen_lista(
        self,
        contrato_id: int,
        limite: Optional[int] = 50,
        offset: int = 0
    ) -> List[PagoResumen]:
        """
        Obtiene lista resumida de pagos para mostrar en tabla.

        Args:
            contrato_id: ID del contrato
            limite: Número máximo de resultados
            offset: Registros a saltar

        Returns:
            Lista de resúmenes de pago

        Raises:
            DatabaseError: Si hay error de BD
        """
        pagos = await self.repository.obtener_por_contrato(contrato_id, limite, offset)

        # Obtener código del contrato
        contrato = await self.contrato_repository.obtener_por_id(contrato_id)

        resumenes = []
        for pago in pagos:
            resumen = PagoResumen.from_pago(pago)
            resumen.codigo_contrato = contrato.codigo
            resumenes.append(resumen)

        return resumenes


# Instancia global del servicio (singleton)
pago_service = PagoService()
