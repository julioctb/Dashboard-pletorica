"""
Componentes UI para la pagina Admin Onboarding.

Pipeline cards, tabla de empleados y badges.
"""
import reflex as rx

from app.presentation.components.ui import skeleton_tabla
from app.presentation.theme import Colors, Typography, Spacing

from .state import AdminOnboardingState


# =============================================================================
# BADGES
# =============================================================================

def badge_onboarding(estatus: str) -> rx.Component:
    """Badge de estatus de onboarding (replica del de expedientes)."""
    return rx.match(
        estatus,
        ("REGISTRADO", rx.badge("Registrado", color_scheme="gray", variant="soft", size="1")),
        ("DATOS_PENDIENTES", rx.badge("Datos Pendientes", color_scheme="yellow", variant="soft", size="1")),
        ("DOCUMENTOS_PENDIENTES", rx.badge("Docs Pendientes", color_scheme="orange", variant="soft", size="1")),
        ("EN_REVISION", rx.badge("En Revision", color_scheme="blue", variant="soft", size="1")),
        ("APROBADO", rx.badge("Aprobado", color_scheme="green", variant="soft", size="1")),
        ("RECHAZADO", rx.badge("Rechazado", color_scheme="red", variant="soft", size="1")),
        ("ACTIVO_COMPLETO", rx.badge("Completo", color_scheme="teal", variant="soft", size="1")),
        rx.badge(estatus, size="1"),
    )


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
                    font_size="24px",
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
        border_radius="8px",
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
            "green", "check-circle", "APROBADO",
        ),
        _pipeline_card(
            "Rechazado",
            AdminOnboardingState.conteo_rechazado,
            "red", "x-circle", "RECHAZADO",
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
    return rx.hstack(
        rx.select.root(
            rx.select.trigger(placeholder="Filtrar por estatus..."),
            rx.select.content(
                rx.foreach(
                    AdminOnboardingState.opciones_estatus_pipeline,
                    lambda opt: rx.select.item(opt["label"], value=opt["value"]),
                ),
            ),
            value=AdminOnboardingState.filtro_estatus_onboarding,
            on_change=AdminOnboardingState.set_filtro_estatus_onboarding,
            size="2",
        ),
        rx.icon_button(
            rx.icon("refresh-cw", size=16),
            size="2",
            variant="outline",
            color_scheme="gray",
            on_click=AdminOnboardingState.recargar_pipeline,
        ),
        rx.spacer(),
        rx.text(
            AdminOnboardingState.total_filtrados.to(str) + " empleados",
            font_size=Typography.SIZE_SM,
            color=Colors.TEXT_SECONDARY,
        ),
        align="center",
        width="100%",
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
            rx.text(
                emp["clave"],
                font_size=Typography.SIZE_SM,
                font_weight=Typography.WEIGHT_MEDIUM,
                color=Colors.TEXT_PRIMARY,
            ),
        ),
        rx.table.cell(
            rx.text(
                emp["nombre_completo"],
                font_size=Typography.SIZE_SM,
            ),
        ),
        rx.table.cell(
            rx.text(
                emp["nombre_empresa"],
                font_size=Typography.SIZE_SM,
                color=Colors.TEXT_SECONDARY,
            ),
        ),
        rx.table.cell(
            rx.text(
                emp["curp"],
                font_size=Typography.SIZE_SM,
                color=Colors.TEXT_MUTED,
            ),
        ),
        rx.table.cell(
            badge_onboarding(emp.get("estatus_onboarding", "")),
        ),
        rx.table.cell(
            rx.text(
                emp.get("email", ""),
                font_size=Typography.SIZE_SM,
                color=Colors.TEXT_SECONDARY,
            ),
        ),
        _hover={"background": Colors.SURFACE_HOVER},
    )


def tabla_onboarding_admin() -> rx.Component:
    """Tabla de empleados en onboarding (admin global)."""
    return rx.cond(
        AdminOnboardingState.loading,
        skeleton_tabla(filas=6, columnas=6),
        rx.cond(
            AdminOnboardingState.total_filtrados > 0,
            rx.table.root(
                rx.table.header(
                    rx.table.row(
                        *[
                            rx.table.column_header_cell(
                                rx.text(
                                    h["nombre"],
                                    font_size=Typography.SIZE_XS,
                                    font_weight=Typography.WEIGHT_SEMIBOLD,
                                    color=Colors.TEXT_MUTED,
                                    text_transform="uppercase",
                                ),
                                width=h["ancho"],
                            )
                            for h in ENCABEZADOS_ONBOARDING
                        ],
                    ),
                ),
                rx.table.body(
                    rx.foreach(
                        AdminOnboardingState.empleados_filtrados,
                        fila_onboarding_admin,
                    ),
                ),
                width="100%",
                variant="surface",
            ),
            # Sin resultados
            rx.center(
                rx.vstack(
                    rx.icon("users", size=40, color=Colors.TEXT_MUTED),
                    rx.text(
                        "No hay empleados en onboarding",
                        font_size=Typography.SIZE_SM,
                        color=Colors.TEXT_MUTED,
                    ),
                    align="center",
                    spacing="2",
                ),
                padding_y="60px",
            ),
        ),
    )
