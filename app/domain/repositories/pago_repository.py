"""Repositorio de pagos apoyado en BaseRepository para CRUD canónico."""

from typing import List, Optional
from decimal import Decimal

from app.domain.models import Pago
from app.core.exceptions import DatabaseError
from app.domain.repositories.base_repository import BaseRepository
from app.domain.repositories.shared import (
    apply_date_range_filter,
    apply_eq_filters,
    apply_order,
    apply_pagination,
)

class SupabasePagoRepository(BaseRepository[Pago]):
    """Implementacion del repositorio de pagos usando Supabase."""

    tabla = "pagos"
    entidad_class = Pago
    entidad_nombre = "Pago"

    def __init__(self, db_manager=None):
        super().__init__(db_manager)

    async def obtener_todos(
        self,
        contrato_id: Optional[int] = None,
        fecha_desde: Optional[str] = None,
        fecha_hasta: Optional[str] = None,
        limite: int = 100,
        offset: int = 0
    ) -> List[dict]:
        return await self._ejecutar_query(
            "obtener pagos",
            lambda: self._query_obtener_todos(
                contrato_id=contrato_id,
                fecha_desde=fecha_desde,
                fecha_hasta=fecha_hasta,
                limite=limite,
                offset=offset,
            ),
        )

    async def contar_todos(
        self,
        contrato_id: Optional[int] = None,
        fecha_desde: Optional[str] = None,
        fecha_hasta: Optional[str] = None,
    ) -> int:
        return await self._ejecutar_query(
            "contar pagos",
            lambda: self._query_contar_todos(
                contrato_id=contrato_id,
                fecha_desde=fecha_desde,
                fecha_hasta=fecha_hasta,
            ),
        )

    async def obtener_por_id(self, pago_id: int) -> Pago:
        return await super().obtener_por_id(pago_id)

    async def obtener_por_contrato(
        self,
        contrato_id: int,
        limite: Optional[int] = None,
        offset: int = 0
    ) -> List[Pago]:
        return await self._ejecutar_query(
            "obtener pagos por contrato",
            lambda: self._query_obtener_por_contrato(contrato_id, limite, offset),
        )

    async def crear(self, pago: Pago) -> Pago:
        return await super().crear(pago)

    async def actualizar(self, pago: Pago) -> Pago:
        return await super().actualizar_entidad(pago)

    async def eliminar(self, pago_id: int) -> bool:
        return await super().eliminar(pago_id)

    async def obtener_total_pagado(self, contrato_id: int) -> Decimal:
        """
        Obtiene el total pagado de un contrato.

        Raises:
            DatabaseError: Si hay error de conexion
        """
        return await self._ejecutar_query(
            "obtener total pagado de contrato",
            lambda: self._query_obtener_total_pagado(contrato_id),
        )

    async def obtener_ultimo_pago(self, contrato_id: int) -> Optional[Pago]:
        """
        Obtiene el ultimo pago de un contrato.

        Raises:
            DatabaseError: Si hay error de conexion
        """
        return await self._ejecutar_query(
            "obtener último pago de contrato",
            lambda: self._query_obtener_ultimo_pago(contrato_id),
        )

    async def contar_pagos(self, contrato_id: int) -> int:
        """
        Cuenta los pagos de un contrato.

        Raises:
            DatabaseError: Si hay error de conexion
        """
        return await self._ejecutar_query(
            "contar pagos de contrato",
            lambda: self._query_contar_pagos(contrato_id),
        )

    async def obtener_totales_por_contratos(
        self,
        contrato_ids: List[int]
    ) -> dict[int, Decimal]:
        """
        Obtiene el total pagado para multiples contratos en una sola query.

        Returns:
            Diccionario {contrato_id: total_pagado}

        Raises:
            DatabaseError: Si hay error de conexion
        """
        if not contrato_ids:
            return {}

        return await self._ejecutar_query(
            "obtener totales de pagos",
            lambda: self._query_obtener_totales_por_contratos(contrato_ids),
        )

    def _insertar(self, entidad: Pago) -> Pago:
        datos = entidad.model_dump(
            mode="json",
            exclude={"id", "fecha_creacion", "fecha_actualizacion"},
        )
        result = self.supabase.table(self.tabla).insert(datos).execute()
        if not result.data:
            raise DatabaseError("No se pudo crear el pago (sin respuesta de BD)")
        return self.entidad_class(**result.data[0])

    def _query_obtener_todos(
        self,
        *,
        contrato_id: Optional[int],
        fecha_desde: Optional[str],
        fecha_hasta: Optional[str],
        limite: int,
        offset: int,
    ) -> List[dict]:
        query = self.supabase.table(self.tabla).select(
            "*, contratos(codigo, empresa_id, empresas(nombre_comercial))"
        )
        query = apply_order(query, "fecha_pago", desc=True)
        query = apply_eq_filters(query, {"contrato_id": contrato_id})
        query = apply_date_range_filter(query, "fecha_pago", fecha_desde, fecha_hasta)
        query = apply_pagination(query, limite, offset)
        result = query.execute()

        pagos = []
        for data in result.data:
            contrato_info = data.pop("contratos", {}) or {}
            empresa_info = contrato_info.pop("empresas", {}) or {}
            pagos.append(
                {
                    **data,
                    "contrato_codigo": contrato_info.get("codigo", ""),
                    "empresa_nombre": empresa_info.get("nombre_comercial", ""),
                }
            )
        return pagos

    def _query_contar_todos(
        self,
        *,
        contrato_id: Optional[int],
        fecha_desde: Optional[str],
        fecha_hasta: Optional[str],
    ) -> int:
        query = self.supabase.table(self.tabla).select("id", count="exact")
        query = apply_eq_filters(query, {"contrato_id": contrato_id})
        query = apply_date_range_filter(query, "fecha_pago", fecha_desde, fecha_hasta)
        result = query.execute()
        return result.count or 0

    def _query_obtener_por_contrato(
        self,
        contrato_id: int,
        limite: Optional[int],
        offset: int,
    ) -> List[Pago]:
        query = self.supabase.table(self.tabla).select("*")
        query = apply_eq_filters(query, {"contrato_id": contrato_id})
        query = apply_order(query, "fecha_pago", desc=True)
        query = apply_pagination(query, limite, offset)
        result = query.execute()
        return [self.entidad_class(**data) for data in result.data]

    def _query_obtener_total_pagado(self, contrato_id: int) -> Decimal:
        result = self.supabase.table(self.tabla).select("monto").eq(
            "contrato_id",
            contrato_id,
        ).execute()
        if not result.data:
            return Decimal("0")
        return sum(Decimal(str(p["monto"])) for p in result.data)

    def _query_obtener_ultimo_pago(self, contrato_id: int) -> Optional[Pago]:
        query = self.supabase.table(self.tabla).select("*").eq(
            "contrato_id",
            contrato_id,
        )
        query = apply_order(query, "fecha_pago", desc=True).limit(1)
        result = query.execute()
        if not result.data:
            return None
        return self.entidad_class(**result.data[0])

    def _query_contar_pagos(self, contrato_id: int) -> int:
        result = self.supabase.table(self.tabla).select("id", count="exact").eq(
            "contrato_id",
            contrato_id,
        ).execute()
        return result.count or 0

    def _query_obtener_totales_por_contratos(
        self,
        contrato_ids: List[int],
    ) -> dict[int, Decimal]:
        result = self.supabase.table(self.tabla).select("contrato_id, monto").in_(
            "contrato_id",
            contrato_ids,
        ).execute()

        totales: dict[int, Decimal] = {cid: Decimal("0") for cid in contrato_ids}
        for pago in result.data:
            cid = pago["contrato_id"]
            if cid in totales:
                totales[cid] += Decimal(str(pago["monto"]))
        return totales
