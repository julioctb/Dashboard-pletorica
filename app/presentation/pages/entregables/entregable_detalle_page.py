"""
Página de Detalle de Entregable (Admin).
Permite ver archivos, detalle de personal, y aprobar/rechazar.
"""

import reflex as rx

from app.presentation.pages.entregables.entregable_detalle_state import EntregableDetalleState
from app.presentation.components.shared.auth_state import AuthState
from app.presentation.layout import page_layout
from app.presentation.components.ui import (
    status_badge_reactive,
    form_input,
    form_textarea,
    form_date,
    table_shell,
)
from app.presentation.theme import Colors, Spacing, Radius, Shadows


# =============================================================================
# HEADER
# =============================================================================
def _breadcrumb() -> rx.Component:
    return rx.hstack(
        rx.button(
            rx.icon("arrow-left", size=16),
            "Volver",
            variant="ghost",
            size="2",
            on_click=EntregableDetalleState.volver_a_listado,
        ),
        rx.text("/", color=Colors.TEXT_MUTED),
        rx.text(EntregableDetalleState.contrato_info["codigo"], size="2", color=Colors.TEXT_SECONDARY),
        rx.text("/", color=Colors.TEXT_MUTED),
        rx.text(f"Período {EntregableDetalleState.numero_periodo}", size="2", weight="medium"),
        spacing="2",
        align="center",
        padding_bottom=Spacing.MD,
    )


def _header_entregable() -> rx.Component:
    return rx.card(
        rx.hstack(
            rx.vstack(
                rx.hstack(
                    rx.text(f"Período {EntregableDetalleState.numero_periodo}", size="6", weight="bold"),
                    status_badge_reactive(EntregableDetalleState.estatus_actual),
                    spacing="3",
                    align="center",
                ),
                rx.text(EntregableDetalleState.periodo_texto, size="3", color=Colors.TEXT_SECONDARY),
                rx.hstack(
                    rx.text("Contrato:", size="2", color=Colors.TEXT_MUTED),
                    rx.text(EntregableDetalleState.contrato_info["codigo"], size="2", weight="medium"),
                    rx.text("•", color=Colors.TEXT_MUTED),
                    rx.text(EntregableDetalleState.contrato_info["empresa_nombre"], size="2"),
                    spacing="2",
                ),
                spacing="2",
                align="start",
            ),
            rx.spacer(),
            rx.match(
                EntregableDetalleState.estatus_actual,
                # EN_REVISION: Aprobar / Rechazar entregable (solo con permiso autorizar)
                ("EN_REVISION", rx.cond(
                    AuthState.puede_autorizar_entregables,
                    rx.hstack(
                        rx.button(
                            rx.icon("circle-x", size=16),
                            "Rechazar",
                            border=f"1px solid {Colors.ERROR}",
                            color=Colors.ERROR,
                            background="transparent",
                            _hover={"background": Colors.ERROR_LIGHT},
                            on_click=EntregableDetalleState.abrir_modal_rechazar,
                        ),
                        rx.button(
                            rx.icon("circle-check", size=16),
                            "Aprobar",
                            background=Colors.PRIMARY,
                            color=Colors.TEXT_INVERSE,
                            _hover={"background": Colors.PRIMARY_HOVER},
                            on_click=EntregableDetalleState.abrir_modal_aprobar,
                        ),
                        spacing="2",
                    ),
                    rx.badge("En revisión", color_scheme="sky", size="2"),
                )),
                # PREFACTURA_ENVIADA: Aprobar / Rechazar prefactura (solo con permiso autorizar)
                ("PREFACTURA_ENVIADA", rx.cond(
                    AuthState.puede_autorizar_entregables,
                    rx.hstack(
                        rx.button(
                            rx.icon("file-x", size=16),
                            "Rechazar Prefactura",
                            border=f"1px solid {Colors.ERROR}",
                            color=Colors.ERROR,
                            background="transparent",
                            _hover={"background": Colors.ERROR_LIGHT},
                            on_click=EntregableDetalleState.abrir_modal_rechazar_prefactura,
                        ),
                        rx.button(
                            rx.icon("file-check", size=16),
                            "Aprobar Prefactura",
                            background=Colors.SUCCESS,
                            color=Colors.TEXT_INVERSE,
                            _hover={"opacity": "0.9"},
                            on_click=EntregableDetalleState.aprobar_prefactura,
                            loading=EntregableDetalleState.procesando,
                        ),
                        spacing="2",
                    ),
                    rx.badge("Prefactura pendiente de revisión", color_scheme="sky", size="2"),
                )),
                # FACTURADO: Registrar pago (solo con permiso autorizar pagos)
                ("FACTURADO", rx.cond(
                    AuthState.puede_autorizar_pagos,
                    rx.button(
                        rx.icon("banknote", size=16),
                        "Registrar Pago",
                        background=Colors.PRIMARY,
                        color=Colors.TEXT_INVERSE,
                        _hover={"background": Colors.PRIMARY_HOVER},
                        on_click=EntregableDetalleState.abrir_modal_registrar_pago,
                    ),
                    rx.badge("Pendiente de pago", color_scheme="amber", size="2"),
                )),
                # APROBADO: Esperando prefactura del cliente
                ("APROBADO", rx.badge(
                    rx.icon("clock", size=12), "Esperando prefactura",
                    color_scheme="amber", size="2",
                )),
                # PREFACTURA_RECHAZADA: Cliente debe corregir
                ("PREFACTURA_RECHAZADA", rx.badge(
                    rx.icon("triangle-alert", size=12), "Prefactura rechazada",
                    color_scheme="red", size="2",
                )),
                # PREFACTURA_APROBADA: Esperando factura
                ("PREFACTURA_APROBADA", rx.badge(
                    rx.icon("clock", size=12), "Esperando factura",
                    color_scheme="green", size="2",
                )),
                # PAGADO: Completado
                ("PAGADO", rx.badge(
                    rx.icon("badge-check", size=12), "Pagado",
                    color_scheme="green", size="2",
                )),
                # RECHAZADO
                ("RECHAZADO", rx.badge(
                    rx.icon("x", size=12), "Rechazado",
                    color_scheme="red", size="2",
                )),
                # Default
                rx.badge("Pendiente de entrega", color_scheme="gray", size="2"),
            ),
            width="100%",
            align="start",
        ),
        padding="5",
    )


