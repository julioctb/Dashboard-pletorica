"""
Badges reutilizables para el sistema.

Uso:
    from app.presentation.components.ui import (
        estatus_badge,
        tipo_empresa_badge,
        tipo_movimiento_badge,
        modalidad_badge,
    )
"""
import reflex as rx


def estatus_badge(estatus: str) -> rx.Component:
    """Badge de estatus con color según el estado."""
    return rx.match(
        estatus,
        ("ACTIVO", rx.badge("Activo", color_scheme="green", size="1")),
        ("BORRADOR", rx.badge("Borrador", color_scheme="gray", size="1")),
        ("SUSPENDIDO", rx.badge("Suspendido", color_scheme="orange", size="1")),
        ("VENCIDO", rx.badge("Vencido", color_scheme="yellow", size="1")),
        ("CANCELADO", rx.badge("Cancelado", color_scheme="red", size="1")),
        ("CERRADO", rx.badge("Cerrado", color_scheme="blue", size="1")),
        ("INACTIVO", rx.badge("Inactivo", color_scheme="gray", size="1")),
        rx.badge(estatus, color_scheme="gray", size="1"),  # default
    )


def tipo_empresa_badge(tipo: str) -> rx.Component:
    """Badge para tipo de empresa."""
    return rx.match(
        tipo,
        ("NOMINA", rx.badge("NOMINA", color_scheme="blue", size="1")),
        ("MANTENIMIENTO", rx.badge("MANTENIMIENTO", color_scheme="green", size="1")),
        ("SUMINISTRO", rx.badge("SUMINISTRO", color_scheme="purple", size="1")),
        ("SERVICIOS", rx.badge("SERVICIOS", color_scheme="orange", size="1")),
        rx.badge(tipo, color_scheme="gray", size="1"),
    )


def tipo_movimiento_badge(tipo: str) -> rx.Component:
    """Badge para tipo de movimiento laboral."""
    return rx.match(
        tipo,
        ("ALTA", rx.badge("Alta", color_scheme="green", size="1")),
        ("BAJA", rx.badge("Baja", color_scheme="red", size="1")),
        ("MODIFICACION", rx.badge("Modificación", color_scheme="blue", size="1")),
        ("REINGRESO", rx.badge("Reingreso", color_scheme="yellow", size="1")),
        ("TRANSFERENCIA", rx.badge("Transferencia", color_scheme="purple", size="1")),
        rx.badge(tipo, color_scheme="gray", size="1"),
    )


def modalidad_badge(modalidad: str) -> rx.Component:
    """Badge para modalidad de contrato."""
    return rx.match(
        modalidad,
        ("PRESENCIAL", rx.badge("Presencial", color_scheme="blue", size="1")),
        ("REMOTO", rx.badge("Remoto", color_scheme="green", size="1")),
        ("HIBRIDO", rx.badge("Híbrido", color_scheme="purple", size="1")),
        rx.badge(modalidad, color_scheme="gray", size="1"),
    )


def prioridad_badge(prioridad: str) -> rx.Component:
    """Badge para prioridad."""
    return rx.match(
        prioridad,
        ("ALTA", rx.badge("Alta", color_scheme="red", size="1")),
        ("MEDIA", rx.badge("Media", color_scheme="yellow", size="1")),
        ("BAJA", rx.badge("Baja", color_scheme="green", size="1")),
        rx.badge(prioridad, color_scheme="gray", size="1"),
    )


def resultado_badge(resultado: str) -> rx.Component:
    """Badge para resultado de validación."""
    return rx.match(
        resultado,
        ("VALIDO", rx.badge("Válido", color_scheme="green", variant="soft", size="1")),
        ("REINGRESO", rx.badge("Reingreso", color_scheme="yellow", variant="soft", size="1")),
        ("ERROR", rx.badge("Error", color_scheme="red", variant="soft", size="1")),
        rx.badge(resultado, color_scheme="gray", size="1"),
    )