"""Componentes genéricos de UI reutilizables"""

from .headers import page_header
from .form_input import form_input, form_select, form_textarea
from .form_field import form_field, form_section
from .buttons import boton_accion, acciones_crud
from .badges import estatus_badge
from .tables import tabla_vacia, tabla
from .skeletons import skeleton_tabla
from .filters import (
    input_busqueda,
    indicador_filtros,
    contador_registros,
    switch_inactivos,
    barra_filtros,
)
from .barra_herramientas import barra_herramientas

__all__ = [
    'page_header',
    'form_input',
    'form_select',
    'form_textarea',
    'form_field',
    'form_section',
    'boton_accion',
    'acciones_crud',
    'estatus_badge',
    # tablas
    'tabla_vacia',
    'tabla',
    'skeleton_tabla',
    # filtros
    'input_busqueda',
    'indicador_filtros',
    'contador_registros',
    'switch_inactivos',
    'barra_filtros',
    'barra_herramientas',
]
