"""
Servicio de Usuarios y Autenticación.

Este servicio gestiona tres responsabilidades principales:

1. AUTENTICACIÓN (Supabase Auth):
   - Crear usuarios (requiere service_role key)
   - Login/logout
   - Validación de tokens JWT

2. PERFILES (user_profiles):
   - CRUD de perfiles de usuario
   - Cambio de roles (solo admin)

3. EMPRESAS (user_companies):
   - Asignar/quitar acceso a empresas
   - Gestionar empresa principal

IMPORTANTE:
- La creación de usuarios requiere SUPABASE_SERVICE_KEY (service_role)
- Las operaciones de lectura/escritura normales usan SUPABASE_KEY (anon)
- RLS está activo: usuarios normales solo ven su propio perfil
"""
import logging
from datetime import datetime
from typing import List, Optional, Tuple
from uuid import UUID

from supabase import create_client, Client

from app.core.config import Config
from app.core.exceptions import (
    NotFoundError,
    DuplicateError,
    DatabaseError,
    BusinessRuleError,
    ValidationError,
)
from app.database import db_manager
from app.entities.user_profile import (
    UserProfile,
    UserProfileCreate,
    UserProfileUpdate,
    UserProfileResumen,
)
from app.entities.user_company import (
    UserCompany,
    UserCompanyCreate,
    UserCompanyResumen,
)

logger = logging.getLogger(__name__)


# =============================================================================
# SERVICIO PRINCIPAL
# =============================================================================

