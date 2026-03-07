"""Badges de dominio reutilizables (empleados/documentos)."""

import reflex as rx


def payroll_period_status_badge(estatus: rx.Var | str) -> rx.Component:
    """Badge reactivo para el workflow de periodos de nomina."""
    return rx.match(
        estatus,
        ("BORRADOR", rx.badge("Borrador", color_scheme="gray", size="1")),
        ("EN_PREPARACION_RRHH", rx.badge("Preparando", color_scheme="blue", size="1")),
        ("ENVIADO_A_CONTABILIDAD", rx.badge("Enviado", color_scheme="orange", size="1")),
        ("EN_PROCESO_CONTABILIDAD", rx.badge("En proceso", color_scheme="purple", size="1")),
        ("CALCULADO", rx.badge("Calculado", color_scheme="green", size="1")),
        ("CERRADO", rx.badge("Cerrado", color_scheme="gray", size="1", variant="surface")),
        rx.badge(estatus, color_scheme="gray", variant="soft", size="1"),
    )


def employee_status_badge(estatus: str, variant: str = "soft") -> rx.Component:
    """Badge de estatus de empleado con labels consistentes."""
    return rx.match(
        estatus,
        ("ACTIVO", rx.badge("Activo", color_scheme="green", variant=variant, size="1")),
        ("INACTIVO", rx.badge("Inactivo", color_scheme="red", variant=variant, size="1")),
        ("SUSPENDIDO", rx.badge("Suspendido", color_scheme="orange", variant=variant, size="1")),
        rx.badge(estatus, color_scheme="gray", variant=variant, size="1"),
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
