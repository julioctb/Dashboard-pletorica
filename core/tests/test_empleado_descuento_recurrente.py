"""Tests del contrato de descuentos recurrentes por empleado."""

from datetime import date

import pytest
from pydantic import ValidationError

from core.domain.models.empleado_descuento_recurrente import (
    EmpleadoDescuentoRecurrenteCreate,
    es_descuento_recurrente_activo_en_rango,
)


def test_descuento_recurrente_normaliza_monto_y_acepta_vigencia_indefinida():
    descuento = EmpleadoDescuentoRecurrenteCreate(
        empleado_id=10,
        concepto_clave="descuento_infonavit",
        monto_periodico="$ 1,250.5",
        fecha_inicio=date(2026, 3, 1),
        notas="Crédito vigente",
    )

    assert descuento.concepto_clave == "DESCUENTO_INFONAVIT"
    assert str(descuento.monto_periodico) == "1250.50"
    assert descuento.fecha_fin is None


def test_descuento_recurrente_rechaza_fecha_fin_anterior_a_inicio():
    with pytest.raises(ValidationError):
        EmpleadoDescuentoRecurrenteCreate(
            empleado_id=10,
            concepto_clave="PENSION_ALIMENTICIA",
            monto_periodico="500.00",
            fecha_inicio=date(2026, 3, 15),
            fecha_fin=date(2026, 3, 1),
        )


def test_descuento_recurrente_activo_en_rango_detecta_cruce_parcial():
    assert es_descuento_recurrente_activo_en_rango(
        fecha_inicio_descuento=date(2026, 2, 20),
        fecha_fin_descuento=date(2026, 3, 2),
        fecha_inicio_rango=date(2026, 3, 1),
        fecha_fin_rango=date(2026, 3, 15),
    )
