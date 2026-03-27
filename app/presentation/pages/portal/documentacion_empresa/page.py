"""Página portal para la documentación anual de la empresa."""

import reflex as rx

from app.presentation.components.backoffice.empresas.empresa_documentacion_ui import (
    panel_documentacion_empresa,
)
from app.presentation.layouts.backoffice import page_header, page_layout
from app.presentation.theme import Colors

from .state import DocumentacionEmpresaPortalState


def documentacion_empresa_portal_page() -> rx.Component:
    return rx.box(
        page_layout(
            header=page_header(
                titulo="Documentación Anual",
                subtitulo="Carga y comparte el expediente anual de tu empresa",
                icono="folder-lock",
                color_icono=Colors.PORTAL_ACCENT_SCHEME,
            ),
            toolbar=rx.fragment(),
            content=panel_documentacion_empresa(
                DocumentacionEmpresaPortalState,
                can_edit=DocumentacionEmpresaPortalState.es_admin_empresa,
                can_share=DocumentacionEmpresaPortalState.es_admin_empresa,
            ),
        ),
        width="100%",
        min_height="100vh",
        on_mount=DocumentacionEmpresaPortalState.on_mount_documentacion_empresa_portal,
    )
