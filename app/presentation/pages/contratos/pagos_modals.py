"""
Modales para el módulo de Pagos de Contratos.
"""
import reflex as rx
from app.presentation.components.ui.form_input import form_input, form_textarea, form_date
from app.presentation.components.ui.modals import modal_confirmar_eliminar as modal_eliminar_generico
from app.presentation.pages.contratos.pagos_state import PagosState


def resumen_pagos() -> rx.Component:
    """Tarjeta con resumen de pagos del contrato"""
    return rx.card(
        rx.hstack(
            # Monto Máximo
            rx.vstack(
                rx.text("Monto Máximo", size="1", color="gray"),
                rx.text(PagosState.contrato_monto_maximo, weight="bold", size="3"),
                spacing="1",
                align="center",
            ),
            rx.separator(orientation="vertical", size="2"),
            # Total Pagado
            rx.vstack(
                rx.text("Total Pagado", size="1", color="gray"),
                rx.text(PagosState.total_pagado, weight="bold", size="3", color="green"),
                spacing="1",
                align="center",
            ),
            rx.separator(orientation="vertical", size="2"),
            # Saldo Pendiente
            rx.vstack(
                rx.text("Saldo Pendiente", size="1", color="gray"),
                rx.text(PagosState.saldo_pendiente, weight="bold", size="3", color="orange"),
                spacing="1",
                align="center",
            ),
            rx.separator(orientation="vertical", size="2"),
            # Porcentaje
            rx.vstack(
                rx.text("Avance", size="1", color="gray"),
                rx.text(PagosState.porcentaje_pagado, weight="bold", size="3", color="blue"),
                spacing="1",
                align="center",
            ),
            justify="between",
            width="100%",
            padding="3",
        ),
        width="100%",
    )


def fila_pago(pago: dict) -> rx.Component:
    """Fila de la tabla de pagos"""
    return rx.table.row(
        rx.table.cell(
            rx.text(pago["fecha_pago_fmt"], size="2"),
        ),
        rx.table.cell(
            rx.text(pago["monto_fmt"], size="2", weight="medium"),
        ),
        rx.table.cell(
            rx.text(pago["concepto"], size="2"),
            max_width="200px",
            overflow="hidden",
            text_overflow="ellipsis",
            white_space="nowrap",
        ),
        rx.table.cell(
            rx.cond(
                pago["numero_factura"],
                rx.text(pago["numero_factura"], size="2", color="gray"),
                rx.text("-", size="2", color="gray"),
            ),
        ),
        rx.table.cell(
            rx.hstack(
                # Editar
                rx.cond(
                    ~PagosState.contrato_esta_cerrado,
                    rx.icon_button(
                        rx.icon("pencil", size=14),
                        size="1",
                        variant="ghost",
                        color_scheme="blue",
                        on_click=lambda: PagosState.abrir_modal_editar_pago(pago),
                        title="Editar",
                    ),
                ),
                # Eliminar
                rx.cond(
                    ~PagosState.contrato_esta_cerrado,
                    rx.icon_button(
                        rx.icon("trash-2", size=14),
                        size="1",
                        variant="ghost",
                        color_scheme="red",
                        on_click=lambda: PagosState.abrir_confirmar_eliminar(pago),
                        title="Eliminar",
                    ),
                ),
                spacing="1",
            ),
        ),
    )


def tabla_pagos() -> rx.Component:
    """Tabla de pagos del contrato"""
    return rx.cond(
        PagosState.cantidad_pagos > 0,
        rx.table.root(
            rx.table.header(
                rx.table.row(
                    rx.table.column_header_cell("Fecha", width="100px"),
                    rx.table.column_header_cell("Monto", width="120px"),
                    rx.table.column_header_cell("Concepto", width="200px"),
                    rx.table.column_header_cell("Factura", width="100px"),
                    rx.table.column_header_cell("Acciones", width="80px"),
                ),
            ),
            rx.table.body(
                rx.foreach(PagosState.pagos, fila_pago),
            ),
            width="100%",
            size="1",
        ),
        rx.callout(
            "No hay pagos registrados para este contrato",
            icon="info",
            color_scheme="gray",
            size="2",
        ),
    )


def modal_pagos() -> rx.Component:
    """Modal principal para ver y gestionar pagos de un contrato"""
    return rx.dialog.root(
        rx.dialog.content(
            # Header
            rx.dialog.title(
                rx.hstack(
                    rx.icon("credit-card", size=20),
                    rx.text("Pagos del Contrato"),
                    rx.badge(PagosState.contrato_codigo, color_scheme="blue"),
                    spacing="2",
                    align="center",
                ),
            ),
            rx.dialog.description(
                "Gestione los pagos realizados a este contrato",
                margin_bottom="16px",
            ),

            # Contenido
            rx.vstack(
                # Resumen de pagos
                resumen_pagos(),

                # Barra de acciones
                rx.hstack(
                    rx.cond(
                        ~PagosState.contrato_esta_cerrado,
                        rx.button(
                            rx.icon("plus", size=16),
                            "Registrar Pago",
                            on_click=PagosState.abrir_modal_crear_pago,
                            color_scheme="blue",
                            size="2",
                        ),
                    ),
                    rx.spacer(),
                    rx.cond(
                        PagosState.puede_cerrar_contrato,
                        rx.button(
                            rx.icon("lock", size=16),
                            "Cerrar Contrato",
                            on_click=PagosState.cerrar_contrato_pagado,
                            color_scheme="green",
                            variant="outline",
                            size="2",
                            loading=PagosState.saving,
                        ),
                    ),
                    rx.cond(
                        PagosState.contrato_esta_cerrado,
                        rx.badge(
                            rx.hstack(
                                rx.icon("circle-check", size=14),
                                rx.text("Contrato Cerrado"),
                                spacing="1",
                            ),
                            color_scheme="green",
                            size="2",
                        ),
                    ),
                    width="100%",
                    padding_y="3",
                ),

                # Tabla de pagos
                rx.cond(
                    PagosState.loading,
                    rx.center(
                        rx.spinner(size="3"),
                        padding="8",
                    ),
                    tabla_pagos(),
                ),

                spacing="4",
                width="100%",
            ),

            # Footer
            rx.hstack(
                rx.button(
                    "Cerrar",
                    variant="soft",
                    color_scheme="gray",
                    on_click=PagosState.cerrar_modal_pagos,
                ),
                justify="end",
                margin_top="4",
            ),

            max_width="700px",
            padding="6",
        ),
        open=PagosState.mostrar_modal_pagos,
        # No cerrar al hacer click fuera - solo con botones
        on_open_change=rx.noop,
    )


