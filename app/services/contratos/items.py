"""Subservicio de items y flujo requisición -> contrato."""

from __future__ import annotations

from decimal import Decimal
from typing import Optional, TYPE_CHECKING

from app.core.exceptions import BusinessRuleError
from app.entities.contrato_item import ContratoItem, ContratoItemCreate

if TYPE_CHECKING:
    from app.services.contrato_service import ContratoService


class ContratoItemService:
    """Encapsula items de contrato y creación desde requisición."""

    def __init__(self, root: "ContratoService"):
        self.root = root

    async def crear_desde_requisicion(
        self,
        requisicion_id: int,
        contrato_create,
        codigo_empresa: str,
        clave_servicio: str,
        items_contrato: Optional[list[ContratoItemCreate]] = None,
    ):
        from app.core.enums import EstadoRequisicion
        from app.entities import ContratoCreate
        from app.services.requisicion_service import requisicion_service

        requisicion = await requisicion_service.obtener_por_id(requisicion_id)
        if requisicion.estado != EstadoRequisicion.ADJUDICADA:
            raise BusinessRuleError(
                "Solo se pueden crear contratos desde requisiciones ADJUDICADAS. "
                f"Estado actual: {requisicion.estado}"
            )

        datos = contrato_create.model_dump()
        datos["requisicion_id"] = requisicion_id
        contrato_create_con_req = ContratoCreate(**datos)

        contrato = await self.root.crear_con_codigo_auto(
            contrato_create_con_req,
            codigo_empresa,
            clave_servicio,
        )

        if items_contrato:
            items = []
            for item_create in items_contrato:
                items.append(
                    ContratoItem(
                        **item_create.model_dump(),
                        subtotal=item_create.cantidad * item_create.precio_unitario,
                    )
                )
            await self.root.repository.crear_items_batch(contrato.id, items)

        await requisicion_service.marcar_contratada(requisicion_id, contrato.id)
        return contrato

    async def obtener_items(self, contrato_id: int) -> list[ContratoItem]:
        return await self.root.repository.obtener_items(contrato_id)

    async def copiar_items_desde_requisicion(
        self,
        contrato_id: int,
        requisicion_items: list,
        precios: dict[int, Decimal],
    ) -> list[ContratoItem]:
        items = []
        for req_item in requisicion_items:
            req_item_id = req_item.id if hasattr(req_item, "id") else req_item.get("id")
            precio = precios.get(req_item_id, Decimal("0"))

            cantidad = (
                req_item.cantidad
                if hasattr(req_item, "cantidad")
                else Decimal(str(req_item.get("cantidad", 1)))
            )
            descripcion = (
                req_item.descripcion
                if hasattr(req_item, "descripcion")
                else req_item.get("descripcion", "")
            )
            unidad = (
                req_item.unidad_medida
                if hasattr(req_item, "unidad_medida")
                else req_item.get("unidad_medida", "Pieza")
            )
            numero = (
                req_item.numero_item
                if hasattr(req_item, "numero_item")
                else req_item.get("numero_item", 1)
            )
            specs = (
                req_item.especificaciones_tecnicas
                if hasattr(req_item, "especificaciones_tecnicas")
                else req_item.get("especificaciones_tecnicas")
            )

            items.append(
                ContratoItem(
                    requisicion_item_id=req_item_id,
                    numero_item=numero,
                    unidad_medida=unidad,
                    cantidad=cantidad,
                    descripcion=descripcion,
                    precio_unitario=precio,
                    subtotal=cantidad * precio,
                    especificaciones_tecnicas=specs,
                )
            )

        return await self.root.repository.crear_items_batch(contrato_id, items)
