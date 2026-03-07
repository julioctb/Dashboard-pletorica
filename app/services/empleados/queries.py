"""Subservicio de consultas del dominio de empleados."""

from __future__ import annotations

import logging
from datetime import date
from typing import Optional, TYPE_CHECKING
from uuid import UUID

from app.core.exceptions import NotFoundError
from app.database import db_manager
from app.entities.empleado import Empleado, EmpleadoResumen

if TYPE_CHECKING:
    from app.services.empleado_service import EmpleadoService


logger = logging.getLogger(__name__)


class EmpleadoQueryService:
    """Encapsula lecturas y búsquedas de empleados."""

    def __init__(self, root: "EmpleadoService"):
        self.root = root

    async def obtener_por_id(self, empleado_id: int) -> Empleado:
        return await self.root.repository.obtener_por_id(empleado_id)

    async def obtener_por_curp(self, curp: str) -> Optional[Empleado]:
        return await self.root.repository.obtener_por_curp(curp.upper())

    async def obtener_por_user_id(self, user_id: UUID) -> Optional[Empleado]:
        try:
            supabase = db_manager.get_client()
            result = (
                supabase.table("empleados")
                .select("*")
                .eq("user_id", str(user_id))
                .limit(1)
                .execute()
            )
            if not result.data:
                return None
            return Empleado(**result.data[0])
        except Exception as exc:
            logger.warning("Error buscando empleado por user_id %s: %s", user_id, exc)
            return None

    async def obtener_por_clave(self, clave: str) -> Optional[Empleado]:
        return await self.root.repository.obtener_por_clave(clave.upper())

    async def obtener_todos(
        self,
        incluir_inactivos: bool = False,
        limite: Optional[int] = 50,
        offset: int = 0,
    ) -> list[Empleado]:
        return await self.root.repository.obtener_todos(incluir_inactivos, limite, offset)

    async def obtener_por_empresa(
        self,
        empresa_id: int,
        incluir_inactivos: bool = False,
        limite: Optional[int] = 50,
        offset: int = 0,
    ) -> list[Empleado]:
        return await self.root.repository.obtener_por_empresa(
            empresa_id,
            incluir_inactivos,
            limite,
            offset,
        )

    async def obtener_resumen_empleados(
        self,
        incluir_inactivos: bool = False,
        limite: int = 100,
        offset: int = 0,
    ) -> list[EmpleadoResumen]:
        empleados = await self.obtener_todos(incluir_inactivos, limite, offset)
        return [EmpleadoResumen.from_empleado(emp, None) for emp in empleados]

    async def obtener_resumen_por_empresa(
        self,
        empresa_id: int,
        incluir_inactivos: bool = False,
        limite: int = 50,
        offset: int = 0,
    ) -> list[EmpleadoResumen]:
        empleados = await self.obtener_por_empresa(
            empresa_id,
            incluir_inactivos,
            limite,
            offset,
        )

        from app.services import empresa_service

        try:
            empresa = await empresa_service.obtener_por_id(empresa_id)
            empresa_nombre = empresa.nombre_comercial
        except NotFoundError:
            empresa_nombre = None

        from app.services.empleado_documento_service import empleado_documento_service

        progreso_expediente = await empleado_documento_service.contar_progreso_requerido_lote(
            [emp.id for emp in empleados if emp.id is not None]
        )

        return [
            EmpleadoResumen.from_empleado(
                emp,
                empresa_nombre,
                documentos_aprobados_expediente=progreso_expediente.get(
                    emp.id,
                    {},
                ).get("aprobados_requeridos", 0),
                documentos_requeridos_expediente=progreso_expediente.get(
                    emp.id,
                    {},
                ).get("total_requeridos", 0),
            )
            for emp in empleados
        ]

    async def buscar(
        self,
        texto: str,
        empresa_id: Optional[int] = None,
        limite: int = 20,
    ) -> list[Empleado]:
        if not texto or len(texto) < 2:
            return []
        return await self.root.repository.buscar(texto, empresa_id, limite)

    async def contar(
        self,
        empresa_id: Optional[int] = None,
        estatus: Optional[str] = None,
    ) -> int:
        return await self.root.repository.contar(empresa_id, estatus)

    async def obtener_disponibles_para_asignacion(self, limite: int = 100) -> list[EmpleadoResumen]:
        return await self.root.repository.obtener_disponibles_para_asignacion(limite)

    async def generar_clave(self, anio: Optional[int] = None) -> str:
        if anio is None:
            anio = date.today().year
        consecutivo = await self.root.repository.obtener_siguiente_consecutivo(anio)
        return Empleado.generar_clave(anio, consecutivo)

    async def validar_curp_disponible(
        self,
        curp: str,
        excluir_id: Optional[int] = None,
    ) -> bool:
        return not await self.root.repository.existe_curp(curp, excluir_id)
