"""
Dashboard del portal de cliente.

Panel operativo que responde: que necesita mi atencion hoy?
Metricas enriquecidas + 6 widgets de seguimiento.
"""

import reflex as rx

from app.presentation.components.ui import metric_card, metric_card_grid
from app.presentation.components.ui.badges_domain import payroll_period_status_badge
from app.presentation.pages.portal.state.portal_dashboard_state import (
    PortalDashboardState,
)
from app.presentation.layouts.backoffice import page_layout, page_header
from app.presentation.theme import CardStyles, Colors, Radius, StatusColors, Typography


# =============================================================================
# HELPERS LOCALES
# =============================================================================


def _section_label(text: str) -> rx.Component:
    """Label de seccion en uppercase."""
    return rx.text(
        text,
        font_size=Typography.SIZE_XS,
        font_weight=Typography.WEIGHT_SEMIBOLD,
        color=Colors.TEXT_MUTED,
        letter_spacing=Typography.LETTER_SPACING_WIDE,
        text_transform="uppercase",
    )


def _widget_skeleton() -> rx.Component:
    """Skeleton de un widget de seguimiento."""
    return rx.card(
        rx.vstack(
            # Header
            rx.hstack(
                rx.skeleton(width="140px", height="14px"),
                rx.spacer(),
                rx.skeleton(width="70px", height="12px"),
                width="100%",
                align="center",
            ),
            # Body lines
            rx.skeleton(width="100%", height="12px"),
            rx.skeleton(width="85%", height="12px"),
            rx.skeleton(width="70%", height="12px"),
            rx.skeleton(width="90%", height="12px"),
            spacing="3",
            width="100%",
        ),
        width="100%",
        style={**CardStyles.BASE},
    )


def _widget_container(*children: rx.Component) -> rx.Component:
    """Card base para widgets sin hover."""
    return rx.card(
        rx.vstack(*children, spacing="3", width="100%"),
        width="100%",
        style={**CardStyles.BASE},
    )


def _widget_header(
    titulo: str,
    link_text: str = "",
    link_href: str | rx.Var = "",
) -> rx.Component:
    """Header de widget con titulo y link opcional."""
    return rx.hstack(
        rx.text(
            titulo,
            font_size=Typography.SIZE_SM,
            font_weight=Typography.WEIGHT_SEMIBOLD,
            color=Colors.TEXT_PRIMARY,
        ),
        rx.spacer(),
        rx.cond(
            link_text != "",
            rx.link(
                rx.text(
                    link_text,
                    font_size=Typography.SIZE_XS,
                    color=Colors.PORTAL_PRIMARY_TEXT,
                ),
                href=link_href,
                underline="none",
            ),
            rx.fragment(),
        ),
        width="100%",
        align="center",
    )


def _metric_skeleton() -> rx.Component:
    return rx.card(
        rx.hstack(
            rx.vstack(
                rx.skeleton(width="120px", height="14px"),
                rx.skeleton(width="70px", height="28px"),
                rx.skeleton(width="90px", height="12px"),
                spacing="2",
                align_items="start",
            ),
            rx.spacer(),
            rx.skeleton(width="48px", height="48px", border_radius=Radius.XL),
            width="100%",
            align="center",
        ),
        width="100%",
        style={**CardStyles.BASE},
    )


# =============================================================================
# METRICAS PRINCIPALES
# =============================================================================


