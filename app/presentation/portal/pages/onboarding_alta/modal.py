"""
Modal para alta de empleados en onboarding.
"""
import reflex as rx

from app.presentation.theme import Colors, Typography, Spacing
from app.presentation.components.ui import boton_guardar, boton_cancelar
from app.presentation.components.reusable import (
    employee_curp_field,
    employee_email_field,
    employee_name_fields_section,
)

from .state import OnboardingAltaState


def modal_alta_empleado() -> rx.Component:
    """Modal para registrar un nuevo empleado en onboarding."""
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title("Registrar Empleado"),
            rx.dialog.description(
                rx.text(
                    "El empleado se asignara a ",
                    rx.text(
                        OnboardingAltaState.nombre_empresa_actual,
                        font_weight=Typography.WEIGHT_BOLD,
                        as_="span",
                    ),
                ),
            ),

            rx.vstack(
                # CURP con validacion realtime
                _campo_curp(),

                # Nombre y apellidos
                _campos_nombre(),

                # Email
                _campo_email(),

                spacing="4",
                width="100%",
                padding_y=Spacing.BASE,
            ),

            # Botones de accion
            rx.hstack(
                boton_cancelar(
                    on_click=OnboardingAltaState.cerrar_modal_alta,
                ),
                boton_guardar(
                    texto="Registrar Empleado",
                    texto_guardando="Registrando...",
                    on_click=OnboardingAltaState.registrar_empleado,
                    saving=OnboardingAltaState.saving,
                    color_scheme="teal",
                ),
                spacing="3",
                justify="end",
                width="100%",
            ),

            max_width="550px",
        ),
        open=OnboardingAltaState.mostrar_modal_alta,
        on_open_change=rx.noop,
    )


# =============================================================================
# CAMPOS DEL FORMULARIO
# =============================================================================

def _campo_curp() -> rx.Component:
    """Campo CURP con indicador de validacion realtime."""
    return employee_curp_field(
        value=OnboardingAltaState.form_curp,
        on_change=OnboardingAltaState.set_form_curp,
        on_blur=[
            OnboardingAltaState.validar_curp_blur,
            OnboardingAltaState.validar_curp_realtime,
        ],
        error=OnboardingAltaState.error_curp,
        placeholder="18 caracteres (ej: ABCD123456HDFXXX00)",
        validation_indicator=rx.cond(
            OnboardingAltaState.curp_validado,
            rx.hstack(
                rx.cond(
                    OnboardingAltaState.curp_es_valido,
                    rx.hstack(
                        rx.icon("circle-check", size=14, color=Colors.SUCCESS),
                        rx.text(
                            OnboardingAltaState.curp_mensaje,
                            font_size=Typography.SIZE_XS,
                            color=Colors.SUCCESS,
                        ),
                        spacing="1",
                        align="center",
                    ),
                    rx.hstack(
                        rx.icon("circle-x", size=14, color=Colors.ERROR),
                        rx.text(
                            OnboardingAltaState.curp_mensaje,
                            font_size=Typography.SIZE_XS,
                            color=Colors.ERROR,
                        ),
                        spacing="1",
                        align="center",
                    ),
                ),
            ),
            rx.fragment(),
        ),
        local_error_condition=(OnboardingAltaState.error_curp != "") & (~OnboardingAltaState.curp_validado),
    )


def _campos_nombre() -> rx.Component:
    """Campos de nombre y apellidos."""
    return employee_name_fields_section(
        nombre_value=OnboardingAltaState.form_nombre,
        nombre_on_change=OnboardingAltaState.set_form_nombre,
        nombre_on_blur=OnboardingAltaState.validar_nombre_blur,
        nombre_error=OnboardingAltaState.error_nombre,
        apellido_paterno_value=OnboardingAltaState.form_apellido_paterno,
        apellido_paterno_on_change=OnboardingAltaState.set_form_apellido_paterno,
        apellido_paterno_on_blur=OnboardingAltaState.validar_apellido_paterno_blur,
        apellido_paterno_error=OnboardingAltaState.error_apellido_paterno,
        apellido_materno_value=OnboardingAltaState.form_apellido_materno,
        apellido_materno_on_change=OnboardingAltaState.set_form_apellido_materno,
        materno_requerido=False,
        materno_placeholder="Apellido materno (opcional)",
        materno_inline=False,
    )


def _campo_email() -> rx.Component:
    """Campo email."""
    return employee_email_field(
        value=OnboardingAltaState.form_email,
        on_change=OnboardingAltaState.set_form_email,
        on_blur=OnboardingAltaState.validar_email_blur,
        error=OnboardingAltaState.error_email,
        placeholder="correo@ejemplo.com (opcional)",
    )
