"""Tests para aliases compartidos de validadores de formulario."""

from core.core.validation.catalogo_form_validators import (
    validar_tipo_servicio_id_categoria_puesto_form,
)
from core.core.validation.contrato_categoria_form_validators import (
    validar_notas_contrato_categoria,
)
from core.core.validation.contrato_form_validators import (
    validar_tipo_servicio_id_contrato,
)
from core.core.validation.constants import NOTAS_PAGO_MAX
from core.core.validation.pago_form_validators import validar_notas_pago_form


def test_validadores_tipo_servicio_reusan_el_mismo_helper():
    assert validar_tipo_servicio_id_categoria_puesto_form is validar_tipo_servicio_id_contrato
    assert validar_tipo_servicio_id_contrato("") == "Debe seleccionar un tipo de servicio"
    assert validar_tipo_servicio_id_categoria_puesto_form("12") == ""


def test_validadores_notas_reusan_el_mismo_helper():
    assert validar_notas_contrato_categoria is validar_notas_pago_form

    texto_largo = "x" * (NOTAS_PAGO_MAX + 1)
    esperado = f"El campo notas no puede exceder {NOTAS_PAGO_MAX} caracteres"

    assert validar_notas_contrato_categoria(texto_largo) == esperado
    assert validar_notas_pago_form("nota breve") == ""