def _metricas_grid() -> rx.Component:
    """Grid de 4 metricas principales con footers enriquecidos."""
    return rx.cond(
        PortalDashboardState.loading,
        metric_card_grid(
            *[_metric_skeleton() for _ in range(4)],
            spacing="4",
        ),
        metric_card_grid(
            metric_card(
                titulo="Empleados Activos",
                valor=PortalDashboardState.total_empleados_dashboard,
                icono="users",
                color_scheme="blue",
                href=PortalDashboardState.ruta_rrhh_principal,
                footer=rx.cond(
                    PortalDashboardState.empleados_en_onboarding > 0,
                    rx.text(
                        PortalDashboardState.empleados_en_onboarding.to(str)
                        + " en onboarding",
                        font_size=Typography.SIZE_XS,
                        color=Colors.TEXT_SECONDARY,
                    ),
                    rx.text(" ", font_size=Typography.SIZE_XS),
                ),
            ),
            metric_card(
                titulo="Contratos Activos",
                valor=PortalDashboardState.total_contratos,
                icono="file-text",
                color_scheme=Colors.PORTAL_ACCENT_SCHEME,
                href=PortalDashboardState.ruta_contrato_principal,
                footer=rx.cond(
                    PortalDashboardState.contratos_por_vencer > 0,
                    rx.text(
                        PortalDashboardState.contratos_por_vencer.to(str)
                        + " por vencer",
                        font_size=Typography.SIZE_XS,
                        color=Colors.WARNING,
                    ),
                    rx.text(" ", font_size=Typography.SIZE_XS),
                ),
            ),
            metric_card(
                titulo="Plazas Ocupadas",
                valor=PortalDashboardState.total_plazas_ocupadas,
                icono="user-check",
                color_scheme="green",
                href=PortalDashboardState.ruta_rrhh_principal,
                footer=rx.text(
                    "de "
                    + PortalDashboardState.total_plazas.to(str)
                    + " ("
                    + PortalDashboardState.porcentaje_cobertura.to(str)
                    + "%)",
                    font_size=Typography.SIZE_XS,
                    color=rx.cond(
                        PortalDashboardState.porcentaje_cobertura >= 80,
                        Colors.SUCCESS,
                        rx.cond(
                            PortalDashboardState.porcentaje_cobertura >= 50,
                            Colors.WARNING,
                            Colors.ERROR,
                        ),
                    ),
                ),
            ),
            metric_card(
                titulo="Plazas Vacantes",
                valor=PortalDashboardState.total_plazas_vacantes,
                icono="user-x",
                color_scheme="orange",
                href=PortalDashboardState.ruta_rrhh_principal,
                footer=rx.text(
                    "Min "
                    + PortalDashboardState.plazas_minimas.to(str)
                    + " - Max "
                    + PortalDashboardState.plazas_maximas.to(str),
                    font_size=Typography.SIZE_XS,
                    color=Colors.TEXT_SECONDARY,
                ),
            ),
            spacing="4",
        ),
    )


# =============================================================================
# WIDGET: COBERTURA POR CONTRATO
# =============================================================================


def _badge_ocupadas_cat(cat: rx.Var) -> rx.Component:
    """Badge semaforo numerico por categoria."""
    ocupadas = cat["ocupadas"].to(int)
    minimo = cat["min"].to(int)
    return rx.badge(
        ocupadas.to(str),
        color_scheme=rx.cond(
            ocupadas < minimo,
            "red",
            rx.cond(ocupadas == minimo, "amber", "green"),
        ),
        variant="soft",
        size="1",
    )


def _categoria_row(cat: rx.Var) -> rx.Component:
    """Fila de categoria dentro de un contrato."""
    return rx.hstack(
        rx.text(
            cat["nombre"],
            font_size=Typography.SIZE_XS,
            color=Colors.TEXT_PRIMARY,
            flex="1",
            min_width="0",
            overflow="hidden",
            text_overflow="ellipsis",
            white_space="nowrap",
        ),
        rx.text(
            cat["min"].to(str),
            font_size=Typography.SIZE_XS,
            color=Colors.TEXT_SECONDARY,
            width="36px",
            text_align="right",
            font_variant_numeric="tabular-nums",
        ),
        rx.text(
            cat["max"].to(str),
            font_size=Typography.SIZE_XS,
            color=Colors.TEXT_SECONDARY,
            width="36px",
            text_align="right",
            font_variant_numeric="tabular-nums",
        ),
        rx.box(
            _badge_ocupadas_cat(cat),
            width="40px",
            display="flex",
            justify_content="flex-end",
        ),
        width="100%",
        align="center",
        spacing="2",
    )


