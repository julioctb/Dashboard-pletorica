"""Componentes UI para la página dedicada de expediente de empleados."""

import reflex as rx

from app.presentation.components.ui import (
    breadcrumb_dynamic,
    document_status_badge,
    form_textarea,
    metric_card,
    modal_formulario,
    tabla_action_button,
    tabla_cta_button,
)
from app.presentation.theme import Colors, Radius, Spacing, Typography

from .state import ExpedientesState, UPLOAD_ID_EXPEDIENTE


ENCABEZADOS_DOCUMENTOS = [
    {"nombre": "Documento", "ancho": "35%", "header_align": "left"},
    {"nombre": "Archivo", "ancho": "auto", "header_align": "left"},
    {"nombre": "Ver.", "ancho": "60px", "header_align": "center"},
    {"nombre": "Estatus", "ancho": "100px", "header_align": "center"},
    {"nombre": "Acciones", "ancho": "100px", "header_align": "center"},
]


def _seccion_header(
    titulo: str,
    badge_text: rx.Var | str,
    badge_scheme: str,
    *,
    border_top: bool = False,
) -> rx.Component:
    return rx.flex(
        rx.text(
            titulo,
            font_size=Typography.SIZE_XS,
            font_weight=Typography.WEIGHT_MEDIUM,
            color=Colors.TEXT_SECONDARY,
            text_transform="uppercase",
            letter_spacing="0.04em",
        ),
        rx.badge(
            badge_text,
            color_scheme=badge_scheme,
            variant="soft",
            size="1",
        ),
        justify="between",
        align="center",
        width="100%",
        padding_x=Spacing.LG,
        padding_y=Spacing.MD,
        border_top=f"1px solid {Colors.BORDER}" if border_top else "none",
        border_bottom=f"1px solid {Colors.BORDER}",
    )


def _header_cells_documentos() -> list[rx.Component]:
    return [
        rx.table.column_header_cell(
            rx.text(
                col["nombre"],
                font_size=Typography.SIZE_XS,
                font_weight=Typography.WEIGHT_MEDIUM,
                color=Colors.TEXT_SECONDARY,
                text_transform="uppercase",
                letter_spacing="0.04em",
            ),
            width=col.get("ancho", "auto"),
            text_align=col.get("header_align", "left"),
        )
        for col in ENCABEZADOS_DOCUMENTOS
    ]


def _archivo_cell(doc: dict) -> rx.Component:
    return rx.cond(
        doc.get("subido", False),
        rx.button(
            doc.get("nombre_archivo", "Documento"),
            on_click=ExpedientesState.ver_documento(doc),
            variant="ghost",
            size="1",
            color_scheme=Colors.NEUTRAL_SCHEME,
            justify="start",
            padding="0",
            height="auto",
            text_align="left",
        ),
        rx.text(
            "—",
            color=Colors.TEXT_MUTED,
            font_size=Typography.SIZE_SM,
        ),
    )


def _acciones_documento(doc: dict, *, obligatorio: bool) -> rx.Component:
    color_subir = Colors.PORTAL_ACCENT_SCHEME if obligatorio else Colors.NEUTRAL_SCHEME
    es_pendiente = doc.get("estatus", "") == "PENDIENTE_REVISION"

    return rx.cond(
        doc.get("subido", False),
        rx.hstack(
            tabla_action_button(
                icon="eye",
                tooltip="Ver archivo",
                on_click=ExpedientesState.ver_documento(doc),
                color_scheme=Colors.NEUTRAL_SCHEME,
            ),
            tabla_action_button(
                icon="download",
                tooltip="Descargar",
                on_click=ExpedientesState.descargar_documento(doc),
                color_scheme=Colors.NEUTRAL_SCHEME,
            ),
            rx.cond(
                es_pendiente,
                tabla_cta_button(
                    text="Aprobar",
                    on_click=ExpedientesState.aprobar_documento(doc),
                    color_scheme="green",
                    variant="soft",
                    size="1",
                ),
                rx.fragment(),
            ),
            rx.cond(
                es_pendiente,
                tabla_cta_button(
                    text="Rechazar",
                    on_click=ExpedientesState.abrir_modal_rechazo(doc),
                    color_scheme="red",
                    variant="soft",
                    size="1",
                ),
                rx.fragment(),
            ),
            spacing="1",
            align="center",
            justify="center",
            wrap="wrap",
        ),
        tabla_cta_button(
            text="Subir",
            on_click=ExpedientesState.abrir_subir(doc.get("tipo_documento", "")),
            color_scheme=color_subir,
            variant="outline",
            size="1",
        ),
    )


