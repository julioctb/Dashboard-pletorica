"""Validadores de formulario (UI) para Sedes."""
from .validator_factory import crear_validador
from .fields_catalog import CAMPO_CODIGO_SEDE, CAMPO_NOMBRE_SEDE, CAMPO_NOMBRE_CORTO_SEDE


validar_codigo_sede_form = crear_validador(CAMPO_CODIGO_SEDE)
validar_nombre_sede_form = crear_validador(CAMPO_NOMBRE_SEDE)
validar_nombre_corto_sede_form = crear_validador(CAMPO_NOMBRE_CORTO_SEDE)


def validar_formulario_sede_form(codigo: str, nombre: str, nombre_corto: str = "") -> dict:
    errores = {}
    if error := validar_codigo_sede_form(codigo):
        errores["codigo"] = error
    if error := validar_nombre_sede_form(nombre):
        errores["nombre"] = error
    if error := validar_nombre_corto_sede_form(nombre_corto):
        errores["nombre_corto"] = error
    return errores


__all__ = [
    "validar_codigo_sede_form",
    "validar_nombre_sede_form",
    "validar_nombre_corto_sede_form",
    "validar_formulario_sede_form",
]
