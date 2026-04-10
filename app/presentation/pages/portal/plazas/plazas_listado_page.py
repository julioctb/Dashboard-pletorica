"""Página principal de plazas en portal."""

from __future__ import annotations

import reflex as rx

from app.presentation.components.ui import (
    empty_state_card,
    feedback_callout,
    metric_card,
    metric_card_grid,
    page_header,
    table_shell,
)
from app.presentation.layouts.backoffice import page_layout
from app.presentation.theme import Colors, Radius, Spacing, Transitions, Typography

from .state import PlazasListadoState


PLAZAS_HEADERS = [
    {"nombre": "Contrato", "ancho": "200px", "header_align": "left"},
    {"nombre": "Sueldo", "ancho": "140px", "header_align": "right"},
    {"nombre": "Mínimo", "ancho": "80px", "header_align": "center"},
    {"nombre": "Máximo", "ancho": "80px", "header_align": "center"},
    {"nombre": "Ocupadas", "ancho": "100px", "header_align": "center"},
]


def _metricas() -> rx.Component:
    card_props = {
        "icono": None,
        "show_icon": False,
        "align": "center",
        "background": Colors.SECONDARY_LIGHT,
        "border": "none",
        "hoverable": False,
    }

    return metric_card_grid(
        metric_card(
            titulo="Plazas configuradas",
            valor=PlazasListadoState.plazas_configuradas,
            value_color=Colors.TEXT_PRIMARY,
            descripcion=PlazasListadoState.descripcion_metrica_plazas,
            **card_props,
        ),
        metric_card(
            titulo="Cobertura",
            valor=PlazasListadoState.cobertura_pct_texto,
            value_color=PlazasListadoState.cobertura_color_metrica,
            descripcion=PlazasListadoState.descripcion_metrica_cobertura,
            **card_props,
        ),
        metric_card(
            titulo="Presupuesto/mes",
            valor=PlazasListadoState.presupuesto_mensual_fmt,
            value_color=Colors.TEXT_PRIMARY,
            descripcion=PlazasListadoState.descripcion_metrica_presupuesto,
            **card_props,
        ),
        metric_card(
            titulo="Costo real/mes",
            valor=PlazasListadoState.costo_real_mensual_fmt,
            value_color=Colors.TEXT_PRIMARY,
            descripcion=PlazasListadoState.descripcion_metrica_costo_real,
            **card_props,
        ),
    )


def _contrato_chip(chip: dict) -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.text(
                    chip["codigo_display"],
                    font_size=Typography.SIZE_SM,
                    font_weight=Typography.WEIGHT_SEMIBOLD,
                ),
                rx.spacer(),
                rx.text(
                    chip["cobertura_texto"],
                    font_size=Typography.SIZE_XS,
                    color=chip["cobertura_color"],
                    font_weight=Typography.WEIGHT_MEDIUM,
                    font_variant_numeric="tabular-nums",
                ),
                width="100%",
                align="center",
                spacing="2",
            ),
            rx.text(
                chip["descripcion"],
                font_size=Typography.SIZE_XS,
                color=Colors.TEXT_MUTED,
                width="100%",
            ),
            spacing="1",
            align_items="start",
            width="100%",
        ),
        min_width="220px",
        padding=Spacing.MD,
        border=f"1px solid {Colors.BORDER}",
        border_color=rx.cond(chip["activo"], Colors.PORTAL_PRIMARY_TEXT, Colors.BORDER),
        border_radius=Radius.LG,
        background=rx.cond(chip["activo"], Colors.PORTAL_PRIMARY_LIGHTER, Colors.SURFACE),
        cursor="pointer",
        on_click=PlazasListadoState.seleccionar_contrato(chip["selector_value"]),
        transition=Transitions.NORMAL,
        _hover={
            "background": Colors.SECONDARY_LIGHT,
            "border_color": Colors.BORDER_STRONG,
        },
    )


