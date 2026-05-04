"""Tests de validación para el modelo BajaEmpleado."""

from datetime import date, timedelta

import pytest

from app.domain.enums import EstatusBaja, EstatusLiquidacion, MotivoBaja
from app.domain.models.baja_empleado import BajaEmpleado


def _payload_base() -> dict:
    hoy = date.today()
    return {
        "empleado_id": 10,
        "empresa_id": 3,
        "plaza_id": 22,
        "motivo": MotivoBaja.FIN_CONTRATO,
        "notas": "Baja de prueba",
        "fecha_registro": hoy,
        "fecha_efectiva": hoy,
        "fecha_limite_liquidacion": hoy + timedelta(days=15),
        "estatus_liquidacion": EstatusLiquidacion.PENDIENTE,
        "estatus": EstatusBaja.INICIADA,
        "es_automatica": False,
    }


def test_baja_empleado_rechaza_fecha_efectiva_anterior_en_alta_manual():
    payload = _payload_base()
    payload["fecha_efectiva"] = payload["fecha_registro"] - timedelta(days=1)
    payload["es_automatica"] = False

    with pytest.raises(ValueError, match="fecha efectiva no puede ser anterior"):
        BajaEmpleado(**payload)


def test_baja_empleado_permite_fecha_efectiva_anterior_en_alta_automatica():
    payload = _payload_base()
    payload["fecha_efectiva"] = payload["fecha_registro"] - timedelta(days=1)
    payload["es_automatica"] = True

    baja = BajaEmpleado(**payload)

    assert baja.es_automatica is True


def test_baja_empleado_hidrata_registro_legacy_con_id_sin_fallar():
    payload = _payload_base()
    payload["id"] = 999
    payload["fecha_efectiva"] = payload["fecha_registro"] - timedelta(days=3)
    payload["es_automatica"] = False

    baja = BajaEmpleado(**payload)

    assert baja.id == 999
