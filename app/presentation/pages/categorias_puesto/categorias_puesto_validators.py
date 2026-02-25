"""Compatibilidad de validadores de Categorías de Puesto (wrapper sobre core.validation)."""
from app.core.validation.catalogo_form_validators import (
    validar_clave_catalogo_form as validar_clave,
    validar_nombre_catalogo_form as validar_nombre,
    validar_descripcion_catalogo_form as validar_descripcion,
    validar_orden_categoria_puesto_form as validar_orden,
    validar_tipo_servicio_id_categoria_puesto_form as validar_tipo_servicio_id,
    validar_formulario_categoria_puesto_form as validar_formulario_categoria,
)

__all__ = [
    "validar_clave",
    "validar_nombre",
    "validar_descripcion",
    "validar_orden",
    "validar_tipo_servicio_id",
    "validar_formulario_categoria",
]
