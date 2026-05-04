"""Módulo compartido de incapacidades para el portal."""

from .components import (
    filtros_incapacidades_empresa,
    lista_incapacidades_empleado,
    metricas_incapacidades_empresa,
    modal_registro_incapacidad,
    seccion_incapacidades_empleado,
    tabla_incapacidades_empresa,
)
from .page import incapacidades_page
from .state import IncapacidadState

__all__ = [
    "IncapacidadState",
    "filtros_incapacidades_empresa",
    "incapacidades_page",
    "lista_incapacidades_empleado",
    "metricas_incapacidades_empresa",
    "modal_registro_incapacidad",
    "seccion_incapacidades_empleado",
    "tabla_incapacidades_empresa",
]
