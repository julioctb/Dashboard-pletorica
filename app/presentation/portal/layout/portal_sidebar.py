"""
Sidebar del portal de cliente.

Sidebar simplificado con solo las secciones relevantes para
usuarios de empresas proveedoras. Muestra la empresa activa
y opciones para cambiar empresa (si tiene multiples asignadas).
"""
import reflex as rx

from app.core.config import Config
from app.presentation.components.shared.auth_state import AuthState
from app.presentation.portal.state.portal_state import PortalState
from app.presentation.components.ui.notification_bell import notification_bell_portal, NotificationBellState
from app.presentation.layout.primitives import nav_group, nav_item
from app.presentation.theme import (
    Colors,
    Spacing,
    Transitions,
    Typography,
)


# =============================================================================
# HELPERS DE VISIBILIDAD
# =============================================================================


def _cond_item(condition, text: str, icon: str, href: str) -> rx.Component:
    """Renderiza un item de navegacion solo si la condicion es verdadera."""
    return rx.cond(condition, nav_item(text=text, icon=icon, href=href), rx.fragment())


def _cond_group(condition, label: str, *items) -> rx.Component:
    """Renderiza un grupo completo solo si la condicion es verdadera."""
    return rx.cond(
        condition,
        nav_group(*items, label=label),
        rx.fragment(),
    )


# =============================================================================
# COMPONENTES
# =============================================================================

def _portal_header() -> rx.Component:
    """Header del sidebar con nombre de la empresa y campana de notificaciones."""
    return rx.hstack(
        rx.center(
            rx.icon("building-2", size=20, color=Colors.PORTAL_PRIMARY),
            width="36px",
            height="36px",
            border_radius="8px",
            background=Colors.PORTAL_PRIMARY_LIGHT,
            flex_shrink="0",
        ),
        rx.vstack(
            rx.text(
                PortalState.nombre_empresa_actual,
                font_size=Typography.SIZE_SM,
                font_weight=Typography.WEIGHT_BOLD,
                color=Colors.TEXT_PRIMARY,
                line_height="1.2",
                white_space="nowrap",
                overflow="hidden",
                text_overflow="ellipsis",
                max_width="130px",
            ),
            rx.text(
                rx.cond(AuthState.es_empleado_portal, "Portal Empleado", "Portal Cliente"),
                font_size=Typography.SIZE_XS,
                color=Colors.TEXT_MUTED,
                line_height="1.2",
            ),
            spacing="0",
            align_items="start",
        ),
        rx.spacer(),
        notification_bell_portal(),
        padding_x=Spacing.MD,
        padding_y=Spacing.LG,
        align="center",
        width="100%",
        gap=Spacing.SM,
    )


def _portal_navigation() -> rx.Component:
    """Navegacion completa del portal, filtrada por rol_empresa."""
    return rx.vstack(
        # --- Dashboard (siempre visible) ---
        nav_group(nav_item(text="Dashboard", icon="layout-dashboard", href="/portal")),
        # --- Mi Empresa (admin_empresa, rrhh) ---
        _cond_group(
            AuthState.es_rrhh | AuthState.es_admin_empresa,
            "Mi Empresa",
            _cond_item(AuthState.es_admin_empresa, "Datos Empresa", "building-2", "/portal/mi-empresa"),
            _cond_item(AuthState.puede_gestionar_personal, "Empleados", "users", "/portal/empleados"),
            _cond_item(AuthState.puede_gestionar_personal, "Alta Masiva", "upload", "/portal/alta-masiva"),
            _cond_item(AuthState.puede_configurar_empresa, "Configuracion", "settings", "/portal/configuracion-empresa"),
        ),
        # --- RRHH (puede_registrar_personal) ---
        _cond_group(
            AuthState.puede_registrar_personal,
            "RRHH",
            _cond_item(AuthState.puede_registrar_personal, "Alta Empleados", "user-plus", "/portal/onboarding"),
            _cond_item(AuthState.es_rrhh, "Expedientes", "folder-check", "/portal/expedientes"),
        ),
        # --- Autoservicio (siempre visible) ---
        nav_group(
            nav_item(text="Mis Datos", icon="user-check", href="/portal/mis-datos"),
            label="Autoservicio",
        ),
        # --- Operacion (operaciones, contabilidad, admin_empresa) ---
        _cond_group(
            AuthState.es_operaciones | AuthState.es_contabilidad,
            "Operacion",
            _cond_item(AuthState.es_operaciones, "Contratos", "file-text", "/portal/contratos"),
            _cond_item(AuthState.es_operaciones | AuthState.es_contabilidad, "Entregables", "package-check", "/portal/entregables"),
            _cond_item(AuthState.es_rrhh, "Plazas", "briefcase", "/portal/plazas"),
            _cond_item(AuthState.es_operaciones, "Requisiciones", "clipboard-list", "/portal/requisiciones"),
        ),
        spacing="0",
        width="100%",
        flex="1",
        overflow_y="auto",
        padding_x=Spacing.XS,
    )


