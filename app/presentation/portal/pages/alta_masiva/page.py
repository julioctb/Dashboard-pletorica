"""
Pagina Alta Masiva del portal de cliente.

Wizard de 3 pasos para carga masiva de empleados:
1. Subir archivo CSV/Excel
2. Preview de validacion (validos, reingresos, errores)
3. Resultados del procesamiento
"""
import reflex as rx

from app.presentation.layout import page_layout, page_header

from .state import AltaMasivaState
from .components import indicador_pasos
from .paso_1 import paso_1_subir
from .paso_2 import paso_2_preview
from .paso_3 import paso_3_resultados


def alta_masiva_page() -> rx.Component:
    """Pagina de alta masiva de empleados."""
    return rx.box(
        page_layout(
            header=page_header(
                titulo="Alta Masiva",
                subtitulo="Carga masiva de empleados desde archivo",
                icono="upload",
            ),
            content=rx.vstack(
                indicador_pasos(),
                rx.match(
                    AltaMasivaState.paso_actual,
                    (1, paso_1_subir()),
                    (2, paso_2_preview()),
                    (3, paso_3_resultados()),
                    paso_1_subir(),
                ),
                width="100%",
                spacing="6",
            ),
        ),
        width="100%",
        min_height="100vh",
        on_mount=AltaMasivaState.on_mount_alta_masiva,
    )
