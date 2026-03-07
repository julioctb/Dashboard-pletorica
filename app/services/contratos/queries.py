"""Subservicio de consultas del dominio de contratos."""

from __future__ import annotations

from datetime import date
from typing import Optional, TYPE_CHECKING

from app.entities import Contrato, ContratoResumen, EstatusContrato

if TYPE_CHECKING:
    from app.services.contrato_service import ContratoService


class ContratoQueryService:
    """Encapsula lecturas y búsquedas de contratos."""

    def __init__(self, root: "ContratoService"):
        self.root = root

    async def obtener_por_id(self, contrato_id: int) -> Contrato:
        return await self.root.repository.obtener_por_id(contrato_id)

    async def obtener_por_codigo(self, codigo: str) -> Optional[Contrato]:
        return await self.root.repository.obtener_por_codigo(codigo)

    async def obtener_todos(
        self,
        incluir_inactivos: bool = False,
        limite: Optional[int] = None,
        offset: int = 0,
    ) -> list[Contrato]:
        return await self.root.repository.obtener_todos(incluir_inactivos, limite, offset)

    async def obtener_resumen_contratos(
        self,
        incluir_inactivos: bool = False,
        limite: Optional[int] = 50,
        offset: int = 0,
    ) -> list[ContratoResumen]:
        contratos = await self.obtener_todos(incluir_inactivos, limite, offset)
        return [ContratoResumen.from_contrato(c) for c in contratos]

    async def obtener_por_empresa(
        self,
        empresa_id: int,
        incluir_inactivos: bool = False,
    ) -> list[Contrato]:
        return await self.root.repository.obtener_por_empresa(empresa_id, incluir_inactivos)

    async def obtener_por_tipo_servicio(
        self,
        tipo_servicio_id: int,
        incluir_inactivos: bool = False,
    ) -> list[Contrato]:
        return await self.root.repository.obtener_por_tipo_servicio(
            tipo_servicio_id,
            incluir_inactivos,
        )

    async def buscar_por_texto(self, termino: str, limite: int = 10) -> list[Contrato]:
        if not termino or len(termino) < 2:
            return []
        return await self.root.repository.buscar_por_texto(termino, limite)

    async def buscar_con_filtros(
        self,
        texto: Optional[str] = None,
        empresa_id: Optional[int] = None,
        tipo_servicio_id: Optional[int] = None,
        estatus: Optional[str] = None,
        modalidad: Optional[str] = None,
        fecha_inicio_desde: Optional[date] = None,
        fecha_inicio_hasta: Optional[date] = None,
        incluir_inactivos: bool = False,
        limite: int = 50,
        offset: int = 0,
    ) -> list[ContratoResumen]:
        if texto and len(texto.strip()) < 2:
            texto = None

        contratos = await self.root.repository.buscar_con_filtros(
            texto=texto,
            empresa_id=empresa_id,
            tipo_servicio_id=tipo_servicio_id,
            estatus=estatus,
            modalidad=modalidad,
            fecha_inicio_desde=fecha_inicio_desde,
            fecha_inicio_hasta=fecha_inicio_hasta,
            incluir_inactivos=incluir_inactivos,
            limite=limite,
            offset=offset,
        )
        return [ContratoResumen.from_contrato(c) for c in contratos]

    async def obtener_con_personal(
        self,
        solo_activos: bool = True,
        limite: int = 50,
    ) -> list[ContratoResumen]:
        contratos = await self.root.repository.obtener_todos(
            incluir_inactivos=not solo_activos,
            limite=limite,
        )
        contratos_con_personal = [
            c
            for c in contratos
            if c.tiene_personal
            and (
                not solo_activos
                or c.estatus in [EstatusContrato.ACTIVO, EstatusContrato.BORRADOR]
            )
        ]
        return [ContratoResumen.from_contrato(c) for c in contratos_con_personal]

    async def obtener_vigentes(self) -> list[Contrato]:
        return await self.root.repository.obtener_vigentes()

    async def obtener_por_vencer(self, dias: int = 30) -> list[Contrato]:
        return await self.root.repository.obtener_por_vencer(dias)

    async def existe_codigo(self, codigo: str, excluir_id: Optional[int] = None) -> bool:
        return await self.root.repository.existe_codigo(codigo, excluir_id)
