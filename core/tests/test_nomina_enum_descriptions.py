"""Protege descripciones compartidas de enums de nomina."""

from core.core.enums import OrigenCaptura, OrigenMovimiento


def test_origenes_nomina_comparten_descripcion_consistente():
    assert OrigenCaptura.SISTEMA.descripcion == "Calculado por el sistema"
    assert OrigenMovimiento.SISTEMA.descripcion == "Calculado por el sistema"
    assert OrigenCaptura.CONTABILIDAD.descripcion == "Capturado por Contabilidad"
    assert OrigenMovimiento.CONTABILIDAD.descripcion == "Capturado por Contabilidad"
