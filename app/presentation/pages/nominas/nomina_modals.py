"""
Modales del módulo de Nóminas (vista RRHH).

- Modal crear período
- Modal descuentos manuales por empleado
- Dialogs de confirmación (iniciar preparación, enviar a Contabilidad)
"""
import reflex as rx

from app.presentation.pages.nominas.nomina_rrhh_state import NominaRRHHState
from app.presentation.components.ui import (
    form_input,
    form_select,
    form_date,
    boton_guardar,
    boton_cancelar,
    feedback_callout,
)
from app.presentation.theme import Colors, Spacing, Typography, Radius


# =============================================================================
# MODAL — CREAR PERÍODO
# =============================================================================

def modal_crear_periodo() -> rx.Component:
    """Modal para crear un nuevo período de nómina."""
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title("Nueva nómina"),
            rx.dialog.description(
                NominaRRHHState.descripcion_modal_periodo,
                margin_bottom="16px",
            ),
            rx.cond(
                NominaRRHHState.mensaje_info != "",
                feedback_callout(
                    NominaRRHHState.mensaje_info,
                    NominaRRHHState.tipo_mensaje,
                    margin_bottom="16px",
                ),
                rx.fragment(),
            ),
            rx.vstack(
                form_select(
                    label="Tipo de corrida",
                    required=True,
                    placeholder="Selecciona el tipo de corrida",
                    value=NominaRRHHState.form_tipo_corrida,
                    on_change=NominaRRHHState.set_form_tipo_corrida,
                    options=NominaRRHHState.opciones_tipo_corrida,
                    error=NominaRRHHState.error_tipo_corrida,
                ),
                rx.cond(
                    ~NominaRRHHState.es_form_aguinaldo,
                    form_select(
                        label="Contrato base de nomina",
                        required=True,
                        placeholder="Selecciona un contrato activo con personal",
                        value=NominaRRHHState.form_contrato_nomina_id,
                        on_change=NominaRRHHState.set_form_contrato_nomina_id,
                        options=NominaRRHHState.contratos_nomina_opciones,
                        error=NominaRRHHState.error_contrato_nomina,
                        hint="Solo se muestran contratos activos con personal habilitado.",
                    ),
                    rx.fragment(),
                ),
                rx.cond(
                    NominaRRHHState.es_form_aguinaldo,
                    form_select(
                        label="Ejercicio fiscal",
                        required=True,
                        placeholder="Selecciona un ejercicio fiscal",
                        value=NominaRRHHState.form_ejercicio_fiscal,
                        on_change=NominaRRHHState.set_form_ejercicio_fiscal,
                        options=NominaRRHHState.ejercicios_aguinaldo_catalogo,
                        error=NominaRRHHState.error_ejercicio_fiscal,
                        hint="Se genera una sola corrida anual de aguinaldo por empresa y ejercicio.",
                    ),
                    form_select(
                        label="Período",
                        required=True,
                        placeholder="Selecciona un período",
                        value=NominaRRHHState.form_periodo_key,
                        on_change=NominaRRHHState.set_form_periodo_key,
                        options=NominaRRHHState.periodos_disponibles_catalogo,
                        error=NominaRRHHState.error_periodo,
                        hint="Solo se muestran periodos no creados del mes actual según la política activa.",
                    ),
                ),
                rx.cond(
                    (~NominaRRHHState.es_form_aguinaldo) & ~NominaRRHHState.tiene_contratos_nomina,
                    rx.callout.root(
                        rx.callout.icon(rx.icon("triangle-alert", size=16)),
                        rx.callout.text(
                            "No hay contratos activos con personal disponibles para generar nómina."
                        ),
                        color_scheme="orange",
                        variant="soft",
                        width="100%",
                    ),
                    rx.fragment(),
                ),
                rx.cond(
                    (~NominaRRHHState.es_form_aguinaldo) & ~NominaRRHHState.tiene_periodos_disponibles,
                    rx.callout.root(
                        rx.callout.icon(rx.icon("calendar-range", size=16)),
                        rx.callout.text(
                            "No hay periodos disponibles para el mes actual o falta configurar la política de nómina."
                        ),
                        color_scheme="gray",
                        variant="soft",
                        width="100%",
                    ),
                    rx.fragment(),
                ),
                rx.cond(
                    NominaRRHHState.es_form_aguinaldo & ~NominaRRHHState.tiene_ejercicios_aguinaldo,
                    rx.callout.root(
                        rx.callout.icon(rx.icon("gift", size=16)),
                        rx.callout.text(
                            "No hay ejercicios disponibles para generar la corrida anual de aguinaldo."
                        ),
                        color_scheme="gray",
                        variant="soft",
                        width="100%",
                    ),
                    rx.fragment(),
                ),
                rx.hstack(
                    form_input(
                        label="Fecha de generación",
                        value=NominaRRHHState.fecha_generacion_preview_fmt,
                        read_only=True,
                    ),
                    form_input(
                        label="Generado por",
                        value=NominaRRHHState.form_generado_por_preview,
                        read_only=True,
                    ),
                    spacing="3",
                    width="100%",
                ),
                form_date(
                    label="Fecha de pago",
                    required=True,
                    value=NominaRRHHState.form_fecha_pago,
                    on_change=NominaRRHHState.set_form_fecha_pago,
                    error=NominaRRHHState.error_fecha_pago,
                    hint="Se autocompleta desde la configuración operativa, pero puedes ajustarla.",
                ),
                spacing="4",
                width="100%",
            ),
            rx.hstack(
                boton_cancelar(on_click=NominaRRHHState.cerrar_modal_periodo),
                boton_guardar(
                    texto="Generar nómina",
                    texto_guardando="Generando...",
                    on_click=NominaRRHHState.crear_periodo,
                    saving=NominaRRHHState.saving,
                    disabled=~NominaRRHHState.puede_generar_periodo,
                ),
                spacing="3",
                justify="end",
                margin_top="4",
                width="100%",
            ),
            max_width="640px",
        ),
        open=NominaRRHHState.mostrar_modal_periodo,
        on_open_change=NominaRRHHState.set_mostrar_modal_periodo,
    )


