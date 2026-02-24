"""
Pagina Configuracion Operativa de empresa en el portal.

Permite configurar dias de pago (primera y segunda quincena)
y dias de bloqueo bancario antes de la fecha de pago.
"""
import reflex as rx

from app.presentation.layout import page_layout, page_header
from app.presentation.components.ui import boton_guardar
from app.presentation.theme import Colors, Typography, Spacing

from .state import ConfiguracionEmpresaState


# =============================================================================
# SECCIONES
# =============================================================================

def _seccion_dias_pago() -> rx.Component:
    """Seccion de configuracion de dias de pago."""
    return rx.vstack(
        rx.text(
            "Dias de Pago",
            font_size=Typography.SIZE_LG,
            font_weight=Typography.WEIGHT_BOLD,
            color=Colors.TEXT_PRIMARY,
        ),
        rx.text(
            "Configure los dias del mes en que se realizan los pagos de nomina.",
            font_size=Typography.SIZE_SM,
            color=Colors.TEXT_SECONDARY,
        ),
        rx.separator(),
        # Primera quincena
        rx.vstack(
            rx.text(
                "Dia de pago — Primera quincena",
                font_size=Typography.SIZE_SM,
                font_weight=Typography.WEIGHT_MEDIUM,
            ),
            rx.input(
                type="number",
                min="1",
                max="28",
                value=ConfiguracionEmpresaState.form_dia_pago_1q.to(str),
                on_change=ConfiguracionEmpresaState.set_form_dia_pago_1q,
                width="120px",
            ),
            rx.text(
                "Dia del mes (1-28) en que se paga la primera quincena.",
                font_size=Typography.SIZE_XS,
                color=Colors.TEXT_MUTED,
            ),
            spacing="1",
        ),
        # Segunda quincena
        rx.vstack(
            rx.text(
                "Dia de pago — Segunda quincena",
                font_size=Typography.SIZE_SM,
                font_weight=Typography.WEIGHT_MEDIUM,
            ),
            rx.input(
                type="number",
                min="0",
                max="28",
                value=ConfiguracionEmpresaState.form_dia_pago_2q.to(str),
                on_change=ConfiguracionEmpresaState.set_form_dia_pago_2q,
                width="120px",
            ),
            rx.text(
                "Dia del mes (1-28) para la segunda quincena. Ingrese 0 para ultimo dia del mes.",
                font_size=Typography.SIZE_XS,
                color=Colors.TEXT_MUTED,
            ),
            spacing="1",
        ),
        width="100%",
        spacing="3",
        padding=Spacing.LG,
        background=Colors.SURFACE,
        border=f"1px solid {Colors.BORDER}",
        border_radius="8px",
    )


def _seccion_bloqueo_bancario() -> rx.Component:
    """Seccion de configuracion de bloqueo bancario."""
    return rx.vstack(
        rx.text(
            "Bloqueo Bancario",
            font_size=Typography.SIZE_LG,
            font_weight=Typography.WEIGHT_BOLD,
            color=Colors.TEXT_PRIMARY,
        ),
        rx.text(
            "Configure cuantos dias antes del pago se bloquean los cambios a datos bancarios.",
            font_size=Typography.SIZE_SM,
            color=Colors.TEXT_SECONDARY,
        ),
        rx.separator(),
        rx.vstack(
            rx.text(
                "Dias de bloqueo antes del pago",
                font_size=Typography.SIZE_SM,
                font_weight=Typography.WEIGHT_MEDIUM,
            ),
            rx.input(
                type="number",
                min="1",
                max="10",
                value=ConfiguracionEmpresaState.form_dias_bloqueo.to(str),
                on_change=ConfiguracionEmpresaState.set_form_dias_bloqueo,
                width="120px",
            ),
            rx.text(
                "Numero de dias (1-10) antes de la fecha de pago en que se impide "
                "a los empleados modificar su cuenta bancaria.",
                font_size=Typography.SIZE_XS,
                color=Colors.TEXT_MUTED,
            ),
            spacing="1",
        ),
        rx.callout.root(
            rx.callout.icon(rx.icon("info", size=16)),
            rx.callout.text(
                "Este bloqueo previene cambios bancarios de ultimo momento que podrian "
                "causar rechazos en las transferencias de nomina.",
                font_size=Typography.SIZE_SM,
            ),
            color_scheme="blue",
            variant="soft",
            width="100%",
        ),
        width="100%",
        spacing="3",
        padding=Spacing.LG,
        background=Colors.SURFACE,
        border=f"1px solid {Colors.BORDER}",
        border_radius="8px",
    )


# =============================================================================
# PAGINA
# =============================================================================

def configuracion_empresa_page() -> rx.Component:
    """Pagina de configuracion operativa de la empresa."""
    return rx.box(
        page_layout(
            header=page_header(
                titulo="Configuracion Operativa",
                subtitulo="Parametros de pago y bloqueo bancario",
                icono="settings",
            ),
            toolbar=rx.fragment(),
            content=rx.cond(
                ConfiguracionEmpresaState.loading,
                rx.center(rx.spinner(size="3"), padding_y="60px"),
                rx.vstack(
                    _seccion_dias_pago(),
                    _seccion_bloqueo_bancario(),
                    # Boton guardar
                    rx.hstack(
                        rx.spacer(),
                        boton_guardar(
                            on_click=ConfiguracionEmpresaState.guardar_configuracion,
                            saving=ConfiguracionEmpresaState.saving,
                            disabled=~ConfiguracionEmpresaState.tiene_cambios,
                            texto="Guardar cambios",
                        ),
                        width="100%",
                    ),
                    width="100%",
                    spacing="4",
                    max_width="700px",
                ),
            ),
        ),
        width="100%",
        min_height="100vh",
        on_mount=ConfiguracionEmpresaState.on_mount_configuracion_empresa,
    )