class UserService:
    """
    Servicio para gestión de usuarios, autenticación y permisos.

    Utiliza dos clientes de Supabase:
    - Cliente normal (anon key): Para operaciones sujetas a RLS
    - Cliente admin (service_role key): Para crear usuarios y operaciones privilegiadas

    Attributes:
        supabase: Cliente con anon key para operaciones normales
        supabase_admin: Cliente con service_role key para operaciones admin
        tabla_profiles: Nombre de la tabla de perfiles
        tabla_companies: Nombre de la tabla de relaciones usuario-empresa
    """

    def __init__(self):
        """Inicializa el servicio con ambos clientes de Supabase."""
        # Cliente anon para auth de usuario (sign_in, sign_out, tokens)
        self.supabase: Client = db_manager.get_anon_client()
        self.tabla_profiles = 'user_profiles'
        self.tabla_companies = 'user_companies'

        # Cliente admin (service_role, ignora RLS) - para crear usuarios y queries de datos
        self.supabase_admin: Optional[Client] = db_manager.get_client()

    # =========================================================================
    # AUTENTICACIÓN
    # =========================================================================

    async def crear_usuario(
        self,
        datos: UserProfileCreate,
        empresas_ids: Optional[List[int]] = None,
        empresa_principal_id: Optional[int] = None,
    ) -> UserProfile:
        """
        Crea un nuevo usuario en Supabase Auth.

        El trigger en la BD automáticamente crea el registro en user_profiles
        con los datos del metadata.

        Args:
            datos: Datos del usuario a crear (email, password, nombre, rol, telefono)
            empresas_ids: Lista de IDs de empresas a asignar (opcional)
            empresa_principal_id: ID de la empresa principal (debe estar en empresas_ids)

        Returns:
            UserProfile del usuario creado

        Raises:
            BusinessRuleError: Si no hay service_role key configurada
            DuplicateError: Si el email ya existe
            ValidationError: Si los datos no son válidos
            DatabaseError: Si hay error de BD
        """
        if not self.supabase_admin:
            raise BusinessRuleError(
                "No se puede crear usuarios: SUPABASE_SERVICE_KEY no configurada"
            )

        # Validar empresa_principal está en la lista
        if empresa_principal_id and empresas_ids:
            if empresa_principal_id not in empresas_ids:
                raise ValidationError(
                    "La empresa principal debe estar en la lista de empresas asignadas"
                )

        try:
            # Preparar metadata para el trigger
            metadata = datos.to_auth_metadata()

            # Crear usuario en Supabase Auth
            response = self.supabase_admin.auth.admin.create_user({
                "email": datos.email,
                "password": datos.password,
                "email_confirm": True,  # Confirmar email automáticamente
                "user_metadata": metadata,
            })

            if not response.user:
                raise DatabaseError("Error al crear usuario en Supabase Auth")

            user_id = UUID(response.user.id)
            logger.info(f"Usuario creado en Auth: {user_id}")

            # Esperar un momento para que el trigger cree el profile
            # (En producción esto es casi instantáneo, pero por seguridad)
            import asyncio
            await asyncio.sleep(0.5)

            # Obtener el profile creado por el trigger
            profile = await self.obtener_por_id(user_id)

            # Actualizar permisos granulares si se proporcionaron
            if datos.permisos or datos.puede_gestionar_usuarios:
                permisos_update = {}
                if datos.permisos:
                    permisos_update['permisos'] = datos.permisos
                if datos.puede_gestionar_usuarios:
                    permisos_update['puede_gestionar_usuarios'] = datos.puede_gestionar_usuarios
                if permisos_update:
                    self.supabase_admin.table(self.tabla_profiles)\
                        .update(permisos_update)\
                        .eq('id', str(user_id))\
                        .execute()
                    profile = await self.obtener_por_id(user_id)

            # Asignar empresas si se proporcionaron
            if empresas_ids:
                for empresa_id in empresas_ids:
                    es_principal = (empresa_id == empresa_principal_id)
                    try:
                        await self.asignar_empresa(
                            user_id=user_id,
                            empresa_id=empresa_id,
                            es_principal=es_principal,
                        )
                    except Exception as e:
                        logger.warning(
                            f"Error asignando empresa {empresa_id} a usuario {user_id}: {e}"
                        )

            return profile

        except Exception as e:
            error_msg = str(e).lower()
            if "already registered" in error_msg or "already exists" in error_msg:
                raise DuplicateError(
                    f"El email {datos.email} ya está registrado",
                    field="email",
                    value=datos.email
                )
            logger.error(f"Error creando usuario: {e}")
            raise DatabaseError(f"Error al crear usuario: {str(e)}")

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
        try:
            # Autenticar con Supabase Auth
            response = self.supabase.auth.sign_in_with_password({
                "email": email.strip().lower(),
                "password": password,
            })

            if not response.user or not response.session:
                raise ValidationError("Credenciales inválidas")

            user_id = UUID(response.user.id)

            # Obtener el profile
            profile = await self.obtener_por_id(user_id)

            # Verificar que el usuario esté activo
            if not profile.activo:
                # Cerrar la sesión que acabamos de crear
                self.supabase.auth.sign_out()
                raise BusinessRuleError(
                    "Tu cuenta está desactivada. Contacta al administrador."
                )

            # Actualizar último acceso
            await self._actualizar_ultimo_acceso(user_id)

            # Preparar datos de sesión para el frontend
            session_data = {
                "access_token": response.session.access_token,
                "refresh_token": response.session.refresh_token,
                "expires_at": response.session.expires_at,
                "user_id": str(user_id),
            }

            logger.info(f"Login exitoso: {email}")
            return profile, session_data

        except ValidationError:
            raise
        except BusinessRuleError:
            raise
        except Exception as e:
            error_msg = str(e).lower()
            if "invalid" in error_msg or "credentials" in error_msg:
                raise ValidationError("Email o contraseña incorrectos")
            logger.error(f"Error en login: {e}")
            raise DatabaseError(f"Error de autenticación: {str(e)}")

    async def logout(self) -> bool:
        """
        Cierra la sesión actual.

        Returns:
            True si se cerró correctamente

        Note:
            Esta operación es del lado del servidor. El frontend
            también debe limpiar los tokens almacenados.
        """
        try:
            self.supabase.auth.sign_out()
            logger.info("Logout exitoso")
            return True
        except Exception as e:
            logger.warning(f"Error en logout (no crítico): {e}")
            return True  # Consideramos exitoso aunque falle el servidor

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
        try:
            # Obtener usuario del token
            response = self.supabase.auth.get_user(access_token)

            if not response.user:
                return None

            user_id = UUID(response.user.id)
            profile = await self.obtener_por_id(user_id)

            # Verificar que esté activo
            if not profile.activo:
                return None

            return profile

        except Exception as e:
            logger.debug(f"Token inválido o expirado: {e}")
            return None

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
        try:
            response = self.supabase.auth.refresh_session(refresh_token)

            if not response.session:
                return None

            return {
                "access_token": response.session.access_token,
                "refresh_token": response.session.refresh_token,
                "expires_at": response.session.expires_at,
            }

        except Exception as e:
            logger.debug(f"Error refrescando token: {e}")
            return None

    # =========================================================================
    # GESTIÓN DE PERFILES
    # =========================================================================

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
        try:
            result = self.supabase_admin.table(self.tabla_profiles)\
                .select('*')\
                .eq('id', str(user_id))\
                .execute()

            if not result.data:
                raise NotFoundError(f"Usuario con ID {user_id} no encontrado")

            return UserProfile(**result.data[0])

        except NotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error obteniendo usuario {user_id}: {e}")
            raise DatabaseError(f"Error de base de datos: {str(e)}")

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
        if not self.supabase_admin:
            logger.warning("No se puede buscar por email sin service_role key")
            return None

        try:
            # Buscar en auth.users
            response = self.supabase_admin.auth.admin.list_users()

            for user in response:
                if user.email and user.email.lower() == email.lower():
                    return await self.obtener_por_id(UUID(user.id))

            return None

        except Exception as e:
            logger.error(f"Error buscando usuario por email {email}: {e}")
            return None

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
        # Verificar que existe
        await self.obtener_por_id(user_id)

        try:
            # Preparar datos para actualizar (excluir None)
            datos_update = datos.model_dump(
                mode='json',
                exclude_none=True,
            )

            if not datos_update:
                # Nada que actualizar, retornar el profile actual
                return await self.obtener_por_id(user_id)

            result = self.supabase_admin.table(self.tabla_profiles)\
                .update(datos_update)\
                .eq('id', str(user_id))\
                .execute()

            if not result.data:
                raise DatabaseError("No se pudo actualizar el perfil")

            logger.info(f"Perfil actualizado: {user_id}")
            return UserProfile(**result.data[0])

        except NotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error actualizando perfil {user_id}: {e}")
            raise DatabaseError(f"Error de base de datos: {str(e)}")

    async def cambiar_rol(self, user_id: UUID, nuevo_rol: str) -> UserProfile:
        """
        Cambia el rol de un usuario.

        Args:
            user_id: UUID del usuario
            nuevo_rol: Nuevo rol ('admin' o 'client')

        Returns:
            UserProfile actualizado

        Raises:
            ValidationError: Si el rol no es válido
            NotFoundError: Si el usuario no existe
            DatabaseError: Si hay error de BD

        Note:
            Esta operación debería estar protegida para solo admins.
        """
        if nuevo_rol not in ('admin', 'client'):
            raise ValidationError(f"Rol inválido: {nuevo_rol}. Use 'admin' o 'client'")

        return await self.actualizar_perfil(
            user_id,
            UserProfileUpdate(rol=nuevo_rol)
        )

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
        profile = await self.obtener_por_id(user_id)

        if not profile.activo:
            raise BusinessRuleError("El usuario ya está desactivado")

        return await self.actualizar_perfil(
            user_id,
            UserProfileUpdate(activo=False)
        )

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
        profile = await self.obtener_por_id(user_id)

        if profile.activo:
            raise BusinessRuleError("El usuario ya está activo")

        return await self.actualizar_perfil(
            user_id,
            UserProfileUpdate(activo=True)
        )

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
        try:
            query = self.supabase_admin.table(self.tabla_profiles).select('*')

            if not incluir_inactivos:
                query = query.eq('activo', True)

            if rol:
                query = query.eq('rol', rol)

            query = query.order('fecha_creacion', desc=True)\
                .range(offset, offset + limite - 1)

            result = query.execute()

            # Obtener emails de auth.users (un solo request)
            emails_map = {}
            try:
                auth_users = self.supabase_admin.auth.admin.list_users()
                emails_map = {u.id: u.email for u in auth_users if u.email}
            except Exception as e:
                logger.warning(f"No se pudieron obtener emails de auth.users: {e}")

            # Convertir a resumen con datos enriquecidos
            resumenes = []
            for data in result.data:
                profile = UserProfile(**data)
                # Obtener cantidad de empresas
                empresas = await self.obtener_empresas_usuario(profile.id)
                empresa_principal = next(
                    (e.empresa_nombre for e in empresas if e.es_principal),
                    None
                )

                resumen = UserProfileResumen(
                    id=profile.id,
                    nombre_completo=profile.nombre_completo,
                    rol=profile.rol if isinstance(profile.rol, str) else profile.rol.value,
                    activo=profile.activo,
                    ultimo_acceso=profile.ultimo_acceso,
                    puede_gestionar_usuarios=profile.puede_gestionar_usuarios,
                    permisos=profile.permisos,
                    email=emails_map.get(str(profile.id)),
                    cantidad_empresas=len(empresas),
                    empresa_principal=empresa_principal,
                )
                resumenes.append(resumen)

            return resumenes

        except Exception as e:
            logger.error(f"Error listando usuarios: {e}")
            raise DatabaseError(f"Error de base de datos: {str(e)}")

    async def _actualizar_ultimo_acceso(self, user_id: UUID) -> None:
        """Actualiza el timestamp de último acceso."""
        try:
            self.supabase_admin.table(self.tabla_profiles)\
                .update({'ultimo_acceso': datetime.now().isoformat()})\
                .eq('id', str(user_id))\
                .execute()
        except Exception as e:
            # No es crítico, solo loguear
            logger.warning(f"Error actualizando último acceso: {e}")

    # =========================================================================
    # GESTIÓN DE EMPRESAS
    # =========================================================================

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
        try:
            # Query con JOIN a empresas para obtener datos enriquecidos
            result = self.supabase_admin.table(self.tabla_companies)\
                .select('*, empresas(nombre_comercial, rfc, tipo_empresa, estatus)')\
                .eq('user_id', str(user_id))\
                .order('es_principal', desc=True)\
                .execute()

            resumenes = []
            for data in result.data:
                empresa_data = data.get('empresas', {})
                resumen = UserCompanyResumen(
                    id=data['id'],
                    user_id=UUID(data['user_id']),
                    empresa_id=data['empresa_id'],
                    es_principal=data['es_principal'],
                    fecha_creacion=data.get('fecha_creacion'),
                    empresa_nombre=empresa_data.get('nombre_comercial'),
                    empresa_rfc=empresa_data.get('rfc'),
                    empresa_tipo=empresa_data.get('tipo_empresa'),
                    empresa_activa=empresa_data.get('estatus') == 'ACTIVO',
                )
                resumenes.append(resumen)

            return resumenes

        except Exception as e:
            logger.error(f"Error obteniendo empresas de usuario {user_id}: {e}")
            raise DatabaseError(f"Error de base de datos: {str(e)}")

    async def asignar_empresa(
        self,
        user_id: UUID,
        empresa_id: int,
        es_principal: bool = False,
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
        # Verificar que el usuario existe
        await self.obtener_por_id(user_id)

        # Verificar que la empresa existe
        await self._validar_empresa_existe(empresa_id)

        try:
            # Si es principal, quitar principal de otras
            if es_principal:
                await self._quitar_principal_actual(user_id)

            # Crear la relación
            datos = {
                'user_id': str(user_id),
                'empresa_id': empresa_id,
                'es_principal': es_principal,
            }

            result = self.supabase_admin.table(self.tabla_companies)\
                .insert(datos)\
                .execute()

            if not result.data:
                raise DatabaseError("No se pudo asignar la empresa")

            logger.info(f"Empresa {empresa_id} asignada a usuario {user_id}")
            return UserCompany(**result.data[0])

        except Exception as e:
            error_msg = str(e).lower()
            if "duplicate" in error_msg or "unique" in error_msg:
                raise DuplicateError(
                    f"El usuario ya tiene asignada la empresa {empresa_id}",
                    field="empresa_id",
                    value=str(empresa_id)
                )
            logger.error(f"Error asignando empresa: {e}")
            raise DatabaseError(f"Error de base de datos: {str(e)}")

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
        # Verificar que la relación existe
        empresas = await self.obtener_empresas_usuario(user_id)
        relacion = next(
            (e for e in empresas if e.empresa_id == empresa_id),
            None
        )

        if not relacion:
            raise NotFoundError(
                f"El usuario no tiene asignada la empresa {empresa_id}"
            )

        # No permitir quedarse sin empresas (opcional, depende de reglas de negocio)
        # if len(empresas) == 1:
        #     raise BusinessRuleError("El usuario debe tener al menos una empresa asignada")

        try:
            self.supabase_admin.table(self.tabla_companies)\
                .delete()\
                .eq('user_id', str(user_id))\
                .eq('empresa_id', empresa_id)\
                .execute()

            # Si era la principal, asignar otra como principal
            if relacion.es_principal and len(empresas) > 1:
                otra_empresa = next(e for e in empresas if e.empresa_id != empresa_id)
                await self.cambiar_empresa_principal(user_id, otra_empresa.empresa_id)

            logger.info(f"Empresa {empresa_id} removida de usuario {user_id}")
            return True

        except Exception as e:
            logger.error(f"Error removiendo empresa: {e}")
            raise DatabaseError(f"Error de base de datos: {str(e)}")

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
        # Verificar que la relación existe
        empresas = await self.obtener_empresas_usuario(user_id)
        relacion = next(
            (e for e in empresas if e.empresa_id == empresa_id),
            None
        )

        if not relacion:
            raise NotFoundError(
                f"El usuario no tiene asignada la empresa {empresa_id}"
            )

        try:
            # Quitar principal actual
            await self._quitar_principal_actual(user_id)

            # Marcar la nueva como principal
            result = self.supabase_admin.table(self.tabla_companies)\
                .update({'es_principal': True})\
                .eq('user_id', str(user_id))\
                .eq('empresa_id', empresa_id)\
                .execute()

            if not result.data:
                raise DatabaseError("No se pudo cambiar la empresa principal")

            logger.info(f"Empresa principal de {user_id} cambiada a {empresa_id}")
            return UserCompany(**result.data[0])

        except NotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error cambiando empresa principal: {e}")
            raise DatabaseError(f"Error de base de datos: {str(e)}")

    async def _quitar_principal_actual(self, user_id: UUID) -> None:
        """Quita la marca de principal de todas las empresas del usuario."""
        try:
            self.supabase_admin.table(self.tabla_companies)\
                .update({'es_principal': False})\
                .eq('user_id', str(user_id))\
                .eq('es_principal', True)\
                .execute()
        except Exception as e:
            logger.warning(f"Error quitando principal actual: {e}")

    async def _validar_empresa_existe(self, empresa_id: int) -> None:
        """Valida que una empresa exista y esté activa."""
        from app.services import empresa_service

        try:
            empresa = await empresa_service.obtener_por_id(empresa_id)
            if not empresa.esta_activa():
                raise BusinessRuleError(
                    f"La empresa {empresa_id} no está activa"
                )
        except NotFoundError:
            raise NotFoundError(f"Empresa con ID {empresa_id} no encontrada")

    # =========================================================================
    # RESET DE CONTRASEÑA (SUPER ADMIN)
    # =========================================================================

    async def resetear_password(self, user_id: UUID, nueva_password: str) -> None:
        """
        Resetea la contraseña de un usuario (solo super admin).

        Args:
            user_id: UUID del usuario
            nueva_password: Nueva contraseña (mínimo 8 caracteres)

        Raises:
            BusinessRuleError: Si no hay service_role key configurada
            DatabaseError: Si hay error al actualizar
        """
        if not self.supabase_admin:
            raise BusinessRuleError(
                "No se puede resetear: SUPABASE_SERVICE_KEY no configurada"
            )

        try:
            self.supabase_admin.auth.admin.update_user_by_id(
                str(user_id),
                {"password": nueva_password},
            )
            logger.info(f"Contraseña reseteada para usuario {user_id}")
        except Exception as e:
            logger.error(f"Error reseteando contraseña de {user_id}: {e}")
            raise DatabaseError(f"Error al resetear contraseña: {str(e)}")

    # =========================================================================
    # VALIDACIÓN DE PERMISOS
    # =========================================================================

    async def validar_super_admin(self, user_id: UUID) -> None:
        """
        Valida que el usuario tiene permiso de gestionar usuarios (super admin).

        Raises:
            BusinessRuleError: Si no tiene el permiso
        """
        profile = await self.obtener_por_id(user_id)
        if not profile.puede_gestionar_usuarios:
            raise BusinessRuleError(
                "No tiene permiso para gestionar usuarios"
            )

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
        profile = await self.obtener_por_id(user_id)
        if not profile.permisos.get(modulo, {}).get(accion, False):
            raise BusinessRuleError(
                f"No tiene permiso para {accion} en {modulo}"
            )

    # =========================================================================
    # UTILIDADES
    # =========================================================================

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
        try:
            result = self.supabase_admin.table(self.tabla_companies)\
                .select('id')\
                .eq('user_id', str(user_id))\
                .eq('empresa_id', empresa_id)\
                .execute()

            return len(result.data) > 0

        except Exception as e:
            logger.error(f"Error verificando acceso: {e}")
            return False

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
        empresas = await self.obtener_empresas_usuario(user_id)
        return next(
            (e for e in empresas if e.es_principal),
            empresas[0] if empresas else None  # Fallback a la primera
        )

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
        try:
            # Obtener todos los usuarios activos
            result = self.supabase_admin.table(self.tabla_profiles)\
                .select('*')\
                .eq('activo', True)\
                .execute()

            usuarios_con_permiso = []
            for data in result.data:
                profile = UserProfile(**data)
                # Verificar si tiene el permiso
                if profile.permisos.get(modulo, {}).get(accion, False):
                    usuarios_con_permiso.append(profile)

            return usuarios_con_permiso

        except Exception as e:
            logger.error(f"Error obteniendo usuarios con permiso {modulo}:{accion}: {e}")
            raise DatabaseError(f"Error de base de datos: {str(e)}")


# =============================================================================
# SINGLETON
# =============================================================================

user_service = UserService()