def _selector_contrato() -> rx.Component:
    return rx.flex(
        rx.foreach(
            PlazasListadoState.chips_contrato,
            _contrato_chip,
        ),
        width="100%",
        gap=Spacing.SM,
        overflow_x="auto",
        padding_bottom=Spacing.XS,
    )


def _encabezado_tabla() -> rx.Component:
    return rx.flex(
        rx.vstack(
            rx.text(
                "Categorías por contrato",
                font_size=Typography.SIZE_LG,
                font_weight=Typography.WEIGHT_SEMIBOLD,
                color=Colors.TEXT_PRIMARY,
            ),
            rx.text(
                "Sueldos, plazas y cobertura sobre contratos activos.",
                font_size=Typography.SIZE_SM,
                color=Colors.TEXT_SECONDARY,
            ),
            spacing="1",
            align_items="start",
        ),
        rx.cond(
            PlazasListadoState.puede_editar_configuracion,
            rx.button(
                "Editar configuración",
                variant="ghost",
                color_scheme=Colors.PORTAL_ACCENT_SCHEME,
                on_click=PlazasListadoState.ir_a_editar_configuracion,
            ),
            rx.fragment(),
        ),
        width="100%",
        align="center",
        justify="between",
        gap=Spacing.SM,
        wrap="wrap",
    )


def _empty_state() -> rx.Component:
    return empty_state_card(
        title=PlazasListadoState.titulo_empty_state,
        description=PlazasListadoState.descripcion_empty_state,
        icon="layout-grid",
        action_button=rx.button(
            "Ir a contratos",
            on_click=PlazasListadoState.ir_a_contratos,
            color_scheme=Colors.PORTAL_ACCENT_SCHEME,
            size="2",
        ),
    )


def _fila_separador(item: dict) -> rx.Component:
    return rx.table.row(
        rx.table.cell(
            rx.vstack(
                rx.text(
                    item["nombre_categoria"],
                    font_weight=Typography.WEIGHT_MEDIUM,
                    color=Colors.TEXT_PRIMARY,
                    font_size=Typography.SIZE_SM,
                ),
                rx.text(
                    item["meta_texto"],
                    font_size=Typography.SIZE_XS,
                    color=Colors.TEXT_MUTED,
                ),
                spacing="1",
                align_items="start",
            ),
            text_align="left",
        ),
        rx.table.cell(
            rx.text(
                item["sueldo_separador_texto"],
                font_size=Typography.SIZE_XS,
                color=Colors.TEXT_MUTED,
                font_variant_numeric="tabular-nums",
            ),
            text_align="right",
        ),
        rx.table.cell(
            rx.text(
                item["sum_min_texto"],
                font_weight=Typography.WEIGHT_MEDIUM,
                color=Colors.TEXT_PRIMARY,
                font_variant_numeric="tabular-nums",
                text_align="center",
            ),
            text_align="center",
        ),
        rx.table.cell(
            rx.text(
                item["sum_max_texto"],
                font_weight=Typography.WEIGHT_MEDIUM,
                color=Colors.TEXT_PRIMARY,
                font_variant_numeric="tabular-nums",
                text_align="center",
            ),
            text_align="center",
        ),
        rx.table.cell(
            rx.text(
                item["cobertura_texto"],
                font_weight=Typography.WEIGHT_MEDIUM,
                color=item["cobertura_color"],
                font_variant_numeric="tabular-nums",
                text_align="center",
            ),
            text_align="center",
        ),
        background=Colors.SECONDARY_LIGHT,
    )


