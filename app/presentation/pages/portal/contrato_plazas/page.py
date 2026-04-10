"""Página portal de plazas por contrato."""

import reflex as rx

from app.presentation.layouts.backoffice import page_layout

from .components import contenido_contrato_plazas, _header_plazas
from .modals import (
    modal_asignacion_plaza,
    modal_asignacion_sede_plaza,
    modal_categoria_contrato,
    modal_categoria_plaza,
    modal_reasignacion_plaza,
    modal_salario_plaza,
)
from .state import ContratoPlazasState


def contrato_plazas_page() -> rx.Component:
    return rx.box(
        page_layout(
            header=_header_plazas(),
            content=rx.vstack(
                contenido_contrato_plazas(),
                modal_categoria_contrato(),
                modal_asignacion_plaza(),
                modal_categoria_plaza(),
                modal_salario_plaza(),
                modal_asignacion_sede_plaza(),
                modal_reasignacion_plaza(),
                width="100%",
                spacing="4",
                max_width="900px",
                margin_x="auto",
            ),
        ),
        width="100%",
        min_height="100vh",
        on_mount=ContratoPlazasState.on_mount_contrato_plazas,
    )
