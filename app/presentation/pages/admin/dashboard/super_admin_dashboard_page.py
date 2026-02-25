"""
Página del panel de Super Admin (/admin).
"""

import reflex as rx

from app.presentation.components.ui import metric_card
from app.presentation.layout import page_header, page_layout
from app.presentation.theme import Colors, Spacing, Typography

from .super_admin_dashboard_state import SuperAdminDashboardState


def _boton_actualizar() -> rx.Component:
    return rx.tooltip(
        rx.icon_button(
            rx.icon("refresh-cw", size=16),
            on_click=SuperAdminDashboardState.refrescar,
            loading=SuperAdminDashboardState.cargando,
            variant="outline",
            color_scheme="gray",
            size="2",
            cursor="pointer",
        ),
        content="Actualizar métricas",
    )


def _skeleton_metric() -> rx.Component:
    return rx.card(
        rx.hstack(
            rx.vstack(
                rx.skeleton(width="120px", height="14px"),
                rx.skeleton(width="70px", height="28px"),
                spacing="2",
                align_items="start",
            ),
            rx.spacer(),
            rx.skeleton(width="48px", height="48px", border_radius="9999px"),
            width="100%",
            align="center",
        ),
        width="100%",
    )


def _skeleton_dashboard() -> rx.Component:
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


def _kpis() -> rx.Component:
    return rx.grid(
        metric_card(
            titulo="Usuarios activos",
            valor=SuperAdminDashboardState.metricas_dict["usuarios_activos"].to(str),
            icono="users",
            color_scheme="blue",
            href="/admin/usuarios",
        ),
        metric_card(
            titulo="Usuarios inactivos",
            valor=SuperAdminDashboardState.metricas_dict["usuarios_inactivos"].to(str),
            icono="user-x",
            color_scheme="gray",
            href="/admin/usuarios",
        ),
        metric_card(
            titulo="Super admins",
            valor=SuperAdminDashboardState.metricas_dict["super_admins"].to(str),
            icono="shield-check",
            color_scheme="violet",
            href="/admin/usuarios",
        ),
        metric_card(
            titulo="Instituciones activas",
            valor=SuperAdminDashboardState.metricas_dict["instituciones_activas"].to(str),
            icono="building",
            color_scheme="green",
            href="/admin/instituciones",
        ),
        metric_card(
            titulo="Onboarding en revisión",
            valor=SuperAdminDashboardState.metricas_dict["onboarding_en_revision"].to(str),
            icono="clipboard-check",
            color_scheme="amber",
            href="/admin/onboarding",
        ),
        metric_card(
            titulo="Onboarding rechazado",
            valor=SuperAdminDashboardState.metricas_dict["onboarding_rechazado"].to(str),
            icono="triangle-alert",
            color_scheme="red",
            href="/admin/onboarding",
        ),
        metric_card(
            titulo="Usuarios sin último acceso",
            valor=SuperAdminDashboardState.metricas_dict["usuarios_sin_ultimo_acceso"].to(str),
            icono="clock-3",
            color_scheme="orange",
            href="/admin/usuarios",
        ),
        metric_card(
            titulo="Instituciones sin empresas",
            valor=SuperAdminDashboardState.metricas_dict["instituciones_sin_empresas"].to(str),
            icono="building-2",
            color_scheme="orange",
            href="/admin/instituciones",
        ),
        metric_card(
            titulo="Requisiciones pendientes",
            valor=SuperAdminDashboardState.metricas_dict["requisiciones_pendientes"].to(str),
            icono="clipboard-list",
            color_scheme="amber",
            href="/requisiciones",
        ),
        metric_card(
            titulo="Contratos por vencer",
            valor=SuperAdminDashboardState.metricas_dict["contratos_por_vencer"].to(str),
            icono="calendar-clock",
            color_scheme="red",
            href="/contratos",
        ),
        columns=rx.breakpoints(initial="1", sm="2", lg="3"),
        spacing="4",
        width="100%",
    )


def _banner_advertencias() -> rx.Component:
    return rx.cond(
        SuperAdminDashboardState.advertencias.length() > 0,
        rx.card(
            rx.vstack(
                rx.hstack(
                    rx.icon("triangle-alert", size=16, color="var(--amber-9)"),
                    rx.text(
                        "Se cargaron datos parciales",
                        font_weight=Typography.WEIGHT_SEMIBOLD,
                        color=Colors.TEXT_PRIMARY,
                    ),
                    spacing="2",
                    align="center",
                ),
                rx.foreach(
                    SuperAdminDashboardState.advertencias,
                    lambda advertencia: rx.text(
                        "• " + advertencia,
                        size="2",
                        color=Colors.TEXT_SECONDARY,
                    ),
                ),
                spacing="2",
                width="100%",
                align_items="start",
            ),
            width="100%",
            background="var(--amber-2)",
            border="1px solid var(--amber-6)",
        ),
        rx.fragment(),
    )


def _fila_alerta(titulo: str, descripcion: str, href: str, icono: str = "circle-alert") -> rx.Component:
    return rx.link(
        rx.card(
            rx.hstack(
                rx.hstack(
                    rx.icon(icono, size=16, color="var(--amber-9)"),
                    rx.vstack(
                        rx.text(titulo, weight="medium"),
                        rx.text(descripcion, size="2", color=Colors.TEXT_SECONDARY),
                        spacing="0",
                        align_items="start",
                    ),
                    spacing="3",
                    align="center",
                ),
                rx.spacer(),
                rx.icon("arrow-right", size=16, color=Colors.TEXT_MUTED),
                width="100%",
                align="center",
            ),
            width="100%",
        ),
        href=href,
        underline="none",
        width="100%",
    )


