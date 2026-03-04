"""
State para la pagina Usuarios Empresa del portal.
Solo accesible para admin_empresa.
Permite gestionar el equipo de su propia empresa: crear, editar rol/permisos, desactivar.
"""
from typing import List
from uuid import UUID

import reflex as rx

from app.core.constants.permisos import PERMISOS_DEFAULT, ROLES_ASIGNABLES_POR_ADMIN_EMPRESA
from app.core.exceptions import DatabaseError, DuplicateError, BusinessRuleError, NotFoundError
from app.presentation.portal.state.portal_state import PortalState
from app.presentation.pages.admin.usuarios.usuarios_validators import (
    validar_email,
    validar_nombre_completo,
    validar_telefono,
)
from app.services import user_service


class UsuariosEmpresaState(PortalState):
    """State para la gestion de usuarios de la empresa desde el portal."""

    # ========================
    # LISTA DE USUARIOS
    # ========================
    usuarios_empresa: List[dict] = []
    filtro_busqueda_usr: str = ""
    filtro_rol_usr: str = ""

    # ========================
    # MODAL CREAR
    # ========================
    mostrar_modal_crear: bool = False
    form_email: str = ""
    form_nombre: str = ""
    form_telefono: str = ""
    form_rol_empresa: str = "lectura"
    form_permisos: dict = {
        "requisiciones": {"operar": False, "autorizar": False},
        "entregables": {"operar": False, "autorizar": False},
        "pagos": {"operar": False, "autorizar": False},
        "contratos": {"operar": False, "autorizar": False},
        "empresas": {"operar": False, "autorizar": False},
        "empleados": {"operar": False, "autorizar": False},
    }
    error_email: str = ""
    error_nombre: str = ""
    error_telefono: str = ""

    # ========================
    # MODAL EDITAR
    # ========================
    mostrar_modal_editar: bool = False
    edit_user_id: str = ""
    edit_nombre_display: str = ""
    edit_email_display: str = ""
    edit_rol_empresa: str = ""
    edit_permisos: dict = {
        "requisiciones": {"operar": False, "autorizar": False},
        "entregables": {"operar": False, "autorizar": False},
        "pagos": {"operar": False, "autorizar": False},
        "contratos": {"operar": False, "autorizar": False},
        "empresas": {"operar": False, "autorizar": False},
        "empleados": {"operar": False, "autorizar": False},
    }

    # ========================
    # MODAL DESACTIVAR
    # ========================
    mostrar_modal_desactivar: bool = False
    usuario_desactivar: dict = {}

    # ========================
    # UI
    # ========================
    saving: bool = False

    # ========================
    # SETTERS — filtros
    # ========================
    def set_filtro_busqueda_usr(self, value: str):
        self.filtro_busqueda_usr = value

    def set_filtro_rol_usr(self, value: str):
        self.filtro_rol_usr = "" if value == "all" else value

    # ========================
    # SETTERS — crear
    # ========================
    def set_form_email(self, value: str):
        self.form_email = value.strip().lower()
        self.error_email = ""

    def set_form_nombre(self, value: str):
        self.form_nombre = value
        self.error_nombre = ""

    def set_form_telefono(self, value: str):
        self.form_telefono = value
        self.error_telefono = ""

    def set_form_rol_empresa(self, value: str):
        self.form_rol_empresa = value

    # ========================
    # SETTERS — editar
    # ========================
    def set_edit_rol_empresa(self, value: str):
        self.edit_rol_empresa = value

    # ========================
    # VALIDADORES ON_BLUR
    # ========================
    def validar_email_campo(self):
        self.error_email = validar_email(self.form_email)

    def validar_nombre_campo(self):
        self.error_nombre = validar_nombre_completo(self.form_nombre)

    def validar_telefono_campo(self):
        self.error_telefono = validar_telefono(self.form_telefono)

    # ========================
    # TOGGLE DE PERMISOS
    # ========================
    def toggle_permiso(self, modulo: str, accion: str):
        """Alterna un permiso en el formulario de creación."""
        permisos = {k: dict(v) for k, v in self.form_permisos.items()}
        if modulo in permisos and accion in permisos[modulo]:
            permisos[modulo][accion] = not permisos[modulo][accion]
        self.form_permisos = permisos

    def toggle_permiso_editar(self, modulo: str, accion: str):
        """Alterna un permiso en el formulario de edición."""
        permisos = {k: dict(v) for k, v in self.edit_permisos.items()}
        if modulo in permisos and accion in permisos[modulo]:
            permisos[modulo][accion] = not permisos[modulo][accion]
        self.edit_permisos = permisos

    # ========================
    # COMPUTED VARS
    # ========================
    @rx.var
    def usuarios_filtrados(self) -> List[dict]:
        """Filtra usuarios en memoria por búsqueda y rol."""
        usuarios = self.usuarios_empresa
        termino = self.filtro_busqueda_usr.lower().strip()
        if termino:
            usuarios = [
                u for u in usuarios
                if termino in (u.get('nombre_completo') or '').lower()
                or termino in (u.get('email') or '').lower()
            ]
        if self.filtro_rol_usr:
            usuarios = [
                u for u in usuarios
                if u.get('rol_empresa') == self.filtro_rol_usr
            ]
        return usuarios

    @rx.var
    def total_filtrados(self) -> int:
        return len(self.usuarios_filtrados)

    @rx.var
    def opciones_roles(self) -> List[dict]:
        return ROLES_ASIGNABLES_POR_ADMIN_EMPRESA

    @rx.var
    def nombre_usuario_desactivar(self) -> str:
        return str(self.usuario_desactivar.get('nombre_completo', '') or '')

    @rx.var
    def activo_usuario_desactivar(self) -> bool:
        return bool(self.usuario_desactivar.get('activo_empresa', True))

    @rx.var
    def filtro_rol_select(self) -> str:
        return self.filtro_rol_usr if self.filtro_rol_usr else "all"

    # ========================
    # MONTAJE
    # ========================
    async def on_mount_usuarios_empresa(self):
        resultado = await self.on_mount_portal()
        if resultado:
            self.loading = False
            yield resultado
            return
        if not self.es_admin_empresa:
            yield rx.redirect("/portal")
            return
        async for _ in self._montar_pagina(self._fetch_usuarios):
            yield

    # ========================
    # CARGA DE DATOS
    # ========================
    async def _fetch_usuarios(self):
        """Carga los usuarios de la empresa (sin manejo de loading)."""
        if not self.id_empresa_actual:
            return
        try:
            usuarios = await user_service.listar_usuarios_empresa(
                empresa_id=self.id_empresa_actual,
            )
            self.usuarios_empresa = self.excluir_usuario_actual(
                usuarios,
                id_field="user_id",
            )
        except DatabaseError as e:
            self.mostrar_mensaje(f"Error cargando usuarios: {e}", "error")
            self.usuarios_empresa = []
        except Exception as e:
            self.mostrar_mensaje(f"Error inesperado: {e}", "error")
            self.usuarios_empresa = []

    async def recargar_usuarios(self):
        """Recarga la lista de usuarios."""
        async for _ in self._recargar_datos(self._fetch_usuarios):
            yield

    # ========================
    # MODAL CREAR
    # ========================
    def abrir_modal_crear(self):
        self._limpiar_form_crear()
        self.mostrar_modal_crear = True

    def cerrar_modal_crear(self):
        self.mostrar_modal_crear = False
        self._limpiar_form_crear()

    def _limpiar_form_crear(self):
        self.form_email = ""
        self.form_nombre = ""
        self.form_telefono = ""
        self.form_rol_empresa = "lectura"
        self.form_permisos = dict(PERMISOS_DEFAULT)
        self.error_email = ""
        self.error_nombre = ""
        self.error_telefono = ""

    async def crear_usuario(self):
        """Crea o vincula un usuario a la empresa del portal."""
        # Validar formulario
        self.error_email = validar_email(self.form_email)
        self.error_nombre = validar_nombre_completo(self.form_nombre)
        self.error_telefono = validar_telefono(self.form_telefono)
        if self.error_email or self.error_nombre or self.error_telefono:
            return rx.toast.error("Por favor corrija los errores del formulario")

        if not self.id_empresa_actual:
            return rx.toast.error("No hay empresa seleccionada")

        actor_id = None
        if self.id_usuario:
            try:
                actor_id = UUID(str(self.id_usuario))
            except ValueError:
                pass

        self.saving = True
        try:
            resultado = await user_service.crear_o_vincular_usuario_empresa(
                email=self.form_email,
                nombre_completo=self.form_nombre,
                empresa_id=self.id_empresa_actual,
                rol_empresa=self.form_rol_empresa,
                permisos=dict(self.form_permisos),
                telefono=self.form_telefono,
                actor_user_id=actor_id,
            )
            self.cerrar_modal_crear()
            await self._fetch_usuarios()
            if resultado.get('es_nuevo'):
                return rx.toast.success(
                    f"Usuario {resultado['email']} creado y vinculado a la empresa."
                )
            return rx.toast.success(
                f"Usuario {resultado['email']} vinculado correctamente a la empresa."
            )
        except DuplicateError as e:
            self.error_email = "Este usuario ya tiene acceso a esta empresa."
            return rx.toast.error(str(e))
        except BusinessRuleError as e:
            return rx.toast.error(str(e))
        except Exception as e:
            return self.manejar_error_con_toast(e, "creando usuario")
        finally:
            self.saving = False

    # ========================
    # MODAL EDITAR
    # ========================
    def abrir_modal_editar(self, usuario: dict):
        """Abre el modal de edición con los datos del usuario."""
        if not usuario:
            return
        self.edit_user_id = str(usuario.get('user_id', ''))
        self.edit_email_display = str(usuario.get('email', ''))
        self.edit_nombre_display = str(usuario.get('nombre_completo', ''))
        self.edit_rol_empresa = str(usuario.get('rol_empresa', 'lectura'))
        # Cargar permisos existentes (o defaults si no tiene)
        permisos_raw = usuario.get('permisos') or {}
        self.edit_permisos = self._merge_permisos(permisos_raw)
        self.mostrar_modal_editar = True

    def cerrar_modal_editar(self):
        self.mostrar_modal_editar = False
        self.edit_user_id = ""
        self.edit_email_display = ""
        self.edit_nombre_display = ""
        self.edit_rol_empresa = ""
        self.edit_permisos = dict(PERMISOS_DEFAULT)

    def _merge_permisos(self, permisos_existentes: dict) -> dict:
        """Fusiona permisos existentes con los defaults (para módulos faltantes)."""
        merged = {k: dict(v) for k, v in PERMISOS_DEFAULT.items()}
        for modulo, acciones in permisos_existentes.items():
            if modulo in merged and isinstance(acciones, dict):
                merged[modulo].update({
                    k: bool(v) for k, v in acciones.items()
                    if k in merged[modulo]
                })
        return merged

    async def guardar_edicion(self):
        """Guarda los cambios de rol y permisos del usuario."""
        if not self.edit_user_id or not self.id_empresa_actual:
            return rx.toast.error("Error: datos incompletos")

        self.saving = True
        try:
            user_id = UUID(self.edit_user_id)
            # Actualizar rol en user_companies
            await user_service.asignar_rol_empresa(
                user_id=user_id,
                empresa_id=self.id_empresa_actual,
                rol_empresa=self.edit_rol_empresa,
            )
            # Actualizar permisos en user_profiles
            from app.entities import UserProfileUpdate
            await user_service.actualizar_perfil(
                user_id=user_id,
                datos=UserProfileUpdate(permisos=dict(self.edit_permisos)),
            )
            self.cerrar_modal_editar()
            await self._fetch_usuarios()
            return rx.toast.success("Cambios guardados correctamente.")
        except NotFoundError:
            return rx.toast.error("Usuario no encontrado en esta empresa.")
        except Exception as e:
            return self.manejar_error_con_toast(e, "guardando cambios")
        finally:
            self.saving = False

    # ========================
    # MODAL DESACTIVAR
    # ========================
    def abrir_modal_desactivar(self, usuario: dict):
        if not usuario:
            return
        self.usuario_desactivar = usuario
        self.mostrar_modal_desactivar = True

    def cerrar_modal_desactivar(self):
        self.mostrar_modal_desactivar = False
        self.usuario_desactivar = {}

    async def confirmar_toggle_activo(self):
        """Activa o desactiva al usuario en la empresa."""
        usr = self.usuario_desactivar
        if not usr or not self.id_empresa_actual:
            yield rx.toast.error("Error: datos incompletos")
            return

        self.saving = True
        try:
            user_id = UUID(str(usr.get('user_id', '')))
            nuevo_estado = await user_service.toggle_activo_en_empresa(
                user_id=user_id,
                empresa_id=self.id_empresa_actual,
            )
            self.cerrar_modal_desactivar()
            await self._fetch_usuarios()
            if nuevo_estado:
                yield rx.toast.success(f"Usuario reactivado correctamente.")
            else:
                yield rx.toast.success(f"Usuario desactivado correctamente.")
        except NotFoundError:
            yield rx.toast.error("Usuario no encontrado en esta empresa.")
        except Exception as e:
            yield self.manejar_error_con_toast(e, "cambiando estado del usuario")
        finally:
            self.saving = False
