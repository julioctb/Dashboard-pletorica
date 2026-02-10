"""Badge de estado para requisiciones."""
import reflex as rx


def estado_requisicion_badge(estado: str, show_icon: bool = False) -> rx.Component:
    """
    Badge reactivo para estados de requisición.

    Colores:
        BORRADOR -> gray
        ENVIADA -> blue
        EN REVISION -> orange
        APROBADA -> green
        ADJUDICADA -> purple
        CONTRATADA -> teal
        CANCELADA -> red
    """
    return rx.match(
        estado,
        ("BORRADOR", rx.badge(
            rx.hstack(
                rx.icon("file-pen", size=12) if show_icon else rx.fragment(),
                "Borrador",
                spacing="1",
            ) if show_icon else "Borrador",
            color_scheme="gray",
            variant="soft",
        )),
        ("ENVIADA", rx.badge(
            rx.hstack(
                rx.icon("send", size=12) if show_icon else rx.fragment(),
                "Enviada",
                spacing="1",
            ) if show_icon else "Enviada",
            color_scheme="blue",
            variant="soft",
        )),
        ("EN REVISION", rx.badge(
            rx.hstack(
                rx.icon("search", size=12) if show_icon else rx.fragment(),
                "En revision",
                spacing="1",
            ) if show_icon else "En revision",
            color_scheme="orange",
            variant="soft",
        )),
        ("APROBADA", rx.badge(
            rx.hstack(
                rx.icon("circle-check", size=12) if show_icon else rx.fragment(),
                "Aprobada",
                spacing="1",
            ) if show_icon else "Aprobada",
            color_scheme="green",
            variant="soft",
        )),
        ("ADJUDICADA", rx.badge(
            rx.hstack(
                rx.icon("award", size=12) if show_icon else rx.fragment(),
                "Adjudicada",
                spacing="1",
            ) if show_icon else "Adjudicada",
            color_scheme="purple",
            variant="soft",
        )),
        ("CONTRATADA", rx.badge(
            rx.hstack(
                rx.icon("file-check", size=12) if show_icon else rx.fragment(),
                "Contratada",
                spacing="1",
            ) if show_icon else "Contratada",
            color_scheme="teal",
            variant="soft",
        )),
        ("CANCELADA", rx.badge(
            rx.hstack(
                rx.icon("circle-x", size=12) if show_icon else rx.fragment(),
                "Cancelada",
                spacing="1",
            ) if show_icon else "Cancelada",
            color_scheme="red",
            variant="soft",
        )),
        rx.badge(estado, color_scheme="gray", variant="soft"),
    )