def _contrato_cobertura_block(contrato: rx.Var) -> rx.Component:
    """Bloque de un contrato con su tabla de categorias."""
    return rx.vstack(
        # Label del contrato
        rx.text(
            contrato["contrato_numero"],
            font_size=Typography.SIZE_XS,
            font_weight=Typography.WEIGHT_SEMIBOLD,
            color=Colors.TEXT_MUTED,
            text_transform="uppercase",
            letter_spacing=Typography.LETTER_SPACING_WIDE,
        ),
        rx.separator(size="4", color_scheme="gray"),
        # Header de tabla
        rx.hstack(
            rx.text(
                "Categoria",
                font_size="11px",
                font_weight=Typography.WEIGHT_MEDIUM,
                color=Colors.TEXT_MUTED,
                text_transform="uppercase",
                flex="1",
            ),
            rx.text(
                "Min",
                font_size="11px",
                font_weight=Typography.WEIGHT_MEDIUM,
                color=Colors.TEXT_MUTED,
                text_transform="uppercase",
                width="36px",
                text_align="right",
            ),
            rx.text(
                "Max",
                font_size="11px",
                font_weight=Typography.WEIGHT_MEDIUM,
                color=Colors.TEXT_MUTED,
                text_transform="uppercase",
                width="36px",
                text_align="right",
            ),
            rx.text(
                "Ocup.",
                font_size="11px",
                font_weight=Typography.WEIGHT_MEDIUM,
                color=Colors.TEXT_MUTED,
                text_transform="uppercase",
                width="40px",
                text_align="right",
            ),
            width="100%",
            align="center",
            spacing="2",
        ),
        # Filas de categorias con scroll si son muchas
        rx.box(
            rx.vstack(
                rx.foreach(contrato["categorias"].to(list[dict]), _categoria_row),
                spacing="1",
                width="100%",
            ),
            max_height="200px",
            overflow_y="auto",
            width="100%",
        ),
        spacing="2",
        width="100%",
    )


def _leyenda_semaforo() -> rx.Component:
    """Leyenda de colores del semaforo."""

    def _item(color_scheme: str, label: str) -> rx.Component:
        return rx.hstack(
            rx.badge(" ", color_scheme=color_scheme, variant="soft", size="1"),
            rx.text(label, font_size="11px", color=Colors.TEXT_MUTED),
            spacing="1",
            align="center",
        )

    return rx.hstack(
        _item("green", "Sobre min"),
        _item("amber", "En min"),
        _item("red", "Bajo min"),
        spacing="3",
        width="100%",
        justify="start",
        padding_top="2",
    )


def _widget_cobertura() -> rx.Component:
    return _widget_container(
        _widget_header(
            "Cobertura por contrato", "Ver plazas", "/portal/empleados?view=plaza"
        ),
        rx.cond(
            PortalDashboardState.tiene_cobertura,
            rx.vstack(
                rx.foreach(
                    PortalDashboardState.cobertura_por_contrato,
                    _contrato_cobertura_block,
                ),
                _leyenda_semaforo(),
                spacing="4",
                width="100%",
            ),
            rx.center(
                rx.text(
                    "Sin contratos con personal",
                    font_size=Typography.SIZE_XS,
                    color=Colors.TEXT_MUTED,
                ),
                padding="4",
                width="100%",
            ),
        ),
    )


# =============================================================================
# WIDGET: ESTADO DE NOMINA
# =============================================================================


def _widget_nomina() -> rx.Component:
    return _widget_container(
        _widget_header("Estado de nomina", "Ir a nominas", "/portal/nominas"),
        rx.cond(
            PortalDashboardState.tiene_nomina_activa,
            rx.vstack(
                rx.text(
                    PortalDashboardState.nomina_periodo_label,
                    font_size=Typography.SIZE_XS,
                    color=Colors.TEXT_SECONDARY,
                ),
                payroll_period_status_badge(PortalDashboardState.nomina_estatus),
                spacing="2",
                width="100%",
            ),
            rx.center(
                rx.text(
                    "Sin periodos abiertos",
                    font_size=Typography.SIZE_XS,
                    color=Colors.TEXT_MUTED,
                ),
                padding="4",
                width="100%",
            ),
        ),
    )


# =============================================================================
# WIDGET: ENTREGABLES DEL MES
# =============================================================================


