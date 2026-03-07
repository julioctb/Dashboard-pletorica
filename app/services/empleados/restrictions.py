"""Subservicio de restricciones de empleados."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional, TYPE_CHECKING
from uuid import UUID

from app.core.enums import AccionRestriccion
from app.core.exceptions import BusinessRuleError
from app.core.validation.constants import MOTIVO_RESTRICCION_MIN
from app.database import db_manager
from app.entities.empleado_restriccion_log import EmpleadoRestriccionLogResumen

if TYPE_CHECKING:
    from app.services.empleado_service import EmpleadoService


logger = logging.getLogger(__name__)


class EmpleadoRestrictionService:
    """Encapsula restricciones, liberaciones y auditoría."""

    def __init__(self, root: "EmpleadoService"):
        self.root = root

    async def restringir_empleado(
        self,
        empleado_id: int,
        motivo: str,
        admin_user_id: UUID,
        notas: Optional[str] = None,
    ):
        if not await self.es_admin(admin_user_id):
            raise BusinessRuleError("Solo administradores BUAP pueden restringir empleados")

        empleado = await self.root.obtener_por_id(empleado_id)
        if empleado.is_restricted:
            raise BusinessRuleError(
                f"El empleado {empleado.clave} ya tiene una restriccion activa"
            )
        if not motivo or len(motivo.strip()) < MOTIVO_RESTRICCION_MIN:
            raise BusinessRuleError(
                f"El motivo debe tener al menos {MOTIVO_RESTRICCION_MIN} caracteres"
            )

        ahora = datetime.now(timezone.utc)
        empleado.is_restricted = True
        empleado.restriction_reason = motivo.strip()
        empleado.restricted_at = ahora
        empleado.restricted_by = admin_user_id

        empleado_actualizado = await self.root.repository.actualizar(empleado)
        await self.registrar_log_restriccion(
            empleado_id=empleado_id,
            accion=AccionRestriccion.RESTRICCION,
            motivo=motivo.strip(),
            ejecutado_por=admin_user_id,
            notas=notas,
        )

        logger.info(
            "Empleado %s restringido por admin %s. Motivo: %s...",
            empleado.clave,
            admin_user_id,
            motivo[:50],
        )
        return empleado_actualizado

    async def liberar_empleado(
        self,
        empleado_id: int,
        motivo: str,
        admin_user_id: UUID,
        notas: Optional[str] = None,
    ):
        if not await self.es_admin(admin_user_id):
            raise BusinessRuleError("Solo administradores BUAP pueden liberar empleados")

        empleado = await self.root.obtener_por_id(empleado_id)
        if not empleado.is_restricted:
            raise BusinessRuleError(
                f"El empleado {empleado.clave} no tiene restriccion activa"
            )
        if not motivo or len(motivo.strip()) < MOTIVO_RESTRICCION_MIN:
            raise BusinessRuleError(
                f"El motivo de liberacion debe tener al menos {MOTIVO_RESTRICCION_MIN} caracteres"
            )

        empleado.is_restricted = False
        empleado.restriction_reason = None
        empleado.restricted_at = None
        empleado.restricted_by = None

        empleado_actualizado = await self.root.repository.actualizar(empleado)
        await self.registrar_log_restriccion(
            empleado_id=empleado_id,
            accion=AccionRestriccion.LIBERACION,
            motivo=motivo.strip(),
            ejecutado_por=admin_user_id,
            notas=notas,
        )

        logger.info(
            "Empleado %s liberado por admin %s. Motivo: %s...",
            empleado.clave,
            admin_user_id,
            motivo[:50],
        )
        return empleado_actualizado

    async def obtener_historial_restricciones(
        self,
        empleado_id: int,
        admin_user_id: Optional[UUID] = None,
    ) -> list[EmpleadoRestriccionLogResumen]:
        if not await self.es_admin(admin_user_id):
            raise BusinessRuleError(
                "Solo administradores pueden ver el historial de restricciones"
            )

        await self.root.obtener_por_id(empleado_id)
        supabase = db_manager.get_client()
        result = (
            supabase.table("empleado_restricciones_log")
            .select("*, user_profiles(nombre_completo)")
            .eq("empleado_id", empleado_id)
            .order("fecha", desc=True)
            .execute()
        )

        return [
            EmpleadoRestriccionLogResumen(
                id=r["id"],
                empleado_id=r["empleado_id"],
                accion=r["accion"],
                motivo=r["motivo"],
                fecha=r["fecha"],
                ejecutado_por_nombre=(
                    r.get("user_profiles", {}).get("nombre_completo", "Desconocido")
                ),
                notas=r.get("notas"),
            )
            for r in result.data
        ]

    async def es_admin(self, user_id: Optional[UUID]) -> bool:
        from app.core.config import Config

        if not Config.requiere_autenticacion():
            return True
        if not user_id:
            return False
        try:
            supabase = db_manager.get_client()
            result = (
                supabase.table("user_profiles")
                .select("rol, activo")
                .eq("id", str(user_id))
                .single()
                .execute()
            )
            if result.data:
                return result.data["rol"] == "admin" and result.data["activo"]
            return False
        except Exception:
            return False

    async def registrar_log_restriccion(
        self,
        empleado_id: int,
        accion: AccionRestriccion,
        motivo: str,
        ejecutado_por: UUID,
        notas: Optional[str] = None,
    ) -> None:
        datos = {
            "empleado_id": empleado_id,
            "accion": accion.value if isinstance(accion, AccionRestriccion) else accion,
            "motivo": motivo,
            "ejecutado_por": str(ejecutado_por),
            "notas": notas,
        }
        db_manager.get_client().table("empleado_restricciones_log").insert(datos).execute()
