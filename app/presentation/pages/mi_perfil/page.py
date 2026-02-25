"""Página compartida de Mi Perfil (backoffice/portal)."""
import reflex as rx

from app.presentation.layout import page_layout, page_header
from app.presentation.components.ui import form_input, boton_guardar
from app.presentation.theme import Colors, Radius, Spacing, Typography

from .state import MiPerfilState


def _card_seccion(titulo: str, subtitulo: str, contenido: rx.Component) -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.vstack(
                rx.text(
                    titulo,
                    font_size=Typography.SIZE_XL,
                    font_weight=Typography.WEIGHT_BOLD,
                    color=Colors.TEXT_PRIMARY,
                ),
                rx.text(
                    subtitulo,
                    font_size=Typography.SIZE_SM,
                    color=Colors.TEXT_MUTED,
                ),
                spacing="1",
                width="100%",
                align_items="start",
            ),
            rx.box(
                height="1px",
                width="100%",
                background=Colors.BORDER,
            ),
            contenido,
            width="100%",
            spacing="4",
            align_items="stretch",
        ),
        width="100%",
        background=Colors.SURFACE,
        border=f"1px solid {Colors.BORDER}",
        border_radius=Radius.XL,
        padding=Spacing.LG,
    )


def _seccion_cuenta() -> rx.Component:
    return _card_seccion(
        "Cuenta",
        "Actualiza tu información básica de acceso.",
        rx.vstack(
            form_input(
                label="Email",
                value=MiPerfilState.email_actual,
                read_only=True,
                disabled=True,
            ),
            form_input(
                label="Nombre completo",
                value=MiPerfilState.form_nombre_completo,
                on_change=MiPerfilState.set_form_nombre_completo,
                error=MiPerfilState.error_nombre_completo,
                required=True,
                placeholder="Nombre completo",
            ),
            form_input(
                label="Teléfono",
                value=MiPerfilState.form_telefono,
                on_change=MiPerfilState.set_form_telefono,
                error=MiPerfilState.error_telefono,
                placeholder="10 dígitos",
                hint="Opcional. Captura 10 dígitos.",
                max_length=10,
                input_mode="numeric",
            ),
            rx.hstack(
                form_input(
                    label="Rol de plataforma",
                    value=MiPerfilState.rol_plataforma_label,
                    read_only=True,
                    disabled=True,
                ),
                form_input(
                    label="Contexto",
                    value=MiPerfilState.contexto_cuenta_label,
                    read_only=True,
                    disabled=True,
                ),
                width="100%",
                gap=Spacing.MD,
                align="start",
                wrap="wrap",
            ),
            rx.hstack(
                rx.spacer(),
                boton_guardar(
                    texto="Guardar cambios",
                    texto_guardando="Guardando...",
                    on_click=MiPerfilState.guardar_perfil,
                    saving=MiPerfilState.guardando_perfil,
                    disabled=~MiPerfilState.puede_guardar_perfil,
                ),
                width="100%",
                align="center",
            ),
            width="100%",
            spacing="3",
            align_items="stretch",
        ),
    )


def _seccion_seguridad() -> rx.Component:
    return _card_seccion(
        "Seguridad",
        "Cambia tu contraseña de acceso.",
        rx.vstack(
            form_input(
                label="Nueva contraseña",
                type="password",
                value=MiPerfilState.form_password_nueva,
                on_change=MiPerfilState.set_form_password_nueva,
                error=MiPerfilState.error_password_nueva,
                hint="Mínimo 8 caracteres.",
                required=True,
            ),
            form_input(
                label="Confirmar contraseña",
                type="password",
                value=MiPerfilState.form_password_confirmacion,
                on_change=MiPerfilState.set_form_password_confirmacion,
                error=MiPerfilState.error_password_confirmacion,
                required=True,
            ),
            rx.hstack(
                rx.spacer(),
                boton_guardar(
                    texto="Actualizar contraseña",
                    texto_guardando="Actualizando...",
                    on_click=MiPerfilState.cambiar_password,
                    saving=MiPerfilState.guardando_password,
                    disabled=~MiPerfilState.puede_cambiar_password,
                    color_scheme="gray",
                ),
                width="100%",
                align="center",
            ),
            width="100%",
            spacing="3",
            align_items="stretch",
        ),
    )


def mi_perfil_page() -> rx.Component:
    """Pantalla de perfil personal compartida para cualquier usuario autenticado."""
    return rx.box(
        page_layout(
            header=page_header(
                titulo="Mi Perfil",
                subtitulo="Administra tu cuenta personal y seguridad",
                icono="user",
            ),
            toolbar=rx.fragment(),
            content=rx.cond(
                MiPerfilState.loading,
                rx.center(rx.spinner(size="3"), padding_y="60px"),
                rx.vstack(
                    _seccion_cuenta(),
                    _seccion_seguridad(),
                    width="100%",
                    spacing="4",
                    padding_top=Spacing.SM,
                ),
            ),
        ),
        width="100%",
        min_height="100vh",
        on_mount=MiPerfilState.on_mount_mi_perfil,
    )
