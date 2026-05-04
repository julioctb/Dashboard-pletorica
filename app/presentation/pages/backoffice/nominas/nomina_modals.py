"""
Modales del módulo de Nóminas (vista RRHH).

- Modal crear período
- Modal descuentos manuales por empleado
- Dialogs de confirmación (iniciar preparación, enviar a Contabilidad)
"""
import reflex as rx

from app.presentation.pages.backoffice.nominas.nomina_rrhh_state import NominaRRHHState
from app.presentation.components.ui import (
    form_input,
    form_select,
    form_date,
    botones_modal,
    feedback_callout,
    modal_confirmar_accion,
    modal_formulario,
    modal_section_label,
)
from app.presentation.theme import Colors, Spacing, Typography, Radius


# =============================================================================
# MODAL — CREAR PERÍODO
# =============================================================================

def modal_crear_periodo() -> rx.Component:
    """Modal para crear un nuevo período de nómina."""
    _disabled = {
        "disabled": True,
        "read_only": True,
        "background": Colors.SECONDARY_LIGHT,
        "color": Colors.TEXT_SECONDARY,
        "cursor": "not-allowed",
    }

    contenido = rx.vstack(
        # Callout de info contextual
        rx.cond(
            NominaRRHHState.mensaje_info != "",
            feedback_callout(
                NominaRRHHState.mensaje_info,
                NominaRRHHState.tipo_mensaje,
            ),
            rx.fragment(),
        ),
        # Tipo de nómina — bloqueado fuera de diciembre
        rx.cond(
            NominaRRHHState.es_diciembre,
            form_select(
                label="Tipo de nómina",
                required=True,
                placeholder="Selecciona el tipo de nómina",
                value=NominaRRHHState.form_tipo_corrida,
                on_change=NominaRRHHState.set_form_tipo_corrida,
                options=NominaRRHHState.opciones_tipo_corrida,
                error=NominaRRHHState.error_tipo_corrida,
                hint="La opción de aguinaldo se habilita solo en diciembre.",
                label_variant="portal",
                style_variant="portal",
            ),
            rx.vstack(
                modal_section_label("Tipo de nómina"),
                rx.hstack(
                    rx.icon("lock", size=14, color=Colors.TEXT_MUTED),
                    rx.text(
                        "Ordinaria",
                        font_size=Typography.SIZE_SM,
                        color=Colors.TEXT_SECONDARY,
                    ),
                    spacing="2",
                    align="center",
                    padding=Spacing.SM,
                    background=Colors.SECONDARY_LIGHT,
                    border_radius=Radius.MD,
                    border=f"1px solid {Colors.BORDER}",
                    width="100%",
                    cursor="not-allowed",
                ),
                rx.text(
                    "La opción de aguinaldo se habilita solo en diciembre.",
                    font_size=Typography.SIZE_XS,
                    color=Colors.TEXT_MUTED,
                ),
                spacing="1",
                width="100%",
            ),
        ),
        # Contrato base (solo para corridas no-aguinaldo)
        rx.cond(
            ~NominaRRHHState.es_form_aguinaldo,
            form_select(
                label="Contrato base de nómina",
                required=True,
                placeholder="Selecciona un contrato activo con personal",
                value=NominaRRHHState.form_contrato_nomina_id,
                on_change=NominaRRHHState.set_form_contrato_nomina_id,
                options=NominaRRHHState.contratos_nomina_opciones,
                error=NominaRRHHState.error_contrato_nomina,
                hint="Solo se muestran contratos activos con personal habilitado.",
                label_variant="portal",
                style_variant="portal",
            ),
            rx.fragment(),
        ),
        # Período / Ejercicio fiscal
        rx.cond(
            NominaRRHHState.es_form_aguinaldo,
            form_select(
                label="Período",
                required=True,
                placeholder="Selecciona un período",
                value=NominaRRHHState.form_ejercicio_fiscal,
                on_change=NominaRRHHState.set_form_ejercicio_fiscal,
                options=NominaRRHHState.ejercicios_aguinaldo_catalogo,
                error=NominaRRHHState.error_ejercicio_fiscal,
                hint="Se genera una sola corrida anual de aguinaldo por empresa y ejercicio.",
                label_variant="portal",
                style_variant="portal",
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
                label_variant="portal",
                style_variant="portal",
            ),
        ),
        # Avisos de advertencia
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
        # Divisor antes de campos auto-generados
        rx.divider(border_color=Colors.BORDER),
        # Campos auto-generados (solo lectura)
        rx.grid(
            form_input(
                label="Fecha de generación",
                value=NominaRRHHState.fecha_generacion_preview_fmt,
                label_variant="portal",
                style_variant="portal",
                **_disabled,
            ),
            form_input(
                label="Generado por",
                value=NominaRRHHState.form_generado_por_preview,
                label_variant="portal",
                style_variant="portal",
                **_disabled,
            ),
            columns="2",
            spacing="3",
            width="100%",
        ),
        # Fecha de pago
        form_date(
            label="Fecha de pago",
            required=True,
            value=NominaRRHHState.form_fecha_pago,
            on_change=NominaRRHHState.set_form_fecha_pago,
            error=NominaRRHHState.error_fecha_pago,
            hint="Se autorellena con la fecha de hoy. Puedes ajustarla.",
            label_variant="portal",
        ),
        spacing="4",
        width="100%",
    )

    return modal_formulario(
        open=NominaRRHHState.mostrar_modal_periodo,
        titulo="Nueva nómina",
        descripcion=(
            "Selecciona el contrato base, el período del mes actual, "
            "valida la auditoría y confirma la fecha de pago."
        ),
        contenido=contenido,
        icono="file-text",
        color_icono="teal",
        on_guardar=NominaRRHHState.crear_periodo,
        on_cancelar=NominaRRHHState.cerrar_modal_periodo,
        loading=NominaRRHHState.saving,
        puede_guardar=NominaRRHHState.puede_generar_periodo,
        texto_guardar="Generar nómina",
        texto_guardando="Generando...",
        color_guardar="teal",
        max_width="640px",
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


def _contenido_descuentos() -> rx.Component:
    """Contenido del modal de descuentos: lista existente + formulario."""
    return rx.vstack(
        # --- Descuentos existentes ---
        rx.cond(
            NominaRRHHState.descuentos_empleado,
            rx.vstack(
                rx.hstack(
                    rx.text(
                        "Descuentos aplicados",
                        font_size=Typography.SIZE_SM,
                        font_weight=Typography.WEIGHT_MEDIUM,
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
                rx.box(height="1px", background=Colors.BORDER, width="100%"),
                modal_section_label("AGREGAR DESCUENTO"),
                form_select(
                    label="Tipo de descuento",
                    required=True,
                    placeholder="Selecciona un descuento disponible",
                    value=NominaRRHHState.form_concepto_clave,
                    on_change=NominaRRHHState.set_form_concepto_clave,
                    options=NominaRRHHState.opciones_conceptos_rrhh,
                    disabled=~NominaRRHHState.tiene_opciones_conceptos_rrhh,
                    label_variant="portal",
                    style_variant="portal",
                ),
                rx.grid(
                    form_input(
                        label="Monto",
                        required=True,
                        placeholder="$ 0.00",
                        value=NominaRRHHState.form_monto_descuento,
                        on_change=NominaRRHHState.set_form_monto_descuento,
                        disabled=~NominaRRHHState.tiene_opciones_conceptos_rrhh,
                        error=NominaRRHHState.error_monto,
                        label_variant="portal",
                        style_variant="portal",
                    ),
                    form_input(
                        label="Notas",
                        hint=rx.text.span(
                            "(opcional)",
                            font_size=Typography.SIZE_XS,
                            font_weight=Typography.WEIGHT_REGULAR,
                            color=Colors.TEXT_MUTED,
                        ),
                        placeholder="Ej: Crédito 12345678",
                        value=NominaRRHHState.form_notas_descuento,
                        on_change=NominaRRHHState.set_form_notas_descuento,
                        disabled=~NominaRRHHState.tiene_opciones_conceptos_rrhh,
                        label_variant="portal",
                        style_variant="portal",
                    ),
                    columns="2",
                    spacing="3",
                    width="100%",
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
    )


def modal_descuentos_empleado() -> rx.Component:
    """Modal para agregar/ver descuentos manuales de RRHH de un empleado."""
    return modal_formulario(
        open=NominaRRHHState.mostrar_modal_descuento,
        titulo="Descuentos",
        descripcion=NominaRRHHState.nombre_empleado_seleccionado,
        icono="circle-minus",
        color_icono="teal",
        color_guardar="teal",
        max_width="480px",
        contenido=_contenido_descuentos(),
        texto_cancelar="Cerrar",
        on_cancelar=NominaRRHHState.cerrar_modal_descuento,
        on_guardar=NominaRRHHState.guardar_descuento,
        texto_guardar="Añadir",
        texto_guardando="Añadiendo...",
        loading=NominaRRHHState.saving,
        puede_guardar=NominaRRHHState.puede_editar_descuentos
        & NominaRRHHState.puede_anadir_descuento,
    )


# =============================================================================
# DIALOG — INICIAR PREPARACIÓN
# =============================================================================

def dialog_iniciar_preparacion() -> rx.Component:
    """Confirmación para iniciar preparación (BORRADOR → EN_PREPARACION_RRHH)."""
    return modal_confirmar_accion(
        open=NominaRRHHState.mostrar_dialog_iniciar,
        titulo="Iniciar preparación de nómina",
        mensaje=(
            "Al iniciar la preparación podrás capturar descuentos manuales "
            "para cada empleado. El período pasará a estado 'En preparación'."
        ),
        on_confirmar=NominaRRHHState.iniciar_preparacion,
        on_cancelar=NominaRRHHState.cerrar_dialog_iniciar,
        loading=NominaRRHHState.saving,
        texto_confirmar="Iniciar preparación",
        texto_confirmando="Iniciando...",
        color_confirmar="blue",
        max_width="420px",
    )


# =============================================================================
# DIALOG — ENVIAR A CONTABILIDAD
# =============================================================================

def dialog_enviar_contabilidad() -> rx.Component:
    """Confirmación para enviar a Contabilidad. Acción irreversible para RRHH."""
    return modal_confirmar_accion(
        open=NominaRRHHState.mostrar_dialog_envio,
        titulo="Enviar a Contabilidad",
        mensaje="¿Confirmas el envío de esta nómina a Contabilidad?",
        detalle_contenido=rx.callout(
            "Una vez enviada, RRHH no podrá modificar los descuentos. "
            "Asegúrate de haber capturado INFONAVIT, FONACOT y préstamos.",
            icon="triangle-alert",
            color_scheme="orange",
            size="1",
        ),
        on_confirmar=NominaRRHHState.enviar_a_contabilidad,
        on_cancelar=NominaRRHHState.cerrar_dialog_envio,
        loading=NominaRRHHState.saving,
        texto_confirmar="Enviar a Contabilidad",
        texto_confirmando="Enviando...",
        color_confirmar="orange",
        max_width="440px",
    )
