"""Badges de dominio reutilizables (empleados/documentos)."""

import reflex as rx


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
