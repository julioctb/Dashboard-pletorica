"""
Servicio orquestador para el proceso de baja de empleados.

Patron Orquestador: coordina empleado_service y notificacion_service.
Accede directo a tabla bajas_empleado.

Plazos reales:
- Liquidacion/finiquito: 15 dias habiles (con alerta)
- Comunicacion a BUAP: sin deadline estricto
- Sustitucion: dato informativo
"""
import logging
from datetime import date, timedelta
from typing import List, Optional

from app.database import db_manager
from app.core.enums import (
    EstatusBaja,
    EstatusLiquidacion,
    EstatusEmpleado,
)
from app.core.exceptions import (
    BusinessRuleError,
    DatabaseError,
    NotFoundError,
)
from app.entities.baja_empleado import (
    BajaEmpleado,
    BajaEmpleadoCreate,
    BajaEmpleadoResumen,
)

logger = logging.getLogger(__name__)


class BajaService:
    """Orquestador del flujo de baja de empleados."""

    def __init__(self):
        self.supabase = db_manager.get_client()
        self.tabla = 'bajas_empleado'

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
                self.supabase.table(self.tabla)
                .select('*')
                .eq('id', baja_id)
                .execute()
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
                .select('*')
                .eq('empleado_id', empleado_id)
                .neq('estatus', EstatusBaja.CERRADA.value)
                .neq('estatus', EstatusBaja.CANCELADA.value)
                .limit(1)
                .execute()
            )
            if result.data:
                return BajaEmpleado(**result.data[0])
            return None
        except Exception as e:
            logger.error(f"Error validando baja activa empleado {empleado_id}: {e}")
            raise DatabaseError(f"Error validando baja activa: {e}")

    async def _actualizar_baja(self, baja: BajaEmpleado) -> BajaEmpleado:
        """Persiste cambios de una baja en BD."""
        payload = {
            'estatus': baja.estatus.value,
            'estatus_liquidacion': baja.estatus_liquidacion.value,
            'fecha_comunicacion_buap': (
                baja.fecha_comunicacion_buap.isoformat()
                if baja.fecha_comunicacion_buap else None
            ),
            'requiere_sustitucion': baja.requiere_sustitucion,
            'notas': baja.notas,
        }
        try:
            result = (
                self.supabase.table(self.tabla)
                .update(payload)
                .eq('id', baja.id)
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
        4. Inserta en bajas_empleado
        5. Da de baja al empleado via empleado_service
        6. Crea notificacion con plazo de liquidacion
        """
        from app.services.empleado_service import empleado_service
        from app.services.notificacion_service import notificacion_service
        from app.entities.notificacion import NotificacionCreate

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
            try:
                from app.services.historial_laboral_service import historial_laboral_service

                registro = await historial_laboral_service.obtener_registro_activo(
                    datos.empleado_id
                )
                if registro:
                    plaza_id = registro.plaza_id
            except Exception as e:
                logger.warning(f"No se pudo obtener plaza activa: {e}")

        fecha_limite_liq = self._calcular_fecha_limite(datos.fecha_efectiva, 15)

        try:
            payload = {
                'empleado_id': datos.empleado_id,
                'empresa_id': datos.empresa_id,
                'plaza_id': plaza_id,
                'motivo': datos.motivo.value,
                'fecha_registro': date.today().isoformat(),
                'fecha_efectiva': datos.fecha_efectiva.isoformat(),
                'fecha_limite_liquidacion': fecha_limite_liq.isoformat(),
                'notas': datos.notas,
                'estatus': EstatusBaja.INICIADA.value,
                'estatus_liquidacion': EstatusLiquidacion.PENDIENTE.value,
                'registrado_por': (
                    str(datos.registrado_por) if datos.registrado_por else None
                ),
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

        await empleado_service.dar_de_baja(
            empleado_id=datos.empleado_id,
            motivo=datos.motivo,
            fecha_baja=datos.fecha_efectiva,
        )

        try:
            nombre = f"{empleado.nombre} {empleado.apellido_paterno}"
            await notificacion_service.crear(NotificacionCreate(
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
            ))
        except Exception as e:
            logger.warning(f"Error creando notificacion de baja: {e}")

        return baja

    async def comunicar_a_buap(
        self, baja_id: int, fecha: Optional[date] = None
    ) -> BajaEmpleado:
        """Registra que se comunico la baja a BUAP."""
        baja = await self._obtener_baja_por_id(baja_id)
        baja.comunicar(fecha)
        return await self._actualizar_baja(baja)

    async def actualizar_sustitucion(
        self, baja_id: int, requiere: bool
    ) -> BajaEmpleado:
        """Registra si BUAP solicito sustitucion."""
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
        Cancela la baja y reactiva al empleado.
        """
        if not notas or len(notas.strip()) < 5:
            raise BusinessRuleError(
                "Debe indicar el motivo de cancelacion (minimo 5 caracteres)"
            )

        baja = await self._obtener_baja_por_id(baja_id)
        baja.cancelar(notas.strip())
        baja_actualizada = await self._actualizar_baja(baja)

        try:
            from app.services.empleado_service import empleado_service

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
                    '*, empleados!bajas_empleado_empleado_id_fkey('
                    'clave, nombre, apellido_paterno)'
                )
                .eq('empresa_id', empresa_id)
                .order('fecha_creacion', desc=True)
            )

            if solo_activas:
                query = (
                    query.neq('estatus', EstatusBaja.CERRADA.value)
                    .neq('estatus', EstatusBaja.CANCELADA.value)
                )

            result = query.execute()

            resumenes = []
            for row in (result.data or []):
                emp = row.get('empleados', {}) or {}
                nombre = f"{emp.get('nombre', '')} {emp.get('apellido_paterno', '')}".strip()
                clave = emp.get('clave', '')
                baja = BajaEmpleado(**{k: v for k, v in row.items() if k != 'empleados'})

                resumenes.append(BajaEmpleadoResumen(
                    id=baja.id,
                    empleado_id=baja.empleado_id,
                    empleado_nombre=nombre,
                    empleado_clave=clave,
                    motivo=(
                        baja.motivo.value
                        if hasattr(baja.motivo, 'value') else str(baja.motivo)
                    ),
                    fecha_efectiva=baja.fecha_efectiva,
                    estatus=baja.estatus.value,
                    estatus_liquidacion=baja.estatus_liquidacion.value,
                    dias_para_liquidar=baja.dias_para_liquidar,
                    requiere_sustitucion=baja.requiere_sustitucion,
                    fue_comunicada=baja.fue_comunicada,
                ))

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
                    '*, empleados!bajas_empleado_empleado_id_fkey('
                    'clave, nombre, apellido_paterno)'
                )
                .eq('empresa_id', empresa_id)
                .neq('estatus', EstatusBaja.CERRADA.value)
                .neq('estatus', EstatusBaja.CANCELADA.value)
                .execute()
            )

            alertas = []
            for row in (result.data or []):
                baja = BajaEmpleado(**{k: v for k, v in row.items() if k != 'empleados'})
                if baja.estatus not in (EstatusBaja.INICIADA, EstatusBaja.COMUNICADA):
                    continue
                emp = row.get('empleados', {}) or {}
                nombre = f"{emp.get('nombre', '')} {emp.get('apellido_paterno', '')}".strip()
                clave = emp.get('clave', '')
                dias = baja.dias_para_liquidar

                if dias < 0:
                    alertas.append({
                        'baja_id': baja.id,
                        'tipo': 'LIQUIDACION_VENCIDA',
                        'nivel': 'critico',
                        'dias': abs(dias),
                        'empleado': nombre,
                        'clave': clave,
                        'mensaje': (
                            f"Liquidacion de {nombre} ({clave}): vencida "
                            f"hace {abs(dias)} dia(s)"
                        ),
                    })
                elif dias <= 5:
                    alertas.append({
                        'baja_id': baja.id,
                        'tipo': 'LIQUIDACION_PROXIMA',
                        'nivel': 'advertencia',
                        'dias': dias,
                        'empleado': nombre,
                        'clave': clave,
                        'mensaje': (
                            f"Liquidacion de {nombre} ({clave}): {dias} dia(s) restantes"
                        ),
                    })

            alertas.sort(
                key=lambda a: (0 if a['nivel'] == 'critico' else 1, a.get('dias', 0))
            )
            return alertas
        except Exception as e:
            logger.error(f"Error obteniendo alertas de bajas: {e}")
            return []


baja_service = BajaService()
