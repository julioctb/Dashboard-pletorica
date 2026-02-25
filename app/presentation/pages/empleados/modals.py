"""
Modales para la pagina de Empleados.

Modal crear/editar, detalle, baja, restriccion, liberacion e historial.
"""
import reflex as rx

from app.presentation.pages.empleados.empleados_state import EmpleadosState
from app.presentation.theme import Colors
from app.presentation.components.reusable import (
    employee_form_body,
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
from app.presentation.components.ui import boton_cancelar, boton_guardar
from .components import estatus_badge, restriccion_badge


# =============================================================================
# MODAL CREAR/EDITAR EMPLEADO
# =============================================================================

def modal_empleado() -> rx.Component:
    """Modal para crear/editar empleado"""
    return employee_form_modal(
        open_state=EmpleadosState.mostrar_modal_empleado,
        title=EmpleadosState.titulo_modal,
        description="Complete los datos del empleado",
        body=employee_form_body(
                # Empresa
                rx.vstack(
                    rx.text("Empresa", size="2", weight="medium"),
                    rx.select.root(
                        rx.select.trigger(
                            placeholder="Seleccionar empresa...",
                            width="100%",
                        ),
                        rx.select.content(
                            rx.foreach(
                                EmpleadosState.opciones_empresas,
                                lambda opt: rx.select.item(opt["label"], value=opt["value"]),
                            ),
                        ),
                        value=EmpleadosState.form_empresa_id,
                        on_change=EmpleadosState.set_form_empresa_id,
                    ),
                    rx.cond(
                        EmpleadosState.error_empresa_id != "",
                        rx.text(EmpleadosState.error_empresa_id, size="1", color="red"),
                    ),
                    width="100%",
                    spacing="1",
                ),

                # CURP (obligatorio, solo en creación)
                rx.cond(
                    ~EmpleadosState.es_edicion,
                    employee_curp_field(
                        value=EmpleadosState.form_curp,
                        on_change=EmpleadosState.set_form_curp,
                        on_blur=EmpleadosState.validar_curp_blur,
                        error=EmpleadosState.error_curp,
                        placeholder="18 caracteres",
                    ),
                ),

                # Nombre y apellidos
                employee_name_fields_section(
                    nombre_value=EmpleadosState.form_nombre,
                    nombre_on_change=EmpleadosState.set_form_nombre,
                    nombre_on_blur=EmpleadosState.validar_nombre_blur,
                    nombre_error=EmpleadosState.error_nombre,
                    apellido_paterno_value=EmpleadosState.form_apellido_paterno,
                    apellido_paterno_on_change=EmpleadosState.set_form_apellido_paterno,
                    apellido_paterno_on_blur=EmpleadosState.validar_apellido_paterno_blur,
                    apellido_paterno_error=EmpleadosState.error_apellido_paterno,
                    apellido_materno_value=EmpleadosState.form_apellido_materno,
                    apellido_materno_on_change=EmpleadosState.set_form_apellido_materno,
                    materno_requerido=False,
                    materno_placeholder="Apellido materno (opcional)",
                ),

                # RFC y NSS
                employee_rfc_nss_row(
                    rfc_value=EmpleadosState.form_rfc,
                    rfc_on_change=EmpleadosState.set_form_rfc,
                    rfc_on_blur=EmpleadosState.validar_rfc_blur,
                    rfc_error=EmpleadosState.error_rfc,
                    nss_value=EmpleadosState.form_nss,
                    nss_on_change=EmpleadosState.set_form_nss,
                    nss_on_blur=EmpleadosState.validar_nss_blur,
                    nss_error=EmpleadosState.error_nss,
                    rfc_required=False,
                    nss_required=False,
                    rfc_placeholder="13 caracteres",
                    nss_placeholder="11 dígitos",
                ),

                # Fecha nacimiento y género
                employee_birth_gender_row(
                    fecha_value=EmpleadosState.form_fecha_nacimiento,
                    fecha_on_change=EmpleadosState.set_form_fecha_nacimiento,
                    genero_value=EmpleadosState.form_genero,
                    genero_on_change=EmpleadosState.set_form_genero,
                    opciones_genero=EmpleadosState.opciones_genero,
                    fecha_required=False,
                    genero_required=False,
                    genero_label="Género",
                ),

                # Teléfono y email
                employee_phone_email_row(
                    telefono_value=EmpleadosState.form_telefono,
                    telefono_on_change=EmpleadosState.set_form_telefono,
                    telefono_on_blur=EmpleadosState.validar_telefono_blur,
                    telefono_error=EmpleadosState.error_telefono,
                    email_value=EmpleadosState.form_email,
                    email_on_change=EmpleadosState.set_form_email,
                    email_on_blur=EmpleadosState.validar_email_blur,
                    email_error=EmpleadosState.error_email,
                    telefono_required=False,
                    telefono_placeholder="10 dígitos",
                    email_placeholder="correo@ejemplo.com",
                ),

                # Dirección
                employee_address_field(
                    value=EmpleadosState.form_direccion,
                    on_change=EmpleadosState.set_form_direccion,
                    placeholder="Dirección completa",
                    label="Dirección",
                ),

                # Contacto de emergencia
                employee_emergency_contact_section(
                    mode="simple",
                    simple_value=EmpleadosState.form_contacto_emergencia,
                    simple_on_change=EmpleadosState.set_form_contacto_emergencia,
                    simple_placeholder="Nombre y teléfono",
                    label_weight="medium",
                ),

                # Notas
                employee_notes_field(
                    value=EmpleadosState.form_notas,
                    on_change=EmpleadosState.set_form_notas,
                    placeholder="Observaciones adicionales",
                ),

                padding_y="4",
        ),
        on_cancel=EmpleadosState.cerrar_modal_empleado,
        on_save=EmpleadosState.guardar_empleado,
        save_text=rx.cond(
            EmpleadosState.es_edicion,
            "Guardar Cambios",
            "Crear Empleado",
        ),
        saving=EmpleadosState.saving,
        save_loading_text="Guardando...",
        max_width="600px",
    )


# =============================================================================
# MODAL DETALLE EMPLEADO
# =============================================================================

def modal_detalle_empleado() -> rx.Component:
    """Modal de detalle del empleado"""
    return rx.dialog.root(
        rx.dialog.content(
            rx.hstack(
                rx.dialog.title(
                    rx.hstack(
                        rx.icon("user", size=20),
                        EmpleadosState.nombre_completo_seleccionado,
                        spacing="2",
                        align="center",
                    ),
                ),
                rx.spacer(),
                rx.button(
                    rx.icon("x", size=16),
                    variant="ghost",
                    color_scheme="gray",
                    size="1",
                    on_click=EmpleadosState.cerrar_modal_detalle,
                    cursor="pointer",
                ),
                align="center",
                width="100%",
            ),

            rx.vstack(
                # Información principal
                rx.cond(
                    EmpleadosState.empleado_seleccionado,
                    rx.vstack(
                        # Clave, estatus y badge de restriccion
                        rx.hstack(
                            rx.badge(
                                EmpleadosState.empleado_seleccionado["clave"],
                                variant="outline",
                                size="2",
                            ),
                            estatus_badge(EmpleadosState.empleado_seleccionado["estatus"]),
                            restriccion_badge(EmpleadosState.empleado_esta_restringido),
                            spacing="2",
                        ),

                        # Callout de restriccion (si esta restringido)
                        rx.cond(
                            EmpleadosState.empleado_esta_restringido,
                            rx.callout(
                                rx.vstack(
                                    rx.text("Motivo:", weight="bold", size="2"),
                                    rx.cond(
                                        EmpleadosState.es_admin,
                                        rx.text(
                                            EmpleadosState.motivo_restriccion_actual,
                                            size="2",
                                        ),
                                        rx.text(
                                            "Contacte al administrador para mas informacion.",
                                            size="2",
                                            color="gray",
                                        ),
                                    ),
                                    rx.cond(
                                        EmpleadosState.fecha_restriccion_actual != "",
                                        rx.text(
                                            "Desde: ",
                                            EmpleadosState.fecha_restriccion_actual,
                                            size="1",
                                            color="gray",
                                        ),
                                    ),
                                    spacing="1",
                                    align_items="start",
                                ),
                                icon="triangle-alert",
                                color_scheme="red",
                                size="2",
                                width="100%",
                            ),
                        ),

                        rx.divider(),

                        # Datos personales
                        rx.vstack(
                            rx.text("Datos Personales", weight="bold", size="3"),
                            rx.hstack(
                                rx.vstack(
                                    rx.text("CURP", size="1", color="gray"),
                                    rx.text(EmpleadosState.empleado_seleccionado["curp"], size="2"),
                                    spacing="1",
                                ),
                                rx.vstack(
                                    rx.text("RFC", size="1", color="gray"),
                                    rx.text(
                                        rx.cond(
                                            EmpleadosState.empleado_seleccionado["rfc"],
                                            EmpleadosState.empleado_seleccionado["rfc"],
                                            "No registrado",
                                        ),
                                        size="2",
                                    ),
                                    spacing="1",
                                ),
                                rx.vstack(
                                    rx.text("NSS", size="1", color="gray"),
                                    rx.text(
                                        rx.cond(
                                            EmpleadosState.empleado_seleccionado["nss"],
                                            EmpleadosState.empleado_seleccionado["nss"],
                                            "No registrado",
                                        ),
                                        size="2",
                                    ),
                                    spacing="1",
                                ),
                                spacing="4",
                                width="100%",
                            ),
                            spacing="2",
                            width="100%",
                            align_items="start",
                        ),

                        rx.divider(),

                        # Empresa y contacto
                        rx.vstack(
                            rx.text("Información Laboral", weight="bold", size="3"),
                            rx.hstack(
                                rx.vstack(
                                    rx.text("Empresa", size="1", color="gray"),
                                    rx.text(EmpleadosState.empleado_seleccionado["empresa_nombre"], size="2"),
                                    spacing="1",
                                ),
                                rx.vstack(
                                    rx.text("Fecha Ingreso", size="1", color="gray"),
                                    rx.text(
                                        rx.cond(
                                            EmpleadosState.empleado_seleccionado["fecha_ingreso"],
                                            EmpleadosState.empleado_seleccionado["fecha_ingreso"],
                                            "No registrada",
                                        ),
                                        size="2",
                                    ),
                                    spacing="1",
                                ),
                                spacing="4",
                                width="100%",
                            ),
                            spacing="2",
                            width="100%",
                            align_items="start",
                        ),

                        rx.divider(),

                        # Contacto
                        rx.vstack(
                            rx.text("Contacto", weight="bold", size="3"),
                            rx.hstack(
                                rx.vstack(
                                    rx.text("Teléfono", size="1", color="gray"),
                                    rx.text(
                                        rx.cond(
                                            EmpleadosState.empleado_seleccionado["telefono"],
                                            EmpleadosState.empleado_seleccionado["telefono"],
                                            "No registrado",
                                        ),
                                        size="2",
                                    ),
                                    spacing="1",
                                ),
                                rx.vstack(
                                    rx.text("Email", size="1", color="gray"),
                                    rx.text(
                                        rx.cond(
                                            EmpleadosState.empleado_seleccionado["email"],
                                            EmpleadosState.empleado_seleccionado["email"],
                                            "No registrado",
                                        ),
                                        size="2",
                                    ),
                                    spacing="1",
                                ),
                                spacing="4",
                                width="100%",
                            ),
                            spacing="2",
                            width="100%",
                            align_items="start",
                        ),

                        spacing="4",
                        width="100%",
                    ),
                ),

                spacing="4",
                width="100%",
                padding_y="4",
            ),

            # Botones de accion
            rx.box(height="16px"),
            rx.hstack(
                # Ver historial (solo admin)
                rx.cond(
                    EmpleadosState.es_admin,
                    rx.button(
                        rx.icon("history", size=14),
                        "Historial",
                        variant="soft",
                        color_scheme="gray",
                        on_click=EmpleadosState.abrir_modal_historial,
                    ),
                ),
                # Restringir (solo admin, solo si no restringido)
                rx.cond(
                    EmpleadosState.puede_restringir,
                    rx.button(
                        rx.icon("ban", size=14),
                        "Restringir",
                        variant="soft",
                        color_scheme="red",
                        on_click=EmpleadosState.abrir_modal_restriccion,
                    ),
                ),
                # Liberar (solo admin, solo si restringido)
                rx.cond(
                    EmpleadosState.puede_liberar,
                    rx.button(
                        rx.icon("circle-check", size=14),
                        "Liberar",
                        variant="soft",
                        color_scheme="green",
                        on_click=EmpleadosState.abrir_modal_liberacion,
                    ),
                ),
                # Reactivar (si inactivo Y no restringido)
                rx.cond(
                    EmpleadosState.empleado_esta_inactivo & ~EmpleadosState.empleado_esta_restringido,
                    rx.button(
                        rx.icon("user-check", size=14),
                        "Reactivar",
                        variant="soft",
                        color_scheme="green",
                        on_click=EmpleadosState.reactivar_empleado,
                    ),
                ),
                spacing="3",
                width="100%",
                justify="end",
            ),

            max_width="650px",
        ),
        open=EmpleadosState.mostrar_modal_detalle,
        # No cerrar al hacer click fuera - solo con botones
        on_open_change=rx.noop,
    )


# =============================================================================
# MODAL BAJA
# =============================================================================

def modal_baja() -> rx.Component:
    """Modal para dar de baja a un empleado"""
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title("Dar de Baja"),
            rx.dialog.description(
                rx.text(
                    "¿Está seguro que desea dar de baja a ",
                    rx.text(EmpleadosState.nombre_completo_seleccionado, weight="bold"),
                    "?",
                ),
            ),

            rx.vstack(
                rx.vstack(
                    rx.text("Motivo de baja *", size="2", weight="medium"),
                    rx.select.root(
                        rx.select.trigger(
                            placeholder="Seleccionar motivo...",
                            width="100%",
                        ),
                        rx.select.content(
                            rx.foreach(
                                EmpleadosState.opciones_motivo_baja,
                                lambda opt: rx.select.item(opt["label"], value=opt["value"]),
                            ),
                        ),
                        value=EmpleadosState.form_motivo_baja,
                        on_change=EmpleadosState.set_form_motivo_baja,
                    ),
                    width="100%",
                    spacing="1",
                ),
                spacing="4",
                width="100%",
                padding_y="4",
            ),

            rx.hstack(
                boton_cancelar(on_click=EmpleadosState.cerrar_modal_baja),
                boton_guardar(
                    texto="Confirmar Baja",
                    texto_guardando="Procesando...",
                    on_click=EmpleadosState.dar_de_baja,
                    saving=EmpleadosState.saving,
                    color_scheme="red",
                ),
                spacing="3",
                justify="end",
                width="100%",
            ),

            max_width="400px",
        ),
        open=EmpleadosState.mostrar_modal_baja,
        # No cerrar al hacer click fuera - solo con botones
        on_open_change=rx.noop,
    )


