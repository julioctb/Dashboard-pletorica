"""
Página del dashboard de nóminas.

Mantiene el bloque operativo y el resumen del período seleccionado con
una presentación alineada al design system.
"""
import reflex as rx

from core.presentation.components.ui import metric_card, payroll_period_status_badge
from core.presentation.layouts.backoffice import page_header, page_layout
from core.presentation.pages.backoffice.nominas.dashboard_state import NominaDashboardState
from core.presentation.theme import Colors, Radius, Spacing, Typography


def _opcion_anio(anio: dict) -> rx.Component:
    return rx.select.item(
        anio["label"],
        value=anio["value"],
    )


def selector_anio_dashboard() -> rx.Component:
    return rx.select.root(
        rx.select.trigger(placeholder="Año", width="120px"),
        rx.select.content(
            rx.foreach(
                NominaDashboardState.anios_disponibles,
                _opcion_anio,
            ),
        ),
        value=NominaDashboardState.filtro_anio,
        on_change=NominaDashboardState.cambiar_filtro_anio,
        size="2",
    )


def _opcion_contrato(contrato: dict) -> rx.Component:
    return rx.select.item(
        contrato["label"],
        value=contrato["value"],
    )


def selector_contrato_dashboard() -> rx.Component:
    return rx.select.root(
        rx.select.trigger(placeholder="Contrato", width="320px"),
        rx.select.content(
            rx.foreach(
                NominaDashboardState.contratos_nomina_opciones,
                _opcion_contrato,
            ),
        ),
        value=NominaDashboardState.filtro_contrato_nomina_id,
        on_change=NominaDashboardState.cambiar_filtro_contrato_nomina,
        size="2",
    )


def _section_label(texto: str) -> rx.Component:
    return rx.text(
        texto,
        font_size=Typography.SIZE_XS,
        font_weight=Typography.WEIGHT_SEMIBOLD,
        color=Colors.TEXT_MUTED,
        text_transform="uppercase",
        letter_spacing=Typography.LETTER_SPACING_WIDE,
    )


def _section_header(
    titulo: str,
    *,
    badge: rx.Component | None = None,
    right: rx.Component | None = None,
) -> rx.Component:
    return rx.hstack(
        rx.hstack(
            _section_label(titulo),
            badge if badge is not None else rx.fragment(),
            spacing="2",
            align="center",
        ),
        rx.spacer(),
        right if right is not None else rx.fragment(),
        width="100%",
        align="center",
        spacing="2",
        wrap="wrap",
    )


def _metric_tile(
    titulo: str,
    valor: rx.Var | str,
    *,
    hint: rx.Var | str | None = None,
    accent_color: rx.Var | str | None = None,
    footer: rx.Component | None = None,
) -> rx.Component:
    return metric_card(
        titulo=titulo,
        valor=valor,
        icono=None,
        show_icon=False,
        background=Colors.SECONDARY_LIGHT,
        border="none",
        hoverable=False,
        value_color=accent_color,
        descripcion=hint,
        footer=footer,
        align="center",
    )


def _progress_bar(value_width: rx.Var | str) -> rx.Component:
    return rx.box(
        rx.box(
            height="4px",
            width=value_width,
            background=Colors.PRIMARY,
            border_radius=Radius.FULL,
        ),
        width="100%",
        height="4px",
        background=Colors.BORDER,
        border_radius=Radius.FULL,
        overflow="hidden",
    )


def _progress_footer() -> rx.Component:
    return rx.vstack(
        _progress_bar(NominaDashboardState.cobertura_plazas_width),
        rx.text(
            NominaDashboardState.cobertura_plazas_hint,
            font_size=Typography.SIZE_XS,
            color=Colors.TEXT_SECONDARY,
            text_align="center",
            width="100%",
        ),
        spacing="2",
        width="100%",
        align="center",
    )


def _metric_skeleton() -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.skeleton(width="92px", height="12px"),
            rx.skeleton(width="86px", height="30px"),
            rx.skeleton(width="132px", height="12px"),
            spacing="2",
            align="center",
            width="100%",
        ),
        width="100%",
        background=Colors.SECONDARY_LIGHT,
        border_radius=Radius.LG,
        padding=Spacing.MD,
    )


def _header_periodo_skeleton() -> rx.Component:
    return rx.hstack(
        rx.skeleton(width="112px", height="24px", border_radius=Radius.FULL),
        rx.spacer(),
        rx.skeleton(width="220px", height="16px"),
        width="100%",
        align="center",
        spacing="2",
    )


def _section_skeleton(*, title: str, columns: str, cards: int, right: rx.Component | None = None) -> rx.Component:
    return rx.vstack(
        _section_header(title, right=right),
        rx.grid(
            *[_metric_skeleton() for _ in range(cards)],
            columns=rx.breakpoints(initial="1", sm="2", lg=columns),
            gap=Spacing.SM,
            width="100%",
        ),
        spacing="3",
        width="100%",
    )


def skeleton_dashboard_nomina() -> rx.Component:
    return rx.vstack(
        _section_skeleton(title="Plantilla", columns="4", cards=4),
        _section_skeleton(title="Incidencias del periodo", columns="4", cards=4),
        _section_skeleton(
            title="Nómina del periodo",
            columns="4",
            cards=4,
            right=_header_periodo_skeleton(),
        ),
        spacing="4",
        width="100%",
    )


def _categoria_card(categoria: dict) -> rx.Component:
    return _metric_tile(
        categoria["label"],
        categoria["valor"].to(str),
    )


