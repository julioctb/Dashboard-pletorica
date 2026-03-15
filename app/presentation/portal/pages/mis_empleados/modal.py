"""
Modal para crear/editar empleados en el portal.
"""
import reflex as rx

from app.presentation.theme import Colors, Radius, Spacing, Typography
from app.presentation.components.ui import (
    employee_status_badge,
    form_date,
    form_input,
    modal_formulario,
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
    employee_date_field,
    employee_emergency_contact_section,
    employee_name_fields_section,
    employee_notes_field,
    employee_phone_email_row,
    employee_recurring_discount_card,
    employee_recurring_discounts_section,
    employee_rfc_nss_row,
)

from .state import MisEmpleadosState
from ..expedientes.state import ExpedientesState


def modal_empleado() -> rx.Component:
    """Modal para crear o editar un empleado."""
    return employee_form_modal(
        open_state=MisEmpleadosState.mostrar_modal_empleado,
        title=rx.cond(
            MisEmpleadosState.es_edicion,
            "Editar empleado",
            "Nuevo empleado",
        ),
        description=rx.text(
            rx.cond(
                MisEmpleadosState.es_edicion,
                "Asignado a ",
                "Se asignará a ",
            ),
            rx.text(
                MisEmpleadosState.nombre_empresa_actual,
                as_="span",
                font_weight=Typography.WEIGHT_MEDIUM,
                color=Colors.SECONDARY,
            ),
            font_size=Typography.SIZE_SM,
            color=Colors.TEXT_SECONDARY,
        ),
        body=rx.vstack(
            _employee_modal_identificacion_section(),
            _employee_modal_contacto_section(),
            _employee_modal_contacto_emergencia_section(),
            _employee_modal_datos_bancarios_section(),
            _employee_modal_descuentos_section(),
            _employee_modal_notas_field(),
            gap=Spacing.MD,
            width="100%",
            align="stretch",
        ),
        on_cancel=MisEmpleadosState.cerrar_modal_empleado,
        on_save=MisEmpleadosState.guardar_empleado,
        save_text=rx.cond(
            MisEmpleadosState.es_edicion,
            "Guardar cambios",
            "Crear empleado",
        ),
        saving=MisEmpleadosState.saving,
        save_loading_text="Guardando...",
        save_color_scheme="teal",
        max_width="920px",
    )


def _employee_modal_section(
    title: str,
    *children,
    description: rx.Component | None = None,
    header_action: rx.Component | None = None,
) -> rx.Component:
    """Contenedor visual de sección para el modal de empleado."""
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.vstack(
                    rx.text(
                        title,
                        font_size=Typography.SIZE_SM,
                        font_weight=Typography.WEIGHT_MEDIUM,
                        color=Colors.TEXT_PRIMARY,
                    ),
                    description if description is not None else rx.fragment(),
                    spacing="1",
                    align="start",
                ),
                rx.spacer(),
                header_action if header_action is not None else rx.fragment(),
                width="100%",
                align="center",
            ),
            *children,
            width="100%",
            gap=Spacing.MD,
            align="stretch",
        ),
        width="100%",
        padding=Spacing.MD,
        background=Colors.SURFACE,
        border=f"1px solid {Colors.BORDER}",
        border_radius=Radius.LG,
    )


def _employee_modal_three_col_grid(*children) -> rx.Component:
    """Grid responsivo de tres columnas para grupos de campos."""
    return rx.grid(
        *children,
        columns=rx.breakpoints(initial="1", sm="2", md="3"),
        gap=Spacing.MD,
        width="100%",
    )


def _employee_modal_two_col_grid(*children) -> rx.Component:
    """Grid responsivo de dos columnas para grupos de campos."""
    return rx.grid(
        *children,
        columns=rx.breakpoints(initial="1", sm="2"),
        gap=Spacing.MD,
        width="100%",
    )


def _employee_modal_input(
    *,
    label: str,
    value,
    on_change,
    placeholder: str = "",
    error=None,
    on_blur=None,
    required: bool = False,
    max_length: int | None = None,
    disabled=False,
    hint: str = "",
) -> rx.Component:
    """Input del modal con labels estilo wizard."""
    return form_input(
        label=label,
        label_variant="wizard",
        value=value,
        on_change=on_change,
        on_blur=on_blur,
        placeholder=placeholder,
        error=error,
        required=required,
        max_length=max_length,
        disabled=disabled,
        hint=hint,
    )