# =============================================================================
# MODAL RESTRICCION
# =============================================================================

def modal_restriccion() -> rx.Component:
    """Modal para restringir un empleado."""
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title(
                rx.hstack(
                    rx.icon("ban", size=20, color=Colors.ERROR),
                    rx.text("Restringir Empleado"),
                    spacing="2",
                    align="center",
                ),
            ),

            rx.vstack(
                # Info del empleado
                rx.cond(
                    EmpleadosState.empleado_seleccionado,
                    rx.vstack(
                        rx.hstack(
                            rx.text("Empleado:", weight="medium"),
                            rx.text(EmpleadosState.nombre_completo_seleccionado),
                            spacing="2",
                        ),
                        rx.hstack(
                            rx.text("Clave:", weight="medium"),
                            rx.badge(
                                EmpleadosState.empleado_seleccionado["clave"],
                                variant="outline",
                            ),
                            spacing="2",
                        ),
                        rx.hstack(
                            rx.text("CURP:", weight="medium"),
                            rx.text(EmpleadosState.empleado_seleccionado["curp"]),
                            spacing="2",
                        ),
                        spacing="2",
                        width="100%",
                        align_items="start",
                    ),
                ),

                rx.divider(),

                # Advertencia
                rx.callout(
                    rx.text(
                        "Esta accion bloqueara al empleado en ", rx.text.strong("TODO")," el sistema. " \
                        "Ninguna empresa proveedora podra darlo de alta.", as_='span'
                    ),
                    icon="triangle-alert",
                    color_scheme="red",
                    size="2",
                ),

                # Motivo (obligatorio)
                rx.vstack(
                    rx.text("Motivo de restriccion *", size="2", weight="medium"),
                    rx.text_area(
                        placeholder="Describa el motivo de la restriccion (minimo 10 caracteres)...",
                        value=EmpleadosState.form_motivo_restriccion,
                        on_change=EmpleadosState.set_form_motivo_restriccion,
                        max_length=500,
                        rows="3",
                        width="100%",
                    ),
                    rx.text(
                        EmpleadosState.form_motivo_restriccion.length(),
                        "/500 caracteres (min. 10)",
                        size="1",
                        color="gray",
                    ),
                    width="100%",
                    spacing="1",
                ),

                # Notas adicionales (opcional)
                rx.vstack(
                    rx.text("Notas adicionales (opcional)", size="2", weight="medium"),
                    rx.text_area(
                        placeholder="Observaciones, numero de expediente, etc...",
                        value=EmpleadosState.form_notas_restriccion,
                        on_change=EmpleadosState.set_form_notas_restriccion,
                        max_length=1000,
                        rows="2",
                        width="100%",
                    ),
                    width="100%",
                    spacing="1",
                ),

                # Botones
                rx.hstack(
                    boton_cancelar(
                        on_click=EmpleadosState.cerrar_modal_restriccion,
                    ),
                    boton_guardar(
                        texto="Confirmar Restriccion",
                        texto_guardando="Restringiendo...",
                        on_click=EmpleadosState.confirmar_restriccion,
                        saving=EmpleadosState.saving,
                        disabled=~EmpleadosState.puede_guardar_restriccion,
                        color_scheme="red",
                    ),
                    spacing="3",
                    justify="end",
                    width="100%",
                ),
                spacing="4",
                width="100%",
                padding_y="4",
            ),


            max_width="500px",
        ),
        open=EmpleadosState.mostrar_modal_restriccion,
        # No cerrar al hacer click fuera - solo con botones
        on_open_change=rx.noop,
    )