def _fila_documento(doc: dict, *, obligatorio: bool) -> rx.Component:
    return rx.table.row(
        rx.table.cell(
            rx.text(
                doc.get("tipo_documento_label", "Documento"),
                font_size=Typography.SIZE_SM,
                font_weight=Typography.WEIGHT_MEDIUM,
                color=Colors.TEXT_PRIMARY,
            ),
        ),
        rx.table.cell(_archivo_cell(doc)),
        rx.table.cell(
            rx.cond(
                doc.get("subido", False),
                rx.text(
                    doc.get("version_texto", "—"),
                    font_size=Typography.SIZE_SM,
                    color=Colors.TEXT_SECONDARY,
                    text_align="center",
                    width="100%",
                ),
                rx.text(
                    "—",
                    font_size=Typography.SIZE_SM,
                    color=Colors.TEXT_MUTED,
                    text_align="center",
                    width="100%",
                ),
            ),
        ),
        rx.table.cell(
            rx.center(
                document_status_badge(
                    doc.get("estatus", ""),
                    missing_label="Sin subir",
                ),
                width="100%",
            ),
        ),
        rx.table.cell(
            rx.center(
                _acciones_documento(doc, obligatorio=obligatorio),
                width="100%",
            )
        ),
    )


def _tabla_documentos(
    documentos,
    *,
    obligatorio: bool,
    empty_text: str,
) -> rx.Component:
    return rx.table.root(
        rx.table.header(
            rx.table.row(*_header_cells_documentos()),
        ),
        rx.table.body(
            rx.cond(
                documentos.length() > 0,
                rx.foreach(
                    documentos,
                    lambda doc: _fila_documento(doc, obligatorio=obligatorio),
                ),
                rx.table.row(
                    rx.table.cell(
                        rx.text(
                            empty_text,
                            color=Colors.TEXT_MUTED,
                            font_size=Typography.SIZE_SM,
                            text_align="center",
                        ),
                        col_span=5,
                    ),
                ),
            ),
        ),
        width="100%",
        variant="surface",
    )


def _breadcrumb() -> rx.Component:
    return rx.box(
        breadcrumb_dynamic(items=ExpedientesState.breadcrumb_items),
        width="100%",
    )


def _page_header() -> rx.Component:
    return rx.flex(
        rx.hstack(
            rx.center(
                rx.text(
                    ExpedientesState.iniciales_empleado,
                    font_size=Typography.SIZE_SM,
                    font_weight=Typography.WEIGHT_SEMIBOLD,
                    color=Colors.TEXT_SECONDARY,
                ),
                width="48px",
                height="48px",
                border_radius=Radius.FULL,
                background=Colors.SECONDARY_LIGHT,
                border=f"1px solid {Colors.BORDER}",
                flex_shrink="0",
            ),
            rx.vstack(
                rx.text(
                    "Expediente documental",
                    font_size=Typography.SIZE_3XL,
                    font_weight=Typography.WEIGHT_SEMIBOLD,
                    color=Colors.TEXT_PRIMARY,
                    line_height=Typography.LINE_HEIGHT_TIGHT,
                ),
                rx.hstack(
                    rx.text(
                        ExpedientesState.nombre_empleado_ui,
                        font_size=Typography.SIZE_SM,
                        color=Colors.TEXT_SECONDARY,
                    ),
                    rx.cond(
                        ExpedientesState.clave_empleado != "",
                        rx.badge(
                            ExpedientesState.clave_empleado,
                            color_scheme=Colors.NEUTRAL_SCHEME,
                            variant="outline",
                            size="2",
                        ),
                        rx.fragment(),
                    ),
                    rx.badge(
                        ExpedientesState.estatus_empleado_label,
                        color_scheme=Colors.PORTAL_ACCENT_SCHEME,
                        variant="soft",
                        size="2",
                    ),
                    spacing="2",
                    align="center",
                    wrap="wrap",
                ),
                spacing="1",
                align="start",
            ),
            spacing="3",
            align="center",
        ),
        rx.button(
            rx.icon("upload", size=16),
            "Subir documento",
            color_scheme=Colors.PORTAL_ACCENT_SCHEME,
            size="2",
            on_click=ExpedientesState.abrir_modal_subir,
        ),
        justify="between",
        align="center",
        wrap="wrap",
        width="100%",
        row_gap=Spacing.MD,
        margin_bottom=Spacing.SM,
    )


