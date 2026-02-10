"""
Pagina principal de Pagos.
Muestra todos los pagos del sistema con filtros.
"""
import reflex as rx
from app.presentation.pages.pagos.pagos_state import PagosPageState
from app.presentation.components.ui import (
    tabla_vacia,
    skeleton_tabla,
    form_input,
    form_select,
    form_date,
    form_textarea,
    boton_guardar,
    boton_cancelar,
    tabla_action_button,
    tabla_action_buttons,
)
from app.presentation.components.ui.modals import modal_confirmar_eliminar
from app.presentation.theme import Colors, Typography
from app.presentation.layout import page_layout, page_header, page_toolbar


# =============================================================================
# TABLA DE PAGOS
# =============================================================================

ENCABEZADOS = [
    {"nombre": "Fecha", "ancho": "100px"},
    {"nombre": "Contrato", "ancho": "120px"},
    {"nombre": "Empresa", "ancho": "200px"},
    {"nombre": "Monto", "ancho": "120px"},
    {"nombre": "Concepto", "ancho": "250px"},
    {"nombre": "Factura", "ancho": "100px"},
    {"nombre": "Acciones", "ancho": "80px"},
]


def _fila_pago(pago: dict) -> rx.Component:
    """Fila de la tabla de pagos."""
    return rx.table.row(
        rx.table.cell(
            rx.text(pago["fecha_pago_fmt"], font_size=Typography.SIZE_SM),
        ),
        rx.table.cell(
            rx.badge(pago["contrato_codigo"], color_scheme="blue", size="1"),
        ),
        rx.table.cell(
            rx.text(
                pago["empresa_nombre"],
                font_size=Typography.SIZE_SM,
                max_width="200px",
                overflow="hidden",
                text_overflow="ellipsis",
                white_space="nowrap",
            ),
        ),
        rx.table.cell(
            rx.text(
                pago["monto_fmt"],
                font_size=Typography.SIZE_SM,
                font_weight=Typography.WEIGHT_BOLD,
                color="var(--green-11)",
            ),
        ),
        rx.table.cell(
            rx.text(
                pago["concepto"],
                font_size=Typography.SIZE_SM,
                max_width="250px",
                overflow="hidden",
                text_overflow="ellipsis",
                white_space="nowrap",
            ),
        ),
        rx.table.cell(
            rx.cond(
                pago["numero_factura"],
                rx.text(pago["numero_factura"], font_size=Typography.SIZE_SM, color=Colors.TEXT_MUTED),
                rx.text("-", font_size=Typography.SIZE_SM, color=Colors.TEXT_MUTED),
            ),
        ),
        rx.table.cell(
            tabla_action_buttons([
                tabla_action_button(
                    icon="pencil",
                    tooltip="Editar",
                    on_click=lambda: PagosPageState.abrir_modal_editar(pago),
                    color_scheme="blue",
                ),
                tabla_action_button(
                    icon="trash-2",
                    tooltip="Eliminar",
                    on_click=lambda: PagosPageState.abrir_modal_eliminar(pago),
                    color_scheme="red",
                ),
            ]),
        ),
    )


def _tabla_pagos() -> rx.Component:
    """Tabla de pagos."""
    return rx.cond(
        PagosPageState.loading,
        skeleton_tabla(columnas=ENCABEZADOS, filas=5),
        rx.cond(
            PagosPageState.tiene_pagos,
            rx.vstack(
                rx.table.root(
                    rx.table.header(
                        rx.table.row(
                            rx.foreach(
                                ENCABEZADOS,
                                lambda col: rx.table.column_header_cell(
                                    col["nombre"],
                                    width=col["ancho"],
                                ),
                            ),
                        ),
                    ),
                    rx.table.body(
                        rx.foreach(PagosPageState.pagos, _fila_pago),
                    ),
                    width="100%",
                    variant="surface",
                ),
                rx.text(
                    "Mostrando ",
                    PagosPageState.total_registros,
                    " pago(s)",
                    font_size=Typography.SIZE_SM,
                    color=Colors.TEXT_MUTED,
                ),
                width="100%",
                spacing="3",
            ),
            tabla_vacia(
                mensaje="No hay pagos registrados",
                onclick=PagosPageState.abrir_modal_crear,
            ),
        ),
    )


# =============================================================================
# FILTROS
# =============================================================================

def _filtros() -> rx.Component:
    """Filtros de pagos."""
    return rx.hstack(
        # Filtro por contrato
        rx.select.root(
            rx.select.trigger(placeholder="Contrato", width="180px"),
            rx.select.content(
                rx.foreach(
                    PagosPageState.contratos_opciones,
                    lambda opt: rx.select.item(opt["label"], value=opt["value"]),
                ),
            ),
            value=PagosPageState.filtro_contrato_id,
            on_change=PagosPageState.set_filtro_contrato_id,
        ),
        # Fecha desde
        rx.vstack(
            rx.text("Desde", size="1", color=Colors.TEXT_MUTED),
            rx.input(
                type="date",
                value=PagosPageState.filtro_fecha_desde,
                on_change=PagosPageState.set_filtro_fecha_desde,
                width="140px",
            ),
            spacing="1",
        ),
        # Fecha hasta
        rx.vstack(
            rx.text("Hasta", size="1", color=Colors.TEXT_MUTED),
            rx.input(
                type="date",
                value=PagosPageState.filtro_fecha_hasta,
                on_change=PagosPageState.set_filtro_fecha_hasta,
                width="140px",
            ),
            spacing="1",
        ),
        # Boton aplicar
        rx.button(
            "Filtrar",
            on_click=PagosPageState.aplicar_filtros,
            variant="soft",
            size="2",
        ),
        # Boton limpiar
        rx.button(
            rx.icon("x", size=14),
            "Limpiar",
            on_click=PagosPageState.limpiar_filtros,
            variant="ghost",
            size="2",
        ),
        spacing="3",
        wrap="wrap",
        align="end",
    )