# =============================================================================
# ARCHIVOS
# =============================================================================
def _card_imagen(archivo: dict) -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.center(
                rx.icon("image", size=40, color=Colors.PRIMARY),
                width="100%",
                height="120px",
                background=Colors.PRIMARY_LIGHT,
                border_radius=f"{Radius.MD} {Radius.MD} 0 0",
            ),
            rx.vstack(
                rx.text(archivo["nombre"], size="1", weight="medium", no_of_lines=1),
                rx.text(f"{archivo['tamanio_mb']} MB", size="1", color=Colors.TEXT_MUTED),
                spacing="0",
                padding=Spacing.SM,
                width="100%",
            ),
            spacing="0",
            width="100%",
        ),
        border=f"1px solid {Colors.BORDER}",
        border_radius=Radius.MD,
        overflow="hidden",
        cursor="pointer",
        _hover={"box_shadow": Shadows.MD, "border_color": Colors.PRIMARY},
        on_click=EntregableDetalleState.ver_imagen(archivo["id"]),
        width="150px",
    )


def _card_documento(archivo: dict) -> rx.Component:
    return rx.hstack(
        rx.center(
            rx.icon("file-text", size=20, color=Colors.ERROR),
            width="40px",
            height="40px",
            background=Colors.ERROR_LIGHT,
            border_radius=Radius.MD,
        ),
        rx.vstack(
            rx.text(archivo["nombre"], size="2", weight="medium", no_of_lines=1),
            rx.text(f"{archivo['tamanio_mb']} MB", size="1", color=Colors.TEXT_MUTED),
            spacing="0",
            align="start",
        ),
        rx.spacer(),
        rx.button(
            rx.icon("download", size=14),
            size="1",
            variant="ghost",
            on_click=EntregableDetalleState.descargar_documento(archivo["id"]),
        ),
        padding=Spacing.SM,
        border=f"1px solid {Colors.BORDER}",
        border_radius=Radius.MD,
        width="100%",
        align="center",
    )


