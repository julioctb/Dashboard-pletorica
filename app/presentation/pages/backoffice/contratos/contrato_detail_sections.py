"""Secciones reutilizables para el detalle visual de contratos."""

from __future__ import annotations

from typing import Any

import reflex as rx

from app.presentation.components.ui import (
    empty_state_card,
    metric_card,
    status_badge_reactive,
    table_shell,
)
from app.presentation.theme import (
    CardStyles,
    Colors,
    Radius,
    Spacing,
    Typography,
)


# =============================================================================
# HELPERS
# =============================================================================

_DASH = "\u2014"  # em-dash para datos vacíos


def contrato_detail_text(
    valor: Any,
    *,
    fallback: str = _DASH,
    weight: str | None = None,
    color: str = Colors.TEXT_PRIMARY,
    white_space: str | None = None,
    tabular_nums: bool = False,
) -> rx.Component:
    """Texto consistente para campos del detalle de contrato."""
    text_props: dict = {
        "font_size": Typography.SIZE_SM,
        "color": color,
    }
    if weight is not None:
        text_props["font_weight"] = weight
    if white_space is not None:
        text_props["white_space"] = white_space
    if tabular_nums:
        text_props["font_variant_numeric"] = "tabular-nums"

    return rx.cond(
        valor,
        rx.text(valor, **text_props),
        rx.text(
            fallback,
            font_size=Typography.SIZE_SM,
            color=Colors.TEXT_MUTED,
        ),
    )


def contrato_detail_field(label: str, contenido: rx.Component) -> rx.Component:
    """Campo de detalle en modo solo lectura."""
    return rx.vstack(
        rx.text(
            label,
            font_size=Typography.SIZE_XS,
            font_weight=Typography.WEIGHT_MEDIUM,
            color=Colors.TEXT_SECONDARY,
            text_transform="uppercase",
            letter_spacing="0.04em",
        ),
        contenido,
        spacing="1",
        width="100%",
        align="start",
    )


def _section_title(text: str) -> rx.Component:
    """Titulo de seccion dentro de una card."""
    return rx.text(
        text,
        font_size=Typography.SIZE_BASE,
        font_weight=Typography.WEIGHT_SEMIBOLD,
        color=Colors.TEXT_PRIMARY,
    )


def _section_subtitle(text: str) -> rx.Component:
    """Subtitulo descriptivo bajo un titulo de seccion."""
    return rx.text(
        text,
        font_size=Typography.SIZE_SM,
        color=Colors.TEXT_SECONDARY,
    )


def _section_card(*children: rx.Component) -> rx.Component:
    """Card de seccion alineada al design system."""
    return rx.card(
        rx.vstack(*children, spacing="4", width="100%"),
        width="100%",
        style={
            "border": f"1px solid {Colors.BORDER}",
            "border_radius": Radius.LG,
            "background": Colors.SURFACE,
            "padding": Spacing.XL,
        },
    )


# =============================================================================
# CATEGORIAS TABLE
# =============================================================================

def _categoria_detalle_row(categoria: dict) -> rx.Component:
    return rx.table.row(
        rx.table.cell(
            rx.cond(
                categoria["categoria_clave"],
                rx.badge(
                    categoria["categoria_clave"],
                    color_scheme="blue",
                    variant="soft",
                    size="1",
                ),
                rx.text(_DASH, size="2", color=Colors.TEXT_MUTED),
            ),
        ),
        rx.table.cell(
            rx.text(
                categoria["categoria_nombre"],
                size="2",
                color=Colors.TEXT_PRIMARY,
            ),
        ),
        rx.table.cell(
            rx.text(
                categoria["cantidad_minima"],
                size="2",
                color=Colors.TEXT_PRIMARY,
                font_variant_numeric="tabular-nums",
            ),
        ),
        rx.table.cell(
            rx.text(
                categoria["cantidad_maxima"],
                size="2",
                color=Colors.TEXT_PRIMARY,
                font_variant_numeric="tabular-nums",
            ),
        ),
        rx.table.cell(
            rx.text(
                categoria["costo_unitario_fmt"],
                size="2",
                weight="medium",
                color=Colors.TEXT_PRIMARY,
                font_variant_numeric="tabular-nums",
            ),
        ),
        rx.table.cell(
            rx.text(
                categoria["costo_minimo_fmt"],
                size="2",
                color=Colors.TEXT_SECONDARY,
                font_variant_numeric="tabular-nums",
            ),
        ),
        rx.table.cell(
            rx.text(
                categoria["costo_maximo_fmt"],
                size="2",
                color=Colors.TEXT_SECONDARY,
                font_variant_numeric="tabular-nums",
            ),
        ),
    )


