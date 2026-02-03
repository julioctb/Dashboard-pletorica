"""
Servicio de aplicación para gestión de empleados.

Patrón de manejo de errores:
- Las excepciones del repository se propagan (NotFoundError, DuplicateError, DatabaseError)
- El servicio NO captura excepciones, las deja subir al State
- Logging solo para debugging, NO para control de flujo

IMPORTANTE: Este servicio registra automáticamente los movimientos en historial_laboral:
- crear() -> registrar_alta()
- dar_de_baja() -> registrar_baja()
- reactivar() -> registrar_reactivacion()
- suspender() -> registrar_suspension()
"""
import logging
from typing import List, Optional
from datetime import date, datetime, timezone
from uuid import UUID

from app.entities.empleado import (
    Empleado,
    EmpleadoCreate,
    EmpleadoUpdate,
    EmpleadoResumen,
)
from app.entities.empleado_restriccion_log import EmpleadoRestriccionLogResumen
from app.core.enums import EstatusEmpleado, MotivoBaja, AccionRestriccion
from app.core.validation.constants import MOTIVO_RESTRICCION_MIN
from app.repositories.empleado_repository import SupabaseEmpleadoRepository
from app.core.exceptions import (
    NotFoundError,
    DuplicateError,
    BusinessRuleError,
)

logger = logging.getLogger(__name__)


def _get_historial_service():
    """Import diferido para evitar imports circulares"""
    from app.services.historial_laboral_service import historial_laboral_service
    return historial_laboral_service


