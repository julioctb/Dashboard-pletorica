"""
Sidebar del portal de cliente.

Sidebar simplificado con solo las secciones relevantes para
usuarios de empresas proveedoras. Muestra la empresa activa
y opciones para cambiar empresa (si tiene multiples asignadas).
"""
import reflex as rx

from app.core.config import Config
from app.presentation.components.ui.notification_bell import (
    NotificationBellState,
    notification_bell_portal,
)
from app.presentation.components.shared.auth_state import AuthState
from app.presentation.layouts.backoffice.primitives import nav_item, route_is_active
from app.presentation.pages.portal.state.portal_state import PortalState
from app.presentation.theme import (
    Colors,
    Layout,
    Radius,
    Spacing,
    Transitions,
    Typography,
)


# =============================================================================
# HELPERS
# =============================================================================


def _sidebar_section_label(label: str) -> rx.Component:
    """Etiqueta de sección consistente con el sistema del portal."""
    return rx.text(
        label,
        font_size=Typography.SIZE_XS,
        font_weight=Typography.WEIGHT_SEMIBOLD,
        color=Colors.TEXT_MUTED,
        text_transform="uppercase",
        letter_spacing=Typography.LETTER_SPACING_SECTION_LABEL,
        padding_x=Spacing.BASE,
        padding_top=Spacing.LG,
        padding_bottom=Spacing.XS,
    )


def _sidebar_divider() -> rx.Component:
    """Separador visual entre herramientas y flujo operativo."""
    return rx.box(
        height="1px",
        background=Colors.BORDER,
        margin_x=Spacing.BASE,
        margin_y=Spacing.XS,
        width="auto",
    )


def _sidebar_item(
    text: str,
    icon: str,
    href: str,
    *,
    active_paths: tuple[str, ...] | None = None,
    padding_left: str | None = None,
) -> rx.Component:
    """Item base del sidebar portal."""
    rutas_activas = active_paths or (href,)
    return nav_item(
        text=text,
        icon=icon,
        href=href,
        is_active=route_is_active(
            PortalState.router.route_id,
            rutas_activas[0],
            *rutas_activas[1:],
        ),
        icon_color=Colors.TEXT_SECONDARY,
        text_color=Colors.TEXT_SECONDARY,
        hover_bg=Colors.PORTAL_PRIMARY_LIGHTER,
        active_bg=Colors.PORTAL_PRIMARY_LIGHT,
        active_text=Colors.PORTAL_PRIMARY_TEXT,
        padding_x=Spacing.BASE,
        padding_left=padding_left,
        padding_right=Spacing.BASE if padding_left is not None else None,
    )


def _cond_item(condition, component: rx.Component) -> rx.Component:
    """Renderiza un item solo si la condición es verdadera."""
    return rx.cond(condition, component, rx.fragment())


# =============================================================================
# COMPONENTES
# =============================================================================

