"""State de Mi Perfil (cuenta personal) reutilizable para backoffice y portal."""
import logging
from typing import Optional
from uuid import UUID

import reflex as rx
from pydantic import ValidationError as PydanticValidationError

from app.presentation.components.shared.auth_state import AuthState
from app.services import user_service
from app.entities.user_profile import UserProfileUpdate
from app.core.validation import (
    validar_nombre_completo_usuario,
    validar_telefono_usuario,
    validar_password_usuario,
)

logger = logging.getLogger(__name__)


class MiPerfilState(AuthState):
    """Gestión de la cuenta personal del usuario autenticado."""

    # ========================
    # FORM - CUENTA
    # ========================
    form_nombre_completo: str = ""
    form_telefono: str = ""
    error_nombre_completo: str = ""
    error_telefono: str = ""
    email_actual: str = ""
    guardando_perfil: bool = False

    # ========================
    # FORM - SEGURIDAD
    # ========================
    form_password_nueva: str = ""
    form_password_confirmacion: str = ""
    error_password_nueva: str = ""
    error_password_confirmacion: str = ""
    guardando_password: bool = False

    # ========================
    # SETTERS / HELPERS DE UI
    # ========================
    def set_form_nombre_completo(self, value: str):
        self.form_nombre_completo = value
        self.error_nombre_completo = ""

    def set_form_telefono(self, value: str):
        self.form_telefono = value
        self.error_telefono = ""

    def set_form_password_nueva(self, value: str):
        self.form_password_nueva = value
        self.error_password_nueva = ""

    def set_form_password_confirmacion(self, value: str):
        self.form_password_confirmacion = value
        self.error_password_confirmacion = ""

    def _limpiar_errores_perfil(self):
        self.limpiar_errores_campos(["nombre_completo", "telefono"])

    def _limpiar_errores_password(self):
        self.limpiar_errores_campos(["error_password_nueva", "error_password_confirmacion"])

    def _cargar_formulario_desde_usuario(self):
        self.form_nombre_completo = str(self.usuario_actual.get("nombre_completo", "") or "")
        self.form_telefono = str(self.usuario_actual.get("telefono", "") or "")
        self.email_actual = str(self.usuario_actual.get("email", "") or "")

    async def _asegurar_email_actual(self):
        """Intenta completar el email desde token si no viene en user_profiles."""
        if not self._access_token:
            return

        try:
            await self._enriquecer_email_usuario_desde_token()
            self.email_actual = str(self.usuario_actual.get("email", "") or "")
        except Exception as e:
            logger.debug("No se pudo obtener email en Mi Perfil: %s", e)

    # ========================
    # COMPUTED VARS
    # ========================
    @rx.var
    def rol_plataforma_label(self) -> str:
        rol = str(self.usuario_actual.get("rol", "") or "")
        labels = {
            "superadmin": "Super Admin",
            "admin": "Admin",
            "institucion": "Institución",
            "proveedor": "Proveedor",
            "client": "Proveedor",
            "empleado": "Empleado",
        }
        return labels.get(rol, rol.title() if rol else "Sin rol")

    @rx.var
    def contexto_cuenta_label(self) -> str:
        if self.es_institucion and self.institucion_actual:
            nombre_inst = self.institucion_actual.get("nombre")
            if self.empresa_actual and self.empresa_actual.get("empresa_nombre"):
                return f"{nombre_inst} · {self.empresa_actual.get('empresa_nombre')}"
            return str(nombre_inst or "Institución asignada")

        if self.empresa_actual:
            return str(self.empresa_actual.get("empresa_nombre", "Empresa asignada"))

        return "Sin contexto asignado"

    @rx.var
    def puede_guardar_perfil(self) -> bool:
        return (
            bool(self.form_nombre_completo.strip())
            and not self.error_nombre_completo
            and not self.error_telefono
            and not self.guardando_perfil
        )

    @rx.var
    def puede_cambiar_password(self) -> bool:
        return (
            bool(self.form_password_nueva)
            and bool(self.form_password_confirmacion)
            and not self.error_password_nueva
            and not self.error_password_confirmacion
            and not self.guardando_password
        )

    # ========================
    # MONTAJE
    # ========================
    async def on_mount_mi_perfil(self):
        async for _ in self._montar_pagina_auth(self._fetch_mi_perfil):
            yield

    async def _fetch_mi_perfil(self):
        self._limpiar_errores_perfil()
        self._limpiar_errores_password()
        await self._asegurar_email_actual()
        self._cargar_formulario_desde_usuario()

    # ========================
    # VALIDACIONES
    # ========================
    def _validar_form_perfil(self) -> Optional[UserProfileUpdate]:
        self._limpiar_errores_perfil()

        es_valido = self.validar_lote_campos([
            ("error_nombre_completo", self.form_nombre_completo, validar_nombre_completo_usuario),
            ("error_telefono", self.form_telefono, validar_telefono_usuario),
        ])
        if not es_valido:
            return None

        try:
            payload = UserProfileUpdate(
                nombre_completo=self.form_nombre_completo,
                telefono=(self.form_telefono or None),
            )
            return payload
        except PydanticValidationError as e:
            self.aplicar_errores_validacion(
                e,
                fallback_attr="error_nombre_completo",
            )
            if not self.error_nombre_completo and not self.error_telefono:
                self.error_nombre_completo = "Revise los datos capturados"
            return None

    def _validar_form_password(self) -> bool:
        self._limpiar_errores_password()

        error_password = validar_password_usuario(self.form_password_nueva)
        if error_password == "La contrasena es requerida":
            self.error_password_nueva = "Capture una nueva contraseña"
        elif error_password:
            self.error_password_nueva = "La contraseña debe tener al menos 8 caracteres"

        if not self.form_password_confirmacion:
            self.error_password_confirmacion = "Confirme la nueva contraseña"
        elif self.form_password_nueva != self.form_password_confirmacion:
            self.error_password_confirmacion = "Las contraseñas no coinciden"

        return not self.error_password_nueva and not self.error_password_confirmacion

    # ========================
    # ACCIONES
    # ========================
    async def guardar_perfil(self):
        payload = self._validar_form_perfil()
        if not payload:
            return rx.toast.error(
                "Revise los campos del formulario",
                position="top-center",
            )

        if not self.id_usuario:
            return rx.toast.error("Sesión inválida", position="top-center")

        self.guardando_perfil = True
        try:
            actualizado = await user_service.actualizar_perfil(UUID(self.id_usuario), payload)
            email_actual = self.usuario_actual.get("email", self.email_actual)
            self.usuario_actual = {
                **actualizado.model_dump(mode="json"),
                "email": email_actual,
            }
            self._cargar_formulario_desde_usuario()
            return rx.toast.success("Perfil actualizado", position="top-center")
        except Exception as e:
            return self.manejar_error_con_toast(e, "al actualizar perfil")
        finally:
            self.guardando_perfil = False

    async def cambiar_password(self):
        if not self._validar_form_password():
            return rx.toast.error(
                "Revise la contraseña capturada",
                position="top-center",
            )

        self.guardando_password = True
        try:
            await user_service.cambiar_password_usuario_autenticado(
                access_token=self._access_token,
                refresh_token=self._refresh_token,
                nueva_password=self.form_password_nueva,
            )
            self.form_password_nueva = ""
            self.form_password_confirmacion = ""
            self._limpiar_errores_password()
            return rx.toast.success("Contraseña actualizada", position="top-center")
        except Exception as e:
            return self.manejar_error_con_toast(e, "al cambiar contraseña")
        finally:
            self.guardando_password = False