def modal_pago_form() -> rx.Component:
    """Modal para crear/editar un pago"""
    return rx.dialog.root(
        rx.dialog.content(
            # Header
            rx.dialog.title(
                rx.cond(
                    PagosState.es_edicion_pago,
                    "Editar Pago",
                    "Registrar Pago"
                )
            ),
            rx.dialog.description(
                rx.cond(
                    PagosState.es_edicion_pago,
                    "Modifique la información del pago",
                    "Complete la información del pago"
                ),
                margin_bottom="16px",
            ),

            # Formulario
            rx.vstack(
                # Fecha y Monto
                rx.hstack(
                    form_date(
                        label="Fecha de pago",
                        required=True,
                        value=PagosState.form_fecha_pago,
                        on_change=PagosState.set_form_fecha_pago,
                        error=PagosState.error_fecha_pago,
                    ),
                    form_input(
                        label="Monto",
                        required=True,
                        placeholder="Ej: 50,000.00",
                        value=PagosState.form_monto,
                        on_change=PagosState.set_form_monto,
                        on_blur=PagosState.validar_monto_campo,
                        error=PagosState.error_monto,
                    ),
                    spacing="3",
                    width="100%",
                ),

                # Concepto
                form_textarea(
                    label="Concepto",
                    required=True,
                    placeholder="Ej: Pago mensual por servicio de limpieza",
                    value=PagosState.form_concepto,
                    on_change=PagosState.set_form_concepto,
                    on_blur=PagosState.validar_concepto_campo,
                    error=PagosState.error_concepto,
                    rows="2",
                ),

                # Número de Factura y Comprobante
                rx.hstack(
                    form_input(
                        label="Numero de factura",
                        placeholder="Ej: FAC-001",
                        value=PagosState.form_numero_factura,
                        on_change=PagosState.set_form_numero_factura,
                        on_blur=PagosState.validar_numero_factura_campo,
                        error=PagosState.error_numero_factura,
                    ),
                    form_input(
                        label="Comprobante/Referencia",
                        placeholder="Ej: REF-2026-001",
                        value=PagosState.form_comprobante,
                        on_change=PagosState.set_form_comprobante,
                        on_blur=PagosState.validar_comprobante_campo,
                        error=PagosState.error_comprobante,
                    ),
                    spacing="3",
                    width="100%",
                ),

                # Notas
                form_textarea(
                    label="Notas",
                    placeholder="Ej: Observaciones adicionales del pago",
                    value=PagosState.form_notas,
                    on_change=PagosState.set_form_notas,
                    on_blur=PagosState.validar_notas_campo,
                    error=PagosState.error_notas,
                    rows="2",
                ),

                spacing="4",
                width="100%",
            ),

            # Footer
            rx.hstack(
                rx.button(
                    "Cancelar",
                    variant="soft",
                    color_scheme="gray",
                    on_click=PagosState.cerrar_modal_pago_form,
                ),
                rx.button(
                    rx.cond(
                        PagosState.es_edicion_pago,
                        "Guardar Cambios",
                        "Registrar Pago"
                    ),
                    on_click=PagosState.guardar_pago,
                    disabled=~PagosState.puede_guardar_pago,
                    loading=PagosState.saving,
                    color_scheme="blue",
                ),
                justify="end",
                spacing="3",
                margin_top="4",
            ),

            max_width="500px",
            padding="6",
        ),
        open=PagosState.mostrar_modal_pago_form,
        # No cerrar al hacer click fuera - solo con botones
        on_open_change=rx.noop,
    )


def modal_confirmar_eliminar_pago() -> rx.Component:
    """Modal de confirmación para eliminar pago (usa componente genérico)"""
    return modal_eliminar_generico(
        open=PagosState.mostrar_modal_confirmar_eliminar,
        titulo="Eliminar Pago",
        mensaje="¿Está seguro de eliminar este pago?",
        detalle_contenido=rx.cond(
            PagosState.pago_seleccionado,
            rx.vstack(
                rx.hstack(
                    rx.text("Monto: ", weight="bold"),
                    rx.text(PagosState.pago_seleccionado["monto_fmt"], weight="bold"),
                    spacing="1",
                ),
                rx.hstack(
                    rx.text("Fecha: ", size="2"),
                    rx.text(PagosState.pago_seleccionado["fecha_pago_fmt"], size="2"),
                    spacing="1",
                ),
                spacing="1",
            ),
            rx.text(""),
        ),
        on_confirmar=PagosState.eliminar_pago,
        on_cancelar=PagosState.cerrar_confirmar_eliminar,
        loading=PagosState.saving,
    )