def _seccion_archivos() -> rx.Component:
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.icon("paperclip", size=20, color=Colors.PRIMARY),
                rx.text("Archivos Subidos", size="4", weight="bold"),
                rx.spacer(),
                rx.badge(EntregableDetalleState.archivos.length(), " archivos", color_scheme="gray"),
                align="center",
                width="100%",
            ),
            rx.divider(),
            rx.cond(
                EntregableDetalleState.tiene_archivos,
                rx.vstack(
                    rx.cond(
                        EntregableDetalleState.archivos_imagenes.length() > 0,
                        rx.vstack(
                            rx.text("Imágenes", size="2", weight="medium", color=Colors.TEXT_SECONDARY),
                            rx.hstack(
                                rx.foreach(EntregableDetalleState.archivos_imagenes, _card_imagen),
                                spacing="3",
                                flex_wrap="wrap",
                            ),
                            spacing="2",
                            align="start",
                            width="100%",
                        ),
                        rx.fragment(),
                    ),
                    rx.cond(
                        EntregableDetalleState.archivos_documentos.length() > 0,
                        rx.vstack(
                            rx.text("Documentos", size="2", weight="medium", color=Colors.TEXT_SECONDARY),
                            rx.foreach(EntregableDetalleState.archivos_documentos, _card_documento),
                            spacing="2",
                            align="start",
                            width="100%",
                        ),
                        rx.fragment(),
                    ),
                    spacing="4",
                    width="100%",
                ),
                rx.center(
                    rx.vstack(
                        rx.icon("file-x", size=40, color=Colors.TEXT_MUTED),
                        rx.text("No hay archivos subidos", color=Colors.TEXT_MUTED),
                        spacing="2",
                        align="center",
                    ),
                    padding="8",
                    width="100%",
                ),
            ),
            spacing="4",
            width="100%",
        ),
        padding="5",
    )


# =============================================================================
# DETALLE DE PERSONAL
# =============================================================================
def _fila_detalle_personal(detalle: dict) -> rx.Component:
    return rx.table.row(
        rx.table.cell(
            rx.vstack(
                rx.text(detalle["categoria_clave"], weight="medium"),
                rx.text(detalle["categoria_nombre"], size="1", color=Colors.TEXT_MUTED),
                spacing="0",
            ),
        ),
        rx.table.cell(rx.text(detalle["cantidad_reportada"])),
        rx.table.cell(
            rx.hstack(
                rx.text(detalle["cantidad_validada"], weight="medium"),
                rx.cond(
                    detalle["cumple_minimo"],
                    rx.cond(
                        detalle["excede_maximo"],
                        rx.icon("triangle-alert", size=14, color=Colors.WARNING),
                        rx.icon("check", size=14, color=Colors.SUCCESS),
                    ),
                    rx.icon("circle-alert", size=14, color=Colors.ERROR),
                ),
                spacing="1",
                align="center",
            ),
        ),
        rx.table.cell(
            rx.text(f"({detalle['cantidad_minima']} - {detalle['cantidad_maxima']})", size="1", color=Colors.TEXT_MUTED),
        ),
        rx.table.cell(rx.text(f"${detalle['tarifa_unitaria']}")),
        rx.table.cell(rx.text(f"${detalle['subtotal']}", weight="medium")),
    )


