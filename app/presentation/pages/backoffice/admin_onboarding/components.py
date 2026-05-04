"""
Componentes UI para la pagina Admin Onboarding.

Pipeline cards, tabla de empleados y badges.
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
from app.presentation.theme import Colors, Radius, Spacing, Typography

from .state import AdminOnboardingState


# =============================================================================
# PIPELINE CARDS
# =============================================================================

def _pipeline_card(
    label: str,
    count_var,
    color_scheme: str,
    icon: str,
    estatus_key: str,
) -> rx.Component:
    """Card individual del pipeline, clickeable para filtrar."""
    is_active = AdminOnboardingState.filtro_estatus_onboarding == estatus_key

    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.icon(icon, size=20, color=f"var(--{color_scheme}-9)"),
                rx.spacer(),
                rx.text(
                    count_var,
                    font_size=Typography.SIZE_2XL,
                    font_weight=Typography.WEIGHT_BOLD,
                    color=f"var(--{color_scheme}-9)",
                ),
                width="100%",
                align="center",
            ),
            rx.text(
                label,
                font_size=Typography.SIZE_SM,
                color=Colors.TEXT_SECONDARY,
                font_weight=Typography.WEIGHT_MEDIUM,
            ),
            spacing="2",
            width="100%",
        ),
        padding=Spacing.MD,
        border_radius=Radius.LG,
        border=rx.cond(
            is_active,
            f"2px solid var(--{color_scheme}-9)",
            f"1px solid {Colors.BORDER}",
        ),
        background=rx.cond(
            is_active,
            f"var(--{color_scheme}-2)",
            Colors.SURFACE,
        ),
        cursor="pointer",
        on_click=lambda: AdminOnboardingState.filtrar_por_estatus(estatus_key),
        flex="1",
        min_width="140px",
        style={
            "_hover": {"background": f"var(--{color_scheme}-2)"},
        },
    )


def pipeline_cards() -> rx.Component:
    """Fila de pipeline cards con conteos por estatus."""
    return rx.hstack(
        _pipeline_card(
            "Datos Pendientes",
            AdminOnboardingState.conteo_datos_pendientes,
            "yellow", "user-pen", "DATOS_PENDIENTES",
        ),
        _pipeline_card(
            "Docs Pendientes",
            AdminOnboardingState.conteo_docs_pendientes,
            "orange", "file-up", "DOCUMENTOS_PENDIENTES",
        ),
        _pipeline_card(
            "En Revision",
            AdminOnboardingState.conteo_en_revision,
            "blue", "scan-search", "EN_REVISION",
        ),
        _pipeline_card(
            "Aprobado",
            AdminOnboardingState.conteo_aprobado,
            "green", "circle-check", "APROBADO",
        ),
        _pipeline_card(
            "Rechazado",
            AdminOnboardingState.conteo_rechazado,
            "red", "circle-x", "RECHAZADO",
        ),
        width="100%",
        gap=Spacing.MD,
        flex_wrap="wrap",
    )


# =============================================================================
# FILTROS
# =============================================================================

def filtros_onboarding_admin() -> rx.Component:
    """Filtros para la tabla de onboarding admin."""
    return onboarding_filters(
        opciones=AdminOnboardingState.opciones_estatus_pipeline,
        value=AdminOnboardingState.filtro_estatus_onboarding,
        on_change=AdminOnboardingState.set_filtro_estatus_onboarding,
        on_reload=AdminOnboardingState.recargar_pipeline,
        placeholder="Filtrar por estatus...",
        total_text=AdminOnboardingState.total_filtrados.to(str) + " empleados",
    )


# =============================================================================
# TABLA
# =============================================================================

ENCABEZADOS_ONBOARDING = [
    {"nombre": "Clave", "ancho": "100px"},
    {"nombre": "Nombre", "ancho": "200px"},
    {"nombre": "Empresa", "ancho": "180px"},
    {"nombre": "CURP", "ancho": "180px"},
    {"nombre": "Estatus", "ancho": "150px"},
    {"nombre": "Email", "ancho": "180px"},
]


def fila_onboarding_admin(emp: dict) -> rx.Component:
    """Fila de la tabla de onboarding admin."""
    return rx.table.row(
        rx.table.cell(
            table_text_sm(
                emp["clave"],
                weight=Typography.WEIGHT_MEDIUM,
            ),
        ),
        rx.table.cell(
            table_text_sm(emp["nombre_completo"]),
        ),
        rx.table.cell(
            table_text_sm(emp["nombre_empresa"], tone="secondary"),
        ),
        rx.table.cell(
            table_text_sm(emp["curp"], tone="muted"),
        ),
        rx.table.cell(
            badge_onboarding(emp.get("estatus_onboarding", "")),
        ),
        rx.table.cell(
            table_text_sm(emp.get("email", ""), tone="secondary"),
        ),
        _hover={"background": Colors.SURFACE_HOVER},
    )


def tabla_onboarding_admin() -> rx.Component:
    """Tabla de empleados en onboarding (admin global)."""
    return onboarding_table(
        loading=AdminOnboardingState.loading,
        headers=ENCABEZADOS_ONBOARDING,
        rows=AdminOnboardingState.empleados_filtrados,
        row_renderer=fila_onboarding_admin,
        total=AdminOnboardingState.total_filtrados,
        total_condition=AdminOnboardingState.total_filtrados > 0,
        empty_title="No hay empleados en onboarding",
        empty_description="No hay registros para el filtro seleccionado.",
        empty_icon="users",
        loading_rows=6,
        header_variant="admin",
    )
