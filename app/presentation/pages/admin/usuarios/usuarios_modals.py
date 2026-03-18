"""
Modales para el modulo de gestion de usuarios.
"""
import reflex as rx
from app.presentation.pages.admin.usuarios.usuarios_state import UsuariosAdminState
from app.presentation.components.ui.form_input import form_input, form_select
from app.presentation.components.ui.buttons import boton_guardar, boton_cancelar
from app.presentation.components.ui.modals import modal_confirmar_accion, modal_formulario, modal_detalle
from app.presentation.components.shared.auth_state import AuthState
from app.presentation.components.shared.permisos_matrix import matriz_permisos_component
from app.presentation.theme import Spacing, Radius


def _matriz_permisos() -> rx.Component:
    """Matriz de permisos con checkboxes (operar/autorizar por módulo)."""
    return matriz_permisos_component(
        permisos_var=UsuariosAdminState.form_permisos,
        toggle_fn=UsuariosAdminState.toggle_permiso,
        superadmin_condition=UsuariosAdminState.puede_mostrar_checkbox_superadmin,
        gestion_usuarios_var=UsuariosAdminState.form_puede_gestionar_usuarios,
        gestion_usuarios_fn=UsuariosAdminState.set_form_puede_gestionar_usuarios,
    )


# =============================================================================
# MODAL CREAR USUARIO
# =============================================================================

def _selector_institucion_crear() -> rx.Component:
    """Selector de institución para perfiles institucionales."""
    return form_select(
        label="Institución",
        required=True,
        placeholder="Seleccionar institución",
        options=UsuariosAdminState.opciones_instituciones,
        value=UsuariosAdminState.form_institucion_id,
        on_change=UsuariosAdminState.set_form_institucion_id,
        error=UsuariosAdminState.error_institucion,
        hint="Aplica para perfiles institucionales (ej. BUAP).",
    )


def _fila_asignacion_inicial(fila: dict) -> rx.Component:
    """Fila de asignación inicial empresa + rol_empresa."""
    return rx.vstack(
        rx.hstack(
            rx.text("Empresa / Rol", size="1", weight="bold", color="var(--gray-9)"),
            rx.spacer(),
            rx.checkbox(
                "Principal",
                checked=fila["es_principal"],
                on_change=lambda _v: UsuariosAdminState.marcar_asignacion_principal(fila["idx"]),
                size="1",
            ),
            rx.cond(
                UsuariosAdminState.form_asignaciones_empresas.length() > 1,
                rx.icon_button(
                    rx.icon("trash-2", size=14),
                    size="1",
                    variant="ghost",
                    color_scheme="red",
                    on_click=UsuariosAdminState.quitar_asignacion_empresa(fila["idx"]),
                ),
            ),
            align="center",
            width="100%",
        ),
        rx.hstack(
            rx.select.root(
                rx.select.trigger(
                    placeholder="Seleccionar empresa...",
                    width="100%",
                ),
                rx.select.content(
                    rx.foreach(
                        UsuariosAdminState.opciones_empresas_creacion,
                        lambda e: rx.select.item(e["label"], value=e["id"]),
                    ),
                ),
                value=fila["empresa_id"],
                on_change=lambda value: UsuariosAdminState.set_asignacion_empresa_id(fila["idx"], value),
                width="100%",
                min_width="240px",
                flex="1",
            ),
            rx.select.root(
                rx.select.trigger(
                    placeholder="Rol dentro de la empresa",
                    width="100%",
                ),
                rx.select.content(
                    rx.foreach(
                        UsuariosAdminState.opciones_roles_empresa,
                        lambda rol: rx.select.item(rol["label"], value=rol["value"]),
                    ),
                ),
                value=fila["rol_empresa"],
                on_change=lambda value: UsuariosAdminState.set_asignacion_rol_empresa(fila["idx"], value),
                width="100%",
                min_width="240px",
                flex="1",
            ),
            width="100%",
            gap="2",
            align="start",
            wrap="wrap",
        ),
        width="100%",
        spacing="2",
        padding=Spacing.MD,
        border="1px solid var(--gray-5)",
        border_radius=Radius.LG,
        background="var(--gray-2)",
    )


def _seccion_asignaciones_iniciales() -> rx.Component:
    """Sección de asignaciones empresa + rol_empresa para proveedores."""
    return rx.vstack(
        rx.text("Empresas y perfil por empresa", size="2", weight="bold"),
        rx.text(
            "Asigna una o más empresas y define el rol del usuario en cada una.",
            size="1",
            color="var(--gray-9)",
        ),
        rx.foreach(
            UsuariosAdminState.form_asignaciones_empresas,
            _fila_asignacion_inicial,
        ),
        rx.button(
            rx.icon("plus", size=14),
            "Agregar empresa",
            variant="soft",
            size="2",
            on_click=UsuariosAdminState.agregar_asignacion_empresa,
            width="100%",
        ),
        rx.cond(
            UsuariosAdminState.error_asignaciones != "",
            rx.text(UsuariosAdminState.error_asignaciones, color="var(--red-9)", size="1"),
            rx.text("", size="1"),
        ),
        spacing="2",
        width="100%",
        align_items="stretch",
    )

