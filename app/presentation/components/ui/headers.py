"""Componentes genéricos de headers para páginas"""
import reflex as rx


def page_header(icono: str, titulo: str, subtitulo: str = "") -> rx.Component:
    """
    Header genérico para páginas con icono, título y subtítulo

    Args:
        icono: Nombre del icono (ej: "building-2", "users", "calendar")
        titulo: Título principal de la página
        subtitulo: Subtítulo descriptivo (opcional)

    Returns:
        Componente de header con layout consistente
    """
    return rx.hstack(
        rx.icon(icono, size=32, color="var(--blue-9)"),
        rx.vstack(
            rx.text(titulo, size="6", weight="bold"),
            rx.text(subtitulo, size="3", color="var(--gray-9)"),
            align="start",
            spacing="1"
        ),
        spacing="3",
        align="center"
    )
