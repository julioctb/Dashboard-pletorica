"""
Página del Dashboard Administrativo.

Panel de control para administradores BUAP con métricas KPI:
- Empresas activas
- Empleados activos
- Contratos activos
- Plazas ocupadas / vacantes
- Requisiciones pendientes
Uso:
    from app.presentation.pages.dashboard import dashboard_page
"""

import reflex as rx

from app.presentation.pages.dashboard.dashboard_state import DashboardState
from app.presentation.layout import page_layout, page_header
from app.presentation.components.ui.metric_card import metric_card
from app.presentation.theme import (
    Colors,
    Typography,
    Radius,
)


# =============================================================================
# SKELETON DE CARGA
# =============================================================================

def _skeleton_metric() -> rx.Component:
    """Skeleton placeholder para una metric_card durante carga."""
    return rx.card(
        rx.hstack(
            rx.vstack(
                rx.skeleton(width="100px", height="14px"),
                rx.skeleton(width="60px", height="32px"),
                spacing="2",
            ),
            rx.spacer(),
            rx.skeleton(width="48px", height="48px", border_radius=Radius.XL),
            width="100%",
            align="center",
        ),
        width="100%",
    )


def _skeleton_grid() -> rx.Component:
    """Grid de skeletons mientras cargan las métricas."""
    return rx.grid(
        _skeleton_metric(),
        _skeleton_metric(),
        _skeleton_metric(),
        _skeleton_metric(),
        _skeleton_metric(),
        _skeleton_metric(),
        columns=rx.breakpoints(initial="1", sm="2", lg="3"),
        spacing="4",
        width="100%",
    )


# =============================================================================
# SECCIÓN: MÉTRICAS KPI
# =============================================================================

def _metricas_grid() -> rx.Component:
    """Grid de métricas KPI principales."""
    return rx.grid(
        # Fila 1: Entidades principales
        metric_card(
            titulo="Empresas activas",
            valor=DashboardState.metricas["empresas_activas"].to(str),
            icono="building-2",
            color_scheme="blue",
            href="/empresas",
        ),
        metric_card(
            titulo="Empleados activos",
            valor=DashboardState.metricas["empleados_activos"].to(str),
            icono="users",
            color_scheme="teal",
            href="/empleados",
        ),
        metric_card(
            titulo="Contratos activos",
            valor=DashboardState.metricas["contratos_activos"].to(str),
            icono="file-text",
            color_scheme="green",
            href="/contratos",
        ),

        # Fila 2: Plazas y alertas
        metric_card(
            titulo="Plazas ocupadas",
            valor=DashboardState.metricas["plazas_ocupadas"].to(str),
            icono="user-check",
            color_scheme="green",
            href="/plazas",
        ),
        metric_card(
            titulo="Plazas vacantes",
            valor=DashboardState.metricas["plazas_vacantes"].to(str),
            icono="user-plus",
            color_scheme="sky",
            href="/plazas",
        ),

        # Alertas como métricas con color de urgencia
        metric_card(
            titulo="Requisiciones pendientes",
            valor=DashboardState.metricas["requisiciones_pendientes"].to(str),
            icono="clipboard-list",
            color_scheme="amber",
            href="/wip/requisiciones",
        ),

        columns=rx.breakpoints(initial="1", sm="2", lg="3"),
        spacing="4",
        width="100%",
    )



# =============================================================================
# BOTÓN DE REFRESCAR
# =============================================================================

def _boton_refrescar() -> rx.Component:
    """Botón para refrescar métricas manualmente."""
    return rx.tooltip(
        rx.icon_button(
            rx.icon("refresh-cw", size=16),
            on_click=DashboardState.refrescar,
            loading=DashboardState.loading,
            variant="outline",
            color_scheme="gray",
            size="2",
            cursor="pointer",
        ),
        content="Actualizar métricas",
    )


# =============================================================================
# PÁGINA PRINCIPAL
# =============================================================================

def dashboard_page() -> rx.Component:
    """Página principal del dashboard administrativo BUAP."""
    return rx.box(
        page_layout(
            header=page_header(
                titulo="Panel de Control",
                subtitulo="Visión general del sistema",
                icono="layout-dashboard",
                accion_principal=_boton_refrescar(),
            ),
            content=rx.cond(
                DashboardState.loading & ~DashboardState.metricas_cargadas,
                # Primera carga: mostrar skeletons
                _skeleton_grid(),
                # Datos cargados
                rx.vstack(
                    _metricas_grid(),
                    spacing="5",
                    width="100%",
                ),
            ),
        ),
        width="100%",
        min_height="100vh",
        on_mount=DashboardState.cargar_metricas,
    )