# =============================================================================
# SECTIONS
# =============================================================================

def contrato_detail_info_sections(
    datos: Any,
    categorias: Any,
    *,
    total_categorias: Any,
    tiene_categorias: Any,
) -> rx.Component:
    """Contenido compartido de detalle de contrato para backoffice y portal."""
    return rx.vstack(
        # ── Informacion general ──────────────────────────────────────────
        _section_card(
            rx.hstack(
                rx.vstack(
                    _section_title("Informacion general"),
                    _section_subtitle(
                        "Resumen operativo y financiero del contrato.",
                    ),
                    spacing="1",
                    align="start",
                ),
                rx.spacer(),
                rx.badge(
                    datos["codigo"],
                    variant="outline",
                    size="2",
                    color_scheme=Colors.NEUTRAL_SCHEME,
                ),
                align="center",
                width="100%",
            ),
            rx.grid(
                contrato_detail_field(
                    "Empresa",
                    contrato_detail_text(datos["nombre_empresa_fmt"]),
                ),
                contrato_detail_field(
                    "Tipo de servicio",
                    contrato_detail_text(datos["nombre_servicio_fmt"]),
                ),
                contrato_detail_field(
                    "Tipo de contrato",
                    contrato_detail_text(datos["tipo_contrato_fmt"]),
                ),
                contrato_detail_field(
                    "Modalidad",
                    contrato_detail_text(datos["modalidad_adjudicacion_fmt"]),
                ),
                contrato_detail_field(
                    "Estatus",
                    status_badge_reactive(datos["estatus"], show_icon=True),
                ),
                contrato_detail_field(
                    "Folio institucion",
                    contrato_detail_text(datos["numero_folio_buap_fmt"]),
                ),
                columns=rx.breakpoints(initial="1", sm="2", lg="3"),
                spacing="4",
                width="100%",
            ),
        ),
        # ── Vigencia ─────────────────────────────────────────────────────
        _section_card(
            _section_title("Vigencia"),
            rx.grid(
                contrato_detail_field(
                    "Inicio",
                    contrato_detail_text(datos["fecha_inicio_fmt"]),
                ),
                contrato_detail_field(
                    "Fin",
                    contrato_detail_text(
                        rx.cond(datos["fecha_fin"], datos["fecha_fin_fmt"], ""),
                        fallback="Indefinido",
                    ),
                ),
                contrato_detail_field(
                    "Tipo de duracion",
                    contrato_detail_text(datos["tipo_duracion_fmt"]),
                ),
                contrato_detail_field(
                    "Vigencia",
                    rx.badge(
                        datos["vigencia_label"],
                        color_scheme=datos["vigencia_color_scheme"],
                        size="1",
                        variant="soft",
                    ),
                ),
                columns=rx.breakpoints(initial="1", sm="2", lg="3"),
                spacing="4",
                width="100%",
            ),
        ),
        # ── Planeacion de personal ───────────────────────────────────────
        _section_card(
            _section_title("Planeacion de personal"),
            rx.grid(
                metric_card(
                    titulo="Plazas minimas",
                    valor=datos["cantidad_plazas_minima"],
                    icono="users",
                    color_scheme="teal",
                    descripcion="Compromiso minimo del contrato",
                    hoverable=False,
                    background=Colors.SECONDARY_LIGHT,
                    border="none",
                ),
                metric_card(
                    titulo="Plazas maximas",
                    valor=datos["cantidad_plazas_maxima"],
                    icono="briefcase",
                    color_scheme="green",
                    descripcion="Capacidad maxima materializable",
                    hoverable=False,
                    background=Colors.SECONDARY_LIGHT,
                    border="none",
                ),
                metric_card(
                    titulo="Categorias",
                    valor=total_categorias,
                    icono="tags",
                    color_scheme="amber",
                    descripcion="Perfiles configurados en el contrato",
                    hoverable=False,
                    background=Colors.SECONDARY_LIGHT,
                    border="none",
                ),
                columns=rx.breakpoints(initial="1", sm="2", lg="3"),
                spacing="3",
                width="100%",
            ),
        ),
        # ── Montos del contrato ──────────────────────────────────────────
        _section_card(
            rx.hstack(
                _section_title("Montos del contrato"),
                rx.spacer(),
                rx.badge(
                    rx.cond(
                        datos["incluye_iva"],
                        "Incluye IVA",
                        "Sin IVA",
                    ),
                    color_scheme=Colors.NEUTRAL_SCHEME,
                    variant="soft",
                    size="1",
                ),
                align="center",
                width="100%",
            ),
            rx.grid(
                metric_card(
                    titulo="Monto minimo",
                    valor=datos["monto_minimo_fmt"],
                    icono="banknote",
                    color_scheme="teal",
                    descripcion="Estimacion minima del contrato",
                    hoverable=False,
                    background=Colors.SECONDARY_LIGHT,
                    border="none",
                ),
                metric_card(
                    titulo="Monto maximo",
                    valor=datos["monto_maximo_fmt"],
                    icono="wallet",
                    color_scheme="green",
                    descripcion="Tope autorizado del contrato",
                    hoverable=False,
                    background=Colors.SECONDARY_LIGHT,
                    border="none",
                ),
                columns=rx.breakpoints(initial="1", sm="2"),
                spacing="3",
                width="100%",
            ),
        ),
        # ── Categorias configuradas ──────────────────────────────────────
        _section_card(
            rx.hstack(
                _section_title("Categorias configuradas"),
                rx.spacer(),
                rx.cond(
                    tiene_categorias,
                    rx.badge(
                        total_categorias,
                        color_scheme=Colors.NEUTRAL_SCHEME,
                        variant="soft",
                    ),
                    rx.fragment(),
                ),
                width="100%",
                align="center",
            ),
            rx.cond(
                tiene_categorias,
                rx.box(
                    table_shell(
                        loading=False,
                        has_rows=True,
                        empty_component=rx.fragment(),
                        header_cells=[
                            rx.table.column_header_cell("Clave", width="90px"),
                            rx.table.column_header_cell("Categoria"),
                            rx.table.column_header_cell("Min.", width="70px"),
                            rx.table.column_header_cell("Max.", width="70px"),
                            rx.table.column_header_cell("Costo", width="120px"),
                            rx.table.column_header_cell("Monto min.", width="120px"),
                            rx.table.column_header_cell("Monto max.", width="120px"),
                        ],
                        body_component=rx.foreach(categorias, _categoria_detalle_row),
                    ),
                    overflow_x="auto",
                    width="100%",
                ),
                empty_state_card(
                    title="Sin categorias configuradas",
                    description="Este contrato no tiene un desglose de plazas por categoria capturado.",
                    icon="tags",
                ),
            ),
        ),
        # ── Objeto del contrato ──────────────────────────────────────────
        _section_card(
            _section_title("Objeto del contrato"),
            contrato_detail_text(
                datos["descripcion_objeto"],
                fallback="Sin objeto capturado",
                white_space="pre-wrap",
            ),
        ),
        # ── Notas (condicional) ──────────────────────────────────────────
        rx.cond(
            datos["notas"],
            _section_card(
                _section_title("Notas"),
                rx.text(
                    datos["notas"],
                    font_size=Typography.SIZE_SM,
                    color=Colors.TEXT_PRIMARY,
                ),
            ),
            rx.fragment(),
        ),
        spacing="4",
        width="100%",
    )