def _seccion_plantilla() -> rx.Component:
    return rx.vstack(
        _section_header("Plantilla"),
        rx.grid(
            _metric_tile(
                "Activos / plazas",
                NominaDashboardState.valor_activos_card,
                footer=_progress_footer(),
            ),
            rx.foreach(
                NominaDashboardState.categorias_plantilla,
                _categoria_card,
            ),
            _metric_tile(
                "Movimientos",
                NominaDashboardState.total_movimientos_periodo.to(str),
                hint=NominaDashboardState.hint_movimientos_periodo,
            ),
            columns=rx.breakpoints(initial="1", sm="2", lg="4"),
            gap=Spacing.SM,
            width="100%",
        ),
        spacing="3",
        width="100%",
    )


def _seccion_incidencias_periodo() -> rx.Component:
    return rx.vstack(
        _section_header("Incidencias del periodo"),
        rx.grid(
            _metric_tile(
                "Faltas",
                NominaDashboardState.total_faltas_periodo.to(str),
                hint=NominaDashboardState.hint_faltas_periodo,
            ),
            _metric_tile(
                "Incapacidades",
                NominaDashboardState.total_incapacidades_dias.to(str),
                hint=NominaDashboardState.hint_incapacidades_periodo,
            ),
            _metric_tile(
                "Horas extra",
                NominaDashboardState.total_horas_extra_periodo.to(str),
                hint=NominaDashboardState.hint_horas_extra_periodo,
            ),
            _metric_tile(
                "Permisos",
                NominaDashboardState.total_permisos_periodo.to(str),
                hint=rx.cond(
                    NominaDashboardState.total_permisos_periodo > 0,
                    NominaDashboardState.total_permisos_periodo.to(str) + " permisos",
                    "",
                ),
            ),
            columns=rx.breakpoints(initial="1", sm="2", lg="4"),
            gap=Spacing.SM,
            width="100%",
        ),
        spacing="3",
        width="100%",
    )


def grid_cards_operativas() -> rx.Component:
    return rx.vstack(
        _seccion_plantilla(),
        _seccion_incidencias_periodo(),
        spacing="4",
        width="100%",
    )


def callout_warning_operativo() -> rx.Component:
    return rx.cond(
        NominaDashboardState.warning_resumen_operativo != "",
        rx.callout.root(
            rx.callout.icon(rx.icon("triangle-alert", size=16)),
            rx.callout.text(NominaDashboardState.warning_resumen_operativo),
            color_scheme="orange",
            variant="soft",
            width="100%",
        ),
        rx.fragment(),
    )


def resumen_financiero_periodo() -> rx.Component:
    return rx.cond(
        NominaDashboardState.tiene_resumen,
        rx.vstack(
            _section_header(
                "Nómina del periodo",
                badge=payroll_period_status_badge(
                    NominaDashboardState.periodo_estatus_actual
                ),
                right=rx.text(
                    NominaDashboardState.periodo_actual_header_label,
                    font_size=Typography.SIZE_SM,
                    font_weight=Typography.WEIGHT_MEDIUM,
                    color=Colors.PRIMARY,
                ),
            ),
            rx.grid(
                _metric_tile(
                    "Empleados",
                    NominaDashboardState.total_empleados_kpi.to(str),
                    hint=NominaDashboardState.delta_empleados_label,
                ),
                _metric_tile(
                    "Neto a dispersar",
                    NominaDashboardState.neto_a_dispersar_display,
                    hint=NominaDashboardState.delta_neto_label,
                    accent_color=rx.cond(
                        NominaDashboardState.neto_a_dispersar_display == "—",
                        Colors.TEXT_MUTED,
                        Colors.PRIMARY,
                    ),
                ),
                _metric_tile(
                    "Transferencia",
                    NominaDashboardState.total_transferencia_empleados.to(str),
                    hint=NominaDashboardState.monto_transferencia_total_fmt,
                ),
                _metric_tile(
                    "Efectivo",
                    NominaDashboardState.total_efectivo_empleados.to(str),
                    hint=NominaDashboardState.monto_efectivo_total_fmt,
                ),
                columns=rx.breakpoints(initial="1", sm="2", lg="4"),
                gap=Spacing.SM,
                width="100%",
            ),
            rx.cond(
                NominaDashboardState.referencia_periodo_anterior_label != "",
                rx.text(
                    NominaDashboardState.referencia_periodo_anterior_label,
                    font_size=Typography.SIZE_XS,
                    color=Colors.TEXT_MUTED,
                    text_align="center",
                    width="100%",
                ),
                rx.fragment(),
            ),
            spacing="3",
            width="100%",
        ),
        rx.fragment(),
    )


def _contenido_dashboard() -> rx.Component:
    return rx.vstack(
        callout_warning_operativo(),
        grid_cards_operativas(),
        resumen_financiero_periodo(),
        spacing="4",
        width="100%",
    )


def dashboard_nomina_page() -> rx.Component:
    return rx.box(
        page_layout(
            header=rx.box(
                page_header(
                    titulo="Nóminas",
                    subtitulo=NominaDashboardState.contrato_activo_label,
                    icono="chart-bar",
                    accion_principal=rx.hstack(
                        selector_contrato_dashboard(),
                        selector_anio_dashboard(),
                        spacing="3",
                        align="center",
                        wrap="wrap",
                    ),
                ),
                width="100%",
                max_width="1024px",
                margin_x="auto",
            ),
            content=rx.box(
                rx.cond(
                    NominaDashboardState.loading,
                    skeleton_dashboard_nomina(),
                    _contenido_dashboard(),
                ),
                width="100%",
                max_width="1024px",
                margin_x="auto",
            ),
        ),
        width="100%",
        min_height="100vh",
        on_mount=NominaDashboardState.on_mount_dashboard,
    )
