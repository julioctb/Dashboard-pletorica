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
)
from app.presentation.theme import Colors, Spacing, Typography, Radius


# =============================================================================
# MODAL — CREAR PERÍODO
# =============================================================================

def modal_crear_periodo() -> rx.Component:
    """Modal para crear un nuevo período de nómina."""
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title("Nuevo período de nómina"),
            rx.dialog.description(
                "Define el rango de fechas y la periodicidad del período.",
                margin_bottom="16px",
            ),
            rx.cond(
                NominaRRHHState.mensaje_info != "",
                rx.callout(
                    NominaRRHHState.mensaje_info,
                    icon=rx.cond(
                        NominaRRHHState.tipo_mensaje == "error",
                        "triangle-alert",
                        "info",
                    ),
                    color_scheme=rx.cond(
                        NominaRRHHState.tipo_mensaje == "error",
                        "red",
                        "blue",
                    ),
                    size="2",
                    width="100%",
                    role="alert",
                    aria_live="assertive",
                    margin_bottom="16px",
                ),
                rx.fragment(),
            ),
            rx.vstack(
                form_input(
                    label="Nombre del período",
                    required=True,
                    placeholder="Ej: Quincena 1 Marzo 2026",
                    value=NominaRRHHState.form_nombre,
                    on_change=NominaRRHHState.set_form_nombre,
                    error=NominaRRHHState.error_nombre,
                    max_length=100,
                ),
                form_select(
                    label="Periodicidad",
                    required=True,
                    value=NominaRRHHState.form_periodicidad,
                    on_change=NominaRRHHState.set_form_periodicidad,
                    options=NominaRRHHState.opciones_periodicidad,
                ),
                rx.hstack(
                    form_date(
                        label="Fecha de inicio",
                        required=True,
                        value=NominaRRHHState.form_fecha_inicio,
                        on_change=NominaRRHHState.set_form_fecha_inicio,
                        error=NominaRRHHState.error_fecha_inicio,
                    ),
                    form_date(
                        label="Fecha de fin",
                        required=True,
                        value=NominaRRHHState.form_fecha_fin,
                        on_change=NominaRRHHState.set_form_fecha_fin,
                        error=NominaRRHHState.error_fecha_fin,
                    ),
                    spacing="3",
                    width="100%",
                ),
                form_date(
                    label="Fecha de pago (opcional)",
                    value=NominaRRHHState.form_fecha_pago,
                    on_change=NominaRRHHState.set_form_fecha_pago,
                    error=NominaRRHHState.error_fecha_pago,
                ),
                spacing="4",
                width="100%",
            ),
            rx.hstack(
                boton_cancelar(on_click=NominaRRHHState.cerrar_modal_periodo),
                boton_guardar(
                    texto="Crear período",
                    texto_guardando="Creando...",
                    on_click=NominaRRHHState.crear_periodo,
                    saving=NominaRRHHState.saving,
                ),
                spacing="3",
                justify="end",
                margin_top="4",
                width="100%",
            ),
            max_width="480px",
        ),
        open=NominaRRHHState.mostrar_modal_periodo,
        on_open_change=NominaRRHHState.set_mostrar_modal_periodo,
    )


# =============================================================================
# MODAL — DESCUENTOS EMPLEADO
# =============================================================================

def _fila_descuento(descuento: dict) -> rx.Component:
    """Fila en la lista de descuentos existentes."""
    return rx.hstack(
        rx.text(
            descuento['concepto_nombre'],
            size="2",
            color=Colors.TEXT_PRIMARY,
            flex="1",
        ),
        rx.text(
            "$" + descuento['monto'].to(str),
            size="2",
            weight="medium",
            color=Colors.TEXT_PRIMARY,
            min_width="80px",
            text_align="right",
        ),
        rx.cond(
            NominaRRHHState.puede_editar_descuentos,
            rx.icon_button(
                rx.icon("trash-2", size=14),
                size="1",
                variant="ghost",
                color_scheme="red",
                on_click=NominaRRHHState.eliminar_descuento(descuento['id']),
            ),
            rx.fragment(),
        ),
        width="100%",
        align="center",
        padding_y=Spacing.XS,
        border_bottom=f"1px solid {Colors.BORDER}",
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
                        rx.text(
                            "Descuentos aplicados",
                            size="2",
                            weight="medium",
                            color=Colors.TEXT_SECONDARY,
                        ),
                        rx.vstack(
                            rx.foreach(
                                NominaRRHHState.descuentos_empleado,
                                _fila_descuento,
                            ),
                            width="100%",
                            spacing="0",
                        ),
                        width="100%",
                        spacing="2",
                    ),
                    rx.text(
                        "Sin descuentos aplicados aún.",
                        size="2",
                        color=Colors.TEXT_MUTED,
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
                            value=NominaRRHHState.form_concepto_clave,
                            on_change=NominaRRHHState.set_form_concepto_clave,
                            options=NominaRRHHState.opciones_conceptos_rrhh,
                        ),
                        form_input(
                            label="Monto",
                            required=True,
                            placeholder="Ej: 1500.00",
                            value=NominaRRHHState.form_monto_descuento,
                            on_change=NominaRRHHState.set_form_monto_descuento,
                            error=NominaRRHHState.error_monto,
                        ),
                        form_input(
                            label="Notas (opcional)",
                            placeholder="Ej: Crédito 12345678",
                            value=NominaRRHHState.form_notas_descuento,
                            on_change=NominaRRHHState.set_form_notas_descuento,
                        ),
                        rx.hstack(
                            rx.button(
                                rx.icon("plus", size=14),
                                "Agregar descuento",
                                on_click=NominaRRHHState.guardar_descuento,
                                loading=NominaRRHHState.saving,
                                color_scheme="orange",
                                size="2",
                            ),
                            justify="end",
                            width="100%",
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
                rx.dialog.close(
                    rx.button(
                        "Cerrar",
                        on_click=NominaRRHHState.cerrar_modal_descuento,
                        variant="soft",
                        color_scheme="gray",
                    ),
                ),
                justify="end",
                margin_top="4",
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
