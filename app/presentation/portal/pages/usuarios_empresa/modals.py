"""
Modales para la gestion de usuarios de la empresa desde el portal.
"""
import reflex as rx

from app.presentation.portal.pages.usuarios_empresa.state import UsuariosEmpresaState
from app.presentation.components.ui.form_input import form_input, form_select
from app.presentation.components.ui.buttons import boton_guardar, boton_cancelar
from app.presentation.components.ui.modals import modal_confirmar_accion
from app.presentation.components.shared.permisos_matrix import matriz_permisos_component
from app.presentation.theme import Spacing, Radius


# =============================================================================
# MODAL CREAR USUARIO
# =============================================================================

def modal_crear_usuario_empresa() -> rx.Component:
    """Modal para crear o vincular un usuario a la empresa."""
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title("Agregar Usuario"),
            rx.dialog.description(
                "Ingresa los datos del usuario. Si el email ya existe como proveedor, "
                "se vinculará a tu empresa automáticamente.",
                margin_bottom=Spacing.MD,
                color="var(--gray-10)",
                size="2",
            ),

            rx.box(
                rx.vstack(
                    # Email
                    form_input(
                        label="Email",
                        required=True,
                        placeholder="usuario@ejemplo.com",
                        value=UsuariosEmpresaState.form_email,
                        on_change=UsuariosEmpresaState.set_form_email,
                        on_blur=UsuariosEmpresaState.validar_email_campo,
                        error=UsuariosEmpresaState.error_email,
                        type="email",
                    ),

                    # Nombre completo
                    form_input(
                        label="Nombre completo",
                        required=True,
                        placeholder="Nombre y apellidos",
                        value=UsuariosEmpresaState.form_nombre,
                        on_change=UsuariosEmpresaState.set_form_nombre,
                        on_blur=UsuariosEmpresaState.validar_nombre_campo,
                        error=UsuariosEmpresaState.error_nombre,
                        max_length=150,
                    ),

                    # Telefono
                    form_input(
                        label="Telefono",
                        placeholder="10 digitos (opcional)",
                        value=UsuariosEmpresaState.form_telefono,
                        on_change=UsuariosEmpresaState.set_form_telefono,
                        on_blur=UsuariosEmpresaState.validar_telefono_campo,
                        error=UsuariosEmpresaState.error_telefono,
                        max_length=10,
                    ),

                    # Rol en la empresa
                    form_select(
                        label="Rol en la empresa",
                        required=True,
                        placeholder="Seleccionar rol",
                        options=UsuariosEmpresaState.opciones_roles,
                        value=UsuariosEmpresaState.form_rol_empresa,
                        on_change=UsuariosEmpresaState.set_form_rol_empresa,
                    ),

                    # Matriz de permisos
                    matriz_permisos_component(
                        permisos_var=UsuariosEmpresaState.form_permisos,
                        toggle_fn=UsuariosEmpresaState.toggle_permiso,
                    ),

                    spacing="4",
                    width="100%",
                    padding="0",
                ),
                width="100%",
                overflow_y="auto",
                max_height="calc(85vh - 170px)",
                padding_right=Spacing.XS,
            ),

            # Botones
            rx.hstack(
                boton_cancelar(on_click=UsuariosEmpresaState.cerrar_modal_crear),
                boton_guardar(
                    texto="Agregar Usuario",
                    texto_guardando="Agregando...",
                    on_click=UsuariosEmpresaState.crear_usuario,
                    saving=UsuariosEmpresaState.saving,
                ),
                spacing="3",
                justify="end",
                width="100%",
                padding_top=Spacing.SM,
                border_top="1px solid var(--gray-4)",
                margin_top=Spacing.SM,
            ),

            max_width="620px",
            width=f"calc(100vw - {Spacing.XXL})",
            max_height="85vh",
            overflow="hidden",
            padding=Spacing.LG,
            border_radius=Radius.XL,
            display="flex",
            flex_direction="column",
        ),
        open=UsuariosEmpresaState.mostrar_modal_crear,
        on_open_change=rx.noop,
    )


# =============================================================================
# MODAL EDITAR USUARIO
# =============================================================================

