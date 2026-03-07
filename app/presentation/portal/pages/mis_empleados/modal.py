"""
Modal para crear/editar empleados en el portal.
"""
import reflex as rx

from app.presentation.theme import Colors, Radius, Spacing, Typography
from app.presentation.components.ui import (
    employee_status_badge,
    form_date,
    form_select,
    form_textarea,
)
from app.presentation.components.reusable import (
    employee_form_body,
    employee_form_modal,
    employee_address_field,
    employee_bank_data_section,
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
                "El empleado se asignará a ",
                rx.text(
                    MisEmpleadosState.nombre_empresa_actual,
                    font_weight=Typography.WEIGHT_BOLD,
                    as_="span",
                ),
            ),
        ),
        body=employee_form_body(
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

                # Datos bancarios
                _seccion_datos_bancarios(),

                # Notas
                _campo_notas(),

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


def modal_baja() -> rx.Component:
    """Modal para dar de baja a un empleado desde el portal."""
    return employee_form_modal(
        open_state=MisEmpleadosState.mostrar_modal_baja,
        title="Dar de Baja",
        description=rx.vstack(
            rx.text("Se registrará la baja del empleado seleccionado."),
            rx.hstack(
                rx.text(
                    MisEmpleadosState.nombre_empleado_baja,
                    font_weight=Typography.WEIGHT_BOLD,
                ),
                rx.cond(
                    MisEmpleadosState.clave_empleado_baja != "",
                    rx.text(
                        "(" + MisEmpleadosState.clave_empleado_baja + ")",
                        color=Colors.TEXT_SECONDARY,
                    ),
                    rx.fragment(),
                ),
                spacing="2",
                align="center",
            ),
            spacing="1",
            align="start",
        ),
        body=employee_form_body(
            form_select(
                label="Motivo de baja",
                required=True,
                placeholder="Seleccionar motivo...",
                value=MisEmpleadosState.form_motivo_baja,
                on_change=MisEmpleadosState.set_form_motivo_baja,
                options=[
                    {"label": "Renuncia voluntaria", "value": "RENUNCIA"},
                    {"label": "Despido", "value": "DESPIDO"},
                    {"label": "Fin de contrato", "value": "FIN_CONTRATO"},
                    {"label": "Jubilación", "value": "JUBILACION"},
                    {"label": "Fallecimiento", "value": "FALLECIMIENTO"},
                    {"label": "Otro", "value": "OTRO"},
                ],
                error=MisEmpleadosState.error_motivo_baja,
            ),
            form_date(
                label="Fecha efectiva",
                value=MisEmpleadosState.form_fecha_efectiva_baja,
                on_change=MisEmpleadosState.set_form_fecha_efectiva_baja,
                error=MisEmpleadosState.error_fecha_efectiva_baja,
                hint="Último día de trabajo. Si es hoy, deje el campo vacío.",
            ),
            form_textarea(
                label="Observaciones",
                placeholder="Detalles adicionales sobre la baja...",
                value=MisEmpleadosState.form_notas_baja,
                on_change=MisEmpleadosState.set_form_notas_baja,
                rows="3",
            ),
            rx.callout(
                rx.text(
                    "Se generará una alerta automática para entregar liquidación o finiquito dentro de 15 días hábiles.",
                    font_size=Typography.SIZE_BASE,
                ),
                icon="info",
                color_scheme="blue",
                size="1",
                width="100%",
            ),
            padding_y=Spacing.SM,
        ),
        on_cancel=MisEmpleadosState.cerrar_modal_baja,
        on_save=MisEmpleadosState.confirmar_baja,
        save_text="Confirmar Baja",
        saving=MisEmpleadosState.saving,
        save_loading_text="Procesando...",
        save_color_scheme="red",
        max_width="480px",
    )


# =============================================================================
# MODALES DE DETALLE
# =============================================================================

def modal_detalle_empleado() -> rx.Component:
    """Modal de solo lectura para consulta operativa del empleado."""
    return rx.dialog.root(
        rx.dialog.content(
            rx.hstack(
                rx.vstack(
                    rx.dialog.title(MisEmpleadosState.detalle_nombre_empleado),
                    rx.hstack(
                        rx.cond(
                            MisEmpleadosState.detalle_clave_empleado != "",
                            rx.badge(
                                MisEmpleadosState.detalle_clave_empleado,
                                variant="outline",
                                size="2",
                            ),
                            rx.fragment(),
                        ),
                        rx.cond(
                            MisEmpleadosState.empleado_detalle.get("estatus", "") != "",
                            employee_status_badge(
                                MisEmpleadosState.empleado_detalle.get("estatus", ""),
                                size="2",
                            ),
                            rx.fragment(),
                        ),
                        rx.cond(
                            MisEmpleadosState.detalle_expediente_href != "",
                            rx.link(
                                rx.badge(
                                    "Expediente " + MisEmpleadosState.detalle_expediente_resumen,
                                    variant="soft",
                                    color_scheme="teal",
                                    size="2",
                                ),
                                href=MisEmpleadosState.detalle_expediente_href,
                                underline="none",
                                display="inline-flex",
                                align_items="center",
                                line_height="1",
                            ),
                            rx.badge(
                                "Expediente " + MisEmpleadosState.detalle_expediente_resumen,
                                variant="soft",
                                color_scheme="teal",
                                size="2",
                            ),
                        ),
                        spacing="2",
                        align="center",
                        wrap="wrap",
                        width="100%",
                    ),
                    spacing="2",
                    align="start",
                    width="100%",
                ),
                rx.button(
                    rx.icon("x", size=16),
                    variant="ghost",
                    color_scheme="gray",
                    size="1",
                    on_click=MisEmpleadosState.cerrar_modal_detalle,
                ),
                align="start",
                justify="between",
                width="100%",
                spacing="3",
            ),
            rx.cond(
                MisEmpleadosState.loading_detalle_empleado,
                rx.center(
                    rx.vstack(
                        rx.spinner(size="3"),
                        rx.text(
                            "Cargando detalle del empleado...",
                            color=Colors.TEXT_SECONDARY,
                            font_size=Typography.SIZE_SM,
                        ),
                        spacing="3",
                        align="center",
                    ),
                    min_height="320px",
                    width="100%",
                ),
                rx.vstack(
                    _seccion_detalle(
                        "Datos generales",
                        "user",
                        rx.grid(
                            _campo_detalle(
                                "CURP",
                                MisEmpleadosState.empleado_detalle.get("curp", ""),
                            ),
                            _campo_detalle(
                                "RFC",
                                MisEmpleadosState.empleado_detalle.get("rfc", ""),
                            ),
                            _campo_detalle(
                                "NSS",
                                MisEmpleadosState.empleado_detalle.get("nss", ""),
                            ),
                            _campo_detalle(
                                "Fecha de ingreso",
                                MisEmpleadosState.empleado_detalle.get("fecha_ingreso", ""),
                            ),
                            _campo_detalle(
                                "Telefono",
                                MisEmpleadosState.empleado_detalle.get("telefono", ""),
                            ),
                            _campo_detalle(
                                "Email",
                                MisEmpleadosState.empleado_detalle.get("email", ""),
                            ),
                            _campo_detalle(
                                "Direccion",
                                MisEmpleadosState.empleado_detalle.get("direccion", ""),
                                ancho_completo=True,
                            ),
                            _campo_detalle(
                                "Notas",
                                MisEmpleadosState.empleado_detalle.get("notas", ""),
                                fallback="Sin notas registradas",
                                ancho_completo=True,
                            ),
                            columns=rx.breakpoints(initial="1", sm="2"),
                            spacing="4",
                            width="100%",
                        ),
                    ),
                    _seccion_detalle(
                        "Contacto de emergencia",
                        "phone",
                        rx.grid(
                            _campo_detalle(
                                "Nombre",
                                MisEmpleadosState.empleado_detalle.get("contacto_nombre", ""),
                            ),
                            _campo_detalle(
                                "Telefono",
                                MisEmpleadosState.empleado_detalle.get("contacto_telefono", ""),
                            ),
                            _campo_detalle(
                                "Parentesco",
                                MisEmpleadosState.empleado_detalle.get("contacto_parentesco", ""),
                            ),
                            columns=rx.breakpoints(initial="1", sm="2"),
                            spacing="4",
                            width="100%",
                        ),
                    ),
                    _seccion_detalle(
                        "Datos bancarios actuales",
                        "credit-card",
                        rx.cond(
                            MisEmpleadosState.detalle_tiene_bancarios,
                            rx.grid(
                                _campo_detalle(
                                    "Banco",
                                    MisEmpleadosState.detalle_banco_actual,
                                ),
                                _campo_detalle(
                                    "Cuenta bancaria",
                                    MisEmpleadosState.detalle_cuenta_bancaria_mascara,
                                ),
                                _campo_detalle(
                                    "CLABE interbancaria",
                                    MisEmpleadosState.detalle_clabe_mascara,
                                ),
                                columns=rx.breakpoints(initial="1", sm="2"),
                                spacing="4",
                                width="100%",
                            ),
                            rx.text(
                                "No hay datos bancarios registrados.",
                                color=Colors.TEXT_SECONDARY,
                                font_size=Typography.SIZE_SM,
                            ),
                        ),
                    ),
                    _seccion_detalle(
                        "Trazabilidad bancaria",
                        "history",
                        rx.grid(
                            _campo_detalle(
                                "Ultima actualizacion",
                                MisEmpleadosState.ultima_actualizacion_bancaria,
                            ),
                            _campo_detalle(
                                "Origen",
                                MisEmpleadosState.origen_ultima_actualizacion_bancaria,
                            ),
                            _campo_detalle(
                                "Cambios registrados",
                                MisEmpleadosState.historial_bancario_total.to_string(),
                                fallback="0",
                            ),
                            columns=rx.breakpoints(initial="1", sm="2"),
                            spacing="4",
                            width="100%",
                        ),
                        rx.cond(
                            MisEmpleadosState.tiene_historial_bancario,
                            rx.callout(
                                rx.text(
                                    "El historial bancario conserva cada actualización registrada del empleado.",
                                    font_size=Typography.SIZE_SM,
                                ),
                                icon="shield-check",
                                color_scheme="green",
                                size="1",
                                width="100%",
                            ),
                            rx.callout(
                                rx.text(
                                    "Aún no hay movimientos bancarios auditados para este empleado.",
                                    font_size=Typography.SIZE_SM,
                                ),
                                icon="info",
                                color_scheme="gray",
                                size="1",
                                width="100%",
                            ),
                        ),
                        action=rx.cond(
                            MisEmpleadosState.tiene_historial_bancario,
                            rx.button(
                                rx.icon("history", size=14),
                                "Ver historial bancario",
                                on_click=MisEmpleadosState.abrir_modal_historial_bancario,
                                variant="soft",
                                color_scheme="gray",
                                size="2",
                            ),
                            rx.fragment(),
                        ),
                    ),
                    spacing="4",
                    width="100%",
                    padding_y=Spacing.SM,
                ),
            ),
            rx.hstack(
                rx.button(
                    "Cerrar",
                    variant="soft",
                    color_scheme="gray",
                    on_click=MisEmpleadosState.cerrar_modal_detalle,
                ),
                rx.cond(
                    MisEmpleadosState.puede_editar_detalle,
                    rx.button(
                        rx.icon("pencil", size=14),
                        "Editar",
                        variant="soft",
                        color_scheme="teal",
                        on_click=MisEmpleadosState.abrir_modal_editar_desde_detalle,
                    ),
                    rx.fragment(),
                ),
                rx.spacer(),
                rx.cond(
                    MisEmpleadosState.puede_dar_baja_detalle,
                    rx.button(
                        rx.icon("user-minus", size=14),
                        "Dar de baja",
                        variant="soft",
                        color_scheme="red",
                        on_click=MisEmpleadosState.abrir_modal_baja_desde_detalle,
                    ),
                    rx.fragment(),
                ),
                width="100%",
                align="center",
                spacing="3",
                margin_top="4",
            ),
            max_width="820px",
            padding="6",
        ),
        open=MisEmpleadosState.mostrar_modal_detalle,
        on_open_change=rx.noop,
    )


def modal_historial_bancario() -> rx.Component:
    """Modal secundario con el historial de cambios bancarios del empleado."""
    return rx.dialog.root(
        rx.dialog.content(
            rx.hstack(
                rx.vstack(
                    rx.dialog.title("Historial bancario"),
                    rx.text(
                        MisEmpleadosState.detalle_nombre_empleado,
                        color=Colors.TEXT_SECONDARY,
                        font_size=Typography.SIZE_SM,
                    ),
                    spacing="1",
                    align="start",
                ),
                rx.button(
                    rx.icon("x", size=16),
                    variant="ghost",
                    color_scheme="gray",
                    size="1",
                    on_click=MisEmpleadosState.cerrar_modal_historial_bancario,
                ),
                align="start",
                justify="between",
                width="100%",
            ),
            rx.cond(
                MisEmpleadosState.tiene_historial_bancario,
                rx.box(
                    rx.vstack(
                        rx.foreach(
                            MisEmpleadosState.historial_bancario,
                            _tarjeta_historial_bancario,
                        ),
                        spacing="3",
                        width="100%",
                    ),
                    max_height="420px",
                    overflow_y="auto",
                    width="100%",
                    padding_right="2",
                ),
                rx.center(
                    rx.text(
                        "No hay cambios bancarios registrados para este empleado.",
                        color=Colors.TEXT_SECONDARY,
                        font_size=Typography.SIZE_SM,
                    ),
                    min_height="220px",
                    width="100%",
                ),
            ),
            rx.hstack(
                rx.spacer(),
                rx.button(
                    "Cerrar",
                    variant="soft",
                    color_scheme="gray",
                    on_click=MisEmpleadosState.cerrar_modal_historial_bancario,
                ),
                width="100%",
                margin_top="4",
            ),
            max_width="760px",
            padding="6",
        ),
        open=MisEmpleadosState.mostrar_modal_historial_bancario,
        on_open_change=rx.noop,
    )


# =============================================================================
# CAMPOS DEL FORMULARIO
# =============================================================================

def _seccion_detalle(
    titulo: str,
    icono: str,
    *contenido: rx.Component,
    action: rx.Component | None = None,
) -> rx.Component:
    """Caja reutilizable para las secciones del modal de detalle."""
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.hstack(
                    rx.icon(icono, size=16, color=Colors.PORTAL_PRIMARY),
                    rx.text(
                        titulo,
                        font_size=Typography.SIZE_SM,
                        font_weight=Typography.WEIGHT_BOLD,
                        color=Colors.TEXT_PRIMARY,
                    ),
                    spacing="2",
                    align="center",
                ),
                rx.spacer(),
                action if action is not None else rx.fragment(),
                align="center",
                width="100%",
            ),
            rx.separator(),
            *contenido,
            spacing="3",
            width="100%",
        ),
        width="100%",
        background=Colors.SURFACE_HOVER,
        border=f"1px solid {Colors.BORDER}",
        border_radius=Radius.LG,
        padding=Spacing.BASE,
    )