# =============================================================================
# MODAL LIBERACION
# =============================================================================

def modal_liberacion() -> rx.Component:
    """Modal para liberar restriccion de un empleado."""
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title(
                rx.hstack(
                    rx.icon("circle-check", size=20, color=Colors.SUCCESS),
                    rx.text("Liberar Restriccion"),
                    spacing="2",
                    align="center",
                ),
            ),

            rx.vstack(
                # Info del empleado
                rx.cond(
                    EmpleadosState.empleado_seleccionado,
                    rx.vstack(
                        rx.hstack(
                            rx.text("Empleado:", weight="medium"),
                            rx.text(EmpleadosState.nombre_completo_seleccionado),
                            spacing="2",
                        ),
                        rx.badge(
                            EmpleadosState.empleado_seleccionado["clave"],
                            variant="outline",
                        ),
                        spacing="2",
                        width="100%",
                    ),
                ),

                rx.divider(),

                # Restriccion actual
                rx.callout(
                    rx.vstack(
                        rx.text("Restriccion actual:", weight="bold", size="2"),
                        rx.text(
                            EmpleadosState.motivo_restriccion_actual,
                            size="2",
                        ),
                        rx.cond(
                            EmpleadosState.fecha_restriccion_actual != "",
                            rx.text(
                                "Fecha: ",
                                EmpleadosState.fecha_restriccion_actual,
                                size="1",
                                color="gray",
                            ),
                        ),
                        spacing="1",
                        align_items="start",
                    ),
                    icon="info",
                    color_scheme="blue",
                    size="2",
                ),

                # Motivo de liberacion (obligatorio)
                rx.vstack(
                    rx.text("Motivo de liberacion *", size="2", weight="medium"),
                    rx.text_area(
                        placeholder="Describa por que se libera la restriccion (minimo 10 caracteres)...",
                        value=EmpleadosState.form_motivo_liberacion,
                        on_change=EmpleadosState.set_form_motivo_liberacion,
                        max_length=500,
                        rows="3",
                        width="100%",
                    ),
                    rx.text(
                        EmpleadosState.form_motivo_liberacion.length(),
                        "/500 caracteres (min. 10)",
                        size="1",
                        color="gray",
                    ),
                    width="100%",
                    spacing="1",
                ),

                # Notas adicionales (opcional)
                rx.vstack(
                    rx.text("Notas adicionales (opcional)", size="2", weight="medium"),
                    rx.text_area(
                        placeholder="Observaciones adicionales...",
                        value=EmpleadosState.form_notas_liberacion,
                        on_change=EmpleadosState.set_form_notas_liberacion,
                        max_length=1000,
                        rows="2",
                        width="100%",
                    ),
                    width="100%",
                    spacing="1",
                ),

                spacing="4",
                width="100%",
                padding_y="4",
            ),

            # Botones
            rx.hstack(
                boton_cancelar(
                    on_click=EmpleadosState.cerrar_modal_liberacion,
                ),
                boton_guardar(
                    texto="Confirmar Liberacion",
                    texto_guardando="Liberando...",
                    on_click=EmpleadosState.confirmar_liberacion,
                    saving=EmpleadosState.saving,
                    disabled=~EmpleadosState.puede_guardar_liberacion,
                    color_scheme="green",
                ),
                spacing="3",
                justify="end",
                width="100%",
            ),

            max_width="500px",
        ),
        open=EmpleadosState.mostrar_modal_liberacion,
        # No cerrar al hacer click fuera - solo con botones
        on_open_change=rx.noop,
    )


