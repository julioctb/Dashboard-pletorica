"""
Servicio para el historial de cambios bancarios de empleados.

Patron Direct Access, insert-only (inmutable).
Solo se insertan registros, nunca se modifican ni eliminan.
"""
import logging
from typing import List

from app.database import db_manager
from app.core.exceptions import DatabaseError
from app.entities.cuenta_bancaria_historial import (
    CuentaBancariaHistorial,
    CuentaBancariaHistorialCreate,
)

logger = logging.getLogger(__name__)


class CuentaBancariaHistorialService:
    """Servicio de historial de cambios bancarios (insert-only)."""

    def __init__(self):
        self.supabase = db_manager.get_client()
        self.tabla = 'cuenta_bancaria_historial'

    async def registrar_cambio(
        self, datos: CuentaBancariaHistorialCreate
    ) -> CuentaBancariaHistorial:
        """
        Registra un cambio de datos bancarios.

        Args:
            datos: Datos del cambio bancario a registrar.

        Returns:
            CuentaBancariaHistorial creado.

        Raises:
            DatabaseError: Si hay error de BD.
        """
        try:
            payload = datos.model_dump(mode='json', exclude_none=True)
            result = self.supabase.table(self.tabla).insert(payload).execute()

            if not result.data:
                raise DatabaseError("No se pudo registrar el cambio bancario")

            return CuentaBancariaHistorial(**result.data[0])

        except DatabaseError:
            raise
        except Exception as e:
            logger.error(f"Error registrando cambio bancario: {e}")
            raise DatabaseError(f"Error registrando cambio bancario: {e}")

    async def obtener_historial(
        self, empleado_id: int, limite: int = 50
    ) -> List[CuentaBancariaHistorial]:
        """
        Obtiene el historial de cambios bancarios de un empleado.

        Args:
            empleado_id: ID del empleado.
            limite: Maximo de registros a retornar.

        Returns:
            Lista de cambios bancarios ordenados por fecha descendente.

        Raises:
            DatabaseError: Si hay error de BD.
        """
        try:
            result = (
                self.supabase.table(self.tabla)
                .select('*')
                .eq('empleado_id', empleado_id)
                .order('fecha_cambio', desc=True)
                .limit(limite)
                .execute()
            )

            return [CuentaBancariaHistorial(**r) for r in (result.data or [])]

        except Exception as e:
            logger.error(f"Error obteniendo historial bancario: {e}")
            raise DatabaseError(f"Error obteniendo historial bancario: {e}")


cuenta_bancaria_historial_service = CuentaBancariaHistorialService()
