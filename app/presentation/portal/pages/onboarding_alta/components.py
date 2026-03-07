"""
Componentes UI para la pagina Alta de Empleados (Onboarding) del portal.

Tabla, filtros y badges de estatus onboarding.
"""
import reflex as rx

from app.presentation.components.ui import (
    badge_onboarding,
    tabla_action_button,
    table_cell_actions,
    table_cell_badge,
    table_cell_text_sm,
    table_pagination,
)
from app.presentation.components.reusable.onboarding_list import (
    onboarding_filters,
    onboarding_table,
)
from app.presentation.theme import Typography

from .state import OnboardingAltaState


def _boton_enviar_enlace(emp: dict) -> rx.Component:
    """Botón para enviar correo con enlace de registro al empleado.
    Solo visible si tiene email y estatus es DATOS_PENDIENTES.
    TODO: Implementar envío real de correo. Configurar plantilla
    del mensaje en /portal/configuracion-empresa.
    """
    return tabla_action_button(
        icon="send",
        tooltip="Enviar enlace de registro",
        on_click=OnboardingAltaState.enviar_enlace_registro(emp["id"]),
        color_scheme="teal",
        visible=(
            (emp.get("estatus_onboarding", "") == "DATOS_PENDIENTES")
            & (emp.get("email", "") != "")
        ),
    )


def fila_onboarding(emp: dict) -> rx.Component:
    """Fila de la tabla de empleados en onboarding."""
    return rx.table.row(
        table_cell_text_sm(
            emp["nombre_completo"],
            weight=Typography.WEIGHT_MEDIUM,
        ),
        table_cell_text_sm(
            emp.get("email", ""),
            tone="secondary",
            fallback="-",
        ),
        table_cell_badge(
            badge_onboarding(emp.get("estatus_onboarding", "")),
        ),
        table_cell_actions(
            _boton_enviar_enlace(emp),
        ),
    )


ENCABEZADOS_ONBOARDING = [
    {"nombre": "Nombre", "ancho": "280px"},
    {"nombre": "Email", "ancho": "260px"},
    {"nombre": "Estatus", "ancho": "150px"},
    {"nombre": "Acciones", "ancho": "96px"},
]


def tabla_onboarding() -> rx.Component:
    """Tabla de empleados en onboarding."""
    return onboarding_table(
        loading=OnboardingAltaState.loading,
        headers=ENCABEZADOS_ONBOARDING,
        rows=OnboardingAltaState.empleados_onboarding_paginados,
        row_renderer=fila_onboarding,
        total=OnboardingAltaState.total_onboarding_filtrados,
        total_condition=OnboardingAltaState.total_onboarding_filtrados > 0,
        empty_title="No hay empleados en proceso de onboarding",
        empty_description="Registre un nuevo empleado para iniciar su proceso de alta",
        empty_icon="user-plus",
        loading_rows=5,
        total_caption=OnboardingAltaState.resumen_paginacion_onboarding,
        footer_component=table_pagination(
            current_page=OnboardingAltaState.pagina_onboarding_actual,
            total_pages=OnboardingAltaState.total_paginas_onboarding,
            page_numbers=OnboardingAltaState.paginas_visibles_onboarding,
            on_page_change=OnboardingAltaState.ir_a_pagina,
            on_previous=OnboardingAltaState.pagina_anterior,
            on_next=OnboardingAltaState.pagina_siguiente,
            color_scheme="teal",
        ),
    )


def filtros_onboarding() -> rx.Component:
    """Filtros de la tabla de onboarding."""
    return onboarding_filters(
        opciones=OnboardingAltaState.opciones_estatus_onboarding,
        value=OnboardingAltaState.filtro_estatus_onboarding,
        on_change=OnboardingAltaState.set_filtro_estatus_onboarding,
        on_reload=OnboardingAltaState.recargar_onboarding,
        total_text=OnboardingAltaState.total_onboarding_filtrados.to(str) + " empleados",
    )
