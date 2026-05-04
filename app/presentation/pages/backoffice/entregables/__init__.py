"""
Módulo de Entregables (Admin).
Páginas: entregables_page (listado), entregable_detalle_page (detalle y revisión)
Estados: EntregablesState, EntregableDetalleState
"""

from app.presentation.pages.backoffice.entregables.entregables_state import EntregablesState
from app.presentation.pages.backoffice.entregables.entregable_detalle_state import EntregableDetalleState
from app.presentation.pages.backoffice.entregables.entregables_page import entregables_page
from app.presentation.pages.backoffice.entregables.entregable_detalle_page import entregable_detalle_page

__all__ = [
    "EntregablesState",
    "EntregableDetalleState",
    "entregables_page",
    "entregable_detalle_page",
]
