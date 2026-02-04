"""
Servicio de aplicacion para gestion de pagos de contratos.

Usa SupabasePagoRepository para operaciones de datos de pagos
y SupabaseContratoRepository para operaciones de contratos.
"""
import logging
from typing import List, Optional
from decimal import Decimal

from app.entities import (
    Pago,
    PagoCreate,
    PagoUpdate,
    ResumenPagosContrato,
    EstatusContrato,
)
from app.repositories import SupabaseContratoRepository, SupabasePagoRepository
from app.core.exceptions import NotFoundError, BusinessRuleError

logger = logging.getLogger(__name__)


class PagoService:
    """
    Servicio de aplicacion para pagos.
    Orquesta las operaciones de negocio delegando acceso a datos a los repositorios.
    """

    def __init__(self, contrato_repository=None, pago_repository=None):
        if contrato_repository is None:
            contrato_repository = SupabaseContratoRepository()
        self.contrato_repository = contrato_repository

        if pago_repository is None:
            pago_repository = SupabasePagoRepository()
        self.repository = pago_repository

    # ==========================================
    # OPERACIONES CRUD (publicas)
    # ==========================================

    async def obtener_por_id(self, pago_id: int) -> Pago:
        """
        Obtiene un pago por su ID.

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

        Raises:
            DatabaseError: Si hay error de BD
        """
        return await self.repository.obtener_por_contrato(contrato_id, limite, offset)

    async def crear(self, pago_create: PagoCreate) -> Pago:
        """
        Crea un nuevo pago.

        Raises:
            NotFoundError: Si el contrato no existe
            BusinessRuleError: Si el contrato no puede recibir pagos
            DatabaseError: Si hay error de BD
        """
        contrato = await self.contrato_repository.obtener_por_id(pago_create.contrato_id)

        if contrato.estatus not in [EstatusContrato.ACTIVO, EstatusContrato.BORRADOR]:
            raise BusinessRuleError(
                f"No se pueden registrar pagos en un contrato con estatus {contrato.estatus}"
            )

        pago = Pago(**pago_create.model_dump())
        return await self.repository.crear(pago)

    async def actualizar(self, pago_id: int, pago_update: PagoUpdate) -> Pago:
        """
        Actualiza un pago existente.

        Raises:
            NotFoundError: Si el pago no existe
            DatabaseError: Si hay error de BD
        """
        pago_actual = await self.repository.obtener_por_id(pago_id)

        datos_actualizados = pago_actual.model_dump()
        for campo, valor in pago_update.model_dump(exclude_unset=True).items():
            if valor is not None:
                datos_actualizados[campo] = valor

        pago_modificado = Pago(**datos_actualizados)
        return await self.repository.actualizar(pago_modificado)

    async def eliminar(self, pago_id: int) -> bool:
        """
        Elimina un pago.

        Raises:
            NotFoundError: Si el pago no existe
            DatabaseError: Si hay error de BD
        """
        await self.repository.obtener_por_id(pago_id)
        return await self.repository.eliminar(pago_id)

    # ==========================================
    # RESUMEN DE PAGOS
    # ==========================================

    async def obtener_resumen_pagos_contrato(self, contrato_id: int) -> ResumenPagosContrato:
        """
        Obtiene el resumen de pagos de un contrato.

        Raises:
            NotFoundError: Si el contrato no existe
            DatabaseError: Si hay error de BD
        """
        contrato = await self.contrato_repository.obtener_por_id(contrato_id)

        total_pagado = await self.repository.obtener_total_pagado(contrato_id)
        cantidad_pagos = await self.repository.contar_pagos(contrato_id)
        ultimo_pago = await self.repository.obtener_ultimo_pago(contrato_id)

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

    async def obtener_saldos_pendientes_batch(
        self,
        contratos_info: List[dict]
    ) -> dict[int, Decimal]:
        """
        Obtiene los saldos pendientes de multiples contratos en una sola query.

        Raises:
            DatabaseError: Si hay error de BD
        """
        if not contratos_info:
            return {}

        contrato_ids = [c['id'] for c in contratos_info]
        montos_maximos = {c['id']: Decimal(str(c.get('monto_maximo') or 0)) for c in contratos_info}

        totales_pagados = await self.repository.obtener_totales_por_contratos(contrato_ids)

        saldos = {}
        for cid in contrato_ids:
            monto_maximo = montos_maximos.get(cid, Decimal("0"))
            total_pagado = totales_pagados.get(cid, Decimal("0"))
            saldos[cid] = max(monto_maximo - total_pagado, Decimal("0"))

        return saldos

    async def verificar_contrato_pagado(self, contrato_id: int) -> bool:
        """
        Verifica si un contrato esta completamente pagado.
        """
        resumen = await self.obtener_resumen_pagos_contrato(contrato_id)
        return resumen.esta_pagado

    # ==========================================
    # OPERACIONES DE CIERRE
    # ==========================================

    async def cerrar_contrato(self, contrato_id: int, forzar: bool = False) -> bool:
        """
        Cierra un contrato si esta completamente pagado.

        Raises:
            NotFoundError: Si el contrato no existe
            BusinessRuleError: Si no esta pagado y no se fuerza
            DatabaseError: Si hay error de BD
        """
        contrato = await self.contrato_repository.obtener_por_id(contrato_id)

        if contrato.estatus == EstatusContrato.CERRADO:
            raise BusinessRuleError("El contrato ya esta cerrado")

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

        await self.contrato_repository.cambiar_estatus(contrato_id, EstatusContrato.CERRADO)
        return True


# Instancia global del servicio (singleton)
pago_service = PagoService()
