"""
Componentes de subida de documentos para el autoservicio del empleado.

Lista de tipos de documento obligatorios/opcionales con estatus y
area de subida. Usa un solo rx.upload con id estatico para evitar
problemas de id dinamico dentro de rx.foreach.
"""

import reflex as rx

from app.presentation.components.common.upload_zone import (
    ACCEPT_IMAGES_PDF,
    upload_zone,
)
from app.presentation.components.ui import document_status_badge
from app.presentation.components.reusable import (
    document_section_container,
    document_section_header,
    documento_observacion,
    documento_requerido_badge,
    documento_subido_icon,
)
from app.presentation.theme import Colors, Typography, Spacing

from .state import MisDatosState

# ID estatico para el upload (uno solo, el tipo se setea en state)
UPLOAD_ID = "upload_doc_expediente"


# =============================================================================
# BADGES
# =============================================================================


def _badge_doc_estatus(estatus: str) -> rx.Component:
    """Badge de estatus de un documento."""
    return document_status_badge(estatus)


# =============================================================================
# FILA DE TIPO DE DOCUMENTO
# =============================================================================


def fila_tipo_documento(tipo_doc: dict) -> rx.Component:
    """Fila individual para un tipo de documento."""
    return rx.hstack(
        # Icono
        documento_subido_icon(tipo_doc["subido"]),
        # Nombre y obligatorio
        rx.vstack(
            rx.hstack(
                rx.text(
                    tipo_doc["nombre"],
                    font_size=Typography.SIZE_SM,
                    font_weight=Typography.WEIGHT_MEDIUM,
                ),
                documento_requerido_badge(tipo_doc["obligatorio"]),
                align="center",
                gap="2",
            ),
            # Observacion de rechazo si existe
            documento_observacion(tipo_doc["observacion"]),
            spacing="1",
        ),
        rx.spacer(),
        # Badge estatus
        _badge_doc_estatus(tipo_doc["estatus"]),
        # Boton para seleccionar tipo y abrir upload
        rx.cond(
            MisDatosState.puede_subir_docs,
            rx.button(
                rx.cond(
                    tipo_doc["subido"],
                    rx.text("Resubir", font_size=Typography.SIZE_XS),
                    rx.text("Subir", font_size=Typography.SIZE_XS),
                ),
                rx.icon("upload", size=14),
                size="1",
                variant="outline",
                color_scheme=rx.cond(
                    tipo_doc["estatus"] == "RECHAZADO",
                    "red",
                    "blue",
                ),
                on_click=MisDatosState.set_tipo_documento_subiendo(tipo_doc["tipo"]),
            ),
            rx.fragment(),
        ),
        width="100%",
        padding_y=Spacing.SM,
        padding_x=Spacing.MD,
        align="center",
        border_bottom=f"1px solid {Colors.BORDER}",
    )


# =============================================================================
# AREA DE SUBIDA (unica, estatica)
# =============================================================================


def area_subida_documento() -> rx.Component:
    """Area de upload que aparece cuando se selecciona un tipo de documento."""
    return rx.cond(
        MisDatosState.tipo_documento_subiendo != "",
        rx.vstack(
            rx.hstack(
                rx.icon("file-up", size=18, color="var(--blue-9)"),
                rx.text(
                    "Subir documento: ",
                    font_size=Typography.SIZE_SM,
                    font_weight=Typography.WEIGHT_MEDIUM,
                ),
                rx.text(
                    MisDatosState.tipo_documento_subiendo,
                    font_size=Typography.SIZE_SM,
                    color="var(--blue-9)",
                    font_weight=Typography.WEIGHT_BOLD,
                ),
                rx.spacer(),
                rx.icon_button(
                    rx.icon("x", size=14),
                    size="1",
                    variant="ghost",
                    color_scheme="gray",
                    on_click=MisDatosState.set_tipo_documento_subiendo(""),
                ),
                align="center",
                width="100%",
            ),
            upload_zone(
                upload_id=UPLOAD_ID,
                title="Arrastre un archivo o haga clic para seleccionar",
                helper_text="PDF, PNG o JPG (max 1 archivo)",
                accept=ACCEPT_IMAGES_PDF,
                max_files=1,
                loading=MisDatosState.subiendo_archivo,
                on_drop=MisDatosState.handle_upload_documento,
                auto_upload=True,
                icon="cloud-upload",
                icon_color=Colors.TEXT_MUTED,
                icon_size=32,
                border=f"2px dashed {Colors.BORDER}",
                border_radius="8px",
                hover_border_color="var(--blue-7)",
                padding=Spacing.LG,
            ),
            width="100%",
            spacing="2",
            padding=Spacing.MD,
            background="var(--blue-2)",
            border=f"1px solid var(--blue-6)",
            border_radius="8px",
        ),
        rx.fragment(),
    )


# =============================================================================
# LISTA COMPLETA DE DOCUMENTOS
# =============================================================================


def lista_documentos_requeridos() -> rx.Component:
    """Lista de todos los tipos de documento con su estatus."""
    return rx.vstack(
        document_section_header(
            title="Documentos del expediente",
            subtitle="Seleccione un documento y suba el archivo correspondiente.",
            actions=rx.cond(
                MisDatosState.puede_enviar_revision,
                rx.button(
                    rx.icon("send", size=16),
                    "Enviar a revision",
                    on_click=MisDatosState.enviar_a_revision,
                    loading=MisDatosState.saving,
                    color_scheme="green",
                    size="2",
                ),
                rx.fragment(),
            ),
        ),
        # Area de subida (aparece al seleccionar tipo)
        area_subida_documento(),
        # Lista de tipos
        document_section_container(
            rx.foreach(
                MisDatosState.tipos_documento_lista,
                fila_tipo_documento,
            ),
        ),
        width="100%",
        spacing="3",
    )