def _metricas() -> rx.Component:
    return rx.grid(
        metric_card(
            titulo="Requeridos",
            valor=ExpedientesState.total_requeridos,
            icono=None,
            show_icon=False,
            align="left",
            color_scheme=Colors.NEUTRAL_SCHEME,
            background=Colors.SECONDARY_LIGHT,
            border="none",
            hoverable=False,
        ),
        metric_card(
            titulo="Aprobados",
            valor=ExpedientesState.total_aprobados,
            icono=None,
            show_icon=False,
            align="left",
            value_color=Colors.SUCCESS,
            background=Colors.SECONDARY_LIGHT,
            border="none",
            hoverable=False,
        ),
        metric_card(
            titulo="Pendientes",
            valor=ExpedientesState.total_pendientes,
            icono=None,
            show_icon=False,
            align="left",
            value_color=Colors.WARNING,
            background=Colors.SECONDARY_LIGHT,
            border="none",
            hoverable=False,
        ),
        metric_card(
            titulo="Rechazados",
            valor=ExpedientesState.total_rechazados,
            icono=None,
            show_icon=False,
            align="left",
            value_color=Colors.ERROR,
            background=Colors.SECONDARY_LIGHT,
            border="none",
            hoverable=False,
        ),
        columns=rx.breakpoints(initial="2", md="4"),
        spacing="3",
        width="100%",
    )


def _barra_progreso() -> rx.Component:
    return rx.box(
        rx.flex(
            rx.text(
                "Progreso del expediente",
                font_size=Typography.SIZE_SM,
                font_weight=Typography.WEIGHT_MEDIUM,
                color=Colors.TEXT_PRIMARY,
            ),
            rx.flex(
                rx.text(
                    ExpedientesState.total_aprobados.to(str)
                    + " de "
                    + ExpedientesState.total_requeridos.to(str)
                    + " documentos",
                    font_size=Typography.SIZE_XS,
                    color=Colors.TEXT_SECONDARY,
                ),
                rx.text(
                    ExpedientesState.progreso_porcentaje.to(str) + "%",
                    font_size=Typography.SIZE_XS,
                    font_weight=Typography.WEIGHT_MEDIUM,
                    color=Colors.TEXT_PRIMARY,
                ),
                align="center",
                spacing="2",
            ),
            justify="between",
            align="center",
            width="100%",
        ),
        rx.box(
            rx.box(
                width=ExpedientesState.progreso_porcentaje.to(str) + "%",
                height="100%",
                background=Colors.PORTAL_PRIMARY,
                border_radius=Radius.FULL,
            ),
            width="100%",
            height="6px",
            background=Colors.SECONDARY_LIGHT,
            border_radius=Radius.FULL,
            overflow="hidden",
            margin_top=Spacing.SM,
        ),
        width="100%",
        margin_bottom=Spacing.XL,
    )


def _tabla_documentos_seccionada() -> rx.Component:
    return rx.box(
        _seccion_header(
            "DOCUMENTOS OBLIGATORIOS",
            badge_text=ExpedientesState.total_documentos_obligatorios.to(str) + " requeridos",
            badge_scheme="amber",
        ),
        _tabla_documentos(
            ExpedientesState.documentos_obligatorios,
            obligatorio=True,
            empty_text="No hay documentos obligatorios configurados.",
        ),
        _seccion_header(
            "DOCUMENTOS OPCIONALES",
            badge_text=ExpedientesState.total_documentos_opcionales.to(str) + " opcionales",
            badge_scheme=Colors.NEUTRAL_SCHEME,
            border_top=True,
        ),
        _tabla_documentos(
            ExpedientesState.documentos_opcionales,
            obligatorio=False,
            empty_text="No hay documentos opcionales configurados.",
        ),
        background=Colors.SURFACE,
        border=f"1px solid {Colors.BORDER}",
        border_radius=Radius.LG,
        overflow="hidden",
        width="100%",
    )


def _loading_state() -> rx.Component:
    return rx.vstack(
        rx.skeleton(height="20px", width="260px"),
        rx.skeleton(height="56px", width="100%"),
        rx.grid(
            rx.skeleton(height="92px", width="100%"),
            rx.skeleton(height="92px", width="100%"),
            rx.skeleton(height="92px", width="100%"),
            rx.skeleton(height="92px", width="100%"),
            columns=rx.breakpoints(initial="2", md="4"),
            spacing="3",
            width="100%",
        ),
        rx.skeleton(height="30px", width="100%"),
        rx.skeleton(height="340px", width="100%"),
        spacing="4",
        width="100%",
    )