def _employee_modal_date(
    *,
    label: str,
    value,
    on_change,
    error=None,
    on_blur=None,
    required: bool = False,
    hint: str = "",
) -> rx.Component:
    """Campo de fecha del modal con labels estilo wizard."""
    return form_date(
        label=label,
        label_variant="wizard",
        value=value,
        on_change=on_change,
        on_blur=on_blur,
        error=error,
        required=required,
        hint=hint,
    )


def _employee_modal_select(
    *,
    label: str,
    value,
    on_change,
    options,
    placeholder: str = "Seleccionar...",
    error=None,
    required: bool = False,
    disabled=False,
    hint: str = "",
) -> rx.Component:
    """Select del modal con labels estilo wizard."""
    return form_select(
        label=label,
        label_variant="wizard",
        value=value,
        on_change=on_change,
        options=options,
        placeholder=placeholder,
        error=error,
        required=required,
        disabled=disabled,
        hint=hint,
    )


def _employee_modal_identificacion_section() -> rx.Component:
    """Sección visual de identificación."""
    return _employee_modal_section(
        "Identificación",
        _employee_modal_three_col_grid(
            _employee_modal_input(
                label="CURP",
                value=MisEmpleadosState.form_curp,
                on_change=MisEmpleadosState.set_form_curp,
                on_blur=MisEmpleadosState.validar_curp_blur,
                error=MisEmpleadosState.error_curp,
                required=True,
                placeholder="18 caracteres",
                max_length=18,
                disabled=MisEmpleadosState.es_edicion,
            ),
            _employee_modal_input(
                label="RFC",
                value=MisEmpleadosState.form_rfc,
                on_change=MisEmpleadosState.set_form_rfc,
                on_blur=MisEmpleadosState.validar_rfc_blur,
                error=MisEmpleadosState.error_rfc,
                required=True,
                placeholder="13 caracteres",
                max_length=13,
            ),
            _employee_modal_input(
                label="NSS",
                value=MisEmpleadosState.form_nss,
                on_change=MisEmpleadosState.set_form_nss,
                on_blur=MisEmpleadosState.validar_nss_blur,
                error=MisEmpleadosState.error_nss,
                required=True,
                placeholder="11 dígitos",
                max_length=11,
            ),
        ),
        _employee_modal_three_col_grid(
            _employee_modal_input(
                label="Nombre",
                value=MisEmpleadosState.form_nombre,
                on_change=MisEmpleadosState.set_form_nombre,
                on_blur=MisEmpleadosState.validar_nombre_blur,
                error=MisEmpleadosState.error_nombre,
                required=True,
                placeholder="Nombre(s)",
            ),
            _employee_modal_input(
                label="Ap. paterno",
                value=MisEmpleadosState.form_apellido_paterno,
                on_change=MisEmpleadosState.set_form_apellido_paterno,
                on_blur=MisEmpleadosState.validar_apellido_paterno_blur,
                error=MisEmpleadosState.error_apellido_paterno,
                required=True,
                placeholder="Apellido paterno",
            ),
            _employee_modal_input(
                label="Ap. materno",
                value=MisEmpleadosState.form_apellido_materno,
                on_change=MisEmpleadosState.set_form_apellido_materno,
                on_blur=MisEmpleadosState.validar_apellido_materno_blur,
                error=MisEmpleadosState.error_apellido_materno,
                required=True,
                placeholder="Apellido materno",
            ),
        ),
        _employee_modal_three_col_grid(
            _employee_modal_date(
                label="Fecha de nacimiento",
                value=MisEmpleadosState.form_fecha_nacimiento,
                on_change=MisEmpleadosState.set_form_fecha_nacimiento,
                on_blur=MisEmpleadosState.validar_fecha_nacimiento_blur,
                error=MisEmpleadosState.error_fecha_nacimiento,
                required=True,
            ),
            _employee_modal_select(
                label="Género",
                value=MisEmpleadosState.form_genero,
                on_change=MisEmpleadosState.set_form_genero,
                options=MisEmpleadosState.opciones_genero,
                error=MisEmpleadosState.error_genero,
                required=True,
            ),
            _employee_modal_date(
                label="Fecha de ingreso",
                value=MisEmpleadosState.form_fecha_ingreso,
                on_change=MisEmpleadosState.set_form_fecha_ingreso,
                on_blur=MisEmpleadosState.validar_fecha_ingreso_blur,
                error=MisEmpleadosState.error_fecha_ingreso,
                required=True,
            ),
        ),
    )