# =============================================================================
# MODAL HISTORIAL RESTRICCIONES
# =============================================================================

def _item_historial(item: dict) -> rx.Component:
    """Renderiza un item del historial de restricciones."""
    return rx.card(
        rx.vstack(
            # Header con badge de accion y fecha
            rx.hstack(
                rx.cond(
                    item["es_restriccion"],
                    rx.badge(
                        rx.hstack(
                            rx.icon("ban", size=12),
                            rx.text("RESTRICCION"),
                            spacing="1",
                        ),
                        color_scheme="red",
                        variant="solid",
                    ),
                    rx.badge(
                        rx.hstack(
                            rx.icon("check", size=12),
                            rx.text("LIBERACION"),
                            spacing="1",
                        ),
                        color_scheme="green",
                        variant="solid",
                    ),
                ),
                rx.spacer(),
                rx.text(item["fecha"], size="1", color="gray"),
                width="100%",
            ),

            # Motivo
            rx.text(item["motivo"], size="2"),

            # Ejecutado por
            rx.hstack(
                rx.icon("user", size=12, color="gray"),
                rx.text("Por: ", item["ejecutado_por_nombre"], size="1", color="gray"),
                spacing="1",
            ),

            # Notas (si existen)
            rx.cond(
                item["notas"] != "",
                rx.box(
                    rx.text(
                        item["notas"],
                        size="1",
                        color="gray",
                        style={"font-style": "italic"},
                    ),
                    padding="2",
                    background="var(--gray-2)",
                    border_radius="4px",
                    width="100%",
                ),
            ),

            spacing="2",
            width="100%",
            align_items="start",
        ),
        width="100%",
    )