def _portal_user_section() -> rx.Component:
    """Seccion de usuario en el footer del sidebar."""
    return rx.vstack(
        rx.box(
            height="1px",
            background=Colors.BORDER,
            width="100%",
        ),
        rx.menu.root(
            rx.menu.trigger(
                rx.hstack(
                    rx.center(
                        rx.icon("user", size=18, color=Colors.PORTAL_PRIMARY),
                        width="32px",
                        height="32px",
                        border_radius="50%",
                        background=Colors.PORTAL_PRIMARY_LIGHT,
                        flex_shrink="0",
                    ),
                    rx.vstack(
                        rx.text(
                            PortalState.nombre_usuario,
                            font_size=Typography.SIZE_SM,
                            font_weight=Typography.WEIGHT_MEDIUM,
                            color=Colors.TEXT_PRIMARY,
                            white_space="nowrap",
                            overflow="hidden",
                            text_overflow="ellipsis",
                            max_width="140px",
                        ),
                        rx.text(
                            PortalState.email_usuario,
                            font_size=Typography.SIZE_XS,
                            color=Colors.TEXT_MUTED,
                            white_space="nowrap",
                            overflow="hidden",
                            text_overflow="ellipsis",
                            max_width="140px",
                        ),
                        spacing="0",
                        align_items="start",
                    ),
                    rx.spacer(),
                    rx.icon("chevrons-up-down", size=14, color=Colors.TEXT_MUTED),
                    width="100%",
                    align="center",
                    padding_x=Spacing.SM,
                    padding_y=Spacing.SM,
                    gap=Spacing.SM,
                    border_radius="8px",
                    cursor="pointer",
                    transition=Transitions.FAST,
                    style={
                        "_hover": {
                            "background": Colors.SIDEBAR_ITEM_HOVER,
                        },
                    },
                ),
            ),
            rx.menu.content(
                rx.menu.item(
                    rx.hstack(
                        rx.icon("user", size=14),
                        rx.text("Mi Perfil"),
                        spacing="2",
                        align="center",
                    ),
                    on_click=rx.redirect("/portal/mis-datos"),
                ),
                rx.menu.separator(),
                rx.menu.item(
                    rx.hstack(
                        rx.icon("log-out", size=14),
                        rx.text("Cerrar sesion"),
                        spacing="2",
                        align="center",
                    ),
                    color=Colors.ERROR,
                    on_click=PortalState.cerrar_sesion,
                ),
                side="top",
                align="start",
            ),
        ),
        width="100%",
        spacing="0",
        padding_x=Spacing.XS,
        padding_y=Spacing.SM,
    )


# =============================================================================
# DEV SIMULATION BANNER
# =============================================================================

def _dev_simulation_banner() -> rx.Component:
    """
    Banner rojo SIMULACION con botón Volver a Admin.
    Solo visible si Config.DEBUG y AuthState.simulando_cliente.
    """
    if not Config.DEBUG:
        return rx.fragment()

    return rx.cond(
        AuthState.simulando_cliente,
        rx.vstack(
            rx.hstack(
                rx.icon("bug", size=14, color=Colors.TEXT_INVERSE),
                rx.text(
                    "SIMULACION",
                    font_size="11px",
                    font_weight=Typography.WEIGHT_BOLD,
                    color=Colors.TEXT_INVERSE,
                    letter_spacing=Typography.LETTER_SPACING_WIDE,
                ),
                align="center",
                justify="center",
                gap="2",
            ),
            rx.button(
                rx.icon("arrow-left", size=14),
                rx.text("Volver a Admin", font_size="12px"),
                size="1",
                variant="outline",
                color_scheme="red",
                width="100%",
                on_click=AuthState.desactivar_simulacion_cliente,
                cursor="pointer",
                style={
                    "color": Colors.TEXT_INVERSE,
                    "border_color": "var(--red-7)",
                    "_hover": {"background": "var(--red-8)"},
                },
            ),
            width="100%",
            padding=Spacing.SM,
            background="var(--red-9)",
            spacing="2",
            align_items="center",
        ),
        rx.fragment(),
    )


# =============================================================================
# SIDEBAR COMPLETO DEL PORTAL
# =============================================================================

def portal_sidebar() -> rx.Component:
    """
    Sidebar completo del portal de cliente.

    Uso:
        def portal_index(content):
            return rx.hstack(
                portal_sidebar(),
                rx.box(content, flex="1"),
            )
    """
    return rx.box(
        rx.vstack(
            _dev_simulation_banner(),
            _portal_header(),
            _portal_navigation(),
            _portal_user_section(),
            height="100vh",
            width="100%",
            spacing="0",
            align_items="stretch",
        ),
        width="240px",
        min_width="240px",
        height="100vh",
        background=Colors.SURFACE,
        border_right=f"1px solid {Colors.BORDER}",
        flex_shrink="0",
        on_mount=NotificationBellState.cargar_notificaciones_portal,
    )