def _entregable_row(item: rx.Var) -> rx.Component:
    return rx.hstack(
        rx.vstack(
            rx.text(
                item["nombre"],
                font_size=Typography.SIZE_SM,
                font_weight=Typography.WEIGHT_MEDIUM,
                color=Colors.TEXT_PRIMARY,
            ),
            rx.text(
                item["contrato_codigo"],
                font_size=Typography.SIZE_XS,
                color=Colors.TEXT_MUTED,
            ),
            spacing="0",
        ),
        rx.spacer(),
        rx.match(
            item["estatus"],
            (
                "PENDIENTE",
                rx.badge(
                    StatusColors.get_entregable_status_label("PENDIENTE"),
                    color_scheme=StatusColors.get_entregable_status_color_scheme(
                        "PENDIENTE"
                    ),
                    size="1",
                    variant="soft",
                ),
            ),
            (
                "EN_REVISION",
                rx.badge(
                    StatusColors.get_entregable_status_label("EN_REVISION"),
                    color_scheme=StatusColors.get_entregable_status_color_scheme(
                        "EN_REVISION"
                    ),
                    size="1",
                    variant="soft",
                ),
            ),
            (
                "APROBADO",
                rx.badge(
                    StatusColors.get_entregable_status_label("APROBADO"),
                    color_scheme=StatusColors.get_entregable_status_color_scheme(
                        "APROBADO"
                    ),
                    size="1",
                    variant="soft",
                ),
            ),
            (
                "RECHAZADO",
                rx.badge(
                    StatusColors.get_entregable_status_label("RECHAZADO"),
                    color_scheme=StatusColors.get_entregable_status_color_scheme(
                        "RECHAZADO"
                    ),
                    size="1",
                    variant="soft",
                ),
            ),
            (
                "FACTURADO",
                rx.badge(
                    StatusColors.get_entregable_status_label("FACTURADO"),
                    color_scheme=StatusColors.get_entregable_status_color_scheme(
                        "FACTURADO"
                    ),
                    size="1",
                    variant="soft",
                ),
            ),
            (
                "PAGADO",
                rx.badge(
                    StatusColors.get_entregable_status_label("PAGADO"),
                    color_scheme=StatusColors.get_entregable_status_color_scheme(
                        "PAGADO"
                    ),
                    size="1",
                    variant="soft",
                ),
            ),
            rx.badge(item["estatus"], color_scheme="gray", size="1", variant="soft"),
        ),
        width="100%",
        align="center",
        padding_y="1",
    )


def _widget_entregables() -> rx.Component:
    return _widget_container(
        _widget_header("Entregables", "Ver todos", "/portal/entregables"),
        rx.cond(
            PortalDashboardState.tiene_entregables,
            rx.vstack(
                rx.hstack(
                    rx.text(
                        PortalDashboardState.entregables_completados.to(str)
                        + " de "
                        + PortalDashboardState.entregables_total.to(str)
                        + " completados",
                        font_size=Typography.SIZE_XS,
                        color=Colors.TEXT_SECONDARY,
                    ),
                    width="100%",
                ),
                rx.foreach(
                    PortalDashboardState.entregables_del_mes,
                    _entregable_row,
                ),
                spacing="2",
                width="100%",
            ),
            rx.center(
                rx.text(
                    "Sin entregables registrados",
                    font_size=Typography.SIZE_XS,
                    color=Colors.TEXT_MUTED,
                ),
                padding="4",
                width="100%",
            ),
        ),
    )


# =============================================================================
# WIDGET: AUSENCIAS RECIENTES (Top 5 empleados)
# =============================================================================


def _ausencia_empleado_row(item: rx.Var) -> rx.Component:
    return rx.hstack(
        rx.text(
            item["nombre"],
            font_size=Typography.SIZE_SM,
            color=Colors.TEXT_PRIMARY,
        ),
        rx.spacer(),
        rx.badge(
            item["total"].to(str),
            color_scheme="red",
            variant="soft",
            size="1",
        ),
        width="100%",
        align="center",
        padding_y="1",
    )


