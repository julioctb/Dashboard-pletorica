"""
Servicio de Historial Laboral.

Este servicio es principalmente de LECTURA para la UI.
Los métodos de escritura son INTERNOS y se llaman automáticamente
desde empleado_service cuando ocurren eventos relevantes.

IMPORTANTE: NO exponer métodos de escritura en la UI.
Los registros se crean automáticamente cuando:
- Se crea un empleado (ALTA)
- Se asigna un empleado a una plaza (ASIGNACION)
- Se cambia de plaza (CAMBIO_PLAZA)
- Se suspende un empleado (SUSPENSION)
- Se reactiva un empleado (REACTIVACION)
- Se da de baja un empleado (BAJA)
"""
from typing import List, Optional
from datetime import date
import logging

from app.repositories.historial_laboral_repository import (
    SupabaseHistorialLaboralRepository,
)
from app.entities.historial_laboral import (
    HistorialLaboral,
    HistorialLaboralInterno,
    HistorialLaboralResumen,
)
from app.core.enums import EstatusHistorial, TipoMovimiento, EstatusPlaza
from app.core.exceptions import DatabaseError

logger = logging.getLogger(__name__)


class HistorialLaboralService:
    """
    Servicio para gestionar el historial laboral.

    El historial es una bitácora automática de movimientos de empleados.
    Los registros se crean automáticamente desde el empleado_service.
    """

    def __init__(self, repository=None):
        self.repository = repository or SupabaseHistorialLaboralRepository()

    # =========================================================================
    # MÉTODOS DE LECTURA (para UI)
    # =========================================================================

    async def obtener_por_id(self, historial_id: int) -> HistorialLaboral:
        """Obtiene un registro por ID"""
        return await self.repository.obtener_por_id(historial_id)

    async def obtener_por_empleado(
        self,
        empleado_id: int,
        limite: int = 50
    ) -> List[HistorialLaboralResumen]:
        """Obtiene el historial completo de un empleado"""
        return await self.repository.obtener_por_empleado(empleado_id, limite)

    async def obtener_todos(
        self,
        empleado_id: Optional[int] = None,
        estatus: Optional[str] = None,
        limite: int = 50,
        offset: int = 0
    ) -> List[HistorialLaboralResumen]:
        """Obtiene registros con filtros opcionales"""
        return await self.repository.obtener_todos(
            empleado_id=empleado_id,
            estatus=estatus,
            limite=limite,
            offset=offset
        )

    async def contar(
        self,
        empleado_id: Optional[int] = None,
        estatus: Optional[str] = None
    ) -> int:
        """Cuenta registros con filtros"""
        return await self.repository.contar(empleado_id, estatus)

    async def obtener_registro_activo(self, empleado_id: int) -> Optional[HistorialLaboral]:
        """Obtiene el registro activo (sin fecha_fin) de un empleado"""
        return await self.repository.obtener_registro_activo(empleado_id)

    # =========================================================================
    # MÉTODOS INTERNOS DE ESCRITURA (llamados desde empleado_service)
    # =========================================================================

    async def registrar_alta(
        self,
        empleado_id: int,
        plaza_id: Optional[int] = None,
        fecha: Optional[date] = None,
        notas: Optional[str] = None
    ) -> HistorialLaboral:
        """
        Registra el alta de un empleado en el sistema.

        Si tiene plaza asignada → estatus ACTIVO
        Si no tiene plaza → estatus INACTIVO

        Se llama automáticamente desde empleado_service.crear()
        """
        # Determinar estatus según si tiene plaza o no
        estatus = EstatusHistorial.ACTIVO if plaza_id else EstatusHistorial.INACTIVO

        datos = HistorialLaboralInterno(
            empleado_id=empleado_id,
            plaza_id=plaza_id,
            tipo_movimiento=TipoMovimiento.ALTA,
            fecha_inicio=fecha or date.today(),
            estatus=estatus,
            notas=notas or "Alta en el sistema"
        )

        historial = await self.repository.crear(datos)

        # Si hay plaza, marcarla como ocupada
        if plaza_id:
            await self._actualizar_estatus_plaza(plaza_id, EstatusPlaza.OCUPADA)

        logger.info(f"Registrada ALTA de empleado {empleado_id}, estatus={estatus}")
        return historial

    async def registrar_asignacion(
        self,
        empleado_id: int,
        plaza_id: int,
        fecha: Optional[date] = None,
        notas: Optional[str] = None
    ) -> HistorialLaboral:
        """
        Registra la asignación de un empleado a una plaza.

        Cierra el registro anterior (si existe) y crea uno nuevo.
        Se llama automáticamente cuando se asigna empleado a plaza.
        """
        fecha_movimiento = fecha or date.today()

        # Cerrar registro activo anterior (si existe)
        await self.repository.cerrar_registro_activo(empleado_id, fecha_movimiento)

        # Crear nuevo registro
        datos = HistorialLaboralInterno(
            empleado_id=empleado_id,
            plaza_id=plaza_id,
            tipo_movimiento=TipoMovimiento.ASIGNACION,
            fecha_inicio=fecha_movimiento,
            estatus=EstatusHistorial.ACTIVO,
            notas=notas or f"Asignación a plaza {plaza_id}"
        )

        historial = await self.repository.crear(datos)

        # Marcar plaza como ocupada
        await self._actualizar_estatus_plaza(plaza_id, EstatusPlaza.OCUPADA)

        logger.info(f"Registrada ASIGNACION de empleado {empleado_id} a plaza {plaza_id}")
        return historial

    async def registrar_cambio_plaza(
        self,
        empleado_id: int,
        nueva_plaza_id: int,
        fecha: Optional[date] = None,
        notas: Optional[str] = None
    ) -> HistorialLaboral:
        """
        Registra el cambio de plaza de un empleado.

        Cierra el registro anterior, libera la plaza anterior,
        y crea nuevo registro con la nueva plaza.
        """
        fecha_movimiento = fecha or date.today()

        # Obtener registro activo para saber la plaza anterior
        registro_activo = await self.repository.obtener_registro_activo(empleado_id)
        plaza_anterior_id = registro_activo.plaza_id if registro_activo else None

        # Cerrar registro activo
        await self.repository.cerrar_registro_activo(empleado_id, fecha_movimiento)

        # Liberar plaza anterior si existe
        if plaza_anterior_id:
            await self._actualizar_estatus_plaza(plaza_anterior_id, EstatusPlaza.VACANTE)

        # Crear nuevo registro
        nota_final = notas or f"Cambio de plaza {plaza_anterior_id or 'sin plaza'} a {nueva_plaza_id}"
        datos = HistorialLaboralInterno(
            empleado_id=empleado_id,
            plaza_id=nueva_plaza_id,
            tipo_movimiento=TipoMovimiento.CAMBIO_PLAZA,
            fecha_inicio=fecha_movimiento,
            estatus=EstatusHistorial.ACTIVO,
            notas=nota_final
        )

        historial = await self.repository.crear(datos)

        # Marcar nueva plaza como ocupada
        await self._actualizar_estatus_plaza(nueva_plaza_id, EstatusPlaza.OCUPADA)

        logger.info(f"Registrado CAMBIO_PLAZA de empleado {empleado_id}: {plaza_anterior_id} -> {nueva_plaza_id}")
        return historial

    async def registrar_suspension(
        self,
        empleado_id: int,
        fecha: Optional[date] = None,
        notas: Optional[str] = None
    ) -> HistorialLaboral:
        """
        Registra la suspensión de un empleado.

        Cierra el registro anterior, libera la plaza (si tiene),
        y crea nuevo registro con estatus SUSPENDIDO.
        """
        fecha_movimiento = fecha or date.today()

        # Obtener registro activo para saber la plaza
        registro_activo = await self.repository.obtener_registro_activo(empleado_id)
        plaza_id = registro_activo.plaza_id if registro_activo else None

        # Cerrar registro activo
        await self.repository.cerrar_registro_activo(empleado_id, fecha_movimiento)

        # Liberar plaza si existe
        if plaza_id:
            await self._actualizar_estatus_plaza(plaza_id, EstatusPlaza.VACANTE)

        # Crear nuevo registro de suspensión (sin plaza)
        datos = HistorialLaboralInterno(
            empleado_id=empleado_id,
            plaza_id=None,  # Suspendido no tiene plaza
            tipo_movimiento=TipoMovimiento.SUSPENSION,
            fecha_inicio=fecha_movimiento,
            estatus=EstatusHistorial.SUSPENDIDO,
            notas=notas or "Suspensión temporal"
        )

        historial = await self.repository.crear(datos)

        logger.info(f"Registrada SUSPENSION de empleado {empleado_id}")
        return historial

    async def registrar_reactivacion(
        self,
        empleado_id: int,
        plaza_id: Optional[int] = None,
        fecha: Optional[date] = None,
        notas: Optional[str] = None
    ) -> HistorialLaboral:
        """
        Registra la reactivación de un empleado.

        Cierra el registro de suspensión y crea nuevo registro.
        Si se especifica plaza, el empleado queda ACTIVO.
        Si no hay plaza, queda INACTIVO (disponible para asignación).
        """
        fecha_movimiento = fecha or date.today()

        # Cerrar registro de suspensión
        await self.repository.cerrar_registro_activo(empleado_id, fecha_movimiento)

        # Determinar estatus según si tiene plaza
        estatus = EstatusHistorial.ACTIVO if plaza_id else EstatusHistorial.INACTIVO

        # Crear nuevo registro
        datos = HistorialLaboralInterno(
            empleado_id=empleado_id,
            plaza_id=plaza_id,
            tipo_movimiento=TipoMovimiento.REACTIVACION,
            fecha_inicio=fecha_movimiento,
            estatus=estatus,
            notas=notas or "Reactivación de empleado"
        )

        historial = await self.repository.crear(datos)

        # Si hay plaza, marcarla como ocupada
        if plaza_id:
            await self._actualizar_estatus_plaza(plaza_id, EstatusPlaza.OCUPADA)

        logger.info(f"Registrada REACTIVACION de empleado {empleado_id}, estatus={estatus}")
        return historial

    async def registrar_baja(
        self,
        empleado_id: int,
        fecha: Optional[date] = None,
        notas: Optional[str] = None
    ) -> HistorialLaboral:
        """
        Registra la baja de un empleado del sistema.

        Cierra el registro anterior, libera la plaza (si tiene),
        y crea nuevo registro con estatus INACTIVO y tipo BAJA.
        """
        fecha_movimiento = fecha or date.today()

        # Obtener registro activo para saber la plaza
        registro_activo = await self.repository.obtener_registro_activo(empleado_id)
        plaza_id = registro_activo.plaza_id if registro_activo else None

        # Cerrar registro activo
        await self.repository.cerrar_registro_activo(empleado_id, fecha_movimiento)

        # Liberar plaza si existe
        if plaza_id:
            await self._actualizar_estatus_plaza(plaza_id, EstatusPlaza.VACANTE)

        # Crear nuevo registro de baja (sin plaza, inactivo)
        datos = HistorialLaboralInterno(
            empleado_id=empleado_id,
            plaza_id=None,
            tipo_movimiento=TipoMovimiento.BAJA,
            fecha_inicio=fecha_movimiento,
            estatus=EstatusHistorial.INACTIVO,
            notas=notas or "Baja del sistema"
        )

        historial = await self.repository.crear(datos)

        logger.info(f"Registrada BAJA de empleado {empleado_id}")
        return historial

    async def liberar_plaza_empleado(
        self,
        empleado_id: int,
        fecha: Optional[date] = None
    ) -> Optional[HistorialLaboral]:
        """
        Libera la plaza de un empleado sin cambiar su estatus general.

        Usado cuando se desasigna un empleado de una plaza
        pero sigue disponible para otras asignaciones.
        """
        fecha_movimiento = fecha or date.today()

        # Obtener registro activo
        registro_activo = await self.repository.obtener_registro_activo(empleado_id)
        if not registro_activo or not registro_activo.plaza_id:
            return None  # No tiene plaza que liberar

        plaza_id = registro_activo.plaza_id

        # Cerrar registro activo
        await self.repository.cerrar_registro_activo(empleado_id, fecha_movimiento)

        # Liberar plaza
        await self._actualizar_estatus_plaza(plaza_id, EstatusPlaza.VACANTE)

        # Crear nuevo registro sin plaza
        datos = HistorialLaboralInterno(
            empleado_id=empleado_id,
            plaza_id=None,
            tipo_movimiento=TipoMovimiento.ASIGNACION,  # Desasignación
            fecha_inicio=fecha_movimiento,
            estatus=EstatusHistorial.INACTIVO,
            notas=f"Desasignación de plaza {plaza_id}"
        )

        historial = await self.repository.crear(datos)

        logger.info(f"Liberada plaza {plaza_id} de empleado {empleado_id}")
        return historial

    # =========================================================================
    # HELPERS
    # =========================================================================

    async def _actualizar_estatus_plaza(
        self,
        plaza_id: int,
        nuevo_estatus: EstatusPlaza
    ) -> None:
        """Actualiza el estatus de una plaza"""
        try:
            from app.repositories.plaza_repository import SupabasePlazaRepository
            plaza_repo = SupabasePlazaRepository()
            await plaza_repo.cambiar_estatus(plaza_id, nuevo_estatus)
        except Exception as e:
            logger.error(f"Error actualizando estatus de plaza {plaza_id}: {e}")
            # No lanzamos excepción para no interrumpir el flujo principal


# =============================================================================
# SINGLETON
# =============================================================================

historial_laboral_service = HistorialLaboralService()
