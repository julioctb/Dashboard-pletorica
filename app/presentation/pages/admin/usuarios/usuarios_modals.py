"""
Modales para el modulo de gestion de usuarios.
"""
import reflex as rx
from app.presentation.pages.admin.usuarios.usuarios_state import UsuariosAdminState
from app.presentation.components.ui.form_input import form_input, form_select
from app.presentation.components.ui.modals import modal_confirmar_accion


# =============================================================================
# MODAL CREAR USUARIO
# =============================================================================

def modal_crear_usuario() -> rx.Component:
    """Modal para crear nuevo usuario."""
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title("Crear Usuario"),
            rx.dialog.description(
                rx.vstack(
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

                    # Rol
                    form_select(
                        label="Rol",
                        required=True,
                        placeholder="Seleccionar rol",
                        options=[
                            {"label": "Cliente (Empresa proveedora)", "value": "client"},
                            {"label": "Administrador (BUAP)", "value": "admin"},
                        ],
                        value=UsuariosAdminState.form_rol,
                        on_change=UsuariosAdminState.set_form_rol,
                    ),

                    spacing="4",
                    width="100%",
                    padding_y="4",
                ),
            ),

            # Botones
            rx.hstack(
                rx.dialog.close(
                    rx.button(
                        "Cancelar",
                        variant="soft",
                        color_scheme="gray",
                        on_click=UsuariosAdminState.cerrar_modal_crear,
                    ),
                ),
                rx.button(
                    rx.cond(
                        UsuariosAdminState.saving,
                        rx.hstack(rx.spinner(size="1"), rx.text("Creando..."), spacing="2"),
                        rx.text("Crear Usuario"),
                    ),
                    on_click=UsuariosAdminState.crear_usuario,
                    disabled=~UsuariosAdminState.puede_crear,
                    color_scheme="blue",
                ),
                spacing="3",
                justify="end",
                width="100%",
                padding_top="4",
            ),

            max_width="450px",
        ),
        open=UsuariosAdminState.mostrar_modal_crear,
        on_open_change=UsuariosAdminState.set_mostrar_modal_crear,
    )


# =============================================================================
# MODAL EDITAR USUARIO
# =============================================================================

def modal_editar_usuario() -> rx.Component:
    """Modal para editar usuario existente."""
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title("Editar Usuario"),
            rx.dialog.description(
                rx.vstack(
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
                        options=[
                            {"label": "Cliente (Empresa proveedora)", "value": "client"},
                            {"label": "Administrador (BUAP)", "value": "admin"},
                        ],
                        value=UsuariosAdminState.form_edit_rol,
                        on_change=UsuariosAdminState.set_form_edit_rol,
                    ),

                    spacing="4",
                    width="100%",
                    padding_y="4",
                ),
            ),

            # Botones
            rx.hstack(
                rx.dialog.close(
                    rx.button(
                        "Cancelar",
                        variant="soft",
                        color_scheme="gray",
                        on_click=UsuariosAdminState.cerrar_modal_editar,
                    ),
                ),
                rx.button(
                    rx.cond(
                        UsuariosAdminState.saving,
                        rx.hstack(rx.spinner(size="1"), rx.text("Guardando..."), spacing="2"),
                        rx.text("Guardar"),
                    ),
                    on_click=UsuariosAdminState.editar_usuario,
                    disabled=~UsuariosAdminState.puede_editar,
                    color_scheme="blue",
                ),
                spacing="3",
                justify="end",
                width="100%",
                padding_top="4",
            ),

            max_width="450px",
        ),
        open=UsuariosAdminState.mostrar_modal_editar,
        on_open_change=UsuariosAdminState.set_mostrar_modal_editar,
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
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title("Gestionar Empresas"),
            rx.dialog.description(
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
                    rx.text(""),
                ),
                margin_bottom="16px",
            ),

            rx.vstack(
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
                    rx.button(
                        rx.icon("plus", size=14),
                        "Asignar",
                        on_click=UsuariosAdminState.asignar_empresa,
                        disabled=UsuariosAdminState.form_empresa_id == "",
                        size="2",
                        color_scheme="blue",
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

            # Boton cerrar
            rx.hstack(
                rx.dialog.close(
                    rx.button(
                        "Cerrar",
                        variant="soft",
                        color_scheme="gray",
                        on_click=UsuariosAdminState.cerrar_modal_empresas,
                    ),
                ),
                justify="end",
                width="100%",
                margin_top="16px",
            ),

            max_width="500px",
            padding="24px",
            overflow_x="hidden",
        ),
        open=UsuariosAdminState.mostrar_modal_empresas,
        on_open_change=UsuariosAdminState.set_mostrar_modal_empresas,
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
