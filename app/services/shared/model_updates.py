"""Helpers compartidos para mutaciones parciales sobre entidades."""

from __future__ import annotations

from typing import Any, TypeVar

TEntity = TypeVar("TEntity")


def merge_update_model(entity: TEntity, update_model: Any) -> TEntity:
    """Aplica un update parcial sin sobrescribir valores existentes con `None`.

    Para modelos Pydantic, reconstruye la entidad completa en una sola validación
    para evitar estados intermedios inválidos al asignar campo por campo.
    """

    cambios = {
        campo: valor
        for campo, valor in update_model.model_dump(exclude_unset=True).items()
        if valor is not None
    }

    if not cambios:
        return entity

    if hasattr(entity, "model_dump"):
        datos = entity.model_dump(mode="python")
        datos.update(cambios)
        return type(entity)(**datos)

    for campo, valor in cambios.items():
        setattr(entity, campo, valor)
    return entity