def _employee_modal_contacto_section() -> rx.Component:
    """Sección visual de contacto."""
    return _employee_modal_section(
        "Contacto",
        _employee_modal_two_col_grid(
            _employee_modal_input(
                label="Teléfono",
                value=MisEmpleadosState.form_telefono,
                on_change=MisEmpleadosState.set_form_telefono,
                on_blur=MisEmpleadosState.validar_telefono_blur,
                error=MisEmpleadosState.error_telefono,
                required=True,
                placeholder="10 dígitos",
                max_length=15,
            ),
            _employee_modal_input(
                label="Email",
                value=MisEmpleadosState.form_email,
                on_change=MisEmpleadosState.set_form_email,
                on_blur=MisEmpleadosState.validar_email_blur,
                error=MisEmpleadosState.error_email,
                placeholder="correo@ejemplo.com",
            ),
        ),
        _employee_modal_input(
            label="Dirección",
            value=MisEmpleadosState.form_direccion,
            on_change=MisEmpleadosState.set_form_direccion,
            placeholder="Dirección completa",
        ),
    )


def _employee_modal_contacto_emergencia_section() -> rx.Component:
    """Sección visual de contacto de emergencia."""
    return _employee_modal_section(
        "Contacto de emergencia",
        _employee_modal_three_col_grid(
            _employee_modal_input(
                label="Nombre",
                value=MisEmpleadosState.form_contacto_nombre,
                on_change=MisEmpleadosState.set_form_contacto_nombre,
                on_blur=MisEmpleadosState.validar_contacto_nombre_blur,
                error=MisEmpleadosState.error_contacto_nombre,
                placeholder="Nombre completo",
            ),
            _employee_modal_input(
                label="Teléfono",
                value=MisEmpleadosState.form_contacto_telefono,
                on_change=MisEmpleadosState.set_form_contacto_telefono,
                on_blur=MisEmpleadosState.validar_contacto_telefono_blur,
                error=MisEmpleadosState.error_contacto_telefono,
                placeholder="10 dígitos",
                max_length=15,
            ),
            _employee_modal_select(
                label="Parentesco",
                value=MisEmpleadosState.form_contacto_parentesco,
                on_change=MisEmpleadosState.set_form_contacto_parentesco,
                options=MisEmpleadosState.opciones_parentesco,
                error=MisEmpleadosState.error_contacto_parentesco,
            ),
        ),
    )


def _employee_modal_datos_bancarios_section() -> rx.Component:
    """Sección visual de datos bancarios."""
    return _employee_modal_section(
        "Datos bancarios",
        _employee_modal_three_col_grid(
            _employee_modal_select(
                label="Banco",
                value=MisEmpleadosState.form_banco,
                on_change=MisEmpleadosState.set_form_banco,
                options=MisEmpleadosState.opciones_banco_empleado,
                error=MisEmpleadosState.error_banco,
                placeholder="Seleccionar banco",
                disabled=MisEmpleadosState.datos_bancarios_bloqueados,
            ),
            _employee_modal_input(
                label="No. de cuenta",
                value=MisEmpleadosState.form_cuenta_bancaria,
                on_change=MisEmpleadosState.set_form_cuenta_bancaria,
                on_blur=MisEmpleadosState.validar_cuenta_bancaria_blur,
                error=MisEmpleadosState.error_cuenta_bancaria,
                placeholder="10-18 dígitos",
                max_length=18,
                disabled=MisEmpleadosState.datos_bancarios_bloqueados,
            ),
            _employee_modal_input(
                label="CLABE interbancaria",
                value=MisEmpleadosState.form_clabe,
                on_change=MisEmpleadosState.set_form_clabe,
                on_blur=MisEmpleadosState.validar_clabe_blur,
                error=MisEmpleadosState.error_clabe,
                placeholder="18 dígitos",
                max_length=18,
                disabled=MisEmpleadosState.datos_bancarios_bloqueados,
            ),
        ),
        description=rx.cond(
            MisEmpleadosState.descripcion_datos_bancarios != "",
            rx.text(
                MisEmpleadosState.descripcion_datos_bancarios,
                font_size=Typography.SIZE_XS,
                color=Colors.TEXT_SECONDARY,
            ),
            rx.fragment(),
        ),
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
    )


