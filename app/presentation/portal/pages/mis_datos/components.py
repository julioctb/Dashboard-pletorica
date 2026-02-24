"""
Componentes UI para la pagina Mis Datos del portal.

Formularios de datos personales/bancarios, progreso del expediente
y estados informativos (revision, aprobado).
"""
import reflex as rx

from app.presentation.components.ui import (
    form_input,
    boton_guardar,
)
from app.presentation.theme import Colors, Typography, Spacing

from .state import MisDatosState


# =============================================================================
# FORMULARIO DATOS PERSONALES
# =============================================================================

def formulario_datos_personales() -> rx.Component:
    """Formulario de datos personales del empleado."""
    return rx.vstack(
        rx.text(
            "Datos Personales",
            font_size=Typography.SIZE_LG,
            font_weight=Typography.WEIGHT_BOLD,
            color=Colors.TEXT_PRIMARY,
        ),
        rx.text(
            "Complete su informacion personal",
            font_size=Typography.SIZE_SM,
            color=Colors.TEXT_SECONDARY,
        ),
        rx.separator(),
        form_input(
            label="Telefono",
            placeholder="10 digitos",
            value=MisDatosState.form_telefono,
            on_change=MisDatosState.set_form_telefono,
            max_length=10,
        ),
        form_input(
            label="Direccion",
            placeholder="Calle, numero, colonia, ciudad, estado",
            value=MisDatosState.form_direccion,
            on_change=MisDatosState.set_form_direccion,
            max_length=300,
        ),
        form_input(
            label="Contacto de emergencia",
            placeholder="Nombre y telefono",
            value=MisDatosState.form_contacto_emergencia,
            on_change=MisDatosState.set_form_contacto_emergencia,
            max_length=200,
        ),
        form_input(
            label="Entidad de nacimiento",
            placeholder="Ej: Puebla",
            value=MisDatosState.form_entidad_nacimiento,
            on_change=MisDatosState.set_form_entidad_nacimiento,
            max_length=100,
        ),
        width="100%",
        spacing="3",
    )


# =============================================================================
# FORMULARIO DATOS BANCARIOS
# =============================================================================

def formulario_datos_bancarios() -> rx.Component:
    """Formulario de datos bancarios del empleado."""
    return rx.vstack(
        rx.text(
            "Datos Bancarios",
            font_size=Typography.SIZE_LG,
            font_weight=Typography.WEIGHT_BOLD,
            color=Colors.TEXT_PRIMARY,
        ),
        rx.text(
            "Informacion de su cuenta bancaria para deposito de nomina",
            font_size=Typography.SIZE_SM,
            color=Colors.TEXT_SECONDARY,
        ),
        rx.separator(),
        form_input(
            label="Numero de cuenta",
            placeholder="10-18 digitos",
            value=MisDatosState.form_cuenta_bancaria,
            on_change=MisDatosState.set_form_cuenta_bancaria,
            max_length=18,
        ),
        form_input(
            label="Banco",
            placeholder="Ej: BBVA, Santander, Banorte",
            value=MisDatosState.form_banco,
            on_change=MisDatosState.set_form_banco,
            max_length=100,
        ),
        form_input(
            label="CLABE interbancaria",
            placeholder="18 digitos",
            value=MisDatosState.form_clabe,
            on_change=MisDatosState.set_form_clabe,
            max_length=18,
        ),
        width="100%",
        spacing="3",
    )


# =============================================================================
# SECCION COMPLETA DE DATOS
# =============================================================================

def seccion_datos() -> rx.Component:
    """Combina formularios de datos personales y bancarios."""
    return rx.vstack(
        rx.hstack(
            rx.box(
                formulario_datos_personales(),
                flex="1",
                padding=Spacing.LG,
                background=Colors.SURFACE,
                border=f"1px solid {Colors.BORDER}",
                border_radius="8px",
            ),
            rx.box(
                formulario_datos_bancarios(),
                flex="1",
                padding=Spacing.LG,
                background=Colors.SURFACE,
                border=f"1px solid {Colors.BORDER}",
                border_radius="8px",
            ),
            width="100%",
            gap=Spacing.MD,
            flex_wrap="wrap",
        ),
        rx.hstack(
            rx.spacer(),
            boton_guardar(
                on_click=MisDatosState.guardar_datos_personales,
                saving=MisDatosState.saving,
                texto="Guardar y continuar",
            ),
            width="100%",
        ),
        width="100%",
        spacing="4",
    )


