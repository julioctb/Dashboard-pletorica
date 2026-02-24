"""
Modal para crear/editar empleados en el portal.
"""
import reflex as rx

from app.presentation.theme import Colors, Typography, Spacing
from app.presentation.components.reusable import (
    employee_form_modal,
    employee_address_field,
    employee_birth_gender_row,
    employee_curp_field,
    employee_emergency_contact_section,
    employee_name_fields_section,
    employee_notes_field,
    employee_phone_email_row,
    employee_rfc_nss_row,
)

from .state import MisEmpleadosState


def modal_empleado() -> rx.Component:
    """Modal para crear o editar un empleado."""
    return employee_form_modal(
        open_state=MisEmpleadosState.mostrar_modal_empleado,
        title=rx.cond(
            MisEmpleadosState.es_edicion,
            "Editar Empleado",
            "Nuevo Empleado",
        ),
        description=rx.cond(
            MisEmpleadosState.es_edicion,
            rx.text("Modifique los datos del empleado. El CURP no se puede cambiar."),
            rx.text(
                "El empleado se asignara a ",
                rx.text(
                    MisEmpleadosState.nombre_empresa_actual,
                    font_weight=Typography.WEIGHT_BOLD,
                    as_="span",
                ),
            ),
        ),
        body=rx.vstack(
                # CURP (obligatorio en creacion, inmutable en edicion)
                _campo_curp(),

                # Nombre y apellidos
                _campos_nombre(),

                # RFC y NSS (obligatorios)
                _campos_rfc_nss(),

                # Fecha nacimiento y genero (obligatorios)
                _campos_fecha_genero(),

                # Telefono (obligatorio) y email (opcional)
                _campos_telefono_email(),

                # Direccion
                _campo_direccion(),

                # Contacto de emergencia (3 campos)
                _seccion_contacto_emergencia(),

                # Notas
                _campo_notas(),

                spacing="4",
                width="100%",
                padding_y=Spacing.BASE,
            ),
        on_cancel=MisEmpleadosState.cerrar_modal_empleado,
        on_save=MisEmpleadosState.guardar_empleado,
        save_text=rx.cond(
            MisEmpleadosState.es_edicion,
            "Guardar Cambios",
            "Crear Empleado",
        ),
        saving=MisEmpleadosState.saving,
        save_loading_text="Guardando...",
        save_color_scheme="teal",
        max_width="600px",
    )


# =============================================================================
# CAMPOS DEL FORMULARIO
# =============================================================================

def _campo_curp() -> rx.Component:
    """Campo CURP."""
    return employee_curp_field(
        value=MisEmpleadosState.form_curp,
        on_change=MisEmpleadosState.set_form_curp,
        on_blur=MisEmpleadosState.validar_curp_blur,
        error=MisEmpleadosState.error_curp,
        disabled=MisEmpleadosState.es_edicion,
        placeholder="18 caracteres",
    )


def _campos_nombre() -> rx.Component:
    """Campos de nombre y apellidos."""
    return employee_name_fields_section(
        nombre_value=MisEmpleadosState.form_nombre,
        nombre_on_change=MisEmpleadosState.set_form_nombre,
        nombre_on_blur=MisEmpleadosState.validar_nombre_blur,
        nombre_error=MisEmpleadosState.error_nombre,
        apellido_paterno_value=MisEmpleadosState.form_apellido_paterno,
        apellido_paterno_on_change=MisEmpleadosState.set_form_apellido_paterno,
        apellido_paterno_on_blur=MisEmpleadosState.validar_apellido_paterno_blur,
        apellido_paterno_error=MisEmpleadosState.error_apellido_paterno,
        apellido_materno_value=MisEmpleadosState.form_apellido_materno,
        apellido_materno_on_change=MisEmpleadosState.set_form_apellido_materno,
        apellido_materno_on_blur=MisEmpleadosState.validar_apellido_materno_blur,
        apellido_materno_error=MisEmpleadosState.error_apellido_materno,
        materno_requerido=True,
        materno_mostrar_error=True,
    )


