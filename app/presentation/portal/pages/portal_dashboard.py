"""
Dashboard del portal de cliente.

Muestra metricas rapidas de la empresa del usuario:
- Empleados activos
- Contratos activos
- Plazas ocupadas / vacantes
- Accesos rapidos a las secciones principales
"""
import reflex as rx

from app.presentation.portal.state.portal_state import PortalState
from app.presentation.layout import page_layout, page_header
from app.presentation.theme import Colors, Typography, Spacing


# =============================================================================
# COMPONENTES DE METRICAS
# =============================================================================

def _metric_card(
    titulo: str,
    valor: rx.Var,
    icono: str,
    color_scheme: str,
    href: str,
) -> rx.Component:
    """Tarjeta de metrica con valor, icono y link."""
    return rx.link(
        rx.card(
            rx.hstack(
                rx.vstack(
                    rx.text(
                        titulo,
                        font_size=Typography.SIZE_XS,
                        color=Colors.TEXT_MUTED,
                        font_weight=Typography.WEIGHT_MEDIUM,
                    ),
                    rx.text(
                        valor,
                        font_size="1.75rem",
                        font_weight=Typography.WEIGHT_BOLD,
                        color=Colors.TEXT_PRIMARY,
                        line_height="1",
                    ),
                    spacing="1",
                    align_items="start",
                ),
                rx.spacer(),
                rx.center(
                    rx.icon(icono, size=24, color=f"var(--{color_scheme}-9)"),
                    width="48px",
                    height="48px",
                    border_radius="12px",
                    background=f"var(--{color_scheme}-3)",
                    flex_shrink="0",
                ),
                width="100%",
                align="center",
            ),
            width="100%",
            style={
                "_hover": {"box_shadow": "0 2px 8px rgba(0,0,0,0.08)"},
                "transition": "box-shadow 0.2s",
            },
        ),
        href=href,
        underline="none",
        width="100%",
    )


def _metricas_grid() -> rx.Component:
    """Grid de metricas principales."""
    return rx.cond(
        PortalState.loading,
        # Skeleton
        rx.grid(
            *[rx.skeleton(rx.card(rx.box(height="80px"), width="100%")) for _ in range(4)],
            columns="4",
            spacing="4",
            width="100%",
        ),
        rx.grid(
            _metric_card(
                titulo="Empleados Activos",
                valor=PortalState.total_empleados,
                icono="users",
                color_scheme="blue",
                href="/portal/empleados",
            ),
            _metric_card(
                titulo="Contratos Activos",
                valor=PortalState.total_contratos,
                icono="file-text",
                color_scheme="teal",
                href="/portal/contratos",
            ),
            _metric_card(
                titulo="Plazas Ocupadas",
                valor=PortalState.total_plazas_ocupadas,
                icono="user-check",
                color_scheme="green",
                href="/portal/plazas",
            ),
            _metric_card(
                titulo="Plazas Vacantes",
                valor=PortalState.total_plazas_vacantes,
                icono="user-x",
                color_scheme="orange",
                href="/portal/plazas",
            ),
            columns=rx.breakpoints(initial="1", sm="2", lg="4"),
            spacing="4",
            width="100%",
        ),
    )


# =============================================================================
# ACCESOS RAPIDOS
# =============================================================================

def _quick_link(texto: str, icono: str, href: str, descripcion: str) -> rx.Component:
    """Acceso rapido a una seccion."""
    return rx.link(
        rx.card(
            rx.hstack(
                rx.icon(icono, size=20, color=Colors.TEXT_SECONDARY),
                rx.vstack(
                    rx.text(texto, font_size=Typography.SIZE_SM, font_weight=Typography.WEIGHT_MEDIUM),
                    rx.text(descripcion, font_size=Typography.SIZE_XS, color=Colors.TEXT_MUTED),
                    spacing="0",
                ),
                spacing="3",
                align="center",
                width="100%",
            ),
            width="100%",
            style={
                "_hover": {"background": "var(--gray-3)"},
                "transition": "background 0.2s",
                "cursor": "pointer",
            },
        ),
        href=href,
        underline="none",
        width="100%",
    )


def _accesos_rapidos() -> rx.Component:
    """Seccion de accesos rapidos."""
    return rx.vstack(
        rx.text(
            "Accesos rapidos",
            font_size=Typography.SIZE_SM,
            font_weight=Typography.WEIGHT_SEMIBOLD,
            color=Colors.TEXT_SECONDARY,
        ),
        rx.grid(
            _quick_link(
                "Ver empleados",
                "users",
                "/portal/empleados",
                "Lista completa de empleados",
            ),
            _quick_link(
                "Mis contratos",
                "file-text",
                "/portal/contratos",
                "Contratos y categorias",
            ),
            _quick_link(
                "Datos de empresa",
                "building-2",
                "/portal/mi-empresa",
                "RFC, contacto y datos generales",
            ),
            _quick_link(
                "Requisiciones",
                "clipboard-list",
                "/portal/requisiciones",
                "Requisiciones de la empresa",
            ),
            columns=rx.breakpoints(initial="1", sm="2"),
            spacing="3",
            width="100%",
        ),
        spacing="3",
        width="100%",
    )


# =============================================================================
# PAGINA PRINCIPAL
# =============================================================================

def portal_dashboard_page() -> rx.Component:
    """Pagina de dashboard del portal de cliente."""
    return rx.box(
        page_layout(
            header=page_header(
                titulo=rx.cond(
                    PortalState.nombre_usuario,
                    rx.text("Bienvenido, ", PortalState.nombre_usuario),
                    "Dashboard",
                ),
                subtitulo=PortalState.nombre_empresa_actual,
                icono="layout-dashboard",
            ),
            content=rx.vstack(
                _metricas_grid(),
                _accesos_rapidos(),
                spacing="6",
                width="100%",
            ),
        ),
        width="100%",
        min_height="100vh",
        on_mount=PortalState.on_mount_dashboard,
    )
