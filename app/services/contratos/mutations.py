"""Subservicio de mutaciones y ciclo de vida del dominio de contratos."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.core.exceptions import BusinessRuleError
from app.entities import Contrato, ContratoCreate, ContratoUpdate, EstatusContrato

if TYPE_CHECKING:
    from app.services.contrato_service import ContratoService


class ContratoMutationService:
    """Encapsula creación, edición y cambios de estatus."""

    def __init__(self, root: "ContratoService"):
        self.root = root

    async def crear(self, contrato_create: ContratoCreate) -> Contrato:
        contrato = Contrato(**contrato_create.model_dump())
        return await self.root.repository.crear(contrato)

    async def crear_con_codigo_auto(
        self,
        contrato_create: ContratoCreate,
        codigo_empresa: str,
        clave_servicio: str,
    ) -> Contrato:
        codigo = await self.generar_codigo_contrato(
            codigo_empresa,
            clave_servicio,
            contrato_create.fecha_inicio.year,
        )
        datos = contrato_create.model_dump()
        datos["codigo"] = codigo
        contrato = Contrato(**datos)
        return await self.root.repository.crear(contrato)

    async def generar_codigo_contrato(
        self,
        codigo_empresa: str,
        clave_servicio: str,
        anio: int,
    ) -> str:
        consecutivo = await self.root.repository.obtener_siguiente_consecutivo(
            codigo_empresa,
            clave_servicio,
            anio,
        )
        return Contrato.generar_codigo(codigo_empresa, clave_servicio, anio, consecutivo)

    async def actualizar(self, contrato_id: int, contrato_update: ContratoUpdate) -> Contrato:
        contrato_actual = await self.root.repository.obtener_por_id(contrato_id)
        if not contrato_actual.puede_modificarse():
            raise BusinessRuleError(
                f"No se puede modificar un contrato en estado {contrato_actual.estatus}"
            )

        datos_actualizados = contrato_actual.model_dump()
        for campo, valor in contrato_update.model_dump(exclude_unset=True).items():
            if valor is not None:
                datos_actualizados[campo] = valor

        contrato_modificado = Contrato(**datos_actualizados)
        return await self.root.repository.actualizar(contrato_modificado)

    async def activar(self, contrato_id: int) -> Contrato:
        contrato = await self.root.repository.obtener_por_id(contrato_id)
        if not contrato.puede_activarse():
            raise BusinessRuleError(
                f"No se puede activar un contrato en estado {contrato.estatus}"
            )
        return await self.root.repository.cambiar_estatus(contrato_id, EstatusContrato.ACTIVO)

    async def suspender(self, contrato_id: int) -> Contrato:
        contrato = await self.root.repository.obtener_por_id(contrato_id)
        if contrato.estatus != EstatusContrato.ACTIVO:
            raise BusinessRuleError("Solo se pueden suspender contratos activos")
        return await self.root.repository.cambiar_estatus(
            contrato_id,
            EstatusContrato.SUSPENDIDO,
        )

    async def reactivar(self, contrato_id: int) -> Contrato:
        contrato = await self.root.repository.obtener_por_id(contrato_id)
        if contrato.estatus != EstatusContrato.SUSPENDIDO:
            raise BusinessRuleError("Solo se pueden reactivar contratos suspendidos")
        return await self.root.repository.cambiar_estatus(contrato_id, EstatusContrato.ACTIVO)

    async def cancelar(self, contrato_id: int) -> Contrato:
        contrato = await self.root.repository.obtener_por_id(contrato_id)
        if contrato.estatus == EstatusContrato.CANCELADO:
            raise BusinessRuleError("El contrato ya está cancelado")
        return await self.root.repository.cambiar_estatus(
            contrato_id,
            EstatusContrato.CANCELADO,
        )

    async def eliminar(self, contrato_id: int) -> bool:
        return await self.root.repository.eliminar(contrato_id)
