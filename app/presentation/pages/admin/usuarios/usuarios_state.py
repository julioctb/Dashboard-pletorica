"""
Estado de Reflex para el modulo de gestion de usuarios (admin).
Maneja el estado de la UI, CRUD de usuarios, y gestion de empresas asignadas.
"""
import reflex as rx
from typing import List, Optional
from uuid import UUID

from app.entities import UserProfileCreate, UserProfileUpdate
from app.services import user_service, empresa_service
from app.presentation.components.shared.auth_state import AuthState
from app.presentation.pages.admin.usuarios.usuarios_validators import (
    validar_email,
    validar_password,
    validar_nombre_completo,
    validar_telefono,
)


# Campos con sus valores por defecto para limpiar formulario
FORM_DEFAULTS_CREAR = {
    "email": "",
    "password": "",
    "nombre_completo": "",
    "telefono": "",
    "rol": "client",
}

FORM_DEFAULTS_EDITAR = {
    "edit_nombre_completo": "",
    "edit_telefono": "",
    "edit_rol": "",
}

# Permisos default (todo desactivado)
PERMISOS_DEFAULT = {
    "requisiciones": {"operar": False, "autorizar": False},
    "entregables": {"operar": False, "autorizar": False},
    "pagos": {"operar": False, "autorizar": False},
    "contratos": {"operar": False, "autorizar": False},
    "empresas": {"operar": False, "autorizar": False},
    "empleados": {"operar": False, "autorizar": False},
}

# Módulos que tienen flujo de autorización
MODULOS_CON_AUTORIZACION = {"requisiciones", "entregables", "pagos"}


