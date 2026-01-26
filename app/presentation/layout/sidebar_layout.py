"""
Sidebar Layout - Sidebar Colapsable
====================================

Sidebar responsive con soporte para colapso a modo icono-only.
Agrupa items por categoría y muestra indicador de página activa.

Características:
- Colapsa de 240px a 72px
- Transición suave de 200ms
- Tooltips en modo colapsado
- Grupos de navegación (Operación, Catálogos, Herramientas)
- Indicador visual de página activa

Uso:
    from app.presentation.layout import sidebar
    
    def index(content):
        return rx.hstack(
            sidebar(),
            rx.box(content, ...),
        )
"""

import reflex as rx
from app.presentation.layout.sidebar_state import SidebarState
from app.presentation.theme import (
    Colors,
    Spacing,
    Transitions,
    Typography,
    Shadows,
    Sidebar as SidebarConfig,
)


# =============================================================================
# CONFIGURACIÓN DE NAVEGACIÓN
# =============================================================================

# Estructura de navegación agrupada
NAVIGATION_GROUPS = [
    {
        "label": None,  # Sin etiqueta = item suelto
        "items": [
            {"text": "Dashboard", "icon": "layout-dashboard", "href": "/"},
        ],
    },
    {
        "label": "Operación",
        "items": [
            {"text": "Requisiciones", "icon": "clipboard-list", "href": "/requisiciones"},
            {"text": "Contratos", "icon": "file-text", "href": "/contratos"},
            {"text": "Pagos", "icon": "credit-card", "href": "/pagos"},
            {"text": "Empresas", "icon": "building-2", "href": "/empresas"},
            {"text": "Sedes", "icon": "map-pin-house", "href": "/sedes"},
            
        ],
    },
    {
        "label": "Personal",
        "items":[
            {"text": "Empleados", "icon": "users", "href": "/empleados"},
            {"text": "Historial", "icon": "history", "href": "/historial-laboral"},
        ]
    },
    {
        "label": "Catálogos",
        "items": [
            {"text": "Tipos de Servicio", "icon": "briefcase", "href": "/tipos-servicio"},
            {"text": "Categorías Puesto", "icon": "folder", "href": "/categorias-puesto"},
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


# =============================================================================
# COMPONENTES DEL SIDEBAR
# =============================================================================

def sidebar_header() -> rx.Component:
    """
    Header del sidebar con logo y título.
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
        # Título (solo visible expandido)
        rx.cond(
            SidebarState.is_collapsed,
            rx.fragment(),
            rx.vstack(
                rx.text(
                    "BUAP",
                    font_size=Typography.SIZE_LG,
                    font_weight=Typography.WEIGHT_BOLD,
                    color=Colors.TEXT_PRIMARY,
                    line_height="1.2",
                ),
                rx.text(
                    "Sistema de Gestión",
                    font_size=Typography.SIZE_XS,
                    color=Colors.TEXT_SECONDARY,
                    line_height="1.2",
                ),
                spacing="0",
                align_items="start",
            ),
        ),
        padding_x=Spacing.MD,
        padding_y=Spacing.LG,
        align="center",
        justify=rx.cond(SidebarState.is_collapsed, "center", "start"),
        width="100%",
        gap=Spacing.SM,
    )


def sidebar_item(text: str, icon: str, href: str) -> rx.Component:
    """
    Item de navegación individual.
    Muestra tooltip en modo colapsado.
    """
    # Contenido base del item
    item_content = rx.hstack(
        rx.icon(
            icon,
            size=20,
            color=Colors.TEXT_SECONDARY,
            flex_shrink="0",
        ),
        # Texto solo visible cuando está expandido
        rx.cond(
            ~SidebarState.is_collapsed,
            rx.text(
                text,
                font_size=Typography.SIZE_SM,
                font_weight=Typography.WEIGHT_MEDIUM,
                color=Colors.TEXT_PRIMARY,
                white_space="nowrap",
            ),
        ),
        width="100%",
        padding_x=Spacing.MD,
        padding_y=Spacing.SM,
        align="center",
        justify=rx.cond(SidebarState.is_collapsed, "center", "start"),
        gap=Spacing.SM,
        border_radius="8px",
        transition=Transitions.FAST,
        style={
            "_hover": {
                "background": Colors.SIDEBAR_ITEM_HOVER,
            },
        },
    )
    
    # Envolver en tooltip si está colapsado
    item_with_tooltip = rx.cond(
        SidebarState.is_collapsed,
        rx.tooltip(
            item_content,
            content=text,
            side="right",
        ),
        item_content,
    )
    
    return rx.link(
        item_with_tooltip,
        href=href,
        underline="none",
        width="100%",
    )


def sidebar_group_label(label: str) -> rx.Component:
    """
    Etiqueta de grupo de navegación.
    Solo visible cuando el sidebar está expandido.
    """
    return rx.cond(
        ~SidebarState.is_collapsed,
        rx.text(
            label.upper(),
            font_size=Typography.SIZE_XS,
            font_weight=Typography.WEIGHT_SEMIBOLD,
            color=Colors.TEXT_MUTED,
            letter_spacing=Typography.LETTER_SPACING_WIDE,
            padding_x=Spacing.MD,
            padding_top=Spacing.LG,
            padding_bottom=Spacing.XS,
        ),
        # En modo colapsado, mostrar separador sutil
        rx.box(
            height="1px",
            background=Colors.BORDER,
            margin_y=Spacing.SM,
            margin_x=Spacing.MD,
        ),
    )


def sidebar_group(group: dict) -> rx.Component:
    """
    Renderiza un grupo de navegación con su etiqueta e items.
    """
    items = [
        sidebar_item(
            text=item["text"],
            icon=item["icon"],
            href=item["href"],
        )
        for item in group["items"]
    ]
    
    if group["label"]:
        return rx.vstack(
            sidebar_group_label(group["label"]),
            *items,
            spacing="1",
            width="100%",
            align_items="stretch",
        )
    else:
        return rx.vstack(
            *items,
            spacing="1",
            width="100%",
            align_items="stretch",
        )


def sidebar_navigation() -> rx.Component:
    """
    Contenedor principal de navegación con todos los grupos.
    """
    groups = [sidebar_group(group) for group in NAVIGATION_GROUPS]
    
    return rx.vstack(
        *groups,
        spacing="0",
        width="100%",
        flex="1",
        overflow_y="auto",
        padding_x=Spacing.XS,
    )


def sidebar_toggle_button() -> rx.Component:
    """
    Botón para colapsar/expandir el sidebar.
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


def sidebar_footer() -> rx.Component:
    """
    Footer del sidebar con versión y configuración.
    """
    return rx.vstack(
        # Separador
        rx.box(
            height="1px",
            background=Colors.BORDER,
            width="100%",
        ),
        # Contenido del footer
        rx.hstack(
            rx.cond(
                SidebarState.is_collapsed,
                rx.fragment(),
                rx.text(
                    "v1.0.0",
                    font_size=Typography.SIZE_XS,
                    color=Colors.TEXT_MUTED,
                ),
            ),
            rx.spacer(),
            rx.tooltip(
                rx.icon_button(
                    rx.icon("settings", size=18),
                    size="1",
                    variant="ghost",
                    color_scheme="gray",
                    cursor="pointer",
                ),
                content="Configuración",
                side=rx.cond(SidebarState.is_collapsed, "right", "top"),

            ),
            width="100%",
            padding=Spacing.MD,
            align="center",
            justify=rx.cond(SidebarState.is_collapsed, "center", "between"),
        ),
        width="100%",
        spacing="0",
    )


def sidebar() -> rx.Component:
    """
    Sidebar completo con header, navegación y footer.
    
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
            sidebar_footer(),
            height="100vh",
            width="100%",
            spacing="0",
            align_items="stretch",
        ),
        # Botón de toggle (posicionado absoluto)
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
        overflow="visible",  # Para que el botón toggle se vea
    )


# =============================================================================
# VERSIÓN SIMPLIFICADA PARA DESKTOP ONLY
# =============================================================================

def sidebar_desktop() -> rx.Component:
    """
    Versión desktop-only del sidebar.
    Igual que sidebar() pero explícitamente para escritorio.
    """
    return rx.desktop_only(sidebar())