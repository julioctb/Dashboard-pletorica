"""Servicio para la configuración fiscal/patronal de empresas."""
import logging

from app.core.exceptions import DatabaseError
from app.entities.configuracion_fiscal_empresa import (
    ConfiguracionFiscalEmpresa,
    ConfiguracionFiscalEmpresaCreate,
    ConfiguracionFiscalEmpresaUpdate,
)
from app.services.direct_service import EmpresaConfigDirectService

logger = logging.getLogger(__name__)


class ConfiguracionFiscalService(
    EmpresaConfigDirectService[
        ConfiguracionFiscalEmpresa,
        ConfiguracionFiscalEmpresaCreate,
        ConfiguracionFiscalEmpresaUpdate,
    ]
):
    """Servicio de configuración fiscal de empresas (1:1)."""

    entity_cls = ConfiguracionFiscalEmpresa
    create_cls = ConfiguracionFiscalEmpresaCreate
    update_cls = ConfiguracionFiscalEmpresaUpdate
    nombre_config = "fiscal"

    def __init__(self):
        super().__init__("configuracion_fiscal_empresa")

    async def obtener_por_empresa(self, empresa_id: int) -> ConfiguracionFiscalEmpresa | None:
        try:
            return await super().obtener_por_empresa(empresa_id)
        except DatabaseError:
            raise
        except Exception as e:
            logger.error(f"Error obteniendo config fiscal empresa {empresa_id}: {e}")
            raise DatabaseError(f"Error obteniendo configuración fiscal: {e}")

    async def crear_o_actualizar(
        self, empresa_id: int, datos: ConfiguracionFiscalEmpresaUpdate
    ) -> ConfiguracionFiscalEmpresa:
        try:
            return await super().crear_o_actualizar(empresa_id, datos)
        except DatabaseError:
            raise
        except Exception as e:
            logger.error(f"Error en crear_o_actualizar config fiscal: {e}")
            raise DatabaseError(f"Error en configuración fiscal: {e}")

    async def obtener_o_crear_default(self, empresa_id: int) -> ConfiguracionFiscalEmpresa:
        try:
            return await super().obtener_o_crear_default(empresa_id)
        except DatabaseError:
            raise
        except Exception as e:
            logger.error(f"Error obteniendo default config fiscal empresa {empresa_id}: {e}")
            raise DatabaseError(f"Error obteniendo configuración fiscal: {e}")


configuracion_fiscal_service = ConfiguracionFiscalService()