# =============================================================================
# MODAL CREAR/EDITAR
# =============================================================================

def _modal_pago() -> rx.Component:
    """Modal para crear o editar pago."""
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title(
                rx.cond(
                    PagosPageState.es_edicion,
                    "Editar Pago",
                    "Registrar Pago",
                ),
            ),
            rx.dialog.description(
                rx.cond(
                    PagosPageState.es_edicion,
                    "Modifique los datos del pago.",
                    "Complete los datos del nuevo pago.",
                ),
                margin_bottom="16px",
            ),
            rx.vstack(
                # Contrato (solo en creacion)
                rx.cond(
                    ~PagosPageState.es_edicion,
                    form_select(
                        label="Contrato",
                        required=True,
                        placeholder="Seleccione contrato",
                        value=PagosPageState.form_contrato_id,
                        on_change=PagosPageState.set_form_contrato_id,
                        options=PagosPageState.contratos_opciones[1:],  # Sin "Todos"
                        error=PagosPageState.error_contrato_id,
                    ),
                ),
                # Fecha y monto
                rx.hstack(
                    form_date(
                        label="Fecha de pago",
                        required=True,
                        value=PagosPageState.form_fecha_pago,
                        on_change=PagosPageState.set_form_fecha_pago,
                        error=PagosPageState.error_fecha_pago,
                    ),
                    form_input(
                        label="Monto",
                        required=True,
                        placeholder="Ej: 50000.00",
                        value=PagosPageState.form_monto,
                        on_change=PagosPageState.set_form_monto,
                        error=PagosPageState.error_monto,
                    ),
                    spacing="3",
                    width="100%",
                ),
                # Concepto
                form_textarea(
                    label="Concepto",
                    required=True,
                    placeholder="Descripcion del pago",
                    value=PagosPageState.form_concepto,
                    on_change=PagosPageState.set_form_concepto,
                    error=PagosPageState.error_concepto,
                    rows="2",
                ),
                # Factura y comprobante
                rx.hstack(
                    form_input(
                        label="Numero de factura",
                        placeholder="Ej: FAC-001",
                        value=PagosPageState.form_numero_factura,
                        on_change=PagosPageState.set_form_numero_factura,
                    ),
                    form_input(
                        label="Comprobante/Referencia",
                        placeholder="Ej: REF-2026",
                        value=PagosPageState.form_comprobante,
                        on_change=PagosPageState.set_form_comprobante,
                    ),
                    spacing="3",
                    width="100%",
                ),
                # Notas
                form_textarea(
                    label="Notas",
                    placeholder="Observaciones adicionales...",
                    value=PagosPageState.form_notas,
                    on_change=PagosPageState.set_form_notas,
                    rows="2",
                ),
                spacing="4",
                width="100%",
            ),
            # Botones
            rx.hstack(
                boton_cancelar(on_click=PagosPageState.cerrar_modal_pago),
                boton_guardar(
                    texto=rx.cond(
                        PagosPageState.es_edicion,
                        "Guardar Cambios",
                        "Registrar Pago",
                    ),
                    texto_guardando="Guardando...",
                    on_click=PagosPageState.guardar_pago,
                    saving=PagosPageState.saving,
                ),
                spacing="3",
                justify="end",
                margin_top="4",
            ),
            max_width="500px",
        ),
        open=PagosPageState.mostrar_modal_pago,
        on_open_change=rx.noop,
    )


def _modal_eliminar() -> rx.Component:
    """Modal de confirmacion para eliminar."""
    return modal_confirmar_eliminar(
        open=PagosPageState.mostrar_modal_eliminar,
        titulo="Eliminar Pago",
        mensaje="Esta seguro de eliminar este pago?",
        detalle_contenido=rx.cond(
            PagosPageState.pago_seleccionado,
            rx.vstack(
                rx.hstack(
                    rx.text("Monto: ", weight="bold"),
                    rx.text(PagosPageState.pago_seleccionado["monto_fmt"]),
                    spacing="1",
                ),
                rx.hstack(
                    rx.text("Concepto: "),
                    rx.text(PagosPageState.pago_seleccionado["concepto"]),
                    spacing="1",
                ),
                spacing="1",
            ),
            rx.text(""),
        ),
        on_confirmar=PagosPageState.eliminar_pago,
        on_cancelar=PagosPageState.cerrar_modal_eliminar,
        loading=PagosPageState.saving,
    )


# =============================================================================
# PAGINA
# =============================================================================

def pagos_page() -> rx.Component:
    """Pagina de Pagos."""
    return rx.box(
        page_layout(
            header=page_header(
                titulo="Pagos",
                subtitulo="Registro de pagos a contratos",
                icono="credit-card",
                accion_principal=rx.button(
                    rx.icon("plus", size=16),
                    "Nuevo Pago",
                    on_click=PagosPageState.abrir_modal_crear,
                    color_scheme="blue",
                ),
            ),
            toolbar=page_toolbar(
                search_value=PagosPageState.filtro_busqueda,
                search_placeholder="Buscar por concepto o factura...",
                on_search_change=PagosPageState.set_filtro_busqueda,
                on_search_clear=lambda: PagosPageState.set_filtro_busqueda(""),
                filters=_filtros(),
                show_view_toggle=False,
            ),
            content=rx.vstack(
                _tabla_pagos(),
                _modal_pago(),
                _modal_eliminar(),
                spacing="4",
                width="100%",
            ),
        ),
        width="100%",
        min_height="100vh",
        on_mount=PagosPageState.on_mount,
    )