def modal_historial_restricciones() -> rx.Component:
    """Modal que muestra el historial de restricciones de un empleado."""
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title(
                rx.hstack(
                    rx.icon("history", size=20),
                    rx.text("Historial de Restricciones"),
                    spacing="2",
                    align="center",
                ),
            ),

            rx.vstack(
                # Info del empleado
                rx.cond(
                    EmpleadosState.empleado_seleccionado,
                    rx.hstack(
                        rx.text("Empleado:", weight="medium"),
                        rx.text(EmpleadosState.nombre_completo_seleccionado),
                        rx.badge(
                            EmpleadosState.empleado_seleccionado["clave"],
                            variant="outline",
                            size="1",
                        ),
                        spacing="2",
                    ),
                ),

                rx.divider(),

                # Lista de historial
                rx.cond(
                    EmpleadosState.loading,
                    rx.center(
                        rx.spinner(size="3"),
                        padding="8",
                    ),
                    rx.cond(
                        EmpleadosState.tiene_historial_restricciones,
                        rx.vstack(
                            rx.foreach(
                                EmpleadosState.historial_restricciones,
                                _item_historial,
                            ),
                            spacing="3",
                            width="100%",
                            max_height="400px",
                            overflow_y="auto",
                        ),
                        rx.callout(
                            "Este empleado no tiene historial de restricciones.",
                            icon="info",
                            color_scheme="blue",
                        ),
                    ),
                ),

                spacing="4",
                width="100%",
                padding_y="4",
            ),

            # Boton cerrar
            rx.hstack(
                rx.button(
                    "Cerrar",
                    variant="soft",
                    color_scheme="gray",
                    on_click=EmpleadosState.cerrar_modal_historial,
                ),
                justify="end",
                width="100%",
            ),

            max_width="550px",
        ),
        open=EmpleadosState.mostrar_modal_historial,
        # No cerrar al hacer click fuera - solo con botones
        on_open_change=rx.noop,
    )