def _widget_ausencias_empleados() -> rx.Component:
    return _widget_container(
        _widget_header("Incidencias del mes", "Ver asistencias", "/portal/asistencias"),
        rx.cond(
            PortalDashboardState.tiene_ausencias,
            rx.vstack(
                rx.text(
                    PortalDashboardState.total_faltas_mes.to(str)
                    + " incidencias registradas",
                    font_size=Typography.SIZE_XS,
                    color=Colors.TEXT_SECONDARY,
                ),
                rx.foreach(
                    PortalDashboardState.top_ausencias_empleados,
                    _ausencia_empleado_row,
                ),
                spacing="2",
                width="100%",
            ),
            rx.center(
                rx.text(
                    "Sin incidencias este mes",
                    font_size=Typography.SIZE_XS,
                    color=Colors.TEXT_MUTED,
                ),
                padding="4",
                width="100%",
            ),
        ),
    )


# =============================================================================
# WIDGET: TIPO DE AUSENCIA (Top 5 tipos)
# =============================================================================


def _tipo_ausencia_row(item: rx.Var) -> rx.Component:
    return rx.hstack(
        rx.text(
            item["tipo"],
            font_size=Typography.SIZE_SM,
            color=Colors.TEXT_PRIMARY,
        ),
        rx.spacer(),
        rx.text(
            item["cantidad"].to(str),
            font_size=Typography.SIZE_SM,
            font_weight=Typography.WEIGHT_SEMIBOLD,
            color=Colors.TEXT_SECONDARY,
        ),
        width="100%",
        align="center",
        padding_y="1",
    )


def _widget_tipos_ausencia() -> rx.Component:
    return _widget_container(
        _widget_header("Por tipo de incidencia"),
        rx.cond(
            PortalDashboardState.tiene_ausencias,
            rx.vstack(
                rx.foreach(
                    PortalDashboardState.top_tipos_ausencia,
                    _tipo_ausencia_row,
                ),
                spacing="1",
                width="100%",
            ),
            rx.center(
                rx.text(
                    "Sin datos",
                    font_size=Typography.SIZE_XS,
                    color=Colors.TEXT_MUTED,
                ),
                padding="4",
                width="100%",
            ),
        ),
    )


# =============================================================================
# WIDGET: GASTOS (Placeholder)
# =============================================================================


def _widget_gastos_placeholder() -> rx.Component:
    return rx.box(
        _widget_container(
            _widget_header("Gastos del mes"),
            rx.center(
                rx.vstack(
                    rx.icon("wallet", size=32, color=Colors.TEXT_MUTED),
                    rx.text(
                        "Próximamente",
                        font_size=Typography.SIZE_XS,
                        color=Colors.TEXT_MUTED,
                    ),
                    spacing="2",
                    align="center",
                ),
                padding="6",
                width="100%",
            ),
        ),
        opacity="0.5",
        width="100%",
    )


# =============================================================================
# GRID DE SEGUIMIENTO
# =============================================================================


def _seguimiento_grid() -> rx.Component:
    """Grid de 6 widgets en 2 columnas con skeleton loading."""
    return rx.cond(
        PortalDashboardState.loading,
        rx.grid(
            *[_widget_skeleton() for _ in range(6)],
            columns=rx.breakpoints(initial="1", md="2"),
            spacing="4",
            width="100%",
        ),
        rx.grid(
            _widget_cobertura(),
            _widget_nomina(),
            _widget_entregables(),
            _widget_ausencias_empleados(),
            _widget_gastos_placeholder(),
            _widget_tipos_ausencia(),
            columns=rx.breakpoints(initial="1", md="2"),
            spacing="4",
            width="100%",
        ),
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
                    PortalDashboardState.nombre_usuario,
                    rx.text("Bienvenido, ", PortalDashboardState.nombre_usuario),
                    "Dashboard",
                ),
                subtitulo=PortalDashboardState.nombre_empresa_actual,
                icono="layout-dashboard",
                color_icono=Colors.PORTAL_ACCENT_SCHEME,
            ),
            content=rx.vstack(
                _section_label("RESUMEN OPERATIVO"),
                _metricas_grid(),
                _section_label("SEGUIMIENTO"),
                _seguimiento_grid(),
                spacing="6",
                width="100%",
            ),
        ),
        width="100%",
        min_height="100vh",
        on_mount=PortalDashboardState.on_mount_dashboard,
    )