def _seccion_detalle_personal() -> rx.Component:
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.icon("users", size=20, color=Colors.PRIMARY),
                rx.text("Detalle de Personal", size="4", weight="bold"),
                rx.spacer(),
                rx.text(
                    f"Total: ${EntregableDetalleState.monto_calculado_total}",
                    size="3",
                    weight="bold",
                    color=Colors.PRIMARY,
                ),
                align="center",
                width="100%",
            ),
            rx.divider(),
            rx.cond(
                EntregableDetalleState.tiene_detalle_personal,
                rx.box(
                    table_shell(
                        loading=EntregableDetalleState.loading,
                        has_rows=True,
                        header_cells=[
                            rx.table.column_header_cell("Categoría"),
                            rx.table.column_header_cell("Reportado"),
                            rx.table.column_header_cell("Validado"),
                            rx.table.column_header_cell("Rango"),
                            rx.table.column_header_cell("Tarifa"),
                            rx.table.column_header_cell("Subtotal"),
                        ],
                        body_component=rx.foreach(
                            EntregableDetalleState.detalle_personal,
                            _fila_detalle_personal,
                        ),
                        empty_component=rx.fragment(),
                    ),
                    overflow_x="auto",
                ),
                rx.center(
                    rx.vstack(
                        rx.icon("users-round", size=40, color=Colors.TEXT_MUTED),
                        rx.text("No hay detalle de personal", color=Colors.TEXT_MUTED),
                        spacing="2",
                        align="center",
                    ),
                    padding="8",
                    width="100%",
                ),
            ),
            spacing="4",
            width="100%",
        ),
        padding="5",
    )


# =============================================================================
# OBSERVACIONES RECHAZO
# =============================================================================
def _seccion_observaciones_rechazo() -> rx.Component:
    return rx.cond(
        EntregableDetalleState.entregable["observaciones_rechazo"],
        rx.callout(
            rx.text(EntregableDetalleState.entregable["observaciones_rechazo"]),
            icon="triangle-alert",
            color_scheme="red",
            width="100%",
        ),
        rx.fragment(),
    )


# =============================================================================
# SECCIÓN PREFACTURA/FACTURA (POST-APROBACIÓN)
# =============================================================================
def _card_archivo_pago(archivo: dict) -> rx.Component:
    """Card para mostrar un archivo de pago (prefactura/factura)."""
    return rx.hstack(
        rx.center(
            rx.icon("file-text", size=20, color=Colors.PRIMARY),
            width="40px",
            height="40px",
            background=Colors.PRIMARY_LIGHT,
            border_radius=Radius.MD,
        ),
        rx.vstack(
            rx.text(archivo["nombre"], size="2", weight="medium", no_of_lines=1),
            rx.hstack(
                rx.text(f"{archivo['tamanio_mb']} MB", size="1", color=Colors.TEXT_MUTED),
                rx.cond(
                    archivo["categoria"],
                    rx.badge(archivo["categoria"], size="1", variant="soft", color_scheme="gray"),
                    rx.fragment(),
                ),
                spacing="2",
            ),
            spacing="0",
            align="start",
        ),
        rx.spacer(),
        rx.button(
            rx.icon("download", size=14),
            "Descargar",
            size="1",
            variant="soft",
            on_click=EntregableDetalleState.descargar_archivo_pago(archivo["id"]),
        ),
        padding=Spacing.SM,
        border=f"1px solid {Colors.BORDER}",
        border_radius=Radius.MD,
        width="100%",
        align="center",
    )


def _seccion_prefactura() -> rx.Component:
    """Sección visible cuando hay prefactura enviada (PREFACTURA_ENVIADA)."""
    return rx.cond(
        EntregableDetalleState.puede_revisar_prefactura,
        rx.card(
            rx.vstack(
                rx.hstack(
                    rx.icon("file-search", size=20, color=Colors.INFO),
                    rx.text("Prefactura Recibida", size="4", weight="bold"),
                    rx.spacer(),
                    rx.badge("Pendiente de revisión", color_scheme="sky", size="2"),
                    align="center",
                    width="100%",
                ),
                rx.divider(),
                rx.callout(
                    "Revise la prefactura y apruébela o rechácela. Si la aprueba, el cliente podrá subir la factura definitiva.",
                    icon="info",
                    color_scheme="blue",
                ),
                # Archivos de la prefactura
                rx.cond(
                    EntregableDetalleState.tiene_archivos_pago,
                    rx.vstack(
                        rx.text("Archivos", size="2", weight="medium", color=Colors.TEXT_SECONDARY),
                        rx.foreach(EntregableDetalleState.archivos_pago, _card_archivo_pago),
                        spacing="2",
                        width="100%",
                    ),
                    rx.text("No se encontraron archivos adjuntos", size="2", color=Colors.TEXT_MUTED),
                ),
                # Info del monto
                rx.hstack(
                    rx.text("Monto aprobado:", size="2", color=Colors.TEXT_MUTED),
                    rx.text(f"${EntregableDetalleState.monto_aprobado_texto}", size="2", weight="bold"),
                    spacing="2",
                ),
                spacing="4",
                width="100%",
            ),
            padding="5",
            border=f"2px solid {Colors.INFO}",
        ),
        rx.fragment(),
    )