def detalle_expediente() -> rx.Component:
    """Vista principal de expediente de empleado."""
    return rx.box(
        rx.cond(
            ExpedientesState.loading,
            _loading_state(),
            rx.vstack(
                _breadcrumb(),
                _page_header(),
                _metricas(),
                _barra_progreso(),
                _tabla_documentos_seccionada(),
                spacing="4",
                width="100%",
            ),
        ),
        width="100%",
        padding_x=Spacing.PAGE_PADDING,
        padding_y=Spacing.XL,
    )


def modal_subir_documento() -> rx.Component:
    """Modal pequeño para seleccionar tipo y subir archivo."""
    return rx.dialog.root(
        rx.dialog.content(
            rx.vstack(
                rx.hstack(
                    rx.vstack(
                        rx.text(
                            "Subir documento",
                            font_size=Typography.SIZE_XL,
                            font_weight=Typography.WEIGHT_SEMIBOLD,
                        ),
                        rx.text(
                            "Seleccione el tipo de documento y cargue un archivo.",
                            font_size=Typography.SIZE_SM,
                            color=Colors.TEXT_SECONDARY,
                        ),
                        spacing="1",
                        align="start",
                    ),
                    rx.spacer(),
                    rx.icon_button(
                        rx.icon("x", size=18),
                        variant="ghost",
                        color_scheme=Colors.NEUTRAL_SCHEME,
                        on_click=ExpedientesState.cerrar_modal_subir,
                    ),
                    width="100%",
                    align="start",
                ),
                rx.vstack(
                    rx.box(
                        rx.text(
                            "Documento",
                            font_size=Typography.SIZE_SM,
                            font_weight=Typography.WEIGHT_MEDIUM,
                            color=Colors.TEXT_PRIMARY,
                            margin_bottom=Spacing.XS,
                        ),
                        rx.select.root(
                            rx.select.trigger(
                                placeholder="Seleccionar tipo de documento...",
                                width="100%",
                            ),
                            rx.select.content(
                                rx.foreach(
                                    ExpedientesState.tipos_documento_disponibles,
                                    lambda opt: rx.select.item(
                                        opt["label"],
                                        value=opt["value"],
                                    ),
                                ),
                            ),
                            value=ExpedientesState.tipo_documento_subiendo,
                            on_change=ExpedientesState.set_tipo_documento_subiendo,
                            size="2",
                            width="100%",
                        ),
                        width="100%",
                    ),
                    rx.cond(
                        ExpedientesState.tipo_documento_subiendo != "",
                        rx.upload(
                            rx.vstack(
                                rx.cond(
                                    ExpedientesState.subiendo_archivo,
                                    rx.spinner(size="2"),
                                    rx.icon(
                                        "cloud-upload",
                                        size=30,
                                        color=Colors.TEXT_SECONDARY,
                                    ),
                                ),
                                rx.text(
                                    "Arrastre un archivo o haga clic para seleccionar",
                                    font_size=Typography.SIZE_SM,
                                    color=Colors.TEXT_SECONDARY,
                                ),
                                rx.text(
                                    "PDF, PNG o JPG (máximo 1 archivo)",
                                    font_size=Typography.SIZE_XS,
                                    color=Colors.TEXT_MUTED,
                                ),
                                spacing="2",
                                align="center",
                                width="100%",
                                padding_y=Spacing.XL,
                            ),
                            id=UPLOAD_ID_EXPEDIENTE,
                            accept={
                                "application/pdf": [".pdf"],
                                "image/png": [".png"],
                                "image/jpeg": [".jpg", ".jpeg"],
                            },
                            max_files=1,
                            on_drop=ExpedientesState.handle_upload_documento(
                                rx.upload_files(upload_id=UPLOAD_ID_EXPEDIENTE),
                            ),
                            border=f"1px dashed {Colors.BORDER_STRONG}",
                            border_radius=Radius.LG,
                            background=Colors.SECONDARY_LIGHT,
                            width="100%",
                            cursor="pointer",
                        ),
                        rx.callout.root(
                            rx.callout.icon(rx.icon("info", size=16)),
                            rx.callout.text("Seleccione primero el tipo de documento."),
                            color_scheme=Colors.NEUTRAL_SCHEME,
                            variant="soft",
                            width="100%",
                        ),
                    ),
                    spacing="3",
                    width="100%",
                ),
                rx.hstack(
                    rx.spacer(),
                    rx.button(
                        "Cerrar",
                        variant="outline",
                        color_scheme=Colors.NEUTRAL_SCHEME,
                        on_click=ExpedientesState.cerrar_modal_subir,
                    ),
                    spacing="2",
                    width="100%",
                    align="center",
                ),
                spacing="4",
                width="100%",
            ),
            max_width="520px",
            width="min(96vw, 520px)",
            padding=Spacing.LG,
        ),
        open=ExpedientesState.mostrar_modal_subir,
        on_open_change=ExpedientesState.set_mostrar_modal_subir,
    )


