"""
Sidebar del portal de cliente.

Sidebar simplificado con solo las secciones relevantes para
usuarios de empresas proveedoras. Muestra la empresa activa
y opciones para cambiar empresa (si tiene multiples asignadas).
"""
import reflex as rx

from app.presentation.portal.state.portal_state import PortalState
from app.presentation.theme import (
    Colors,
    Spacing,
    Transitions,
    Typography,
    Shadows,
)


# =============================================================================
# CONFIGURACION DE NAVEGACION DEL PORTAL
# =============================================================================

PORTAL_NAVIGATION = [
    {
        "label": None,
        "items": [
            {"text": "Dashboard", "icon": "layout-dashboard", "href": "/portal"},
        ],
    },
    {
        "label": "Mi Empresa",
        "items": [
            {"text": "Datos Empresa", "icon": "building-2", "href": "/portal/mi-empresa"},
            {"text": "Empleados", "icon": "users", "href": "/portal/empleados"},
        ],
    },
    {
        "label": "Operacion",
        "items": [
            {"text": "Contratos", "icon": "file-text", "href": "/portal/contratos"},
            {"text": "Plazas", "icon": "briefcase", "href": "/portal/plazas"},
            {"text": "Requisiciones", "icon": "clipboard-list", "href": "/portal/requisiciones"},
        ],
    },
]


# =============================================================================
# COMPONENTES
# =============================================================================

def _portal_header() -> rx.Component:
    """Header del sidebar con nombre de la empresa."""
    return rx.hstack(
        rx.center(
            rx.icon("building-2", size=20, color="var(--teal-9)"),
            width="36px",
            height="36px",
            border_radius="8px",
            background="var(--teal-3)",
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
                max_width="160px",
            ),
            rx.text(
                "Portal Cliente",
                font_size=Typography.SIZE_XS,
                color=Colors.TEXT_MUTED,
                line_height="1.2",
            ),
            spacing="0",
            align_items="start",
        ),
        padding_x=Spacing.MD,
        padding_y=Spacing.LG,
        align="center",
        width="100%",
        gap=Spacing.SM,
    )


def _portal_item(text: str, icon: str, href: str) -> rx.Component:
    """Item de navegacion del portal."""
    return rx.link(
        rx.hstack(
            rx.icon(
                icon,
                size=20,
                color=Colors.TEXT_SECONDARY,
                flex_shrink="0",
            ),
            rx.text(
                text,
                font_size=Typography.SIZE_SM,
                font_weight=Typography.WEIGHT_MEDIUM,
                color=Colors.TEXT_PRIMARY,
                white_space="nowrap",
            ),
            width="100%",
            padding_x=Spacing.MD,
            padding_y=Spacing.SM,
            align="center",
            gap=Spacing.SM,
            border_radius="8px",
            transition=Transitions.FAST,
            style={
                "_hover": {
                    "background": Colors.SIDEBAR_ITEM_HOVER,
                },
            },
        ),
        href=href,
        underline="none",
        width="100%",
    )


def _portal_group_label(label: str) -> rx.Component:
    """Etiqueta de grupo."""
    return rx.text(
        label.upper(),
        font_size=Typography.SIZE_XS,
        font_weight=Typography.WEIGHT_SEMIBOLD,
        color=Colors.TEXT_MUTED,
        letter_spacing=Typography.LETTER_SPACING_WIDE,
        padding_x=Spacing.MD,
        padding_top=Spacing.LG,
        padding_bottom=Spacing.XS,
    )


def _portal_group(group: dict) -> rx.Component:
    """Renderiza un grupo de navegacion."""
    items = [
        _portal_item(text=item["text"], icon=item["icon"], href=item["href"])
        for item in group["items"]
    ]

    if group["label"]:
        return rx.vstack(
            _portal_group_label(group["label"]),
            *items,
            spacing="1",
            width="100%",
            align_items="stretch",
        )
    return rx.vstack(
        *items,
        spacing="1",
        width="100%",
        align_items="stretch",
    )


def _portal_navigation() -> rx.Component:
    """Navegacion completa del portal."""
    groups = [_portal_group(group) for group in PORTAL_NAVIGATION]
    return rx.vstack(
        *groups,
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
                        rx.icon("user", size=18, color="var(--teal-9)"),
                        width="32px",
                        height="32px",
                        border_radius="50%",
                        background="var(--teal-3)",
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
                    on_click=rx.redirect("/portal/perfil"),
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
    )
