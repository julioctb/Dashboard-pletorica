"""Tests del listado de contratos en el portal."""

import asyncio

from app.core.ui_helpers import FILTRO_TODOS
from app.presentation.portal.pages import mis_contratos as mis_contratos_module


class _DummyMisContratosState:
    _fetch_contratos = mis_contratos_module.MisContratosState._fetch_contratos
    _enriquecer_contrato = mis_contratos_module.MisContratosState._enriquecer_contrato

    def __init__(self, filtro_estatus: str):
        self.id_empresa_actual = 26
        self.filtro_estatus_cto = filtro_estatus
        self.contratos = []
        self.total_contratos_lista = 0
        self.mensajes = []

    def mostrar_mensaje(self, mensaje: str, tipo: str):
        self.mensajes.append((mensaje, tipo))


class _FakeContratoService:
    def __init__(self):
        self.calls = []

    async def obtener_por_empresa(self, empresa_id: int, incluir_inactivos: bool = False):
        self.calls.append((empresa_id, incluir_inactivos))
        return [
            {
                "id": 1,
                "codigo": "CTO-001",
                "fecha_inicio": "2026-01-01",
                "fecha_fin": "2026-02-01",
                "monto_minimo": "1000",
                "monto_maximo": "2000",
            }
        ]


def test_fetch_contratos_portal_incluye_vencidos_por_default(monkeypatch):
    dummy = _DummyMisContratosState(FILTRO_TODOS)
    fake_service = _FakeContratoService()

    monkeypatch.setattr(
        mis_contratos_module,
        "contrato_service",
        fake_service,
    )

    asyncio.run(dummy._fetch_contratos())

    assert fake_service.calls == [(26, True)]
    assert dummy.total_contratos_lista == 1
    assert dummy.contratos[0]["fecha_fin_fmt"] == "01/02/2026"
    assert dummy.contratos[0]["vigencia_label"] == "VENCIDO"


def test_fetch_contratos_portal_filtra_activos_solo_cuando_se_pide(monkeypatch):
    dummy = _DummyMisContratosState("ACTIVO")
    fake_service = _FakeContratoService()

    monkeypatch.setattr(
        mis_contratos_module,
        "contrato_service",
        fake_service,
    )

    asyncio.run(dummy._fetch_contratos())

    assert fake_service.calls == [(26, False)]
    assert dummy.total_contratos_lista == 1
