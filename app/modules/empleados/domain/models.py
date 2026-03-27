"""Employee domain models re-exported from the legacy structure."""

from app.domain.models.baja_empleado import BajaEmpleado, BajaEmpleadoCreate, BajaEmpleadoResumen
from app.domain.models.cuenta_bancaria_historial import CuentaBancariaHistorial
from app.domain.models.empleado import Empleado, EmpleadoCreate, EmpleadoResumen, EmpleadoUpdate
from app.domain.models.empleado_descuento_recurrente import (
    EmpleadoDescuentoRecurrente,
    EmpleadoDescuentoRecurrenteCreate,
)
from app.domain.models.empleado_documento import EmpleadoDocumento
from app.domain.models.historial_laboral import (
    HistorialLaboral,
    HistorialLaboralInterno,
    HistorialLaboralResumen,
)
from app.domain.models.incapacidad import Incapacidad

models___all__ = [
    "BajaEmpleado",
    "BajaEmpleadoCreate",
    "BajaEmpleadoResumen",
    "CuentaBancariaHistorial",
    "Empleado",
    "EmpleadoCreate",
    "EmpleadoResumen",
    "EmpleadoUpdate",
    "EmpleadoDescuentoRecurrente",
    "EmpleadoDescuentoRecurrenteCreate",
    "EmpleadoDocumento",
    "HistorialLaboral",
    "HistorialLaboralInterno",
    "HistorialLaboralResumen",
    "Incapacidad",
]

__all__ = models___all__
