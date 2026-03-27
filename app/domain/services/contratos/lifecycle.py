"""Ciclo laboral automático asociado a la vigencia de contratos."""

from __future__ import annotations

import logging
from datetime import date, datetime, timezone

from app.domain.enums import EstatusEmpleado, EstatusPlaza, EstatusContrato, MotivoBaja
from app.database import db_manager
from app.domain.models.baja_empleado import BajaEmpleadoCreate
from app.domain.services.baja_service import baja_service

logger = logging.getLogger(__name__)


class ContratoLifecycleService:
    """Orquesta cierres laborales cuando un contrato vence."""

    def __init__(self):
        self.supabase = db_manager.get_client()

    async def procesar_bajas_por_fin_contrato(self) -> int:
        """Procesa contratos vencidos pendientes de cierre laboral."""
        try:
            result = (
                self.supabase.table("contratos")
                .select("id, empresa_id, fecha_fin")
                .eq("estatus", EstatusContrato.VENCIDO.value)
                .is_("fin_contrato_procesado_at", "null")
                .lte("fecha_fin", date.today().isoformat())
                .execute()
            )
        except Exception as exc:
            logger.error("Error consultando contratos vencidos pendientes: %s", exc)
            return 0

        procesados = 0
        for contrato in (result.data or []):
            await self._procesar_contrato_vencido(contrato)
            procesados += 1
        return procesados

    async def _procesar_contrato_vencido(self, contrato: dict) -> None:
        contrato_id = int(contrato["id"])
        empresa_id = int(contrato["empresa_id"])
        fecha_fin = date.fromisoformat(str(contrato["fecha_fin"]))

        try:
            plazas_result = (
                self.supabase.table("plazas")
                .select("id, empleado_id")
                .eq("contrato_id", contrato_id)
                .eq("estatus", EstatusPlaza.OCUPADA.value)
                .not_.is_("empleado_id", "null")
                .execute()
            )
            empleado_ids = sorted(
                {
                    int(item.get("empleado_id"))
                    for item in (plazas_result.data or [])
                    if item.get("empleado_id") is not None
                }
            )

            if empleado_ids:
                empleados_result = (
                    self.supabase.table("empleados")
                    .select("id, clave, estatus, empresa_id")
                    .in_("id", empleado_ids)
                    .execute()
                )
                empleados_activos = [
                    item
                    for item in (empleados_result.data or [])
                    if item.get("estatus") == EstatusEmpleado.ACTIVO.value
                    and int(item.get("empresa_id") or 0) == empresa_id
                ]

                for empleado in empleados_activos:
                    try:
                        await baja_service.registrar_baja(
                            BajaEmpleadoCreate(
                                empleado_id=int(empleado["id"]),
                                empresa_id=empresa_id,
                                motivo=MotivoBaja.FIN_CONTRATO,
                                fecha_efectiva=fecha_fin,
                                notas=(
                                    "Baja automática por fin de contrato "
                                    f"#{contrato_id}."
                                ),
                                registrado_por=None,
                                es_automatica=True,
                                contrato_id_origen=contrato_id,
                            )
                        )
                    except Exception as exc:
                        logger.warning(
                            "No se pudo registrar baja automática de empleado %s por contrato %s: %s",
                            empleado.get("id"),
                            contrato_id,
                            exc,
                        )

            self.supabase.table("contratos").update(
                {"fin_contrato_procesado_at": datetime.now(timezone.utc).isoformat()}
            ).eq("id", contrato_id).execute()
        except Exception as exc:
            logger.error(
                "Error procesando cierre laboral automático del contrato %s: %s",
                contrato_id,
                exc,
            )


contrato_lifecycle_service = ContratoLifecycleService()
