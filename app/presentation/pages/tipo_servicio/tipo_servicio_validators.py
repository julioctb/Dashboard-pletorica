"""Compatibilidad de validadores de Tipos de Servicio (wrapper sobre core.validation)."""
from app.core.validation.catalogo_form_validators import (
    validar_clave_catalogo_form as validar_clave,
    validar_nombre_catalogo_form as validar_nombre,
    validar_descripcion_catalogo_form as validar_descripcion,
    validar_formulario_tipo_servicio_form as validar_formulario_tipo,
)

__all__ = [
    "validar_clave",
    "validar_nombre",
    "validar_descripcion",
    "validar_formulario_tipo",
]
