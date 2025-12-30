import reflex as rx
from app.presentation.pages.simulador.simulador_state import SimuladorState

from app.presentation.components.ui.headers import page_header


def simulador_page() -> rx.Component:
    """Pagina del simulador del costo patronal"""

    return rx.vstack(
        page_header(
            icono='calculator',
            titulo='Simulador de Costo Patronal',
            subtitulo='Proyección 2026'
        )
    )