def _employee_modal_descuento_row(
    *,
    form_key: str,
    title: str,
    badge_text: str,
    badge_color_scheme: str,
    active,
    amount_value,
    start_value,
    end_value,
    notes_value,
    is_last: bool = False,
) -> rx.Component:
    """Fila colapsable para un descuento recurrente."""
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.switch(
                    checked=active,
                    on_change=lambda value: MisEmpleadosState.set_form_descuento_activo(form_key, value),
                ),
                rx.badge(
                    badge_text,
                    color_scheme=badge_color_scheme,
                    variant="soft",
                    size="1",
                ),
                rx.text(
                    title,
                    font_size=Typography.SIZE_SM,
                    font_weight=Typography.WEIGHT_MEDIUM,
                    color=Colors.TEXT_PRIMARY,
                ),
                rx.spacer(),
                rx.text(
                    rx.cond(active, "Activo", "Inactivo"),
                    font_size=Typography.SIZE_XS,
                    font_weight=Typography.WEIGHT_MEDIUM,
                    color=rx.cond(active, Colors.PORTAL_PRIMARY_TEXT, Colors.TEXT_MUTED),
                ),
                width="100%",
                align="center",
                spacing="3",
            ),
            rx.cond(
                active,
                rx.vstack(
                    _employee_modal_three_col_grid(
                        _employee_modal_input(
                            label="Monto por período",
                            value=amount_value,
                            on_change=lambda value: MisEmpleadosState.set_form_descuento_monto(form_key, value),
                            placeholder="Ej: 1500.00",
                            required=True,
                        ),
                        _employee_modal_date(
                            label="Fecha inicio",
                            value=start_value,
                            on_change=lambda value: MisEmpleadosState.set_form_descuento_inicio(form_key, value),
                            required=True,
                        ),
                        _employee_modal_date(
                            label="Fecha fin",
                            value=end_value,
                            on_change=lambda value: MisEmpleadosState.set_form_descuento_fin(form_key, value),
                            hint="Vacía = indefinido",
                        ),
                    ),
                    _employee_modal_input(
                        label="Notas",
                        value=notes_value,
                        on_change=lambda value: MisEmpleadosState.set_form_descuento_notas(form_key, value),
                        placeholder="Referencia o detalles opcionales",
                    ),
                    width="100%",
                    gap=Spacing.MD,
                    padding_top=Spacing.SM,
                    align="stretch",
                ),
                rx.fragment(),
            ),
            width="100%",
            gap=Spacing.SM,
            align="stretch",
        ),
        width="100%",
        padding_y=Spacing.MD,
        border_bottom="none" if is_last else f"1px solid {Colors.BORDER}",
    )