def modal_editar_usuario_empresa() -> rx.Component:
    """Modal para editar rol y permisos de un usuario existente."""
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title("Editar Usuario"),
            rx.dialog.description(
                "Modifica el rol y los permisos del usuario en tu empresa.",
                margin_bottom=Spacing.MD,
                color="var(--gray-10)",
                size="2",
            ),

            rx.box(
                rx.vstack(
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
                    ),

                    # Matriz de permisos
                    matriz_permisos_component(
                        permisos_var=UsuariosEmpresaState.edit_permisos,
                        toggle_fn=UsuariosEmpresaState.toggle_permiso_editar,
                    ),

                    spacing="4",
                    width="100%",
                    padding="0",
                ),
                width="100%",
                overflow_y="auto",
                max_height="calc(85vh - 170px)",
                padding_right=Spacing.XS,
            ),

            # Botones
            rx.hstack(
                boton_cancelar(on_click=UsuariosEmpresaState.cerrar_modal_editar),
                boton_guardar(
                    texto="Guardar",
                    texto_guardando="Guardando...",
                    on_click=UsuariosEmpresaState.guardar_edicion,
                    saving=UsuariosEmpresaState.saving,
                ),
                spacing="3",
                justify="end",
                width="100%",
                padding_top=Spacing.SM,
                border_top="1px solid var(--gray-4)",
                margin_top=Spacing.SM,
            ),

            max_width="620px",
            width=f"calc(100vw - {Spacing.XXL})",
            max_height="85vh",
            overflow="hidden",
            padding=Spacing.LG,
            border_radius=Radius.XL,
            display="flex",
            flex_direction="column",
        ),
        open=UsuariosEmpresaState.mostrar_modal_editar,
        on_open_change=rx.noop,
    )


# =============================================================================
# MODAL DESACTIVAR / REACTIVAR USUARIO
# =============================================================================

def modal_toggle_activo_usuario() -> rx.Component:
    """Modal de confirmación para desactivar o reactivar un usuario."""
    return rx.alert_dialog.root(
        rx.alert_dialog.content(
            rx.alert_dialog.title(
                rx.cond(
                    UsuariosEmpresaState.activo_usuario_desactivar,
                    "Desactivar Usuario",
                    "Reactivar Usuario",
                )
            ),
            rx.vstack(
                rx.cond(
                    UsuariosEmpresaState.activo_usuario_desactivar,
                    rx.text("¿Seguro que deseas desactivar a este usuario?"),
                    rx.text("¿Seguro que deseas reactivar a este usuario?"),
                ),
                rx.callout(
                    rx.text(
                        UsuariosEmpresaState.nombre_usuario_desactivar,
                        weight="bold",
                        size="2",
                    ),
                    icon="user-cog",
                    color_scheme="orange",
                    size="2",
                ),
                rx.cond(
                    UsuariosEmpresaState.activo_usuario_desactivar,
                    rx.text(
                        "El usuario no podra acceder a esta empresa. Puedes reactivarlo despues.",
                        size="2",
                        color="gray",
                    ),
                    rx.text(
                        "El usuario recuperara acceso a esta empresa.",
                        size="2",
                        color="gray",
                    ),
                ),
                # Botones
                rx.hstack(
                    rx.alert_dialog.cancel(
                        rx.button(
                            "Cancelar",
                            variant="soft",
                            color_scheme="gray",
                            on_click=UsuariosEmpresaState.cerrar_modal_desactivar,
                        ),
                    ),
                    rx.alert_dialog.action(
                        rx.cond(
                            UsuariosEmpresaState.activo_usuario_desactivar,
                            rx.button(
                                rx.cond(
                                    UsuariosEmpresaState.saving,
                                    rx.spinner(size="2"),
                                    rx.text("Desactivar"),
                                ),
                                color_scheme="red",
                                disabled=UsuariosEmpresaState.saving,
                                on_click=UsuariosEmpresaState.confirmar_toggle_activo,
                            ),
                            rx.button(
                                rx.cond(
                                    UsuariosEmpresaState.saving,
                                    rx.spinner(size="2"),
                                    rx.text("Reactivar"),
                                ),
                                color_scheme="green",
                                disabled=UsuariosEmpresaState.saving,
                                on_click=UsuariosEmpresaState.confirmar_toggle_activo,
                            ),
                        ),
                    ),
                    spacing="3",
                    justify="end",
                    width="100%",
                    margin_top="16px",
                ),
                spacing="3",
                width="100%",
            ),
            max_width="400px",
        ),
        open=UsuariosEmpresaState.mostrar_modal_desactivar,
    )
