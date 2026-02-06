"""
Modales para la pagina de Empleados.

Modal crear/editar, detalle, baja, restriccion, liberacion e historial.
"""
import reflex as rx

from app.presentation.pages.empleados.empleados_state import EmpleadosState
from .components import estatus_badge, restriccion_badge


# =============================================================================
# MODAL CREAR/EDITAR EMPLEADO
# =============================================================================

def modal_empleado() -> rx.Component:
    """Modal para crear/editar empleado"""
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title(EmpleadosState.titulo_modal),
            rx.dialog.description("Complete los datos del empleado"),

            rx.vstack(
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
                    rx.vstack(
                        rx.text("CURP *", size="2", weight="medium"),
                        rx.input(
                            value=EmpleadosState.form_curp,
                            on_change=EmpleadosState.set_form_curp,
                            on_blur=EmpleadosState.validar_curp_blur,
                            placeholder="18 caracteres",
                            max_length=18,
                            width="100%",
                        ),
                        rx.cond(
                            EmpleadosState.error_curp != "",
                            rx.text(EmpleadosState.error_curp, size="1", color="red"),
                        ),
                        width="100%",
                        spacing="1",
                    ),
                ),

                # Nombre y apellidos
                rx.hstack(
                    rx.vstack(
                        rx.text("Nombre *", size="2", weight="medium"),
                        rx.input(
                            value=EmpleadosState.form_nombre,
                            on_change=EmpleadosState.set_form_nombre,
                            on_blur=EmpleadosState.validar_nombre_blur,
                            placeholder="Nombre(s)",
                            width="100%",
                        ),
                        rx.cond(
                            EmpleadosState.error_nombre != "",
                            rx.text(EmpleadosState.error_nombre, size="1", color="red"),
                        ),
                        width="100%",
                        spacing="1",
                    ),
                    rx.vstack(
                        rx.text("Apellido Paterno *", size="2", weight="medium"),
                        rx.input(
                            value=EmpleadosState.form_apellido_paterno,
                            on_change=EmpleadosState.set_form_apellido_paterno,
                            on_blur=EmpleadosState.validar_apellido_paterno_blur,
                            placeholder="Apellido paterno",
                            width="100%",
                        ),
                        rx.cond(
                            EmpleadosState.error_apellido_paterno != "",
                            rx.text(EmpleadosState.error_apellido_paterno, size="1", color="red"),
                        ),
                        width="100%",
                        spacing="1",
                    ),
                    rx.vstack(
                        rx.text("Apellido Materno", size="2", weight="medium"),
                        rx.input(
                            value=EmpleadosState.form_apellido_materno,
                            on_change=EmpleadosState.set_form_apellido_materno,
                            placeholder="Apellido materno (opcional)",
                            width="100%",
                        ),
                        width="100%",
                        spacing="1",
                    ),
                    spacing="3",
                    width="100%",
                ),

                # RFC y NSS
                rx.hstack(
                    rx.vstack(
                        rx.text("RFC", size="2", weight="medium"),
                        rx.input(
                            value=EmpleadosState.form_rfc,
                            on_change=EmpleadosState.set_form_rfc,
                            on_blur=EmpleadosState.validar_rfc_blur,
                            placeholder="13 caracteres",
                            max_length=13,
                            width="100%",
                        ),
                        rx.cond(
                            EmpleadosState.error_rfc != "",
                            rx.text(EmpleadosState.error_rfc, size="1", color="red"),
                        ),
                        width="100%",
                        spacing="1",
                    ),
                    rx.vstack(
                        rx.text("NSS", size="2", weight="medium"),
                        rx.input(
                            value=EmpleadosState.form_nss,
                            on_change=EmpleadosState.set_form_nss,
                            on_blur=EmpleadosState.validar_nss_blur,
                            placeholder="11 dígitos",
                            max_length=11,
                            width="100%",
                        ),
                        rx.cond(
                            EmpleadosState.error_nss != "",
                            rx.text(EmpleadosState.error_nss, size="1", color="red"),
                        ),
                        width="100%",
                        spacing="1",
                    ),
                    spacing="3",
                    width="100%",
                ),

                # Fecha nacimiento y género
                rx.hstack(
                    rx.vstack(
                        rx.text("Fecha de Nacimiento", size="2", weight="medium"),
                        rx.input(
                            type="date",
                            value=EmpleadosState.form_fecha_nacimiento,
                            on_change=EmpleadosState.set_form_fecha_nacimiento,
                            width="100%",
                        ),
                        width="100%",
                        spacing="1",
                    ),
                    rx.vstack(
                        rx.text("Género", size="2", weight="medium"),
                        rx.select.root(
                            rx.select.trigger(
                                placeholder="Seleccionar...",
                                width="100%",
                            ),
                            rx.select.content(
                                rx.foreach(
                                    EmpleadosState.opciones_genero,
                                    lambda opt: rx.select.item(opt["label"], value=opt["value"]),
                                ),
                            ),
                            value=EmpleadosState.form_genero,
                            on_change=EmpleadosState.set_form_genero,
                        ),
                        width="100%",
                        spacing="1",
                    ),
                    spacing="3",
                    width="100%",
                ),

                # Teléfono y email
                rx.hstack(
                    rx.vstack(
                        rx.text("Teléfono", size="2", weight="medium"),
                        rx.input(
                            value=EmpleadosState.form_telefono,
                            on_change=EmpleadosState.set_form_telefono,
                            on_blur=EmpleadosState.validar_telefono_blur,
                            placeholder="10 dígitos",
                            max_length=15,
                            width="100%",
                        ),
                        rx.cond(
                            EmpleadosState.error_telefono != "",
                            rx.text(EmpleadosState.error_telefono, size="1", color="red"),
                        ),
                        width="100%",
                        spacing="1",
                    ),
                    rx.vstack(
                        rx.text("Email", size="2", weight="medium"),
                        rx.input(
                            value=EmpleadosState.form_email,
                            on_change=EmpleadosState.set_form_email,
                            on_blur=EmpleadosState.validar_email_blur,
                            placeholder="correo@ejemplo.com",
                            width="100%",
                        ),
                        rx.cond(
                            EmpleadosState.error_email != "",
                            rx.text(EmpleadosState.error_email, size="1", color="red"),
                        ),
                        width="100%",
                        spacing="1",
                    ),
                    spacing="3",
                    width="100%",
                ),

                # Dirección
                rx.vstack(
                    rx.text("Dirección", size="2", weight="medium"),
                    rx.text_area(
                        value=EmpleadosState.form_direccion,
                        on_change=EmpleadosState.set_form_direccion,
                        placeholder="Dirección completa",
                        width="100%",
                        rows="2",
                    ),
                    width="100%",
                    spacing="1",
                ),

                # Contacto de emergencia
                rx.vstack(
                    rx.text("Contacto de Emergencia", size="2", weight="medium"),
                    rx.input(
                        value=EmpleadosState.form_contacto_emergencia,
                        on_change=EmpleadosState.set_form_contacto_emergencia,
                        placeholder="Nombre y teléfono",
                        width="100%",
                    ),
                    width="100%",
                    spacing="1",
                ),

                # Notas
                rx.vstack(
                    rx.text("Notas", size="2", weight="medium"),
                    rx.text_area(
                        value=EmpleadosState.form_notas,
                        on_change=EmpleadosState.set_form_notas,
                        placeholder="Observaciones adicionales",
                        width="100%",
                        rows="2",
                    ),
                    width="100%",
                    spacing="1",
                ),

                spacing="4",
                width="100%",
                padding_y="4",
            ),

            # Botones de acción
            rx.hstack(
                rx.button(
                    "Cancelar",
                    variant="soft",
                    color_scheme="gray",
                    on_click=EmpleadosState.cerrar_modal_empleado,
                ),
                rx.button(
                    rx.cond(
                        EmpleadosState.saving,
                        rx.spinner(size="1"),
                        rx.icon("save", size=16),
                    ),
                    "Guardar",
                    on_click=EmpleadosState.guardar_empleado,
                    disabled=EmpleadosState.saving,
                    color_scheme="blue",
                ),
                spacing="3",
                justify="end",
                width="100%",
            ),

            max_width="600px",
        ),
        open=EmpleadosState.mostrar_modal_empleado,
        # No cerrar al hacer click fuera - solo con botones
        on_open_change=rx.noop,
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
                rx.button(
                    "Cancelar",
                    variant="soft",
                    color_scheme="gray",
                    on_click=EmpleadosState.cerrar_modal_baja,
                ),
                rx.button(
                    rx.cond(
                        EmpleadosState.saving,
                        rx.spinner(size="1"),
                        rx.icon("user-x", size=16),
                    ),
                    "Confirmar Baja",
                    on_click=EmpleadosState.dar_de_baja,
                    disabled=EmpleadosState.saving,
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
                    rx.icon("ban", size=20, color="red"),
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
                    rx.button(
                        "Cancelar",
                        variant="soft",
                        color_scheme="gray",
                        on_click=EmpleadosState.cerrar_modal_restriccion,
                    ),
                    rx.button(
                        rx.cond(
                            EmpleadosState.saving,
                            rx.hstack(
                                rx.spinner(size="1"),
                                rx.text("Restringiendo..."),
                                spacing="2",
                            ),
                            rx.hstack(
                                rx.icon("ban", size=14),
                                rx.text("Confirmar Restriccion"),
                                spacing="2",
                            ),
                        ),
                        on_click=EmpleadosState.confirmar_restriccion,
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
                    rx.icon("circle-check", size=20, color="green"),
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
                rx.button(
                    "Cancelar",
                    variant="soft",
                    color_scheme="gray",
                    on_click=EmpleadosState.cerrar_modal_liberacion,
                ),
                rx.button(
                    rx.cond(
                        EmpleadosState.saving,
                        rx.hstack(
                            rx.spinner(size="1"),
                            rx.text("Liberando..."),
                            spacing="2",
                        ),
                        rx.hstack(
                            rx.icon("check", size=14),
                            rx.text("Confirmar Liberacion"),
                            spacing="2",
                        ),
                    ),
                    on_click=EmpleadosState.confirmar_liberacion,
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
