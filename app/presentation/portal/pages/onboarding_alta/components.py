"""
Componentes UI para la pagina Alta de Empleados (Onboarding) del portal.

Tabla, filtros y badges de estatus onboarding.
"""
import reflex as rx

from app.presentation.components.ui import (
    badge_onboarding,
    table_text_sm,
)
from app.presentation.components.reusable.onboarding_list import (
    onboarding_filters,
    onboarding_table,
)
from app.presentation.theme import Colors, Typography

from .state import OnboardingAltaState


def fila_onboarding(emp: dict) -> rx.Component:
    """Fila de la tabla de empleados en onboarding."""
    return rx.table.row(
        rx.table.cell(
            table_text_sm(
                emp["clave"],
                weight=Typography.WEIGHT_MEDIUM,
                color=Colors.PORTAL_PRIMARY_TEXT,
            ),
        ),
        rx.table.cell(
            table_text_sm(
                emp["nombre_completo"],
                weight=Typography.WEIGHT_MEDIUM,
            ),
        ),
        rx.table.cell(
            table_text_sm(emp["curp"], tone="secondary"),
        ),
        rx.table.cell(
            table_text_sm(emp.get("email", "-"), tone="secondary"),
        ),
        rx.table.cell(
            badge_onboarding(emp.get("estatus_onboarding", "")),
        ),
    )


ENCABEZADOS_ONBOARDING = [
    {"nombre": "Clave", "ancho": "120px"},
    {"nombre": "Nombre", "ancho": "auto"},
    {"nombre": "CURP", "ancho": "200px"},
    {"nombre": "Email", "ancho": "180px"},
    {"nombre": "Estatus", "ancho": "150px"},
]


def tabla_onboarding() -> rx.Component:
    """Tabla de empleados en onboarding."""
    return onboarding_table(
        loading=OnboardingAltaState.loading,
        headers=ENCABEZADOS_ONBOARDING,
        rows=OnboardingAltaState.empleados_onboarding_filtrados,
        row_renderer=fila_onboarding,
        total=OnboardingAltaState.total_onboarding,
        total_condition=OnboardingAltaState.total_onboarding > 0,
        empty_title="No hay empleados en proceso de onboarding",
        empty_description="Registre un nuevo empleado para iniciar su proceso de alta",
        empty_icon="user-plus",
        loading_rows=5,
        total_caption="Mostrando "
        + OnboardingAltaState.total_onboarding.to(str)
        + " empleado(s) en onboarding",
    )


def filtros_onboarding() -> rx.Component:
    """Filtros de la tabla de onboarding."""
    return onboarding_filters(
        opciones=OnboardingAltaState.opciones_estatus_onboarding,
        value=OnboardingAltaState.filtro_estatus_onboarding,
        on_change=OnboardingAltaState.set_filtro_estatus_onboarding,
        on_reload=OnboardingAltaState.recargar_onboarding,
    )