# =============================================================================
# MODAL — DESCUENTOS EMPLEADO
# =============================================================================

def _fila_descuento(descuento: dict) -> rx.Component:
    """Fila en la lista de descuentos existentes."""
    return rx.box(
        rx.hstack(
            rx.hstack(
                rx.badge(
                    descuento['badge'],
                    color_scheme=descuento['color_scheme'],
                    variant="soft",
                    size="1",
                ),
                rx.vstack(
                    rx.text(
                        descuento['concepto_nombre'],
                        size="2",
                        color=Colors.TEXT_PRIMARY,
                        weight="medium",
                    ),
                    rx.text(
                        descuento['origen_label'],
                        size="1",
                        color=Colors.TEXT_SECONDARY,
                    ),
                    spacing="0",
                    align="start",
                ),
                spacing="2",
                align="center",
                flex="1",
                min_width="0",
            ),
            rx.hstack(
                rx.vstack(
                    rx.text(
                        "Monto",
                        size="1",
                        color=Colors.TEXT_MUTED,
                        width="100%",
                        text_align="right",
                    ),
                    rx.text(
                        descuento['monto_fmt'],
                        size="2",
                        weight="bold",
                        color=Colors.TEXT_PRIMARY,
                        width="100%",
                        text_align="right",
                    ),
                    spacing="0",
                    align="end",
                    min_width="120px",
                ),
                rx.cond(
                    NominaRRHHState.puede_editar_descuentos,
                    rx.icon_button(
                        rx.icon("trash-2", size=14),
                        size="1",
                        variant="soft",
                        color_scheme="red",
                        on_click=NominaRRHHState.eliminar_descuento(descuento['id']),
                    ),
                    rx.fragment(),
                ),
                spacing="3",
                align="center",
            ),
            width="100%",
            align="center",
            spacing="3",
        ),
        width="100%",
        padding=Spacing.MD,
        background=Colors.SURFACE,
        border=f"1px solid {Colors.BORDER}",
        border_radius=Radius.MD,
    )


