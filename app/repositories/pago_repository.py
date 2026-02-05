"""
Repositorio de Pagos - Implementacion para Supabase.

Patron de manejo de errores:
- NotFoundError: Cuando no se encuentra un recurso
- DatabaseError: Errores de conexion o infraestructura
"""
import logging
from typing import List, Optional
from decimal import Decimal

from app.entities import Pago
from app.core.exceptions import NotFoundError, DatabaseError

logger = logging.getLogger(__name__)


class SupabasePagoRepository:
    """Implementacion del repositorio de pagos usando Supabase."""

    def __init__(self, db_manager=None):
        if db_manager is None:
            from app.database import db_manager as default_db
            db_manager = default_db

        self.supabase = db_manager.get_client()
        self.tabla = 'pagos'

    async def obtener_por_id(self, pago_id: int) -> Pago:
        """
        Obtiene un pago por su ID.

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

    async def obtener_por_contrato(
        self,
        contrato_id: int,
        limite: Optional[int] = None,
        offset: int = 0
    ) -> List[Pago]:
        """
        Obtiene todos los pagos de un contrato.

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

    async def crear(self, pago: Pago) -> Pago:
        """
        Crea un nuevo pago.

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

    async def actualizar(self, pago: Pago) -> Pago:
        """
        Actualiza un pago existente.

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

    async def eliminar(self, pago_id: int) -> bool:
        """
        Elimina un pago.

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

    async def obtener_total_pagado(self, contrato_id: int) -> Decimal:
        """
        Obtiene el total pagado de un contrato.

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

    async def obtener_ultimo_pago(self, contrato_id: int) -> Optional[Pago]:
        """
        Obtiene el ultimo pago de un contrato.

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

    async def contar_pagos(self, contrato_id: int) -> int:
        """
        Cuenta los pagos de un contrato.

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

    async def obtener_totales_por_contratos(
        self,
        contrato_ids: List[int]
    ) -> dict[int, Decimal]:
        """
        Obtiene el total pagado para multiples contratos en una sola query.

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

            totales: dict[int, Decimal] = {cid: Decimal("0") for cid in contrato_ids}
            for pago in result.data:
                cid = pago['contrato_id']
                if cid in totales:
                    totales[cid] += Decimal(str(pago['monto']))

            return totales
        except Exception as e:
            logger.error(f"Error obteniendo totales de pagos: {e}")
            raise DatabaseError(f"Error de base de datos: {str(e)}")
