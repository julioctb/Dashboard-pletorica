"""
Servicio para la configuracion operativa de empresas.

Patron Direct Access con upsert (relacion 1:1 con empresa).
"""
import logging
from typing import Optional

from app.database import db_manager
from app.core.exceptions import DatabaseError, NotFoundError
from app.entities.configuracion_operativa_empresa import (
    ConfiguracionOperativaEmpresa,
    ConfiguracionOperativaEmpresaCreate,
    ConfiguracionOperativaEmpresaUpdate,
)

logger = logging.getLogger(__name__)


class ConfiguracionOperativaService:
    """Servicio de configuracion operativa de empresas (1:1)."""

    def __init__(self):
        self.supabase = db_manager.get_client()
        self.tabla = 'configuracion_operativa_empresa'

    async def obtener_por_empresa(
        self, empresa_id: int
    ) -> Optional[ConfiguracionOperativaEmpresa]:
        """
        Obtiene la configuracion operativa de una empresa.

        Returns:
            ConfiguracionOperativaEmpresa o None si no existe.

        Raises:
            DatabaseError: Si hay error de BD.
        """
        try:
            result = (
                self.supabase.table(self.tabla)
                .select('*')
                .eq('empresa_id', empresa_id)
                .execute()
            )

            if not result.data:
                return None

            return ConfiguracionOperativaEmpresa(**result.data[0])

        except Exception as e:
            logger.error(f"Error obteniendo config operativa empresa {empresa_id}: {e}")
            raise DatabaseError(f"Error obteniendo configuracion operativa: {e}")

    async def crear_o_actualizar(
        self, empresa_id: int, datos: ConfiguracionOperativaEmpresaUpdate
    ) -> ConfiguracionOperativaEmpresa:
        """
        Crea o actualiza la configuracion operativa de una empresa.

        Si ya existe, actualiza los campos proporcionados.
        Si no existe, crea con los valores proporcionados + defaults.

        Returns:
            ConfiguracionOperativaEmpresa actualizada/creada.

        Raises:
            DatabaseError: Si hay error de BD.
        """
        try:
            existente = await self.obtener_por_empresa(empresa_id)

            if existente:
                # Actualizar solo campos no-None
                payload = datos.model_dump(mode='json', exclude_none=True)
                if not payload:
                    return existente

                result = (
                    self.supabase.table(self.tabla)
                    .update(payload)
                    .eq('empresa_id', empresa_id)
                    .execute()
                )

                if not result.data:
                    raise DatabaseError("No se pudo actualizar la configuracion operativa")

                return ConfiguracionOperativaEmpresa(**result.data[0])
            else:
                # Crear nueva con defaults + valores proporcionados
                create_data = ConfiguracionOperativaEmpresaCreate(
                    empresa_id=empresa_id,
                    **(datos.model_dump(exclude_none=True)),
                )
                payload = create_data.model_dump(mode='json')
                result = self.supabase.table(self.tabla).insert(payload).execute()

                if not result.data:
                    raise DatabaseError("No se pudo crear la configuracion operativa")

                return ConfiguracionOperativaEmpresa(**result.data[0])

        except DatabaseError:
            raise
        except Exception as e:
            logger.error(f"Error en crear_o_actualizar config operativa: {e}")
            raise DatabaseError(f"Error en configuracion operativa: {e}")

    async def obtener_o_crear_default(
        self, empresa_id: int
    ) -> ConfiguracionOperativaEmpresa:
        """
        Obtiene la configuracion existente o crea una con valores default.

        Returns:
            ConfiguracionOperativaEmpresa (existente o nueva con defaults).

        Raises:
            DatabaseError: Si hay error de BD.
        """
        existente = await self.obtener_por_empresa(empresa_id)
        if existente:
            return existente

        return await self.crear_o_actualizar(
            empresa_id,
            ConfiguracionOperativaEmpresaUpdate(),
        )


configuracion_operativa_service = ConfiguracionOperativaService()
