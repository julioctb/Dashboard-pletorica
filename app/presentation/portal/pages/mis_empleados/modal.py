"""
Modal para crear/editar empleados en el portal.
"""
import reflex as rx

from .state import MisEmpleadosState


def modal_empleado() -> rx.Component:
    """Modal para crear o editar un empleado."""
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title(
                rx.cond(
                    MisEmpleadosState.es_edicion,
                    "Editar Empleado",
                    "Nuevo Empleado",
                ),
            ),
            rx.dialog.description(
                rx.cond(
                    MisEmpleadosState.es_edicion,
                    rx.text("Modifique los datos del empleado. El CURP no se puede cambiar."),
                    rx.text(
                        "El empleado se asignara a ",
                        rx.text(
                            MisEmpleadosState.nombre_empresa_actual,
                            weight="bold",
                            as_="span",
                        ),
                    ),
                ),
            ),

            rx.vstack(
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
                padding_y="4",
            ),

            # Botones de accion
            rx.hstack(
                rx.dialog.close(
                    rx.button(
                        "Cancelar",
                        variant="soft",
                        color_scheme="gray",
                        on_click=MisEmpleadosState.cerrar_modal_empleado,
                    ),
                ),
                rx.button(
                    rx.cond(
                        MisEmpleadosState.saving,
                        rx.spinner(size="1"),
                        rx.icon("save", size=16),
                    ),
                    "Guardar",
                    on_click=MisEmpleadosState.guardar_empleado,
                    disabled=MisEmpleadosState.saving,
                    color_scheme="teal",
                ),
                spacing="3",
                justify="end",
                width="100%",
            ),

            max_width="600px",
        ),
        open=MisEmpleadosState.mostrar_modal_empleado,
        on_open_change=lambda open: rx.cond(~open, MisEmpleadosState.cerrar_modal_empleado(), None),
    )


# =============================================================================
# CAMPOS DEL FORMULARIO
# =============================================================================

def _campo_curp() -> rx.Component:
    """Campo CURP."""
    return rx.vstack(
        rx.text("CURP *", size="2", weight="medium"),
        rx.input(
            value=MisEmpleadosState.form_curp,
            on_change=MisEmpleadosState.set_form_curp,
            on_blur=MisEmpleadosState.validar_curp_blur,
            placeholder="18 caracteres",
            max_length=18,
            width="100%",
            disabled=MisEmpleadosState.es_edicion,
        ),
        rx.cond(
            MisEmpleadosState.error_curp != "",
            rx.text(MisEmpleadosState.error_curp, size="1", color="red"),
        ),
        width="100%",
        spacing="1",
    )


def _campos_nombre() -> rx.Component:
    """Campos de nombre y apellidos."""
    return rx.hstack(
        rx.vstack(
            rx.text("Nombre *", size="2", weight="medium"),
            rx.input(
                value=MisEmpleadosState.form_nombre,
                on_change=MisEmpleadosState.set_form_nombre,
                on_blur=MisEmpleadosState.validar_nombre_blur,
                placeholder="Nombre(s)",
                width="100%",
            ),
            rx.cond(
                MisEmpleadosState.error_nombre != "",
                rx.text(MisEmpleadosState.error_nombre, size="1", color="red"),
            ),
            width="100%",
            spacing="1",
        ),
        rx.vstack(
            rx.text("Ap. Paterno *", size="2", weight="medium"),
            rx.input(
                value=MisEmpleadosState.form_apellido_paterno,
                on_change=MisEmpleadosState.set_form_apellido_paterno,
                on_blur=MisEmpleadosState.validar_apellido_paterno_blur,
                placeholder="Apellido paterno",
                width="100%",
            ),
            rx.cond(
                MisEmpleadosState.error_apellido_paterno != "",
                rx.text(MisEmpleadosState.error_apellido_paterno, size="1", color="red"),
            ),
            width="100%",
            spacing="1",
        ),
        rx.vstack(
            rx.text("Ap. Materno *", size="2", weight="medium"),
            rx.input(
                value=MisEmpleadosState.form_apellido_materno,
                on_change=MisEmpleadosState.set_form_apellido_materno,
                on_blur=MisEmpleadosState.validar_apellido_materno_blur,
                placeholder="Apellido materno",
                width="100%",
            ),
            rx.cond(
                MisEmpleadosState.error_apellido_materno != "",
                rx.text(MisEmpleadosState.error_apellido_materno, size="1", color="red"),
            ),
            width="100%",
            spacing="1",
        ),
        spacing="3",
        width="100%",
    )


