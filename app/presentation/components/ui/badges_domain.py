"""Badges de dominio reutilizables (empleados/documentos)."""

import reflex as rx


def payroll_period_status_badge(estatus: rx.Var | str) -> rx.Component:
    """Badge reactivo para el workflow de periodos de nomina."""
    return rx.match(
        estatus,
        ("BORRADOR", rx.badge("Abierto", color_scheme="gray", size="1", variant="soft")),
        (
            "EN_PREPARACION_RRHH",
            rx.badge("En preparación", color_scheme="blue", size="1", variant="soft"),
        ),
        (
            "ENVIADO_A_CONTABILIDAD",
            rx.badge("Enviado", color_scheme="amber", size="1", variant="soft"),
        ),
        (
            "EN_PROCESO_CONTABILIDAD",
            rx.badge("En contabilidad", color_scheme="blue", size="1", variant="soft"),
        ),
        ("CALCULADO", rx.badge("Listo para pago", color_scheme="blue", size="1", variant="soft")),
        ("CERRADO", rx.badge("Cerrado", color_scheme="green", size="1", variant="soft")),
        rx.badge(estatus, color_scheme="gray", variant="soft", size="1"),
    )


def employee_status_badge(
    estatus: str,
    variant: str = "soft",
    size: str = "1",
) -> rx.Component:
    """Badge de estatus de empleado con labels consistentes."""
    return rx.match(
        estatus,
        ("ACTIVO", rx.badge("Activo", color_scheme="green", variant=variant, size=size)),
        ("EN_ALTA", rx.badge("En alta", color_scheme="amber", variant=variant, size=size)),
        ("EN_BAJA", rx.badge("En baja", color_scheme="red", variant=variant, size=size)),
        ("INACTIVO", rx.badge("Inactivo", color_scheme="red", variant=variant, size=size)),
        ("SUSPENDIDO", rx.badge("Suspendido", color_scheme="orange", variant=variant, size=size)),
        rx.badge(estatus, color_scheme="gray", variant=variant, size=size),
    )


def document_status_badge(estatus: str, missing_label: str = "Sin subir") -> rx.Component:
    """Badge de estatus de documento para portal/admin."""
    return rx.match(
        estatus,
        ("PENDIENTE_REVISION", rx.badge("Pendiente", color_scheme="yellow", variant="soft", size="1")),
        ("APROBADO", rx.badge("Aprobado", color_scheme="green", variant="soft", size="1")),
        ("RECHAZADO", rx.badge("Rechazado", color_scheme="red", variant="soft", size="1")),
        ("", rx.badge(missing_label, color_scheme="gray", variant="outline", size="1")),
        rx.badge(missing_label if estatus is None else estatus, color_scheme="gray", variant="soft", size="1"),
    )