def modal_rechazo() -> rx.Component:
    """Modal para ingresar observación de rechazo."""
    return modal_formulario(
        open=ExpedientesState.mostrar_modal_rechazo,
        titulo="Rechazar documento",
        descripcion="Ingrese el motivo del rechazo. El empleado podrá ver esta observación.",
        icono="circle-x",
        color_icono="red",
        color_guardar="red",
        texto_guardar="Rechazar",
        texto_guardando="Rechazando...",
        on_guardar=ExpedientesState.confirmar_rechazo,
        on_cancelar=ExpedientesState.cerrar_modal_rechazo,
        loading=ExpedientesState.saving,
        max_width="500px",
        contenido=rx.vstack(
            form_textarea(
                label="Observación",
                required=True,
                value=ExpedientesState.form_observacion_rechazo,
                on_change=ExpedientesState.set_form_observacion_rechazo,
                placeholder="Describa el motivo del rechazo (mín. 5 caracteres)...",
                error=ExpedientesState.error_observacion,
                label_variant="portal",
                style_variant="portal",
                rows="4",
            ),
            spacing="4",
            width="100%",
        ),
    )


def modal_preview_documento() -> rx.Component:
    """Modal para vista previa de documentos del expediente."""
    return rx.dialog.root(
        rx.dialog.content(
            rx.vstack(
                rx.hstack(
                    rx.vstack(
                        rx.text(
                            "Vista previa",
                            font_size=Typography.SIZE_XL,
                            font_weight=Typography.WEIGHT_SEMIBOLD,
                        ),
                        rx.text(
                            ExpedientesState.preview_nombre_archivo,
                            font_size=Typography.SIZE_SM,
                            color=Colors.TEXT_SECONDARY,
                        ),
                        spacing="0",
                        align="start",
                    ),
                    rx.spacer(),
                    rx.icon_button(
                        rx.icon("x", size=20),
                        variant="ghost",
                        color_scheme=Colors.NEUTRAL_SCHEME,
                        on_click=ExpedientesState.cerrar_modal_preview,
                    ),
                    width="100%",
                    align="center",
                ),
                rx.cond(
                    ExpedientesState.preview_es_imagen,
                    rx.center(
                        rx.image(
                            src=ExpedientesState.preview_url,
                            max_width="100%",
                            max_height="70vh",
                            object_fit="contain",
                            border_radius=Radius.MD,
                        ),
                        width="100%",
                        padding=Spacing.MD,
                    ),
                    rx.cond(
                        ExpedientesState.preview_es_pdf,
                        rx.el.iframe(
                            src=ExpedientesState.preview_url,
                            width="100%",
                            height="70vh",
                            style={
                                "border": f"1px solid {Colors.BORDER}",
                                "borderRadius": Radius.LG,
                                "background": Colors.SURFACE,
                            },
                        ),
                        rx.center(
                            rx.vstack(
                                rx.icon("file-text", size=40, color=Colors.TEXT_MUTED),
                                rx.text(
                                    "No hay vista previa embebida para este archivo.",
                                    font_size=Typography.SIZE_SM,
                                    color=Colors.TEXT_SECONDARY,
                                ),
                                spacing="2",
                                padding=Spacing.XL,
                            ),
                            width="100%",
                        ),
                    ),
                ),
                rx.hstack(
                    rx.link(
                        rx.button(
                            rx.icon("external-link", size=14),
                            "Abrir en nueva pestaña",
                            variant="soft",
                            size="2",
                            color_scheme=Colors.NEUTRAL_SCHEME,
                        ),
                        href=ExpedientesState.preview_url,
                        is_external=True,
                    ),
                    rx.button(
                        "Cerrar",
                        variant="outline",
                        size="2",
                        color_scheme=Colors.NEUTRAL_SCHEME,
                        on_click=ExpedientesState.cerrar_modal_preview,
                    ),
                    justify="end",
                    width="100%",
                    spacing="2",
                    wrap="wrap",
                ),
                spacing="4",
                width="100%",
            ),
            max_width="960px",
            width="min(96vw, 960px)",
        ),
        open=ExpedientesState.mostrar_modal_preview,
        on_open_change=rx.noop,
    )