def _campos_rfc_nss() -> rx.Component:
    """Campos RFC y NSS."""
    return rx.hstack(
        rx.vstack(
            rx.text("RFC *", size="2", weight="medium"),
            rx.input(
                value=MisEmpleadosState.form_rfc,
                on_change=MisEmpleadosState.set_form_rfc,
                on_blur=MisEmpleadosState.validar_rfc_blur,
                placeholder="13 caracteres",
                max_length=13,
                width="100%",
            ),
            rx.cond(
                MisEmpleadosState.error_rfc != "",
                rx.text(MisEmpleadosState.error_rfc, size="1", color="red"),
            ),
            width="100%",
            spacing="1",
        ),
        rx.vstack(
            rx.text("NSS *", size="2", weight="medium"),
            rx.input(
                value=MisEmpleadosState.form_nss,
                on_change=MisEmpleadosState.set_form_nss,
                on_blur=MisEmpleadosState.validar_nss_blur,
                placeholder="11 digitos",
                max_length=11,
                width="100%",
            ),
            rx.cond(
                MisEmpleadosState.error_nss != "",
                rx.text(MisEmpleadosState.error_nss, size="1", color="red"),
            ),
            width="100%",
            spacing="1",
        ),
        spacing="3",
        width="100%",
    )


def _campos_fecha_genero() -> rx.Component:
    """Campos fecha de nacimiento y genero."""
    return rx.hstack(
        rx.vstack(
            rx.text("Fecha de Nacimiento *", size="2", weight="medium"),
            rx.input(
                type="date",
                value=MisEmpleadosState.form_fecha_nacimiento,
                on_change=MisEmpleadosState.set_form_fecha_nacimiento,
                on_blur=MisEmpleadosState.validar_fecha_nacimiento_blur,
                width="100%",
            ),
            rx.cond(
                MisEmpleadosState.error_fecha_nacimiento != "",
                rx.text(MisEmpleadosState.error_fecha_nacimiento, size="1", color="red"),
            ),
            width="100%",
            spacing="1",
        ),
        rx.vstack(
            rx.text("Genero *", size="2", weight="medium"),
            rx.select.root(
                rx.select.trigger(
                    placeholder="Seleccionar...",
                    width="100%",
                ),
                rx.select.content(
                    rx.foreach(
                        MisEmpleadosState.opciones_genero,
                        lambda opt: rx.select.item(opt["label"], value=opt["value"]),
                    ),
                ),
                value=MisEmpleadosState.form_genero,
                on_change=MisEmpleadosState.set_form_genero,
            ),
            rx.cond(
                MisEmpleadosState.error_genero != "",
                rx.text(MisEmpleadosState.error_genero, size="1", color="red"),
            ),
            width="100%",
            spacing="1",
        ),
        spacing="3",
        width="100%",
    )


