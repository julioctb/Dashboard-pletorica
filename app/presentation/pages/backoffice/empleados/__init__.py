"""
Modulo de paginas de Empleados.

Exporta la pagina principal y el estado para su uso en la aplicacion.
"""
from .page import empleados_page
from .state import EmpleadosState

__all__ = [
    "empleados_page",
    "EmpleadosState",
]