def modal_crear_usuario() -> rx.Component:
    """Modal para crear nuevo usuario."""
    return modal_formulario(
        open=UsuariosAdminState.mostrar_modal_crear,
        titulo="Crear Usuario",
        descripcion="Complete los datos y asigne el perfil del usuario.",
        icono="user-plus",
        on_guardar=UsuariosAdminState.crear_usuario,
        on_cancelar=UsuariosAdminState.cerrar_modal_crear,
        puede_guardar=UsuariosAdminState.puede_crear,
        loading=UsuariosAdminState.saving,
        texto_guardar="Crear Usuario",
        texto_guardando="Creando...",
        scroll_body=True,
        max_body_height="65vh",
        max_width="620px",
        contenido=rx.vstack(
            # Email
            form_input(
                label="Email",
                required=True,
                placeholder="usuario@ejemplo.com",
                value=UsuariosAdminState.form_email,
                on_change=UsuariosAdminState.set_form_email,
                on_blur=UsuariosAdminState.validar_email_campo,
                error=UsuariosAdminState.error_email,
                type="email",
            ),

            # Password
            form_input(
                label="Contrasena",
                required=True,
                placeholder="Minimo 8 caracteres",
                value=UsuariosAdminState.form_password,
                on_change=UsuariosAdminState.set_form_password,
                on_blur=UsuariosAdminState.validar_password_campo,
                error=UsuariosAdminState.error_password,
                type="password",
            ),

            # Nombre completo
            form_input(
                label="Nombre completo",
                required=True,
                placeholder="Nombre y apellidos",
                value=UsuariosAdminState.form_nombre_completo,
                on_change=UsuariosAdminState.set_form_nombre_completo,
                on_blur=UsuariosAdminState.validar_nombre_campo,
                error=UsuariosAdminState.error_nombre_completo,
                max_length=150,
            ),

            # Telefono
            form_input(
                label="Telefono",
                placeholder="10 digitos (opcional)",
                value=UsuariosAdminState.form_telefono,
                on_change=UsuariosAdminState.set_form_telefono,
                on_blur=UsuariosAdminState.validar_telefono_campo,
                error=UsuariosAdminState.error_telefono,
                max_length=10,
            ),

            # Rol de plataforma
            form_select(
                label="Tipo de perfil / rol de plataforma",
                required=True,
                placeholder="Seleccionar rol",
                options=UsuariosAdminState.opciones_roles_creacion,
                value=UsuariosAdminState.form_rol,
                on_change=UsuariosAdminState.set_form_rol,
            ),

            # Institucion (solo rol institucional)
            rx.cond(
                UsuariosAdminState.mostrar_selector_institucion,
                _selector_institucion_crear(),
            ),

            # Asignaciones iniciales por empresa (solo proveedores)
            rx.cond(
                UsuariosAdminState.mostrar_asignaciones_iniciales,
                _seccion_asignaciones_iniciales(),
            ),

            # Matriz de permisos (solo para admins)
            rx.cond(
                UsuariosAdminState.mostrar_permisos,
                _matriz_permisos(),
            ),

            spacing="4",
            width="100%",
        ),
    )


# =============================================================================
# MODAL EDITAR USUARIO
# =============================================================================

