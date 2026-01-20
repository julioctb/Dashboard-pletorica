"""
Repositorio de Pagos - Interface y implementación para Supabase.

Patrón de manejo de errores:
- NotFoundError: Cuando no se encuentra un recurso
- DuplicateError: Cuando se viola unicidad
- DatabaseError: Errores de conexión o infraestructura
- Propagar otras excepciones hacia arriba
"""
from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import date
from decimal import Decimal
import logging

from app.entities import Pago, PagoResumen
from app.core.exceptions import NotFoundError, DatabaseError

logger = logging.getLogger(__name__)


class IPagoRepository(ABC):
    """Interface del repositorio de pagos"""

    @abstractmethod
    async def obtener_por_id(self, pago_id: int) -> Pago:
        """Obtiene un pago por su ID"""
        pass

    @abstractmethod
    async def obtener_por_contrato(
        self,
        contrato_id: int,
        limite: Optional[int] = None,
        offset: int = 0
    ) -> List[Pago]:
        """Obtiene todos los pagos de un contrato"""
        pass

    @abstractmethod
    async def crear(self, pago: Pago) -> Pago:
        """Crea un nuevo pago"""
        pass

    @abstractmethod
    async def actualizar(self, pago: Pago) -> Pago:
        """Actualiza un pago existente"""
        pass

    @abstractmethod
    async def eliminar(self, pago_id: int) -> bool:
        """Elimina un pago"""
        pass

    @abstractmethod
    async def obtener_total_pagado(self, contrato_id: int) -> Decimal:
        """Obtiene el total pagado de un contrato"""
        pass

    @abstractmethod
    async def obtener_ultimo_pago(self, contrato_id: int) -> Optional[Pago]:
        """Obtiene el último pago de un contrato"""
        pass

    @abstractmethod
    async def contar_pagos(self, contrato_id: int) -> int:
        """Cuenta los pagos de un contrato"""
        pass


class SupabasePagoRepository(IPagoRepository):
    """Implementación del repositorio usando Supabase"""

    def __init__(self, db_manager=None):
        """
        Inicializa el repositorio con un cliente de Supabase.

        Args:
            db_manager: Gestor de base de datos. Si es None, se importa el global.
        """
        if db_manager is None:
            from app.database import db_manager as default_db
            db_manager = default_db

        self.supabase = db_manager.get_client()
        self.tabla = 'pagos'

    async def obtener_por_id(self, pago_id: int) -> Pago:
        """
        Obtiene un pago por su ID.

        Args:
            pago_id: ID del pago a buscar

        Returns:
            Pago encontrado

        Raises:
            NotFoundError: Si el pago no existe
            DatabaseError: Si hay error de conexión
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

        Args:
            contrato_id: ID del contrato
            limite: Número máximo de resultados
            offset: Registros a saltar

        Returns:
            Lista de pagos del contrato

        Raises:
            DatabaseError: Si hay error de conexión
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

        Args:
            pago: Pago a crear

        Returns:
            Pago creado con ID asignado

        Raises:
            DatabaseError: Si hay error de conexión
        """
        try:
            datos = pago.model_dump(mode='json', exclude={'id', 'fecha_creacion', 'fecha_actualizacion'})
            result = self.supabase.table(self.tabla).insert(datos).execute()

            if not result.data:
                raise DatabaseError("No se pudo crear el pago (sin respuesta de BD)")

            return Pago(**result.data[0])
        except Exception as e:
            logger.error(f"Error creando pago: {e}")
            raise DatabaseError(f"Error de base de datos al crear pago: {str(e)}")

    async def actualizar(self, pago: Pago) -> Pago:
        """
        Actualiza un pago existente.

        Args:
            pago: Pago con datos actualizados

        Returns:
            Pago actualizado

        Raises:
            NotFoundError: Si el pago no existe
            DatabaseError: Si hay error de conexión
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

        Args:
            pago_id: ID del pago a eliminar

        Returns:
            True si se eliminó exitosamente

        Raises:
            DatabaseError: Si hay error de conexión
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

        Args:
            contrato_id: ID del contrato

        Returns:
            Suma total de los pagos

        Raises:
            DatabaseError: Si hay error de conexión
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
        Obtiene el último pago de un contrato.

        Args:
            contrato_id: ID del contrato

        Returns:
            Último pago o None si no hay pagos

        Raises:
            DatabaseError: Si hay error de conexión
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
            logger.error(f"Error obteniendo último pago del contrato {contrato_id}: {e}")
            raise DatabaseError(f"Error de base de datos: {str(e)}")

    async def contar_pagos(self, contrato_id: int) -> int:
        """
        Cuenta los pagos de un contrato.

        Args:
            contrato_id: ID del contrato

        Returns:
            Número de pagos

        Raises:
            DatabaseError: Si hay error de conexión
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
            fecha_desde: Fecha inicial del rango
            fecha_hasta: Fecha final del rango

        Returns:
            Lista de pagos en el rango

        Raises:
            DatabaseError: Si hay error de conexión
        """
        try:
            query = self.supabase.table(self.tabla)\
                .select('*')\
                .eq('contrato_id', contrato_id)

            if fecha_desde:
                query = query.gte('fecha_pago', fecha_desde.isoformat())
            if fecha_hasta:
                query = query.lte('fecha_pago', fecha_hasta.isoformat())

            query = query.order('fecha_pago', desc=True)
            result = query.execute()

            return [Pago(**data) for data in result.data]
        except Exception as e:
            logger.error(f"Error buscando pagos por fechas: {e}")
            raise DatabaseError(f"Error de base de datos: {str(e)}")