def _campos_telefono_email() -> rx.Component:
    """Campos telefono y email."""
    return rx.hstack(
        rx.vstack(
            rx.text("Telefono *", size="2", weight="medium"),
            rx.input(
                value=MisEmpleadosState.form_telefono,
                on_change=MisEmpleadosState.set_form_telefono,
                on_blur=MisEmpleadosState.validar_telefono_blur,
                placeholder="10 digitos",
                max_length=15,
                width="100%",
            ),
            rx.cond(
                MisEmpleadosState.error_telefono != "",
                rx.text(MisEmpleadosState.error_telefono, size="1", color="red"),
            ),
            width="100%",
            spacing="1",
        ),
        rx.vstack(
            rx.text("Email", size="2", weight="medium"),
            rx.input(
                value=MisEmpleadosState.form_email,
                on_change=MisEmpleadosState.set_form_email,
                on_blur=MisEmpleadosState.validar_email_blur,
                placeholder="correo@ejemplo.com",
                width="100%",
            ),
            rx.cond(
                MisEmpleadosState.error_email != "",
                rx.text(MisEmpleadosState.error_email, size="1", color="red"),
            ),
            width="100%",
            spacing="1",
        ),
        spacing="3",
        width="100%",
    )


def _campo_direccion() -> rx.Component:
    """Campo direccion."""
    return rx.vstack(
        rx.text("Direccion", size="2", weight="medium"),
        rx.text_area(
            value=MisEmpleadosState.form_direccion,
            on_change=MisEmpleadosState.set_form_direccion,
            placeholder="Direccion completa",
            width="100%",
            rows="2",
        ),
        width="100%",
        spacing="1",
    )


def _seccion_contacto_emergencia() -> rx.Component:
    """Seccion de contacto de emergencia (3 campos)."""
    return rx.vstack(
        rx.text("Contacto de Emergencia", size="2", weight="bold"),
        rx.hstack(
            rx.vstack(
                rx.text("Nombre", size="2", weight="medium"),
                rx.input(
                    value=MisEmpleadosState.form_contacto_nombre,
                    on_change=MisEmpleadosState.set_form_contacto_nombre,
                    on_blur=MisEmpleadosState.validar_contacto_nombre_blur,
                    placeholder="Nombre completo",
                    width="100%",
                ),
                rx.cond(
                    MisEmpleadosState.error_contacto_nombre != "",
                    rx.text(MisEmpleadosState.error_contacto_nombre, size="1", color="red"),
                ),
                width="100%",
                spacing="1",
            ),
            rx.vstack(
                rx.text("Telefono", size="2", weight="medium"),
                rx.input(
                    value=MisEmpleadosState.form_contacto_telefono,
                    on_change=MisEmpleadosState.set_form_contacto_telefono,
                    on_blur=MisEmpleadosState.validar_contacto_telefono_blur,
                    placeholder="10 digitos",
                    max_length=15,
                    width="100%",
                ),
                rx.cond(
                    MisEmpleadosState.error_contacto_telefono != "",
                    rx.text(MisEmpleadosState.error_contacto_telefono, size="1", color="red"),
                ),
                width="100%",
                spacing="1",
            ),
            rx.vstack(
                rx.text("Parentesco", size="2", weight="medium"),
                rx.select.root(
                    rx.select.trigger(
                        placeholder="Seleccionar...",
                        width="100%",
                    ),
                    rx.select.content(
                        rx.foreach(
                            MisEmpleadosState.opciones_parentesco,
                            lambda opt: rx.select.item(opt["label"], value=opt["value"]),
                        ),
                    ),
                    value=MisEmpleadosState.form_contacto_parentesco,
                    on_change=MisEmpleadosState.set_form_contacto_parentesco,
                ),
                rx.cond(
                    MisEmpleadosState.error_contacto_parentesco != "",
                    rx.text(MisEmpleadosState.error_contacto_parentesco, size="1", color="red"),
                ),
                width="100%",
                spacing="1",
            ),
            spacing="3",
            width="100%",
        ),
        width="100%",
        spacing="2",
        padding="3",
        border="1px solid var(--gray-5)",
        border_radius="var(--radius-2)",
    )


def _campo_notas() -> rx.Component:
    """Campo notas."""
    return rx.vstack(
        rx.text("Notas", size="2", weight="medium"),
        rx.text_area(
            value=MisEmpleadosState.form_notas,
            on_change=MisEmpleadosState.set_form_notas,
            placeholder="Observaciones adicionales",
            width="100%",
            rows="2",
        ),
        width="100%",
        spacing="1",
    )