def _seccion_facturado() -> rx.Component:
    """Sección visible cuando hay factura enviada (FACTURADO)."""
    return rx.cond(
        EntregableDetalleState.es_facturado,
        rx.card(
            rx.vstack(
                rx.hstack(
                    rx.icon("receipt", size=20, color=Colors.WARNING),
                    rx.text("Factura Recibida", size="4", weight="bold"),
                    rx.spacer(),
                    rx.badge("Pendiente de pago", color_scheme="amber", size="2"),
                    align="center",
                    width="100%",
                ),
                rx.divider(),
                # Datos CFDI
                rx.hstack(
                    rx.vstack(
                        rx.text("Folio Fiscal", size="1", color=Colors.TEXT_MUTED),
                        rx.text(EntregableDetalleState.folio_fiscal_entregable, size="2", weight="medium"),
                        spacing="0",
                    ),
                    rx.vstack(
                        rx.text("Monto Aprobado", size="1", color=Colors.TEXT_MUTED),
                        rx.text(f"${EntregableDetalleState.monto_aprobado_texto}", size="2", weight="bold", color=Colors.PRIMARY),
                        spacing="0",
                    ),
                    spacing="6",
                ),
                # Archivos de factura
                rx.cond(
                    EntregableDetalleState.tiene_archivos_pago,
                    rx.vstack(
                        rx.text("Archivos de Factura", size="2", weight="medium", color=Colors.TEXT_SECONDARY),
                        rx.foreach(EntregableDetalleState.archivos_pago, _card_archivo_pago),
                        spacing="2",
                        width="100%",
                    ),
                    rx.fragment(),
                ),
                spacing="4",
                width="100%",
            ),
            padding="5",
            border=f"2px solid {Colors.WARNING}",
        ),
        rx.fragment(),
    )


def _seccion_pagado() -> rx.Component:
    """Sección visible cuando el entregable está pagado (PAGADO)."""
    return rx.cond(
        EntregableDetalleState.es_pagado,
        rx.card(
            rx.vstack(
                rx.hstack(
                    rx.icon("badge-check", size=20, color=Colors.SUCCESS),
                    rx.text("Pago Registrado", size="4", weight="bold"),
                    rx.spacer(),
                    rx.badge("Completado", color_scheme="green", size="2"),
                    align="center",
                    width="100%",
                ),
                rx.divider(),
                rx.hstack(
                    rx.vstack(
                        rx.text("Folio Fiscal", size="1", color=Colors.TEXT_MUTED),
                        rx.text(EntregableDetalleState.folio_fiscal_entregable, size="2", weight="medium"),
                        spacing="0",
                    ),
                    rx.vstack(
                        rx.text("Monto", size="1", color=Colors.TEXT_MUTED),
                        rx.text(f"${EntregableDetalleState.monto_aprobado_texto}", size="2", weight="bold", color=Colors.SUCCESS),
                        spacing="0",
                    ),
                    rx.cond(
                        EntregableDetalleState.referencia_pago_entregable != "",
                        rx.vstack(
                            rx.text("Referencia", size="1", color=Colors.TEXT_MUTED),
                            rx.text(EntregableDetalleState.referencia_pago_entregable, size="2", weight="medium"),
                            spacing="0",
                        ),
                        rx.fragment(),
                    ),
                    spacing="6",
                ),
                # Archivos
                rx.cond(
                    EntregableDetalleState.tiene_archivos_pago,
                    rx.vstack(
                        rx.text("Archivos", size="2", weight="medium", color=Colors.TEXT_SECONDARY),
                        rx.foreach(EntregableDetalleState.archivos_pago, _card_archivo_pago),
                        spacing="2",
                        width="100%",
                    ),
                    rx.fragment(),
                ),
                spacing="4",
                width="100%",
            ),
            padding="5",
            border=f"2px solid {Colors.SUCCESS}",
        ),
        rx.fragment(),
    )


