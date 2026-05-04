"""
Módulo de Historial Laboral (Solo Lectura).

Bitácora automática de movimientos de empleados.
Los registros se crean automáticamente desde empleado_service.
"""
from app.presentation.pages.backoffice.historial_laboral.historial_laboral_page import historial_laboral_page
from app.presentation.pages.backoffice.historial_laboral.historial_laboral_state import HistorialLaboralState

__all__ = [
    "historial_laboral_page",
    "HistorialLaboralState",
]
