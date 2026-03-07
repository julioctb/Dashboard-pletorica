"""Badge de estado para requisiciones."""
import reflex as rx


def estado_requisicion_badge(
    estado: str,
    show_icon: bool = False,
    size: str = "1",
) -> rx.Component:
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
    def _badge(label: str, color_scheme: str, icon_name: str) -> rx.Component:
        return rx.badge(
            rx.hstack(
                rx.icon(icon_name, size=12),
                label,
                spacing="1",
            ) if show_icon else label,
            color_scheme=color_scheme,
            variant="soft",
            size=size,
        )

    return rx.match(
        estado,
        ("BORRADOR", _badge("Borrador", "gray", "file-pen")),
        ("ENVIADA", _badge("Enviada", "blue", "send")),
        ("EN REVISION", _badge("En revision", "orange", "search")),
        ("APROBADA", _badge("Aprobada", "green", "circle-check")),
        ("ADJUDICADA", _badge("Adjudicada", "purple", "award")),
        ("CONTRATADA", _badge("Contratada", "teal", "file-check")),
        ("CANCELADA", _badge("Cancelada", "red", "circle-x")),
        rx.badge(estado, color_scheme="gray", variant="soft", size=size),
    )
