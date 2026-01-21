"""
Módulo de páginas de Empleados.

Exporta la página principal y el estado para su uso en la aplicación.
"""
from app.presentation.pages.empleados.empleados_page import empleados_page
from app.presentation.pages.empleados.empleados_state import EmpleadosState

__all__ = [
    "empleados_page",
    "EmpleadosState",
]
