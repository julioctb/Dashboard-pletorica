"""Helpers base para servicios con acceso directo a Supabase."""

from __future__ import annotations

from typing import Any, Generic, Iterable, Optional, TypeVar

from app.database import db_manager

TEntity = TypeVar("TEntity")
TCreate = TypeVar("TCreate")
TUpdate = TypeVar("TUpdate")


class DirectSupabaseService:
    """Base mínima para reducir repetición en servicios directos."""

    def __init__(self, tabla: str):
        self.supabase = db_manager.get_client()
        self.tabla = tabla

    def _query(self, select: str = "*"):
        return self.supabase.table(self.tabla).select(select)

    @staticmethod
    def _apply_filters(query, filters: dict[str, Any] | None = None):
        for campo, valor in (filters or {}).items():
            query = query.eq(campo, valor)
        return query

    @staticmethod
    def _build_entity(entity_cls, data: dict[str, Any]):
        return entity_cls(**data)

    def _build_entities(self, entity_cls, rows: Iterable[dict[str, Any]]):
        return [self._build_entity(entity_cls, row) for row in rows]

    def _fetch_one(
        self,
        entity_cls,
        *,
        filters: dict[str, Any],
        not_found_message: str | None = None,
    ):
        result = self._apply_filters(self._query(), filters).limit(1).execute()
        if not result.data:
            if not_found_message:
                raise ValueError(not_found_message)
            return None
        return self._build_entity(entity_cls, result.data[0])

    def _fetch_many(self, entity_cls, query):
        result = query.execute()
        return self._build_entities(entity_cls, result.data or [])

    @staticmethod
    def _merge_update_model(entity, update_model):
        for campo, valor in update_model.model_dump(exclude_unset=True).items():
            if valor is not None:
                setattr(entity, campo, valor)
        return entity

    def _insert_row(self, payload: dict[str, Any]):
        return self.supabase.table(self.tabla).insert(payload).execute()

    def _update_rows(self, payload: dict[str, Any], *, filters: dict[str, Any]):
        query = self.supabase.table(self.tabla).update(payload)
        query = self._apply_filters(query, filters)
        return query.execute()


class EmpresaConfigDirectService(
    DirectSupabaseService,
    Generic[TEntity, TCreate, TUpdate],
):
    """Base para configuraciones singleton 1:1 asociadas a empresa."""

    entity_cls: type[TEntity]
    create_cls: type[TCreate]
    update_cls: type[TUpdate]
    nombre_config: str

    async def obtener_por_empresa(self, empresa_id: int) -> Optional[TEntity]:
        return self._fetch_one(
            self.entity_cls,
            filters={"empresa_id": empresa_id},
        )

    async def crear_o_actualizar(self, empresa_id: int, datos: TUpdate) -> TEntity:
        existente = await self.obtener_por_empresa(empresa_id)
        if existente:
            payload = datos.model_dump(mode="json", exclude_none=True)
            if not payload:
                return existente

            result = self._update_rows(payload, filters={"empresa_id": empresa_id})
            if not result.data:
                raise RuntimeError(
                    f"No se pudo actualizar la configuración {self.nombre_config}"
                )
            return self.entity_cls(**result.data[0])

        create_data = self.create_cls(
            empresa_id=empresa_id,
            **datos.model_dump(exclude_none=True),
        )
        result = self._insert_row(create_data.model_dump(mode="json"))
        if not result.data:
            raise RuntimeError(
                f"No se pudo crear la configuración {self.nombre_config}"
            )
        return self.entity_cls(**result.data[0])

    async def obtener_o_crear_default(self, empresa_id: int) -> TEntity:
        existente = await self.obtener_por_empresa(empresa_id)
        if existente:
            return existente
        return await self.crear_o_actualizar(empresa_id, self.update_cls())