def _employee_modal_descuentos_section() -> rx.Component:
    """Sección visual de descuentos recurrentes."""
    return _employee_modal_section(
        "Descuentos recurrentes",
        rx.cond(
            MisEmpleadosState.error_descuentos_recurrentes != "",
            rx.text(
                MisEmpleadosState.error_descuentos_recurrentes,
                font_size=Typography.SIZE_XS,
                color=Colors.ERROR,
            ),
            rx.fragment(),
        ),
        rx.box(
            _employee_modal_descuento_row(
                form_key="infonavit",
                title="INFONAVIT",
                badge_text="INF",
                badge_color_scheme="blue",
                active=MisEmpleadosState.form_descuento_infonavit_activo,
                amount_value=MisEmpleadosState.form_descuento_infonavit_monto,
                start_value=MisEmpleadosState.form_descuento_infonavit_inicio,
                end_value=MisEmpleadosState.form_descuento_infonavit_fin,
                notes_value=MisEmpleadosState.form_descuento_infonavit_notas,
            ),
            _employee_modal_descuento_row(
                form_key="fonacot",
                title="FONACOT",
                badge_text="FON",
                badge_color_scheme="orange",
                active=MisEmpleadosState.form_descuento_fonacot_activo,
                amount_value=MisEmpleadosState.form_descuento_fonacot_monto,
                start_value=MisEmpleadosState.form_descuento_fonacot_inicio,
                end_value=MisEmpleadosState.form_descuento_fonacot_fin,
                notes_value=MisEmpleadosState.form_descuento_fonacot_notas,
            ),
            _employee_modal_descuento_row(
                form_key="prestamo_empresa",
                title="Préstamo empresa",
                badge_text="PRE",
                badge_color_scheme="teal",
                active=MisEmpleadosState.form_descuento_prestamo_empresa_activo,
                amount_value=MisEmpleadosState.form_descuento_prestamo_empresa_monto,
                start_value=MisEmpleadosState.form_descuento_prestamo_empresa_inicio,
                end_value=MisEmpleadosState.form_descuento_prestamo_empresa_fin,
                notes_value=MisEmpleadosState.form_descuento_prestamo_empresa_notas,
            ),
            _employee_modal_descuento_row(
                form_key="pension_alimenticia",
                title="Pensión alimenticia",
                badge_text="PEN",
                badge_color_scheme="red",
                active=MisEmpleadosState.form_descuento_pension_alimenticia_activo,
                amount_value=MisEmpleadosState.form_descuento_pension_alimenticia_monto,
                start_value=MisEmpleadosState.form_descuento_pension_alimenticia_inicio,
                end_value=MisEmpleadosState.form_descuento_pension_alimenticia_fin,
                notes_value=MisEmpleadosState.form_descuento_pension_alimenticia_notas,
                is_last=True,
            ),
            width="100%",
            border=f"1px solid {Colors.BORDER}",
            border_radius=Radius.MD,
            padding_x=Spacing.MD,
            background=Colors.SURFACE,
        ),
        description=rx.text(
            "Active solo los que aplican. Fecha fin vacía = indefinido.",
            font_size=Typography.SIZE_XS,
            color=Colors.TEXT_SECONDARY,
        ),
    )


def _employee_modal_notas_field() -> rx.Component:
    """Campo de notas generales fuera de las secciones principales."""
    return _employee_modal_input(
        label="Notas",
        value=MisEmpleadosState.form_notas,
        on_change=MisEmpleadosState.set_form_notas,
        placeholder="Observaciones adicionales",
    )


