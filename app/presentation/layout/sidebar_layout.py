"""
Sidebar Layout - Sidebar Colapsable
====================================

Sidebar responsive con soporte para colapso a modo icono-only.
Agrupa items por categoria y muestra indicador de pagina activa.
Incluye seccion de usuario logueado y grupo de administracion (solo admins).

Caracteristicas:
- Colapsa de 240px a 72px
- Transicion suave de 200ms
- Tooltips en modo colapsado
- Grupos de navegacion (Operacion, Catalogos, Herramientas, Administracion)
- Seccion de usuario con menu (perfil, cerrar sesion)
- Indicador visual de pagina activa

Uso:
    from app.presentation.layout import sidebar

    def index(content):
        return rx.hstack(
            sidebar(),
            rx.box(content, ...),
        )
"""

import reflex as rx
from app.core.config import Config
from app.presentation.components.shared.auth_state import AuthState
from app.presentation.layout.sidebar_state import SidebarState
from app.presentation.layout.primitives import collapsible_nav_item, nav_group, nav_group_label
from app.presentation.components.ui.notification_bell import notification_bell, NotificationBellState
from app.presentation.theme import (
    Colors,
    Spacing,
    Transitions,
    Typography,
    Shadows,
)


# =============================================================================
# CONFIGURACION DE NAVEGACION
# =============================================================================

# Estructura de navegacion agrupada
NAVIGATION_GROUPS = [
    {
        "label": None,  # Sin etiqueta = item suelto
        "items": [
            {"text": "Dashboard", "icon": "layout-dashboard", "href": "/"},
        ],
    },
    {
        "label": "Operacion",
        "items": [
            {"text": "Requisiciones", "icon": "clipboard-list", "href": "/requisiciones"},
            {"text": "Contratos", "icon": "file-text", "href": "/contratos"},
            {"text": "Entregables", "icon": "package-check", "href": "/entregables"},
            {"text": "Pagos", "icon": "credit-card", "href": "/pagos"},
            {"text": "Empresas", "icon": "building-2", "href": "/empresas"},
            {"text": "Sedes", "icon": "map-pin-house", "href": "/sedes"},
        ],
    },
    {
        "label": "Personal",
        "items": [
            {"text": "Empleados", "icon": "users", "href": "/empleados"},
            {"text": "Onboarding", "icon": "user-plus", "href": "/admin/onboarding"},
            {"text": "Historial", "icon": "history", "href": "/historial-laboral"},
        ],
    },
    {
        "label": "Catalogos",
        "items": [
            {"text": "Tipos de Servicio", "icon": "briefcase", "href": "/tipos-servicio"},
            {"text": "Categorias Puesto", "icon": "folder", "href": "/categorias-puesto"},
            {"text": "Plazas", "icon": "briefcase", "href": "/plazas"},
        ],
    },
    {
        "label": "Herramientas",
        "items": [
            {"text": "Simulador", "icon": "calculator", "href": "/simulador"},
        ],
    },
]

# Grupo de administracion (solo visible para admins)
ADMIN_NAVIGATION_GROUP = {
    "label": "Administracion",
    "items": [
        {"text": "Usuarios", "icon": "shield", "href": "/admin/usuarios"},
        {"text": "Instituciones", "icon": "building", "href": "/admin/instituciones"},
    ],
}


# =============================================================================
# COMPONENTES DEL SIDEBAR
# =============================================================================

def sidebar_header() -> rx.Component:
    """
    Header del sidebar con logo, titulo y campana de notificaciones.
    En modo colapsado solo muestra el logo.
    """
    return rx.hstack(
        # Logo
        rx.image(
            src="/logo_reflex.jpg",  # Cambiar por logo real
            width="36px",
            height="36px",
            border_radius="8px",
            flex_shrink="0",
        ),
        # Titulo (solo visible expandido)
        rx.cond(
            SidebarState.is_collapsed,
            rx.fragment(),
            rx.hstack(
                rx.vstack(
                    rx.text(
                        "BUAP",
                        font_size=Typography.SIZE_LG,
                        font_weight=Typography.WEIGHT_BOLD,
                        color=Colors.TEXT_PRIMARY,
                        line_height="1.2",
                    ),
                    rx.text(
                        "Sistema de Gestion",
                        font_size=Typography.SIZE_XS,
                        color=Colors.TEXT_SECONDARY,
                        line_height="1.2",
                    ),
                    spacing="0",
                    align_items="start",
                ),
                rx.spacer(),
                notification_bell(),
                align="center",
                flex="1",
            ),
        ),
        padding_x=Spacing.MD,
        padding_y=Spacing.LG,
        align="center",
        justify=rx.cond(SidebarState.is_collapsed, "center", "start"),
        width="100%",
        gap=Spacing.SM,
    )