def _seccion_observaciones_prefactura() -> rx.Component:
    """Muestra observaciones de prefactura rechazada."""
    return rx.cond(
        EntregableDetalleState.observaciones_prefactura_texto != "",
        rx.callout(
            rx.vstack(
                rx.text("Observaciones de Prefactura", weight="bold", size="2"),
                rx.text(EntregableDetalleState.observaciones_prefactura_texto),
                spacing="1",
            ),
            icon="file-x",
            color_scheme="orange",
            width="100%",
        ),
        rx.fragment(),
    )


# =============================================================================
# MODALES
# =============================================================================
def _modal_rechazar_prefactura() -> rx.Component:
    """Modal para rechazar prefactura con observaciones."""
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title("Rechazar Prefactura"),
            rx.dialog.description(
                rx.vstack(
                    rx.callout(
                        "El cliente podrá corregir y volver a enviar la prefactura.",
                        icon="info",
                        color_scheme="blue",
                    ),
                    form_textarea(
                        label="Observaciones",
                        required=True,
                        placeholder="Indique el motivo del rechazo y qué debe corregir...",
                        value=EntregableDetalleState.observaciones_prefactura,
                        on_change=EntregableDetalleState.set_observaciones_prefactura,
                        on_blur=EntregableDetalleState.validar_observaciones_prefactura,
                        error=EntregableDetalleState.error_observaciones_prefactura,
                        min_height="120px",
                    ),
                    spacing="3",
                    width="100%",
                ),
            ),
            rx.hstack(
                rx.button(
                    "Cancelar",
                    variant="soft",
                    color_scheme="gray",
                    on_click=EntregableDetalleState.cerrar_modal_rechazar_prefactura,
                ),
                rx.button(
                    "Rechazar Prefactura",
                    background=Colors.ERROR,
                    color=Colors.TEXT_INVERSE,
                    _hover={"background": Colors.ERROR_HOVER},
                    on_click=EntregableDetalleState.confirmar_rechazo_prefactura,
                    loading=EntregableDetalleState.procesando,
                    disabled=~EntregableDetalleState.puede_guardar_rechazo_prefactura,
                ),
                spacing="3",
                justify="end",
                margin_top="4",
            ),
            max_width="500px",
        ),
        open=EntregableDetalleState.mostrar_modal_rechazar_prefactura,
        on_open_change=rx.noop,
    )


