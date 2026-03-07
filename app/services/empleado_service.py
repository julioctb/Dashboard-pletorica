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
from uuid import UUID

from app.entities.empleado import (
    Empleado,
    EmpleadoCreate,
    EmpleadoUpdate,
    EmpleadoResumen,
)
from app.entities.empleado_restriccion_log import EmpleadoRestriccionLogResumen
from app.core.enums import AccionRestriccion, EstatusEmpleado, MotivoBaja
from app.repositories.empleado_repository import SupabaseEmpleadoRepository
from app.core.exceptions import (
    NotFoundError,
    DuplicateError,
    BusinessRuleError,
)
from app.services.empleados.mutations import EmpleadoMutationService
from app.services.empleados.queries import EmpleadoQueryService
from app.services.empleados.restrictions import EmpleadoRestrictionService

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
        self._query_service = EmpleadoQueryService(self)
        self._mutation_service = EmpleadoMutationService(self)
        self._restriction_service = EmpleadoRestrictionService(self)

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
        return await self._query_service.obtener_por_id(empleado_id)

    async def obtener_por_curp(self, curp: str) -> Optional[Empleado]:
        """
        Obtiene un empleado por su CURP.

        Returns:
            Empleado si existe, None si no existe

        Raises:
            DatabaseError: Si hay error de BD
        """
        return await self._query_service.obtener_por_curp(curp)

    async def obtener_por_user_id(self, user_id: UUID) -> Optional[Empleado]:
        """
        Busca empleado por user_id (para autoservicio). None si no existe.
        """
        return await self._query_service.obtener_por_user_id(user_id)

    async def obtener_por_clave(self, clave: str) -> Optional[Empleado]:
        """
        Obtiene un empleado por su clave (B25-00001).

        Returns:
            Empleado si existe, None si no existe

        Raises:
            DatabaseError: Si hay error de BD
        """
        return await self._query_service.obtener_por_clave(clave)

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
        return await self._mutation_service.crear(empleado_create)

    async def actualizar(self, empleado_id: int, empleado_update: EmpleadoUpdate) -> Empleado:
        """
        Actualiza un empleado existente.
        CURP y clave NO se pueden modificar.

        Raises:
            NotFoundError: Si el empleado no existe
            BusinessRuleError: Si la nueva empresa no es válida
            DatabaseError: Si hay error de BD
        """
        return await self._mutation_service.actualizar(empleado_id, empleado_update)

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
        return await self._mutation_service.dar_de_baja(empleado_id, motivo, fecha_baja)

    async def reactivar(self, empleado_id: int) -> Empleado:
        """
        Reactiva un empleado dado de baja.

        Raises:
            NotFoundError: Si el empleado no existe
            BusinessRuleError: Si el empleado ya está activo
            DatabaseError: Si hay error de BD
        """
        return await self._mutation_service.reactivar(empleado_id)

    async def suspender(self, empleado_id: int) -> Empleado:
        """
        Suspende temporalmente a un empleado.

        Raises:
            NotFoundError: Si el empleado no existe
            BusinessRuleError: Si el empleado ya está suspendido
            DatabaseError: Si hay error de BD
        """
        return await self._mutation_service.suspender(empleado_id)

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
        return await self._mutation_service.reingresar(
            empleado_id,
            nueva_empresa_id,
            datos_actualizados,
        )

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
        return await self._query_service.obtener_todos(incluir_inactivos, limite, offset)

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
        return await self._query_service.obtener_por_empresa(
            empresa_id,
            incluir_inactivos,
            limite,
            offset,
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
        return await self._query_service.obtener_resumen_empleados(
            incluir_inactivos,
            limite,
            offset,
        )

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
        return await self._query_service.obtener_resumen_por_empresa(
            empresa_id,
            incluir_inactivos,
            limite,
            offset,
        )

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
        return await self._query_service.buscar(texto, empresa_id, limite)

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
        return await self._query_service.contar(empresa_id, estatus)

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
        return await self._query_service.obtener_disponibles_para_asignacion(limite)

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
        return await self._query_service.generar_clave(anio)

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
        return await self._query_service.validar_curp_disponible(curp, excluir_id)

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
        return await self._restriction_service.restringir_empleado(
            empleado_id,
            motivo,
            admin_user_id,
            notas,
        )

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
        return await self._restriction_service.liberar_empleado(
            empleado_id,
            motivo,
            admin_user_id,
            notas,
        )

    async def obtener_historial_restricciones(
        self,
        empleado_id: int,
        admin_user_id: Optional[UUID] = None,
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
        return await self._restriction_service.obtener_historial_restricciones(
            empleado_id,
            admin_user_id,
        )

    # =========================================================================
    # HELPERS PRIVADOS (RESTRICCIONES)
    # =========================================================================

    async def _es_admin(self, user_id: Optional[UUID]) -> bool:
        """Verifica si un usuario tiene rol de admin."""
        return await self._restriction_service.es_admin(user_id)

    async def _registrar_log_restriccion(
        self,
        empleado_id: int,
        accion: AccionRestriccion,
        motivo: str,
        ejecutado_por: UUID,
        notas: Optional[str] = None
    ) -> None:
        """Registra un evento en el log de restricciones."""
        await self._restriction_service.registrar_log_restriccion(
            empleado_id,
            accion,
            motivo,
            ejecutado_por,
            notas,
        )


# Singleton del servicio para uso global
empleado_service = EmpleadoService()