class EmpleadoService:
    """
    Servicio de aplicación para empleados.
    Orquesta las operaciones de negocio.

    El CURP es el identificador único real (gobierno mexicano).
    La clave (B25-00001) es para uso operativo interno y nunca cambia.
    """

    def __init__(self, repository=None):
        """
        Inicializa el servicio con un repository.

        Args:
            repository: Implementación del repository. Si es None, usa Supabase.
        """
        if repository is None:
            repository = SupabaseEmpleadoRepository()
        self.repository = repository

    # =========================================================================
    # OPERACIONES CRUD
    # =========================================================================

    async def obtener_por_id(self, empleado_id: int) -> Empleado:
        """
        Obtiene un empleado por su ID.

        Raises:
            NotFoundError: Si el empleado no existe
            DatabaseError: Si hay error de BD
        """
        return await self.repository.obtener_por_id(empleado_id)

    async def obtener_por_curp(self, curp: str) -> Optional[Empleado]:
        """
        Obtiene un empleado por su CURP.

        Returns:
            Empleado si existe, None si no existe

        Raises:
            DatabaseError: Si hay error de BD
        """
        return await self.repository.obtener_por_curp(curp.upper())

    async def obtener_por_clave(self, clave: str) -> Optional[Empleado]:
        """
        Obtiene un empleado por su clave (B25-00001).

        Returns:
            Empleado si existe, None si no existe

        Raises:
            DatabaseError: Si hay error de BD
        """
        return await self.repository.obtener_por_clave(clave.upper())

    async def crear(self, empleado_create: EmpleadoCreate) -> Empleado:
        """
        Crea un nuevo empleado con clave autogenerada.

        Args:
            empleado_create: Datos del empleado a crear

        Returns:
            Empleado creado con ID y clave asignados

        Raises:
            DuplicateError: Si el CURP ya existe
            BusinessRuleError: Si la empresa no es válida
            DatabaseError: Si hay error de BD
        """
        # Verificar CURP: restriccion o duplicado
        empleado_existente = await self.repository.obtener_por_curp(empleado_create.curp)
        if empleado_existente:
            if empleado_existente.is_restricted:
                raise BusinessRuleError(
                    f"El empleado con CURP {empleado_create.curp} tiene restricciones "
                    f"en el sistema. Contacte al administrador de BUAP para mas informacion."
                )
            raise DuplicateError(
                f"Empleado con CURP {empleado_create.curp} ya existe",
                field="curp",
                value=empleado_create.curp
            )

        # Verificar que la empresa existe y es válida (solo si se proporciona)
        if empleado_create.empresa_id is not None:
            await self._validar_empresa(empleado_create.empresa_id)

        # Generar clave automática
        anio = date.today().year
        clave = await self.generar_clave(anio)

        # Crear entidad Empleado
        empleado = Empleado(
            clave=clave,
            empresa_id=empleado_create.empresa_id,
            curp=empleado_create.curp,
            rfc=empleado_create.rfc,
            nss=empleado_create.nss,
            nombre=empleado_create.nombre,
            apellido_paterno=empleado_create.apellido_paterno,
            apellido_materno=empleado_create.apellido_materno,
            fecha_nacimiento=empleado_create.fecha_nacimiento,
            genero=empleado_create.genero,
            telefono=empleado_create.telefono,
            email=empleado_create.email,
            direccion=empleado_create.direccion,
            contacto_emergencia=empleado_create.contacto_emergencia,
            fecha_ingreso=empleado_create.fecha_ingreso or date.today(),
            notas=empleado_create.notas,
            estatus=EstatusEmpleado.ACTIVO,
        )

        empleado_creado = await self.repository.crear(empleado)

        # Registrar alta en historial laboral (sin plaza = INACTIVO en historial)
        try:
            historial_service = _get_historial_service()
            await historial_service.registrar_alta(
                empleado_id=empleado_creado.id,
                plaza_id=None,  # Nuevo empleado no tiene plaza asignada
                fecha=empleado_creado.fecha_ingreso,
                notas=f"Alta de empleado: {empleado_creado.nombre_completo}"
            )
        except Exception as e:
            logger.warning(f"Error registrando alta en historial: {e}")
            # No interrumpimos el flujo si falla el historial

        return empleado_creado

    async def actualizar(self, empleado_id: int, empleado_update: EmpleadoUpdate) -> Empleado:
        """
        Actualiza un empleado existente.
        CURP y clave NO se pueden modificar.

        Raises:
            NotFoundError: Si el empleado no existe
            BusinessRuleError: Si la nueva empresa no es válida
            DatabaseError: Si hay error de BD
        """
        # Obtener empleado existente
        empleado = await self.repository.obtener_por_id(empleado_id)

        # Si cambia empresa_id, validar la nueva empresa
        if empleado_update.empresa_id and empleado_update.empresa_id != empleado.empresa_id:
            await self._validar_empresa(empleado_update.empresa_id)

        # Actualizar solo campos proporcionados
        update_data = empleado_update.model_dump(exclude_unset=True)
        for campo, valor in update_data.items():
            if valor is not None:
                setattr(empleado, campo, valor)

        return await self.repository.actualizar(empleado)

    # =========================================================================
    # OPERACIONES DE ESTADO
    # =========================================================================

    async def dar_de_baja(
        self,
        empleado_id: int,
        motivo: MotivoBaja,
        fecha_baja: Optional[date] = None
    ) -> Empleado:
        """
        Da de baja a un empleado.

        Args:
            empleado_id: ID del empleado
            motivo: Motivo de la baja
            fecha_baja: Fecha de baja (default: hoy)

        Returns:
            Empleado actualizado

        Raises:
            NotFoundError: Si el empleado no existe
            BusinessRuleError: Si el empleado ya está dado de baja
            DatabaseError: Si hay error de BD
        """
        empleado = await self.repository.obtener_por_id(empleado_id)

        if empleado.estatus == EstatusEmpleado.INACTIVO:
            raise BusinessRuleError("El empleado ya está dado de baja")

        empleado.dar_de_baja(motivo, fecha_baja)
        empleado_actualizado = await self.repository.actualizar(empleado)

        # Registrar baja en historial laboral
        try:
            historial_service = _get_historial_service()
            await historial_service.registrar_baja(
                empleado_id=empleado_id,
                fecha=fecha_baja,
                notas=f"Baja por: {motivo.descripcion}"
            )
        except Exception as e:
            logger.warning(f"Error registrando baja en historial: {e}")

        return empleado_actualizado

    async def reactivar(self, empleado_id: int) -> Empleado:
        """
        Reactiva un empleado dado de baja.

        Raises:
            NotFoundError: Si el empleado no existe
            BusinessRuleError: Si el empleado ya está activo
            DatabaseError: Si hay error de BD
        """
        empleado = await self.repository.obtener_por_id(empleado_id)

        if empleado.estatus == EstatusEmpleado.ACTIVO:
            raise BusinessRuleError("El empleado ya está activo")

        empleado.activar()
        empleado_actualizado = await self.repository.actualizar(empleado)

        # Registrar reactivación en historial laboral
        try:
            historial_service = _get_historial_service()
            await historial_service.registrar_reactivacion(
                empleado_id=empleado_id,
                plaza_id=None,  # Sin plaza asignada al reactivar
                notas="Reactivación de empleado"
            )
        except Exception as e:
            logger.warning(f"Error registrando reactivación en historial: {e}")

        return empleado_actualizado

    async def suspender(self, empleado_id: int) -> Empleado:
        """
        Suspende temporalmente a un empleado.

        Raises:
            NotFoundError: Si el empleado no existe
            BusinessRuleError: Si el empleado ya está suspendido
            DatabaseError: Si hay error de BD
        """
        empleado = await self.repository.obtener_por_id(empleado_id)

        if empleado.estatus == EstatusEmpleado.SUSPENDIDO:
            raise BusinessRuleError("El empleado ya está suspendido")

        empleado.suspender()
        empleado_actualizado = await self.repository.actualizar(empleado)

        # Registrar suspensión en historial laboral
        try:
            historial_service = _get_historial_service()
            await historial_service.registrar_suspension(
                empleado_id=empleado_id,
                notas="Suspensión temporal"
            )
        except Exception as e:
            logger.warning(f"Error registrando suspensión en historial: {e}")

        return empleado_actualizado

    async def reingresar(
        self,
        empleado_id: int,
        nueva_empresa_id: int,
        datos_actualizados: Optional[EmpleadoUpdate] = None
    ) -> Empleado:
        """
        Reingresa un empleado existente a una nueva empresa.

        El empleado ya existe en el sistema (por CURP). Se cambia su empresa_id,
        se reactiva si estaba inactivo, y se registra REINGRESO en historial.

        Args:
            empleado_id: ID del empleado existente
            nueva_empresa_id: ID de la empresa destino
            datos_actualizados: Datos opcionales a actualizar (rfc, nss, telefono, etc.)

        Returns:
            Empleado actualizado con nueva empresa

        Raises:
            NotFoundError: Si el empleado no existe
            BusinessRuleError: Si el empleado esta restringido, o ya esta activo
                en la misma empresa, o la empresa no es valida
            DatabaseError: Si hay error de BD
        """
        empleado = await self.repository.obtener_por_id(empleado_id)

        # Verificar restriccion
        if empleado.is_restricted:
            raise BusinessRuleError(
                f"El empleado con CURP {empleado.curp} tiene restricciones "
                f"en el sistema. Contacte al administrador de BUAP para mas informacion."
            )

        # Verificar que no este activo en la misma empresa
        if (
            empleado.estatus == EstatusEmpleado.ACTIVO
            and empleado.empresa_id == nueva_empresa_id
        ):
            raise BusinessRuleError(
                f"El empleado {empleado.clave} ya esta activo en esta empresa"
            )

        # Validar la nueva empresa
        await self._validar_empresa(nueva_empresa_id)

        # Guardar empresa anterior para historial
        empresa_anterior_id = empleado.empresa_id

        # Cambiar empresa
        empleado.empresa_id = nueva_empresa_id

        # Aplicar datos actualizados si se proporcionan
        if datos_actualizados:
            update_data = datos_actualizados.model_dump(exclude_unset=True)
            for campo, valor in update_data.items():
                if valor is not None:
                    setattr(empleado, campo, valor)

        # Activar si estaba inactivo o suspendido
        if empleado.estatus != EstatusEmpleado.ACTIVO:
            empleado.estatus = EstatusEmpleado.ACTIVO
            empleado.fecha_baja = None
            empleado.motivo_baja = None

        empleado_actualizado = await self.repository.actualizar(empleado)

        # Registrar reingreso en historial laboral
        try:
            historial_service = _get_historial_service()
            await historial_service.registrar_reingreso(
                empleado_id=empleado_id,
                empresa_anterior_id=empresa_anterior_id,
                plaza_id=None,
                notas=f"Reingreso a empresa {nueva_empresa_id} desde empresa {empresa_anterior_id}"
            )
        except Exception as e:
            logger.warning(f"Error registrando reingreso en historial: {e}")

        return empleado_actualizado

    # =========================================================================
    # CONSULTAS
    # =========================================================================

    async def obtener_todos(
        self,
        incluir_inactivos: bool = False,
        limite: Optional[int] = 50,
        offset: int = 0
    ) -> List[Empleado]:
        """
        Obtiene todos los empleados con paginación.

        Raises:
            DatabaseError: Si hay error de BD
        """
        return await self.repository.obtener_todos(incluir_inactivos, limite, offset)

    async def obtener_por_empresa(
        self,
        empresa_id: int,
        incluir_inactivos: bool = False,
        limite: Optional[int] = 50,
        offset: int = 0
    ) -> List[Empleado]:
        """
        Obtiene empleados de una empresa específica.

        Raises:
            DatabaseError: Si hay error de BD
        """
        return await self.repository.obtener_por_empresa(
            empresa_id, incluir_inactivos, limite, offset
        )

    async def obtener_resumen_empleados(
        self,
        incluir_inactivos: bool = False,
        limite: int = 100,
        offset: int = 0
    ) -> List[EmpleadoResumen]:
        """
        Obtiene resumen de todos los empleados para UI (selects, listados).

        Raises:
            DatabaseError: Si hay error de BD
        """
        empleados = await self.repository.obtener_todos(
            incluir_inactivos, limite, offset
        )

        return [
            EmpleadoResumen.from_empleado(emp, None)
            for emp in empleados
        ]

    async def obtener_resumen_por_empresa(
        self,
        empresa_id: int,
        incluir_inactivos: bool = False,
        limite: int = 50,
        offset: int = 0
    ) -> List[EmpleadoResumen]:
        """
        Obtiene resumen de empleados de una empresa para UI.

        Raises:
            DatabaseError: Si hay error de BD
        """
        empleados = await self.repository.obtener_por_empresa(
            empresa_id, incluir_inactivos, limite, offset
        )

        # Obtener nombre de empresa (evitar import circular)
        from app.services import empresa_service
        try:
            empresa = await empresa_service.obtener_por_id(empresa_id)
            empresa_nombre = empresa.nombre_comercial
        except NotFoundError:
            empresa_nombre = None

        return [
            EmpleadoResumen.from_empleado(emp, empresa_nombre)
            for emp in empleados
        ]

    async def buscar(
        self,
        texto: str,
        empresa_id: Optional[int] = None,
        limite: int = 20
    ) -> List[Empleado]:
        """
        Busca empleados por nombre, CURP o clave.

        Args:
            texto: Término de búsqueda (mínimo 2 caracteres)
            empresa_id: Filtrar por empresa (opcional)
            limite: Máximo de resultados

        Raises:
            DatabaseError: Si hay error de BD
        """
        if not texto or len(texto) < 2:
            return []

        return await self.repository.buscar(texto, empresa_id, limite)

    async def contar(
        self,
        empresa_id: Optional[int] = None,
        estatus: Optional[str] = None
    ) -> int:
        """
        Cuenta empleados con filtros opcionales.

        Raises:
            DatabaseError: Si hay error de BD
        """
        return await self.repository.contar(empresa_id, estatus)

    async def obtener_disponibles_para_asignacion(
        self,
        limite: int = 100
    ) -> List[EmpleadoResumen]:
        """
        Obtiene empleados disponibles para asignar a una plaza.

        Un empleado está disponible si:
        - Está activo (estatus = ACTIVO)
        - No tiene una asignación activa en historial_laboral

        Returns:
            Lista de EmpleadoResumen de empleados disponibles

        Raises:
            DatabaseError: Si hay error de BD
        """
        return await self.repository.obtener_disponibles_para_asignacion(limite)

    # =========================================================================
    # GENERACIÓN DE CLAVE
    # =========================================================================

    async def generar_clave(self, anio: Optional[int] = None) -> str:
        """
        Genera una nueva clave de empleado: B25-00001

        Args:
            anio: Año para la clave (default: año actual)

        Returns:
            Clave única generada

        Raises:
            DatabaseError: Si hay error de BD
        """
        if anio is None:
            anio = date.today().year

        consecutivo = await self.repository.obtener_siguiente_consecutivo(anio)
        return Empleado.generar_clave(anio, consecutivo)

    # =========================================================================
    # VALIDACIONES
    # =========================================================================

    async def validar_curp_disponible(
        self,
        curp: str,
        excluir_id: Optional[int] = None
    ) -> bool:
        """
        Verifica si un CURP está disponible.

        Args:
            curp: CURP a verificar
            excluir_id: ID de empleado a excluir (para actualizaciones)

        Returns:
            True si el CURP está disponible, False si ya existe
        """
        return not await self.repository.existe_curp(curp, excluir_id)

    async def _validar_empresa(self, empresa_id: int) -> None:
        """
        Valida que una empresa exista y sea válida para empleados.

        Raises:
            BusinessRuleError: Si la empresa no existe o no es válida
        """
        # Importar dentro del método para evitar imports circulares
        from app.services import empresa_service

        try:
            empresa = await empresa_service.obtener_por_id(empresa_id)
        except NotFoundError:
            raise BusinessRuleError(f"Empresa con ID {empresa_id} no existe")

        if not empresa.esta_activa():
            raise BusinessRuleError("La empresa no está activa")

        # Solo empresas de tipo NOMINA pueden tener empleados
        if not empresa.puede_tener_empleados():
            raise BusinessRuleError(
                "Solo empresas de tipo NOMINA pueden tener empleados"
            )

    # =========================================================================
    # RESTRICCIONES DE EMPLEADOS
    # =========================================================================

    async def restringir_empleado(
        self,
        empleado_id: int,
        motivo: str,
        admin_user_id: UUID,
        notas: Optional[str] = None
    ) -> Empleado:
        """
        Restringe un empleado. Solo administradores BUAP pueden ejecutar esto.

        Args:
            empleado_id: ID del empleado a restringir
            motivo: Razon de la restriccion (obligatorio, min 10 caracteres)
            admin_user_id: UUID del admin que restringe
            notas: Observaciones adicionales (opcional)

        Returns:
            Empleado actualizado con restriccion aplicada

        Raises:
            NotFoundError: Si el empleado no existe
            BusinessRuleError: Si ya esta restringido o si no es admin
        """
        if not await self._es_admin(admin_user_id):
            raise BusinessRuleError("Solo administradores BUAP pueden restringir empleados")

        empleado = await self.obtener_por_id(empleado_id)

        if empleado.is_restricted:
            raise BusinessRuleError(
                f"El empleado {empleado.clave} ya tiene una restriccion activa"
            )

        if not motivo or len(motivo.strip()) < MOTIVO_RESTRICCION_MIN:
            raise BusinessRuleError(f"El motivo debe tener al menos {MOTIVO_RESTRICCION_MIN} caracteres")

        # Aplicar restriccion
        ahora = datetime.now(timezone.utc)
        empleado.is_restricted = True
        empleado.restriction_reason = motivo.strip()
        empleado.restricted_at = ahora
        empleado.restricted_by = admin_user_id

        empleado_actualizado = await self.repository.actualizar(empleado)

        # Registrar en log
        await self._registrar_log_restriccion(
            empleado_id=empleado_id,
            accion=AccionRestriccion.RESTRICCION,
            motivo=motivo.strip(),
            ejecutado_por=admin_user_id,
            notas=notas
        )

        logger.info(
            f"Empleado {empleado.clave} restringido por admin {admin_user_id}. "
            f"Motivo: {motivo[:50]}..."
        )

        return empleado_actualizado

    async def liberar_empleado(
        self,
        empleado_id: int,
        motivo: str,
        admin_user_id: UUID,
        notas: Optional[str] = None
    ) -> Empleado:
        """
        Libera la restriccion de un empleado. Solo administradores BUAP.

        Args:
            empleado_id: ID del empleado a liberar
            motivo: Razon de la liberacion (obligatorio, min 10 caracteres)
            admin_user_id: UUID del admin que libera
            notas: Observaciones adicionales (opcional)

        Returns:
            Empleado actualizado sin restriccion

        Raises:
            NotFoundError: Si el empleado no existe
            BusinessRuleError: Si no esta restringido o si no es admin
        """
        if not await self._es_admin(admin_user_id):
            raise BusinessRuleError("Solo administradores BUAP pueden liberar empleados")

        empleado = await self.obtener_por_id(empleado_id)

        if not empleado.is_restricted:
            raise BusinessRuleError(
                f"El empleado {empleado.clave} no tiene restriccion activa"
            )

        if not motivo or len(motivo.strip()) < 10:
            raise BusinessRuleError("El motivo de liberacion debe tener al menos 10 caracteres")

        # Limpiar restriccion
        empleado.is_restricted = False
        empleado.restriction_reason = None
        empleado.restricted_at = None
        empleado.restricted_by = None

        empleado_actualizado = await self.repository.actualizar(empleado)

        # Registrar en log
        await self._registrar_log_restriccion(
            empleado_id=empleado_id,
            accion=AccionRestriccion.LIBERACION,
            motivo=motivo.strip(),
            ejecutado_por=admin_user_id,
            notas=notas
        )

        logger.info(
            f"Empleado {empleado.clave} liberado por admin {admin_user_id}. "
            f"Motivo: {motivo[:50]}..."
        )

        return empleado_actualizado

    async def obtener_historial_restricciones(
        self,
        empleado_id: int,
        admin_user_id: UUID
    ) -> List[EmpleadoRestriccionLogResumen]:
        """
        Obtiene el historial de restricciones de un empleado.
        Solo administradores pueden ver esta informacion.

        Args:
            empleado_id: ID del empleado
            admin_user_id: UUID del admin solicitante

        Returns:
            Lista de registros ordenados por fecha descendente

        Raises:
            BusinessRuleError: Si no es admin
            NotFoundError: Si el empleado no existe
        """
        if not await self._es_admin(admin_user_id):
            raise BusinessRuleError("Solo administradores pueden ver el historial de restricciones")

        # Verificar que el empleado existe
        await self.obtener_por_id(empleado_id)

        from app.database import db_manager
        supabase = db_manager.get_client()

        result = supabase.table('empleado_restricciones_log')\
            .select('*, user_profiles(nombre_completo)')\
            .eq('empleado_id', empleado_id)\
            .order('fecha', desc=True)\
            .execute()

        return [
            EmpleadoRestriccionLogResumen(
                id=r['id'],
                empleado_id=r['empleado_id'],
                accion=r['accion'],
                motivo=r['motivo'],
                fecha=r['fecha'],
                ejecutado_por_nombre=r.get('user_profiles', {}).get('nombre_completo', 'Desconocido'),
                notas=r.get('notas')
            )
            for r in result.data
        ]

    # =========================================================================
    # HELPERS PRIVADOS (RESTRICCIONES)
    # =========================================================================

    async def _es_admin(self, user_id: UUID) -> bool:
        """Verifica si un usuario tiene rol de admin."""
        try:
            from app.database import db_manager
            supabase = db_manager.get_client()

            result = supabase.table('user_profiles')\
                .select('rol, activo')\
                .eq('id', str(user_id))\
                .single()\
                .execute()

            if result.data:
                return result.data['rol'] == 'admin' and result.data['activo']
            return False
        except Exception:
            return False

    async def _registrar_log_restriccion(
        self,
        empleado_id: int,
        accion: AccionRestriccion,
        motivo: str,
        ejecutado_por: UUID,
        notas: Optional[str] = None
    ) -> None:
        """Registra un evento en el log de restricciones."""
        from app.database import db_manager
        supabase = db_manager.get_client()

        datos = {
            'empleado_id': empleado_id,
            'accion': accion.value if isinstance(accion, AccionRestriccion) else accion,
            'motivo': motivo,
            'ejecutado_por': str(ejecutado_por),
            'notas': notas
        }

        supabase.table('empleado_restricciones_log').insert(datos).execute()


# Singleton del servicio para uso global
empleado_service = EmpleadoService()