def _campo_detalle(
    etiqueta: str,
    valor,
    *,
    fallback: str = "No registrado",
    ancho_completo: bool = False,
) -> rx.Component:
    """Par label/valor para secciones del modal."""
    return rx.box(
        rx.vstack(
            rx.text(
                etiqueta,
                font_size=Typography.SIZE_XS,
                color=Colors.TEXT_SECONDARY,
                text_transform="uppercase",
                letter_spacing="0.04em",
            ),
            rx.cond(
                valor != "",
                rx.text(
                    valor,
                    font_size=Typography.SIZE_SM,
                    color=Colors.TEXT_PRIMARY,
                    white_space="pre-wrap",
                ),
                rx.text(
                    fallback,
                    font_size=Typography.SIZE_SM,
                    color=Colors.TEXT_SECONDARY,
                ),
            ),
            spacing="1",
            align="start",
            width="100%",
        ),
        width="100%",
        grid_column="1 / -1" if ancho_completo else "auto",
    )


def _tarjeta_historial_bancario(registro: dict) -> rx.Component:
    """Tarjeta compacta por movimiento del historial bancario."""
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.vstack(
                    rx.text(
                        registro.get("fecha_cambio", ""),
                        font_size=Typography.SIZE_SM,
                        font_weight=Typography.WEIGHT_BOLD,
                        color=Colors.TEXT_PRIMARY,
                    ),
                    rx.text(
                        registro.get("origen", ""),
                        font_size=Typography.SIZE_BASE,
                        color=Colors.TEXT_SECONDARY,
                    ),
                    spacing="1",
                    align="start",
                ),
                rx.spacer(),
                rx.cond(
                    registro.get("tiene_soporte", False),
                    rx.badge(
                        "Con soporte",
                        variant="soft",
                        color_scheme="green",
                        size="2",
                    ),
                    rx.badge(
                        "Sin soporte",
                        variant="soft",
                        color_scheme="gray",
                        size="2",
                    ),
                ),
                align="start",
                width="100%",
            ),
            rx.grid(
                _campo_detalle("Banco", registro.get("banco", "")),
                _campo_detalle("Cuenta", registro.get("cuenta_bancaria", "")),
                _campo_detalle("CLABE", registro.get("clabe_interbancaria", "")),
                columns=rx.breakpoints(initial="1", sm="2"),
                spacing="4",
                width="100%",
            ),
            spacing="3",
            width="100%",
        ),
        width="100%",
        background=Colors.SURFACE,
        border=f"1px solid {Colors.BORDER}",
        border_radius=Radius.LG,
        padding=Spacing.BASE,
    )

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
    """Campos fecha de nacimiento y género."""
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
        genero_label="Género",
    )


