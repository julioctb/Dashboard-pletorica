"""Servicio para la configuracion operativa de empresas."""
import logging

from app.core.exceptions import DatabaseError
from app.entities.configuracion_operativa_empresa import (
    ConfiguracionOperativaEmpresa,
    ConfiguracionOperativaEmpresaCreate,
    ConfiguracionOperativaEmpresaUpdate,
)
from app.services.direct_service import EmpresaConfigDirectService

logger = logging.getLogger(__name__)


class ConfiguracionOperativaService(
    EmpresaConfigDirectService[
        ConfiguracionOperativaEmpresa,
        ConfiguracionOperativaEmpresaCreate,
        ConfiguracionOperativaEmpresaUpdate,
    ]
):
    """Servicio de configuracion operativa de empresas (1:1)."""

    entity_cls = ConfiguracionOperativaEmpresa
    create_cls = ConfiguracionOperativaEmpresaCreate
    update_cls = ConfiguracionOperativaEmpresaUpdate
    nombre_config = "operativa"

    def __init__(self):
        super().__init__("configuracion_operativa_empresa")

    async def obtener_por_empresa(
        self, empresa_id: int
    ) -> ConfiguracionOperativaEmpresa | None:
        try:
            return await super().obtener_por_empresa(empresa_id)
        except DatabaseError:
            raise
        except Exception as e:
            logger.error(f"Error obteniendo config operativa empresa {empresa_id}: {e}")
            raise DatabaseError(f"Error obteniendo configuracion operativa: {e}")

    async def crear_o_actualizar(
        self, empresa_id: int, datos: ConfiguracionOperativaEmpresaUpdate
    ) -> ConfiguracionOperativaEmpresa:
        try:
            return await super().crear_o_actualizar(empresa_id, datos)
        except DatabaseError:
            raise
        except Exception as e:
            logger.error(f"Error en crear_o_actualizar config operativa: {e}")
            raise DatabaseError(f"Error en configuracion operativa: {e}")

    async def obtener_o_crear_default(
        self, empresa_id: int
    ) -> ConfiguracionOperativaEmpresa:
        try:
            return await super().obtener_o_crear_default(empresa_id)
        except DatabaseError:
            raise
        except Exception as e:
            logger.error(
                f"Error obteniendo default config operativa empresa {empresa_id}: {e}"
            )
            raise DatabaseError(f"Error obteniendo configuracion operativa: {e}")


configuracion_operativa_service = ConfiguracionOperativaService()