def _modal_registrar_pago() -> rx.Component:
    """Modal para registrar pago de un entregable facturado."""
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title("Registrar Pago"),
            rx.dialog.description(
                rx.vstack(
                    rx.hstack(
                        rx.vstack(
                            rx.text("Contrato", size="1", color=Colors.TEXT_MUTED),
                            rx.text(EntregableDetalleState.contrato_info["codigo"], size="2", weight="medium"),
                            spacing="0",
                        ),
                        rx.vstack(
                            rx.text("Monto facturado", size="1", color=Colors.TEXT_MUTED),
                            rx.text(f"${EntregableDetalleState.monto_aprobado_texto}", size="2", weight="bold", color=Colors.PRIMARY),
                            spacing="0",
                        ),
                        spacing="6",
                    ),
                    rx.cond(
                        EntregableDetalleState.folio_fiscal_entregable != "",
                        rx.hstack(
                            rx.text("Folio fiscal:", size="2", color=Colors.TEXT_MUTED),
                            rx.text(EntregableDetalleState.folio_fiscal_entregable, size="2", weight="medium"),
                            spacing="2",
                        ),
                        rx.fragment(),
                    ),
                    rx.divider(margin_y="2"),
                    form_date(
                        label="Fecha de pago",
                        required=True,
                        value=EntregableDetalleState.fecha_pago,
                        on_change=EntregableDetalleState.set_fecha_pago,
                        error=EntregableDetalleState.error_fecha_pago,
                    ),
                    form_input(
                        label="Referencia",
                        placeholder="Ej: Transferencia SPEI, Cheque #1234...",
                        value=EntregableDetalleState.referencia_pago,
                        on_change=EntregableDetalleState.set_referencia_pago,
                        hint="Opcional. Referencia bancaria o número de cheque.",
                    ),
                    spacing="3",
                    width="100%",
                ),
            ),
            rx.hstack(
                rx.button(
                    "Cancelar",
                    variant="soft",
                    color_scheme="gray",
                    on_click=EntregableDetalleState.cerrar_modal_registrar_pago,
                ),
                rx.button(
                    "Confirmar Pago",
                    background=Colors.PRIMARY,
                    color=Colors.TEXT_INVERSE,
                    _hover={"background": Colors.PRIMARY_HOVER},
                    on_click=EntregableDetalleState.confirmar_registrar_pago,
                    loading=EntregableDetalleState.procesando,
                    disabled=~EntregableDetalleState.puede_guardar_pago,
                ),
                spacing="3",
                justify="end",
                margin_top="4",
            ),
            max_width="450px",
        ),
        open=EntregableDetalleState.mostrar_modal_registrar_pago,
        on_open_change=rx.noop,
    )


def _modal_aprobar() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title("Aprobar Entregable"),
            rx.dialog.description(
                rx.vstack(
                    rx.text(f"Aprobar el período {EntregableDetalleState.numero_periodo}", size="2"),
                    rx.text(EntregableDetalleState.periodo_texto, size="2", color=Colors.TEXT_MUTED),
                    rx.divider(margin_y="3"),
                    form_input(
                        label="Monto a aprobar",
                        required=True,
                        placeholder="Ej: 85000.00",
                        value=EntregableDetalleState.monto_a_aprobar,
                        on_change=EntregableDetalleState.set_monto_a_aprobar,
                        on_blur=EntregableDetalleState.validar_monto,
                        error=EntregableDetalleState.error_monto,
                        hint=f"Monto calculado: ${EntregableDetalleState.monto_calculado_total}",
                    ),
                    spacing="3",
                    width="100%",
                ),
            ),
            rx.hstack(
                rx.button(
                    "Cancelar",
                    variant="soft",
                    color_scheme="gray",
                    on_click=EntregableDetalleState.cerrar_modal_aprobar,
                ),
                rx.button(
                    "Aprobar",
                    background=Colors.PRIMARY,
                    color=Colors.TEXT_INVERSE,
                    _hover={"background": Colors.PRIMARY_HOVER},
                    on_click=EntregableDetalleState.confirmar_aprobacion,
                    loading=EntregableDetalleState.procesando,
                    disabled=~EntregableDetalleState.puede_guardar_aprobacion,
                ),
                spacing="3",
                justify="end",
                margin_top="4",
            ),
            max_width="450px",
        ),
        open=EntregableDetalleState.mostrar_modal_aprobar,
        # No cerrar al hacer click fuera - solo con botones
        on_open_change=rx.noop,
    )