def _panel_alertas() -> rx.Component:
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.icon("siren", size=18, color="var(--red-9)"),
                rx.text("Atención", weight="bold"),
                spacing="2",
                align="center",
            ),
            rx.cond(
                SuperAdminDashboardState.usuarios_sin_ultimo_acceso > 0,
                _fila_alerta(
                    "Usuarios sin último acceso",
                    "Hay usuarios que no han iniciado sesión.",
                    "/admin/usuarios",
                ),
                rx.fragment(),
            ),
            rx.cond(
                SuperAdminDashboardState.onboarding_rechazado > 0,
                _fila_alerta(
                    "Onboarding rechazado",
                    "Existen empleados con onboarding rechazado.",
                    "/admin/onboarding",
                    icono="triangle-alert",
                ),
                rx.fragment(),
            ),
            rx.cond(
                SuperAdminDashboardState.instituciones_sin_empresas > 0,
                _fila_alerta(
                    "Instituciones sin empresas",
                    "Revise instituciones activas sin empresas asociadas.",
                    "/admin/instituciones",
                    icono="building-2",
                ),
                rx.fragment(),
            ),
            rx.cond(
                (SuperAdminDashboardState.usuarios_sin_ultimo_acceso == 0)
                & (SuperAdminDashboardState.onboarding_rechazado == 0)
                & (SuperAdminDashboardState.instituciones_sin_empresas == 0),
                rx.text(
                    "Sin alertas prioritarias por ahora.",
                    size="2",
                    color=Colors.TEXT_SECONDARY,
                ),
                rx.fragment(),
            ),
            spacing="3",
            width="100%",
            align_items="start",
        ),
        width="100%",
    )


def _acceso_rapido(titulo: str, descripcion: str, href: str, icono: str) -> rx.Component:
    return rx.link(
        rx.card(
            rx.hstack(
                rx.center(
                    rx.icon(icono, size=18, color="var(--blue-9)"),
                    width="36px",
                    height="36px",
                    border_radius="10px",
                    background="var(--blue-3)",
                ),
                rx.vstack(
                    rx.text(titulo, weight="medium"),
                    rx.text(descripcion, size="2", color=Colors.TEXT_SECONDARY),
                    spacing="0",
                    align_items="start",
                ),
                rx.spacer(),
                rx.icon("arrow-right", size=16, color=Colors.TEXT_MUTED),
                width="100%",
                align="center",
            ),
            width="100%",
        ),
        href=href,
        underline="none",
        width="100%",
    )


def _panel_accesos_rapidos() -> rx.Component:
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.icon("zap", size=18, color="var(--blue-9)"),
                rx.text("Accesos rápidos", weight="bold"),
                spacing="2",
                align="center",
            ),
            rx.grid(
                _acceso_rapido("Gestionar usuarios", "Usuarios, roles y permisos", "/admin/usuarios", "users"),
                _acceso_rapido("Pipeline onboarding", "Seguimiento global de onboarding", "/admin/onboarding", "user-plus"),
                _acceso_rapido("Instituciones", "Catálogo y empresas asociadas", "/admin/instituciones", "building"),
                _acceso_rapido("Dashboard operativo", "Volver al panel general", "/", "layout-dashboard"),
                columns=rx.breakpoints(initial="1", md="2"),
                spacing="3",
                width="100%",
            ),
            spacing="3",
            width="100%",
            align_items="start",
        ),
        width="100%",
    )


def _estado_error() -> rx.Component:
    return rx.center(
        rx.card(
            rx.vstack(
                rx.icon("shield-x", size=36, color="var(--red-9)"),
                rx.text("No se pudo cargar el panel", weight="bold"),
                rx.text(
                    SuperAdminDashboardState.error,
                    size="2",
                    color=Colors.TEXT_SECONDARY,
                    text_align="center",
                ),
                rx.button(
                    "Reintentar",
                    on_click=SuperAdminDashboardState.montar_pagina,
                    color_scheme="blue",
                    variant="soft",
                ),
                spacing="3",
                align="center",
            ),
            max_width="480px",
            width="100%",
        ),
        width="100%",
        min_height="40vh",
    )


def _contenido_panel() -> rx.Component:
    return rx.vstack(
        _banner_advertencias(),
        _kpis(),
        rx.grid(
            _panel_alertas(),
            _panel_accesos_rapidos(),
            columns=rx.breakpoints(initial="1", xl="2"),
            spacing="4",
            width="100%",
        ),
        spacing="4",
        width="100%",
        padding_top=Spacing.SM,
    )


def super_admin_dashboard_page() -> rx.Component:
    """Página principal del panel de super admin."""
    return rx.box(
        page_layout(
            header=page_header(
                titulo="Super Admin",
                subtitulo="Control de acceso, operación global y supervisión",
                icono="shield-check",
                accion_principal=_boton_actualizar(),
            ),
            toolbar=rx.fragment(),
            content=rx.cond(
                SuperAdminDashboardState.error,
                _estado_error(),
                rx.cond(
                    SuperAdminDashboardState.cargando & ~SuperAdminDashboardState.metricas_cargadas,
                    _skeleton_dashboard(),
                    _contenido_panel(),
                ),
            ),
        ),
        width="100%",
        min_height="100vh",
        on_mount=SuperAdminDashboardState.montar_pagina,
    )
