"""Página pública para compartir el expediente anual de una empresa."""

import reflex as rx

from app.presentation.components.empresas.empresa_documentacion_ui import (
    panel_documentacion_empresa,
)
from app.presentation.theme import Colors, Spacing

from .empresa_documentacion_share_state import EmpresaDocumentacionShareState


def empresa_documentacion_share_page() -> rx.Component:
    return rx.box(
        rx.center(
            rx.vstack(
                rx.vstack(
                    rx.badge("Solo lectura", color_scheme="blue", variant="soft", size="2"),
                    rx.heading("Expediente anual compartido", size="7"),
                    rx.text(
                        "Documentación fiscal y legal cargada por la empresa proveedora.",
                        color=Colors.TEXT_SECONDARY,
                    ),
                    spacing="2",
                    align="center",
                    width="100%",
                ),
                rx.cond(
                    EmpresaDocumentacionShareState.mensaje_info != "",
                    rx.callout.root(
                        rx.callout.icon(rx.icon("triangle-alert", size=16)),
                        rx.callout.text(EmpresaDocumentacionShareState.mensaje_info),
                        color_scheme="red",
                        variant="soft",
                        width="100%",
                    ),
                    rx.fragment(),
                ),
                rx.cond(
                    EmpresaDocumentacionShareState.tiene_documentacion_cargada,
                    panel_documentacion_empresa(
                        EmpresaDocumentacionShareState,
                        can_edit=False,
                        can_share=False,
                        readonly=True,
                        show_share_block=False,
                        allow_change_year=False,
                    ),
                    rx.fragment(),
                ),
                width="100%",
                max_width="1200px",
                spacing="5",
                padding_y=Spacing.XL,
                padding_x=Spacing.LG,
            ),
            width="100%",
        ),
        min_height="100vh",
        background="linear-gradient(180deg, var(--gray-1) 0%, var(--gray-2) 100%)",
        on_mount=EmpresaDocumentacionShareState.on_mount_empresa_documentacion_share,
    )
