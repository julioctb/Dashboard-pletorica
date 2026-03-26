"""Wrappers de modales de plazas para la pagina por contrato."""

from core.presentation.pages.portal.plaza_shared_modals import (
    modal_asignacion_plaza as shared_modal_asignacion_plaza,
    modal_asignacion_sede_plaza as shared_modal_asignacion_sede_plaza,
    modal_categoria_plaza as shared_modal_categoria_plaza,
    modal_reasignacion_plaza as shared_modal_reasignacion_plaza,
    modal_salario_plaza as shared_modal_salario_plaza,
)

from .state import ContratoPlazasState


def modal_asignacion_plaza():
    return shared_modal_asignacion_plaza(ContratoPlazasState)


def modal_categoria_plaza():
    return shared_modal_categoria_plaza(ContratoPlazasState)


def modal_salario_plaza():
    return shared_modal_salario_plaza(ContratoPlazasState)


def modal_asignacion_sede_plaza():
    return shared_modal_asignacion_sede_plaza(ContratoPlazasState)


def modal_reasignacion_plaza():
    return shared_modal_reasignacion_plaza(ContratoPlazasState)
