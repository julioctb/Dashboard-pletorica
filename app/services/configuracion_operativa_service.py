"""Servicio para la configuracion operativa de empresas."""
import logging

from app.core.enums import EstatusContrato
from app.core.exceptions import BusinessRuleError, DatabaseError
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
            if datos.contrato_nomina_id is not None:
                await self._validar_contrato_nomina(empresa_id, datos.contrato_nomina_id)
            return await super().crear_o_actualizar(empresa_id, datos)
        except (BusinessRuleError, DatabaseError):
            raise
        except ValueError as e:
            raise BusinessRuleError(str(e))
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

    async def listar_contratos_nomina_disponibles(self, empresa_id: int) -> list[dict]:
        """Contratos activos con personal disponibles para ser contrato base."""
        try:
            from app.services import contrato_service

            contratos = await contrato_service.obtener_por_empresa(
                empresa_id,
                incluir_inactivos=False,
            )
            disponibles = [
                contrato
                for contrato in contratos
                if contrato.estatus == EstatusContrato.ACTIVO.value
                and bool(contrato.tiene_personal)
            ]
            return [
                {
                    "value": str(contrato.id),
                    "label": f"{contrato.codigo} - {contrato.descripcion_objeto or 'Contrato activo'}",
                }
                for contrato in disponibles
            ]
        except DatabaseError:
            raise
        except Exception as e:
            logger.error(
                "Error listando contratos de nomina de empresa %s: %s",
                empresa_id,
                e,
            )
            raise DatabaseError(f"Error listando contratos de nomina: {e}")

    async def validar_contrato_nomina(self, empresa_id: int, contrato_id: int) -> None:
        await self._validar_contrato_nomina(empresa_id, contrato_id)

    async def _validar_contrato_nomina(self, empresa_id: int, contrato_id: int) -> None:
        """Valida pertenencia, estatus y alcance del contrato base de nomina."""
        from app.services import contrato_service

        contrato = await contrato_service.obtener_por_id(contrato_id)
        if int(contrato.empresa_id or 0) != int(empresa_id):
            raise BusinessRuleError(
                "El contrato base de nomina debe pertenecer a la empresa activa."
            )
        if contrato.estatus != EstatusContrato.ACTIVO.value:
            raise BusinessRuleError(
                "El contrato base de nomina debe estar activo."
            )
        if not contrato.tiene_personal:
            raise BusinessRuleError(
                "El contrato base de nomina debe tener personal habilitado."
            )


configuracion_operativa_service = ConfiguracionOperativaService()