class UsuariosAdminState(AuthState):
    """Estado para el modulo de gestion de usuarios."""

    # ========================
    # ESTADO DE DATOS
    # ========================
    usuarios: List[dict] = []
    usuario_seleccionado: Optional[dict] = None
    total_usuarios: int = 0

    # Empresas del usuario seleccionado (modal gestionar empresas)
    empresas_usuario: List[dict] = []
    # Todas las empresas activas para asignar
    todas_empresas: List[dict] = []

    # ========================
    # ESTADO DE UI
    # ========================
    mostrar_modal_crear: bool = False
    mostrar_modal_editar: bool = False
    mostrar_modal_empresas: bool = False
    mostrar_modal_confirmar_desactivar: bool = False

    # Filtros
    filtro_rol: str = ""
    incluir_inactivos: bool = False

    # ========================
    # FORMULARIO CREAR USUARIO
    # ========================
    form_email: str = ""
    form_password: str = ""
    form_nombre_completo: str = ""
    form_telefono: str = ""
    form_rol: str = "client"

    # Errores crear
    error_email: str = ""
    error_password: str = ""
    error_nombre_completo: str = ""
    error_telefono: str = ""

    # ========================
    # FORMULARIO EDITAR USUARIO
    # ========================
    form_edit_nombre_completo: str = ""
    form_edit_telefono: str = ""
    form_edit_rol: str = ""

    # Errores editar
    error_edit_nombre_completo: str = ""
    error_edit_telefono: str = ""

    # ========================
    # FORMULARIO PERMISOS (crear y editar)
    # ========================
    form_permisos: dict = {
        "requisiciones": {"operar": False, "autorizar": False},
        "entregables": {"operar": False, "autorizar": False},
        "pagos": {"operar": False, "autorizar": False},
        "contratos": {"operar": False, "autorizar": False},
        "empresas": {"operar": False, "autorizar": False},
        "empleados": {"operar": False, "autorizar": False},
    }
    form_puede_gestionar_usuarios: bool = False

    # ========================
    # FORMULARIO ASIGNAR EMPRESA
    # ========================
    form_empresa_id: str = ""

    # ========================
    # SETTERS EXPLICITOS (Reflex 0.8.21)
    # ========================

    # --- Filtros ---
    def set_filtro_rol(self, value: str):
        self.filtro_rol = value

    def set_filtro_rol_select(self, value: str):
        """Setter para el select de rol (mapea 'all' -> '')."""
        self.filtro_rol = "" if value == "all" else value

    @rx.var
    def filtro_rol_select(self) -> str:
        """Valor para el select de rol (mapea '' -> 'all')."""
        return self.filtro_rol if self.filtro_rol else "all"

    def set_incluir_inactivos(self, value: bool):
        self.incluir_inactivos = value

    # --- Crear ---
    def set_form_email(self, value: str):
        self.form_email = value.strip().lower()
        self.error_email = ""

    def set_form_password(self, value: str):
        self.form_password = value
        self.error_password = ""

    def set_form_nombre_completo(self, value: str):
        self.form_nombre_completo = value
        self.error_nombre_completo = ""

    def set_form_telefono(self, value: str):
        self.form_telefono = value
        self.error_telefono = ""

    def set_form_rol(self, value: str):
        self.form_rol = value

    # --- Editar ---
    def set_form_edit_nombre_completo(self, value: str):
        self.form_edit_nombre_completo = value
        self.error_edit_nombre_completo = ""

    def set_form_edit_telefono(self, value: str):
        self.form_edit_telefono = value
        self.error_edit_telefono = ""

    def set_form_edit_rol(self, value: str):
        self.form_edit_rol = value

    # --- Modales ---
    def set_mostrar_modal_crear(self, value: bool):
        self.mostrar_modal_crear = value

    def set_mostrar_modal_editar(self, value: bool):
        self.mostrar_modal_editar = value

    def set_mostrar_modal_empresas(self, value: bool):
        self.mostrar_modal_empresas = value

    def set_mostrar_modal_confirmar_desactivar(self, value: bool):
        self.mostrar_modal_confirmar_desactivar = value

    # --- Permisos ---
    def set_form_puede_gestionar_usuarios(self, value: bool):
        self.form_puede_gestionar_usuarios = value

    def toggle_permiso(self, modulo: str, accion: str):
        """Toggle un permiso específico en la matriz."""
        permisos = dict(self.form_permisos)
        modulo_permisos = dict(permisos.get(modulo, {"operar": False, "autorizar": False}))
        modulo_permisos[accion] = not modulo_permisos.get(accion, False)
        permisos[modulo] = modulo_permisos
        self.form_permisos = permisos

    # --- Asignar empresa ---
    def set_form_empresa_id(self, value):
        self.form_empresa_id = str(value) if value else ""

    # ========================
    # VALIDACION
    # ========================
    def validar_crear(self) -> bool:
        """Valida formulario de crear. Retorna True si hay errores."""
        self.error_email = validar_email(self.form_email)
        self.error_password = validar_password(self.form_password)
        self.error_nombre_completo = validar_nombre_completo(self.form_nombre_completo)
        self.error_telefono = validar_telefono(self.form_telefono)
        return bool(
            self.error_email
            or self.error_password
            or self.error_nombre_completo
            or self.error_telefono
        )

    def validar_editar(self) -> bool:
        """Valida formulario de editar. Retorna True si hay errores."""
        self.error_edit_nombre_completo = validar_nombre_completo(self.form_edit_nombre_completo)
        self.error_edit_telefono = validar_telefono(self.form_edit_telefono)
        return bool(
            self.error_edit_nombre_completo
            or self.error_edit_telefono
        )

    # --- Validacion on_blur ---
    def validar_email_campo(self):
        self.error_email = validar_email(self.form_email)

    def validar_password_campo(self):
        self.error_password = validar_password(self.form_password)

    def validar_nombre_campo(self):
        self.error_nombre_completo = validar_nombre_completo(self.form_nombre_completo)

    def validar_telefono_campo(self):
        self.error_telefono = validar_telefono(self.form_telefono)

    def validar_edit_nombre_campo(self):
        self.error_edit_nombre_completo = validar_nombre_completo(self.form_edit_nombre_completo)

    def validar_edit_telefono_campo(self):
        self.error_edit_telefono = validar_telefono(self.form_edit_telefono)

    # ========================
    # PROPIEDADES CALCULADAS
    # ========================
    @rx.var
    def puede_crear(self) -> bool:
        tiene_datos = bool(
            self.form_email
            and self.form_password
            and self.form_nombre_completo
            and self.form_rol
        )
        sin_errores = not bool(
            self.error_email
            or self.error_password
            or self.error_nombre_completo
            or self.error_telefono
        )
        return tiene_datos and sin_errores and not self.saving

    @rx.var
    def puede_editar(self) -> bool:
        tiene_datos = bool(self.form_edit_nombre_completo and self.form_edit_rol)
        sin_errores = not bool(
            self.error_edit_nombre_completo or self.error_edit_telefono
        )
        return tiene_datos and sin_errores and not self.saving

    @rx.var
    def mostrar_permisos(self) -> bool:
        """Solo mostrar matriz de permisos cuando el rol es admin."""
        return self.form_rol == "admin"

    @rx.var
    def mostrar_edit_permisos(self) -> bool:
        """Solo mostrar matriz de permisos cuando el rol es admin."""
        return self.form_edit_rol == "admin"

    @rx.var
    def opciones_empresas_disponibles(self) -> List[dict]:
        """Empresas que se pueden asignar (no asignadas al usuario)."""
        ids_asignadas = {str(e.get("empresa_id")) for e in self.empresas_usuario}
        return [
            e for e in self.todas_empresas
            if e.get("id") not in ids_asignadas
        ]

    # ========================
    # ON_MOUNT
    # ========================
    async def on_mount_admin(self):
        """Se ejecuta al montar la pagina."""
        # Verificar autenticacion
        resultado = await self.verificar_y_redirigir()
        if resultado:
            return resultado

        # Verificar que es super admin (puede gestionar usuarios)
        if not self.es_super_admin:
            return rx.redirect("/")

        # Cargar datos (manual loading por auth return pattern)
        self.loading = True
        await self._fetch_usuarios()
        await self._cargar_todas_empresas()
        self.loading = False

    # ========================
    # OPERACIONES DE LECTURA
    # ========================
    async def _fetch_usuarios(self):
        """Carga usuarios desde BD (sin manejo de loading)."""
        try:
            usuarios = await user_service.listar_usuarios(
                incluir_inactivos=self.incluir_inactivos,
                rol=self.filtro_rol or None,
            )
            self.usuarios = [u.model_dump(mode='json') for u in usuarios]
            self.total_usuarios = len(self.usuarios)
        except Exception as e:
            self.manejar_error(e, "al cargar usuarios")
            self.usuarios = []
            self.total_usuarios = 0

    async def cargar_usuarios(self):
        """Carga usuarios con skeleton loading (público)."""
        async for _ in self.recargar_datos(self._fetch_usuarios):
            yield

    async def _cargar_todas_empresas(self):
        """Carga todas las empresas activas para selects de asignacion."""
        try:
            empresas = await empresa_service.obtener_todas(incluir_inactivas=False)
            self.todas_empresas = [
                {
                    "id": str(e.id),
                    "nombre_comercial": e.nombre_comercial,
                    "rfc": e.rfc,
                }
                for e in empresas
            ]
        except Exception:
            self.todas_empresas = []

    async def _cargar_empresas_usuario(self, user_id: str):
        """Carga las empresas asignadas a un usuario."""
        try:
            empresas = await user_service.obtener_empresas_usuario(UUID(user_id))
            self.empresas_usuario = [e.model_dump(mode='json') for e in empresas]
        except Exception:
            self.empresas_usuario = []

    async def aplicar_filtros(self):
        """Aplica filtros y recarga la lista."""
        async for _ in self.recargar_datos(self._fetch_usuarios):
            yield

    # ========================
    # CRUD - CREAR
    # ========================
    def abrir_modal_crear(self):
        """Abre modal de crear usuario."""
        self._limpiar_form_crear()
        self.mostrar_modal_crear = True

    def cerrar_modal_crear(self):
        self.mostrar_modal_crear = False
        self._limpiar_form_crear()

    async def crear_usuario(self):
        """Crea un nuevo usuario."""
        if self.validar_crear():
            return

        self.saving = True
        try:
            # Preparar permisos solo para admins
            permisos = self.form_permisos if self.form_rol == "admin" else PERMISOS_DEFAULT
            puede_gestionar = self.form_puede_gestionar_usuarios if self.form_rol == "admin" else False

            datos = UserProfileCreate(
                email=self.form_email,
                password=self.form_password,
                nombre_completo=self.form_nombre_completo.strip(),
                rol=self.form_rol,
                telefono=self.form_telefono.strip() if self.form_telefono.strip() else None,
                permisos=permisos,
                puede_gestionar_usuarios=puede_gestionar,
            )

            await user_service.crear_usuario(datos)

            self.cerrar_modal_crear()
            await self._fetch_usuarios()

            return rx.toast.success(
                f"Usuario '{datos.nombre_completo}' creado exitosamente",
                position="top-center",
                duration=3000,
            )

        except Exception as e:
            self.manejar_error(
                e,
                "al crear usuario",
                campo_duplicado="error_email",
                valor_duplicado=self.form_email,
            )
        finally:
            self.saving = False

    # ========================
    # CRUD - EDITAR
    # ========================
    def abrir_modal_editar(self, usuario: dict):
        """Abre modal de editar usuario."""
        self._limpiar_form_editar()
        self.usuario_seleccionado = usuario
        self.form_edit_nombre_completo = usuario.get("nombre_completo", "")
        self.form_edit_telefono = usuario.get("telefono", "") or ""
        self.form_edit_rol = usuario.get("rol", "client")
        # Cargar permisos del usuario
        self.form_permisos = usuario.get("permisos", dict(PERMISOS_DEFAULT))
        self.form_puede_gestionar_usuarios = usuario.get("puede_gestionar_usuarios", False)
        self.mostrar_modal_editar = True

    def cerrar_modal_editar(self):
        self.mostrar_modal_editar = False
        self._limpiar_form_editar()
        self.usuario_seleccionado = None

    async def editar_usuario(self):
        """Actualiza un usuario existente."""
        if self.validar_editar():
            return
        if not self.usuario_seleccionado:
            return

        user_id = UUID(str(self.usuario_seleccionado["id"]))

        # Preparar permisos solo para admins
        permisos = self.form_permisos if self.form_edit_rol == "admin" else PERMISOS_DEFAULT
        puede_gestionar = self.form_puede_gestionar_usuarios if self.form_edit_rol == "admin" else False

        datos = UserProfileUpdate(
            nombre_completo=self.form_edit_nombre_completo.strip(),
            telefono=self.form_edit_telefono.strip() if self.form_edit_telefono.strip() else None,
            rol=self.form_edit_rol,
            permisos=permisos,
            puede_gestionar_usuarios=puede_gestionar,
        )

        async def _on_exito():
            self.cerrar_modal_editar()
            await self._fetch_usuarios()

        return await self.ejecutar_guardado(
            operacion=lambda: user_service.actualizar_perfil(user_id, datos),
            mensaje_exito="Usuario actualizado exitosamente",
            on_exito=_on_exito,
        )

    # ========================
    # ACTIVAR / DESACTIVAR
    # ========================
    def confirmar_desactivar(self, usuario: dict):
        """Abre modal de confirmacion para desactivar."""
        # No puede desactivarse a si mismo
        if str(usuario.get("id", "")) == self.id_usuario:
            return rx.toast.error(
                "No puedes desactivar tu propia cuenta",
                position="top-center",
            )
        self.usuario_seleccionado = usuario
        self.mostrar_modal_confirmar_desactivar = True

    def cerrar_confirmar_desactivar(self):
        self.mostrar_modal_confirmar_desactivar = False
        self.usuario_seleccionado = None

    async def desactivar_usuario_accion(self):
        """Desactiva el usuario seleccionado."""
        if not self.usuario_seleccionado:
            return

        user_id = UUID(str(self.usuario_seleccionado["id"]))
        nombre = self.usuario_seleccionado.get("nombre_completo", "")

        async def _on_exito():
            self.cerrar_confirmar_desactivar()
            await self._fetch_usuarios()

        return await self.ejecutar_guardado(
            operacion=lambda: user_service.desactivar_usuario(user_id),
            mensaje_exito=f"Usuario '{nombre}' desactivado",
            on_exito=_on_exito,
        )

    async def activar_usuario_accion(self, user_id: str):
        """Activa un usuario inactivo."""
        return await self.ejecutar_guardado(
            operacion=lambda: user_service.activar_usuario(UUID(user_id)),
            mensaje_exito="Usuario activado",
            on_exito=self._fetch_usuarios,
        )

    # ========================
    # GESTION DE EMPRESAS
    # ========================
    async def abrir_modal_empresas(self, usuario: dict):
        """Abre modal de gestion de empresas del usuario."""
        self.usuario_seleccionado = usuario
        self.form_empresa_id = ""
        await self._cargar_empresas_usuario(str(usuario["id"]))
        await self._cargar_todas_empresas()
        self.mostrar_modal_empresas = True

    def cerrar_modal_empresas(self):
        self.mostrar_modal_empresas = False
        self.usuario_seleccionado = None
        self.empresas_usuario = []
        self.form_empresa_id = ""

    async def asignar_empresa(self):
        """Asigna una empresa al usuario seleccionado."""
        if not self.usuario_seleccionado or not self.form_empresa_id:
            return

        user_id = UUID(str(self.usuario_seleccionado["id"]))
        empresa_id = self.parse_id(self.form_empresa_id)
        es_principal = len(self.empresas_usuario) == 0

        async def _on_exito():
            await self._cargar_empresas_usuario(str(self.usuario_seleccionado["id"]))
            self.form_empresa_id = ""
            await self._fetch_usuarios()

        return await self.ejecutar_guardado(
            operacion=lambda: user_service.asignar_empresa(user_id, empresa_id, es_principal),
            mensaje_exito="Empresa asignada",
            on_exito=_on_exito,
        )

    async def quitar_empresa(self, empresa_id: int):
        """Quita una empresa del usuario seleccionado."""
        if not self.usuario_seleccionado:
            return

        user_id = UUID(str(self.usuario_seleccionado["id"]))

        async def _on_exito():
            await self._cargar_empresas_usuario(str(self.usuario_seleccionado["id"]))
            await self._fetch_usuarios()

        return await self.ejecutar_guardado(
            operacion=lambda: user_service.quitar_empresa(user_id, empresa_id),
            mensaje_exito="Empresa removida",
            on_exito=_on_exito,
        )

    async def hacer_principal(self, empresa_id: int):
        """Cambia la empresa principal del usuario."""
        if not self.usuario_seleccionado:
            return

        user_id = UUID(str(self.usuario_seleccionado["id"]))

        async def _on_exito():
            await self._cargar_empresas_usuario(str(self.usuario_seleccionado["id"]))

        return await self.ejecutar_guardado(
            operacion=lambda: user_service.cambiar_empresa_principal(user_id, empresa_id),
            mensaje_exito="Empresa principal actualizada",
            on_exito=_on_exito,
        )

    # ========================
    # HELPERS PRIVADOS
    # ========================
    def _limpiar_form_crear(self):
        for campo, default in FORM_DEFAULTS_CREAR.items():
            setattr(self, f"form_{campo}", default)
        self.error_email = ""
        self.error_password = ""
        self.error_nombre_completo = ""
        self.error_telefono = ""
        self.form_permisos = dict(PERMISOS_DEFAULT)
        self.form_puede_gestionar_usuarios = False

    def _limpiar_form_editar(self):
        for campo, default in FORM_DEFAULTS_EDITAR.items():
            setattr(self, f"form_{campo}", default)
        self.error_edit_nombre_completo = ""
        self.error_edit_telefono = ""
        self.form_permisos = dict(PERMISOS_DEFAULT)
        self.form_puede_gestionar_usuarios = False
