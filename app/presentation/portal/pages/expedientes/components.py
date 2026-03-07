"""
Componentes UI para el detalle de expediente del portal.
"""
import reflex as rx

from app.presentation.components.reusable import (
    document_table_shell,
    documento_observacion,
    documento_requerido_badge,
    documento_subido_icon,
)
from app.presentation.components.ui import (
    boton_cancelar,
    boton_guardar,
    document_status_badge,
    tabla_action_button,
)
from app.presentation.theme import Colors, Radius, Spacing, Typography

from .state import ExpedientesState

UPLOAD_ID_EXPEDIENTE = "upload_doc_expediente_rrhh"


def badge_documento(estatus: str) -> rx.Component:
    """Badge de estatus de documento."""
    return document_status_badge(estatus)


def fila_documento(doc: dict) -> rx.Component:
    """Fila de documento en el detalle del expediente."""
    es_pendiente = doc.get("estatus", "") == "PENDIENTE_REVISION"

    return rx.table.row(
        rx.table.cell(
            rx.hstack(
                documento_subido_icon(doc.get("subido", False)),
                rx.vstack(
                    rx.text(
                        doc.get("tipo_documento_label", doc.get("tipo_documento", "")),
                        font_size=Typography.SIZE_SM,
                        font_weight=Typography.WEIGHT_MEDIUM,
                    ),
                    documento_requerido_badge(doc.get("obligatorio", False)),
                    spacing="1",
                    align="start",
                ),
                spacing="2",
                align="center",
            ),
        ),
        rx.table.cell(
            rx.cond(
                doc.get("subido", False),
                rx.button(
                    doc.get("nombre_archivo", "-"),
                    on_click=ExpedientesState.ver_documento(doc),
                    variant="ghost",
                    size="1",
                    color_scheme="blue",
                    justify="start",
                    padding="0",
                    height="auto",
                    text_align="left",
                ),
                rx.text(
                    "-",
                    font_size=Typography.SIZE_SM,
                    color=Colors.TEXT_SECONDARY,
                ),
            ),
        ),
        rx.table.cell(
            rx.cond(
                doc.get("subido", False),
                rx.text(
                    f"v{doc.get('version', 1)}",
                    font_size=Typography.SIZE_SM,
                    color=Colors.TEXT_SECONDARY,
                ),
                rx.text(
                    "-",
                    font_size=Typography.SIZE_SM,
                    color=Colors.TEXT_SECONDARY,
                ),
            ),
        ),
        rx.table.cell(
            badge_documento(doc.get("estatus", "")),
        ),
        rx.table.cell(
            documento_observacion(doc.get("observacion_rechazo", ""), mode="tooltip"),
        ),
        rx.table.cell(
            rx.cond(
                doc.get("subido", False),
                rx.hstack(
                    tabla_action_button(
                        icon="eye",
                        tooltip="Ver archivo",
                        on_click=ExpedientesState.ver_documento(doc),
                        color_scheme="blue",
                    ),
                    rx.cond(
                        es_pendiente,
                        rx.button(
                            "Aprobar",
                            on_click=ExpedientesState.aprobar_documento(doc),
                            color_scheme="green",
                            variant="soft",
                            size="1",
                        ),
                        rx.fragment(),
                    ),
                    rx.cond(
                        es_pendiente,
                        rx.button(
                            "Rechazar",
                            on_click=ExpedientesState.abrir_modal_rechazo(doc),
                            color_scheme="red",
                            variant="soft",
                            size="1",
                        ),
                        rx.fragment(),
                    ),
                    spacing="1",
                    align="center",
                ),
                rx.fragment(),
            ),
        ),
    )


ENCABEZADOS_DOCUMENTOS = [
    {"nombre": "Documento", "ancho": "240px"},
    {"nombre": "Archivo", "ancho": "auto"},
    {"nombre": "Version", "ancho": "80px"},
    {"nombre": "Estatus", "ancho": "120px"},
    {"nombre": "Obs.", "ancho": "60px"},
    {"nombre": "Acciones", "ancho": "200px"},
]


