import reflex as rx

def estatus_badge(estatus: str) -> rx.Component:
    """Badge de estatus con color"""
    return rx.badge(
        estatus,
        color_scheme=rx.cond(
            estatus == "ACTIVO",
            "green",
            "red"
        ),
        size="1",
    )