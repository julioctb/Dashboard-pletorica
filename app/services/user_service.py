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
from app.core.validation import validar_password_usuario
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
    UserCompanyAsignacionInicial,
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

    # =========================================================================
    # AUTENTICACIÓN
    # =========================================================================

    async def crear_usuario(
        self,
        datos: UserProfileCreate,
        empresas_ids: Optional[List[int]] = None,
        empresa_principal_id: Optional[int] = None,
        asignaciones_empresas: Optional[List[UserCompanyAsignacionInicial]] = None,
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

        rol_plataforma = datos.rol if isinstance(datos.rol, str) else datos.rol.value

        # Compatibilidad: si no vienen asignaciones nuevas, construirlas desde firma legacy
        if asignaciones_empresas is None and empresas_ids:
            asignaciones_empresas = [
                UserCompanyAsignacionInicial(
                    empresa_id=empresa_id,
                    es_principal=(empresa_id == empresa_principal_id) if empresa_principal_id else False,
                )
                for empresa_id in empresas_ids
            ]

        # Validar empresa_principal está en la lista legacy
        if empresa_principal_id and empresas_ids:
            if empresa_principal_id not in empresas_ids:
                raise ValidationError(
                    "La empresa principal debe estar en la lista de empresas asignadas"
                )

        # Reglas por rol de plataforma
        if rol_plataforma == 'institucion' and asignaciones_empresas:
            raise ValidationError(
                "Los usuarios institucionales no usan asignaciones de empresa (user_companies)"
            )

        if rol_plataforma in ('proveedor', 'client'):
            if not asignaciones_empresas:
                raise ValidationError(
                    "Los usuarios proveedor requieren al menos una empresa asignada"
                )

        if rol_plataforma in ('admin', 'superadmin', 'empleado') and asignaciones_empresas:
            raise ValidationError(
                f"El rol '{rol_plataforma}' no debe incluir asignaciones de empresa"
            )

        if asignaciones_empresas:
            ids_empresas = [a.empresa_id for a in asignaciones_empresas]
            if len(set(ids_empresas)) != len(ids_empresas):
                raise ValidationError("No se puede asignar la misma empresa dos veces")

            principales = [a for a in asignaciones_empresas if a.es_principal]
            if len(principales) == 0:
                asignaciones_empresas[0].es_principal = True
            elif len(principales) > 1:
                raise ValidationError("Solo puede existir una empresa principal")

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

            # Actualizar campos que el trigger aún no soporta (permisos e institucion_id)
            if datos.permisos or datos.puede_gestionar_usuarios:
                permisos_update = {}
                if datos.permisos:
                    permisos_update['permisos'] = datos.permisos
                if datos.puede_gestionar_usuarios:
                    permisos_update['puede_gestionar_usuarios'] = datos.puede_gestionar_usuarios
                if permisos_update:
                    self._actualizar_profile_data(user_id, permisos_update)
                    profile = await self.obtener_por_id(user_id)

            if datos.institucion_id:
                self._actualizar_profile_data(
                    user_id,
                    {'institucion_id': datos.institucion_id},
                )
                profile = await self.obtener_por_id(user_id)

            # Asignar empresas si se proporcionaron
            if asignaciones_empresas:
                for asignacion in asignaciones_empresas:
                    try:
                        await self.asignar_empresa(
                            user_id=user_id,
                            empresa_id=asignacion.empresa_id,
                            es_principal=asignacion.es_principal,
                            rol_empresa=(
                                asignacion.rol_empresa
                                if isinstance(asignacion.rol_empresa, str)
                                else asignacion.rol_empresa.value
                            ),
                        )
                    except Exception as e:
                        logger.warning(
                            f"Error asignando empresa {asignacion.empresa_id} a usuario {user_id}: {e}"
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

    async def obtener_email_desde_token(self, access_token: str) -> Optional[str]:
        """
        Obtiene el email del usuario autenticado a partir del access token.

        Args:
            access_token: JWT de acceso vigente

        Returns:
            Email normalizado si se pudo resolver, None en caso contrario
        """
        if not access_token:
            return None

        try:
            response = self.supabase.auth.get_user(access_token)
            user = getattr(response, "user", None)
            email = getattr(user, "email", None) if user else None
            if not email:
                return None
            return str(email).strip().lower()
        except Exception as e:
            logger.debug(f"No se pudo resolver email desde token: {e}")
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
        if not access_token or not refresh_token:
            raise ValidationError("La sesión es inválida o expiró. Inicia sesión nuevamente.")

        error_password = validar_password_usuario(nueva_password)
        if error_password:
            raise ValidationError(
                "La contraseña debe tener al menos 8 caracteres"
                if "Minimo" in error_password
                else error_password
            )

        try:
            cliente_auth = create_client(Config.SUPABASE_URL, Config.SUPABASE_KEY)

            # Compatibilidad defensiva con distintas firmas de supabase-py
            try:
                cliente_auth.auth.set_session(access_token, refresh_token)
            except TypeError:
                cliente_auth.auth.set_session({
                    "access_token": access_token,
                    "refresh_token": refresh_token,
                })

            try:
                cliente_auth.auth.update_user({"password": nueva_password})
            except TypeError:
                cliente_auth.auth.update_user(password=nueva_password)

            logger.info("Contraseña actualizada por usuario autenticado")
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error cambiando contraseña de usuario autenticado: {e}")
            raise DatabaseError(f"Error al cambiar contraseña: {str(e)}")

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
            data = self._obtener_profile_data(user_id)
            if not data:
                raise NotFoundError(f"Usuario con ID {user_id} no encontrado")
            return UserProfile(**data)

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
            user = self._buscar_auth_user_por_email(email)
            if user and getattr(user, "id", None):
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

            result = self._actualizar_profile_data(user_id, datos_update)

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
        roles_validos = ('superadmin', 'admin', 'institucion', 'proveedor', 'client', 'empleado')
        if nuevo_rol not in roles_validos:
            raise ValidationError(
                f"Rol inválido: {nuevo_rol}. Valores válidos: {', '.join(roles_validos)}"
            )

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
            profile_ids = [
                str(data['id'])
                for data in (result.data or [])
                if data.get('id')
            ]
            empresas_map = await self._obtener_resumen_empresas_por_usuarios(profile_ids)

            # Obtener emails de auth.users (un solo request)
            emails_map = {}
            try:
                emails_map = self._emails_map_auth_users()
            except Exception as e:
                logger.warning(f"No se pudieron obtener emails de auth.users: {e}")

            # Convertir a resumen con datos enriquecidos
            resumenes = []
            for data in result.data:
                profile = UserProfile(**data)
                resumen_empresas = empresas_map.get(
                    str(profile.id),
                    {"cantidad_empresas": 0, "empresa_principal": None},
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
                    cantidad_empresas=resumen_empresas["cantidad_empresas"],
                    empresa_principal=resumen_empresas["empresa_principal"],
                )
                resumenes.append(resumen)

            return resumenes

        except Exception as e:
            logger.error(f"Error listando usuarios: {e}")
            raise DatabaseError(f"Error de base de datos: {str(e)}")

    async def _actualizar_ultimo_acceso(self, user_id: UUID) -> None:
        """Actualiza el timestamp de último acceso."""
        try:
            self._actualizar_profile_data(
                user_id,
                {'ultimo_acceso': datetime.now().isoformat()},
            )
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

            return [
                self._construir_resumen_empresa_usuario(data)
                for data in (result.data or [])
            ]

        except Exception as e:
            logger.error(f"Error obteniendo empresas de usuario {user_id}: {e}")
            raise DatabaseError(f"Error de base de datos: {str(e)}")

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
            if rol_empresa:
                datos['rol_empresa'] = rol_empresa

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
            result = self._actualizar_relacion_user_company(
                user_id,
                empresa_id,
                {'es_principal': True},
            )

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
            return self._obtener_relacion_user_company(
                user_id,
                empresa_id,
                select='id',
            ) is not None

        except Exception as e:
            logger.error(f"Error verificando acceso: {e}")
            return False

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
        from app.core.enums import RolEmpresa

        # Validar que el rol sea válido
        roles_validos = [r.value for r in RolEmpresa]
        if rol_empresa not in roles_validos:
            raise ValidationError(
                f"Rol de empresa inválido: {rol_empresa}. "
                f"Valores válidos: {', '.join(roles_validos)}"
            )

        # Verificar que la relación existe
        try:
            relacion = self._obtener_relacion_user_company(
                user_id,
                empresa_id,
                select='id',
            )
            if not relacion:
                raise NotFoundError(
                    f"El usuario {user_id} no tiene asignada la empresa {empresa_id}"
                )

            # Actualizar rol
            result = self._actualizar_relacion_user_company(
                user_id,
                empresa_id,
                {'rol_empresa': rol_empresa},
            )

            if not result.data:
                raise DatabaseError("No se pudo actualizar el rol de empresa")

            logger.info(
                f"Rol '{rol_empresa}' asignado a usuario {user_id} "
                f"en empresa {empresa_id}"
            )
            return UserCompany(**result.data[0])

        except (NotFoundError, ValidationError):
            raise
        except Exception as e:
            logger.error(f"Error asignando rol de empresa: {e}")
            raise DatabaseError(f"Error de base de datos: {str(e)}")

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
        try:
            relacion = self._obtener_relacion_user_company(
                user_id,
                empresa_id,
                select='rol_empresa',
            )
            if not relacion:
                return False

            rol_actual = relacion.get('rol_empresa', 'lectura')
            return rol_actual in roles_requeridos

        except Exception as e:
            logger.error(f"Error verificando permiso de empresa: {e}")
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
            result = self._query_profile()\
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


    # =========================================================================
    # GESTIÓN DE USUARIOS POR EMPRESA (portal admin_empresa)
    # =========================================================================

    def _generar_password_temporal(self) -> str:
        """Genera una contraseña temporal segura de 16 caracteres."""
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
        try:
            result = self.supabase_admin.table(self.tabla_companies)\
                .select('*')\
                .eq('empresa_id', empresa_id)\
                .execute()

            rows = result.data or []
            user_ids = [
                str(row.get('user_id'))
                for row in rows
                if row.get('user_id')
            ]

            perfiles_map: dict[str, dict] = {}
            if user_ids:
                perfiles_map = self._obtener_profiles_map(
                    user_ids,
                    select='id, nombre_completo, telefono, activo, permisos',
                )

            emails_map = {}
            try:
                emails_map = self._emails_map_auth_users()
            except Exception as e:
                logger.warning(f"No se pudieron obtener emails de auth.users: {e}")

            usuarios = []
            for row in rows:
                user_id = str(row.get('user_id', ''))
                perfil = perfiles_map.get(user_id, {})
                if not perfil:
                    logger.warning(
                        "Usuario %s asignado a empresa %s sin perfil cargado en listado portal",
                        user_id,
                        empresa_id,
                    )
                usuarios.append({
                    'user_id': user_id,
                    'email': emails_map.get(user_id, ''),
                    'nombre_completo': perfil.get('nombre_completo', ''),
                    'telefono': perfil.get('telefono', ''),
                    'rol_empresa': row.get('rol_empresa', 'lectura'),
                    'permisos': perfil.get('permisos') or {},
                    'activo_empresa': row.get('activo', True),
                    'activo_perfil': perfil.get('activo', True),
                    'es_principal': row.get('es_principal', False),
                    'created_at': str(
                        row.get('created_at')
                        or row.get('fecha_creacion')
                        or ''
                    ),
                })

            # Ordenar por nombre
            usuarios.sort(key=lambda u: (u.get('nombre_completo') or '').lower())
            return usuarios

        except Exception as e:
            logger.error(f"Error listando usuarios de empresa {empresa_id}: {e}")
            raise DatabaseError(f"Error de base de datos: {str(e)}")

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
        from app.core.constants.permisos import PERMISOS_DEFAULT

        if not self.supabase_admin:
            raise BusinessRuleError(
                "No se puede crear usuarios: SUPABASE_SERVICE_KEY no configurada"
            )

        # Buscar si el email ya existe en auth.users
        try:
            auth_user = self._buscar_auth_user_por_email(email)
            perfil_data = None
            if auth_user and getattr(auth_user, "id", None):
                perfil_data = self._obtener_profile_data(
                    UUID(str(auth_user.id)),
                    select='id, rol, activo, nombre_completo',
                )
        except Exception as e:
            raise DatabaseError(f"Error buscando usuario: {str(e)}")

        if not perfil_data:
            # --- CASO 1: Usuario nuevo ---
            password_temporal = self._generar_password_temporal()
            perfil = await self.crear_usuario(
                datos=UserProfileCreate(
                    email=email.strip().lower(),
                    password=password_temporal,
                    nombre_completo=nombre_completo.strip(),
                    telefono=telefono.strip() if telefono else "",
                    rol='proveedor',
                    permisos=permisos or dict(PERMISOS_DEFAULT),
                ),
                asignaciones_empresas=[
                    UserCompanyAsignacionInicial(
                        empresa_id=empresa_id,
                        rol_empresa=rol_empresa,
                        es_principal=True,
                    )
                ],
            )
            logger.info(
                f"Usuario nuevo creado: {email} para empresa {empresa_id} "
                f"por actor {actor_user_id}"
            )
            return {
                'user_id': str(perfil.id),
                'email': perfil.email,
                'nombre_completo': perfil.nombre_completo,
                'rol_empresa': rol_empresa,
                'es_nuevo': True,
            }

        else:
            # --- CASO 2/3: Usuario existente ---
            rol_existente = perfil_data.get('rol', '')
            user_id = UUID(perfil_data['id'])

            # Roles que NO pueden ser gestionados por admin_empresa
            roles_no_gestionables = {'admin', 'superadmin', 'institucion', 'empleado'}
            if rol_existente in roles_no_gestionables:
                raise BusinessRuleError(
                    "No se pudo agregar el usuario. "
                    "El email ingresado no está disponible para esta operación."
                )

            # Verificar que el usuario no tenga ya asignación en esta empresa
            try:
                asignacion_existente = self._obtener_relacion_user_company(
                    user_id,
                    empresa_id,
                    select='id',
                )
            except Exception as e:
                raise DatabaseError(f"Error verificando asignación: {str(e)}")

            if asignacion_existente:
                raise DuplicateError(
                    f"El usuario {email} ya tiene acceso a esta empresa.",
                    field="email",
                    value=email,
                )

            # Vincular: asignar empresa + actualizar permisos
            await self.asignar_empresa(
                user_id=user_id,
                empresa_id=empresa_id,
                es_principal=False,
                rol_empresa=rol_empresa,
            )

            # Actualizar permisos en el perfil global
            if permisos:
                self._actualizar_profile_data(user_id, {'permisos': permisos})

            logger.info(
                f"Usuario existente {email} vinculado a empresa {empresa_id} "
                f"por actor {actor_user_id}"
            )
            return {
                'user_id': str(user_id),
                'email': email,
                'nombre_completo': perfil_data.get('nombre_completo', nombre_completo),
                'rol_empresa': rol_empresa,
                'es_nuevo': False,
            }

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
        try:
            # Leer estado actual
            relacion = self._obtener_relacion_user_company(
                user_id,
                empresa_id,
                select='activo',
            )
            if not relacion:
                raise NotFoundError(
                    f"El usuario {user_id} no tiene asignada la empresa {empresa_id}"
                )

            estado_actual = relacion.get('activo', True)
            nuevo_estado = not estado_actual

            # Actualizar
            self._actualizar_relacion_user_company(
                user_id,
                empresa_id,
                {'activo': nuevo_estado},
            )

            logger.info(
                f"Usuario {user_id} en empresa {empresa_id}: "
                f"activo={nuevo_estado}"
            )
            return nuevo_estado

        except NotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error alternando activo en empresa: {e}")
            raise DatabaseError(f"Error de base de datos: {str(e)}")


# =============================================================================
# SINGLETON
# =============================================================================

user_service = UserService()