def modal_descuentos_empleado() -> rx.Component:
    """Modal para agregar/ver descuentos manuales de RRHH de un empleado."""
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title(
                rx.hstack(
                    rx.icon("circle-minus", size=18, color=Colors.WARNING),
                    rx.text("Descuentos — "),
                    rx.text(
                        NominaRRHHState.nombre_empleado_seleccionado,
                        color=Colors.PRIMARY,
                    ),
                    spacing="2",
                    align="center",
                ),
            ),
            rx.vstack(
                # --- Descuentos existentes ---
                rx.cond(
                    NominaRRHHState.descuentos_empleado,
                    rx.vstack(
                        rx.hstack(
                            rx.text(
                                "Descuentos aplicados",
                                size="2",
                                weight="medium",
                                color=Colors.TEXT_SECONDARY,
                            ),
                            rx.spacer(),
                            rx.badge(
                                NominaRRHHState.descuentos_empleado.length().to(str),
                                variant="soft",
                                color_scheme="gray",
                                size="1",
                            ),
                            width="100%",
                            align="center",
                        ),
                        rx.box(
                            rx.vstack(
                                rx.foreach(
                                    NominaRRHHState.descuentos_empleado,
                                    _fila_descuento,
                                ),
                                width="100%",
                                spacing="2",
                            ),
                            width="100%",
                            max_height="240px",
                            overflow_y="auto",
                            padding=Spacing.SM,
                            background=Colors.SECONDARY_LIGHT,
                            border=f"1px solid {Colors.BORDER}",
                            border_radius=Radius.LG,
                        ),
                        width="100%",
                        spacing="2",
                    ),
                    feedback_callout(
                        "Sin descuentos aplicados aún.",
                        "info",
                        width="100%",
                    ),
                ),
                # --- Formulario (solo si está en preparación) ---
                rx.cond(
                    NominaRRHHState.puede_editar_descuentos,
                    rx.vstack(
                        rx.separator(width="100%"),
                        rx.text(
                            "Agregar descuento",
                            size="2",
                            weight="medium",
                            color=Colors.TEXT_SECONDARY,
                        ),
                        form_select(
                            label="Tipo de descuento",
                            required=True,
                            placeholder="Selecciona un descuento disponible",
                            value=NominaRRHHState.form_concepto_clave,
                            on_change=NominaRRHHState.set_form_concepto_clave,
                            options=NominaRRHHState.opciones_conceptos_rrhh,
                            disabled=~NominaRRHHState.tiene_opciones_conceptos_rrhh,
                        ),
                        form_input(
                            label="Monto",
                            required=True,
                            placeholder="Ej: $ 1,500.00",
                            value=NominaRRHHState.form_monto_descuento,
                            on_change=NominaRRHHState.set_form_monto_descuento,
                            disabled=~NominaRRHHState.tiene_opciones_conceptos_rrhh,
                            error=NominaRRHHState.error_monto,
                        ),
                        form_input(
                            label="Notas (opcional)",
                            placeholder="Ej: Crédito 12345678",
                            value=NominaRRHHState.form_notas_descuento,
                            on_change=NominaRRHHState.set_form_notas_descuento,
                            disabled=~NominaRRHHState.tiene_opciones_conceptos_rrhh,
                        ),
                        rx.cond(
                            ~NominaRRHHState.tiene_opciones_conceptos_rrhh,
                            feedback_callout(
                                "Todos los descuentos disponibles ya están aplicados en este período.",
                                "warning",
                                width="100%",
                            ),
                            rx.fragment(),
                        ),
                        width="100%",
                        spacing="3",
                    ),
                    rx.cond(
                        NominaRRHHState.periodo_enviado,
                        rx.callout(
                            "El período fue enviado a Contabilidad. "
                            "No se pueden modificar los descuentos.",
                            icon="lock",
                            color_scheme="gray",
                            size="1",
                        ),
                        rx.fragment(),
                    ),
                ),
                spacing="4",
                width="100%",
            ),
            rx.hstack(
                boton_cancelar(
                    texto="Cerrar",
                    on_click=NominaRRHHState.cerrar_modal_descuento,
                ),
                rx.spacer(),
                rx.cond(
                    NominaRRHHState.puede_editar_descuentos,
                    boton_guardar(
                        texto="Añadir",
                        texto_guardando="Añadiendo...",
                        on_click=NominaRRHHState.guardar_descuento,
                        saving=NominaRRHHState.saving,
                        disabled=~NominaRRHHState.puede_anadir_descuento,
                        color_scheme="orange",
                        size="2",
                    ),
                    rx.fragment(),
                ),
                width="100%",
                align="center",
                spacing="3",
                margin_top=Spacing.BASE,
            ),
            max_width="480px",
        ),
        open=NominaRRHHState.mostrar_modal_descuento,
        on_open_change=rx.noop,
    )


