"""
Servicio orquestador para el proceso de baja de empleados.

Patron Orquestador: coordina empleado_service y notificacion_service.
Accede directo a tabla bajas_empleado.

Plazos reales:
- Liquidacion/finiquito: 15 dias habiles (con alerta)
- Comunicación al cliente: sin deadline estricto
- Sustitucion: dato informativo
"""

import logging
from datetime import date, timedelta
from typing import List, Optional

from app.database import db_manager
from app.domain.enums import (
    EstatusBaja,
    EstatusLiquidacion,
    EstatusEmpleado,
)
from app.core.exceptions import (
    BusinessRuleError,
    DatabaseError,
    NotFoundError,
)
from app.domain.models.baja_empleado import (
    BajaEmpleado,
    BajaEmpleadoCreate,
    BajaEmpleadoResumen,
)

logger = logging.getLogger(__name__)


class BajaService:
    """Orquestador del flujo de baja de empleados."""

    def __init__(self):
        self.supabase = db_manager.get_client()
        self.tabla = "bajas_empleado"

    def _calcular_fecha_limite(self, fecha_base: date, dias_habiles: int) -> date:
        """Calcula fecha limite sumando dias habiles (lun-vie)."""
        dias_agregados = 0
        fecha = fecha_base
        while dias_agregados < dias_habiles:
            fecha += timedelta(days=1)
            if fecha.weekday() < 5:
                dias_agregados += 1
        return fecha

    async def _obtener_baja_por_id(self, baja_id: int) -> BajaEmpleado:
        """Obtiene una baja por ID o lanza NotFoundError."""
        try:
            result = (
                self.supabase.table(self.tabla).select("*").eq("id", baja_id).execute()
            )
            if not result.data:
                raise NotFoundError(f"Baja {baja_id} no encontrada")
            return BajaEmpleado(**result.data[0])
        except NotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error obteniendo baja {baja_id}: {e}")
            raise DatabaseError(f"Error obteniendo baja: {e}")

    async def _obtener_baja_activa(self, empleado_id: int) -> Optional[BajaEmpleado]:
        """Verifica si el empleado tiene una baja activa."""
        try:
            result = (
                self.supabase.table(self.tabla)
                .select("*")
                .eq("empleado_id", empleado_id)
                .neq("estatus", EstatusBaja.CERRADA.value)
                .neq("estatus", EstatusBaja.CANCELADA.value)
                .limit(1)
                .execute()
            )
            if result.data:
                return BajaEmpleado(**result.data[0])
            return None
        except Exception as e:
            logger.error(f"Error validando baja activa empleado {empleado_id}: {e}")
            raise DatabaseError(f"Error validando baja activa: {e}")

    async def obtener_ultimas_bajas_por_empleados(
        self,
        empleado_ids: list[int],
    ) -> dict[int, dict]:
        """
        Obtiene la ultima baja no cancelada por empleado.

        Se usa para enriquecer listados y detalles sin depender de las
        columnas legacy fecha_baja/motivo_baja en empleados.
        """
        if not empleado_ids:
            return {}

        try:
            result = (
                self.supabase.table(self.tabla)
                .select("empleado_id, motivo, fecha_efectiva, estatus, fecha_creacion")
                .in_("empleado_id", empleado_ids)
                .neq("estatus", EstatusBaja.CANCELADA.value)
                .order("fecha_efectiva", desc=True)
                .order("fecha_creacion", desc=True)
                .execute()
            )
        except Exception as e:
            logger.error("Error obteniendo ultimas bajas por empleados: %s", e)
            raise DatabaseError(f"Error consultando bajas: {e}")

        ultimas_bajas: dict[int, dict] = {}
        for row in result.data or []:
            empleado_id = int(row.get("empleado_id") or 0)
            if empleado_id <= 0 or empleado_id in ultimas_bajas:
                continue
            ultimas_bajas[empleado_id] = row

        return ultimas_bajas

    async def _actualizar_baja(self, baja: BajaEmpleado) -> BajaEmpleado:
        """Persiste cambios de una baja en BD."""
        payload = {
            "estatus": baja.estatus.value,
            "estatus_liquidacion": baja.estatus_liquidacion.value,
            "fecha_comunicacion_buap": (
                baja.fecha_comunicacion_buap.isoformat()
                if baja.fecha_comunicacion_buap
                else None
            ),
            "requiere_sustitucion": baja.requiere_sustitucion,
            "notas": baja.notas,
        }
        try:
            result = (
                self.supabase.table(self.tabla)
                .update(payload)
                .eq("id", baja.id)
                .execute()
            )
            if not result.data:
                raise DatabaseError(f"No se pudo actualizar la baja {baja.id}")
            return BajaEmpleado(**result.data[0])
        except DatabaseError:
            raise
        except Exception as e:
            logger.error(f"Error actualizando baja {baja.id}: {e}")
            raise DatabaseError(f"Error actualizando baja: {e}")

    async def registrar_baja(self, datos: BajaEmpleadoCreate) -> BajaEmpleado:
        """
        Registra una baja completa.

        1. Valida empleado activo y sin baja en proceso
        2. Obtiene plaza actual si no se proporciono
        3. Calcula fecha limite de liquidacion
        4. Libera la plaza actual si existe
        5. Sincroniza al empleado como INACTIVO
        6. Inserta en bajas_empleado
        7. Registra BAJA en historial
        8. Crea notificacion con plazo de liquidacion
        """
        from app.domain.services.empleado_service import empleado_service
        from app.domain.services.notificacion_service import notificacion_service
        from app.domain.models.notificacion import NotificacionCreate

        fecha_registro = date.today()
        if not datos.es_automatica and datos.fecha_efectiva < fecha_registro:
            raise BusinessRuleError(
                "La fecha efectiva no puede ser anterior a la fecha de registro"
            )

        empleado = await empleado_service.obtener_por_id(datos.empleado_id)
        if empleado.estatus != EstatusEmpleado.ACTIVO:
            raise BusinessRuleError(
                f"El empleado {empleado.clave} no esta activo "
                f"(estatus: {empleado.estatus})"
            )

        baja_existente = await self._obtener_baja_activa(datos.empleado_id)
        if baja_existente:
            raise BusinessRuleError(
                f"El empleado {empleado.clave} ya tiene una baja en proceso "
                f"(estatus: {baja_existente.estatus.descripcion})"
            )

        plaza_id = datos.plaza_id
        if not plaza_id:
            plaza_id = empleado.plaza_actual_id

        fecha_limite_liq = self._calcular_fecha_limite(datos.fecha_efectiva, 15)

        if plaza_id:
            from app.domain.services import plaza_service

            await plaza_service.liberar_plaza(plaza_id)
        else:
            await empleado_service.sincronizar_estatus_por_plazas(
                datos.empleado_id,
                tiene_plaza_activa=False,
            )

        try:
            payload = {
                "empleado_id": datos.empleado_id,
                "empresa_id": datos.empresa_id,
                "plaza_id": plaza_id,
                "motivo": datos.motivo.value,
                "fecha_registro": fecha_registro.isoformat(),
                "fecha_efectiva": datos.fecha_efectiva.isoformat(),
                "fecha_limite_liquidacion": fecha_limite_liq.isoformat(),
                "notas": datos.notas,
                "estatus": EstatusBaja.INICIADA.value,
                "estatus_liquidacion": EstatusLiquidacion.PENDIENTE.value,
                "registrado_por": (
                    str(datos.registrado_por) if datos.registrado_por else None
                ),
                "es_automatica": bool(datos.es_automatica),
                "contrato_id_origen": datos.contrato_id_origen,
            }
            result = self.supabase.table(self.tabla).insert(payload).execute()
            if not result.data:
                raise DatabaseError("No se pudo registrar la baja")
            baja = BajaEmpleado(**result.data[0])
        except DatabaseError:
            raise
        except Exception as e:
            logger.error(f"Error insertando baja: {e}")
            raise DatabaseError(f"Error registrando baja: {e}")

        try:
            from app.domain.services.historial_laboral_service import (
                historial_laboral_service,
            )

            await historial_laboral_service.registrar_baja(
                empleado_id=datos.empleado_id,
                fecha=datos.fecha_efectiva,
                notas=f"Baja por: {datos.motivo.descripcion}",
            )
        except Exception as e:
            logger.warning(f"Error registrando baja en historial: {e}")

        try:
            nombre = f"{empleado.nombre} {empleado.apellido_paterno}"
            await notificacion_service.crear(
                NotificacionCreate(
                    empresa_id=datos.empresa_id,
                    titulo="Baja de empleado registrada",
                    mensaje=(
                        f"Se registro la baja de {nombre} ({empleado.clave}) "
                        f"por {datos.motivo.descripcion}. "
                        f"Entregar liquidacion antes del {fecha_limite_liq.strftime('%d/%m/%Y')}."
                    ),
                    tipo="baja_registrada",
                    entidad_tipo="BAJA_EMPLEADO",
                    entidad_id=baja.id,
                )
            )
        except Exception as e:
            logger.warning(f"Error creando notificacion de baja: {e}")

        return baja

    async def comunicar_a_buap(
        self, baja_id: int, fecha: Optional[date] = None
    ) -> BajaEmpleado:
        """Registra que se comunicó la baja al cliente."""
        baja = await self._obtener_baja_por_id(baja_id)
        baja.comunicar(fecha)
        baja_actualizada = await self._actualizar_baja(baja)

        # Notificacion interna para admin/superadmin
        try:
            from app.domain.services.notificacion_service import notificacion_service
            from app.domain.models.notificacion import NotificacionCreate

            await notificacion_service.crear(
                NotificacionCreate(
                    empresa_id=baja.empresa_id,
                    titulo="Baja comunicada al cliente",
                    mensaje=(
                        f"Se comunicó al cliente la baja del empleado (baja #{baja.id}). "
                        f"Pendiente: entregar liquidación antes del "
                        f"{baja.fecha_limite_liquidacion.strftime('%d/%m/%Y')}."
                    ),
                    tipo="baja_comunicada",
                    entidad_tipo="BAJA_EMPLEADO",
                    entidad_id=baja.id,
                )
            )
        except Exception as e:
            logger.warning(f"Error creando notificacion de comunicacion: {e}")

        return baja_actualizada

    async def actualizar_sustitucion(
        self, baja_id: int, requiere: bool
    ) -> BajaEmpleado:
        """Registra si el cliente solicitó sustitución."""
        baja = await self._obtener_baja_por_id(baja_id)
        if not baja.es_proceso_activo:
            raise BusinessRuleError("Solo se puede actualizar en bajas activas")
        baja.requiere_sustitucion = requiere
        return await self._actualizar_baja(baja)

    async def registrar_liquidacion(self, baja_id: int) -> BajaEmpleado:
        """Marca liquidacion/finiquito como entregada."""
        baja = await self._obtener_baja_por_id(baja_id)
        baja.marcar_liquidada()
        return await self._actualizar_baja(baja)

    async def cerrar_baja(self, baja_id: int) -> BajaEmpleado:
        """Cierra el proceso de baja."""
        baja = await self._obtener_baja_por_id(baja_id)
        baja.cerrar()
        return await self._actualizar_baja(baja)

    async def cancelar_baja(self, baja_id: int, notas: str) -> BajaEmpleado:
        """
        Cancela la baja y retira la suspensión si aplica.
        """
        if not notas or len(notas.strip()) < 5:
            raise BusinessRuleError(
                "Debe indicar el motivo de cancelacion (minimo 5 caracteres)"
            )

        baja = await self._obtener_baja_por_id(baja_id)
        baja.cancelar(notas.strip())
        baja_actualizada = await self._actualizar_baja(baja)

        try:
            from app.domain.services.empleado_service import empleado_service

            await empleado_service.reactivar(baja.empleado_id)
        except Exception as e:
            logger.error(f"Error reactivando empleado {baja.empleado_id}: {e}")
            raise BusinessRuleError(
                f"Baja cancelada pero error al reactivar empleado: {e}"
            )

        return baja_actualizada

    async def obtener_bajas_empresa(
        self,
        empresa_id: int,
        solo_activas: bool = True,
    ) -> List[BajaEmpleadoResumen]:
        """Lista bajas de una empresa con datos resumidos del empleado."""
        try:
            query = (
                self.supabase.table(self.tabla)
                .select(
                    "*, empleados!bajas_empleado_empleado_id_fkey("
                    "clave, nombre, apellido_paterno)"
                )
                .eq("empresa_id", empresa_id)
                .order("fecha_creacion", desc=True)
            )

            if solo_activas:
                query = query.neq("estatus", EstatusBaja.CERRADA.value).neq(
                    "estatus", EstatusBaja.CANCELADA.value
                )

            result = query.execute()

            resumenes = []
            for row in result.data or []:
                emp = row.get("empleados", {}) or {}
                nombre = (
                    f"{emp.get('nombre', '')} {emp.get('apellido_paterno', '')}".strip()
                )
                clave = emp.get("clave", "")
                baja = BajaEmpleado(
                    **{k: v for k, v in row.items() if k != "empleados"}
                )

                resumenes.append(
                    BajaEmpleadoResumen(
                        id=baja.id,
                        empleado_id=baja.empleado_id,
                        empleado_nombre=nombre,
                        empleado_clave=clave,
                        motivo=(
                            baja.motivo.value
                            if hasattr(baja.motivo, "value")
                            else str(baja.motivo)
                        ),
                        fecha_efectiva=baja.fecha_efectiva,
                        estatus=baja.estatus.value,
                        estatus_liquidacion=baja.estatus_liquidacion.value,
                        dias_para_liquidar=baja.dias_para_liquidar,
                        requiere_sustitucion=baja.requiere_sustitucion,
                        fue_comunicada=baja.fue_comunicada,
                    )
                )

            return resumenes
        except Exception as e:
            logger.error(f"Error obteniendo bajas de empresa {empresa_id}: {e}")
            raise DatabaseError(f"Error consultando bajas: {e}")

    async def obtener_alertas_pendientes(self, empresa_id: int) -> List[dict]:
        """
        Bajas activas con alertas de liquidacion.
        """
        try:
            result = (
                self.supabase.table(self.tabla)
                .select(
                    "*, empleados!bajas_empleado_empleado_id_fkey("
                    "clave, nombre, apellido_paterno)"
                )
                .eq("empresa_id", empresa_id)
                .neq("estatus", EstatusBaja.CERRADA.value)
                .neq("estatus", EstatusBaja.CANCELADA.value)
                .execute()
            )

            alertas = []
            for row in result.data or []:
                baja = BajaEmpleado(
                    **{k: v for k, v in row.items() if k != "empleados"}
                )
                if baja.estatus not in (EstatusBaja.INICIADA, EstatusBaja.COMUNICADA):
                    continue
                emp = row.get("empleados", {}) or {}
                nombre = (
                    f"{emp.get('nombre', '')} {emp.get('apellido_paterno', '')}".strip()
                )
                clave = emp.get("clave", "")
                dias = baja.dias_para_liquidar

                if dias < 0:
                    alertas.append(
                        {
                            "baja_id": baja.id,
                            "tipo": "LIQUIDACION_VENCIDA",
                            "nivel": "critico",
                            "dias": abs(dias),
                            "empleado": nombre,
                            "clave": clave,
                            "mensaje": (
                                f"Liquidacion de {nombre} ({clave}): vencida "
                                f"hace {abs(dias)} dia(s)"
                            ),
                        }
                    )
                elif dias <= 5:
                    alertas.append(
                        {
                            "baja_id": baja.id,
                            "tipo": "LIQUIDACION_PROXIMA",
                            "nivel": "advertencia",
                            "dias": dias,
                            "empleado": nombre,
                            "clave": clave,
                            "mensaje": (
                                f"Liquidacion de {nombre} ({clave}): {dias} dia(s) restantes"
                            ),
                        }
                    )

            alertas.sort(
                key=lambda a: (0 if a["nivel"] == "critico" else 1, a.get("dias", 0))
            )
            return alertas
        except Exception as e:
            logger.error(f"Error obteniendo alertas de bajas: {e}")
            return []


baja_service = BajaService()
