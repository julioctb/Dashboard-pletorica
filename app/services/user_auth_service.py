"""Subservicio de autenticacion para usuarios."""

from __future__ import annotations

import asyncio
import logging
from typing import Optional, TYPE_CHECKING
from uuid import UUID

from supabase import create_client

from app.core.config import Config
from app.core.exceptions import BusinessRuleError, DatabaseError, DuplicateError, ValidationError
from app.core.validation import validar_password_usuario
from app.entities.user_company import UserCompanyAsignacionInicial
from app.entities.user_profile import UserProfile, UserProfileCreate

if TYPE_CHECKING:
    from app.services.user_service import UserService


logger = logging.getLogger(__name__)


class UserAuthService:
    """Encapsula autenticacion y altas en Supabase Auth."""

    def __init__(self, root: "UserService"):
        self.root = root

    async def crear_usuario(
        self,
        datos: UserProfileCreate,
        empresas_ids: Optional[list[int]] = None,
        empresa_principal_id: Optional[int] = None,
        asignaciones_empresas: Optional[list[UserCompanyAsignacionInicial]] = None,
    ) -> UserProfile:
        if not self.root.supabase_admin:
            raise BusinessRuleError(
                "No se puede crear usuarios: SUPABASE_SERVICE_KEY no configurada"
            )

        rol_plataforma = datos.rol if isinstance(datos.rol, str) else datos.rol.value

        if asignaciones_empresas is None and empresas_ids:
            asignaciones_empresas = [
                UserCompanyAsignacionInicial(
                    empresa_id=empresa_id,
                    es_principal=(empresa_id == empresa_principal_id) if empresa_principal_id else False,
                )
                for empresa_id in empresas_ids
            ]

        if empresa_principal_id and empresas_ids and empresa_principal_id not in empresas_ids:
            raise ValidationError(
                "La empresa principal debe estar en la lista de empresas asignadas"
            )

        if rol_plataforma == "institucion" and asignaciones_empresas:
            raise ValidationError(
                "Los usuarios institucionales no usan asignaciones de empresa (user_companies)"
            )

        if rol_plataforma in ("proveedor", "client") and not asignaciones_empresas:
            raise ValidationError(
                "Los usuarios proveedor requieren al menos una empresa asignada"
            )

        if rol_plataforma in ("admin", "superadmin", "empleado") and asignaciones_empresas:
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
            response = self.root.supabase_admin.auth.admin.create_user(
                {
                    "email": datos.email,
                    "password": datos.password,
                    "email_confirm": True,
                    "user_metadata": datos.to_auth_metadata(),
                }
            )

            if not response.user:
                raise DatabaseError("Error al crear usuario en Supabase Auth")

            user_id = UUID(response.user.id)
            logger.info("Usuario creado en Auth: %s", user_id)

            await asyncio.sleep(0.5)

            profile = await self.root.obtener_por_id(user_id)

            if datos.permisos or datos.puede_gestionar_usuarios:
                permisos_update = {}
                if datos.permisos:
                    permisos_update["permisos"] = datos.permisos
                if datos.puede_gestionar_usuarios:
                    permisos_update["puede_gestionar_usuarios"] = datos.puede_gestionar_usuarios
                if permisos_update:
                    self.root._actualizar_profile_data(user_id, permisos_update)
                    profile = await self.root.obtener_por_id(user_id)

            if datos.institucion_id:
                self.root._actualizar_profile_data(
                    user_id,
                    {"institucion_id": datos.institucion_id},
                )
                profile = await self.root.obtener_por_id(user_id)

            if asignaciones_empresas:
                for asignacion in asignaciones_empresas:
                    try:
                        await self.root.asignar_empresa(
                            user_id=user_id,
                            empresa_id=asignacion.empresa_id,
                            es_principal=asignacion.es_principal,
                            rol_empresa=(
                                asignacion.rol_empresa
                                if isinstance(asignacion.rol_empresa, str)
                                else asignacion.rol_empresa.value
                            ),
                        )
                    except Exception as exc:
                        logger.warning(
                            "Error asignando empresa %s a usuario %s: %s",
                            asignacion.empresa_id,
                            user_id,
                            exc,
                        )

            return profile
        except Exception as exc:
            error_msg = str(exc).lower()
            if "already registered" in error_msg or "already exists" in error_msg:
                raise DuplicateError(
                    f"El email {datos.email} ya está registrado",
                    field="email",
                    value=datos.email,
                )
            logger.error("Error creando usuario: %s", exc)
            raise DatabaseError(f"Error al crear usuario: {exc}")

    async def login(self, email: str, password: str):
        try:
            response = self.root.supabase.auth.sign_in_with_password(
                {
                    "email": email.strip().lower(),
                    "password": password,
                }
            )

            if not response.user or not response.session:
                raise ValidationError("Credenciales inválidas")

            user_id = UUID(response.user.id)
            profile = await self.root.obtener_por_id(user_id)

            if not profile.activo:
                self.root.supabase.auth.sign_out()
                raise BusinessRuleError(
                    "Tu cuenta está desactivada. Contacta al administrador."
                )

            await self.root._actualizar_ultimo_acceso(user_id)

            return profile, {
                "access_token": response.session.access_token,
                "refresh_token": response.session.refresh_token,
                "expires_at": response.session.expires_at,
                "user_id": str(user_id),
            }
        except ValidationError:
            raise
        except BusinessRuleError:
            raise
        except Exception as exc:
            error_msg = str(exc).lower()
            if "invalid" in error_msg or "credentials" in error_msg:
                raise ValidationError("Email o contraseña incorrectos")
            logger.error("Error en login: %s", exc)
            raise DatabaseError(f"Error de autenticación: {exc}")

    async def logout(self) -> bool:
        try:
            self.root.supabase.auth.sign_out()
            logger.info("Logout exitoso")
            return True
        except Exception as exc:
            logger.warning("Error en logout (no crítico): %s", exc)
            return True

    async def validar_token(self, access_token: str) -> Optional[UserProfile]:
        try:
            response = self.root.supabase.auth.get_user(access_token)
            if not response.user:
                return None

            user_id = UUID(response.user.id)
            profile = await self.root.obtener_por_id(user_id)
            return profile if profile.activo else None
        except Exception as exc:
            logger.debug("Token inválido o expirado: %s", exc)
            return None

    async def obtener_email_desde_token(self, access_token: str) -> Optional[str]:
        if not access_token:
            return None

        try:
            response = self.root.supabase.auth.get_user(access_token)
            user = getattr(response, "user", None)
            email = getattr(user, "email", None) if user else None
            return str(email).strip().lower() if email else None
        except Exception as exc:
            logger.debug("No se pudo resolver email desde token: %s", exc)
            return None

    async def refrescar_token(self, refresh_token: str) -> Optional[dict]:
        try:
            response = self.root.supabase.auth.refresh_session(refresh_token)
            if not response.session:
                return None
            return {
                "access_token": response.session.access_token,
                "refresh_token": response.session.refresh_token,
                "expires_at": response.session.expires_at,
            }
        except Exception as exc:
            logger.debug("Error refrescando token: %s", exc)
            return None

    async def cambiar_password_usuario_autenticado(
        self,
        access_token: str,
        refresh_token: str,
        nueva_password: str,
    ) -> None:
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
            try:
                cliente_auth.auth.set_session(access_token, refresh_token)
            except TypeError:
                cliente_auth.auth.set_session(
                    {
                        "access_token": access_token,
                        "refresh_token": refresh_token,
                    }
                )

            try:
                cliente_auth.auth.update_user({"password": nueva_password})
            except TypeError:
                cliente_auth.auth.update_user(password=nueva_password)

            logger.info("Contraseña actualizada por usuario autenticado")
        except ValidationError:
            raise
        except Exception as exc:
            logger.error("Error cambiando contraseña de usuario autenticado: %s", exc)
            raise DatabaseError(f"Error al cambiar contraseña: {exc}")

    async def resetear_password(self, user_id: UUID, nueva_password: str) -> None:
        if not self.root.supabase_admin:
            raise BusinessRuleError(
                "No se puede resetear: SUPABASE_SERVICE_KEY no configurada"
            )

        try:
            self.root.supabase_admin.auth.admin.update_user_by_id(
                str(user_id),
                {"password": nueva_password},
            )
            logger.info("Contraseña reseteada para usuario %s", user_id)
        except Exception as exc:
            logger.error("Error reseteando contraseña de %s: %s", user_id, exc)
            raise DatabaseError(f"Error al resetear contraseña: {exc}")
