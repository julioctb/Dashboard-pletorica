"""Subservicio de perfiles de usuario."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Optional, TYPE_CHECKING
from uuid import UUID

from app.core.exceptions import BusinessRuleError, DatabaseError, NotFoundError, ValidationError
from app.entities.user_profile import UserProfile, UserProfileResumen, UserProfileUpdate

if TYPE_CHECKING:
    from app.services.user_service import UserService


logger = logging.getLogger(__name__)


class UserProfileService:
    """Gestiona consultas y mutaciones de user_profiles."""

    def __init__(self, root: "UserService"):
        self.root = root

    async def obtener_por_id(self, user_id: UUID) -> UserProfile:
        try:
            data = self.root._obtener_profile_data(user_id)
            if not data:
                raise NotFoundError(f"Usuario con ID {user_id} no encontrado")
            return UserProfile(**data)
        except NotFoundError:
            raise
        except Exception as exc:
            logger.error("Error obteniendo usuario %s: %s", user_id, exc)
            raise DatabaseError(f"Error de base de datos: {exc}")

    async def obtener_por_email(self, email: str) -> Optional[UserProfile]:
        if not self.root.supabase_admin:
            logger.warning("No se puede buscar por email sin service_role key")
            return None

        try:
            user = self.root._buscar_auth_user_por_email(email)
            if user and getattr(user, "id", None):
                return await self.obtener_por_id(UUID(user.id))
            return None
        except Exception as exc:
            logger.error("Error buscando usuario por email %s: %s", email, exc)
            return None

    async def actualizar_perfil(
        self,
        user_id: UUID,
        datos: UserProfileUpdate,
    ) -> UserProfile:
        await self.obtener_por_id(user_id)

        try:
            datos_update = datos.model_dump(mode="json", exclude_none=True)
            if not datos_update:
                return await self.obtener_por_id(user_id)

            result = self.root._actualizar_profile_data(user_id, datos_update)
            if not result.data:
                raise DatabaseError("No se pudo actualizar el perfil")

            logger.info("Perfil actualizado: %s", user_id)
            return UserProfile(**result.data[0])
        except NotFoundError:
            raise
        except Exception as exc:
            logger.error("Error actualizando perfil %s: %s", user_id, exc)
            raise DatabaseError(f"Error de base de datos: {exc}")

    async def cambiar_rol(self, user_id: UUID, nuevo_rol: str) -> UserProfile:
        roles_validos = ("superadmin", "admin", "institucion", "proveedor", "client", "empleado")
        if nuevo_rol not in roles_validos:
            raise ValidationError(
                f"Rol inválido: {nuevo_rol}. Valores válidos: {', '.join(roles_validos)}"
            )

        return await self.actualizar_perfil(user_id, UserProfileUpdate(rol=nuevo_rol))

    async def desactivar_usuario(self, user_id: UUID) -> UserProfile:
        profile = await self.obtener_por_id(user_id)
        if not profile.activo:
            raise BusinessRuleError("El usuario ya está desactivado")
        return await self.actualizar_perfil(user_id, UserProfileUpdate(activo=False))

    async def activar_usuario(self, user_id: UUID) -> UserProfile:
        profile = await self.obtener_por_id(user_id)
        if profile.activo:
            raise BusinessRuleError("El usuario ya está activo")
        return await self.actualizar_perfil(user_id, UserProfileUpdate(activo=True))

    async def listar_usuarios(
        self,
        incluir_inactivos: bool = False,
        rol: Optional[str] = None,
        limite: int = 50,
        offset: int = 0,
    ) -> list[UserProfileResumen]:
        try:
            query = self.root.supabase_admin.table(self.root.tabla_profiles).select("*")

            if not incluir_inactivos:
                query = query.eq("activo", True)

            if rol:
                query = query.eq("rol", rol)

            result = (
                query.order("fecha_creacion", desc=True)
                .range(offset, offset + limite - 1)
                .execute()
            )
            profile_ids = [str(data["id"]) for data in (result.data or []) if data.get("id")]
            empresas_map = await self.root._obtener_resumen_empresas_por_usuarios(profile_ids)

            emails_map = {}
            try:
                emails_map = self.root._emails_map_auth_users()
            except Exception as exc:
                logger.warning("No se pudieron obtener emails de auth.users: %s", exc)

            resumenes = []
            for data in result.data or []:
                profile = UserProfile(**data)
                resumen_empresas = empresas_map.get(
                    str(profile.id),
                    {"cantidad_empresas": 0, "empresa_principal": None},
                )

                resumenes.append(
                    UserProfileResumen(
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
                )

            return resumenes
        except Exception as exc:
            logger.error("Error listando usuarios: %s", exc)
            raise DatabaseError(f"Error de base de datos: {exc}")

    async def actualizar_ultimo_acceso(self, user_id: UUID) -> None:
        try:
            self.root._actualizar_profile_data(
                user_id,
                {"ultimo_acceso": datetime.now().isoformat()},
            )
        except Exception as exc:
            logger.warning("Error actualizando último acceso: %s", exc)

    async def validar_super_admin(self, user_id: UUID) -> None:
        profile = await self.obtener_por_id(user_id)
        if not profile.puede_gestionar_usuarios:
            raise BusinessRuleError("No tiene permiso para gestionar usuarios")

    async def validar_permiso(self, user_id: UUID, modulo: str, accion: str) -> None:
        profile = await self.obtener_por_id(user_id)
        if not profile.permisos.get(modulo, {}).get(accion, False):
            raise BusinessRuleError(f"No tiene permiso para {accion} en {modulo}")

    async def obtener_usuarios_con_permiso(
        self,
        modulo: str,
        accion: str,
    ) -> list[UserProfile]:
        try:
            result = self.root._query_profile().eq("activo", True).execute()
            usuarios_con_permiso = []
            for data in result.data or []:
                profile = UserProfile(**data)
                if profile.permisos.get(modulo, {}).get(accion, False):
                    usuarios_con_permiso.append(profile)
            return usuarios_con_permiso
        except Exception as exc:
            logger.error(
                "Error obteniendo usuarios con permiso %s:%s: %s",
                modulo,
                accion,
                exc,
            )
            raise DatabaseError(f"Error de base de datos: {exc}")