# =============================================================================
# DIALOG — INICIAR PREPARACIÓN
# =============================================================================

def dialog_iniciar_preparacion() -> rx.Component:
    """Confirmación para iniciar preparación (BORRADOR → EN_PREPARACION_RRHH)."""
    return rx.alert_dialog.root(
        rx.alert_dialog.content(
            rx.alert_dialog.title("Iniciar preparación de nómina"),
            rx.alert_dialog.description(
                "Al iniciar la preparación podrás capturar descuentos manuales "
                "para cada empleado. El período pasará a estado 'En preparación'.",
            ),
            rx.hstack(
                rx.alert_dialog.cancel(
                    rx.button(
                        "Cancelar",
                        variant="soft",
                        color_scheme="gray",
                        on_click=NominaRRHHState.cerrar_dialog_iniciar,
                    ),
                ),
                rx.alert_dialog.action(
                    rx.button(
                        "Iniciar preparación",
                        on_click=NominaRRHHState.iniciar_preparacion,
                        loading=NominaRRHHState.saving,
                        color_scheme="blue",
                    ),
                ),
                spacing="3",
                justify="end",
                margin_top="4",
            ),
            max_width="420px",
        ),
        open=NominaRRHHState.mostrar_dialog_iniciar,
    )


# =============================================================================
# DIALOG — ENVIAR A CONTABILIDAD
# =============================================================================

def dialog_enviar_contabilidad() -> rx.Component:
    """Confirmación para enviar a Contabilidad. Acción irreversible para RRHH."""
    return rx.alert_dialog.root(
        rx.alert_dialog.content(
            rx.alert_dialog.title("Enviar a Contabilidad"),
            rx.alert_dialog.description(
                rx.vstack(
                    rx.text(
                        "¿Confirmas el envío de esta nómina a Contabilidad?",
                    ),
                    rx.callout(
                        "Una vez enviada, RRHH no podrá modificar los descuentos. "
                        "Asegúrate de haber capturado INFONAVIT, FONACOT y préstamos.",
                        icon="triangle-alert",
                        color_scheme="orange",
                        size="1",
                    ),
                    spacing="3",
                ),
            ),
            rx.hstack(
                rx.alert_dialog.cancel(
                    rx.button(
                        "Cancelar",
                        variant="soft",
                        color_scheme="gray",
                        on_click=NominaRRHHState.cerrar_dialog_envio,
                    ),
                ),
                rx.alert_dialog.action(
                    rx.button(
                        rx.icon("send", size=14),
                        "Enviar a Contabilidad",
                        on_click=NominaRRHHState.enviar_a_contabilidad,
                        loading=NominaRRHHState.saving,
                        color_scheme="orange",
                    ),
                ),
                spacing="3",
                justify="end",
                margin_top="4",
            ),
            max_width="440px",
        ),
        open=NominaRRHHState.mostrar_dialog_envio,
    )
