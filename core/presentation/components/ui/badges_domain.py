"""Badges de dominio reutilizables (empleados/documentos)."""

import reflex as rx

from core.presentation.theme import Colors, StatusColors


def payroll_period_status_badge(estatus: rx.Var | str) -> rx.Component:
    """Badge reactivo para el workflow de periodos de nomina."""
    return rx.match(
        estatus,
        ("BORRADOR", rx.badge("Abierto", color_scheme=StatusColors.BORRADOR_SCHEME, size="1", variant="soft")),
        (
            "EN_PREPARACION_RRHH",
            rx.badge("En preparación", color_scheme="blue", size="1", variant="soft"),
        ),
        (
            "ENVIADO_A_CONTABILIDAD",
            rx.badge("Enviado", color_scheme=Colors.WARNING_SCHEME, size="1", variant="soft"),
        ),
        (
            "EN_PROCESO_CONTABILIDAD",
            rx.badge("En contabilidad", color_scheme="blue", size="1", variant="soft"),
        ),
        ("CALCULADO", rx.badge("Listo para pago", color_scheme="blue", size="1", variant="soft")),
        ("CERRADO", rx.badge("Cerrado", color_scheme=StatusColors.ACTIVO_SCHEME, size="1", variant="soft")),
        rx.badge(estatus, color_scheme=Colors.NEUTRAL_SCHEME, variant="soft", size="1"),
    )


def employee_status_badge(
    estatus: str,
    variant: str = "soft",
    size: str = "1",
) -> rx.Component:
    """Badge de estatus de empleado con labels consistentes."""
    return rx.match(
        estatus,
        ("ACTIVO", rx.badge("Activo", color_scheme=StatusColors.ACTIVO_SCHEME, variant=variant, size=size)),
        ("EN_ALTA", rx.badge("En alta", color_scheme=Colors.WARNING_SCHEME, variant=variant, size=size)),
        ("EN_BAJA", rx.badge("En baja", color_scheme=StatusColors.BAJA_SCHEME, variant=variant, size=size)),
        ("BAJA", rx.badge("Baja", color_scheme=StatusColors.BAJA_SCHEME, variant=variant, size=size)),
        ("INACTIVO", rx.badge("Inactivo", color_scheme=StatusColors.INACTIVO_SCHEME, variant=variant, size=size)),
        ("SUSPENDIDO", rx.badge("Suspendido", color_scheme=Colors.WARNING_SCHEME, variant=variant, size=size)),
        rx.badge(estatus, color_scheme=Colors.NEUTRAL_SCHEME, variant=variant, size=size),
    )


def document_status_badge(estatus: str, missing_label: str = "Sin subir") -> rx.Component:
    """Badge de estatus de documento para portal/admin."""
    return rx.match(
        estatus,
        ("PENDIENTE_REVISION", rx.badge("Pendiente", color_scheme=Colors.WARNING_SCHEME, variant="soft", size="1")),
        ("APROBADO", rx.badge("Aprobado", color_scheme=StatusColors.APROBADO_SCHEME, variant="soft", size="1")),
        ("RECHAZADO", rx.badge("Rechazado", color_scheme=StatusColors.RECHAZADO_SCHEME, variant="soft", size="1")),
        ("", rx.badge(missing_label, color_scheme=Colors.NEUTRAL_SCHEME, variant="outline", size="1")),
        rx.badge(
            missing_label if estatus is None else estatus,
            color_scheme=Colors.NEUTRAL_SCHEME,
            variant="soft",
            size="1",
        ),
    )
