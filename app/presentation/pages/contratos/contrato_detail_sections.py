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
from app.presentation.theme import Colors, Typography


def contrato_detail_text(
    valor: Any,
    *,
    fallback: str = "No disponible",
    weight: str | None = None,
    color: str = Colors.TEXT_PRIMARY,
    white_space: str | None = None,
) -> rx.Component:
    """Texto consistente para campos del detalle de contrato."""
    text_props = {
        "font_size": Typography.SIZE_SM,
        "color": color,
    }
    if weight is not None:
        text_props["font_weight"] = weight
    if white_space is not None:
        text_props["white_space"] = white_space

    return rx.cond(
        valor,
        rx.text(valor, **text_props),
        rx.text(
            fallback,
            font_size=Typography.SIZE_SM,
            color=Colors.TEXT_MUTED,
            font_style="italic",
        ),
    )


def contrato_detail_field(label: str, contenido: rx.Component) -> rx.Component:
    """Campo de detalle en modo solo lectura."""
    return rx.vstack(
        rx.text(
            label,
            font_size=Typography.SIZE_XS,
            font_weight=Typography.WEIGHT_SEMIBOLD,
            color=Colors.TEXT_MUTED,
            text_transform="uppercase",
            letter_spacing=Typography.LETTER_SPACING_WIDE,
        ),
        contenido,
        spacing="1",
        width="100%",
        align="start",
    )


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
                rx.text("-", size="2", color=Colors.TEXT_MUTED),
            ),
        ),
        rx.table.cell(
            rx.text(
                categoria["categoria_nombre"],
                size="2",
                color=Colors.TEXT_PRIMARY,
            ),
        ),
        rx.table.cell(rx.text(categoria["cantidad_minima"], size="2", color=Colors.TEXT_PRIMARY)),
        rx.table.cell(rx.text(categoria["cantidad_maxima"], size="2", color=Colors.TEXT_PRIMARY)),
        rx.table.cell(
            rx.text(
                categoria["costo_unitario_fmt"],
                size="2",
                weight="medium",
                color=Colors.TEXT_PRIMARY,
            ),
        ),
        rx.table.cell(rx.text(categoria["costo_minimo_fmt"], size="2", color=Colors.TEXT_SECONDARY)),
        rx.table.cell(rx.text(categoria["costo_maximo_fmt"], size="2", color=Colors.TEXT_SECONDARY)),
    )


