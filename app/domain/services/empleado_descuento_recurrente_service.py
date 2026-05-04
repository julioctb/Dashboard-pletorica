"""Servicio de configuración de descuentos recurrentes por empleado."""

from __future__ import annotations

import logging
from collections import defaultdict
from datetime import date
from typing import Iterable

from app.core.exceptions import BusinessRuleError, DatabaseError
from app.core.text_utils import formatear_fecha, formatear_moneda
from app.database import db_manager
from app.domain.models.empleado_descuento_recurrente import (
    DESCUENTOS_RECURRENTES_POR_CLAVE,
    EmpleadoDescuentoRecurrente,
    EmpleadoDescuentoRecurrenteCreate,
)

logger = logging.getLogger(__name__)


class EmpleadoDescuentoRecurrenteService:
    """Gestiona la configuración maestra de descuentos recurrentes."""

    def __init__(self):
        self.supabase = db_manager.get_client()
        self.tabla = "empleado_descuentos_recurrentes"

    @staticmethod
    def _orden_concepto(concepto_clave: str) -> int:
        meta = DESCUENTOS_RECURRENTES_POR_CLAVE.get(concepto_clave, {})
        return int(meta.get("orden", 999))

    def _ordenar_descuentos(
        self,
        descuentos: Iterable[EmpleadoDescuentoRecurrente],
    ) -> list[EmpleadoDescuentoRecurrente]:
        """Mantiene un orden estable por concepto para UI y snapshot."""
        return sorted(
            list(descuentos),
            key=lambda item: (
                self._orden_concepto(item.concepto_clave),
                item.fecha_inicio,
            ),
        )

    async def reemplazar_descuentos_empleado(
        self,
        empleado_id: int,
        descuentos: list[EmpleadoDescuentoRecurrenteCreate],
    ) -> list[EmpleadoDescuentoRecurrente]:
        """Reemplaza la configuración completa de descuentos del empleado."""
        try:
            vistos: set[str] = set()
            payload: list[dict] = []
            for descuento in self._ordenar_descuentos(descuentos):
                if descuento.empleado_id != empleado_id:
                    raise BusinessRuleError(
                        "El descuento recurrente no corresponde al empleado editado."
                    )
                if descuento.concepto_clave in vistos:
                    raise BusinessRuleError(
                        "No se permiten descuentos recurrentes duplicados del mismo tipo."
                    )
                vistos.add(descuento.concepto_clave)
                payload.append(
                    {
                        "empleado_id": empleado_id,
                        "concepto_clave": descuento.concepto_clave,
                        "monto_periodico": float(descuento.monto_periodico),
                        "fecha_inicio": descuento.fecha_inicio.isoformat(),
                        "fecha_fin": (
                            descuento.fecha_fin.isoformat()
                            if descuento.fecha_fin
                            else None
                        ),
                        "notas": descuento.notas or None,
                    }
                )

            self.supabase.table(self.tabla).delete().eq(
                "empleado_id",
                empleado_id,
            ).execute()

            if not payload:
                return []

            result = self.supabase.table(self.tabla).insert(payload).execute()
            return [
                EmpleadoDescuentoRecurrente(**item)
                for item in (result.data or [])
            ]
        except (BusinessRuleError, DatabaseError):
            raise
        except Exception as exc:
            logger.error(
                "Error reemplazando descuentos recurrentes del empleado %s: %s",
                empleado_id,
                exc,
            )
            raise DatabaseError(
                f"Error guardando descuentos recurrentes del empleado: {exc}"
            )

    async def obtener_por_empleado(
        self,
        empleado_id: int,
    ) -> list[EmpleadoDescuentoRecurrente]:
        """Obtiene la configuración completa del empleado."""
        descuentos = await self.obtener_por_empleados([empleado_id])
        return descuentos.get(empleado_id, [])

    async def obtener_por_empleados(
        self,
        empleado_ids: list[int],
    ) -> dict[int, list[EmpleadoDescuentoRecurrente]]:
        """Carga descuentos por lote para enriquecer listados y formularios."""
        if not empleado_ids:
            return {}

        try:
            result = (
                self.supabase.table(self.tabla)
                .select("*")
                .in_("empleado_id", empleado_ids)
                .execute()
            )

            agrupados: dict[int, list[EmpleadoDescuentoRecurrente]] = defaultdict(list)
            for item in (result.data or []):
                descuento = EmpleadoDescuentoRecurrente(**item)
                agrupados[descuento.empleado_id].append(descuento)

            return {
                empleado_id: self._ordenar_descuentos(descuentos)
                for empleado_id, descuentos in agrupados.items()
            }
        except Exception as exc:
            logger.error("Error obteniendo descuentos recurrentes por lote: %s", exc)
            raise DatabaseError(
                f"Error consultando descuentos recurrentes por empleado: {exc}"
            )

    async def obtener_vigentes_en_rango(
        self,
        empleado_ids: list[int],
        fecha_inicio: date,
        fecha_fin: date,
    ) -> dict[int, list[EmpleadoDescuentoRecurrente]]:
        """Obtiene descuentos vigentes en cualquier parte del rango indicado."""
        descuentos = await self.obtener_por_empleados(empleado_ids)
        vigentes: dict[int, list[EmpleadoDescuentoRecurrente]] = {}
        for empleado_id, items in descuentos.items():
            activos = [
                item
                for item in items
                if item.esta_activo_en_rango(fecha_inicio, fecha_fin)
            ]
            if activos:
                vigentes[empleado_id] = activos
        return vigentes

    def _serializar_descuento_ui(
        self,
        descuento: EmpleadoDescuentoRecurrente,
        *,
        fecha_referencia: date,
    ) -> dict:
        """Proyección ligera para UI de empleados."""
        meta = DESCUENTOS_RECURRENTES_POR_CLAVE[descuento.concepto_clave]
        fecha_inicio = descuento.fecha_inicio.isoformat()
        fecha_fin = descuento.fecha_fin.isoformat() if descuento.fecha_fin else ""
        vigencia = (
            f"{formatear_fecha(fecha_inicio)} - {formatear_fecha(fecha_fin)}"
            if fecha_fin
            else f"Desde {formatear_fecha(fecha_inicio)}"
        )
        monto_fmt = formatear_moneda(str(descuento.monto_periodico))
        return {
            "concepto_clave": descuento.concepto_clave,
            "concepto_nombre": meta["nombre"],
            "concepto_label": meta["label"],
            "badge": meta["badge"],
            "color_scheme": meta["color_scheme"],
            "monto_periodico": float(descuento.monto_periodico),
            "monto_periodico_fmt": monto_fmt,
            "fecha_inicio": fecha_inicio,
            "fecha_fin": fecha_fin,
            "vigencia": vigencia,
            "notas": descuento.notas or "",
            "tooltip": f'{meta["nombre"]} · {monto_fmt} · {vigencia}',
            "activo": descuento.esta_activo_en_fecha(fecha_referencia),
        }

    async def obtener_resumenes_ui_por_empleados(
        self,
        empleado_ids: list[int],
        *,
        fecha_referencia: date | None = None,
    ) -> dict[int, dict]:
        """Retorna configurados y activos para uso directo en listados/detalle."""
        fecha_ref = fecha_referencia or date.today()
        descuentos = await self.obtener_por_empleados(empleado_ids)
        resumenes: dict[int, dict] = {}
        for empleado_id in empleado_ids:
            configurados = [
                self._serializar_descuento_ui(descuento, fecha_referencia=fecha_ref)
                for descuento in descuentos.get(empleado_id, [])
            ]
            resumenes[empleado_id] = {
                "descuentos_configurados": configurados,
                "descuentos_activos_hoy": [
                    item for item in configurados if item.get("activo")
                ],
            }
        return resumenes


empleado_descuento_recurrente_service = EmpleadoDescuentoRecurrenteService()

