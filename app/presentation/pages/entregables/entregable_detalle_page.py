"""
Página de Detalle de Entregable (Admin).
Permite ver archivos, detalle de personal, y aprobar/rechazar.
"""

import reflex as rx

from app.presentation.pages.entregables.entregable_detalle_state import EntregableDetalleState
from app.presentation.layout import page_layout
from app.presentation.components.ui import status_badge_reactive, form_input, form_textarea
from app.presentation.theme import Colors, Spacing, Typography, Radius, Shadows


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
            rx.cond(
                EntregableDetalleState.puede_revisar,
                rx.hstack(
                    rx.button(
                        rx.icon("circle-x", size=16),
                        "Rechazar",
                        color_scheme="red",
                        variant="outline",
                        on_click=EntregableDetalleState.abrir_modal_rechazar,
                    ),
                    rx.button(
                        rx.icon("circle-check", size=16),
                        "Aprobar",
                        color_scheme="green",
                        on_click=EntregableDetalleState.abrir_modal_aprobar,
                    ),
                    spacing="2",
                ),
                rx.cond(
                    EntregableDetalleState.estatus_actual == "APROBADO",
                    rx.badge(rx.icon("check", size=12), "Ya aprobado", color_scheme="green", size="2"),
                    rx.cond(
                        EntregableDetalleState.estatus_actual == "RECHAZADO",
                        rx.badge(rx.icon("x", size=12), "Rechazado", color_scheme="red", size="2"),
                        rx.badge("Pendiente de entrega", color_scheme="gray", size="2"),
                    ),
                ),
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
                    color=Colors.SUCCESS,
                ),
                align="center",
                width="100%",
            ),
            rx.divider(),
            rx.cond(
                EntregableDetalleState.tiene_detalle_personal,
                rx.box(
                    rx.table.root(
                        rx.table.header(
                            rx.table.row(
                                rx.table.column_header_cell("Categoría"),
                                rx.table.column_header_cell("Reportado"),
                                rx.table.column_header_cell("Validado"),
                                rx.table.column_header_cell("Rango"),
                                rx.table.column_header_cell("Tarifa"),
                                rx.table.column_header_cell("Subtotal"),
                            ),
                        ),
                        rx.table.body(
                            rx.foreach(EntregableDetalleState.detalle_personal, _fila_detalle_personal),
                        ),
                        width="100%",
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
# MODALES
# =============================================================================
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
                    color_scheme="green",
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
                    color_scheme="red",
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
        rx.grid(
            _seccion_archivos(),
            _seccion_detalle_personal(),
            columns="2",
            spacing="4",
            width="100%",
        ),
        _modal_aprobar(),
        _modal_rechazar(),
        _modal_galeria(),
        spacing="4",
        width="100%",
    )


def entregable_detalle_page() -> rx.Component:
    return rx.box(
        page_layout(
            content=rx.cond(
                EntregableDetalleState.cargando,
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
