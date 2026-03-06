"""Subservicio de configuracion del modulo de asistencias."""

from __future__ import annotations

import logging
from datetime import date
from typing import Optional, TYPE_CHECKING

from app.core.enums import Estatus
from app.core.exceptions import BusinessRuleError, DatabaseError
from app.entities.asistencia import Horario, HorarioCreate, SupervisorSedeCreate

if TYPE_CHECKING:
    from app.services.asistencia_service import AsistenciaService


logger = logging.getLogger(__name__)


class AsistenciaConfigService:
    """Gestiona horarios, supervisiones y catalogos operativos."""

    def __init__(self, root: "AsistenciaService"):
        self.root = root

    async def obtener_horario_activo(
        self,
        empresa_id: int,
        contrato_id: int,
    ) -> Optional[Horario]:
        try:
            result = (
                self.root.supabase.table("horarios")
                .select("*")
                .eq("empresa_id", empresa_id)
                .eq("contrato_id", contrato_id)
                .eq("es_horario_activo", True)
                .limit(1)
                .execute()
            )
            return Horario(**result.data[0]) if result.data else None
        except Exception as exc:
            logger.error("Error obteniendo horario activo: %s", exc)
            raise DatabaseError(f"Error obteniendo horario activo: {exc}")

    async def obtener_configuracion_asistencias(
        self,
        empresa_id: int,
        contrato_id: int,
    ) -> dict:
        try:
            horarios_result = (
                self.root.supabase.table("horarios")
                .select("*")
                .eq("empresa_id", empresa_id)
                .eq("contrato_id", contrato_id)
                .order("es_horario_activo", desc=True)
                .order("fecha_actualizacion", desc=True)
                .execute()
            )
            horarios = []
            for item in horarios_result.data or []:
                horario = Horario(**item)
                horario_dict = horario.model_dump(mode="json")
                horario_dict["dias_resumen"] = self.root._resumir_dias_laborales(horario.dias_laborales)
                horarios.append(horario_dict)

            asignaciones_result = (
                self.root.supabase.table("supervisor_sedes")
                .select(
                    "id, supervisor_id, sede_id, empresa_id, fecha_inicio, fecha_fin, "
                    "activo, notas, fecha_creacion, fecha_actualizacion, "
                    "supervisor:supervisor_id(id, clave, nombre, apellido_paterno, apellido_materno), "
                    "sede:sede_id(id, codigo, nombre)"
                )
                .eq("empresa_id", empresa_id)
                .order("activo", desc=True)
                .order("fecha_inicio", desc=True)
                .execute()
            )
            asignaciones = []
            for item in asignaciones_result.data or []:
                supervisor_data = item.get("supervisor") or {}
                sede_data = item.get("sede") or {}
                asignaciones.append(
                    {
                        "id": item["id"],
                        "supervisor_id": item.get("supervisor_id"),
                        "sede_id": item.get("sede_id"),
                        "empresa_id": item.get("empresa_id"),
                        "fecha_inicio": item.get("fecha_inicio"),
                        "fecha_fin": item.get("fecha_fin") or "",
                        "activo": bool(item.get("activo")),
                        "notas": item.get("notas") or "",
                        "supervisor_clave": supervisor_data.get("clave", ""),
                        "supervisor_nombre": self.root._nombre_empleado(supervisor_data),
                        "sede_codigo": sede_data.get("codigo", ""),
                        "sede_nombre": sede_data.get("nombre", ""),
                    }
                )

            return {
                "horarios": horarios,
                "asignaciones": asignaciones,
                "supervisores": await self.root._obtener_supervisores_disponibles(empresa_id),
                "sedes": await self.root._obtener_catalogo_sedes(),
            }
        except DatabaseError:
            raise
        except Exception as exc:
            logger.error("Error obteniendo configuracion de asistencias: %s", exc)
            raise DatabaseError(f"Error obteniendo configuracion de asistencias: {exc}")

    async def guardar_horario(
        self,
        horario_id: Optional[int],
        datos: HorarioCreate,
    ) -> Horario:
        payload = {
            "empresa_id": datos.empresa_id,
            "contrato_id": datos.contrato_id,
            "nombre": datos.nombre.strip(),
            "descripcion": (datos.descripcion or "").strip() or None,
            "dias_laborales": self.root._normalizar_dias_laborales(datos.dias_laborales),
            "tolerancia_entrada_min": int(datos.tolerancia_entrada_min),
            "tolerancia_salida_min": int(datos.tolerancia_salida_min),
            "es_horario_activo": bool(datos.es_horario_activo),
            "estatus": Estatus.ACTIVO.value if datos.es_horario_activo else Estatus.INACTIVO.value,
        }
        try:
            if datos.es_horario_activo:
                query = (
                    self.root.supabase.table("horarios")
                    .update({"es_horario_activo": False, "estatus": Estatus.INACTIVO.value})
                    .eq("empresa_id", datos.empresa_id)
                    .eq("contrato_id", datos.contrato_id)
                )
                if horario_id:
                    query = query.neq("id", horario_id)
                query.execute()

            if horario_id:
                result = (
                    self.root.supabase.table("horarios")
                    .update(payload)
                    .eq("id", horario_id)
                    .eq("empresa_id", datos.empresa_id)
                    .execute()
                )
            else:
                result = self.root.supabase.table("horarios").insert(payload).execute()

            if not result.data:
                raise DatabaseError("No se pudo guardar el horario")
            return Horario(**result.data[0])
        except DatabaseError:
            raise
        except Exception as exc:
            logger.error("Error guardando horario: %s", exc)
            raise DatabaseError(f"Error guardando horario: {exc}")

    async def desactivar_horario(self, empresa_id: int, horario_id: int) -> bool:
        try:
            result = (
                self.root.supabase.table("horarios")
                .update({"es_horario_activo": False, "estatus": Estatus.INACTIVO.value})
                .eq("id", horario_id)
                .eq("empresa_id", empresa_id)
                .execute()
            )
            return bool(result.data)
        except Exception as exc:
            logger.error("Error desactivando horario: %s", exc)
            raise DatabaseError(f"Error desactivando horario: {exc}")

    async def guardar_supervision(
        self,
        asignacion_id: Optional[int],
        datos: SupervisorSedeCreate,
    ) -> dict:
        if datos.fecha_fin and datos.fecha_fin < datos.fecha_inicio:
            raise BusinessRuleError("La fecha fin no puede ser anterior a la fecha inicio")

        await self.validar_supervisor_empresa(datos.empresa_id, datos.supervisor_id)
        await self.validar_sede_existe(datos.sede_id)
        await self.validar_supervision_duplicada(
            empresa_id=datos.empresa_id,
            supervisor_id=datos.supervisor_id,
            sede_id=datos.sede_id,
            asignacion_id=asignacion_id,
            activo=datos.activo,
        )

        payload = {
            "empresa_id": datos.empresa_id,
            "supervisor_id": datos.supervisor_id,
            "sede_id": datos.sede_id,
            "fecha_inicio": datos.fecha_inicio.isoformat(),
            "fecha_fin": datos.fecha_fin.isoformat() if datos.fecha_fin else None,
            "activo": bool(datos.activo),
            "notas": (datos.notas or "").strip() or None,
        }
        try:
            if asignacion_id:
                result = (
                    self.root.supabase.table("supervisor_sedes")
                    .update(payload)
                    .eq("id", asignacion_id)
                    .eq("empresa_id", datos.empresa_id)
                    .execute()
                )
            else:
                result = self.root.supabase.table("supervisor_sedes").insert(payload).execute()

            if not result.data:
                raise DatabaseError("No se pudo guardar la asignacion de supervision")
            return result.data[0]
        except DatabaseError:
            raise
        except Exception as exc:
            logger.error("Error guardando asignacion supervisor-sede: %s", exc)
            raise DatabaseError(f"Error guardando asignacion supervisor-sede: {exc}")

    async def desactivar_supervision(
        self,
        empresa_id: int,
        asignacion_id: int,
        fecha_fin: Optional[date] = None,
    ) -> bool:
        try:
            result = (
                self.root.supabase.table("supervisor_sedes")
                .update({"activo": False, "fecha_fin": (fecha_fin or date.today()).isoformat()})
                .eq("id", asignacion_id)
                .eq("empresa_id", empresa_id)
                .execute()
            )
            return bool(result.data)
        except Exception as exc:
            logger.error("Error desactivando asignacion supervisor-sede: %s", exc)
            raise DatabaseError(f"Error desactivando asignacion supervisor-sede: {exc}")

    async def validar_supervisor_empresa(self, empresa_id: int, supervisor_id: int) -> None:
        try:
            result = (
                self.root.supabase.table("empleados")
                .select("id, empresa_id")
                .eq("id", supervisor_id)
                .eq("empresa_id", empresa_id)
                .limit(1)
                .execute()
            )
            if not result.data:
                raise BusinessRuleError("El supervisor seleccionado no pertenece a la empresa")
        except BusinessRuleError:
            raise
        except Exception as exc:
            logger.error("Error validando supervisor: %s", exc)
            raise DatabaseError(f"Error validando supervisor: {exc}")

    async def validar_sede_existe(self, sede_id: int) -> None:
        try:
            result = (
                self.root.supabase.table("sedes")
                .select("id")
                .eq("id", sede_id)
                .limit(1)
                .execute()
            )
            if not result.data:
                raise BusinessRuleError("La sede seleccionada no existe")
        except BusinessRuleError:
            raise
        except Exception as exc:
            logger.error("Error validando sede: %s", exc)
            raise DatabaseError(f"Error validando sede: {exc}")

    async def validar_supervision_duplicada(
        self,
        empresa_id: int,
        supervisor_id: int,
        sede_id: int,
        asignacion_id: Optional[int],
        activo: bool,
    ) -> None:
        if not activo:
            return
        try:
            query = (
                self.root.supabase.table("supervisor_sedes")
                .select("id")
                .eq("empresa_id", empresa_id)
                .eq("supervisor_id", supervisor_id)
                .eq("sede_id", sede_id)
                .eq("activo", True)
            )
            if asignacion_id:
                query = query.neq("id", asignacion_id)
            result = query.limit(1).execute()
            if result.data:
                raise BusinessRuleError(
                    "Ya existe una asignacion activa de este supervisor para la sede seleccionada"
                )
        except BusinessRuleError:
            raise
        except Exception as exc:
            logger.error("Error validando duplicado supervisor-sede: %s", exc)
            raise DatabaseError(f"Error validando duplicado supervisor-sede: {exc}")
