"""Página principal de plazas con listado de contratos y cobertura."""

from __future__ import annotations

import reflex as rx

from app.presentation.components.ui import (
    empty_state_card,
    metric_card,
    status_badge_reactive,
    table_shell,
    table_text_sm,
)
from app.presentation.layouts.backoffice import page_header, page_layout
from app.presentation.theme import Colors, Radius, Typography

from .state import PlazasListadoState


PLAZAS_LISTADO_HEADERS = [
    {"nombre": "Contrato", "ancho": "28%", "header_align": "left"},
    {"nombre": "Vigencia", "ancho": "14%", "header_align": "center"},
    {"nombre": "Categorías", "ancho": "10%", "header_align": "center"},
    {"nombre": "Sedes", "ancho": "10%", "header_align": "center"},
    {"nombre": "Cobertura", "ancho": "16%", "header_align": "center"},
    {"nombre": "Costo/mes", "ancho": "12%", "header_align": "center"},
    {"nombre": "Estatus", "ancho": "10%", "header_align": "center"},
]


def _color_cobertura(cobertura_nivel: rx.Var | str) -> rx.Var | str:
    return rx.match(
        cobertura_nivel,
        ("ALTA", Colors.SUCCESS),
        ("MEDIA", Colors.WARNING),
        Colors.ERROR,
    )


def _contrato_row(contrato: rx.Var) -> rx.Component:
    cobertura_color = _color_cobertura(contrato["cobertura_nivel"])

    return rx.table.row(
        rx.table.cell(
            rx.flex(
                rx.link(
                    contrato["codigo"],
                    href="/portal/contratos/" + contrato["id"].to(str) + "/plazas",
                    font_weight=Typography.WEIGHT_MEDIUM,
                    color=Colors.TEXT_PRIMARY,
                    text_decoration="none",
                    _hover={
                        "color": Colors.PORTAL_PRIMARY_TEXT,
                        "text_decoration": "underline",
                    },
                ),
                rx.text(
                    contrato["descripcion"],
                    font_size=Typography.SIZE_XS,
                    color=Colors.TEXT_MUTED,
                ),
                direction="column",
                gap="1px",
                width="100%",
                min_width="0",
            ),
        ),
        rx.table.cell(
            table_text_sm(contrato["vigencia"], tone="secondary"),
            text_align="center",
        ),
        rx.table.cell(
            table_text_sm(contrato["categorias"].to(str), weight=Typography.WEIGHT_MEDIUM),
            text_align="center",
        ),
        rx.table.cell(
            table_text_sm(contrato["sedes"].to(str), weight=Typography.WEIGHT_MEDIUM),
            text_align="center",
        ),
        rx.table.cell(
            rx.flex(
                rx.text(
                    contrato["ocupadas"].to(str) + "/" + contrato["total_plazas"].to(str),
                    font_size=Typography.SIZE_SM,
                    font_weight=Typography.WEIGHT_MEDIUM,
                    color=cobertura_color,
                ),
                rx.box(
                    rx.box(
                        width=contrato["cobertura_pct"].to(str) + "%",
                        height="100%",
                        border_radius=Radius.SM,
                        background=cobertura_color,
                    ),
                    width="72px",
                    height="6px",
                    border_radius=Radius.SM,
                    background=Colors.SECONDARY_LIGHT,
                    overflow="hidden",
                ),
                direction="column",
                align="center",
                justify="center",
                gap="3px",
                width="100%",
            ),
            text_align="center",
        ),
        rx.table.cell(
            rx.text(
                contrato["costo_mensual_fmt"],
                font_size=Typography.SIZE_SM,
                color=Colors.TEXT_PRIMARY,
                font_weight=Typography.WEIGHT_MEDIUM,
            ),
            text_align="center",
        ),
        rx.table.cell(
            status_badge_reactive(contrato["estatus"]),
            text_align="center",
        ),
        cursor="pointer",
        _hover={"background": Colors.SURFACE_HOVER},
        on_click=PlazasListadoState.ir_a_plazas_contrato(contrato["id"]),
    )


def plazas_listado_page() -> rx.Component:
    """Vista principal de plazas en portal (nivel 1)."""
    return rx.box(
        page_layout(
            header=page_header(
                titulo="Plazas",
                subtitulo="Configuración y cobertura contractual",
                icono="box",
                color_icono=Colors.PORTAL_ACCENT_SCHEME,
            ),
            content=rx.vstack(
                rx.grid(
                    metric_card(
                        titulo="Contratos",
                        valor=PlazasListadoState.total_contratos,
                        icono=None,
                        color_scheme=Colors.NEUTRAL_SCHEME,
                        show_icon=False,
                        align="center",
                    ),
                    metric_card(
                        titulo="Plazas totales",
                        valor=PlazasListadoState.total_plazas,
                        icono=None,
                        color_scheme=Colors.NEUTRAL_SCHEME,
                        show_icon=False,
                        align="center",
                    ),
                    metric_card(
                        titulo="Ocupadas",
                        valor=PlazasListadoState.total_ocupadas,
                        icono=None,
                        color_scheme="green",
                        show_icon=False,
                        align="center",
                        value_color=Colors.SUCCESS,
                        descripcion=PlazasListadoState.cobertura_global + " cobertura",
                    ),
                    metric_card(
                        titulo="Vacantes",
                        valor=PlazasListadoState.total_vacantes,
                        icono=None,
                        color_scheme=Colors.WARNING_SCHEME,
                        show_icon=False,
                        align="center",
                        value_color=Colors.WARNING,
                    ),
                    columns=rx.breakpoints(initial="2", md="4"),
                    spacing="3",
                    width="100%",
                ),
                rx.box(
                    table_shell(
                        loading=PlazasListadoState.is_loading,
                        headers=PLAZAS_LISTADO_HEADERS,
                        rows=PlazasListadoState.contratos,
                        row_renderer=_contrato_row,
                        has_rows=PlazasListadoState.tiene_contratos,
                        empty_component=empty_state_card(
                            title="Sin contratos",
                            description="No hay contratos con plazas configuradas.",
                            icon="file-text",
                        ),
                        table_size="1",
                    ),
                    border=f"1px solid {Colors.BORDER}",
                    border_radius=Radius.LG,
                    overflow="hidden",
                    width="100%",
                ),
                spacing="4",
                width="100%",
            ),
        ),
        width="100%",
        max_width="1120px",
        margin_x="auto",
        min_height="100vh",
        on_mount=PlazasListadoState.cargar_contratos,
    )
