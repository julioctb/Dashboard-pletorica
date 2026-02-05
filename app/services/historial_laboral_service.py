"""
Servicio de Historial Laboral.

Este servicio es principalmente de LECTURA para la UI.
Los metodos de escritura son INTERNOS y se llaman automaticamente
desde empleado_service cuando ocurren eventos relevantes.

IMPORTANTE: NO exponer metodos de escritura en la UI.
Los registros se crean automaticamente cuando:
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

from app.repositories import SupabaseHistorialLaboralRepository
from app.core.exceptions import NotFoundError, DatabaseError
from app.entities.historial_laboral import (
    HistorialLaboral,
    HistorialLaboralInterno,
    HistorialLaboralResumen,
)
from app.core.enums import TipoMovimiento, EstatusPlaza

logger = logging.getLogger(__name__)


class HistorialLaboralService:
    """
    Servicio para gestionar el historial laboral.

    El historial es una bitacora automatica de movimientos de empleados.
    Los registros se crean automaticamente desde el empleado_service.
    """

    def __init__(self):
        self.repository = SupabaseHistorialLaboralRepository()

    # =========================================================================
    # METODOS DE LECTURA (para UI)
    # =========================================================================

    async def obtener_por_id(self, historial_id: int) -> HistorialLaboral:
        """
        Obtiene un registro por ID.

        Raises:
            NotFoundError: Si el registro no existe.
            DatabaseError: Si hay error de conexion/infraestructura.
        """
        return await self.repository.obtener_por_id(historial_id)

    async def obtener_por_empleado(
        self,
        empleado_id: int,
        limite: int = 50
    ) -> List[HistorialLaboralResumen]:
        """
        Obtiene el historial completo de un empleado con datos enriquecidos.

        Raises:
            DatabaseError: Si hay error de conexion/infraestructura.
        """
        try:
            rows = await self.repository.obtener_por_empleado_con_join(empleado_id, limite)

            resumenes = []
            for data in rows:
                resumen = await self._construir_resumen(data)
                resumenes.append(resumen)

            return resumenes

        except Exception as e:
            logger.error(f"Error obteniendo historial de empleado {empleado_id}: {e}")
            raise DatabaseError(f"Error de base de datos: {str(e)}")

    async def obtener_todos(
        self,
        empleado_id: Optional[int] = None,
        limite: int = 50,
        offset: int = 0
    ) -> List[HistorialLaboralResumen]:
        """
        Obtiene registros con filtros opcionales.

        Raises:
            DatabaseError: Si hay error de conexion/infraestructura.
        """
        try:
            rows = await self.repository.obtener_todos_con_join(empleado_id, limite, offset)

            resumenes = []
            for data in rows:
                resumen = await self._construir_resumen(data)
                resumenes.append(resumen)

            return resumenes

        except Exception as e:
            logger.error(f"Error obteniendo historial: {e}")
            raise DatabaseError(f"Error de base de datos: {str(e)}")

    async def contar(
        self,
        empleado_id: Optional[int] = None,
    ) -> int:
        """
        Cuenta registros con filtros.

        Raises:
            DatabaseError: Si hay error de conexion/infraestructura.
        """
        return await self.repository.contar(empleado_id)

    async def obtener_registro_activo(self, empleado_id: int) -> Optional[HistorialLaboral]:
        """
        Obtiene el registro activo (sin fecha_fin) de un empleado.

        Raises:
            DatabaseError: Si hay error de conexion/infraestructura.
        """
        return await self.repository.obtener_registro_activo(empleado_id)

    # =========================================================================
    # METODOS INTERNOS DE ESCRITURA (llamados desde empleado_service)
    # =========================================================================

    async def registrar_alta(
        self,
        empleado_id: int,
        plaza_id: Optional[int] = None,
        fecha: Optional[date] = None,
        notas: Optional[str] = None
    ) -> HistorialLaboral:
        """Registra el alta de un empleado en el sistema."""
        datos = HistorialLaboralInterno(
            empleado_id=empleado_id,
            plaza_id=plaza_id,
            tipo_movimiento=TipoMovimiento.ALTA,
            fecha_inicio=fecha or date.today(),
            notas=notas or "Alta en el sistema"
        )

        historial = await self.repository.crear(datos)

        if plaza_id:
            await self._actualizar_estatus_plaza(plaza_id, EstatusPlaza.OCUPADA)

        logger.info(f"Registrada ALTA de empleado {empleado_id}")
        return historial

    async def registrar_asignacion(
        self,
        empleado_id: int,
        plaza_id: int,
        fecha: Optional[date] = None,
        notas: Optional[str] = None
    ) -> HistorialLaboral:
        """Registra la asignacion de un empleado a una plaza."""
        fecha_movimiento = fecha or date.today()

        await self._cerrar_registro_activo(empleado_id, fecha_movimiento)

        datos = HistorialLaboralInterno(
            empleado_id=empleado_id,
            plaza_id=plaza_id,
            tipo_movimiento=TipoMovimiento.ASIGNACION,
            fecha_inicio=fecha_movimiento,
            notas=notas or f"Asignacion a plaza {plaza_id}"
        )

        historial = await self.repository.crear(datos)

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
        """Registra el cambio de plaza de un empleado."""
        fecha_movimiento = fecha or date.today()

        registro_activo = await self.repository.obtener_registro_activo(empleado_id)
        plaza_anterior_id = registro_activo.plaza_id if registro_activo else None

        await self._cerrar_registro_activo(empleado_id, fecha_movimiento)

        if plaza_anterior_id:
            await self._actualizar_estatus_plaza(plaza_anterior_id, EstatusPlaza.VACANTE)

        nota_final = notas or f"Cambio de plaza {plaza_anterior_id or 'sin plaza'} a {nueva_plaza_id}"
        datos = HistorialLaboralInterno(
            empleado_id=empleado_id,
            plaza_id=nueva_plaza_id,
            tipo_movimiento=TipoMovimiento.CAMBIO_PLAZA,
            fecha_inicio=fecha_movimiento,
            notas=nota_final
        )

        historial = await self.repository.crear(datos)

        await self._actualizar_estatus_plaza(nueva_plaza_id, EstatusPlaza.OCUPADA)

        logger.info(f"Registrado CAMBIO_PLAZA de empleado {empleado_id}: {plaza_anterior_id} -> {nueva_plaza_id}")
        return historial

    async def registrar_suspension(
        self,
        empleado_id: int,
        fecha: Optional[date] = None,
        notas: Optional[str] = None
    ) -> HistorialLaboral:
        """Registra la suspension de un empleado."""
        fecha_movimiento = fecha or date.today()

        registro_activo = await self.repository.obtener_registro_activo(empleado_id)
        plaza_id = registro_activo.plaza_id if registro_activo else None

        await self._cerrar_registro_activo(empleado_id, fecha_movimiento)

        if plaza_id:
            await self._actualizar_estatus_plaza(plaza_id, EstatusPlaza.VACANTE)

        datos = HistorialLaboralInterno(
            empleado_id=empleado_id,
            plaza_id=None,
            tipo_movimiento=TipoMovimiento.SUSPENSION,
            fecha_inicio=fecha_movimiento,
            notas=notas or "Suspension temporal"
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
        """Registra la reactivacion de un empleado."""
        fecha_movimiento = fecha or date.today()

        await self._cerrar_registro_activo(empleado_id, fecha_movimiento)

        datos = HistorialLaboralInterno(
            empleado_id=empleado_id,
            plaza_id=plaza_id,
            tipo_movimiento=TipoMovimiento.REACTIVACION,
            fecha_inicio=fecha_movimiento,
            notas=notas or "Reactivacion de empleado"
        )

        historial = await self.repository.crear(datos)

        if plaza_id:
            await self._actualizar_estatus_plaza(plaza_id, EstatusPlaza.OCUPADA)

        logger.info(f"Registrada REACTIVACION de empleado {empleado_id}")
        return historial

    async def registrar_baja(
        self,
        empleado_id: int,
        fecha: Optional[date] = None,
        notas: Optional[str] = None
    ) -> HistorialLaboral:
        """Registra la baja de un empleado del sistema."""
        fecha_movimiento = fecha or date.today()

        registro_activo = await self.repository.obtener_registro_activo(empleado_id)
        plaza_id = registro_activo.plaza_id if registro_activo else None

        await self._cerrar_registro_activo(empleado_id, fecha_movimiento)

        if plaza_id:
            await self._actualizar_estatus_plaza(plaza_id, EstatusPlaza.VACANTE)

        datos = HistorialLaboralInterno(
            empleado_id=empleado_id,
            plaza_id=None,
            tipo_movimiento=TipoMovimiento.BAJA,
            fecha_inicio=fecha_movimiento,
            notas=notas or "Baja del sistema"
        )

        historial = await self.repository.crear(datos)

        logger.info(f"Registrada BAJA de empleado {empleado_id}")
        return historial

    async def registrar_reingreso(
        self,
        empleado_id: int,
        empresa_anterior_id: Optional[int] = None,
        plaza_id: Optional[int] = None,
        fecha: Optional[date] = None,
        notas: Optional[str] = None
    ) -> HistorialLaboral:
        """Registra el reingreso de un empleado a otra empresa."""
        fecha_movimiento = fecha or date.today()

        await self._cerrar_registro_activo(empleado_id, fecha_movimiento)

        datos = HistorialLaboralInterno(
            empleado_id=empleado_id,
            plaza_id=plaza_id,
            tipo_movimiento=TipoMovimiento.REINGRESO,
            fecha_inicio=fecha_movimiento,
            notas=notas or "Reingreso a otra empresa",
            empresa_anterior_id=empresa_anterior_id,
        )

        historial = await self.repository.crear(datos)

        if plaza_id:
            await self._actualizar_estatus_plaza(plaza_id, EstatusPlaza.OCUPADA)

        logger.info(
            f"Registrado REINGRESO de empleado {empleado_id}, "
            f"empresa_anterior={empresa_anterior_id}"
        )
        return historial

    async def liberar_plaza_empleado(
        self,
        empleado_id: int,
        fecha: Optional[date] = None
    ) -> Optional[HistorialLaboral]:
        """Libera la plaza de un empleado."""
        fecha_movimiento = fecha or date.today()

        registro_activo = await self.repository.obtener_registro_activo(empleado_id)
        if not registro_activo or not registro_activo.plaza_id:
            return None

        plaza_id = registro_activo.plaza_id

        await self._cerrar_registro_activo(empleado_id, fecha_movimiento)

        await self._actualizar_estatus_plaza(plaza_id, EstatusPlaza.VACANTE)

        datos = HistorialLaboralInterno(
            empleado_id=empleado_id,
            plaza_id=None,
            tipo_movimiento=TipoMovimiento.ASIGNACION,
            fecha_inicio=fecha_movimiento,
            notas=f"Desasignacion de plaza {plaza_id}"
        )

        historial = await self.repository.crear(datos)

        logger.info(f"Liberada plaza {plaza_id} de empleado {empleado_id}")
        return historial

    # =========================================================================
    # HELPERS PRIVADOS
    # =========================================================================

    async def _cerrar_registro_activo(
        self,
        empleado_id: int,
        fecha_fin: date
    ) -> Optional[HistorialLaboral]:
        """Cierra el registro activo de un empleado (si existe)."""
        try:
            registro_activo = await self.repository.obtener_registro_activo(empleado_id)
            if not registro_activo:
                return None

            return await self.repository.cerrar_registro(registro_activo.id, fecha_fin)

        except (NotFoundError, DatabaseError):
            raise
        except Exception as e:
            logger.error(f"Error cerrando registro activo: {e}")
            raise DatabaseError(f"Error de base de datos: {str(e)}")

    async def _construir_resumen(self, data: dict) -> HistorialLaboralResumen:
        """
        Construye un HistorialLaboralResumen a partir de un row con JOIN de empleados.

        Enriquece con datos de plaza si plaza_id existe.
        """
        empleado = data.get('empleados', {})
        nombre_completo = f"{empleado.get('nombre', '')} {empleado.get('apellido_paterno', '')}".strip()
        if empleado.get('apellido_materno'):
            nombre_completo += f" {empleado.get('apellido_materno')}"

        empresa_empleado = empleado.get('empresas', {})
        empresa_nombre = empresa_empleado.get('nombre_comercial') if empresa_empleado else None

        plaza_numero = None
        categoria_nombre = None
        contrato_codigo = None

        if data.get('plaza_id'):
            plaza_data = await self.repository.obtener_datos_plaza(data['plaza_id'])
            if plaza_data:
                plaza_numero = plaza_data.get('numero_plaza')
                categoria_nombre = plaza_data.get('categoria_nombre')
                contrato_codigo = plaza_data.get('contrato_codigo')
                empresa_nombre = plaza_data.get('empresa_nombre') or empresa_nombre

        historial = HistorialLaboral(
            id=data['id'],
            empleado_id=data['empleado_id'],
            plaza_id=data.get('plaza_id'),
            tipo_movimiento=data.get('tipo_movimiento'),
            fecha_inicio=data['fecha_inicio'],
            fecha_fin=data.get('fecha_fin'),
            notas=data.get('notas'),
            fecha_creacion=data.get('fecha_creacion'),
            fecha_actualizacion=data.get('fecha_actualizacion'),
        )

        return HistorialLaboralResumen.from_historial(
            historial=historial,
            empleado_clave=empleado.get('clave', ''),
            empleado_nombre=nombre_completo,
            plaza_numero=plaza_numero,
            categoria_nombre=categoria_nombre,
            contrato_codigo=contrato_codigo,
            empresa_nombre=empresa_nombre,
        )

    async def _actualizar_estatus_plaza(
        self,
        plaza_id: int,
        nuevo_estatus: EstatusPlaza
    ) -> None:
        """Actualiza el estatus de una plaza."""
        try:
            from app.repositories.plaza_repository import SupabasePlazaRepository
            plaza_repo = SupabasePlazaRepository()
            await plaza_repo.cambiar_estatus(plaza_id, nuevo_estatus)
        except Exception as e:
            logger.error(f"Error actualizando estatus de plaza {plaza_id}: {e}")


# =============================================================================
# SINGLETON
# =============================================================================

historial_laboral_service = HistorialLaboralService()
