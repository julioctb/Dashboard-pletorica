"""
Pagina Mis Datos del portal — autoservicio del empleado.

Muestra contenido condicional segun el estatus de onboarding:
- DATOS_PENDIENTES: formulario datos personales/bancarios
- DOCUMENTOS_PENDIENTES/RECHAZADO: subida de documentos + progreso
- EN_REVISION: mensaje informativo
- APROBADO/ACTIVO_COMPLETO: mensaje de expediente completo
"""
import reflex as rx

from app.presentation.layout import page_layout, page_header
from app.presentation.theme import Spacing

from .state import MisDatosState
from .components import (
    seccion_datos,
    progreso_expediente,
    estado_revision,
    estado_aprobado,
    estado_no_encontrado,
)
from .upload_docs import lista_documentos_requeridos


def mis_datos_page() -> rx.Component:
    """Pagina de autoservicio del empleado."""
    return rx.box(
        page_layout(
            header=page_header(
                titulo="Mis Datos",
                subtitulo=MisDatosState.subtitulo_pagina,
                icono="user",
            ),
            toolbar=rx.fragment(),
            content=rx.cond(
                MisDatosState.loading,
                rx.center(rx.spinner(size="3"), padding_y="60px"),
                rx.cond(
                    ~MisDatosState.empleado_encontrado,
                    estado_no_encontrado(),
                    # Contenido segun estatus
                    rx.cond(
                        MisDatosState.puede_editar_datos,
                        # DATOS_PENDIENTES
                        seccion_datos(),
                        rx.cond(
                            MisDatosState.puede_subir_docs,
                            # DOCUMENTOS_PENDIENTES o RECHAZADO
                            rx.vstack(
                                progreso_expediente(),
                                lista_documentos_requeridos(),
                                width="100%",
                                spacing="4",
                            ),
                            rx.cond(
                                MisDatosState.esta_en_revision,
                                # EN_REVISION
                                estado_revision(),
                                rx.cond(
                                    MisDatosState.esta_aprobado,
                                    # APROBADO / ACTIVO_COMPLETO
                                    estado_aprobado(),
                                    # Fallback (REGISTRADO u otro)
                                    rx.center(
                                        rx.text(
                                            "Contacte a Recursos Humanos para iniciar su proceso de onboarding.",
                                            color="var(--gray-9)",
                                        ),
                                        padding_y="60px",
                                    ),
                                ),
                            ),
                        ),
                    ),
                ),
            ),
        ),
        width="100%",
        min_height="100vh",
        on_mount=MisDatosState.on_mount_mis_datos,
    )
