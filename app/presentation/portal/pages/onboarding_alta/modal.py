"""
Modal para alta de empleados en onboarding.
"""
import reflex as rx

from app.presentation.theme import Colors, Typography, Spacing
from app.presentation.components.ui import boton_guardar, boton_cancelar

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
    return rx.vstack(
        rx.text(
            "CURP *",
            font_size=Typography.SIZE_SM,
            font_weight=Typography.WEIGHT_MEDIUM,
        ),
        rx.input(
            value=OnboardingAltaState.form_curp,
            on_change=OnboardingAltaState.set_form_curp,
            on_blur=[
                OnboardingAltaState.validar_curp_blur,
                OnboardingAltaState.validar_curp_realtime,
            ],
            placeholder="18 caracteres (ej: ABCD123456HDFXXX00)",
            max_length=18,
            width="100%",
        ),
        # Indicador de validacion
        rx.cond(
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
        ),
        # Error de validacion local
        rx.cond(
            (OnboardingAltaState.error_curp != "") & (~OnboardingAltaState.curp_validado),
            rx.text(
                OnboardingAltaState.error_curp,
                font_size=Typography.SIZE_XS,
                color=Colors.ERROR,
            ),
        ),
        width="100%",
        spacing="1",
    )


def _campos_nombre() -> rx.Component:
    """Campos de nombre y apellidos."""
    return rx.vstack(
        rx.hstack(
            rx.vstack(
                rx.text(
                    "Nombre *",
                    font_size=Typography.SIZE_SM,
                    font_weight=Typography.WEIGHT_MEDIUM,
                ),
                rx.input(
                    value=OnboardingAltaState.form_nombre,
                    on_change=OnboardingAltaState.set_form_nombre,
                    on_blur=OnboardingAltaState.validar_nombre_blur,
                    placeholder="Nombre(s)",
                    width="100%",
                ),
                rx.cond(
                    OnboardingAltaState.error_nombre != "",
                    rx.text(
                        OnboardingAltaState.error_nombre,
                        font_size=Typography.SIZE_XS,
                        color=Colors.ERROR,
                    ),
                ),
                width="100%",
                spacing="1",
            ),
            rx.vstack(
                rx.text(
                    "Ap. Paterno *",
                    font_size=Typography.SIZE_SM,
                    font_weight=Typography.WEIGHT_MEDIUM,
                ),
                rx.input(
                    value=OnboardingAltaState.form_apellido_paterno,
                    on_change=OnboardingAltaState.set_form_apellido_paterno,
                    on_blur=OnboardingAltaState.validar_apellido_paterno_blur,
                    placeholder="Apellido paterno",
                    width="100%",
                ),
                rx.cond(
                    OnboardingAltaState.error_apellido_paterno != "",
                    rx.text(
                        OnboardingAltaState.error_apellido_paterno,
                        font_size=Typography.SIZE_XS,
                        color=Colors.ERROR,
                    ),
                ),
                width="100%",
                spacing="1",
            ),
            spacing="3",
            width="100%",
        ),
        rx.vstack(
            rx.text(
                "Ap. Materno",
                font_size=Typography.SIZE_SM,
                font_weight=Typography.WEIGHT_MEDIUM,
            ),
            rx.input(
                value=OnboardingAltaState.form_apellido_materno,
                on_change=OnboardingAltaState.set_form_apellido_materno,
                placeholder="Apellido materno (opcional)",
                width="100%",
            ),
            width="50%",
            spacing="1",
        ),
        spacing="3",
        width="100%",
    )


def _campo_email() -> rx.Component:
    """Campo email."""
    return rx.vstack(
        rx.text(
            "Email",
            font_size=Typography.SIZE_SM,
            font_weight=Typography.WEIGHT_MEDIUM,
        ),
        rx.input(
            value=OnboardingAltaState.form_email,
            on_change=OnboardingAltaState.set_form_email,
            on_blur=OnboardingAltaState.validar_email_blur,
            placeholder="correo@ejemplo.com (opcional)",
            width="100%",
        ),
        rx.cond(
            OnboardingAltaState.error_email != "",
            rx.text(
                OnboardingAltaState.error_email,
                font_size=Typography.SIZE_XS,
                color=Colors.ERROR,
            ),
        ),
        width="100%",
        spacing="1",
    )