def _fila_detalle(item: dict) -> rx.Component:
    return rx.table.row(
        rx.table.cell(
            rx.vstack(
                rx.badge(
                    item["codigo_contrato"],
                    color_scheme=Colors.PORTAL_ACCENT_SCHEME,
                    size="1",
                    variant="soft",
                ),
                rx.text(
                    item["descripcion_contrato"],
                    font_size=Typography.SIZE_XS,
                    color=Colors.TEXT_MUTED,
                ),
                spacing="1",
                align_items="start",
            ),
            text_align="left",
        ),
        rx.table.cell(
            rx.vstack(
                rx.text(
                    item["sueldo_bruto_fmt"],
                    font_weight=Typography.WEIGHT_MEDIUM,
                    color=Colors.TEXT_PRIMARY,
                    font_size=Typography.SIZE_SM,
                    font_variant_numeric="tabular-nums",
                ),
                rx.text(
                    item["sueldo_diario_label"],
                    font_size=Typography.SIZE_XS,
                    color=Colors.TEXT_MUTED,
                    font_variant_numeric="tabular-nums",
                ),
                rx.cond(
                    item["mostrar_warning_salario_minimo"],
                    rx.flex(
                        rx.icon("triangle-alert", size=11, color=Colors.WARNING),
                        rx.text(
                            "Bajo salario mínimo",
                            font_size=Typography.SIZE_XS,
                            color=Colors.WARNING,
                        ),
                        align="center",
                        gap=Spacing.XS,
                    ),
                    rx.fragment(),
                ),
                spacing="1",
                align_items="end",
                width="100%",
            ),
            text_align="right",
        ),
        rx.table.cell(
            rx.text(
                item["min_plazas_texto"],
                font_weight=Typography.WEIGHT_MEDIUM,
                color=Colors.TEXT_PRIMARY,
                font_variant_numeric="tabular-nums",
                text_align="center",
            ),
            text_align="center",
        ),
        rx.table.cell(
            rx.cond(
                item["max_plazas_es_null"],
                rx.text("—", color=Colors.TEXT_MUTED, text_align="center"),
                rx.text(
                    item["max_plazas_texto"],
                    font_weight=Typography.WEIGHT_MEDIUM,
                    color=Colors.TEXT_PRIMARY,
                    font_variant_numeric="tabular-nums",
                    text_align="center",
                ),
            ),
            text_align="center",
        ),
        rx.table.cell(
            rx.center(
                rx.badge(
                    item["cobertura_texto"],
                    color_scheme=item["cobertura_color_scheme"],
                    size="1",
                    variant="soft",
                    font_variant_numeric="tabular-nums",
                ),
                width="100%",
            ),
            text_align="center",
        ),
    )


def _fila_tabla(item: dict) -> rx.Component:
    return rx.cond(
        item["es_separador"],
        _fila_separador(item),
        _fila_detalle(item),
    )


def _tabla_categorias() -> rx.Component:
    return rx.box(
        table_shell(
            loading=PlazasListadoState.is_loading,
            headers=PLAZAS_HEADERS,
            rows=PlazasListadoState.filas_tabla,
            row_renderer=_fila_tabla,
            has_rows=PlazasListadoState.tiene_filas_tabla,
            empty_component=_empty_state(),
            total_caption=PlazasListadoState.caption_tabla,
            table_size="1",
            loading_rows=6,
        ),
        width="100%",
        overflow_x="auto",
    )


def plazas_listado_page() -> rx.Component:
    """Vista principal de plazas del portal."""
    return rx.box(
        page_layout(
            header=page_header(
                titulo="Plazas",
                subtitulo="Estructura organizacional y presupuesto",
                icono="layout-grid",
                color_icono=Colors.PORTAL_ACCENT_SCHEME,
                accion_principal=rx.button(
                    rx.icon("briefcase", size=16),
                    "Catálogo de puestos",
                    on_click=PlazasListadoState.ir_a_catalogo_puestos,
                    variant="outline",
                    color_scheme=Colors.PORTAL_ACCENT_SCHEME,
                ),
            ),
            content=rx.vstack(
                _metricas(),
                _selector_contrato(),
                rx.cond(
                    PlazasListadoState.mostrar_callout_sin_sede,
                    feedback_callout(
                        rx.text(
                            PlazasListadoState.mensaje_callout_sin_sede,
                            font_size=Typography.SIZE_SM,
                        ),
                        "warning",
                    ),
                    rx.fragment(),
                ),
                _encabezado_tabla(),
                _tabla_categorias(),
                spacing="4",
                width="100%",
            ),
        ),
        width="100%",
        min_height="100vh",
        on_mount=PlazasListadoState.cargar_contratos,
    )