def modal_asignacion_plaza() -> rx.Component:
    """Modal contextual para asignar o reasignar empleados desde la vista por plaza."""
    return modal_formulario(
        open=MisEmpleadosState.mostrar_modal_asignacion_plaza,
        titulo=MisEmpleadosState.titulo_modal_asignacion_plaza,
        descripcion=MisEmpleadosState.descripcion_modal_asignacion_plaza,
        contenido=rx.vstack(
            rx.callout(
                rx.text(
                    "La plaza conserva su sede y categoría. Aquí solo se asigna o reasigna al empleado.",
                    font_size=Typography.SIZE_SM,
                ),
                icon="briefcase",
                color_scheme="blue",
                size="1",
                width="100%",
            ),
            form_select(
                label="Empleado",
                required=True,
                placeholder=MisEmpleadosState.placeholder_empleado_plaza,
                value=MisEmpleadosState.empleado_seleccionado_plaza_id,
                on_change=MisEmpleadosState.set_empleado_seleccionado_plaza_id,
                options=MisEmpleadosState.opciones_empleados_disponibles_plaza,
                disabled=MisEmpleadosState.cargando_empleados_plaza,
                hint=rx.cond(
                    MisEmpleadosState.tiene_empleados_disponibles_plaza,
                    "",
                    "Si no hay empleados disponibles, primero capture uno nuevo.",
                ),
            ),
            rx.cond(
                MisEmpleadosState.cargando_empleados_plaza,
                rx.hstack(
                    rx.spinner(size="2"),
                    rx.text(
                        "Cargando empleados disponibles...",
                        font_size=Typography.SIZE_SM,
                        color=Colors.TEXT_SECONDARY,
                    ),
                    spacing="2",
                    align="center",
                    width="100%",
                ),
                rx.fragment(),
            ),
            rx.cond(
                ~MisEmpleadosState.tiene_empleados_disponibles_plaza & ~MisEmpleadosState.cargando_empleados_plaza,
                rx.button(
                    rx.icon("plus", size=16),
                    "Nuevo empleado",
                    on_click=[
                        MisEmpleadosState.cerrar_modal_asignacion_plaza,
                        MisEmpleadosState.abrir_modal_crear,
                    ],
                    variant="outline",
                    color_scheme="teal",
                    align_self="start",
                ),
                rx.fragment(),
            ),
            spacing="4",
            width="100%",
        ),
        on_guardar=MisEmpleadosState.confirmar_asignacion_plaza,
        on_cancelar=MisEmpleadosState.cerrar_modal_asignacion_plaza,
        puede_guardar=MisEmpleadosState.puede_confirmar_asignacion_plaza,
        loading=MisEmpleadosState.saving,
        texto_guardar=MisEmpleadosState.texto_guardar_asignacion_plaza,
        texto_guardando=rx.cond(
            MisEmpleadosState.modo_asignacion_plaza == "reasignar",
            "Reasignando...",
            "Asignando...",
        ),
        max_width="460px",
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
                            rx.button(
                                rx.badge(
                                    "Expediente " + MisEmpleadosState.detalle_expediente_resumen,
                                    variant="soft",
                                    color_scheme="teal",
                                    size="2",
                                ),
                                on_click=ExpedientesState.abrir_panel_expediente(
                                    MisEmpleadosState.empleado_detalle
                                ),
                                variant="ghost",
                                padding="0",
                                height="auto",
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
                                "Primer ingreso",
                                MisEmpleadosState.empleado_detalle.get("fecha_ingreso", ""),
                            ),
                            _campo_detalle(
                                "Ingreso vigente",
                                MisEmpleadosState.empleado_detalle.get(
                                    "fecha_ingreso_vigente",
                                    "",
                                ),
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
                    _seccion_descuentos_detalle(),
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


def _badge_descuento_empleado(descuento: dict) -> rx.Component:
    """Badge con tooltip para descuentos configurados."""
    return rx.tooltip(
        rx.badge(
            descuento["badge"],
            color_scheme=descuento["color_scheme"],
            variant="soft",
            size="1",
        ),
        content=descuento["tooltip"],
    )


def _fila_descuento_detalle(descuento: dict) -> rx.Component:
    """Fila de detalle para descuentos recurrentes."""
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.hstack(
                    _badge_descuento_empleado(descuento),
                    rx.text(
                        descuento["concepto_nombre"],
                        font_size=Typography.SIZE_SM,
                        font_weight=Typography.WEIGHT_MEDIUM,
                    ),
                    spacing="2",
                    align="center",
                ),
                rx.spacer(),
                rx.text(
                    descuento["monto_periodico_fmt"],
                    font_size=Typography.SIZE_SM,
                    font_weight=Typography.WEIGHT_MEDIUM,
                ),
                width="100%",
                align="center",
            ),
            rx.text(
                descuento["vigencia"],
                font_size=Typography.SIZE_XS,
                color=Colors.TEXT_SECONDARY,
            ),
            rx.cond(
                descuento["notas"] != "",
                rx.text(
                    descuento["notas"],
                    font_size=Typography.SIZE_XS,
                    color=Colors.TEXT_SECONDARY,
                ),
                rx.fragment(),
            ),
            spacing="1",
            width="100%",
        ),
        width="100%",
        padding_y=Spacing.XS,
        border_bottom=f"1px solid {Colors.BORDER}",
    )


def _seccion_descuentos_detalle() -> rx.Component:
    """Sección de solo lectura para descuentos recurrentes."""
    descuentos_configurados = MisEmpleadosState.empleado_detalle.get(
        "descuentos_configurados",
        [],
    ).to(list[dict])
    descuentos_activos = MisEmpleadosState.empleado_detalle.get(
        "descuentos_activos_hoy",
        [],
    ).to(list[dict])
    return _seccion_detalle(
        "Descuentos recurrentes",
        "circle-minus",
        rx.cond(
            descuentos_configurados.length() > 0,
            rx.vstack(
                rx.hstack(
                    rx.foreach(descuentos_activos, _badge_descuento_empleado),
                    spacing="2",
                    wrap="wrap",
                    width="100%",
                ),
                rx.vstack(
                    rx.foreach(descuentos_configurados, _fila_descuento_detalle),
                    spacing="0",
                    width="100%",
                ),
                spacing="3",
                width="100%",
            ),
            rx.text(
                "No hay descuentos recurrentes configurados.",
                color=Colors.TEXT_SECONDARY,
                font_size=Typography.SIZE_SM,
            ),
        ),
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
