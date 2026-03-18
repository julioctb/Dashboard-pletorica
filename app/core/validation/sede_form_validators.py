"""Validadores de formulario (UI) para Sedes."""
from .validator_factory import crear_validador
from .fields_catalog import CAMPO_CODIGO_SEDE, CAMPO_NOMBRE_SEDE, CAMPO_NOMBRE_CORTO_SEDE


validar_codigo_sede_form = crear_validador(CAMPO_CODIGO_SEDE)
validar_nombre_sede_form = crear_validador(CAMPO_NOMBRE_SEDE)
validar_nombre_corto_sede_form = crear_validador(CAMPO_NOMBRE_CORTO_SEDE)


__all__ = [
    "validar_codigo_sede_form",
    "validar_nombre_sede_form",
    "validar_nombre_corto_sede_form",
]