# =============================================================================
# PROGRESO EXPEDIENTE
# =============================================================================

def _metric_mini(label: str, value, color_scheme: str) -> rx.Component:
    """Mini metric card para el progreso."""
    return rx.vstack(
        rx.text(
            value,
            font_size="20px",
            font_weight=Typography.WEIGHT_BOLD,
            color=f"var(--{color_scheme}-9)",
        ),
        rx.text(
            label,
            font_size=Typography.SIZE_XS,
            color=Colors.TEXT_SECONDARY,
        ),
        align="center",
        padding=Spacing.SM,
        border=f"1px solid {Colors.BORDER}",
        border_radius="8px",
        background=Colors.SURFACE,
        flex="1",
        min_width="100px",
    )


def progreso_expediente() -> rx.Component:
    """Barra de progreso y conteos del expediente."""
    return rx.vstack(
        rx.text(
            "Progreso del expediente",
            font_size=Typography.SIZE_LG,
            font_weight=Typography.WEIGHT_BOLD,
            color=Colors.TEXT_PRIMARY,
        ),
        rx.progress(
            value=MisDatosState.porcentaje_expediente,
            width="100%",
            color_scheme="green",
        ),
        rx.hstack(
            _metric_mini("Requeridos", MisDatosState.docs_requeridos, "gray"),
            _metric_mini("Subidos", MisDatosState.docs_subidos, "blue"),
            _metric_mini("Aprobados", MisDatosState.docs_aprobados, "green"),
            _metric_mini("Rechazados", MisDatosState.docs_rechazados, "red"),
            width="100%",
            gap=Spacing.SM,
            flex_wrap="wrap",
        ),
        width="100%",
        spacing="3",
        padding=Spacing.LG,
        background=Colors.SURFACE,
        border=f"1px solid {Colors.BORDER}",
        border_radius="8px",
    )


# =============================================================================
# ESTADOS INFORMATIVOS
# =============================================================================

def estado_revision() -> rx.Component:
    """Card informativa cuando el expediente esta en revision."""
    return rx.center(
        rx.vstack(
            rx.icon("clock", size=48, color="var(--blue-9)"),
            rx.text(
                "Expediente en revision",
                font_size=Typography.SIZE_LG,
                font_weight=Typography.WEIGHT_BOLD,
                color=Colors.TEXT_PRIMARY,
            ),
            rx.text(
                "Su expediente esta siendo revisado por el area de Recursos Humanos. "
                "Le notificaremos cuando el proceso haya concluido.",
                font_size=Typography.SIZE_SM,
                color=Colors.TEXT_SECONDARY,
                text_align="center",
                max_width="400px",
            ),
            align="center",
            spacing="3",
            padding="60px",
        ),
    )


def estado_aprobado() -> rx.Component:
    """Card informativa cuando el expediente esta aprobado."""
    return rx.center(
        rx.vstack(
            rx.icon("check-circle", size=48, color="var(--green-9)"),
            rx.text(
                "Expediente aprobado",
                font_size=Typography.SIZE_LG,
                font_weight=Typography.WEIGHT_BOLD,
                color=Colors.TEXT_PRIMARY,
            ),
            rx.text(
                "Su expediente ha sido revisado y aprobado. "
                "Su proceso de onboarding ha concluido satisfactoriamente.",
                font_size=Typography.SIZE_SM,
                color=Colors.TEXT_SECONDARY,
                text_align="center",
                max_width="400px",
            ),
            align="center",
            spacing="3",
            padding="60px",
        ),
    )


def estado_no_encontrado() -> rx.Component:
    """Mensaje cuando no se encuentra empleado vinculado al usuario."""
    return rx.center(
        rx.vstack(
            rx.icon("user-x", size=48, color=Colors.TEXT_MUTED),
            rx.text(
                "No se encontro un empleado vinculado a su cuenta",
                font_size=Typography.SIZE_LG,
                font_weight=Typography.WEIGHT_BOLD,
                color=Colors.TEXT_PRIMARY,
            ),
            rx.text(
                "Contacte al area de Recursos Humanos para verificar su registro.",
                font_size=Typography.SIZE_SM,
                color=Colors.TEXT_SECONDARY,
                text_align="center",
                max_width="400px",
            ),
            align="center",
            spacing="3",
            padding="60px",
        ),
    )