def _portal_header() -> rx.Component:
    """Header del sidebar con nombre y selector de empresa."""
    return rx.vstack(
        rx.hstack(
            rx.center(
                rx.icon("building-2", size=20, color=Colors.PORTAL_PRIMARY_TEXT),
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
            notification_bell_portal(trigger_variant="icon"),
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
        _sidebar_item("Dashboard", "layout-dashboard", "/portal"),
        rx.cond(
            PortalState.mostrar_herramientas,
            rx.fragment(
                _sidebar_section_label("Herramientas"),
                _sidebar_item("Simulador", "calculator", "/portal/simulador"),
                _sidebar_item("Cotizador", "file-spreadsheet", "/portal/cotizador"),
                _sidebar_divider(),
            ),
            rx.fragment(),
        ),
        rx.cond(
            PortalState.mostrar_seccion_contrato,
            rx.fragment(
                _sidebar_section_label("Contratos"),
                _sidebar_item(
                    "Contratos",
                    "file-text",
                    "/portal/contratos",
                    active_paths=(
                        "/portal/contratos",
                        "/portal/contratos/[codigo_contrato]/plazas",
                    ),
                ),
                _cond_item(
                    PortalState.mostrar_entregables,
                    _sidebar_item(
                        "Entregables",
                        "package-check",
                        "/portal/entregables",
                    ),
                ),
            ),
            rx.fragment(),
        ),
        rx.cond(
            PortalState.mostrar_personal,
            rx.fragment(
                _sidebar_section_label("Personal"),
                _cond_item(
                    AuthState.puede_gestionar_personal | AuthState.puede_registrar_personal,
                    _sidebar_item(
                        "Empleados",
                        "users",
                        "/portal/empleados",
                        active_paths=(
                            "/portal/empleados",
                            "/portal/empleados/[id]",
                            "/portal/onboarding",
                        ),
                    ),
                ),
                _cond_item(
                    AuthState.puede_acceder_rrhh,
                    _sidebar_item(
                        "Incapacidades",
                        "heart-pulse",
                        "/portal/incapacidades",
                    ),
                ),
                _cond_item(
                    AuthState.puede_acceder_rrhh,
                    _sidebar_item("Bajas", "user-minus", "/portal/bajas"),
                ),
                _cond_item(
                    AuthState.es_operaciones | AuthState.puede_acceder_rrhh,
                    _sidebar_item(
                        "Asistencias",
                        "clipboard-check",
                        "/portal/asistencias",
                    ),
                ),
            ),
            rx.fragment(),
        ),
        rx.cond(
            PortalState.mostrar_nomina,
            rx.fragment(
                _sidebar_section_label("Nómina"),
                _sidebar_item("Períodos", "calendar", "/portal/nominas"),
                _cond_item(
                    PortalState.mostrar_seccion_nominas,
                    _sidebar_item(
                        "Preparación",
                        "folder-open",
                        "/portal/nominas/preparacion",
                    ),
                ),
                _cond_item(
                    PortalState.mostrar_seccion_contabilidad,
                    _sidebar_item(
                        "Cálculo",
                        "calculator",
                        "/portal/nominas/calculo",
                    ),
                ),
                _cond_item(
                    PortalState.mostrar_seccion_contabilidad,
                    _sidebar_item(
                        "Conciliación",
                        "file-check",
                        "/portal/nominas/conciliacion",
                    ),
                ),
            ),
            rx.fragment(),
        ),
        rx.cond(
            PortalState.mostrar_seccion_empresa,
            rx.fragment(
                _sidebar_section_label("Empresa"),
                _sidebar_item("Datos empresa", "building-2", "/portal/mi-empresa"),
                _cond_item(
                    AuthState.es_admin_empresa | AuthState.puede_acceder_rrhh,
                    _sidebar_item(
                        "Catálogo de servicios",
                        "briefcase",
                        "/portal/empresa/categorias",
                    ),
                ),
                _cond_item(
                    AuthState.es_admin_empresa,
                    _sidebar_item(
                        "Documentación",
                        "folder-lock",
                        "/portal/documentacion-empresa",
                    ),
                ),
                _cond_item(
                    AuthState.es_admin_empresa,
                    _sidebar_item("Usuarios", "users-round", "/portal/usuarios"),
                ),
                _cond_item(
                    AuthState.puede_configurar_empresa,
                    _sidebar_item(
                        "Configuración",
                        "settings",
                        "/portal/configuracion-empresa",
                    ),
                ),
            ),
            rx.fragment(),
        ),
        rx.cond(
            PortalState.mostrar_seccion_autoservicio,
            rx.fragment(
                _sidebar_section_label("Auto servicio"),
                _sidebar_item(
                    "Mis datos",
                    "user-check",
                    "/portal/mis-datos",
                ),
            ),
            rx.fragment(),
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
                        rx.icon("user", size=18, color=Colors.PORTAL_PRIMARY_TEXT),
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
                    border_radius=Radius.LG,
                    cursor="pointer",
                    transition=Transitions.FAST,
                    style={
                        "_hover": {
                            "background": Colors.PORTAL_PRIMARY_LIGHTER,
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
            _portal_user_section(),
            height="100vh",
            width="100%",
            spacing="0",
            align_items="stretch",
        ),
        width=Layout.SIDEBAR_WIDTH,
        min_width=Layout.SIDEBAR_MIN_WIDTH,
        height="100vh",
        background=Colors.SURFACE,
        border_right=f"1px solid {Colors.BORDER}",
        flex_shrink="0",
        on_mount=[
            NotificationBellState.cargar_notificaciones_portal,
        ],
    )
