"""
Componentes UI para la pagina Alta de Empleados (Onboarding) del portal.

Tabla, filtros y badges de estatus onboarding.
"""
import reflex as rx

from app.presentation.components.ui import skeleton_tabla, badge_onboarding, select_estatus_onboarding
from app.presentation.theme import Colors, Typography, Spacing

from .state import OnboardingAltaState


def fila_onboarding(emp: dict) -> rx.Component:
    """Fila de la tabla de empleados en onboarding."""
    return rx.table.row(
        rx.table.cell(
            rx.text(
                emp["clave"],
                font_size=Typography.SIZE_SM,
                font_weight=Typography.WEIGHT_MEDIUM,
                color=Colors.PORTAL_PRIMARY_TEXT,
            ),
        ),
        rx.table.cell(
            rx.text(
                emp["nombre_completo"],
                font_size=Typography.SIZE_SM,
                font_weight=Typography.WEIGHT_MEDIUM,
            ),
        ),
        rx.table.cell(
            rx.text(
                emp["curp"],
                font_size=Typography.SIZE_SM,
                color=Colors.TEXT_SECONDARY,
            ),
        ),
        rx.table.cell(
            rx.text(
                emp.get("email", "-"),
                font_size=Typography.SIZE_SM,
                color=Colors.TEXT_SECONDARY,
            ),
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
    return rx.cond(
        OnboardingAltaState.loading,
        skeleton_tabla(columnas=ENCABEZADOS_ONBOARDING, filas=5),
        rx.cond(
            OnboardingAltaState.total_onboarding > 0,
            rx.vstack(
                rx.table.root(
                    rx.table.header(
                        rx.table.row(
                            rx.foreach(
                                ENCABEZADOS_ONBOARDING,
                                lambda col: rx.table.column_header_cell(
                                    col["nombre"],
                                    width=col["ancho"],
                                ),
                            ),
                        ),
                    ),
                    rx.table.body(
                        rx.foreach(
                            OnboardingAltaState.empleados_onboarding_filtrados,
                            fila_onboarding,
                        ),
                    ),
                    width="100%",
                    variant="surface",
                ),
                rx.text(
                    "Mostrando ",
                    OnboardingAltaState.total_onboarding,
                    " empleado(s) en onboarding",
                    font_size=Typography.SIZE_SM,
                    color=Colors.TEXT_SECONDARY,
                ),
                width="100%",
                spacing="3",
            ),
            rx.center(
                rx.vstack(
                    rx.icon("user-plus", size=48, color=Colors.TEXT_MUTED),
                    rx.text(
                        "No hay empleados en proceso de onboarding",
                        font_size=Typography.SIZE_LG,
                        color=Colors.TEXT_SECONDARY,
                    ),
                    rx.text(
                        "Registre un nuevo empleado para iniciar su proceso de alta",
                        font_size=Typography.SIZE_SM,
                        color=Colors.TEXT_MUTED,
                    ),
                    spacing="3",
                    align="center",
                ),
                padding=Spacing.MD,
                width="100%",
            ),
        ),
    )


def filtros_onboarding() -> rx.Component:
    """Filtros de la tabla de onboarding."""
    return select_estatus_onboarding(
        opciones=OnboardingAltaState.opciones_estatus_onboarding,
        value=OnboardingAltaState.filtro_estatus_onboarding,
        on_change=OnboardingAltaState.set_filtro_estatus_onboarding,
        on_reload=OnboardingAltaState.recargar_onboarding,
    )