def modal_editar_usuario() -> rx.Component:
    """Modal para editar usuario existente."""
    return modal_formulario(
        open=UsuariosAdminState.mostrar_modal_editar,
        titulo="Editar Usuario",
        descripcion="Actualice los datos del usuario y sus permisos según su rol.",
        icono="user-pen",
        on_guardar=UsuariosAdminState.editar_usuario,
        on_cancelar=UsuariosAdminState.cerrar_modal_editar,
        puede_guardar=UsuariosAdminState.puede_editar,
        loading=UsuariosAdminState.saving,
        scroll_body=True,
        max_body_height="65vh",
        max_width="620px",
        contenido=rx.vstack(
            # Email (solo lectura)
            rx.box(
                rx.text("Email", size="2", weight="medium", color="var(--gray-11)"),
                rx.cond(
                    UsuariosAdminState.usuario_seleccionado,
                    rx.text(
                        UsuariosAdminState.usuario_seleccionado["email"],
                        size="2",
                        color="var(--gray-9)",
                        style={"padding": "8px 12px", "background": "var(--gray-3)", "border_radius": "6px"},
                    ),
                    rx.text("", size="2"),
                ),
                width="100%",
            ),

            # Nombre completo
            form_input(
                label="Nombre completo",
                required=True,
                placeholder="Nombre y apellidos",
                value=UsuariosAdminState.form_edit_nombre_completo,
                on_change=UsuariosAdminState.set_form_edit_nombre_completo,
                on_blur=UsuariosAdminState.validar_edit_nombre_campo,
                error=UsuariosAdminState.error_edit_nombre_completo,
                max_length=150,
            ),

            # Telefono
            form_input(
                label="Telefono",
                placeholder="10 digitos (opcional)",
                value=UsuariosAdminState.form_edit_telefono,
                on_change=UsuariosAdminState.set_form_edit_telefono,
                on_blur=UsuariosAdminState.validar_edit_telefono_campo,
                error=UsuariosAdminState.error_edit_telefono,
                max_length=10,
            ),

            # Rol
            form_select(
                label="Rol",
                required=True,
                placeholder="Seleccionar rol",
                options=UsuariosAdminState.opciones_roles_edicion,
                value=UsuariosAdminState.form_edit_rol,
                on_change=UsuariosAdminState.set_form_edit_rol,
            ),

            # Matriz de permisos (solo para admins)
            rx.cond(
                UsuariosAdminState.mostrar_edit_permisos,
                _matriz_permisos(),
            ),

            # Resetear contraseña (solo super admin)
            rx.cond(
                AuthState.es_super_admin,
                _seccion_reset_password(),
            ),

            spacing="4",
            width="100%",
        ),
    )


# =============================================================================
# SECCIÓN RESET CONTRASEÑA (dentro de modal editar)
# =============================================================================

def _seccion_reset_password() -> rx.Component:
    """Sección colapsable para resetear contraseña de un usuario."""
    return rx.vstack(
        rx.separator(),
        # Botón toggle para mostrar/ocultar
        rx.cond(
            ~UsuariosAdminState.mostrar_seccion_reset,
            rx.button(
                rx.icon("key-round", size=14),
                "Resetear contraseña",
                variant="outline",
                color_scheme="orange",
                size="2",
                width="100%",
                on_click=UsuariosAdminState.set_mostrar_seccion_reset(True),
            ),
            rx.vstack(
                rx.text(
                    "Nueva contraseña",
                    size="2",
                    weight="medium",
                    color="var(--gray-11)",
                ),
                form_input(
                    label="",
                    placeholder="Minimo 8 caracteres",
                    value=UsuariosAdminState.form_reset_password,
                    on_change=UsuariosAdminState.set_form_reset_password,
                    on_blur=UsuariosAdminState.validar_reset_password_campo,
                    error=UsuariosAdminState.error_reset_password,
                    type="password",
                ),
                rx.hstack(
                    boton_cancelar(
                        size="1",
                        on_click=UsuariosAdminState.set_mostrar_seccion_reset(False),
                    ),
                    boton_guardar(
                        texto="Aplicar",
                        texto_guardando="Aplicando...",
                        color_scheme="orange",
                        size="1",
                        on_click=UsuariosAdminState.resetear_password,
                        saving=UsuariosAdminState.saving,
                        disabled=UsuariosAdminState.form_reset_password.length() < 8,
                    ),
                    spacing="2",
                    justify="end",
                    width="100%",
                ),
                spacing="2",
                width="100%",
                padding="12px",
                border="1px solid var(--orange-6)",
                border_radius="8px",
                background="var(--orange-2)",
            ),
        ),
        spacing="3",
        width="100%",
    )


# =============================================================================
# MODAL GESTIONAR EMPRESAS
# =============================================================================