def area_subida_rrhh() -> rx.Component:
    """Area de subida de documentos para RRHH."""
    return rx.vstack(
        rx.cond(
            ExpedientesState.tipo_documento_subiendo == "",
            rx.button(
                rx.icon("upload", size=16),
                "Subir documento",
                on_click=ExpedientesState.set_tipo_documento_subiendo("_seleccionar"),
                variant="outline",
                size="2",
                color_scheme="blue",
            ),
            rx.vstack(
                rx.hstack(
                    rx.select.root(
                        rx.select.trigger(
                            placeholder="Seleccionar tipo de documento...",
                            width="300px",
                        ),
                        rx.select.content(
                            rx.foreach(
                                ExpedientesState.tipos_documento_disponibles,
                                lambda opt: rx.select.item(
                                    opt["label"], value=opt["value"]
                                ),
                            ),
                        ),
                        value=rx.cond(
                            ExpedientesState.tipo_documento_subiendo == "_seleccionar",
                            "",
                            ExpedientesState.tipo_documento_subiendo,
                        ),
                        on_change=ExpedientesState.set_tipo_documento_subiendo,
                    ),
                    rx.icon_button(
                        rx.icon("x", size=14),
                        size="1",
                        variant="ghost",
                        color_scheme="gray",
                        on_click=ExpedientesState.set_tipo_documento_subiendo(""),
                    ),
                    align="center",
                ),
                rx.cond(
                    (ExpedientesState.tipo_documento_subiendo != "")
                    & (ExpedientesState.tipo_documento_subiendo != "_seleccionar"),
                    rx.upload(
                        rx.vstack(
                            rx.cond(
                                ExpedientesState.subiendo_archivo,
                                rx.spinner(size="2"),
                                rx.icon(
                                    "cloud-upload",
                                    size=32,
                                    color="var(--gray-8)",
                                ),
                            ),
                            rx.text(
                                "Arrastre un archivo o haga clic para seleccionar",
                                font_size=Typography.SIZE_BASE,
                                color=Colors.TEXT_SECONDARY,
                            ),
                            rx.text(
                                "PDF, PNG o JPG - se aprobara automaticamente",
                                font_size=Typography.SIZE_SM,
                                color=Colors.TEXT_MUTED,
                            ),
                            align="center",
                            spacing="2",
                            padding_y="24px",
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
                        border="2px dashed var(--gray-6)",
                        border_radius=Radius.LG,
                        width="100%",
                        cursor="pointer",
                        style={"_hover": {"border_color": "var(--blue-7)"}},
                    ),
                ),
                width="100%",
                spacing="2",
                padding="16px",
                background="var(--blue-2)",
                border="1px solid var(--blue-6)",
                border_radius=Radius.LG,
            ),
        ),
        width="100%",
    )


def detalle_expediente() -> rx.Component:
    """Vista de detalle del expediente de un empleado."""
    return rx.vstack(
        rx.hstack(
            rx.button(
                rx.icon("arrow-left", size=16),
                "Volver a empleados",
                on_click=ExpedientesState.volver_a_empleados,
                variant="ghost",
                size="2",
            ),
            rx.spacer(),
            spacing="3",
            width="100%",
            align="center",
        ),
        rx.hstack(
            rx.vstack(
                rx.text(
                    ExpedientesState.nombre_empleado_seleccionado,
                    font_size=Typography.SIZE_LG,
                    font_weight=Typography.WEIGHT_BOLD,
                ),
                rx.text(
                    ExpedientesState.clave_empleado_seleccionado,
                    font_size=Typography.SIZE_SM,
                    color=Colors.TEXT_SECONDARY,
                ),
                spacing="1",
            ),
            rx.spacer(),
            rx.hstack(
                _metric_card("Requeridos", ExpedientesState.total_docs_requeridos, "blue"),
                _metric_card("Aprobados", ExpedientesState.total_docs_aprobados, "green"),
                _metric_card("Pendientes", ExpedientesState.total_docs_pendientes, "yellow"),
                _metric_card("Rechazados", ExpedientesState.total_docs_rechazados, "red"),
                spacing="3",
            ),
            width="100%",
            align="center",
            padding=Spacing.MD,
            background=Colors.SURFACE,
            border=f"1px solid {Colors.BORDER}",
            border_radius=Radius.MD,
        ),
        area_subida_rrhh(),
        rx.vstack(
            rx.hstack(
                rx.text(
                    "Progreso del expediente",
                    font_size=Typography.SIZE_SM,
                    font_weight=Typography.WEIGHT_MEDIUM,
                ),
                rx.spacer(),
                rx.text(
                    ExpedientesState.porcentaje_expediente,
                    "%",
                    font_size=Typography.SIZE_SM,
                    font_weight=Typography.WEIGHT_BOLD,
                ),
                width="100%",
            ),
            rx.progress(
                value=ExpedientesState.porcentaje_expediente,
                max=100,
                width="100%",
                color_scheme="teal",
            ),
            width="100%",
            spacing="2",
        ),
        document_table_shell(
            headers=ENCABEZADOS_DOCUMENTOS,
            items=ExpedientesState.documentos_expediente_lista,
            row_renderer=fila_documento,
            has_items=ExpedientesState.documentos_expediente_lista.length() > 0,
            empty_title="No hay tipos de documento configurados",
            empty_description="No se encontro el catalogo de documentos del expediente.",
            empty_icon="file-x",
        ),
        width="100%",
        spacing="4",
        padding=Spacing.LG,
    )


def _metric_card(label: str, value, color_scheme: str) -> rx.Component:
    """Mini card de metrica."""
    return rx.vstack(
        rx.text(
            value,
            font_size=Typography.SIZE_LG,
            font_weight=Typography.WEIGHT_BOLD,
        ),
        rx.text(
            label,
            font_size=Typography.SIZE_XS,
            color=Colors.TEXT_MUTED,
        ),
        spacing="0",
        align="center",
        padding_x=Spacing.MD,
        padding_y=Spacing.SM,
        border=f"1px solid {Colors.BORDER}",
        border_radius=Radius.MD,
        min_width="80px",
    )


def modal_rechazo() -> rx.Component:
    """Modal para ingresar observacion de rechazo."""
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title("Rechazar Documento"),
            rx.dialog.description(
                "Ingrese el motivo del rechazo. El empleado podra ver esta observacion."
            ),
            rx.vstack(
                rx.text(
                    "Observacion *",
                    font_size=Typography.SIZE_SM,
                    font_weight=Typography.WEIGHT_MEDIUM,
                ),
                rx.text_area(
                    value=ExpedientesState.form_observacion_rechazo,
                    on_change=ExpedientesState.set_form_observacion_rechazo,
                    placeholder="Describa el motivo del rechazo (min. 5 caracteres)...",
                    width="100%",
                    rows="4",
                ),
                rx.cond(
                    ExpedientesState.error_observacion != "",
                    rx.text(
                        ExpedientesState.error_observacion,
                        font_size=Typography.SIZE_XS,
                        color=Colors.ERROR,
                    ),
                ),
                spacing="2",
                width="100%",
                padding_y=Spacing.BASE,
            ),
            rx.hstack(
                boton_cancelar(
                    on_click=ExpedientesState.cerrar_modal_rechazo,
                ),
                boton_guardar(
                    texto="Rechazar",
                    texto_guardando="Rechazando...",
                    on_click=ExpedientesState.confirmar_rechazo,
                    saving=ExpedientesState.saving,
                    color_scheme="red",
                ),
                spacing="3",
                justify="end",
                width="100%",
            ),
            max_width="500px",
        ),
        open=ExpedientesState.mostrar_modal_rechazo,
        on_open_change=rx.noop,
    )


def modal_preview_documento() -> rx.Component:
    """Modal para vista previa de documentos del expediente."""
    return rx.dialog.root(
        rx.dialog.content(
            rx.vstack(
                rx.hstack(
                    rx.vstack(
                        rx.text("Vista previa", size="4", weight="bold"),
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
                                "border": "1px solid var(--gray-6)",
                                "borderRadius": "8px",
                                "background": "white",
                            },
                        ),
                        rx.center(
                            rx.vstack(
                                rx.icon("file-text", size=40, color="var(--gray-8)"),
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
                        ),
                        href=ExpedientesState.preview_url,
                        is_external=True,
                    ),
                    rx.button(
                        "Cerrar",
                        variant="outline",
                        size="2",
                        on_click=ExpedientesState.cerrar_modal_preview,
                    ),
                    spacing="3",
                    justify="end",
                    width="100%",
                ),
                width="100%",
                spacing="4",
            ),
            max_width="900px",
            width="90vw",
        ),
        open=ExpedientesState.mostrar_modal_preview,
        on_open_change=rx.noop,
    )
