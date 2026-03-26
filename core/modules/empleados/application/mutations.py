"""Mutation-oriented services for the employee module."""

from core.domain.services.empleado_documento_service import (
    EmpleadoDocumentoService,
    empleado_documento_service,
)
from core.domain.services.empleado_service import EmpleadoService, empleado_service
from core.domain.services.empleados import EmpleadoMutationService

mutations___all__ = [
    "EmpleadoDocumentoService",
    "EmpleadoMutationService",
    "EmpleadoService",
    "empleado_documento_service",
    "empleado_service",
]

__all__ = mutations___all__