def sidebar_item(text: str, icon: str, href: str, badge: rx.Component = None) -> rx.Component:
    """
    Item de navegacion individual.
    Muestra tooltip en modo colapsado.
    Soporta badge opcional para alertas.
    """
    return collapsible_nav_item(
        text=text,
        icon=icon,
        href=href,
        is_collapsed=SidebarState.is_collapsed,
        badge=badge,
    )


def sidebar_group_label(label: str) -> rx.Component:
    """
    Etiqueta de grupo de navegacion.
    Solo visible cuando el sidebar esta expandido.
    """
    return rx.cond(
        ~SidebarState.is_collapsed,
        nav_group_label(label),
        # En modo colapsado, mostrar separador sutil
        rx.box(
            height="1px",
            background=Colors.BORDER,
            margin_y=Spacing.SM,
            margin_x=Spacing.MD,
        ),
    )


def _entregables_badge() -> rx.Component:
    """Badge de alertas para el item de Entregables."""
    return rx.cond(
        SidebarState.tiene_alertas_entregables,
        rx.badge(
            SidebarState.entregables_pendientes,
            color_scheme="red",
            variant="solid",
            size="1",
        ),
        rx.fragment(),
    )


def sidebar_group(group: dict) -> rx.Component:
    """
    Renderiza un grupo de navegacion con su etiqueta e items.
    """
    items = []
    for item in group["items"]:
        # Item especial para Entregables con badge
        if item["text"] == "Entregables":
            items.append(
                sidebar_item(
                    text=item["text"],
                    icon=item["icon"],
                    href=item["href"],
                    badge=_entregables_badge(),
                )
            )
        else:
            items.append(
                sidebar_item(
                    text=item["text"],
                    icon=item["icon"],
                    href=item["href"],
                )
            )

    if group["label"]:
        return nav_group(
            *items,
            label=group["label"],
        )
    else:
        return nav_group(*items)


def sidebar_admin_group() -> rx.Component:
    """
    Grupo de administracion, solo visible para usuarios con rol admin.
    """
    admin_group = sidebar_group(ADMIN_NAVIGATION_GROUP)
    return rx.cond(
        SidebarState.es_admin,
        admin_group,
        rx.fragment(),
    )


def sidebar_navigation() -> rx.Component:
    """
    Contenedor principal de navegacion con todos los grupos.
    Incluye grupo de administracion condicional para admins.
    """
    groups = [sidebar_group(group) for group in NAVIGATION_GROUPS]

    return rx.vstack(
        *groups,
        sidebar_admin_group(),
        spacing="0",
        width="100%",
        flex="1",
        overflow_y="auto",
        padding_x=Spacing.XS,
    )


def sidebar_toggle_button() -> rx.Component:
    """
    Boton para colapsar/expandir el sidebar.
    """
    return rx.tooltip(
        rx.icon_button(
            rx.icon(SidebarState.toggle_icon, size=16),
            size="1",
            variant="ghost",
            color_scheme="gray",
            on_click=SidebarState.toggle,
            cursor="pointer",
            style={
                "position": "absolute",
                "right": "-12px",
                "top": "72px",
                "z_index": "10",
                "background": Colors.SURFACE,
                "border": f"1px solid {Colors.BORDER}",
                "border_radius": "50%",
                "box_shadow": Shadows.SM,
                "_hover": {
                    "background": Colors.SECONDARY_LIGHT,
                },
            },
        ),
        content=SidebarState.toggle_tooltip,
        side="right",
    )


# =============================================================================
# SECCION DE USUARIO
# =============================================================================

def _user_avatar() -> rx.Component:
    """Avatar del usuario (icono con iniciales en circulo)."""
    return rx.center(
        rx.icon("user", size=18, color="var(--accent-9)"),
        width="32px",
        height="32px",
        border_radius="50%",
        background="var(--accent-3)",
        flex_shrink="0",
    )