def _modal_rechazar() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title("Rechazar Entregable"),
            rx.dialog.description(
                rx.vstack(
                    rx.callout(
                        "El cliente podrá corregir y volver a enviar el entregable.",
                        icon="info",
                        color_scheme="blue",
                    ),
                    form_textarea(
                        label="Observaciones",
                        required=True,
                        placeholder="Indique el motivo del rechazo y qué debe corregir el cliente...",
                        value=EntregableDetalleState.observaciones_rechazo,
                        on_change=EntregableDetalleState.set_observaciones_rechazo,
                        on_blur=EntregableDetalleState.validar_observaciones,
                        error=EntregableDetalleState.error_observaciones,
                        min_height="120px",
                    ),
                    spacing="3",
                    width="100%",
                ),
            ),
            rx.hstack(
                rx.button(
                    "Cancelar",
                    variant="soft",
                    color_scheme="gray",
                    on_click=EntregableDetalleState.cerrar_modal_rechazar,
                ),
                rx.button(
                    "Rechazar",
                    background=Colors.ERROR,
                    color=Colors.TEXT_INVERSE,
                    _hover={"background": Colors.ERROR_HOVER},
                    on_click=EntregableDetalleState.confirmar_rechazo,
                    loading=EntregableDetalleState.procesando,
                    disabled=~EntregableDetalleState.puede_guardar_rechazo,
                ),
                spacing="3",
                justify="end",
                margin_top="4",
            ),
            max_width="500px",
        ),
        open=EntregableDetalleState.mostrar_modal_rechazar,
        # No cerrar al hacer click fuera - solo con botones
        on_open_change=rx.noop,
    )


# =============================================================================
# GALERÍA DE IMÁGENES
# =============================================================================
def _modal_galeria() -> rx.Component:
    """Modal para visualizar imágenes en tamaño completo."""
    return rx.dialog.root(
        rx.dialog.content(
            rx.vstack(
                rx.hstack(
                    rx.text("Vista previa", size="4", weight="bold"),
                    rx.spacer(),
                    rx.icon_button(
                        rx.icon("x", size=20),
                        variant="ghost",
                        on_click=EntregableDetalleState.cerrar_galeria,
                    ),
                    width="100%",
                    align="center",
                ),
                rx.center(
                    rx.image(
                        src=EntregableDetalleState.imagen_seleccionada,
                        max_width="100%",
                        max_height="70vh",
                        object_fit="contain",
                        border_radius=Radius.MD,
                    ),
                    width="100%",
                    padding=Spacing.MD,
                ),
                rx.hstack(
                    rx.link(
                        rx.button(
                            rx.icon("external-link", size=14),
                            "Abrir en nueva pestaña",
                            variant="soft",
                            size="2",
                        ),
                        href=EntregableDetalleState.imagen_seleccionada,
                        is_external=True,
                    ),
                    rx.button(
                        "Cerrar",
                        variant="outline",
                        size="2",
                        on_click=EntregableDetalleState.cerrar_galeria,
                    ),
                    spacing="3",
                    justify="end",
                    width="100%",
                ),
                spacing="4",
                width="100%",
            ),
            max_width="90vw",
            padding="4",
        ),
        open=EntregableDetalleState.mostrar_galeria,
        # No cerrar al hacer click fuera - solo con botones
        on_open_change=rx.noop,
    )


# =============================================================================
# PÁGINA
# =============================================================================
def _contenido_detalle() -> rx.Component:
    return rx.vstack(
        _breadcrumb(),
        _header_entregable(),
        _seccion_observaciones_rechazo(),
        _seccion_observaciones_prefactura(),
        # Secciones de facturación (se muestran según estatus)
        _seccion_prefactura(),
        _seccion_facturado(),
        _seccion_pagado(),
        rx.grid(
            _seccion_archivos(),
            _seccion_detalle_personal(),
            columns="2",
            spacing="4",
            width="100%",
        ),
        # Modales
        _modal_aprobar(),
        _modal_rechazar(),
        _modal_rechazar_prefactura(),
        _modal_registrar_pago(),
        _modal_galeria(),
        spacing="4",
        width="100%",
    )


def entregable_detalle_page() -> rx.Component:
    return rx.box(
        page_layout(
            content=rx.cond(
                EntregableDetalleState.loading,
                rx.center(rx.spinner(size="3"), padding="12"),
                rx.cond(
                    EntregableDetalleState.tiene_entregable,
                    _contenido_detalle(),
                    rx.center(rx.text("Entregable no encontrado", color=Colors.TEXT_MUTED), padding="12"),
                ),
            ),
        ),
        on_mount=EntregableDetalleState.on_mount_detalle,
    )
