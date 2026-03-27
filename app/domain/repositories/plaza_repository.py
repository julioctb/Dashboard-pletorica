"""
Repositorio de Plaza - Implementación para Supabase.

Modelo plazas-first:
- la plaza depende directamente del contrato
- la categoría es opcional al inicio y se asigna después
- el número de plaza es único por contrato
"""
from __future__ import annotations

import logging
from datetime import date
from decimal import Decimal
from typing import Optional

from app.domain.enums import EstatusPlaza
from app.core.exceptions import DatabaseError, DuplicateError, NotFoundError
from app.domain.models.plaza import Plaza

logger = logging.getLogger(__name__)


class SupabasePlazaRepository:
    """Implementación del repositorio usando Supabase."""

    def __init__(self, db_manager=None):
        if db_manager is None:
            from app.database import db_manager as default_db
            db_manager = default_db

        self.supabase = db_manager.get_client()
        self.tabla = "plazas"

    async def obtener_por_id(self, id: int) -> Plaza:
        try:
            result = self.supabase.table(self.tabla).select("*").eq("id", id).execute()
            if not result.data:
                raise NotFoundError(f"Plaza con ID {id} no encontrada")
            return Plaza(**result.data[0])
        except NotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error obteniendo plaza {id}: {e}")
            raise DatabaseError(f"Error de base de datos: {str(e)}")

    async def obtener_por_contrato(
        self,
        contrato_id: int,
        incluir_canceladas: bool = False,
        limite: Optional[int] = None,
        offset: int = 0,
    ) -> list[Plaza]:
        try:
            query = self.supabase.table(self.tabla).select("*").eq("contrato_id", contrato_id)
            if not incluir_canceladas:
                query = query.neq("estatus", EstatusPlaza.CANCELADA.value)
            query = query.order("numero_plaza", desc=False)
            if limite is not None:
                query = query.range(offset, offset + limite - 1)
            result = query.execute()
            return [Plaza(**data) for data in (result.data or [])]
        except Exception as e:
            logger.error(f"Error obteniendo plazas del contrato {contrato_id}: {e}")
            raise DatabaseError(f"Error de base de datos: {str(e)}")

    async def obtener_vacantes_sin_categoria(self, contrato_id: int) -> list[Plaza]:
        try:
            result = (
                self.supabase.table(self.tabla)
                .select("*")
                .eq("contrato_id", contrato_id)
                .eq("estatus", EstatusPlaza.VACANTE.value)
                .is_("categoria_puesto_id", "null")
                .order("numero_plaza", desc=False)
                .execute()
            )
            return [Plaza(**data) for data in (result.data or [])]
        except Exception as e:
            logger.error(f"Error obteniendo vacantes sin categoría del contrato {contrato_id}: {e}")
            raise DatabaseError(f"Error de base de datos: {str(e)}")

    async def obtener_vacantes_con_categoria_sin_sede(self, contrato_id: int) -> list[Plaza]:
        try:
            result = (
                self.supabase.table(self.tabla)
                .select("*")
                .eq("contrato_id", contrato_id)
                .eq("estatus", EstatusPlaza.VACANTE.value)
                .not_.is_("categoria_puesto_id", "null")
                .is_("sede_id", "null")
                .order("numero_plaza", desc=False)
                .execute()
            )
            return [Plaza(**data) for data in (result.data or [])]
        except Exception as e:
            logger.error(
                "Error obteniendo vacantes con categoría y sin sede del contrato %s: %s",
                contrato_id,
                e,
            )
            raise DatabaseError(f"Error de base de datos: {str(e)}")

    async def existe_numero_plaza(
        self,
        contrato_id: int,
        numero_plaza: int,
        excluir_id: Optional[int] = None,
    ) -> bool:
        try:
            query = (
                self.supabase.table(self.tabla)
                .select("id")
                .eq("contrato_id", contrato_id)
                .eq("numero_plaza", numero_plaza)
            )
            if excluir_id:
                query = query.neq("id", excluir_id)
            result = query.execute()
            return bool(result.data)
        except Exception as e:
            logger.error(f"Error verificando número de plaza contrato={contrato_id}, numero={numero_plaza}: {e}")
            raise DatabaseError(f"Error de base de datos: {str(e)}")

    async def crear(self, plaza: Plaza) -> Plaza:
        try:
            if await self.existe_numero_plaza(plaza.contrato_id, plaza.numero_plaza):
                raise DuplicateError(
                    f"Ya existe la plaza #{plaza.numero_plaza} en este contrato",
                    field="numero_plaza",
                    value=str(plaza.numero_plaza),
                )

            datos = plaza.model_dump(mode="json", exclude={"id", "fecha_creacion", "fecha_actualizacion"})
            result = self.supabase.table(self.tabla).insert(datos).execute()
            if not result.data:
                raise DatabaseError("No se pudo crear la plaza")
            return Plaza(**result.data[0])
        except DuplicateError:
            raise
        except Exception as e:
            logger.error(f"Error creando plaza: {e}")
            raise DatabaseError(f"Error de base de datos: {str(e)}")

    async def actualizar(self, plaza: Plaza) -> Plaza:
        try:
            await self.obtener_por_id(plaza.id)
            if await self.existe_numero_plaza(plaza.contrato_id, plaza.numero_plaza, plaza.id):
                raise DuplicateError(
                    f"Ya existe la plaza #{plaza.numero_plaza} en este contrato",
                    field="numero_plaza",
                    value=str(plaza.numero_plaza),
                )

            datos = plaza.model_dump(mode="json", exclude={"id", "fecha_creacion", "fecha_actualizacion"})
            result = (
                self.supabase.table(self.tabla)
                .update(datos)
                .eq("id", plaza.id)
                .execute()
            )
            if not result.data:
                raise NotFoundError(f"Plaza con ID {plaza.id} no encontrada")
            return Plaza(**result.data[0])
        except (NotFoundError, DuplicateError):
            raise
        except Exception as e:
            logger.error(f"Error actualizando plaza {plaza.id}: {e}")
            raise DatabaseError(f"Error de base de datos: {str(e)}")

    async def cancelar(self, id: int) -> bool:
        try:
            result = (
                self.supabase.table(self.tabla)
                .update({"estatus": EstatusPlaza.CANCELADA.value, "empleado_id": None})
                .eq("id", id)
                .execute()
            )
            return bool(result.data)
        except Exception as e:
            logger.error(f"Error cancelando plaza {id}: {e}")
            raise DatabaseError(f"Error de base de datos: {str(e)}")

    async def cambiar_estatus(self, plaza_id: int, nuevo_estatus: EstatusPlaza) -> bool:
        try:
            payload = {"estatus": nuevo_estatus.value}
            if nuevo_estatus == EstatusPlaza.VACANTE:
                payload["empleado_id"] = None
            result = (
                self.supabase.table(self.tabla)
                .update(payload)
                .eq("id", plaza_id)
                .execute()
            )
            return bool(result.data)
        except Exception as e:
            logger.error(f"Error cambiando estatus de plaza {plaza_id}: {e}")
            raise DatabaseError(f"Error de base de datos: {str(e)}")

    async def obtener_siguiente_numero_plaza(self, contrato_id: int) -> int:
        try:
            result = (
                self.supabase.table(self.tabla)
                .select("numero_plaza")
                .eq("contrato_id", contrato_id)
                .order("numero_plaza", desc=True)
                .limit(1)
                .execute()
            )
            if not result.data:
                return 1
            return int(result.data[0]["numero_plaza"]) + 1
        except Exception as e:
            logger.error(f"Error obteniendo siguiente número de plaza del contrato {contrato_id}: {e}")
            raise DatabaseError(f"Error de base de datos: {str(e)}")

    async def contar_por_contrato(self, contrato_id: int, incluir_canceladas: bool = True) -> int:
        try:
            query = self.supabase.table(self.tabla).select("id", count="exact").eq("contrato_id", contrato_id)
            if not incluir_canceladas:
                query = query.neq("estatus", EstatusPlaza.CANCELADA.value)
            result = query.execute()
            return result.count if result.count is not None else 0
        except Exception as e:
            logger.error(f"Error contando plazas del contrato {contrato_id}: {e}")
            raise DatabaseError(f"Error de base de datos: {str(e)}")

    async def contar_por_categoria_puesto(
        self,
        categoria_puesto_id: int,
        incluir_canceladas: bool = False,
    ) -> int:
        try:
            query = (
                self.supabase.table(self.tabla)
                .select("id", count="exact")
                .eq("categoria_puesto_id", categoria_puesto_id)
            )
            if not incluir_canceladas:
                query = query.neq("estatus", EstatusPlaza.CANCELADA.value)
            result = query.execute()
            return result.count if result.count is not None else 0
        except Exception as e:
            logger.error(
                "Error contando plazas de la categoría %s: %s",
                categoria_puesto_id,
                e,
            )
            raise DatabaseError(f"Error de base de datos: {str(e)}")

    async def contar_vigentes_por_categoria(
        self,
        contrato_id: int,
        fecha_referencia: Optional[date] = None,
    ) -> dict[int, int]:
        try:
            fecha = (fecha_referencia or date.today()).isoformat()
            result = (
                self.supabase.table(self.tabla)
                .select("categoria_puesto_id, fecha_inicio, fecha_fin, estatus")
                .eq("contrato_id", contrato_id)
                .neq("estatus", EstatusPlaza.CANCELADA.value)
                .not_.is_("categoria_puesto_id", "null")
                .lte("fecha_inicio", fecha)
                .or_(f"fecha_fin.is.null,fecha_fin.gte.{fecha}")
                .execute()
            )
            conteo: dict[int, int] = {}
            for item in (result.data or []):
                categoria_id = item.get("categoria_puesto_id")
                if categoria_id is None:
                    continue
                conteo[categoria_id] = conteo.get(categoria_id, 0) + 1
            return conteo
        except Exception as e:
            logger.error(f"Error contando plazas vigentes por categoría contrato={contrato_id}: {e}")
            raise DatabaseError(f"Error de base de datos: {str(e)}")

    async def _obtener_empleados_map(self, empleado_ids: list[int]) -> dict[int, dict]:
        if not empleado_ids:
            return {}
        result = (
            self.supabase.table("empleados")
            .select("id, uuid, nombre, apellido_paterno, apellido_materno, curp")
            .in_("id", empleado_ids)
            .execute()
        )
        empleados_map: dict[int, dict] = {}
        for emp in (result.data or []):
            nombre = " ".join(
                part for part in [
                    emp.get("nombre", ""),
                    emp.get("apellido_paterno", ""),
                    emp.get("apellido_materno", ""),
                ]
                if part
            ).strip()
            empleados_map[emp["id"]] = {
                "nombre": nombre,
                "uuid": str(emp.get("uuid", "") or ""),
                "curp": emp.get("curp", ""),
            }
        return empleados_map

    async def _obtener_detalles_relacionados(
        self,
        contrato_ids: list[int],
        categoria_ids: list[int],
        sede_ids: list[int],
    ) -> tuple[dict[int, dict], dict[int, dict], dict[int, dict]]:
        contratos_map: dict[int, dict] = {}
        categorias_map: dict[int, dict] = {}
        sedes_map: dict[int, dict] = {}

        if contrato_ids:
            result_contratos = (
                self.supabase.table("contratos")
                .select("id, codigo, cantidad_plazas_minima, cantidad_plazas_maxima")
                .in_("id", contrato_ids)
                .execute()
            )
            contratos_map = {item["id"]: item for item in (result_contratos.data or [])}

        if categoria_ids:
            result_categorias = (
                self.supabase.table("categorias_puesto")
                .select("id, clave, nombre")
                .in_("id", categoria_ids)
                .execute()
            )
            categorias_map = {item["id"]: item for item in (result_categorias.data or [])}

        if sede_ids:
            result_sedes = (
                self.supabase.table("sedes")
                .select("id, codigo, nombre, nombre_corto")
                .in_("id", sede_ids)
                .execute()
            )
            sedes_map = {item["id"]: item for item in (result_sedes.data or [])}

        return contratos_map, categorias_map, sedes_map

    async def _construir_resumen(self, plazas_data: list[dict]) -> list[dict]:
        if not plazas_data:
            return []

        contrato_ids = sorted({item["contrato_id"] for item in plazas_data if item.get("contrato_id") is not None})
        categoria_ids = sorted({
            item["categoria_puesto_id"]
            for item in plazas_data
            if item.get("categoria_puesto_id") is not None
        })
        sede_ids = sorted({
            item["sede_id"]
            for item in plazas_data
            if item.get("sede_id") is not None
        })
        empleado_ids = sorted({
            item["empleado_id"]
            for item in plazas_data
            if item.get("empleado_id") is not None
        })

        contratos_map, categorias_map, sedes_map = await self._obtener_detalles_relacionados(
            contrato_ids,
            categoria_ids,
            sede_ids,
        )
        empleados_map = await self._obtener_empleados_map(empleado_ids)

        resumen: list[dict] = []
        for item in plazas_data:
            contrato = contratos_map.get(item["contrato_id"], {})
            categoria = categorias_map.get(item.get("categoria_puesto_id"), {})
            sede = sedes_map.get(item.get("sede_id"), {})
            empleado = empleados_map.get(item.get("empleado_id"), {})
            resumen.append({
                **item,
                "contrato_codigo": contrato.get("codigo", ""),
                "sede_codigo": sede.get("codigo", ""),
                "sede_nombre": (
                    sede.get("nombre_corto")
                    or sede.get("nombre")
                    or "Sin sede"
                ) if item.get("sede_id") else "Sin sede",
                "categoria_clave": categoria.get("clave", ""),
                "categoria_nombre": categoria.get("nombre", "Sin categoría") if item.get("categoria_puesto_id") else "Sin categoría",
                "empleado_nombre": empleado.get("nombre", ""),
                "empleado_uuid": empleado.get("uuid", ""),
                "empleado_curp": empleado.get("curp", ""),
            })
        return resumen

    async def obtener_resumen_por_contrato(
        self,
        contrato_id: int,
        incluir_canceladas: bool = False,
        limite: Optional[int] = None,
        offset: int = 0,
    ) -> list[dict]:
        try:
            query = self.supabase.table(self.tabla).select("*").eq("contrato_id", contrato_id)
            if not incluir_canceladas:
                query = query.neq("estatus", EstatusPlaza.CANCELADA.value)
            query = query.order("numero_plaza", desc=False)
            if limite is not None:
                query = query.range(offset, offset + limite - 1)
            result = query.execute()
            return await self._construir_resumen(result.data or [])
        except Exception as e:
            logger.error(f"Error obteniendo resumen de plazas del contrato {contrato_id}: {e}")
            raise DatabaseError(f"Error de base de datos: {str(e)}")

    async def obtener_resumen_ocupadas_por_empresa(self, empresa_id: int) -> list[dict]:
        try:
            contratos_result = (
                self.supabase.table("contratos")
                .select("id")
                .eq("empresa_id", empresa_id)
                .execute()
            )
            contrato_ids = [
                int(item.get("id") or 0)
                for item in (contratos_result.data or [])
                if int(item.get("id") or 0) > 0
            ]
            if not contrato_ids:
                return []

            result = (
                self.supabase.table(self.tabla)
                .select("*")
                .in_("contrato_id", contrato_ids)
                .eq("estatus", EstatusPlaza.OCUPADA.value)
                .not_.is_("empleado_id", "null")
                .order("contrato_id", desc=False)
                .order("numero_plaza", desc=False)
                .execute()
            )
            return await self._construir_resumen(result.data or [])
        except Exception as e:
            logger.error(
                "Error obteniendo resumen de plazas ocupadas empresa=%s: %s",
                empresa_id,
                e,
            )
            raise DatabaseError(f"Error de base de datos: {str(e)}")

    async def obtener_resumen_por_categoria(
        self,
        contrato_id: int,
        categoria_puesto_id: int,
        incluir_canceladas: bool = False,
    ) -> list[dict]:
        try:
            query = (
                self.supabase.table(self.tabla)
                .select("*")
                .eq("contrato_id", contrato_id)
                .eq("categoria_puesto_id", categoria_puesto_id)
            )
            if not incluir_canceladas:
                query = query.neq("estatus", EstatusPlaza.CANCELADA.value)
            result = query.order("numero_plaza", desc=False).execute()
            return await self._construir_resumen(result.data or [])
        except Exception as e:
            logger.error(f"Error obteniendo resumen por categoría contrato={contrato_id}, categoria={categoria_puesto_id}: {e}")
            raise DatabaseError(f"Error de base de datos: {str(e)}")

    async def obtener_totales_por_contrato(self, contrato_id: int) -> dict:
        try:
            plazas = await self.obtener_por_contrato(contrato_id, incluir_canceladas=True)
            result_contrato = (
                self.supabase.table("contratos")
                .select("cantidad_plazas_minima, cantidad_plazas_maxima")
                .eq("id", contrato_id)
                .limit(1)
                .execute()
            )
            contrato = (result_contrato.data or [{}])[0]

            totales = {
                "total_plazas": len(plazas),
                "plazas_vacantes": 0,
                "plazas_ocupadas": 0,
                "plazas_suspendidas": 0,
                "plazas_canceladas": 0,
                "plazas_categorizadas": 0,
                "plazas_sin_categoria": 0,
                "cantidad_plazas_minima": int(contrato.get("cantidad_plazas_minima") or 0),
                "cantidad_plazas_maxima": int(contrato.get("cantidad_plazas_maxima") or 0),
                "costo_total_mensual": Decimal("0"),
            }

            for plaza in plazas:
                if plaza.estatus == EstatusPlaza.VACANTE:
                    totales["plazas_vacantes"] += 1
                elif plaza.estatus == EstatusPlaza.OCUPADA:
                    totales["plazas_ocupadas"] += 1
                elif plaza.estatus == EstatusPlaza.SUSPENDIDA:
                    totales["plazas_suspendidas"] += 1
                elif plaza.estatus == EstatusPlaza.CANCELADA:
                    totales["plazas_canceladas"] += 1

                if plaza.categoria_puesto_id is None:
                    totales["plazas_sin_categoria"] += 1
                else:
                    totales["plazas_categorizadas"] += 1

                if plaza.estatus != EstatusPlaza.CANCELADA:
                    totales["costo_total_mensual"] += plaza.salario_mensual

            maximo = totales["cantidad_plazas_maxima"]
            totales["plazas_desfase"] = max(0, totales["total_plazas"] - maximo) if maximo else 0
            return totales
        except Exception as e:
            logger.error(f"Error calculando totales del contrato {contrato_id}: {e}")
            raise DatabaseError(f"Error de base de datos: {str(e)}")

    async def obtener_resumen_categorias_con_plazas(self, empresa_id: Optional[int] = None) -> list[dict]:
        try:
            query = self.supabase.table(self.tabla).select("*").neq("estatus", EstatusPlaza.CANCELADA.value)
            if empresa_id:
                result_contratos = (
                    self.supabase.table("contratos")
                    .select("id")
                    .eq("empresa_id", empresa_id)
                    .execute()
                )
                contrato_ids = [item["id"] for item in (result_contratos.data or [])]
                if not contrato_ids:
                    return []
                query = query.in_("contrato_id", contrato_ids)

            result = query.execute()
            plazas = result.data or []
            if not plazas:
                return []

            contrato_ids = sorted({item["contrato_id"] for item in plazas})
            categoria_ids = sorted({
                item["categoria_puesto_id"] for item in plazas if item.get("categoria_puesto_id") is not None
            })
            contratos_map, categorias_map, _ = await self._obtener_detalles_relacionados(contrato_ids, categoria_ids, [])

            agrupados: dict[tuple[int, Optional[int]], dict] = {}
            for item in plazas:
                key = (item["contrato_id"], item.get("categoria_puesto_id"))
                contrato = contratos_map.get(item["contrato_id"], {})
                categoria_id = item.get("categoria_puesto_id")
                categoria = categorias_map.get(categoria_id, {})
                if key not in agrupados:
                    agrupados[key] = {
                        "contrato_id": item["contrato_id"],
                        "contrato_codigo": contrato.get("codigo", ""),
                        "categoria_puesto_id": categoria_id,
                        "categoria_clave": categoria.get("clave", ""),
                        "categoria_nombre": categoria.get("nombre", "Sin categoría") if categoria_id else "Sin categoría",
                        "cantidad_esperada": 0,
                        "total_plazas": 0,
                        "plazas_vacantes": 0,
                        "plazas_ocupadas": 0,
                        "plazas_suspendidas": 0,
                    }
                agrupado = agrupados[key]
                agrupado["total_plazas"] += 1
                if item["estatus"] == EstatusPlaza.VACANTE.value:
                    agrupado["plazas_vacantes"] += 1
                elif item["estatus"] == EstatusPlaza.OCUPADA.value:
                    agrupado["plazas_ocupadas"] += 1
                elif item["estatus"] == EstatusPlaza.SUSPENDIDA.value:
                    agrupado["plazas_suspendidas"] += 1
                agrupado["cantidad_esperada"] = agrupado["total_plazas"]

            return sorted(
                agrupados.values(),
                key=lambda item: (
                    item["contrato_codigo"],
                    item["categoria_clave"] or "ZZZ",
                    item["categoria_nombre"],
                ),
            )
        except Exception as e:
            logger.error(f"Error obteniendo resumen por categorías con plazas: {e}")
            raise DatabaseError(f"Error de base de datos: {str(e)}")

    async def obtener_resumen_contratos_con_plazas(
        self,
        empresa_id: Optional[int] = None,
        solo_activos: bool = False,
    ) -> list[dict]:
        try:
            contratos_query = (
                self.supabase.table("contratos")
                .select(
                    "id, codigo, estatus, tipo_servicio_id, tiene_personal, "
                    "cantidad_plazas_minima, cantidad_plazas_maxima"
                )
                .eq("tiene_personal", True)
            )
            if empresa_id:
                contratos_query = contratos_query.eq("empresa_id", empresa_id)
            if solo_activos:
                contratos_query = contratos_query.eq("estatus", "ACTIVO")

            contratos_result = contratos_query.order("codigo", desc=False).execute()
            contratos = contratos_result.data or []
            if not contratos:
                return []

            tipo_servicio_ids = sorted(
                {
                    contrato.get("tipo_servicio_id")
                    for contrato in contratos
                    if contrato.get("tipo_servicio_id") is not None
                }
            )
            tipos_servicio_map: dict[int, dict] = {}
            if tipo_servicio_ids:
                tipos_result = (
                    self.supabase.table("tipos_servicio")
                    .select("id, clave, nombre")
                    .in_("id", tipo_servicio_ids)
                    .execute()
                )
                tipos_servicio_map = {
                    item["id"]: item for item in (tipos_result.data or [])
                }

            resumen = {
                contrato["id"]: {
                    "contrato_id": contrato["id"],
                    "contrato_codigo": contrato.get("codigo", ""),
                    "contrato_estatus": contrato.get("estatus", ""),
                    "tipo_servicio_id": contrato.get("tipo_servicio_id"),
                    "tipo_servicio_clave": (
                        tipos_servicio_map.get(
                            contrato.get("tipo_servicio_id"), {}
                        ).get("clave", "")
                    ),
                    "tipo_servicio_nombre": (
                        tipos_servicio_map.get(
                            contrato.get("tipo_servicio_id"), {}
                        ).get("nombre", "Sin tipo de servicio")
                    ),
                    "cantidad_plazas_minima": int(
                        contrato.get("cantidad_plazas_minima") or 0
                    ),
                    "cantidad_plazas_maxima": int(
                        contrato.get("cantidad_plazas_maxima") or 0
                    ),
                    "total_plazas": 0,
                    "plazas_vacantes": 0,
                    "plazas_ocupadas": 0,
                    "plazas_suspendidas": 0,
                    "total_sedes": 0,
                    "_sede_ids": set(),
                }
                for contrato in contratos
            }

            contrato_ids = list(resumen.keys())
            plazas_result = (
                self.supabase.table(self.tabla)
                .select("contrato_id, estatus, sede_id")
                .in_("contrato_id", contrato_ids)
                .neq("estatus", EstatusPlaza.CANCELADA.value)
                .execute()
            )

            for plaza in (plazas_result.data or []):
                contrato_id = plaza.get("contrato_id")
                if contrato_id not in resumen:
                    continue

                item = resumen[contrato_id]
                item["total_plazas"] += 1
                sede_id = plaza.get("sede_id")
                if sede_id is not None:
                    item["_sede_ids"].add(sede_id)

                if plaza.get("estatus") == EstatusPlaza.VACANTE.value:
                    item["plazas_vacantes"] += 1
                elif plaza.get("estatus") == EstatusPlaza.OCUPADA.value:
                    item["plazas_ocupadas"] += 1
                elif plaza.get("estatus") == EstatusPlaza.SUSPENDIDA.value:
                    item["plazas_suspendidas"] += 1

            salida: list[dict] = []
            for item in resumen.values():
                item["total_sedes"] = len(item.pop("_sede_ids", set()))
                salida.append(item)

            return salida
        except Exception as e:
            logger.error(f"Error obteniendo resumen de contratos con plazas: {e}")
            raise DatabaseError(f"Error de base de datos: {str(e)}")

    async def obtener_empleados_asignados(self, empresa_id: Optional[int] = None) -> list[int]:
        try:
            query = (
                self.supabase.table(self.tabla)
                .select("empleado_id")
                .eq("estatus", EstatusPlaza.OCUPADA.value)
                .not_.is_("empleado_id", "null")
            )
            if empresa_id:
                result_contratos = (
                    self.supabase.table("contratos")
                    .select("id")
                    .eq("empresa_id", empresa_id)
                    .execute()
                )
                contrato_ids = [item["id"] for item in (result_contratos.data or [])]
                if not contrato_ids:
                    return []
                query = query.in_("contrato_id", contrato_ids)
            result = query.execute()
            return sorted({
                item["empleado_id"]
                for item in (result.data or [])
                if item.get("empleado_id") is not None
            })
        except Exception as e:
            logger.error(f"Error obteniendo empleados asignados: {e}")
            raise DatabaseError(f"Error de base de datos: {str(e)}")

    async def empleado_tiene_plaza_activa_con_categoria(
        self,
        empleado_id: int,
        *,
        excluir_plaza_id: Optional[int] = None,
    ) -> bool:
        try:
            query = (
                self.supabase.table(self.tabla)
                .select("id", count="exact")
                .eq("empleado_id", empleado_id)
                .eq("estatus", EstatusPlaza.OCUPADA.value)
                .not_.is_("categoria_puesto_id", "null")
            )
            if excluir_plaza_id is not None:
                query = query.neq("id", excluir_plaza_id)
            result = query.limit(1).execute()
            return bool((result.count or 0) > 0)
        except Exception as e:
            logger.error(
                "Error validando plaza activa con categoría para empleado %s: %s",
                empleado_id,
                e,
            )
            raise DatabaseError(f"Error de base de datos: {str(e)}")

    async def obtener_resumen_por_estatus(
        self,
        estatus: EstatusPlaza,
        limite: int = 100,
    ) -> list[dict]:
        try:
            result = (
                self.supabase.table(self.tabla)
                .select("*")
                .eq("estatus", estatus.value)
                .limit(limite)
                .order("fecha_actualizacion", desc=True)
                .execute()
            )
            return await self._construir_resumen(result.data or [])
        except Exception as e:
            logger.error(f"Error obteniendo plazas por estatus {estatus}: {e}")
            raise DatabaseError(f"Error de base de datos: {str(e)}")
