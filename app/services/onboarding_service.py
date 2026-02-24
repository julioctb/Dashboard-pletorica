"""
Servicio orquestador para el proceso de onboarding de empleados.

Patron Orquestador (como alta_masiva_service): NO accede a BD directamente,
coordina llamadas a otros servicios.
Usa imports diferidos para evitar dependencias circulares.
"""
import logging
from typing import List, Optional
from uuid import UUID

from app.core.enums import EstatusOnboarding
from app.core.exceptions import (
    BusinessRuleError,
    DatabaseError,
    NotFoundError,
    ValidationError,
)
from app.entities.onboarding import AltaEmpleadoBuap, ExpedienteStatus
from app.entities.empleado import Empleado, EmpleadoCreate, EmpleadoUpdate
from app.entities.notificacion import NotificacionCreate

logger = logging.getLogger(__name__)


class OnboardingService:
    """
    Orquestador del flujo de onboarding.

    Coordina curp_service, empleado_service, empleado_documento_service
    y notificacion_service para el proceso de alta y seguimiento.
    """

    TRANSICIONES_VALIDAS = {
        'REGISTRADO': ['DATOS_PENDIENTES'],
        'DATOS_PENDIENTES': ['DOCUMENTOS_PENDIENTES'],
        'DOCUMENTOS_PENDIENTES': ['EN_REVISION'],
        'EN_REVISION': ['APROBADO', 'RECHAZADO'],
        'RECHAZADO': ['DOCUMENTOS_PENDIENTES'],
        'APROBADO': ['ACTIVO_COMPLETO'],
    }

    async def alta_empleado_buap(
        self, datos: AltaEmpleadoBuap, registrado_por: UUID
    ) -> Empleado:
        """
        Registra un nuevo empleado desde RRHH (BUAP/admin).

        Flujo:
        1. Valida CURP (formato + duplicados)
        2. Crea empleado via empleado_service
        3. Actualiza estatus_onboarding y sede_id
        4. Crea notificacion de alta

        Args:
            datos: Datos minimos del alta.
            registrado_por: UUID del usuario que registra.

        Returns:
            Empleado creado.

        Raises:
            BusinessRuleError: Si CURP duplicado o restringido.
            DatabaseError: Si hay error de BD.
        """
        from app.services.curp_service import curp_service
        from app.services.empleado_service import empleado_service
        from app.services.notificacion_service import notificacion_service

        # 1. Validar CURP
        validacion = await curp_service.validar_curp(datos.curp)
        if not validacion.formato_valido:
            raise ValidationError(f"CURP invalido: {validacion.mensaje}")
        if validacion.duplicado:
            if validacion.is_restricted:
                raise BusinessRuleError(
                    f"CURP {datos.curp} pertenece a un empleado restringido"
                )
            raise BusinessRuleError(
                f"CURP {datos.curp} ya esta registrado "
                f"(empleado: {validacion.empleado_nombre})"
            )

        # 2. Crear empleado
        empleado_create = EmpleadoCreate(
            empresa_id=datos.empresa_id,
            curp=datos.curp,
            nombre=datos.nombre,
            apellido_paterno=datos.apellido_paterno,
            apellido_materno=datos.apellido_materno,
            email=datos.email,
        )
        empleado = await empleado_service.crear(empleado_create)

        # 3. Actualizar onboarding y sede
        update_data = EmpleadoUpdate(
            estatus_onboarding=EstatusOnboarding.DATOS_PENDIENTES.value,
        )
        if datos.sede_id:
            update_data.sede_id = datos.sede_id

        empleado = await empleado_service.actualizar(empleado.id, update_data)

        # 4. Notificar alta
        try:
            await notificacion_service.crear(NotificacionCreate(
                empresa_id=datos.empresa_id,
                titulo="Nuevo empleado registrado",
                mensaje=f"Se registro al empleado {empleado.nombre} {empleado.apellido_paterno} ({empleado.clave})",
                tipo="onboarding_alta",
                entidad_tipo="EMPLEADO",
                entidad_id=empleado.id,
            ))
        except Exception as e:
            logger.warning(f"No se pudo crear notificacion de alta: {e}")

        return empleado

    async def obtener_expediente(self, empleado_id: int) -> ExpedienteStatus:
        """
        Calcula el estado del expediente documental de un empleado.

        Returns:
            ExpedienteStatus con conteos y porcentaje.
        """
        from app.services.empleado_documento_service import empleado_documento_service

        conteos = await empleado_documento_service.contar_por_estatus(empleado_id)

        total_requeridos = conteos['total_requeridos']
        porcentaje = 0.0
        if total_requeridos > 0:
            porcentaje = round(
                (conteos['aprobados'] / total_requeridos) * 100, 1
            )

        return ExpedienteStatus(
            documentos_requeridos=total_requeridos,
            documentos_subidos=conteos['subidos'],
            documentos_aprobados=conteos['aprobados'],
            documentos_rechazados=conteos['rechazados'],
            porcentaje_completado=porcentaje,
        )

    async def transicionar_estatus(
        self, empleado_id: int, nuevo_estatus: EstatusOnboarding
    ) -> Empleado:
        """
        Transiciona el estatus de onboarding de un empleado.

        Valida que la transicion sea valida segun TRANSICIONES_VALIDAS.

        Raises:
            NotFoundError: Si el empleado no existe.
            BusinessRuleError: Si la transicion no es valida.
        """
        from app.services.empleado_service import empleado_service

        empleado = await empleado_service.obtener_por_id(empleado_id)
        estatus_actual = empleado.estatus_onboarding or 'REGISTRADO'

        destinos_validos = self.TRANSICIONES_VALIDAS.get(estatus_actual, [])
        if nuevo_estatus.value not in destinos_validos:
            raise BusinessRuleError(
                f"No se puede transicionar de '{estatus_actual}' a '{nuevo_estatus.value}'. "
                f"Transiciones validas: {destinos_validos}"
            )

        update_data = EmpleadoUpdate(
            estatus_onboarding=nuevo_estatus.value,
        )
        return await empleado_service.actualizar(empleado_id, update_data)

    async def obtener_empleados_onboarding(
        self, empresa_id: int, estatus: Optional[str] = None
    ) -> List[dict]:
        """
        Obtiene empleados en proceso de onboarding para una empresa.

        Args:
            empresa_id: ID de la empresa.
            estatus: Filtrar por estatus de onboarding (opcional).

        Returns:
            Lista de dicts con datos resumidos de empleados.
        """
        from app.database import db_manager

        try:
            supabase = db_manager.get_client()
            query = (
                supabase.table('empleados')
                .select(
                    'id, clave, curp, nombre, apellido_paterno, '
                    'apellido_materno, email, estatus_onboarding, '
                    'fecha_creacion, sede_id'
                )
                .eq('empresa_id', empresa_id)
                .not_.is_('estatus_onboarding', 'null')
            )

            if estatus:
                query = query.eq('estatus_onboarding', estatus)

            result = query.order('fecha_creacion', desc=True).execute()

            empleados = []
            for r in (result.data or []):
                nombre_completo = f"{r.get('nombre', '')} {r.get('apellido_paterno', '')}".strip()
                if r.get('apellido_materno'):
                    nombre_completo += f" {r['apellido_materno']}"
                r['nombre_completo'] = nombre_completo
                empleados.append(r)

            return empleados

        except Exception as e:
            logger.error(f"Error obteniendo empleados onboarding empresa {empresa_id}: {e}")
            raise DatabaseError(f"Error obteniendo empleados en onboarding: {e}")


onboarding_service = OnboardingService()
