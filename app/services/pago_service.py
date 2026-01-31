"""
Servicio de aplicación para gestión de pagos de contratos.

Accede directamente a Supabase para operaciones de pagos (sin repositorio intermedio).
Usa SupabaseContratoRepository para operaciones de contratos.
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
from app.repositories import SupabaseContratoRepository
from app.database import db_manager
from app.core.exceptions import NotFoundError, DatabaseError, BusinessRuleError

logger = logging.getLogger(__name__)


class PagoService:
    """
    Servicio de aplicación para pagos.
    Orquesta las operaciones de negocio.
    Accede directamente a Supabase para operaciones CRUD de pagos.
    """

    def __init__(self, contrato_repository=None):
        """
        Inicializa el servicio.

        Args:
            contrato_repository: Implementación del repository de contratos.
        """
        self.supabase = db_manager.get_client()
        self.tabla = "pagos"

        if contrato_repository is None:
            contrato_repository = SupabaseContratoRepository()
        self.contrato_repository = contrato_repository

    # ==========================================
    # OPERACIONES DE ACCESO A DATOS (inline)
    # ==========================================

    async def _obtener_por_id(self, pago_id: int) -> Pago:
        """
        Obtiene un pago por su ID desde Supabase.

        Args:
            pago_id: ID del pago a buscar

        Returns:
            Pago encontrado

        Raises:
            NotFoundError: Si el pago no existe
            DatabaseError: Si hay error de conexion
        """
        try:
            result = self.supabase.table(self.tabla).select('*').eq('id', pago_id).execute()
            if not result.data:
                raise NotFoundError(f"Pago con ID {pago_id} no encontrado")
            return Pago(**result.data[0])
        except NotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error obteniendo pago {pago_id}: {e}")
            raise DatabaseError(f"Error de base de datos al obtener pago: {str(e)}")

    async def _obtener_por_contrato(
        self,
        contrato_id: int,
        limite: Optional[int] = None,
        offset: int = 0
    ) -> List[Pago]:
        """
        Obtiene todos los pagos de un contrato desde Supabase.

        Args:
            contrato_id: ID del contrato
            limite: Numero maximo de resultados
            offset: Registros a saltar

        Returns:
            Lista de pagos del contrato

        Raises:
            DatabaseError: Si hay error de conexion
        """
        try:
            query = self.supabase.table(self.tabla)\
                .select('*')\
                .eq('contrato_id', contrato_id)\
                .order('fecha_pago', desc=True)

            if limite:
                query = query.range(offset, offset + limite - 1)

            result = query.execute()
            return [Pago(**data) for data in result.data]
        except Exception as e:
            logger.error(f"Error obteniendo pagos del contrato {contrato_id}: {e}")
            raise DatabaseError(f"Error de base de datos: {str(e)}")

    async def _crear_pago(self, pago: Pago) -> Pago:
        """
        Crea un nuevo pago en Supabase.

        Args:
            pago: Pago a crear

        Returns:
            Pago creado con ID asignado

        Raises:
            DatabaseError: Si hay error de conexion
        """
        try:
            datos = pago.model_dump(mode='json', exclude={'id', 'fecha_creacion', 'fecha_actualizacion'})
            result = self.supabase.table(self.tabla).insert(datos).execute()

            if not result.data:
                raise DatabaseError("No se pudo crear el pago (sin respuesta de BD)")

            return Pago(**result.data[0])
        except DatabaseError:
            raise
        except Exception as e:
            logger.error(f"Error creando pago: {e}")
            raise DatabaseError(f"Error de base de datos al crear pago: {str(e)}")

    async def _actualizar_pago(self, pago: Pago) -> Pago:
        """
        Actualiza un pago existente en Supabase.

        Args:
            pago: Pago con datos actualizados

        Returns:
            Pago actualizado

        Raises:
            NotFoundError: Si el pago no existe
            DatabaseError: Si hay error de conexion
        """
        try:
            datos = pago.model_dump(mode='json', exclude={'id', 'fecha_creacion', 'fecha_actualizacion'})
            result = self.supabase.table(self.tabla)\
                .update(datos)\
                .eq('id', pago.id)\
                .execute()

            if not result.data:
                raise NotFoundError(f"Pago con ID {pago.id} no encontrado")

            return Pago(**result.data[0])
        except NotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error actualizando pago {pago.id}: {e}")
            raise DatabaseError(f"Error de base de datos al actualizar pago: {str(e)}")

    async def _eliminar_pago(self, pago_id: int) -> bool:
        """
        Elimina un pago de Supabase.

        Args:
            pago_id: ID del pago a eliminar

        Returns:
            True si se elimino exitosamente

        Raises:
            DatabaseError: Si hay error de conexion
        """
        try:
            result = self.supabase.table(self.tabla)\
                .delete()\
                .eq('id', pago_id)\
                .execute()
            return bool(result.data)
        except Exception as e:
            logger.error(f"Error eliminando pago {pago_id}: {e}")
            raise DatabaseError(f"Error de base de datos: {str(e)}")

    async def _obtener_total_pagado(self, contrato_id: int) -> Decimal:
        """
        Obtiene el total pagado de un contrato.

        Args:
            contrato_id: ID del contrato

        Returns:
            Suma total de los pagos

        Raises:
            DatabaseError: Si hay error de conexion
        """
        try:
            result = self.supabase.table(self.tabla)\
                .select('monto')\
                .eq('contrato_id', contrato_id)\
                .execute()

            if not result.data:
                return Decimal("0")

            total = sum(Decimal(str(p['monto'])) for p in result.data)
            return total
        except Exception as e:
            logger.error(f"Error obteniendo total pagado del contrato {contrato_id}: {e}")
            raise DatabaseError(f"Error de base de datos: {str(e)}")

    async def _obtener_ultimo_pago(self, contrato_id: int) -> Optional[Pago]:
        """
        Obtiene el ultimo pago de un contrato.

        Args:
            contrato_id: ID del contrato

        Returns:
            Ultimo pago o None si no hay pagos

        Raises:
            DatabaseError: Si hay error de conexion
        """
        try:
            result = self.supabase.table(self.tabla)\
                .select('*')\
                .eq('contrato_id', contrato_id)\
                .order('fecha_pago', desc=True)\
                .limit(1)\
                .execute()

            if not result.data:
                return None

            return Pago(**result.data[0])
        except Exception as e:
            logger.error(f"Error obteniendo ultimo pago del contrato {contrato_id}: {e}")
            raise DatabaseError(f"Error de base de datos: {str(e)}")

    async def _contar_pagos(self, contrato_id: int) -> int:
        """
        Cuenta los pagos de un contrato.

        Args:
            contrato_id: ID del contrato

        Returns:
            Numero de pagos

        Raises:
            DatabaseError: Si hay error de conexion
        """
        try:
            result = self.supabase.table(self.tabla)\
                .select('id', count='exact')\
                .eq('contrato_id', contrato_id)\
                .execute()

            return result.count or 0
        except Exception as e:
            logger.error(f"Error contando pagos del contrato {contrato_id}: {e}")
            raise DatabaseError(f"Error de base de datos: {str(e)}")

    async def _obtener_totales_por_contratos(
        self,
        contrato_ids: List[int]
    ) -> dict[int, Decimal]:
        """
        Obtiene el total pagado para multiples contratos en una sola query.

        Args:
            contrato_ids: Lista de IDs de contratos

        Returns:
            Diccionario {contrato_id: total_pagado}

        Raises:
            DatabaseError: Si hay error de conexion
        """
        if not contrato_ids:
            return {}

        try:
            result = self.supabase.table(self.tabla)\
                .select('contrato_id, monto')\
                .in_('contrato_id', contrato_ids)\
                .execute()

            # Agrupar por contrato_id y sumar
            totales: dict[int, Decimal] = {cid: Decimal("0") for cid in contrato_ids}
            for pago in result.data:
                cid = pago['contrato_id']
                if cid in totales:
                    totales[cid] += Decimal(str(pago['monto']))

            return totales
        except Exception as e:
            logger.error(f"Error obteniendo totales de pagos: {e}")
            raise DatabaseError(f"Error de base de datos: {str(e)}")

    # ==========================================
    # OPERACIONES CRUD (publicas)
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
        return await self._obtener_por_id(pago_id)

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
            limite: Numero maximo de resultados
            offset: Registros a saltar

        Returns:
            Lista de pagos del contrato

        Raises:
            DatabaseError: Si hay error de BD
        """
        return await self._obtener_por_contrato(contrato_id, limite, offset)

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
        return await self._crear_pago(pago)

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
        pago_actual = await self._obtener_por_id(pago_id)

        # Aplicar actualizaciones
        datos_actualizados = pago_actual.model_dump()
        for campo, valor in pago_update.model_dump(exclude_unset=True).items():
            if valor is not None:
                datos_actualizados[campo] = valor

        pago_modificado = Pago(**datos_actualizados)
        return await self._actualizar_pago(pago_modificado)

    async def eliminar(self, pago_id: int) -> bool:
        """
        Elimina un pago.

        Args:
            pago_id: ID del pago a eliminar

        Returns:
            True si se elimino exitosamente

        Raises:
            NotFoundError: Si el pago no existe
            DatabaseError: Si hay error de BD
        """
        # Verificar que existe
        await self._obtener_por_id(pago_id)
        return await self._eliminar_pago(pago_id)

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
        total_pagado = await self._obtener_total_pagado(contrato_id)
        cantidad_pagos = await self._contar_pagos(contrato_id)
        ultimo_pago = await self._obtener_ultimo_pago(contrato_id)

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

    async def obtener_saldos_pendientes_batch(
        self,
        contratos_info: List[dict]
    ) -> dict[int, Decimal]:
        """
        Obtiene los saldos pendientes de multiples contratos en una sola query.

        Args:
            contratos_info: Lista de dicts con {id, monto_maximo}

        Returns:
            Diccionario {contrato_id: saldo_pendiente}

        Raises:
            DatabaseError: Si hay error de BD
        """
        if not contratos_info:
            return {}

        contrato_ids = [c['id'] for c in contratos_info]
        montos_maximos = {c['id']: Decimal(str(c.get('monto_maximo') or 0)) for c in contratos_info}

        # Una sola query para todos los totales pagados
        totales_pagados = await self._obtener_totales_por_contratos(contrato_ids)

        # Calcular saldos pendientes
        saldos = {}
        for cid in contrato_ids:
            monto_maximo = montos_maximos.get(cid, Decimal("0"))
            total_pagado = totales_pagados.get(cid, Decimal("0"))
            saldos[cid] = max(monto_maximo - total_pagado, Decimal("0"))

        return saldos

    async def verificar_contrato_pagado(self, contrato_id: int) -> bool:
        """
        Verifica si un contrato esta completamente pagado.

        Args:
            contrato_id: ID del contrato

        Returns:
            True si el contrato esta completamente pagado
        """
        resumen = await self.obtener_resumen_pagos_contrato(contrato_id)
        return resumen.esta_pagado

    # ==========================================
    # OPERACIONES DE CIERRE
    # ==========================================

    async def cerrar_contrato(self, contrato_id: int, forzar: bool = False) -> bool:
        """
        Cierra un contrato si esta completamente pagado.

        Args:
            contrato_id: ID del contrato
            forzar: Si True, cierra aunque no este completamente pagado

        Returns:
            True si se cerro exitosamente

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

        # Cambiar estatus a CERRADO
        await self.contrato_repository.cambiar_estatus(contrato_id, EstatusContrato.CERRADO)
        return True


# Instancia global del servicio (singleton)
pago_service = PagoService()
