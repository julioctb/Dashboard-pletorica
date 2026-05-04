"""
Modales para la gestion de usuarios de la empresa desde el portal.
"""
import reflex as rx

from app.presentation.pages.portal.usuarios_empresa.state import UsuariosEmpresaState
from app.presentation.components.ui.form_input import form_input, form_select
from app.presentation.components.ui.modals import modal_confirmar_accion, modal_formulario
from app.presentation.components.shared.permisos_matrix import matriz_permisos_component
from app.presentation.theme import Colors, Spacing


PORTAL_USER_MODAL_DESCRIPTION = (
    "Si el email ya existe como proveedor, se vinculara automaticamente."
)
PORTAL_MODAL_MAX_WIDTH = f"calc({Spacing.XXL} * 20)"
PORTAL_FORM_VARIANT = "portal"


# =============================================================================
# MODAL CREAR USUARIO
# =============================================================================

def modal_crear_usuario_empresa() -> rx.Component:
    """Modal para crear o vincular un usuario a la empresa."""
    return modal_formulario(
        open=UsuariosEmpresaState.mostrar_modal_crear,
        titulo="Agregar usuario",
        descripcion=PORTAL_USER_MODAL_DESCRIPTION,
        icono="user-plus",
        color_icono="teal",
        on_guardar=UsuariosEmpresaState.crear_usuario,
        on_cancelar=UsuariosEmpresaState.cerrar_modal_crear,
        texto_guardar="Agregar usuario",
        texto_guardando="Agregando...",
        color_guardar="teal",
        loading=UsuariosEmpresaState.saving,
        scroll_body=True,
        max_body_height="65vh",
        max_width=PORTAL_MODAL_MAX_WIDTH,
        contenido=rx.vstack(
            form_input(
                label="Email",
                required=True,
                placeholder="usuario@ejemplo.com",
                value=UsuariosEmpresaState.form_email,
                on_change=UsuariosEmpresaState.set_form_email,
                on_blur=UsuariosEmpresaState.validar_email_campo,
                error=UsuariosEmpresaState.error_email,
                type="email",
                label_variant=PORTAL_FORM_VARIANT,
                style_variant=PORTAL_FORM_VARIANT,
            ),
            form_input(
                label="Nombre completo",
                required=True,
                placeholder="Nombre y apellidos",
                value=UsuariosEmpresaState.form_nombre,
                on_change=UsuariosEmpresaState.set_form_nombre,
                on_blur=UsuariosEmpresaState.validar_nombre_campo,
                error=UsuariosEmpresaState.error_nombre,
                max_length=150,
                label_variant=PORTAL_FORM_VARIANT,
                style_variant=PORTAL_FORM_VARIANT,
            ),
            rx.grid(
                form_input(
                    label="Telefono",
                    placeholder="10 digitos (opcional)",
                    value=UsuariosEmpresaState.form_telefono,
                    on_change=UsuariosEmpresaState.set_form_telefono,
                    on_blur=UsuariosEmpresaState.validar_telefono_campo,
                    error=UsuariosEmpresaState.error_telefono,
                    max_length=10,
                    label_variant=PORTAL_FORM_VARIANT,
                    style_variant=PORTAL_FORM_VARIANT,
                ),
                form_select(
                    label="Rol en la empresa",
                    required=True,
                    placeholder="Seleccionar rol",
                    options=UsuariosEmpresaState.opciones_roles,
                    value=UsuariosEmpresaState.form_rol_empresa,
                    on_change=UsuariosEmpresaState.set_form_rol_empresa,
                    label_variant=PORTAL_FORM_VARIANT,
                    style_variant=PORTAL_FORM_VARIANT,
                ),
                columns="2",
                gap=Spacing.MD,
                width="100%",
            ),
            matriz_permisos_component(
                permisos_var=UsuariosEmpresaState.form_permisos,
                toggle_fn=UsuariosEmpresaState.toggle_permiso,
                variant="portal",
                checkbox_color_scheme=Colors.PORTAL_ACCENT_SCHEME,
                show_unavailable_checkbox=True,
            ),
            gap=Spacing.BASE,
            width="100%",
        ),
    )


# =============================================================================
# MODAL EDITAR USUARIO
# =============================================================================

