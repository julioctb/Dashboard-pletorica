import reflex as rx


def estatus_badge(estatus: str) -> rx.Component:
    """Badge de estatus con color según el estado"""
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