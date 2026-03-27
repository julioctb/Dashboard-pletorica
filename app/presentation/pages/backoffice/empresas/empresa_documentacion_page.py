"""Página backoffice de documentación anual de empresas."""

import reflex as rx

from app.presentation.components.backoffice.empresas.empresa_documentacion_ui import (
    panel_documentacion_empresa,
)
from app.presentation.layouts.backoffice import page_header, page_layout

from .empresa_documentacion_state import EmpresaDocumentacionState


def empresa_documentacion_page() -> rx.Component:
    return rx.box(
        page_layout(
            header=page_header(
                titulo="Documentación Anual",
                subtitulo="Checklist fiscal y legal del proveedor por año",
                icono="folders",
                accion_principal=rx.link(
                    rx.button(
                        rx.icon("arrow-left", size=16),
                        "Volver a empresas",
                        variant="outline",
                    ),
                    href="/empresas",
                ),
            ),
            toolbar=rx.fragment(),
            content=panel_documentacion_empresa(
                EmpresaDocumentacionState,
                can_edit=EmpresaDocumentacionState.puede_operar_empresas,
                can_share=EmpresaDocumentacionState.puede_operar_empresas,
            ),
        ),
        width="100%",
        min_height="100vh",
        on_mount=EmpresaDocumentacionState.on_mount_empresa_documentacion,
    )
