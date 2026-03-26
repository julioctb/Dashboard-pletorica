"""Tests unitarios para el desglose de categorías dentro del wizard de contratos."""

import asyncio
from decimal import Decimal

from core.presentation.pages.backoffice.contratos import contratos_state as contratos_state_module


class _DummyContratosState:
    _usa_desglose_categorias_plazas = (
        contratos_state_module.ContratosState._usa_desglose_categorias_plazas
    )
    _obtener_totales_plazas_desde_categorias = (
        contratos_state_module.ContratosState._obtener_totales_plazas_desde_categorias
    )
    _obtener_totales_plazas_formulario = (
        contratos_state_module.ContratosState._obtener_totales_plazas_formulario
    )
    _obtener_totales_montos_desde_categorias = (
        contratos_state_module.ContratosState._obtener_totales_montos_desde_categorias
    )
    _obtener_totales_montos_formulario = (
        contratos_state_module.ContratosState._obtener_totales_montos_formulario
    )
    _sincronizar_montos_desde_categorias = (
        contratos_state_module.ContratosState._sincronizar_montos_desde_categorias
    )
    _sincronizar_totales_plazas_desde_categorias = (
        contratos_state_module.ContratosState._sincronizar_totales_plazas_desde_categorias
    )
    _guardar_categorias_contrato_configuradas = (
        contratos_state_module.ContratosState._guardar_categorias_contrato_configuradas
    )
    _parse_decimal = contratos_state_module.ContratosState._parse_decimal
    _auto_set_poliza = contratos_state_module.ContratosState._auto_set_poliza

    def __init__(self):
        self.form_tiene_personal = True
        self.form_tipo_contrato = contratos_state_module.TipoContrato.SERVICIOS.value
        self.form_cantidad_plazas_minima = "1"
        self.form_cantidad_plazas_maxima = "2"
        self.form_monto_minimo = ""
        self.form_monto_maximo = ""
        self.form_requiere_poliza = False
        self.form_categorias_contrato = []
        self.categorias_contrato_cargadas = True


class _FakeContratoCategoriaService:
    def __init__(self):
        self.calls = []

    async def reemplazar_categorias(self, contrato_id: int, categorias: list[dict]):
        self.calls.append((contrato_id, categorias))


class _FakePlazaService:
    def __init__(self):
        self.calls = []

    async def sincronizar_categorias_desde_contrato(self, contrato_id: int):
        self.calls.append(contrato_id)


def test_totales_plazas_se_derivan_del_desglose_categorias():
    dummy = _DummyContratosState()
    dummy.form_categorias_contrato = [
        {
            "categoria_puesto_id": 10,
            "categoria_clave": "JARA",
            "categoria_nombre": "JARDINERO A",
            "cantidad_minima": 10,
            "cantidad_maxima": 15,
            "costo_unitario": "$ 100",
        },
        {
            "categoria_puesto_id": 20,
            "categoria_clave": "SUP",
            "categoria_nombre": "SUPERVISOR",
            "cantidad_minima": 5,
            "cantidad_maxima": 7,
            "costo_unitario": "$ 200",
        },
    ]

    assert dummy._obtener_totales_plazas_formulario() == (15, 22)
    assert dummy._obtener_totales_montos_formulario() == (
        Decimal("2000"),
        Decimal("2900"),
    )

    dummy._sincronizar_totales_plazas_desde_categorias()

    assert dummy.form_cantidad_plazas_minima == "15"
    assert dummy.form_cantidad_plazas_maxima == "22"
    assert dummy.form_monto_minimo == "$ 2,000"
    assert dummy.form_monto_maximo == "$ 2,900"


def test_guardar_categorias_reemplaza_desglose_del_contrato(monkeypatch):
    dummy = _DummyContratosState()
    dummy.form_categorias_contrato = [
        {
            "categoria_puesto_id": 10,
            "cantidad_minima": 10,
            "cantidad_maxima": 15,
            "costo_unitario": "$ 12,345.67",
        },
        {
            "categoria_puesto_id": 20,
            "cantidad_minima": 5,
            "cantidad_maxima": 7,
            "costo_unitario": "9800",
        },
    ]
    fake_service = _FakeContratoCategoriaService()
    fake_plaza_service = _FakePlazaService()

    monkeypatch.setattr(
        contratos_state_module,
        "contrato_categoria_service",
        fake_service,
    )
    monkeypatch.setattr(
        contratos_state_module,
        "plaza_service",
        fake_plaza_service,
    )

    asyncio.run(dummy._guardar_categorias_contrato_configuradas(9))

    assert fake_service.calls == [
        (
            9,
            [
                {
                    "categoria_puesto_id": 10,
                    "cantidad_minima": 10,
                    "cantidad_maxima": 15,
                    "costo_unitario": Decimal("12345.67"),
                },
                {
                    "categoria_puesto_id": 20,
                    "cantidad_minima": 5,
                    "cantidad_maxima": 7,
                    "costo_unitario": Decimal("9800"),
                },
            ],
        )
    ]
    assert fake_plaza_service.calls == [9]


def test_guardar_categorias_no_toca_relacion_si_no_se_cargaron_en_edicion(monkeypatch):
    dummy = _DummyContratosState()
    dummy.categorias_contrato_cargadas = False
    fake_service = _FakeContratoCategoriaService()

    monkeypatch.setattr(
        contratos_state_module,
        "contrato_categoria_service",
        fake_service,
    )

    asyncio.run(dummy._guardar_categorias_contrato_configuradas(12))

    assert fake_service.calls == []
