"""
Servicio de validación de CURP.

Patrón Direct Access (singleton). Valida formato de CURP
y busca duplicados en la base de datos.
"""
import re
import logging
from typing import Optional

from app.database import db_manager
from app.core.validation.constants import CURP_PATTERN, CURP_LEN
from app.entities.curp_validacion import CurpValidacionResponse

logger = logging.getLogger(__name__)


class CurpService:
    """Servicio para validar CURPs contra formato y duplicados."""

    def __init__(self):
        self.supabase = db_manager.get_client()
        self.tabla = 'empleados'

    def _validar_formato(self, curp: str) -> bool:
        """Valida el formato de un CURP."""
        if not curp or len(curp) != CURP_LEN:
            return False
        return bool(re.match(CURP_PATTERN, curp))

    async def validar_curp(
        self,
        curp: str,
        excluir_empleado_id: Optional[int] = None,
    ) -> CurpValidacionResponse:
        """
        Valida un CURP: formato + búsqueda de duplicados.

        Args:
            curp: CURP a validar (se normaliza a mayúsculas).
            excluir_empleado_id: ID de empleado a excluir de búsqueda
                de duplicados (útil al editar un empleado existente).

        Returns:
            CurpValidacionResponse con resultado de la validación.
        """
        curp = curp.upper().strip()

        # 1. Validar formato
        formato_valido = self._validar_formato(curp)
        if not formato_valido:
            return CurpValidacionResponse(
                curp=curp,
                formato_valido=False,
                mensaje="CURP con formato inválido",
            )

        # 2. Buscar duplicados
        try:
            query = (
                self.supabase.table(self.tabla)
                .select('id, nombre, apellido_paterno, apellido_materno, '
                        'empresa_id, is_restricted, '
                        'empresas(nombre_comercial)')
                .eq('curp', curp)
            )

            if excluir_empleado_id:
                query = query.neq('id', excluir_empleado_id)

            result = query.execute()

            if result.data:
                emp = result.data[0]
                nombre_partes = [emp.get('nombre', ''), emp.get('apellido_paterno', '')]
                if emp.get('apellido_materno'):
                    nombre_partes.append(emp['apellido_materno'])
                nombre_completo = ' '.join(nombre_partes)

                empresa_data = emp.get('empresas')
                empresa_nombre = empresa_data.get('nombre_comercial') if empresa_data else None

                return CurpValidacionResponse(
                    curp=curp,
                    formato_valido=True,
                    duplicado=True,
                    empleado_id=emp['id'],
                    empleado_nombre=nombre_completo,
                    empresa_nombre=empresa_nombre,
                    is_restricted=emp.get('is_restricted', False),
                    mensaje="CURP ya registrado en el sistema",
                )

            return CurpValidacionResponse(
                curp=curp,
                formato_valido=True,
                duplicado=False,
                mensaje="CURP válido y disponible",
            )

        except Exception as e:
            logger.error(f"Error validando CURP {curp}: {e}")
            return CurpValidacionResponse(
                curp=curp,
                formato_valido=True,
                duplicado=False,
                mensaje=f"CURP con formato válido (no se pudo verificar duplicados: {e})",
            )


# Singleton
curp_service = CurpService()