def contrato_detail_info_sections(
    datos: Any,
    categorias: Any,
    *,
    total_categorias: Any,
    tiene_categorias: Any,
) -> rx.Component:
    """Contenido compartido de detalle de contrato para backoffice y portal."""
    return rx.vstack(
        rx.card(
            rx.vstack(
                rx.hstack(
                    rx.vstack(
                        rx.text("Información general", weight="bold", size="4"),
                        rx.text(
                            "Resumen operativo y financiero del contrato.",
                            size="2",
                            color=Colors.TEXT_SECONDARY,
                        ),
                        spacing="1",
                        align="start",
                    ),
                    rx.spacer(),
                    rx.badge(
                        datos["codigo"],
                        color_scheme="blue",
                        size="2",
                        variant="soft",
                    ),
                    align="center",
                    width="100%",
                ),
                rx.grid(
                    contrato_detail_field(
                        "Empresa",
                        contrato_detail_text(
                            rx.cond(datos["nombre_empresa"], datos["nombre_empresa"], "Sin empresa"),
                            fallback="Sin empresa",
                        ),
                    ),
                    contrato_detail_field(
                        "Tipo de servicio",
                        contrato_detail_text(
                            rx.cond(datos["nombre_servicio"], datos["nombre_servicio"], "No aplica"),
                            fallback="No aplica",
                        ),
                    ),
                    contrato_detail_field(
                        "Tipo de contrato",
                        contrato_detail_text(datos["tipo_contrato"]),
                    ),
                    contrato_detail_field(
                        "Modalidad",
                        contrato_detail_text(datos["modalidad_adjudicacion"]),
                    ),
                    contrato_detail_field(
                        "Estatus",
                        status_badge_reactive(datos["estatus"], show_icon=True),
                    ),
                    contrato_detail_field(
                        "Folio institución",
                        contrato_detail_text(
                            rx.cond(datos["numero_folio_buap"], datos["numero_folio_buap"], "Sin folio"),
                            fallback="Sin folio",
                        ),
                    ),
                    columns=rx.breakpoints(initial="1", sm="2", lg="3"),
                    spacing="4",
                    width="100%",
                ),
                spacing="4",
                width="100%",
            ),
            width="100%",
            variant="surface",
        ),
        rx.card(
            rx.vstack(
                rx.text("Vigencia", weight="bold", size="4"),
                rx.grid(
                    contrato_detail_field(
                        "Inicio",
                        contrato_detail_text(datos["fecha_inicio_fmt"]),
                    ),
                    contrato_detail_field(
                        "Fin",
                        contrato_detail_text(
                            rx.cond(datos["fecha_fin"], datos["fecha_fin_fmt"], "Indefinido"),
                            fallback="Indefinido",
                        ),
                    ),
                    contrato_detail_field(
                        "Tipo de duración",
                        contrato_detail_text(
                            rx.cond(datos["tipo_duracion"], datos["tipo_duracion"], "No aplica"),
                            fallback="No aplica",
                        ),
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
                spacing="3",
                width="100%",
            ),
            width="100%",
            variant="surface",
        ),
        rx.card(
            rx.vstack(
                rx.text("Planeación de personal", weight="bold", size="4"),
                rx.grid(
                    metric_card(
                        titulo="Plazas mínimas",
                        valor=datos["cantidad_plazas_minima"],
                        icono="users",
                        color_scheme="blue",
                        descripcion="Compromiso mínimo del contrato",
                    ),
                    metric_card(
                        titulo="Plazas máximas",
                        valor=datos["cantidad_plazas_maxima"],
                        icono="briefcase",
                        color_scheme="green",
                        descripcion="Capacidad máxima materializable",
                    ),
                    metric_card(
                        titulo="Categorías",
                        valor=total_categorias,
                        icono="tags",
                        color_scheme="amber",
                        descripcion="Perfiles configurados en el contrato",
                    ),
                    columns=rx.breakpoints(initial="1", sm="2", lg="3"),
                    spacing="3",
                    width="100%",
                ),
                spacing="3",
                width="100%",
            ),
            width="100%",
            variant="surface",
        ),
        rx.card(
            rx.vstack(
                rx.hstack(
                    rx.text("Montos del contrato", weight="bold", size="4"),
                    rx.spacer(),
                    rx.badge(
                        rx.cond(
                            datos["incluye_iva"],
                            "Incluye IVA",
                            "Sin IVA",
                        ),
                        color_scheme=rx.cond(
                            datos["incluye_iva"],
                            "green",
                            "gray",
                        ),
                        variant="soft",
                    ),
                    align="center",
                    width="100%",
                ),
                rx.grid(
                    metric_card(
                        titulo="Monto mínimo",
                        valor=datos["monto_minimo_fmt"],
                        icono="banknote",
                        color_scheme="blue",
                        descripcion="Estimación mínima del contrato",
                    ),
                    metric_card(
                        titulo="Monto máximo",
                        valor=datos["monto_maximo_fmt"],
                        icono="wallet",
                        color_scheme="green",
                        descripcion="Tope autorizado del contrato",
                    ),
                    columns=rx.breakpoints(initial="1", sm="2"),
                    spacing="3",
                    width="100%",
                ),
                spacing="3",
                width="100%",
            ),
            width="100%",
            variant="surface",
        ),
        rx.card(
            rx.vstack(
                rx.hstack(
                    rx.text("Categorías configuradas", weight="bold", size="4"),
                    rx.spacer(),
                    rx.cond(
                        tiene_categorias,
                        rx.badge(
                            total_categorias,
                            color_scheme="blue",
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
                                rx.table.column_header_cell("Categoría"),
                                rx.table.column_header_cell("Mín.", width="70px"),
                                rx.table.column_header_cell("Máx.", width="70px"),
                                rx.table.column_header_cell("Costo", width="120px"),
                                rx.table.column_header_cell("Monto mín.", width="120px"),
                                rx.table.column_header_cell("Monto máx.", width="120px"),
                            ],
                            body_component=rx.foreach(categorias, _categoria_detalle_row),
                        ),
                        overflow_x="auto",
                        width="100%",
                    ),
                    empty_state_card(
                        title="Sin categorías configuradas",
                        description="Este contrato no tiene un desglose de plazas por categoría capturado.",
                        icon="tags",
                    ),
                ),
                spacing="3",
                width="100%",
            ),
            width="100%",
            variant="surface",
        ),
        rx.card(
            rx.vstack(
                rx.text("Objeto del contrato", weight="bold", size="4"),
                contrato_detail_text(
                    datos["descripcion_objeto"],
                    fallback="Sin objeto capturado",
                    white_space="pre-wrap",
                ),
                spacing="2",
                width="100%",
                align="start",
            ),
            width="100%",
            variant="surface",
        ),
        rx.cond(
            datos["notas"],
            rx.card(
                rx.vstack(
                    rx.text("Notas", weight="bold", size="4"),
                    rx.text(
                        datos["notas"],
                        size="2",
                        color=Colors.TEXT_PRIMARY,
                    ),
                    spacing="2",
                    width="100%",
                    align="start",
                ),
                width="100%",
                variant="surface",
            ),
            rx.fragment(),
        ),
        spacing="4",
        width="100%",
    )
