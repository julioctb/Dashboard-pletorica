"""
Base Service - Helpers comunes para services con repository.

Proporciona:
- _merge_y_actualizar: Patron fetch -> merge exclude_unset -> entidad actualizada
- _cambiar_estatus: Patron activar/desactivar generico
"""
import logging

from app.core.exceptions import BusinessRuleError

logger = logging.getLogger(__name__)


class BaseService:
    """Helpers comunes para services que usan un repository."""

    async def _merge_y_actualizar(self, entity_id, update_model, repo):
        """
        Patron: fetch -> merge exclude_unset -> retorna entidad mergeada.

        El service que llama debe luego validar unicidad y llamar
        repo.actualizar_entidad() con la entidad retornada.

        Args:
            entity_id: ID de la entidad a actualizar
            update_model: Pydantic model con campos a actualizar (exclude_unset)
            repo: Repositorio con metodo obtener_por_id

        Returns:
            Entidad con campos mergeados (sin persistir aun)
        """
        entidad = await repo.obtener_por_id(entity_id)
        datos = update_model.model_dump(exclude_unset=True)
        for campo, valor in datos.items():
            if valor is not None:
                setattr(entidad, campo, valor)
        return entidad

    async def _cambiar_estatus(self, entity_id, nuevo_estatus, repo, nombre_entidad):
        """
        Patron activar/desactivar generico.

        Args:
            entity_id: ID de la entidad
            nuevo_estatus: Estatus destino (ej: Estatus.ACTIVO)
            repo: Repositorio con obtener_por_id y actualizar_entidad
            nombre_entidad: Nombre para mensajes de error

        Returns:
            Entidad actualizada

        Raises:
            BusinessRuleError: Si ya tiene el estatus destino
        """
        entidad = await repo.obtener_por_id(entity_id)

        # Comparar como string para compatibilidad con enums y strings
        estatus_actual = str(entidad.estatus)
        estatus_nuevo = str(nuevo_estatus)

        if estatus_actual == estatus_nuevo:
            raise BusinessRuleError(
                f"{nombre_entidad} ya tiene estatus {estatus_nuevo}"
            )

        entidad.estatus = nuevo_estatus
        return await repo.actualizar_entidad(entidad)