def modal_editar_usuario_empresa() -> rx.Component:
    """Modal para editar rol y permisos de un usuario existente."""
    return modal_formulario(
        open=UsuariosEmpresaState.mostrar_modal_editar,
        titulo="Editar Usuario",
        descripcion="Modifica el rol y los permisos del usuario en tu empresa.",
        icono="user-cog",
        color_icono="teal",
        on_guardar=UsuariosEmpresaState.guardar_edicion,
        on_cancelar=UsuariosEmpresaState.cerrar_modal_editar,
        loading=UsuariosEmpresaState.saving,
        color_guardar="teal",
        scroll_body=True,
        max_body_height="65vh",
        max_width="620px",
        contenido=rx.vstack(
            # Nombre (solo lectura)
            rx.vstack(
                rx.text("Nombre", size="2", weight="medium", color="var(--gray-11)"),
                rx.text(
                    UsuariosEmpresaState.edit_nombre_display,
                    size="2",
                    color="var(--gray-9)",
                    style={
                        "padding": "8px 12px",
                        "background": "var(--gray-3)",
                        "border_radius": "6px",
                        "width": "100%",
                    },
                ),
                spacing="1",
                width="100%",
                align_items="start",
            ),

            # Email (solo lectura)
            rx.vstack(
                rx.text("Email", size="2", weight="medium", color="var(--gray-11)"),
                rx.text(
                    UsuariosEmpresaState.edit_email_display,
                    size="2",
                    color="var(--gray-9)",
                    style={
                        "padding": "8px 12px",
                        "background": "var(--gray-3)",
                        "border_radius": "6px",
                        "width": "100%",
                    },
                ),
                spacing="1",
                width="100%",
                align_items="start",
            ),

            # Rol en la empresa
            form_select(
                label="Rol en la empresa",
                required=True,
                placeholder="Seleccionar rol",
                options=UsuariosEmpresaState.opciones_roles,
                value=UsuariosEmpresaState.edit_rol_empresa,
                on_change=UsuariosEmpresaState.set_edit_rol_empresa,
                label_variant=PORTAL_FORM_VARIANT,
                style_variant=PORTAL_FORM_VARIANT,
            ),

            # Matriz de permisos
            matriz_permisos_component(
                permisos_var=UsuariosEmpresaState.edit_permisos,
                toggle_fn=UsuariosEmpresaState.toggle_permiso_editar,
                variant="portal",
                checkbox_color_scheme=Colors.PORTAL_ACCENT_SCHEME,
                show_unavailable_checkbox=True,
            ),

            spacing="4",
            width="100%",
        ),
    )


# =============================================================================
# MODAL DESACTIVAR / REACTIVAR USUARIO
# =============================================================================

def modal_toggle_activo_usuario() -> rx.Component:
    """Modal de confirmación para desactivar o reactivar un usuario."""
    return modal_confirmar_accion(
        open=UsuariosEmpresaState.mostrar_modal_desactivar,
        titulo=rx.cond(
            UsuariosEmpresaState.activo_usuario_desactivar,
            "Desactivar Usuario",
            "Reactivar Usuario",
        ),
        mensaje=rx.cond(
            UsuariosEmpresaState.activo_usuario_desactivar,
            "¿Seguro que deseas desactivar a este usuario?",
            "¿Seguro que deseas reactivar a este usuario?",
        ),
        detalle_contenido=rx.text(
            UsuariosEmpresaState.nombre_usuario_desactivar,
            weight="bold",
            size="2",
        ),
        nota_adicional=rx.cond(
            UsuariosEmpresaState.activo_usuario_desactivar,
            "El usuario no podra acceder a esta empresa. Puedes reactivarlo despues.",
            "El usuario recuperara acceso a esta empresa.",
        ),
        on_confirmar=UsuariosEmpresaState.confirmar_toggle_activo,
        on_cancelar=UsuariosEmpresaState.cerrar_modal_desactivar,
        loading=UsuariosEmpresaState.saving,
        texto_confirmar=rx.cond(
            UsuariosEmpresaState.activo_usuario_desactivar,
            "Desactivar",
            "Reactivar",
        ),
        texto_confirmando=rx.cond(
            UsuariosEmpresaState.activo_usuario_desactivar,
            "Desactivando...",
            "Reactivando...",
        ),
        color_confirmar="red",
        icono_detalle="user-cog",
        color_detalle="orange",
    )
