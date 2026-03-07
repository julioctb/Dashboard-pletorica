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
from app.presentation.layout.primitives import nav_group, nav_item, route_is_active
from app.presentation.theme import (
    Colors,
    Radius,
    Spacing,
    Transitions,
    Typography,
)


# =============================================================================
# HELPERS DE VISIBILIDAD
# =============================================================================


def _cond_item(
    condition,
    text: str,
    icon: str,
    href: str,
    *,
    active_paths: tuple[str, ...] | None = None,
) -> rx.Component:
    """Renderiza un item de navegacion solo si la condicion es verdadera."""
    rutas_activas = active_paths or (href,)
    return rx.cond(
        condition,
        nav_item(
            text=text,
            icon=icon,
            href=href,
            is_active=route_is_active(
                PortalState.router.route_id,
                rutas_activas[0],
                *rutas_activas[1:],
            ),
        ),
        rx.fragment(),
    )


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
    """Header del sidebar con nombre y selector de empresa."""
    return rx.vstack(
        rx.hstack(
            rx.center(
                rx.icon("building-2", size=20, color=Colors.PORTAL_PRIMARY),
                width="36px",
                height="36px",
                border_radius=Radius.LG,
                background=Colors.PORTAL_PRIMARY_LIGHT,
                flex_shrink="0",
            ),
            rx.vstack(
                rx.text(
                    PortalState.nombre_empresa_actual,
                    font_size=Typography.SIZE_SM,
                    font_weight=Typography.WEIGHT_BOLD,
                    color=Colors.TEXT_PRIMARY,
                    line_height=Typography.LINE_HEIGHT_TIGHT,
                    white_space="nowrap",
                    overflow="hidden",
                    text_overflow="ellipsis",
                    width="100%",
                ),
                rx.text(
                    rx.cond(
                        AuthState.es_empleado_portal,
                        "Portal Empleado",
                        "Portal Cliente",
                    ),
                    font_size=Typography.SIZE_XS,
                    color=Colors.TEXT_MUTED,
                    line_height=Typography.LINE_HEIGHT_TIGHT,
                ),
                spacing="0",
                align_items="start",
                flex="1",
                min_width="0",
            ),
            align="center",
            width="100%",
            gap=Spacing.SM,
        ),
        rx.hstack(
            rx.cond(
                AuthState.tiene_multiples_empresas,
                rx.select.root(
                    rx.select.trigger(
                        placeholder="Seleccionar empresa...",
                        width="100%",
                    ),
                    rx.select.content(
                        rx.foreach(
                            AuthState.empresas_disponibles,
                            lambda emp: rx.select.item(
                                emp["empresa_nombre"],
                                value=emp["empresa_id"].to(str),
                            ),
                        ),
                    ),
                    value=AuthState.id_empresa_actual.to(str),
                    on_change=PortalState.cambiar_empresa_portal,
                    size="1",
                ),
                rx.fragment(),
            ),
            width="100%",
        ),
        padding_x=Spacing.MD,
        padding_y=Spacing.LG,
        width="100%",
        spacing="2",
    )


def _portal_navigation() -> rx.Component:
    """Navegación del portal alineada con las secciones funcionales."""
    return rx.vstack(
        # Dashboard (siempre visible)
        nav_group(
            nav_item(
                text="Dashboard",
                icon="layout-dashboard",
                href="/portal",
                is_active=route_is_active(PortalState.router.route_id, "/portal"),
            ),
        ),
        # Comercial: cotizador, contratos, entregables, reportes
        _cond_group(
            PortalState.mostrar_seccion_contrato,
            "Comercial",
            _cond_item(
                AuthState.es_admin_empresa,
                "Cotizador",
                "file-spreadsheet",
                "/portal/cotizador",
            ),
            _cond_item(
                PortalState.mostrar_seccion_contrato,
                "Contratos",
                "file-text",
                "/portal/contratos",
            ),
            _cond_item(
                PortalState.mostrar_seccion_entregables,
                "Entregables",
                "package-check",
                "/portal/entregables",
            ),
        ),
        # RRHH: empleados, asistencias
        _cond_group(
            PortalState.mostrar_seccion_rrhh,
            "RRHH",
            _cond_item(
                AuthState.puede_gestionar_personal,
                "Empleados",
                "users",
                "/portal/empleados",
                active_paths=(
                    "/portal/empleados",
                    "/portal/empleados/expedientes",
                ),
            ),
            _cond_item(AuthState.es_rrhh, "Plazas", "briefcase", "/portal/plazas"),
            _cond_item(AuthState.puede_registrar_personal, "Contrataciones", "user-plus", "/portal/onboarding"),
            _cond_item(AuthState.es_rrhh, "Bajas", "user-minus", "/portal/bajas"),
            _cond_item(
                AuthState.es_operaciones | AuthState.es_rrhh | AuthState.es_admin_empresa,
                "Asistencias",
                "clipboard-check",
                "/portal/asistencias",
            ),
        ),
        # Nóminas (RRHH)
        _cond_group(
            PortalState.mostrar_seccion_nominas,
            "Nóminas",
            _cond_item(PortalState.mostrar_seccion_nominas, "Períodos", "calculator", "/portal/nominas"),
            _cond_item(PortalState.mostrar_seccion_nominas, "Preparación", "folder-open", "/portal/nominas/preparacion"),
        ),
        # Contabilidad
        _cond_group(
            PortalState.mostrar_seccion_contabilidad,
            "Contabilidad",
            _cond_item(PortalState.mostrar_seccion_contabilidad, "Cálculo", "calculator", "/portal/nominas/calculo"),
            _cond_item(PortalState.mostrar_seccion_contabilidad, "Conciliación", "file-check", "/portal/nominas/conciliacion"),
        ),
        # Empresa: datos, usuarios, configuracion
        _cond_group(
            PortalState.mostrar_seccion_empresa,
            "Empresa",
            _cond_item(
                PortalState.mostrar_seccion_empresa,
                "Datos empresa",
                "building-2",
                "/portal/mi-empresa",
            ),
            _cond_item(AuthState.es_admin_empresa, "Usuarios", "users-round", "/portal/usuarios"),
            _cond_item(AuthState.puede_configurar_empresa, "Configuracion", "settings", "/portal/configuracion-empresa"),
        ),
        # Auto servicio (empleados)
        _cond_group(
            PortalState.mostrar_seccion_autoservicio,
            "Auto servicio",
            _cond_item(
                PortalState.mostrar_seccion_autoservicio,
                "Mis datos",
                "user-check",
                "/portal/mis-datos",
            ),
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
                    on_click=rx.redirect("/portal/mi-perfil"),
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


def _portal_notification_section() -> rx.Component:
    """Campana del portal ubicada sobre el bloque de usuario."""
    return rx.box(
        notification_bell_portal(trigger_variant="sidebar_item"),
        width="100%",
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
                    font_size=Typography.SIZE_XS,
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
                rx.text("Volver a Admin", font_size=Typography.SIZE_XS),
                size="1",
                variant="outline",
                color_scheme="red",
                width="100%",
                on_click=AuthState.desactivar_simulacion_cliente,
                cursor="pointer",
                style={
                    "color": Colors.TEXT_INVERSE,
                    "border_color": Colors.ERROR_HOVER,
                    "_hover": {"background": Colors.ERROR_HOVER},
                },
            ),
            width="100%",
            padding=Spacing.SM,
            background=Colors.ERROR,
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
            _portal_notification_section(),
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
