"""
Componentes de subida de documentos para el autoservicio del empleado.

Lista de tipos de documento obligatorios/opcionales con estatus y
area de subida por tipo.
"""
import reflex as rx

from app.presentation.theme import Colors, Typography, Spacing

from .state import MisDatosState


# =============================================================================
# BADGES
# =============================================================================

def _badge_doc_estatus(estatus: str) -> rx.Component:
    """Badge de estatus de un documento."""
    return rx.match(
        estatus,
        ("PENDIENTE_REVISION", rx.badge("Pendiente", color_scheme="yellow", variant="soft", size="1")),
        ("APROBADO", rx.badge("Aprobado", color_scheme="green", variant="soft", size="1")),
        ("RECHAZADO", rx.badge("Rechazado", color_scheme="red", variant="soft", size="1")),
        rx.badge("Sin subir", color_scheme="gray", variant="outline", size="1"),
    )


# =============================================================================
# FILA DE TIPO DE DOCUMENTO
# =============================================================================

def fila_tipo_documento(tipo_doc: dict) -> rx.Component:
    """Fila individual para un tipo de documento."""
    upload_id = "upload_doc_" + tipo_doc["tipo"].to(str)

    return rx.hstack(
        # Icono
        rx.cond(
            tipo_doc["subido"],
            rx.icon("file-check", size=20, color="var(--green-9)"),
            rx.icon("file-x", size=20, color=Colors.TEXT_MUTED),
        ),
        # Nombre y obligatorio
        rx.vstack(
            rx.hstack(
                rx.text(
                    tipo_doc["nombre"],
                    font_size=Typography.SIZE_SM,
                    font_weight=Typography.WEIGHT_MEDIUM,
                ),
                rx.cond(
                    tipo_doc["obligatorio"],
                    rx.badge("Obligatorio", color_scheme="blue", variant="outline", size="1"),
                    rx.badge("Opcional", color_scheme="gray", variant="outline", size="1"),
                ),
                align="center",
                gap="2",
            ),
            # Observacion de rechazo si existe
            rx.cond(
                tipo_doc["observacion"] != "",
                rx.text(
                    tipo_doc["observacion"],
                    font_size=Typography.SIZE_XS,
                    color="var(--red-9)",
                ),
                rx.fragment(),
            ),
            spacing="1",
        ),
        rx.spacer(),
        # Badge estatus
        _badge_doc_estatus(tipo_doc["estatus"]),
        # Boton subir/resubir
        rx.cond(
            MisDatosState.puede_subir_docs,
            rx.upload(
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
                ),
                id=upload_id,
                accept={
                    "application/pdf": [".pdf"],
                    "image/png": [".png"],
                    "image/jpeg": [".jpg", ".jpeg"],
                },
                max_files=1,
                on_drop=[
                    MisDatosState.set_tipo_documento_subiendo(tipo_doc["tipo"].to(str)),
                    MisDatosState.handle_upload_documento(rx.upload_files(upload_id=upload_id)),
                ],
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
# LISTA COMPLETA DE DOCUMENTOS
# =============================================================================

def lista_documentos_requeridos() -> rx.Component:
    """Lista de todos los tipos de documento con su estatus."""
    return rx.vstack(
        rx.hstack(
            rx.text(
                "Documentos del expediente",
                font_size=Typography.SIZE_LG,
                font_weight=Typography.WEIGHT_BOLD,
                color=Colors.TEXT_PRIMARY,
            ),
            rx.spacer(),
            # Boton enviar a revision
            rx.cond(
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
            width="100%",
            align="center",
        ),
        rx.text(
            "Suba cada documento requerido. Los documentos rechazados deben ser resubidos.",
            font_size=Typography.SIZE_SM,
            color=Colors.TEXT_SECONDARY,
        ),
        rx.box(
            rx.foreach(
                MisDatosState.tipos_documento_lista,
                fila_tipo_documento,
            ),
            width="100%",
            border=f"1px solid {Colors.BORDER}",
            border_radius="8px",
            background=Colors.SURFACE,
            overflow="hidden",
        ),
        width="100%",
        spacing="3",
    )
