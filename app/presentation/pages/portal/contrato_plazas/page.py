"""Pagina portal de plazas por contrato."""

import reflex as rx

from app.presentation.components.ui import status_badge_reactive
from app.presentation.layouts.backoffice import page_header, page_layout
from app.presentation.theme import Colors

from .components import metricas_contrato_plazas, tabla_plazas_contrato_actual
from .modals import (
    modal_asignacion_plaza,
    modal_asignacion_sede_plaza,
    modal_categoria_plaza,
    modal_reasignacion_plaza,
    modal_salario_plaza,
)
from .state import ContratoPlazasState


def _header_plazas() -> rx.Component:
    return page_header(
        titulo="Plazas",
        icono="briefcase",
        titulo_compuesto=rx.hstack(
            rx.link(
                "Contratos",
                href="/portal/contratos",
                size="6",
                weight="bold",
                color=Colors.PORTAL_PRIMARY_TEXT,
                _hover={"text_decoration": "underline"},
            ),
            rx.text("›", color=Colors.TEXT_MUTED, size="5"),
            rx.text(
                "Plazas",
                size="6",
                weight="bold",
            ),
            rx.cond(
                ContratoPlazasState.estatus_contrato_actual != "",
                status_badge_reactive(ContratoPlazasState.estatus_contrato_actual),
                rx.fragment(),
            ),
            align="center",
            spacing="2",
            wrap="wrap",
        ),
        subtitulo_compuesto=rx.vstack(
            rx.text(
                ContratoPlazasState.codigo_contrato_actual,
                size="3",
                weight="medium",
                color=Colors.TEXT_PRIMARY,
            ),
            rx.hstack(
                rx.cond(
                    ContratoPlazasState.tipo_servicio_contrato_actual != "",
                    rx.text(
                        ContratoPlazasState.tipo_servicio_contrato_actual,
                        size="3",
                        color=Colors.TEXT_SECONDARY,
                    ),
                    rx.fragment(),
                ),
                rx.cond(
                    ContratoPlazasState.tipo_servicio_contrato_actual != "",
                    rx.text("·", color=Colors.TEXT_MUTED),
                    rx.fragment(),
                ),
                rx.text(
                    ContratoPlazasState.descripcion_contrato_actual,
                    size="3",
                    color=Colors.TEXT_SECONDARY,
                ),
                align="center",
                spacing="2",
                wrap="wrap",
            ),
            spacing="1",
            align="start",
        ),
        color_icono=Colors.PORTAL_ACCENT_SCHEME,
    )


def contrato_plazas_page() -> rx.Component:
    return rx.box(
        page_layout(
            header=_header_plazas(),
            content=rx.vstack(
                metricas_contrato_plazas(),
                tabla_plazas_contrato_actual(),
                modal_asignacion_plaza(),
                modal_categoria_plaza(),
                modal_salario_plaza(),
                modal_asignacion_sede_plaza(),
                modal_reasignacion_plaza(),
                width="100%",
                spacing="4",
            ),
        ),
        width="100%",
        min_height="100vh",
        on_mount=ContratoPlazasState.on_mount_contrato_plazas,
    )
