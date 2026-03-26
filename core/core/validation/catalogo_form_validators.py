"""Validadores de formulario (UI) para catálogos (tipo servicio/categoría puesto)."""
from .validator_factory import crear_validador
from .fields_catalog import (
    CAMPO_CLAVE_CATALOGO,
    CAMPO_NOMBRE_CATALOGO,
    CAMPO_DESCRIPCION_CATALOGO,
)
from .common_validators import validar_entero_rango
from .form_shared_validators import (
    validar_tipo_servicio_id_form as validar_tipo_servicio_id_categoria_puesto_form,
)


validar_clave_catalogo_form = crear_validador(CAMPO_CLAVE_CATALOGO)
validar_nombre_catalogo_form = crear_validador(CAMPO_NOMBRE_CATALOGO)
validar_descripcion_catalogo_form = crear_validador(CAMPO_DESCRIPCION_CATALOGO)


def validar_orden_categoria_puesto_form(valor: str) -> str:
    return validar_entero_rango(valor, "orden", minimo=0, maximo=None, requerido=False)


__all__ = [
    "validar_clave_catalogo_form",
    "validar_nombre_catalogo_form",
    "validar_descripcion_catalogo_form",
    "validar_orden_categoria_puesto_form",
    "validar_tipo_servicio_id_categoria_puesto_form",
]
