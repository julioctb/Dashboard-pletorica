"""
Estado de Reflex para el modulo de gestion de usuarios.
Maneja el estado de la UI, CRUD de usuarios, y gestion de empresas asignadas.
"""
import reflex as rx
from typing import List, Optional
from uuid import UUID

from app.entities import (
    UserProfileCreate,
    UserProfileUpdate,
    UserCompanyAsignacionInicial,
)
from app.services import user_service, empresa_service, institucion_service
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
    "rol": "proveedor",
    "institucion_id": "",
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

OPCIONES_ROLES_EMPRESA = [
    {"label": "Administrador de Empresa", "value": "admin_empresa"},
    {"label": "RRHH", "value": "rrhh"},
    {"label": "Operaciones", "value": "operaciones"},
    {"label": "Contabilidad", "value": "contabilidad"},
    {"label": "Solo lectura", "value": "lectura"},
]


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
    # Instituciones activas (solo super admin)
    todas_instituciones: List[dict] = []

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
    form_rol: str = "proveedor"
    form_institucion_id: str = ""
    form_asignaciones_empresas: List[dict] = []

    # Errores crear
    error_email: str = ""
    error_password: str = ""
    error_nombre_completo: str = ""
    error_telefono: str = ""
    error_institucion: str = ""
    error_asignaciones: str = ""

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
    # RESET DE CONTRASEÑA (super admin)
    # ========================
    form_reset_password: str = ""
    error_reset_password: str = ""
    mostrar_seccion_reset: bool = False

    # ========================
    # FORMULARIO ASIGNAR EMPRESA (modal gestionar empresas)
    # ========================
    form_empresa_id: str = ""

    # ========================
    # HELPERS INTERNOS
    # ========================
    def _rol_es_proveedor(self, rol: str) -> bool:
        return rol in ("proveedor", "client")

    def _actor_es_superadmin_local(self) -> bool:
        if not self.usuario_actual:
            return False
        return self.usuario_actual.get("rol", "") in ("superadmin", "admin")

    def _actor_es_institucion_local(self) -> bool:
        if not self.usuario_actual:
            return False
        return self.usuario_actual.get("rol", "") == "institucion"

    def _asignacion_default(self, es_principal: bool = False) -> dict:
        return {
            "idx": 0,
            "empresa_id": "",
            "rol_empresa": "admin_empresa",
            "es_principal": es_principal,
        }

    def _normalizar_asignaciones_principal(self):
        if not self.form_asignaciones_empresas:
            return
        asignaciones = [dict(a) for a in self.form_asignaciones_empresas]
        principales = [i for i, a in enumerate(asignaciones) if a.get("es_principal")]
        if len(asignaciones) == 1:
            asignaciones[0]["es_principal"] = True
        elif len(principales) == 0:
            asignaciones[0]["es_principal"] = True
        elif len(principales) > 1:
            principal_idx = principales[0]
            for i, _a in enumerate(asignaciones):
                asignaciones[i]["es_principal"] = (i == principal_idx)
        for i, _a in enumerate(asignaciones):
            asignaciones[i]["idx"] = i
        self.form_asignaciones_empresas = asignaciones

    def _empresa_ids_institucion_actor(self) -> set[int]:
        return {
            int(e.get("empresa_id"))
            for e in (self.empresas_institucion or [])
            if e.get("empresa_id")
        }

    def _rol_matches_filtro(self, rol_usuario: str) -> bool:
        if not self.filtro_rol:
            return True
        if self.filtro_rol == "admin":
            return rol_usuario in ("admin", "superadmin")
        if self.filtro_rol == "proveedor":
            return rol_usuario in ("proveedor", "client")
        return rol_usuario == self.filtro_rol

    async def _usuario_en_alcance_institucional(self, usuario: dict) -> bool:
        """Valida si el usuario objetivo es gestionable por la institución actual."""
        if self._actor_es_superadmin_local():
            return True
        if not self._actor_es_institucion_local():
            return False

        rol_objetivo = str(usuario.get("rol", ""))
        if not self._rol_es_proveedor(rol_objetivo):
            return False

        ids_institucion = self._empresa_ids_institucion_actor()
        if not ids_institucion:
            return False

        ids_usuario = usuario.get("_empresa_ids_asignadas") or []
        if not ids_usuario:
            try:
                empresas = await user_service.obtener_empresas_usuario(UUID(str(usuario["id"])))
                ids_usuario = [int(e.empresa_id) for e in empresas]
            except Exception:
                return False

        return bool(ids_institucion.intersection({int(i) for i in ids_usuario}))

    async def _asegurar_usuario_en_alcance(self, usuario: Optional[dict]) -> Optional[rx.event.EventSpec]:
        if not usuario:
            return rx.toast.error("Usuario no disponible", position="top-center")
        if await self._usuario_en_alcance_institucional(usuario):
            return None
        return rx.toast.error(
            "No tienes permiso para gestionar este usuario",
            position="top-center",
        )

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
        self.error_institucion = ""
        self.error_asignaciones = ""

        if value != "institucion":
            self.form_institucion_id = ""

        if self._rol_es_proveedor(value):
            if not self.form_asignaciones_empresas:
                self.form_asignaciones_empresas = [self._asignacion_default(es_principal=True)]
            self._normalizar_asignaciones_principal()
        else:
            self.form_asignaciones_empresas = []

        if value != "admin":
            self.form_puede_gestionar_usuarios = False
            self.form_permisos = dict(PERMISOS_DEFAULT)

    def set_form_institucion_id(self, value: str):
        self.form_institucion_id = str(value) if value else ""
        self.error_institucion = ""

    def agregar_asignacion_empresa(self):
        asignaciones = [dict(a) for a in self.form_asignaciones_empresas]
        asignaciones.append(self._asignacion_default(es_principal=(len(asignaciones) == 0)))
        self.form_asignaciones_empresas = asignaciones
        self._normalizar_asignaciones_principal()
        self.error_asignaciones = ""

    def quitar_asignacion_empresa(self, index: int):
        asignaciones = [dict(a) for a in self.form_asignaciones_empresas]
        if index < 0 or index >= len(asignaciones):
            return
        asignaciones.pop(index)
        self.form_asignaciones_empresas = asignaciones
        self._normalizar_asignaciones_principal()
        self.error_asignaciones = ""

    def set_asignacion_empresa_id(self, index: int, value: str):
        empresa_id = str(value) if value else ""
        asignaciones = [dict(a) for a in self.form_asignaciones_empresas]
        if index < 0 or index >= len(asignaciones):
            return

        duplicado = any(
            i != index and str(a.get("empresa_id", "")) == empresa_id and empresa_id
            for i, a in enumerate(asignaciones)
        )
        if duplicado:
            self.error_asignaciones = "No se puede repetir la misma empresa en múltiples perfiles"
            return

        asignaciones[index]["empresa_id"] = empresa_id
        self.form_asignaciones_empresas = asignaciones
        self.error_asignaciones = ""

    def set_asignacion_rol_empresa(self, index: int, value: str):
        asignaciones = [dict(a) for a in self.form_asignaciones_empresas]
        if index < 0 or index >= len(asignaciones):
            return
        asignaciones[index]["rol_empresa"] = str(value) if value else "lectura"
        self.form_asignaciones_empresas = asignaciones
        self.error_asignaciones = ""

    def marcar_asignacion_principal(self, index: int):
        asignaciones = [dict(a) for a in self.form_asignaciones_empresas]
        if index < 0 or index >= len(asignaciones):
            return
        for i, _a in enumerate(asignaciones):
            asignaciones[i]["es_principal"] = (i == index)
        self.form_asignaciones_empresas = asignaciones
        self.error_asignaciones = ""

    # --- Editar ---
    def set_form_edit_nombre_completo(self, value: str):
        self.form_edit_nombre_completo = value
        self.error_edit_nombre_completo = ""

    def set_form_edit_telefono(self, value: str):
        self.form_edit_telefono = value
        self.error_edit_telefono = ""

    def set_form_edit_rol(self, value: str):
        # Usuarios institucionales solo pueden mantener proveedor/client
        if self._actor_es_institucion_local() and value not in ("proveedor", "client"):
            self.form_edit_rol = "proveedor"
            return
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
        if self._actor_es_institucion_local():
            self.form_puede_gestionar_usuarios = False
            return
        self.form_puede_gestionar_usuarios = value

    def toggle_permiso(self, modulo: str, accion: str):
        """Toggle un permiso específico en la matriz."""
        permisos = dict(self.form_permisos)
        modulo_permisos = dict(permisos.get(modulo, {"operar": False, "autorizar": False}))
        modulo_permisos[accion] = not modulo_permisos.get(accion, False)
        permisos[modulo] = modulo_permisos
        self.form_permisos = permisos

    # --- Reset contraseña ---
    def set_form_reset_password(self, value: str):
        self.form_reset_password = value
        self.error_reset_password = ""

    def set_mostrar_seccion_reset(self, value: bool):
        self.mostrar_seccion_reset = value
        if not value:
            self.form_reset_password = ""
            self.error_reset_password = ""

    # --- Asignar empresa (modal gestionar empresas) ---
    def set_form_empresa_id(self, value):
        self.form_empresa_id = str(value) if value else ""

    # ========================
    # VALIDACION
    # ========================
    def validar_crear(self) -> bool:
        """Valida formulario de crear. Retorna True si hay errores."""
        self.validar_lote_campos([
            ("error_email", self.form_email, validar_email),
            ("error_password", self.form_password, validar_password),
            ("error_nombre_completo", self.form_nombre_completo, validar_nombre_completo),
            ("error_telefono", self.form_telefono, validar_telefono),
        ])
        self.error_institucion = ""
        # Mantener error actual de duplicados si existe; si no, limpiar antes de revalidar.
        self.error_asignaciones = ""

        if self._actor_es_institucion_local() and self.form_rol != "proveedor":
            self.error_asignaciones = "Los usuarios institucionales solo pueden crear perfiles de proveedor"

        if self.form_rol == "institucion" and not self.form_institucion_id:
            self.error_institucion = "La institución es requerida para perfiles institucionales"

        if self.form_rol != "institucion" and self.form_institucion_id:
            self.error_institucion = ""

        if self._rol_es_proveedor(self.form_rol):
            if not self.form_asignaciones_empresas:
                self.error_asignaciones = "Debe asignar al menos una empresa"
            else:
                self._normalizar_asignaciones_principal()
                ids = []
                principales = 0
                ids_permitidos_institucion = self._empresa_ids_institucion_actor()
                if self._actor_es_institucion_local() and not ids_permitidos_institucion:
                    self.error_asignaciones = "Tu institución no tiene empresas relacionadas disponibles"
                for fila in self.form_asignaciones_empresas:
                    if self.error_asignaciones:
                        break
                    empresa_id = str(fila.get("empresa_id", "")).strip()
                    rol_empresa = str(fila.get("rol_empresa", "")).strip()
                    if not empresa_id:
                        self.error_asignaciones = "Todas las asignaciones deben tener empresa"
                        break
                    if not rol_empresa:
                        self.error_asignaciones = "Todas las asignaciones deben tener rol de empresa"
                        break
                    if empresa_id in ids:
                        self.error_asignaciones = "No se puede repetir la misma empresa en múltiples perfiles"
                        break
                    ids.append(empresa_id)
                    if fila.get("es_principal"):
                        principales += 1
                    if self._actor_es_institucion_local() and ids_permitidos_institucion:
                        if int(empresa_id) not in ids_permitidos_institucion:
                            self.error_asignaciones = (
                                "Solo puedes asignar empresas relacionadas con tu institución"
                            )
                            break
                if not self.error_asignaciones and principales != 1:
                    self.error_asignaciones = "Debe existir exactamente una empresa principal"
        else:
            # Para roles no proveedor no se usan asignaciones iniciales
            self.form_asignaciones_empresas = []

        return bool(
            self.error_email
            or self.error_password
            or self.error_nombre_completo
            or self.error_telefono
            or self.error_institucion
            or self.error_asignaciones
        )

    def validar_editar(self) -> bool:
        """Valida formulario de editar. Retorna True si hay errores."""
        self.validar_lote_campos([
            ("error_edit_nombre_completo", self.form_edit_nombre_completo, validar_nombre_completo),
            ("error_edit_telefono", self.form_edit_telefono, validar_telefono),
        ])
        return bool(
            self.error_edit_nombre_completo
            or self.error_edit_telefono
        )

    # --- Validacion on_blur ---
    def validar_email_campo(self):
        self.validar_y_asignar_error(
            valor=self.form_email,
            validador=validar_email,
            error_attr="error_email",
        )

    def validar_password_campo(self):
        self.validar_y_asignar_error(
            valor=self.form_password,
            validador=validar_password,
            error_attr="error_password",
        )

    def validar_nombre_campo(self):
        self.validar_y_asignar_error(
            valor=self.form_nombre_completo,
            validador=validar_nombre_completo,
            error_attr="error_nombre_completo",
        )

    def validar_telefono_campo(self):
        self.validar_y_asignar_error(
            valor=self.form_telefono,
            validador=validar_telefono,
            error_attr="error_telefono",
        )

    def validar_edit_nombre_campo(self):
        self.validar_y_asignar_error(
            valor=self.form_edit_nombre_completo,
            validador=validar_nombre_completo,
            error_attr="error_edit_nombre_completo",
        )

    def validar_edit_telefono_campo(self):
        self.validar_y_asignar_error(
            valor=self.form_edit_telefono,
            validador=validar_telefono,
            error_attr="error_edit_telefono",
        )

    def validar_reset_password_campo(self):
        self.validar_y_asignar_error(
            valor=self.form_reset_password,
            validador=validar_password,
            error_attr="error_reset_password",
        )

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
        if self.form_rol == "institucion":
            tiene_datos = tiene_datos and bool(self.form_institucion_id)
        if self._rol_es_proveedor(self.form_rol):
            tiene_datos = tiene_datos and self.form_asignaciones_empresas.length() > 0
        sin_errores = not bool(
            self.error_email
            or self.error_password
            or self.error_nombre_completo
            or self.error_telefono
            or self.error_institucion
            or self.error_asignaciones
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
    def mostrar_selector_institucion(self) -> bool:
        return self.form_rol == "institucion"

    @rx.var
    def mostrar_asignaciones_iniciales(self) -> bool:
        return self.form_rol == "proveedor" or self.form_rol == "client"

    @rx.var
    def puede_mostrar_checkbox_superadmin(self) -> bool:
        return self.form_rol == "admin" and not self._actor_es_institucion_local()

    @rx.var
    def opciones_roles_creacion(self) -> List[dict]:
        if self._actor_es_institucion_local():
            return [{"label": "Proveedor (empresa)", "value": "proveedor"}]
        return [
            {"label": "Proveedor (empresa)", "value": "proveedor"},
            {"label": "Perfil institucional (BUAP, etc.)", "value": "institucion"},
            {"label": "Administrador (plataforma)", "value": "admin"},
        ]

    @rx.var
    def opciones_roles_edicion(self) -> List[dict]:
        if self._actor_es_institucion_local():
            return [{"label": "Proveedor (empresa)", "value": "proveedor"}]
        return [
            {"label": "Proveedor (empresa)", "value": "proveedor"},
            {"label": "Perfil institucional (BUAP, etc.)", "value": "institucion"},
            {"label": "Administrador (plataforma)", "value": "admin"},
            {"label": "Cliente (compatibilidad)", "value": "client"},
        ]

    @rx.var
    def opciones_roles_empresa(self) -> List[dict]:
        return OPCIONES_ROLES_EMPRESA

    @rx.var
    def opciones_instituciones(self) -> List[dict]:
        return [
            {
                "label": i.get("nombre", "Institución"),
                "value": str(i.get("id", "")),
            }
            for i in self.todas_instituciones
        ]

    @rx.var
    def opciones_empresas_creacion(self) -> List[dict]:
        if self._actor_es_institucion_local():
            return [
                {
                    "id": str(e.get("empresa_id")),
                    "label": e.get("empresa_nombre", "Empresa"),
                    "rfc": e.get("empresa_rfc", ""),
                }
                for e in self.empresas_institucion
            ]
        return [
            {
                "id": str(e.get("id")),
                "label": e.get("nombre_comercial", "Empresa"),
                "rfc": e.get("rfc", ""),
            }
            for e in self.todas_empresas
        ]

    @rx.var
    def opciones_empresas_disponibles(self) -> List[dict]:
        """Empresas que se pueden asignar (no asignadas al usuario seleccionado)."""
        ids_asignadas = {str(e.get("empresa_id")) for e in self.empresas_usuario}
        if self._actor_es_institucion_local():
            base = [
                {
                    "id": str(e.get("empresa_id")),
                    "nombre_comercial": e.get("empresa_nombre"),
                    "rfc": e.get("empresa_rfc"),
                }
                for e in self.empresas_institucion
            ]
        else:
            base = self.todas_empresas
        return [e for e in base if e.get("id") not in ids_asignadas]

    # ========================
    # ON_MOUNT
    # ========================
    async def on_mount_usuarios(self):
        """Se ejecuta al montar la pagina de gestión de usuarios."""
        auth = await self.get_state(AuthState)
        if not (auth.es_superadmin or auth.es_super_admin or auth.es_institucion):
            self.loading = False
            yield rx.redirect("/")
            return

        async for _ in self._montar_pagina(
            self._fetch_usuarios,
            self._cargar_todas_empresas,
            self._cargar_todas_instituciones,
        ):
            yield

    async def on_mount_admin(self):
        """Compatibilidad: alias anterior del on_mount."""
        async for _ in self.on_mount_usuarios():
            yield

    # ========================
    # OPERACIONES DE LECTURA
    # ========================
    async def _fetch_usuarios(self):
        """Carga usuarios desde BD (sin manejo de loading)."""
        try:
            usuarios = await user_service.listar_usuarios(
                incluir_inactivos=self.incluir_inactivos,
                rol=None,  # filtro local para compatibilidad provider/client
            )
            items = [u.model_dump(mode='json') for u in usuarios]

            # Filtro local por rol (compat provider/client)
            items = [u for u in items if self._rol_matches_filtro(str(u.get("rol", "")))]

            # Ocultar cuenta propia de la gestión de usuarios (Mi Perfil va aparte)
            if self.id_usuario:
                items = [
                    u for u in items
                    if str(u.get("id", "")) != str(self.id_usuario)
                ]

            # Scope institucional: solo proveedores ligados a empresas de su institución
            if self._actor_es_institucion_local():
                ids_institucion = self._empresa_ids_institucion_actor()
                filtrados = []
                for u in items:
                    rol = str(u.get("rol", ""))
                    if not self._rol_es_proveedor(rol):
                        continue
                    try:
                        empresas_u = await user_service.obtener_empresas_usuario(UUID(str(u["id"])))
                    except Exception:
                        continue
                    ids_usuario = [int(e.empresa_id) for e in empresas_u]
                    if ids_institucion.intersection(set(ids_usuario)):
                        u["_empresa_ids_asignadas"] = ids_usuario
                        u["_gestionable"] = True
                        u["_puede_gestionar_empresas"] = True
                        filtrados.append(u)
                items = filtrados
            else:
                for u in items:
                    u["_gestionable"] = True
                    u["_puede_gestionar_empresas"] = self._rol_es_proveedor(str(u.get("rol", "")))

            self.usuarios = items
            self.total_usuarios = len(self.usuarios)
        except Exception as e:
            self.manejar_error(e, "al cargar usuarios")
            self.usuarios = []
            self.total_usuarios = 0

    async def cargar_usuarios(self):
        """Carga usuarios con skeleton loading (público)."""
        async for _ in self._recargar_datos(self._fetch_usuarios):
            yield

    async def _cargar_todas_empresas(self):
        """Carga todas las empresas activas para selects de asignacion."""
        # Usuarios institucionales consumen empresas de AuthState.empresas_institucion.
        if self._actor_es_institucion_local():
            return
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

    async def _cargar_todas_instituciones(self):
        """Carga instituciones activas para el modal (solo super admin)."""
        if not self._actor_es_superadmin_local():
            self.todas_instituciones = []
            return
        try:
            instituciones = await institucion_service.obtener_todas(solo_activas=True)
            self.todas_instituciones = [
                {
                    "id": i.id,
                    "nombre": i.nombre,
                    "codigo": i.codigo,
                }
                for i in instituciones
            ]
        except Exception:
            self.todas_instituciones = []

    async def _cargar_empresas_usuario(self, user_id: str):
        """Carga las empresas asignadas a un usuario."""
        try:
            empresas = await user_service.obtener_empresas_usuario(UUID(user_id))
            self.empresas_usuario = [e.model_dump(mode='json') for e in empresas]
        except Exception:
            self.empresas_usuario = []

    async def aplicar_filtros(self):
        """Aplica filtros y recarga la lista."""
        async for _ in self._recargar_datos(self._fetch_usuarios):
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
            if self._actor_es_institucion_local() and self.form_rol != "proveedor":
                return rx.toast.error(
                    "No tienes permiso para crear ese tipo de perfil",
                    position="top-center",
                )

            # Preparar permisos solo para admins de plataforma
            permisos = self.form_permisos if self.form_rol == "admin" else PERMISOS_DEFAULT
            puede_gestionar = (
                self.form_puede_gestionar_usuarios
                if self.form_rol == "admin" and self._actor_es_superadmin_local()
                else False
            )

            rol_crear = self.form_rol
            datos = UserProfileCreate(
                email=self.form_email,
                password=self.form_password,
                nombre_completo=self.form_nombre_completo.strip(),
                rol=rol_crear,
                telefono=self.form_telefono.strip() if self.form_telefono.strip() else None,
                institucion_id=(
                    self.parse_id(self.form_institucion_id)
                    if self.form_rol == "institucion" and self.form_institucion_id
                    else None
                ),
                permisos=permisos,
                puede_gestionar_usuarios=puede_gestionar,
            )

            asignaciones = None
            if self._rol_es_proveedor(self.form_rol):
                asignaciones = [
                    UserCompanyAsignacionInicial(
                        empresa_id=self.parse_id(str(a.get("empresa_id", ""))),
                        rol_empresa=str(a.get("rol_empresa", "admin_empresa")),
                        es_principal=bool(a.get("es_principal", False)),
                    )
                    for a in self.form_asignaciones_empresas
                ]

            await user_service.crear_usuario(
                datos,
                asignaciones_empresas=asignaciones,
            )

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
    async def abrir_modal_editar(self, usuario: dict):
        """Abre modal de editar usuario."""
        error_scope = await self._asegurar_usuario_en_alcance(usuario)
        if error_scope:
            return error_scope

        self._limpiar_form_editar()
        self.usuario_seleccionado = usuario
        self.form_edit_nombre_completo = usuario.get("nombre_completo", "")
        self.form_edit_telefono = usuario.get("telefono", "") or ""
        rol_usuario = str(usuario.get("rol", "proveedor"))
        self.form_edit_rol = "proveedor" if rol_usuario == "client" else rol_usuario
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

        error_scope = await self._asegurar_usuario_en_alcance(self.usuario_seleccionado)
        if error_scope:
            return error_scope

        if self._actor_es_institucion_local() and self.form_edit_rol != "proveedor":
            return rx.toast.error(
                "No puedes cambiar este usuario a un rol fuera de proveedor",
                position="top-center",
            )

        rol_actual = str(self.usuario_seleccionado.get("rol", ""))
        rol_actual_normalizado = "proveedor" if rol_actual == "client" else rol_actual
        if "institucion" in (rol_actual_normalizado, self.form_edit_rol):
            if rol_actual_normalizado != self.form_edit_rol:
                return rx.toast.error(
                    "El cambio hacia/desde rol institucional no está soportado en este modal",
                    position="top-center",
                )

        user_id = UUID(str(self.usuario_seleccionado["id"]))

        # Preparar permisos solo para admins
        permisos = self.form_permisos if self.form_edit_rol == "admin" else PERMISOS_DEFAULT
        puede_gestionar = (
            self.form_puede_gestionar_usuarios
            if self.form_edit_rol == "admin" and self._actor_es_superadmin_local()
            else False
        )

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
    async def confirmar_desactivar(self, usuario: dict):
        """Abre modal de confirmacion para desactivar."""
        if str(usuario.get("id", "")) == self.id_usuario:
            return rx.toast.error(
                "No puedes desactivar tu propia cuenta",
                position="top-center",
            )

        error_scope = await self._asegurar_usuario_en_alcance(usuario)
        if error_scope:
            return error_scope

        self.usuario_seleccionado = usuario
        self.mostrar_modal_confirmar_desactivar = True

    def cerrar_confirmar_desactivar(self):
        self.mostrar_modal_confirmar_desactivar = False
        self.usuario_seleccionado = None

    async def desactivar_usuario_accion(self):
        """Desactiva el usuario seleccionado."""
        if not self.usuario_seleccionado:
            return

        error_scope = await self._asegurar_usuario_en_alcance(self.usuario_seleccionado)
        if error_scope:
            return error_scope

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
        usuario = next((u for u in self.usuarios if str(u.get("id")) == str(user_id)), None)
        error_scope = await self._asegurar_usuario_en_alcance(usuario)
        if error_scope:
            return error_scope

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
        error_scope = await self._asegurar_usuario_en_alcance(usuario)
        if error_scope:
            return error_scope

        if not self._rol_es_proveedor(str(usuario.get("rol", ""))):
            return rx.toast.error(
                "Solo los usuarios proveedor tienen asignaciones de empresas",
                position="top-center",
            )

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

        error_scope = await self._asegurar_usuario_en_alcance(self.usuario_seleccionado)
        if error_scope:
            return error_scope

        empresa_id = self.parse_id(self.form_empresa_id)
        if self._actor_es_institucion_local() and empresa_id not in self._empresa_ids_institucion_actor():
            return rx.toast.error(
                "Solo puedes asignar empresas relacionadas con tu institución",
                position="top-center",
            )

        user_id = UUID(str(self.usuario_seleccionado["id"]))
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

        error_scope = await self._asegurar_usuario_en_alcance(self.usuario_seleccionado)
        if error_scope:
            return error_scope

        if self._actor_es_institucion_local() and empresa_id not in self._empresa_ids_institucion_actor():
            return rx.toast.error(
                "No puedes remover acceso fuera de empresas relacionadas con tu institución",
                position="top-center",
            )

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

        error_scope = await self._asegurar_usuario_en_alcance(self.usuario_seleccionado)
        if error_scope:
            return error_scope

        if self._actor_es_institucion_local() and empresa_id not in self._empresa_ids_institucion_actor():
            return rx.toast.error(
                "No puedes marcar como principal una empresa fuera de tu alcance",
                position="top-center",
            )

        user_id = UUID(str(self.usuario_seleccionado["id"]))

        async def _on_exito():
            await self._cargar_empresas_usuario(str(self.usuario_seleccionado["id"]))

        return await self.ejecutar_guardado(
            operacion=lambda: user_service.cambiar_empresa_principal(user_id, empresa_id),
            mensaje_exito="Empresa principal actualizada",
            on_exito=_on_exito,
        )

    # ========================
    # RESET DE CONTRASEÑA
    # ========================
    async def resetear_password(self):
        """Resetea la contraseña del usuario seleccionado."""
        error = validar_password(self.form_reset_password)
        if error:
            self.error_reset_password = error
            return

        if not self.usuario_seleccionado:
            return

        error_scope = await self._asegurar_usuario_en_alcance(self.usuario_seleccionado)
        if error_scope:
            return error_scope

        user_id = UUID(str(self.usuario_seleccionado["id"]))

        async def _on_exito():
            self.form_reset_password = ""
            self.error_reset_password = ""
            self.mostrar_seccion_reset = False

        return await self.ejecutar_guardado(
            operacion=lambda: user_service.resetear_password(user_id, self.form_reset_password),
            mensaje_exito="Contraseña reseteada exitosamente",
            on_exito=_on_exito,
        )

    # ========================
    # HELPERS PRIVADOS
    # ========================
    def _limpiar_form_crear(self):
        for campo, default in FORM_DEFAULTS_CREAR.items():
            setattr(self, f"form_{campo}", default)
        self.limpiar_errores_campos([
            "email",
            "password",
            "nombre_completo",
            "telefono",
            "institucion",
            "asignaciones",
        ])
        self.form_permisos = dict(PERMISOS_DEFAULT)
        self.form_puede_gestionar_usuarios = False
        self.form_asignaciones_empresas = [self._asignacion_default(es_principal=True)]

        if self._actor_es_institucion_local():
            self.form_rol = "proveedor"

    def _limpiar_form_editar(self):
        for campo, default in FORM_DEFAULTS_EDITAR.items():
            setattr(self, f"form_{campo}", default)
        self.limpiar_errores_campos([
            "error_edit_nombre_completo",
            "error_edit_telefono",
            "error_reset_password",
        ])
        self.form_permisos = dict(PERMISOS_DEFAULT)
        self.form_puede_gestionar_usuarios = False
        # Reset contraseña
        self.form_reset_password = ""
        self.mostrar_seccion_reset = False
