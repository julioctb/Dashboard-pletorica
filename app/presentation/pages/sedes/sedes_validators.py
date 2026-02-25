"""Compatibilidad de validadores de Sedes (wrapper sobre core.validation)."""
from app.core.validation.sede_form_validators import (
    validar_codigo_sede_form as validar_codigo,
    validar_nombre_sede_form as validar_nombre,
    validar_nombre_corto_sede_form as validar_nombre_corto,
    validar_formulario_sede_form as validar_formulario_sede,
)

__all__ = [
    "validar_codigo",
    "validar_nombre",
    "validar_nombre_corto",
    "validar_formulario_sede",
]
