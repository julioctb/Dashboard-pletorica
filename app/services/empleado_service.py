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
from datetime import date

from app.entities.empleado import (
    Empleado,
    EmpleadoCreate,
    EmpleadoUpdate,
    EmpleadoResumen,
)
from app.core.enums import EstatusEmpleado, MotivoBaja
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
        # Verificar que el CURP no exista
        if await self.repository.existe_curp(empleado_create.curp):
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


# Singleton del servicio para uso global
empleado_service = EmpleadoService()
