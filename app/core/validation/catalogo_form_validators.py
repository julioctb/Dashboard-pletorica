"""Validadores de formulario (UI) para catálogos (tipo servicio/categoría puesto)."""
from .validator_factory import crear_validador
from .fields_catalog import (
    CAMPO_CLAVE_CATALOGO,
    CAMPO_NOMBRE_CATALOGO,
    CAMPO_DESCRIPCION_CATALOGO,
)
from .common_validators import validar_select_requerido, validar_entero_rango


validar_clave_catalogo_form = crear_validador(CAMPO_CLAVE_CATALOGO)
validar_nombre_catalogo_form = crear_validador(CAMPO_NOMBRE_CATALOGO)
validar_descripcion_catalogo_form = crear_validador(CAMPO_DESCRIPCION_CATALOGO)


def validar_orden_categoria_puesto_form(valor: str) -> str:
    return validar_entero_rango(valor, "orden", minimo=0, maximo=None, requerido=False)


def validar_tipo_servicio_id_categoria_puesto_form(valor: str) -> str:
    return validar_select_requerido(valor, "tipo de servicio")


def validar_formulario_categoria_puesto_form(
    tipo_servicio_id: str,
    clave: str,
    nombre: str,
    descripcion: str = "",
    orden: str = "",
) -> dict:
    errores = {}
    if error := validar_tipo_servicio_id_categoria_puesto_form(tipo_servicio_id):
        errores["tipo_servicio_id"] = error
    if error := validar_clave_catalogo_form(clave):
        errores["clave"] = error
    if error := validar_nombre_catalogo_form(nombre):
        errores["nombre"] = error
    if error := validar_descripcion_catalogo_form(descripcion):
        errores["descripcion"] = error
    if error := validar_orden_categoria_puesto_form(orden):
        errores["orden"] = error
    return errores


def validar_formulario_tipo_servicio_form(clave: str, nombre: str, descripcion: str = "") -> dict:
    errores = {}
    if error := validar_clave_catalogo_form(clave):
        errores["clave"] = error
    if error := validar_nombre_catalogo_form(nombre):
        errores["nombre"] = error
    if error := validar_descripcion_catalogo_form(descripcion):
        errores["descripcion"] = error
    return errores


__all__ = [
    "validar_clave_catalogo_form",
    "validar_nombre_catalogo_form",
    "validar_descripcion_catalogo_form",
    "validar_orden_categoria_puesto_form",
    "validar_tipo_servicio_id_categoria_puesto_form",
    "validar_formulario_categoria_puesto_form",
    "validar_formulario_tipo_servicio_form",
]
