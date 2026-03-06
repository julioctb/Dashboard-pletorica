"""Subservicio de empresas asignadas a usuarios."""

from __future__ import annotations

import logging
from typing import Optional, TYPE_CHECKING
from uuid import UUID

from app.core.exceptions import BusinessRuleError, DatabaseError, DuplicateError, NotFoundError, ValidationError
from app.entities.user_company import UserCompany, UserCompanyAsignacionInicial, UserCompanyResumen
from app.entities.user_profile import UserProfileCreate

if TYPE_CHECKING:
    from app.services.user_service import UserService


logger = logging.getLogger(__name__)


class UserCompanyService:
    """Encapsula asignaciones usuario-empresa y portal admin_empresa."""

    def __init__(self, root: "UserService"):
        self.root = root

    async def obtener_empresas_usuario(self, user_id: UUID) -> list[UserCompanyResumen]:
        try:
            result = (
                self.root.supabase_admin.table(self.root.tabla_companies)
                .select("*, empresas(nombre_comercial, rfc, tipo_empresa, estatus)")
                .eq("user_id", str(user_id))
                .order("es_principal", desc=True)
                .execute()
            )
            return [
                self.root._construir_resumen_empresa_usuario(data)
                for data in (result.data or [])
            ]
        except Exception as exc:
            logger.error("Error obteniendo empresas de usuario %s: %s", user_id, exc)
            raise DatabaseError(f"Error de base de datos: {exc}")

    async def asignar_empresa(
        self,
        user_id: UUID,
        empresa_id: int,
        es_principal: bool = False,
        rol_empresa: Optional[str] = None,
    ) -> UserCompany:
        await self.root.obtener_por_id(user_id)
        await self._validar_empresa_existe(empresa_id)

        try:
            if es_principal:
                await self._quitar_principal_actual(user_id)

            datos = {
                "user_id": str(user_id),
                "empresa_id": empresa_id,
                "es_principal": es_principal,
            }
            if rol_empresa:
                datos["rol_empresa"] = rol_empresa

            result = self.root.supabase_admin.table(self.root.tabla_companies).insert(datos).execute()
            if not result.data:
                raise DatabaseError("No se pudo asignar la empresa")

            logger.info("Empresa %s asignada a usuario %s", empresa_id, user_id)
            return UserCompany(**result.data[0])
        except Exception as exc:
            error_msg = str(exc).lower()
            if "duplicate" in error_msg or "unique" in error_msg:
                raise DuplicateError(
                    f"El usuario ya tiene asignada la empresa {empresa_id}",
                    field="empresa_id",
                    value=str(empresa_id),
                )
            logger.error("Error asignando empresa: %s", exc)
            raise DatabaseError(f"Error de base de datos: {exc}")

    async def quitar_empresa(self, user_id: UUID, empresa_id: int) -> bool:
        empresas = await self.obtener_empresas_usuario(user_id)
        relacion = next((e for e in empresas if e.empresa_id == empresa_id), None)
        if not relacion:
            raise NotFoundError(f"El usuario no tiene asignada la empresa {empresa_id}")

        try:
            (
                self.root.supabase_admin.table(self.root.tabla_companies)
                .delete()
                .eq("user_id", str(user_id))
                .eq("empresa_id", empresa_id)
                .execute()
            )

            if relacion.es_principal and len(empresas) > 1:
                otra_empresa = next(e for e in empresas if e.empresa_id != empresa_id)
                await self.cambiar_empresa_principal(user_id, otra_empresa.empresa_id)

            logger.info("Empresa %s removida de usuario %s", empresa_id, user_id)
            return True
        except Exception as exc:
            logger.error("Error removiendo empresa: %s", exc)
            raise DatabaseError(f"Error de base de datos: {exc}")

    async def cambiar_empresa_principal(
        self,
        user_id: UUID,
        empresa_id: int,
    ) -> UserCompany:
        empresas = await self.obtener_empresas_usuario(user_id)
        relacion = next((e for e in empresas if e.empresa_id == empresa_id), None)
        if not relacion:
            raise NotFoundError(f"El usuario no tiene asignada la empresa {empresa_id}")

        try:
            await self._quitar_principal_actual(user_id)
            result = self.root._actualizar_relacion_user_company(
                user_id,
                empresa_id,
                {"es_principal": True},
            )
            if not result.data:
                raise DatabaseError("No se pudo cambiar la empresa principal")

            logger.info("Empresa principal de %s cambiada a %s", user_id, empresa_id)
            return UserCompany(**result.data[0])
        except NotFoundError:
            raise
        except Exception as exc:
            logger.error("Error cambiando empresa principal: %s", exc)
            raise DatabaseError(f"Error de base de datos: {exc}")

    async def quitar_principal_actual(self, user_id: UUID) -> None:
        try:
            (
                self.root.supabase_admin.table(self.root.tabla_companies)
                .update({"es_principal": False})
                .eq("user_id", str(user_id))
                .eq("es_principal", True)
                .execute()
            )
        except Exception as exc:
            logger.warning("Error quitando principal actual: %s", exc)

    async def validar_empresa_existe(self, empresa_id: int) -> None:
        from app.services import empresa_service

        try:
            empresa = await empresa_service.obtener_por_id(empresa_id)
            if not empresa.esta_activa():
                raise BusinessRuleError(f"La empresa {empresa_id} no está activa")
        except NotFoundError:
            raise NotFoundError(f"Empresa con ID {empresa_id} no encontrada")

    async def usuario_tiene_acceso_empresa(self, user_id: UUID, empresa_id: int) -> bool:
        try:
            return (
                self.root._obtener_relacion_user_company(
                    user_id,
                    empresa_id,
                    select="id",
                )
                is not None
            )
        except Exception as exc:
            logger.error("Error verificando acceso: %s", exc)
            return False

    async def asignar_rol_empresa(
        self,
        user_id: UUID,
        empresa_id: int,
        rol_empresa: str,
    ) -> UserCompany:
        from app.core.enums import RolEmpresa

        roles_validos = [r.value for r in RolEmpresa]
        if rol_empresa not in roles_validos:
            raise ValidationError(
                f"Rol de empresa inválido: {rol_empresa}. "
                f"Valores válidos: {', '.join(roles_validos)}"
            )

        try:
            relacion = self.root._obtener_relacion_user_company(
                user_id,
                empresa_id,
                select="id",
            )
            if not relacion:
                raise NotFoundError(
                    f"El usuario {user_id} no tiene asignada la empresa {empresa_id}"
                )

            result = self.root._actualizar_relacion_user_company(
                user_id,
                empresa_id,
                {"rol_empresa": rol_empresa},
            )
            if not result.data:
                raise DatabaseError("No se pudo actualizar el rol de empresa")

            logger.info(
                "Rol '%s' asignado a usuario %s en empresa %s",
                rol_empresa,
                user_id,
                empresa_id,
            )
            return UserCompany(**result.data[0])
        except (NotFoundError, ValidationError):
            raise
        except Exception as exc:
            logger.error("Error asignando rol de empresa: %s", exc)
            raise DatabaseError(f"Error de base de datos: {exc}")

    async def verificar_permiso_empresa(
        self,
        user_id: UUID,
        empresa_id: int,
        roles_requeridos: list[str],
    ) -> bool:
        try:
            relacion = self.root._obtener_relacion_user_company(
                user_id,
                empresa_id,
                select="rol_empresa",
            )
            if not relacion:
                return False

            return relacion.get("rol_empresa", "lectura") in roles_requeridos
        except Exception as exc:
            logger.error("Error verificando permiso de empresa: %s", exc)
            return False

    async def obtener_empresa_principal(
        self,
        user_id: UUID,
    ) -> Optional[UserCompanyResumen]:
        empresas = await self.obtener_empresas_usuario(user_id)
        return next((e for e in empresas if e.es_principal), empresas[0] if empresas else None)

    async def listar_usuarios_empresa(self, empresa_id: int) -> list[dict]:
        try:
            result = (
                self.root.supabase_admin.table(self.root.tabla_companies)
                .select("*")
                .eq("empresa_id", empresa_id)
                .execute()
            )
            rows = result.data or []
            user_ids = [str(row.get("user_id")) for row in rows if row.get("user_id")]

            perfiles_map = {}
            if user_ids:
                perfiles_map = self.root._obtener_profiles_map(
                    user_ids,
                    select="id, nombre_completo, telefono, activo, permisos",
                )

            emails_map = {}
            try:
                emails_map = self.root._emails_map_auth_users()
            except Exception as exc:
                logger.warning("No se pudieron obtener emails de auth.users: %s", exc)

            usuarios = []
            for row in rows:
                user_id = str(row.get("user_id", ""))
                perfil = perfiles_map.get(user_id, {})
                if not perfil:
                    logger.warning(
                        "Usuario %s asignado a empresa %s sin perfil cargado en listado portal",
                        user_id,
                        empresa_id,
                    )
                usuarios.append(
                    {
                        "user_id": user_id,
                        "email": emails_map.get(user_id, ""),
                        "nombre_completo": perfil.get("nombre_completo", ""),
                        "telefono": perfil.get("telefono", ""),
                        "rol_empresa": row.get("rol_empresa", "lectura"),
                        "permisos": perfil.get("permisos") or {},
                        "activo_empresa": row.get("activo", True),
                        "activo_perfil": perfil.get("activo", True),
                        "es_principal": row.get("es_principal", False),
                        "created_at": str(row.get("created_at") or row.get("fecha_creacion") or ""),
                    }
                )

            usuarios.sort(key=lambda u: (u.get("nombre_completo") or "").lower())
            return usuarios
        except Exception as exc:
            logger.error("Error listando usuarios de empresa %s: %s", empresa_id, exc)
            raise DatabaseError(f"Error de base de datos: {exc}")

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
        from app.core.constants.permisos import PERMISOS_DEFAULT

        if not self.root.supabase_admin:
            raise BusinessRuleError(
                "No se puede crear usuarios: SUPABASE_SERVICE_KEY no configurada"
            )

        try:
            auth_user = self.root._buscar_auth_user_por_email(email)
            perfil_data = None
            if auth_user and getattr(auth_user, "id", None):
                perfil_data = self.root._obtener_profile_data(
                    UUID(str(auth_user.id)),
                    select="id, rol, activo, nombre_completo",
                )
        except Exception as exc:
            raise DatabaseError(f"Error buscando usuario: {exc}")

        if not perfil_data:
            password_temporal = self.root._generar_password_temporal()
            perfil = await self.root.crear_usuario(
                datos=UserProfileCreate(
                    email=email.strip().lower(),
                    password=password_temporal,
                    nombre_completo=nombre_completo.strip(),
                    telefono=telefono.strip() if telefono else "",
                    rol="proveedor",
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
                "Usuario nuevo creado: %s para empresa %s por actor %s",
                email,
                empresa_id,
                actor_user_id,
            )
            return {
                "user_id": str(perfil.id),
                "email": perfil.email,
                "nombre_completo": perfil.nombre_completo,
                "rol_empresa": rol_empresa,
                "es_nuevo": True,
            }

        rol_existente = perfil_data.get("rol", "")
        user_id = UUID(perfil_data["id"])

        roles_no_gestionables = {"admin", "superadmin", "institucion", "empleado"}
        if rol_existente in roles_no_gestionables:
            raise BusinessRuleError(
                "No se pudo agregar el usuario. "
                "El email ingresado no está disponible para esta operación."
            )

        try:
            asignacion_existente = self.root._obtener_relacion_user_company(
                user_id,
                empresa_id,
                select="id",
            )
        except Exception as exc:
            raise DatabaseError(f"Error verificando asignación: {exc}")

        if asignacion_existente:
            raise DuplicateError(
                f"El usuario {email} ya tiene acceso a esta empresa.",
                field="email",
                value=email,
            )

        await self.root.asignar_empresa(
            user_id=user_id,
            empresa_id=empresa_id,
            es_principal=False,
            rol_empresa=rol_empresa,
        )

        if permisos:
            self.root._actualizar_profile_data(user_id, {"permisos": permisos})

        logger.info(
            "Usuario existente %s vinculado a empresa %s por actor %s",
            email,
            empresa_id,
            actor_user_id,
        )
        return {
            "user_id": str(user_id),
            "email": email,
            "nombre_completo": perfil_data.get("nombre_completo", nombre_completo),
            "rol_empresa": rol_empresa,
            "es_nuevo": False,
        }

    async def toggle_activo_en_empresa(self, user_id: UUID, empresa_id: int) -> bool:
        try:
            relacion = self.root._obtener_relacion_user_company(
                user_id,
                empresa_id,
                select="activo",
            )
            if not relacion:
                raise NotFoundError(
                    f"El usuario {user_id} no tiene asignada la empresa {empresa_id}"
                )

            nuevo_estado = not relacion.get("activo", True)
            self.root._actualizar_relacion_user_company(
                user_id,
                empresa_id,
                {"activo": nuevo_estado},
            )

            logger.info(
                "Usuario %s en empresa %s: activo=%s",
                user_id,
                empresa_id,
                nuevo_estado,
            )
            return nuevo_estado
        except NotFoundError:
            raise
        except Exception as exc:
            logger.error("Error alternando activo en empresa: %s", exc)
            raise DatabaseError(f"Error de base de datos: {exc}")

    async def _quitar_principal_actual(self, user_id: UUID) -> None:
        await self.quitar_principal_actual(user_id)

    async def _validar_empresa_existe(self, empresa_id: int) -> None:
        await self.validar_empresa_existe(empresa_id)