def _campos_rfc_nss() -> rx.Component:
    """Campos RFC y NSS."""
    return employee_rfc_nss_row(
        rfc_value=MisEmpleadosState.form_rfc,
        rfc_on_change=MisEmpleadosState.set_form_rfc,
        rfc_on_blur=MisEmpleadosState.validar_rfc_blur,
        rfc_error=MisEmpleadosState.error_rfc,
        nss_value=MisEmpleadosState.form_nss,
        nss_on_change=MisEmpleadosState.set_form_nss,
        nss_on_blur=MisEmpleadosState.validar_nss_blur,
        nss_error=MisEmpleadosState.error_nss,
        rfc_required=True,
        nss_required=True,
        rfc_placeholder="13 caracteres",
        nss_placeholder="11 digitos",
    )


def _campos_fecha_genero() -> rx.Component:
    """Campos fecha de nacimiento y genero."""
    return employee_birth_gender_row(
        fecha_value=MisEmpleadosState.form_fecha_nacimiento,
        fecha_on_change=MisEmpleadosState.set_form_fecha_nacimiento,
        fecha_on_blur=MisEmpleadosState.validar_fecha_nacimiento_blur,
        fecha_error=MisEmpleadosState.error_fecha_nacimiento,
        genero_value=MisEmpleadosState.form_genero,
        genero_on_change=MisEmpleadosState.set_form_genero,
        genero_error=MisEmpleadosState.error_genero,
        opciones_genero=MisEmpleadosState.opciones_genero,
        fecha_required=True,
        genero_required=True,
        genero_label="Genero",
    )


def _campos_telefono_email() -> rx.Component:
    """Campos telefono y email."""
    return employee_phone_email_row(
        telefono_value=MisEmpleadosState.form_telefono,
        telefono_on_change=MisEmpleadosState.set_form_telefono,
        telefono_on_blur=MisEmpleadosState.validar_telefono_blur,
        telefono_error=MisEmpleadosState.error_telefono,
        email_value=MisEmpleadosState.form_email,
        email_on_change=MisEmpleadosState.set_form_email,
        email_on_blur=MisEmpleadosState.validar_email_blur,
        email_error=MisEmpleadosState.error_email,
        email_placeholder="correo@ejemplo.com",
    )


def _campo_direccion() -> rx.Component:
    """Campo direccion."""
    return employee_address_field(
        value=MisEmpleadosState.form_direccion,
        on_change=MisEmpleadosState.set_form_direccion,
        placeholder="Direccion completa",
        label="Direccion",
    )


def _seccion_contacto_emergencia() -> rx.Component:
    """Seccion de contacto de emergencia (3 campos)."""
    return employee_emergency_contact_section(
        mode="detailed",
        nombre_value=MisEmpleadosState.form_contacto_nombre,
        nombre_on_change=MisEmpleadosState.set_form_contacto_nombre,
        nombre_on_blur=MisEmpleadosState.validar_contacto_nombre_blur,
        nombre_error=MisEmpleadosState.error_contacto_nombre,
        telefono_value=MisEmpleadosState.form_contacto_telefono,
        telefono_on_change=MisEmpleadosState.set_form_contacto_telefono,
        telefono_on_blur=MisEmpleadosState.validar_contacto_telefono_blur,
        telefono_error=MisEmpleadosState.error_contacto_telefono,
        parentesco_value=MisEmpleadosState.form_contacto_parentesco,
        parentesco_on_change=MisEmpleadosState.set_form_contacto_parentesco,
        parentesco_error=MisEmpleadosState.error_contacto_parentesco,
        opciones_parentesco=MisEmpleadosState.opciones_parentesco,
        bordered=True,
    )


def _campo_notas() -> rx.Component:
    """Campo notas."""
    return employee_notes_field(
        value=MisEmpleadosState.form_notas,
        on_change=MisEmpleadosState.set_form_notas,
        placeholder="Observaciones adicionales",
    )
