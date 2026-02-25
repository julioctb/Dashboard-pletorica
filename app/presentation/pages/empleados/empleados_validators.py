"""Compatibilidad de validadores de empleados (wrapper sobre core.validation)."""
from app.core.validation import (
    validar_curp_empleado as validar_curp,
    validar_rfc_empleado as validar_rfc,
    validar_nss_empleado as validar_nss,
    validar_nombre_empleado as validar_nombre,
    validar_apellido_paterno_empleado as validar_apellido_paterno,
    validar_email_empleado as validar_email,
    validar_telefono_empleado as validar_telefono,
    validar_fecha_nacimiento_empleado as validar_fecha_nacimiento,
    validar_empresa_seleccionada_empleado as validar_empresa_seleccionada,
    validar_motivo_restriccion_empleado as validar_motivo_restriccion,
)

__all__ = [
    "validar_curp",
    "validar_rfc",
    "validar_nss",
    "validar_nombre",
    "validar_apellido_paterno",
    "validar_email",
    "validar_telefono",
    "validar_fecha_nacimiento",
    "validar_empresa_seleccionada",
    "validar_motivo_restriccion",
]