def _campos_telefono_email() -> rx.Component:
    """Campos teléfono y email."""
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
    """Campo dirección."""
    return employee_address_field(
        value=MisEmpleadosState.form_direccion,
        on_change=MisEmpleadosState.set_form_direccion,
        placeholder="Dirección completa",
        label="Dirección",
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


def _seccion_datos_bancarios() -> rx.Component:
    """Sección de datos bancarios."""
    return employee_bank_data_section(
        cuenta_value=MisEmpleadosState.form_cuenta_bancaria,
        cuenta_on_change=MisEmpleadosState.set_form_cuenta_bancaria,
        cuenta_on_blur=MisEmpleadosState.validar_cuenta_bancaria_blur,
        cuenta_error=MisEmpleadosState.error_cuenta_bancaria,
        banco_value=MisEmpleadosState.form_banco,
        banco_on_change=MisEmpleadosState.set_form_banco,
        banco_on_blur=MisEmpleadosState.validar_banco_blur,
        banco_error=MisEmpleadosState.error_banco,
        clabe_value=MisEmpleadosState.form_clabe,
        clabe_on_change=MisEmpleadosState.set_form_clabe,
        clabe_on_blur=MisEmpleadosState.validar_clabe_blur,
        clabe_error=MisEmpleadosState.error_clabe,
        disabled=MisEmpleadosState.datos_bancarios_bloqueados,
        header_action=rx.cond(
            MisEmpleadosState.mostrar_accion_editar_datos_bancarios,
            rx.button(
                MisEmpleadosState.texto_accion_datos_bancarios,
                variant="soft",
                color_scheme="teal",
                size="2",
                on_click=MisEmpleadosState.habilitar_edicion_datos_bancarios,
            ),
            rx.fragment(),
        ),
        helper_text=rx.cond(
            MisEmpleadosState.descripcion_datos_bancarios != "",
            rx.text(
                MisEmpleadosState.descripcion_datos_bancarios,
                font_size=Typography.SIZE_XS,
                color=Colors.TEXT_SECONDARY,
            ),
            rx.fragment(),
        ),
    )


def _campo_notas() -> rx.Component:
    """Campo notas."""
    return employee_notes_field(
        value=MisEmpleadosState.form_notas,
        on_change=MisEmpleadosState.set_form_notas,
        placeholder="Observaciones adicionales",
    )
