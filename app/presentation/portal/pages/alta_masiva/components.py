"""
Componentes compartidos del wizard de alta masiva.
"""
import reflex as rx

from app.presentation.theme import Colors, Spacing, Typography

from .state import AltaMasivaState


def indicador_pasos() -> rx.Component:
    """Indicador visual de los 3 pasos del wizard."""

    def _paso(numero: int, titulo: str) -> rx.Component:
        es_activo = AltaMasivaState.paso_actual >= numero
        es_actual = AltaMasivaState.paso_actual == numero

        return rx.hstack(
            rx.center(
                rx.text(
                    str(numero),
                    font_size=Typography.SIZE_SM,
                    font_weight=Typography.WEIGHT_BOLD,
                ),
                width="32px",
                height="32px",
                border_radius="50%",
                background=rx.cond(es_activo, Colors.PORTAL_PRIMARY, Colors.SECONDARY_LIGHT),
                color=rx.cond(es_activo, Colors.TEXT_INVERSE, Colors.TEXT_SECONDARY),
                flex_shrink="0",
            ),
            rx.text(
                titulo,
                font_size=Typography.SIZE_SM,
                font_weight=rx.cond(es_actual, Typography.WEIGHT_BOLD, Typography.WEIGHT_MEDIUM),
                color=rx.cond(es_activo, Colors.TEXT_PRIMARY, Colors.TEXT_MUTED),
                display=rx.breakpoints(initial="none", sm="block"),
            ),
            spacing="2",
            align="center",
        )

    def _conector() -> rx.Component:
        return rx.box(
            height="2px",
            flex="1",
            max_width="80px",
            background=Colors.BORDER,
        )

    return rx.hstack(
        _paso(1, "Subir archivo"),
        _conector(),
        _paso(2, "Validacion"),
        _conector(),
        _paso(3, "Resultados"),
        width="100%",
        max_width="500px",
        justify="center",
        align="center",
        padding_y=Spacing.MD,
        margin_x="auto",
    )


def card_resumen(
    titulo: str,
    valor: rx.Var,
    color_scheme: str,
    icono: str,
) -> rx.Component:
    """
    Card de resumen con contador.

    Note: color_scheme usa variables Radix dinamicas (var(--{color}-N))
    para permitir multiples colores por card (green, yellow, red, blue).
    """
    color_map = {
        "green": ("var(--green-3)", "var(--green-9)", "var(--green-11)"),
        "yellow": ("var(--yellow-3)", "var(--yellow-9)", "var(--yellow-11)"),
        "red": ("var(--red-3)", "var(--red-9)", "var(--red-11)"),
        "blue": ("var(--blue-3)", "var(--blue-9)", "var(--blue-11)"),
    }
    bg, icon_color, text_color = color_map.get(color_scheme, color_map["blue"])

    return rx.box(
        rx.hstack(
            rx.center(
                rx.icon(icono, size=20, color=icon_color),
                width="40px",
                height="40px",
                border_radius="10px",
                background=bg,
                flex_shrink="0",
            ),
            rx.vstack(
                rx.text(
                    titulo,
                    font_size=Typography.SIZE_XS,
                    font_weight=Typography.WEIGHT_MEDIUM,
                    color=Colors.TEXT_MUTED,
                ),
                rx.text(
                    valor,
                    font_size=Typography.SIZE_XL,
                    font_weight=Typography.WEIGHT_BOLD,
                    color=text_color,
                ),
                spacing="0",
            ),
            spacing="3",
            align="center",
        ),
        padding=Spacing.MD,
        background=Colors.SURFACE,
        border=f"1px solid {Colors.BORDER}",
        border_radius="8px",
        flex="1",
        min_width="140px",
    )


def badge_resultado(resultado: str) -> rx.Component:
    """Badge coloreado segun resultado de validacion."""
    return rx.match(
        resultado,
        ("VALIDO", rx.badge("Valido", color_scheme="green", variant="soft", size="1")),
        ("REINGRESO", rx.badge("Reingreso", color_scheme="yellow", variant="soft", size="1")),
        ("ERROR", rx.badge("Error", color_scheme="red", variant="soft", size="1")),
        rx.badge(resultado, size="1"),
    )