def _fila_empresa_asignada(empresa: dict) -> rx.Component:
    """Fila de una empresa asignada al usuario."""
    return rx.hstack(
        # Info de la empresa
        rx.vstack(
            rx.hstack(
                rx.text(
                    empresa["empresa_nombre"],
                    weight="bold",
                    size="2",
                    overflow="hidden",
                    text_overflow="ellipsis",
                    white_space="nowrap",
                ),
                rx.cond(
                    empresa["es_principal"],
                    rx.badge("Principal", color_scheme="blue", size="1", flex_shrink="0"),
                ),
                spacing="2",
                align="center",
                min_width="0",
                width="100%",
            ),
            rx.cond(
                empresa["empresa_rfc"],
                rx.text(empresa["empresa_rfc"], size="1", color="gray"),
            ),
            spacing="0",
            min_width="0",
            flex="1",
        ),
        # Acciones
        rx.hstack(
            # Hacer principal
            rx.cond(
                ~empresa["es_principal"],
                rx.tooltip(
                    rx.icon_button(
                        rx.icon("star", size=14),
                        size="1",
                        variant="ghost",
                        color_scheme="amber",
                        on_click=UsuariosAdminState.hacer_principal(empresa["empresa_id"]),
                        disabled=UsuariosAdminState.saving,
                    ),
                    content="Hacer principal",
                ),
            ),
            # Quitar
            rx.tooltip(
                rx.icon_button(
                    rx.icon("x", size=14),
                    size="1",
                    variant="ghost",
                    color_scheme="red",
                    on_click=UsuariosAdminState.quitar_empresa(empresa["empresa_id"]),
                    disabled=UsuariosAdminState.saving,
                ),
                content="Quitar acceso",
            ),
            spacing="1",
            flex_shrink="0",
        ),
        width="100%",
        padding="3",
        border_bottom="1px solid var(--gray-4)",
        align="center",
        gap="3",
    )


def modal_gestionar_empresas() -> rx.Component:
    """Modal para gestionar empresas asignadas a un usuario."""
    return modal_detalle(
        open=UsuariosAdminState.mostrar_modal_empresas,
        titulo="Gestionar Empresas",
        on_cerrar=UsuariosAdminState.cerrar_modal_empresas,
        max_width="500px",
        contenido=rx.vstack(
            # Descripcion
            rx.cond(
                UsuariosAdminState.usuario_seleccionado,
                rx.text(
                    "Empresas de ",
                    rx.text(
                        UsuariosAdminState.usuario_seleccionado["nombre_completo"],
                        weight="bold",
                        as_="span",
                    ),
                    size="2",
                    color="gray",
                ),
            ),

            # Asignar nueva empresa
            rx.vstack(
                rx.select.root(
                    rx.select.trigger(
                        placeholder="Seleccionar empresa...",
                        width="100%",
                    ),
                    rx.select.content(
                        rx.foreach(
                            UsuariosAdminState.opciones_empresas_disponibles,
                            lambda e: rx.select.item(
                                e["nombre_comercial"],
                                value=e["id"],
                            ),
                        ),
                    ),
                    value=UsuariosAdminState.form_empresa_id,
                    on_change=UsuariosAdminState.set_form_empresa_id,
                    width="100%",
                ),
                boton_guardar(
                    texto="Asignar",
                    texto_guardando="Asignando...",
                    on_click=UsuariosAdminState.asignar_empresa,
                    saving=UsuariosAdminState.saving,
                    disabled=UsuariosAdminState.form_empresa_id == "",
                    size="2",
                    width="100%",
                ),
                width="100%",
                spacing="2",
            ),

            rx.separator(),

            # Lista de empresas asignadas
            rx.cond(
                UsuariosAdminState.empresas_usuario.length() > 0,
                rx.vstack(
                    rx.foreach(
                        UsuariosAdminState.empresas_usuario,
                        _fila_empresa_asignada,
                    ),
                    width="100%",
                    spacing="0",
                ),
                rx.center(
                    rx.text("Sin empresas asignadas", color="gray", size="2"),
                    padding="6",
                ),
            ),

            spacing="4",
            width="100%",
        ),
    )


# =============================================================================
# MODAL CONFIRMAR DESACTIVAR
# =============================================================================

def modal_confirmar_desactivar() -> rx.Component:
    """Modal de confirmacion para desactivar usuario."""
    return modal_confirmar_accion(
        open=UsuariosAdminState.mostrar_modal_confirmar_desactivar,
        titulo="Desactivar Usuario",
        mensaje="Esta seguro de que desea desactivar este usuario?",
        detalle_contenido=rx.cond(
            UsuariosAdminState.usuario_seleccionado,
            rx.vstack(
                rx.text(
                    UsuariosAdminState.usuario_seleccionado["nombre_completo"],
                    weight="bold",
                ),
                rx.cond(
                    UsuariosAdminState.usuario_seleccionado["email"],
                    rx.text(
                        UsuariosAdminState.usuario_seleccionado["email"],
                        size="2",
                        color="gray",
                    ),
                ),
                spacing="1",
            ),
            rx.text(""),
        ),
        nota_adicional="El usuario no podra iniciar sesion. Podra reactivarlo despues.",
        on_confirmar=UsuariosAdminState.desactivar_usuario_accion,
        on_cancelar=UsuariosAdminState.cerrar_confirmar_desactivar,
        loading=UsuariosAdminState.saving,
        texto_confirmar="Desactivar",
        color_confirmar="red",
        icono_detalle="user-x",
        color_detalle="orange",
    )
