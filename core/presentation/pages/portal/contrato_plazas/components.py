"""Componentes de la pagina de plazas por contrato."""

import reflex as rx

from core.presentation.components.ui import metric_card
from core.presentation.pages.portal.plaza_shared_components import (
    resumen_contrato_plaza,
    tabla_plazas_contrato,
)
from core.presentation.theme import Colors, StatusColors

from .state import ContratoPlazasState


def metricas_contrato_plazas() -> rx.Component:
    return rx.grid(
        metric_card(
            titulo="Plazas",
            valor=ContratoPlazasState.total_plazas_contrato_actual,
            icono=None,
            color_scheme=Colors.NEUTRAL_SCHEME,
            show_icon=False,
            align="center",
            descripcion="Configuradas en el contrato",
        ),
        metric_card(
            titulo="Ocupadas",
            valor=ContratoPlazasState.plazas_ocupadas_contrato_actual,
            icono=None,
            color_scheme=StatusColors.OCUPADA_SCHEME,
            show_icon=False,
            align="center",
            value_color=Colors.SUCCESS,
        ),
        metric_card(
            titulo="Vacantes",
            valor=ContratoPlazasState.plazas_vacantes_contrato_actual,
            icono=None,
            color_scheme=StatusColors.VACANTE_SCHEME,
            show_icon=False,
            align="center",
            value_color=Colors.INFO,
        ),
        metric_card(
            titulo="Suspendidas",
            valor=ContratoPlazasState.plazas_suspendidas_contrato_actual,
            icono=None,
            color_scheme=StatusColors.SUSPENDIDA_SCHEME,
            show_icon=False,
            align="center",
            value_color=Colors.WARNING,
        ),
        columns=rx.breakpoints(initial="2", md="4"),
        spacing="3",
        width="100%",
    )


def resumen_contrato_plazas() -> rx.Component:
    return resumen_contrato_plaza(
        ContratoPlazasState,
        ContratoPlazasState.contrato_plaza_contexto,
    )


def tabla_plazas_contrato_actual() -> rx.Component:
    return tabla_plazas_contrato(ContratoPlazasState)
