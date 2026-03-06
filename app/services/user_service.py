"""Fachada principal para usuarios, autenticacion y permisos."""
import logging
from typing import List, Optional, Tuple
from uuid import UUID

from supabase import Client

from app.core.exceptions import BusinessRuleError, DatabaseError, NotFoundError
from app.database import db_manager
from app.entities.user_company import UserCompany, UserCompanyAsignacionInicial, UserCompanyResumen
from app.entities.user_profile import UserProfile, UserProfileCreate, UserProfileResumen, UserProfileUpdate
from app.services.users.auth import UserAuthService
from app.services.users.companies import UserCompanyService
from app.services.users.profiles import UserProfileService

logger = logging.getLogger(__name__)


class UserService:
    """Fachada estable que delega por subdominio en servicios internos."""

    def __init__(self):
        self.supabase: Client = db_manager.get_anon_client()
        self.tabla_profiles = "user_profiles"
        self.tabla_companies = "user_companies"
        self.supabase_admin: Optional[Client] = db_manager.get_client()
        self._auth_service = UserAuthService(self)
        self._profile_service = UserProfileService(self)
        self._company_service = UserCompanyService(self)

    def _listar_auth_users_admin(self) -> list:
        """Obtiene usuarios de auth.users con una forma estable entre SDKs."""
        if not self.supabase_admin:
            return []

        response = self.supabase_admin.auth.admin.list_users()
        users = getattr(response, "users", None)
        if users is not None:
            return list(users)
        if isinstance(response, list):
            return response
        data = getattr(response, "data", None)
        if isinstance(data, list):
            return data
        return []

    def _emails_map_auth_users(self) -> dict[str, str]:
        """Mapa user_id -> email desde auth.users."""
        emails_map: dict[str, str] = {}
        for user in self._listar_auth_users_admin():
            user_id = getattr(user, "id", None)
            email = getattr(user, "email", None)
            if user_id and email:
                emails_map[str(user_id)] = str(email).strip().lower()
        return emails_map

    def _buscar_auth_user_por_email(self, email: str):
        """Busca un usuario de auth.users por email normalizado."""
        email_normalizado = email.strip().lower()
        for user in self._listar_auth_users_admin():
            user_email = getattr(user, "email", None)
            if user_email and str(user_email).strip().lower() == email_normalizado:
                return user
        return None

    def _query_profile(self, select: str = "*"):
        """Query base para user_profiles."""
        return self.supabase_admin.table(self.tabla_profiles).select(select)

    def _obtener_profile_data(
        self,
        user_id: UUID,
        *,
        select: str = "*",
    ) -> Optional[dict]:
        """Obtiene la fila cruda de user_profiles para un usuario."""
        result = self._query_profile(select).eq('id', str(user_id)).execute()
        return result.data[0] if result.data else None

    def _actualizar_profile_data(self, user_id: UUID, payload: dict):
        """Actualiza user_profiles para un usuario."""
        return self.supabase_admin.table(self.tabla_profiles)\
            .update(payload)\
            .eq('id', str(user_id))\
            .execute()

    def _obtener_profiles_map(
        self,
        user_ids: list[str],
        *,
        select: str,
    ) -> dict[str, dict]:
        """Obtiene perfiles en batch indexados por id."""
        if not user_ids:
            return {}
        result = self._query_profile(select).in_('id', user_ids).execute()
        return {
            str(perfil.get('id')): perfil
            for perfil in (result.data or [])
            if perfil.get('id')
        }

    @staticmethod
    def _construir_resumen_empresa_usuario(data: dict) -> UserCompanyResumen:
        """Convierte una fila con JOIN a empresas en resumen tipado."""
        empresa_data = data.get('empresas', {})
        return UserCompanyResumen(
            id=data['id'],
            user_id=UUID(data['user_id']),
            empresa_id=data['empresa_id'],
            es_principal=data['es_principal'],
            rol_empresa=data.get('rol_empresa', 'lectura'),
            fecha_creacion=data.get('fecha_creacion'),
            empresa_nombre=empresa_data.get('nombre_comercial'),
            empresa_rfc=empresa_data.get('rfc'),
            empresa_tipo=empresa_data.get('tipo_empresa'),
            empresa_activa=empresa_data.get('estatus') == 'ACTIVO',
        )

    async def _obtener_resumen_empresas_por_usuarios(
        self,
        user_ids: list[str],
    ) -> dict[str, dict]:
        """Resume cantidad de empresas y principal por usuario."""
        if not user_ids:
            return {}

        result = self.supabase_admin.table(self.tabla_companies)\
            .select('user_id, es_principal, empresas(nombre_comercial)')\
            .in_('user_id', user_ids)\
            .execute()

        resumen_map: dict[str, dict] = {}
        for row in result.data or []:
            user_id = str(row.get('user_id', ''))
            if not user_id:
                continue
            resumen = resumen_map.setdefault(
                user_id,
                {"cantidad_empresas": 0, "empresa_principal": None},
            )
            resumen["cantidad_empresas"] += 1
            empresa_data = row.get('empresas') or {}
            if row.get('es_principal') and empresa_data.get('nombre_comercial'):
                resumen["empresa_principal"] = empresa_data.get('nombre_comercial')

        return resumen_map

    async def crear_usuario(
        self,
        datos: UserProfileCreate,
        empresas_ids: Optional[List[int]] = None,
        empresa_principal_id: Optional[int] = None,
        asignaciones_empresas: Optional[List[UserCompanyAsignacionInicial]] = None,
    ) -> UserProfile:
        return await self._auth_service.crear_usuario(
            datos=datos,
            empresas_ids=empresas_ids,
            empresa_principal_id=empresa_principal_id,
            asignaciones_empresas=asignaciones_empresas,
        )

    async def login(self, email: str, password: str) -> Tuple[UserProfile, dict]:
        """
        Autentica un usuario con email y contraseña.

        Args:
            email: Email del usuario
            password: Contraseña

        Returns:
            Tupla con (UserProfile, datos de sesión incluyendo tokens)

        Raises:
            ValidationError: Si las credenciales son inválidas
            BusinessRuleError: Si el usuario está inactivo
            DatabaseError: Si hay error de conexión
        """
        return await self._auth_service.login(email, password)

    async def logout(self) -> bool:
        """
        Cierra la sesión actual.

        Returns:
            True si se cerró correctamente

        Note:
            Esta operación es del lado del servidor. El frontend
            también debe limpiar los tokens almacenados.
        """
        return await self._auth_service.logout()

    async def validar_token(self, access_token: str) -> Optional[UserProfile]:
        """
        Valida un token JWT y retorna el perfil del usuario.

        Args:
            access_token: Token JWT a validar

        Returns:
            UserProfile si el token es válido, None si no lo es

        Note:
            Útil para validar tokens en cada request del middleware.
        """
        return await self._auth_service.validar_token(access_token)

    async def obtener_email_desde_token(self, access_token: str) -> Optional[str]:
        """
        Obtiene el email del usuario autenticado a partir del access token.

        Args:
            access_token: JWT de acceso vigente

        Returns:
            Email normalizado si se pudo resolver, None en caso contrario
        """
        return await self._auth_service.obtener_email_desde_token(access_token)

    async def refrescar_token(self, refresh_token: str) -> Optional[dict]:
        """
        Refresca un token de acceso usando el refresh token.

        Args:
            refresh_token: Token de refresco

        Returns:
            Nuevos datos de sesión o None si falló

        Note:
            Los tokens de Supabase expiran cada hora por defecto.
        """
        return await self._auth_service.refrescar_token(refresh_token)

    async def cambiar_password_usuario_autenticado(
        self,
        access_token: str,
        refresh_token: str,
        nueva_password: str,
    ) -> None:
        """
        Cambia la contraseña del usuario autenticado usando su sesión actual.

        Args:
            access_token: Access token del usuario autenticado
            refresh_token: Refresh token del usuario autenticado
            nueva_password: Nueva contraseña (mínimo 8 caracteres)

        Raises:
            ValidationError: Si la contraseña no cumple reglas mínimas
            DatabaseError: Si Supabase rechaza la operación
        """
        await self._auth_service.cambiar_password_usuario_autenticado(
            access_token=access_token,
            refresh_token=refresh_token,
            nueva_password=nueva_password,
        )

    async def obtener_por_id(self, user_id: UUID) -> UserProfile:
        """
        Obtiene un perfil de usuario por su UUID.

        Args:
            user_id: UUID del usuario

        Returns:
            UserProfile encontrado

        Raises:
            NotFoundError: Si el usuario no existe
            DatabaseError: Si hay error de BD
        """
        return await self._profile_service.obtener_por_id(user_id)

    async def obtener_por_email(self, email: str) -> Optional[UserProfile]:
        """
        Busca un usuario por su email.

        Args:
            email: Email a buscar

        Returns:
            UserProfile si existe, None si no

        Note:
            Esta operación requiere acceso a auth.users, por lo que
            usa el cliente admin si está disponible.
        """
        return await self._profile_service.obtener_por_email(email)

    async def actualizar_perfil(
        self,
        user_id: UUID,
        datos: UserProfileUpdate
    ) -> UserProfile:
        """
        Actualiza el perfil de un usuario.

        Args:
            user_id: UUID del usuario a actualizar
            datos: Datos a actualizar (solo campos no-None se actualizan)

        Returns:
            UserProfile actualizado

        Raises:
            NotFoundError: Si el usuario no existe
            DatabaseError: Si hay error de BD
        """
        return await self._profile_service.actualizar_perfil(user_id, datos)

    async def cambiar_rol(self, user_id: UUID, nuevo_rol: str) -> UserProfile:
        """
        Cambia el rol de un usuario.

        Args:
            user_id: UUID del usuario
            nuevo_rol: Nuevo rol (superadmin, admin, institucion, proveedor, client, empleado)

        Returns:
            UserProfile actualizado

        Raises:
            ValidationError: Si el rol no es válido
            NotFoundError: Si el usuario no existe
            DatabaseError: Si hay error de BD

        Note:
            Esta operación debería estar protegida para solo admins.
        """
        return await self._profile_service.cambiar_rol(user_id, nuevo_rol)

    async def desactivar_usuario(self, user_id: UUID) -> UserProfile:
        """
        Desactiva un usuario (soft delete).

        Args:
            user_id: UUID del usuario a desactivar

        Returns:
            UserProfile actualizado

        Raises:
            NotFoundError: Si el usuario no existe
            BusinessRuleError: Si el usuario ya está inactivo
        """
        return await self._profile_service.desactivar_usuario(user_id)

    async def activar_usuario(self, user_id: UUID) -> UserProfile:
        """
        Reactiva un usuario desactivado.

        Args:
            user_id: UUID del usuario a activar

        Returns:
            UserProfile actualizado

        Raises:
            NotFoundError: Si el usuario no existe
            BusinessRuleError: Si el usuario ya está activo
        """
        return await self._profile_service.activar_usuario(user_id)

    async def listar_usuarios(
        self,
        incluir_inactivos: bool = False,
        rol: Optional[str] = None,
        limite: int = 50,
        offset: int = 0,
    ) -> List[UserProfileResumen]:
        """
        Lista usuarios con filtros opcionales.

        Args:
            incluir_inactivos: Si True, incluye usuarios desactivados
            rol: Filtrar por rol ('admin' o 'client')
            limite: Máximo de resultados
            offset: Registros a saltar

        Returns:
            Lista de UserProfileResumen

        Raises:
            DatabaseError: Si hay error de BD

        Note:
            Requiere permisos de admin (RLS lo valida).
        """
        return await self._profile_service.listar_usuarios(
            incluir_inactivos=incluir_inactivos,
            rol=rol,
            limite=limite,
            offset=offset,
        )

    async def _actualizar_ultimo_acceso(self, user_id: UUID) -> None:
        """Actualiza el timestamp de último acceso."""
        await self._profile_service.actualizar_ultimo_acceso(user_id)

    async def obtener_empresas_usuario(
        self,
        user_id: UUID
    ) -> List[UserCompanyResumen]:
        """
        Obtiene las empresas a las que un usuario tiene acceso.

        Args:
            user_id: UUID del usuario

        Returns:
            Lista de UserCompanyResumen con datos de las empresas

        Raises:
            DatabaseError: Si hay error de BD
        """
        return await self._company_service.obtener_empresas_usuario(user_id)

    async def asignar_empresa(
        self,
        user_id: UUID,
        empresa_id: int,
        es_principal: bool = False,
        rol_empresa: Optional[str] = None,
    ) -> UserCompany:
        """
        Asigna una empresa a un usuario.

        Args:
            user_id: UUID del usuario
            empresa_id: ID de la empresa a asignar
            es_principal: Si debe ser la empresa principal

        Returns:
            UserCompany creada

        Raises:
            NotFoundError: Si el usuario o empresa no existe
            DuplicateError: Si la relación ya existe
            DatabaseError: Si hay error de BD
        """
        return await self._company_service.asignar_empresa(
            user_id=user_id,
            empresa_id=empresa_id,
            es_principal=es_principal,
            rol_empresa=rol_empresa,
        )

    async def quitar_empresa(self, user_id: UUID, empresa_id: int) -> bool:
        """
        Remueve el acceso de un usuario a una empresa.

        Args:
            user_id: UUID del usuario
            empresa_id: ID de la empresa a remover

        Returns:
            True si se removió correctamente

        Raises:
            NotFoundError: Si la relación no existe
            BusinessRuleError: Si es la única empresa del usuario
            DatabaseError: Si hay error de BD
        """
        return await self._company_service.quitar_empresa(user_id, empresa_id)

    async def cambiar_empresa_principal(
        self,
        user_id: UUID,
        empresa_id: int
    ) -> UserCompany:
        """
        Cambia la empresa principal de un usuario.

        Args:
            user_id: UUID del usuario
            empresa_id: ID de la nueva empresa principal

        Returns:
            UserCompany actualizada

        Raises:
            NotFoundError: Si la relación no existe
            DatabaseError: Si hay error de BD
        """
        return await self._company_service.cambiar_empresa_principal(user_id, empresa_id)

    async def _quitar_principal_actual(self, user_id: UUID) -> None:
        await self._company_service.quitar_principal_actual(user_id)

    async def _validar_empresa_existe(self, empresa_id: int) -> None:
        await self._company_service.validar_empresa_existe(empresa_id)

    def _query_user_company(
        self,
        user_id: UUID,
        empresa_id: int,
        *,
        select: str = "*",
    ):
        """Query base para la relación usuario-empresa."""
        return self.supabase_admin.table(self.tabla_companies)\
            .select(select)\
            .eq('user_id', str(user_id))\
            .eq('empresa_id', empresa_id)

    def _obtener_relacion_user_company(
        self,
        user_id: UUID,
        empresa_id: int,
        *,
        select: str = "*",
    ) -> Optional[dict]:
        """Obtiene la fila de user_companies para un usuario y empresa."""
        result = self._query_user_company(
            user_id,
            empresa_id,
            select=select,
        ).execute()
        return result.data[0] if result.data else None

    def _actualizar_relacion_user_company(
        self,
        user_id: UUID,
        empresa_id: int,
        payload: dict,
    ):
        """Actualiza la relación user_companies para un usuario y empresa."""
        return self.supabase_admin.table(self.tabla_companies)\
            .update(payload)\
            .eq('user_id', str(user_id))\
            .eq('empresa_id', empresa_id)\
            .execute()

    async def resetear_password(self, user_id: UUID, nueva_password: str) -> None:
        await self._auth_service.resetear_password(user_id, nueva_password)

    async def validar_super_admin(self, user_id: UUID) -> None:
        """
        Valida que el usuario tiene permiso de gestionar usuarios (super admin).

        Raises:
            BusinessRuleError: Si no tiene el permiso
        """
        await self._profile_service.validar_super_admin(user_id)

    async def validar_permiso(
        self, user_id: UUID, modulo: str, accion: str
    ) -> None:
        """
        Valida que el usuario tiene un permiso específico.

        Args:
            user_id: UUID del usuario
            modulo: Nombre del módulo (requisiciones, entregables, etc.)
            accion: 'operar' o 'autorizar'

        Raises:
            BusinessRuleError: Si no tiene el permiso
        """
        await self._profile_service.validar_permiso(user_id, modulo, accion)

    async def usuario_tiene_acceso_empresa(
        self,
        user_id: UUID,
        empresa_id: int
    ) -> bool:
        """
        Verifica si un usuario tiene acceso a una empresa específica.

        Args:
            user_id: UUID del usuario
            empresa_id: ID de la empresa

        Returns:
            True si tiene acceso, False si no
        """
        return await self._company_service.usuario_tiene_acceso_empresa(user_id, empresa_id)

    async def asignar_rol_empresa(
        self, user_id: UUID, empresa_id: int, rol_empresa: str
    ) -> UserCompany:
        """
        Asigna o actualiza el rol de un usuario en una empresa.

        Args:
            user_id: UUID del usuario
            empresa_id: ID de la empresa
            rol_empresa: Rol a asignar (admin_empresa, rrhh, operaciones, etc.)

        Returns:
            UserCompany actualizada

        Raises:
            NotFoundError: Si la relación usuario-empresa no existe
            ValidationError: Si el rol no es válido
            DatabaseError: Si hay error de BD
        """
        return await self._company_service.asignar_rol_empresa(user_id, empresa_id, rol_empresa)

    async def verificar_permiso_empresa(
        self, user_id: UUID, empresa_id: int, roles_requeridos: list[str]
    ) -> bool:
        """
        Verifica si el usuario tiene alguno de los roles requeridos en la empresa.

        Args:
            user_id: UUID del usuario
            empresa_id: ID de la empresa
            roles_requeridos: Lista de roles aceptados (ej: ['rrhh', 'admin_empresa'])

        Returns:
            True si tiene alguno de los roles requeridos
        """
        return await self._company_service.verificar_permiso_empresa(
            user_id,
            empresa_id,
            roles_requeridos,
        )

    async def obtener_empresa_principal(
        self,
        user_id: UUID
    ) -> Optional[UserCompanyResumen]:
        """
        Obtiene la empresa principal de un usuario.

        Args:
            user_id: UUID del usuario

        Returns:
            UserCompanyResumen de la empresa principal, o None si no tiene
        """
        return await self._company_service.obtener_empresa_principal(user_id)

    async def obtener_usuarios_con_permiso(
        self,
        modulo: str,
        accion: str,
    ) -> List[UserProfile]:
        """
        Obtiene todos los usuarios activos que tienen un permiso específico.

        Args:
            modulo: Nombre del módulo (requisiciones, entregables, etc.)
            accion: 'operar' o 'autorizar'

        Returns:
            Lista de UserProfile con el permiso

        Raises:
            DatabaseError: Si hay error de BD
        """
        return await self._profile_service.obtener_usuarios_con_permiso(modulo, accion)

    def _generar_password_temporal(self) -> str:
        import secrets
        import string
        chars = string.ascii_letters + string.digits + "!@#$"
        return ''.join(secrets.choice(chars) for _ in range(16))

    async def listar_usuarios_empresa(self, empresa_id: int) -> list[dict]:
        """
        Lista todos los usuarios asignados a una empresa, aplanando los datos del perfil.

        Args:
            empresa_id: ID de la empresa

        Returns:
            Lista de dicts con campos: user_id, email, nombre_completo, telefono,
            rol_empresa, permisos, activo, es_principal, created_at
        """
        return await self._company_service.listar_usuarios_empresa(empresa_id)

    async def crear_o_vincular_usuario_empresa(
        self,
        email: str,
        nombre_completo: str,
        empresa_id: int,
        rol_empresa: str,
        permisos: dict,
        telefono: str = "",
        actor_user_id: Optional[UUID] = None,
    ) -> dict:
        """
        Crea un usuario nuevo o vincula uno existente a la empresa.

        Flujo:
        1. Si el email no existe → crea usuario nuevo con password temporal
        2. Si existe como proveedor/client → verifica que no tenga ya asignación en esta
           empresa (DuplicateError si la tiene) y lo vincula
        3. Si existe con otro rol (admin, superadmin, etc.) → BusinessRuleError genérico

        Returns:
            Dict con user_id, email, nombre_completo, rol_empresa, es_nuevo
        """
        return await self._company_service.crear_o_vincular_usuario_empresa(
            email=email,
            nombre_completo=nombre_completo,
            empresa_id=empresa_id,
            rol_empresa=rol_empresa,
            permisos=permisos,
            telefono=telefono,
            actor_user_id=actor_user_id,
        )

    async def toggle_activo_en_empresa(self, user_id: UUID, empresa_id: int) -> bool:
        """
        Alterna el estado activo del usuario en la empresa (activo/inactivo).

        Requiere que la columna `activo` exista en user_companies (migración 041).

        Args:
            user_id: UUID del usuario
            empresa_id: ID de la empresa

        Returns:
            Nuevo estado de activo (True = activo, False = inactivo)

        Raises:
            NotFoundError: Si la relación usuario-empresa no existe
            DatabaseError: Si hay error de BD
        """
        return await self._company_service.toggle_activo_en_empresa(user_id, empresa_id)


# =============================================================================
# SINGLETON
# =============================================================================

user_service = UserService()