def _user_section_expanded() -> rx.Component:
    """Seccion de usuario cuando el sidebar esta expandido."""
    return rx.menu.root(
        rx.menu.trigger(
            rx.hstack(
                _user_avatar(),
                rx.vstack(
                    rx.text(
                        SidebarState.nombre_usuario,
                        font_size=Typography.SIZE_SM,
                        font_weight=Typography.WEIGHT_MEDIUM,
                        color=Colors.TEXT_PRIMARY,
                        white_space="nowrap",
                        overflow="hidden",
                        text_overflow="ellipsis",
                        max_width="140px",
                    ),
                    rx.text(
                        SidebarState.nombre_empresa_actual,
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
            # Info del usuario (no clickeable)
            rx.box(
                rx.text(
                    SidebarState.email_usuario,
                    font_size=Typography.SIZE_XS,
                    color=Colors.TEXT_MUTED,
                ),
                padding_x="12px",
                padding_y="8px",
            ),
            rx.menu.separator(),
            # Configuracion
            rx.menu.item(
                rx.hstack(
                    rx.icon("settings", size=14),
                    rx.text("Configuracion"),
                    spacing="2",
                    align="center",
                ),
                on_click=rx.redirect("/configuracion"),
            ),
            rx.menu.separator(),
            # Cerrar sesion
            rx.menu.item(
                rx.hstack(
                    rx.icon("log-out", size=14),
                    rx.text("Cerrar sesion"),
                    spacing="2",
                    align="center",
                ),
                color="red",
                on_click=SidebarState.cerrar_sesion,
            ),
            side="top",
            align="start",
        ),
    )


def _user_section_collapsed() -> rx.Component:
    """Seccion de usuario cuando el sidebar esta colapsado."""
    return rx.menu.root(
        rx.menu.trigger(
            rx.center(
                _user_avatar(),
                width="100%",
                padding_y=Spacing.SM,
                cursor="pointer",
                border_radius="8px",
                transition=Transitions.FAST,
                style={
                    "_hover": {
                        "background": Colors.SIDEBAR_ITEM_HOVER,
                    },
                },
            ),
        ),
        rx.menu.content(
            # Info del usuario
            rx.box(
                rx.text(
                    SidebarState.nombre_usuario,
                    font_size=Typography.SIZE_SM,
                    font_weight=Typography.WEIGHT_MEDIUM,
                ),
                rx.text(
                    SidebarState.nombre_empresa_actual,
                    font_size=Typography.SIZE_XS,
                    color=Colors.TEXT_MUTED,
                ),
                padding_x="12px",
                padding_y="8px",
            ),
            rx.menu.separator(),
            rx.menu.item(
                rx.hstack(
                    rx.icon("settings", size=14),
                    rx.text("Configuracion"),
                    spacing="2",
                    align="center",
                ),
                on_click=rx.redirect("/configuracion"),
            ),
            rx.menu.separator(),
            rx.menu.item(
                rx.hstack(
                    rx.icon("log-out", size=14),
                    rx.text("Cerrar sesion"),
                    spacing="2",
                    align="center",
                ),
                color="red",
                on_click=SidebarState.cerrar_sesion,
            ),
            side="right",
            align="end",
        ),
    )


def sidebar_user_section() -> rx.Component:
    """
    Seccion de usuario en la parte inferior del sidebar.
    Muestra avatar, nombre y empresa actual con menu desplegable.
    En modo colapsado muestra solo el avatar con menu.
    """
    return rx.vstack(
        # Separador
        rx.box(
            height="1px",
            background=Colors.BORDER,
            width="100%",
        ),
        # Contenido segun estado del sidebar
        rx.box(
            rx.cond(
                SidebarState.is_collapsed,
                _user_section_collapsed(),
                _user_section_expanded(),
            ),
            width="100%",
            padding_x=Spacing.XS,
            padding_y=Spacing.SM,
        ),
        width="100%",
        spacing="0",
    )


# =============================================================================
# DEV VIEW SWITCHER (solo DEBUG)
# =============================================================================

def _dev_view_switcher() -> rx.Component:
    """
    Switcher Admin/Cliente para desarrollo.
    Solo se renderiza cuando Config.DEBUG=True.
    Permite simular la vista de portal de cliente con una empresa real.
    """
    if not Config.DEBUG:
        return rx.fragment()

    # Botón Admin
    btn_admin = rx.button(
        rx.icon("shield", size=14),
        rx.cond(~SidebarState.is_collapsed, rx.text("Admin", font_size="12px"), rx.fragment()),
        size="1",
        variant=rx.cond(~AuthState.dev_modo_cliente_activo, "solid", "outline"),
        color_scheme="gray",
        on_click=AuthState.on_dev_view_change("admin"),
        flex="1",
        cursor="pointer",
    )

    # Botón Cliente
    btn_cliente = rx.button(
        rx.icon("building-2", size=14),
        rx.cond(~SidebarState.is_collapsed, rx.text("Cliente", font_size="12px"), rx.fragment()),
        size="1",
        variant=rx.cond(AuthState.dev_modo_cliente_activo, "solid", "outline"),
        color_scheme="teal",
        on_click=AuthState.on_dev_view_change("cliente"),
        flex="1",
        cursor="pointer",
    )

    # Select de empresas (solo visible in modo cliente expandido)
    empresa_select = rx.cond(
        AuthState.dev_modo_cliente_activo & ~SidebarState.is_collapsed,
        rx.select.root(
            rx.select.trigger(placeholder="Seleccionar empresa...", width="100%"),
            rx.select.content(
                rx.foreach(
                    AuthState.opciones_empresas_simulacion,
                    lambda opt: rx.select.item(opt["label"], value=opt["value"]),
                ),
            ),
            value=AuthState.valor_empresa_simulada,
            on_change=AuthState.activar_simulacion_cliente,
            size="1",
        ),
        rx.fragment(),
    )

    # Versión expandida
    expanded = rx.vstack(
        rx.text(
            "DEV VIEW",
            font_size="10px",
            font_weight=Typography.WEIGHT_BOLD,
            color="var(--red-9)",
            letter_spacing=Typography.LETTER_SPACING_WIDE,
        ),
        rx.hstack(
            btn_admin,
            btn_cliente,
            width="100%",
            gap=Spacing.XS,
        ),
        empresa_select,
        width="100%",
        spacing="2",
        padding=Spacing.SM,
        background="var(--red-2)",
        border_radius="8px",
        border="1px dashed var(--red-6)",
    )

    # Versión colapsada: solo icono bug con tooltip
    collapsed = rx.tooltip(
        rx.center(
            rx.icon("bug", size=16, color="var(--red-9)"),
            width="36px",
            height="36px",
            border_radius="8px",
            background="var(--red-2)",
            border="1px dashed var(--red-6)",
            cursor="pointer",
        ),
        content="Dev View Switcher",
        side="right",
    )

    return rx.box(
        rx.cond(SidebarState.is_collapsed, collapsed, expanded),
        width="100%",
        padding_x=Spacing.XS,
    )


# =============================================================================
# FOOTER
# =============================================================================

def _debug_badge() -> rx.Component:
    """Badge de modo desarrollo, solo visible si DEBUG=true."""
    if not Config.DEBUG:
        return rx.fragment()
    return rx.badge(
        "DEV",
        color_scheme="red",
        variant="solid",
        size="1",
    )


def sidebar_footer() -> rx.Component:
    """
    Footer del sidebar con dev view switcher, version y badge de debug.
    """
    return rx.vstack(
        _dev_view_switcher(),
        rx.hstack(
            rx.cond(
                ~SidebarState.is_collapsed,
                rx.hstack(
                    rx.text(
                        "v1.0.0",
                        font_size=Typography.SIZE_XS,
                        color=Colors.TEXT_MUTED,
                    ),
                    _debug_badge(),
                    align="center",
                    gap=Spacing.XS,
                ),
                _debug_badge(),
            ),
            width="100%",
            padding_x=Spacing.MD,
            padding_bottom=Spacing.SM,
            align="center",
            justify=rx.cond(SidebarState.is_collapsed, "center", "start"),
        ),
        width="100%",
        spacing="2",
    )


# =============================================================================
# SIDEBAR COMPLETO
# =============================================================================

def sidebar() -> rx.Component:
    """
    Sidebar completo con header, navegacion, seccion de usuario y footer.

    Uso:
        def layout(content):
            return rx.hstack(
                sidebar(),
                rx.box(content, flex="1"),
            )
    """
    return rx.box(
        rx.vstack(
            sidebar_header(),
            sidebar_navigation(),
            sidebar_user_section(),
            sidebar_footer(),
            height="100vh",
            width="100%",
            spacing="0",
            align_items="stretch",
        ),
        # Boton de toggle (posicionado absoluto)
        sidebar_toggle_button(),

        # Estilos del contenedor
        position="relative",
        width=SidebarState.sidebar_width,
        min_width=SidebarState.sidebar_width,
        height="100vh",
        background=Colors.SURFACE,
        border_right=f"1px solid {Colors.BORDER}",
        transition=f"width {Transitions.NORMAL}, min-width {Transitions.NORMAL}",
        flex_shrink="0",
        overflow="visible",  # Para que el boton toggle se vea
        on_mount=[SidebarState.cargar_alertas, NotificationBellState.cargar_notificaciones],
    )


# =============================================================================
# VERSION SIMPLIFICADA PARA DESKTOP ONLY
# =============================================================================

def sidebar_desktop() -> rx.Component:
    """
    Version desktop-only del sidebar.
    Igual que sidebar() pero explicitamente para escritorio.
    """
    return rx.desktop_only(sidebar())
