"""Tests del motor de calculo quincenal con regla REAL/MIXTA."""

import asyncio
import importlib
import os
import sys
import types
from decimal import Decimal
from types import SimpleNamespace


class _ImportStubSupabaseClient:
    def table(self, *_args, **_kwargs):
        return self

    def select(self, *_args, **_kwargs):
        return self

    def limit(self, *_args, **_kwargs):
        return self

    def execute(self):
        return types.SimpleNamespace(data=[], count=0)


os.environ.setdefault("SUPABASE_URL", "http://localhost")
os.environ.setdefault("SUPABASE_KEY", "test-key")
os.environ.setdefault("SUPABASE_SERVICE_KEY", "test-service-key")
services_pkg = types.ModuleType("app.services")
services_pkg.__path__ = [os.path.join(os.getcwd(), "app", "services")]
sys.modules.setdefault("app.services", services_pkg)
sys.modules.setdefault(
    "dotenv",
    types.SimpleNamespace(load_dotenv=lambda *_args, **_kwargs: False),
)
sys.modules.setdefault(
    "supabase",
    types.SimpleNamespace(
        create_client=lambda *_args, **_kwargs: _ImportStubSupabaseClient(),
        Client=object,
    ),
)

from app.core.enums import PeriodicidadNomina, ReglaCalculoQuincenal

nomina_calculo_module = importlib.import_module("app.services.nomina_calculo_service")


class _FakeResult:
    def __init__(self, data=None):
        self.data = data or []


class _FakeSupabaseTable:
    def __init__(self, client, table_name: str):
        self._client = client
        self._table_name = table_name

    def select(self, *_args, **_kwargs):
        return self

    def update(self, payload):
        self._client.updates.setdefault(self._table_name, []).append(payload)
        return self

    def insert(self, payload):
        self._client.inserts.setdefault(self._table_name, []).append(payload)
        return self

    def delete(self):
        self._client.deletes.append(self._table_name)
        return self

    def eq(self, *_args, **_kwargs):
        return self

    def neq(self, *_args, **_kwargs):
        return self

    def execute(self):
        responses = self._client.responses.setdefault(self._table_name, [])
        if responses:
            return responses.pop(0)
        return _FakeResult([])


class _FakeSupabaseClient:
    def __init__(self, responses=None):
        self.responses = responses or {}
        self.inserts: dict[str, list] = {}
        self.updates: dict[str, list] = {}
        self.deletes: list[str] = []

    def table(self, table_name: str) -> _FakeSupabaseTable:
        return _FakeSupabaseTable(self, table_name)


def _build_service(fake_client: _FakeSupabaseClient):
    service = object.__new__(nomina_calculo_module.NominaCalculoService)
    service.supabase = fake_client
    service.calculadora_imss = SimpleNamespace(
        calcular_obrero=lambda **_kwargs: ({}, {}),
    )
    service._concepto_ids = {
        "SUELDO": 1,
        "DESCUENTO_FALTAS": 2,
        "DESCUENTO_INCAPACIDAD": 3,
        "HORAS_EXTRA_DOBLES": 4,
        "HORAS_EXTRA_TRIPLES": 5,
        "PRIMA_DOMINICAL": 6,
        "ISR": 7,
        "IMSS_OBRERO": 8,
        "SUBSIDIO_EMPLEO": 9,
    }
    return service


def _desactivar_isr_y_subsidio(monkeypatch):
    monkeypatch.setattr(
        nomina_calculo_module.CatalogoISR,
        "calcular_isr_mensual",
        lambda _base: Decimal("0"),
    )
    monkeypatch.setattr(
        nomina_calculo_module.CatalogoISR,
        "calcular_subsidio",
        lambda _base: Decimal("0"),
    )


def test_calculo_quincenal_mixto_usa_base_fija_y_descuento_separado(monkeypatch):
    _desactivar_isr_y_subsidio(monkeypatch)
    fake_client = _FakeSupabaseClient({"nomina_movimientos": [_FakeResult([])]})
    service = _build_service(fake_client)

    nomina = {
        "id": 501,
        "empleado_id": 22,
        "salario_diario": 100,
        "salario_diario_integrado": 100,
        "dias_trabajados": 14,
        "dias_faltas": 1,
        "dias_incapacidad": 0,
        "dias_periodo": 15,
        "horas_extra_dobles": 0,
        "horas_extra_triples": 0,
        "domingos_trabajados": 0,
    }
    periodo = {
        "id": 44,
        "empresa_id": 7,
        "periodicidad": PeriodicidadNomina.QUINCENAL.value,
        "regla_calculo_quincenal": ReglaCalculoQuincenal.MIXTA.value,
    }

    result = asyncio.run(service._calcular_nomina_empleado(nomina, periodo))

    movimientos = fake_client.inserts["nomina_movimientos"][0]
    assert movimientos == [
        {
            "nomina_empleado_id": 501,
            "concepto_id": 1,
            "tipo": "PERCEPCION",
            "origen": "SISTEMA",
            "monto": 1500.0,
            "monto_gravable": 1500.0,
            "monto_exento": 0.0,
            "es_automatico": True,
        },
        {
            "nomina_empleado_id": 501,
            "concepto_id": 2,
            "tipo": "DEDUCCION",
            "origen": "SISTEMA",
            "monto": 100.0,
            "monto_gravable": 0.0,
            "monto_exento": 0.0,
            "es_automatico": True,
        },
    ]
    assert result["total_percepciones"] == Decimal("1500.00")
    assert result["total_deducciones"] == Decimal("100.00")
    assert result["total_neto"] == Decimal("1400.00")


def test_calculo_quincenal_real_no_duplica_descuentos(monkeypatch):
    _desactivar_isr_y_subsidio(monkeypatch)
    fake_client = _FakeSupabaseClient({"nomina_movimientos": [_FakeResult([])]})
    service = _build_service(fake_client)

    nomina = {
        "id": 601,
        "empleado_id": 23,
        "salario_diario": 100,
        "salario_diario_integrado": 100,
        "dias_trabajados": 12,
        "dias_faltas": 1,
        "dias_incapacidad": 2,
        "dias_periodo": 15,
        "horas_extra_dobles": 0,
        "horas_extra_triples": 0,
        "domingos_trabajados": 0,
    }
    periodo = {
        "id": 45,
        "empresa_id": 7,
        "periodicidad": PeriodicidadNomina.QUINCENAL.value,
        "regla_calculo_quincenal": ReglaCalculoQuincenal.REAL.value,
    }

    result = asyncio.run(service._calcular_nomina_empleado(nomina, periodo))

    movimientos = fake_client.inserts["nomina_movimientos"][0]
    assert movimientos == [
        {
            "nomina_empleado_id": 601,
            "concepto_id": 1,
            "tipo": "PERCEPCION",
            "origen": "SISTEMA",
            "monto": 1200.0,
            "monto_gravable": 1200.0,
            "monto_exento": 0.0,
            "es_automatico": True,
        }
    ]
    assert result["total_percepciones"] == Decimal("1200.00")
    assert result["total_deducciones"] == Decimal("0.00")
    assert result["total_neto"] == Decimal("1200.00")


def test_resolver_regla_quincenal_hereda_config_y_persiste_snapshot(monkeypatch):
    fake_client = _FakeSupabaseClient()
    service = _build_service(fake_client)

    async def _fake_config(_empresa_id: int):
        return SimpleNamespace(
            regla_calculo_quincenal=ReglaCalculoQuincenal.REAL.value,
        )

    monkeypatch.setattr(
        nomina_calculo_module.configuracion_operativa_service,
        "obtener_o_crear_default",
        _fake_config,
    )

    periodo = {
        "id": 99,
        "empresa_id": 7,
        "periodicidad": PeriodicidadNomina.QUINCENAL.value,
        "regla_calculo_quincenal": None,
    }

    regla = asyncio.run(service._resolver_regla_calculo_quincenal_periodo(periodo))

    assert regla == ReglaCalculoQuincenal.REAL.value
    assert periodo["regla_calculo_quincenal"] == ReglaCalculoQuincenal.REAL.value
    assert fake_client.updates["periodos_nomina"] == [
        {"regla_calculo_quincenal": "REAL"}
    ]
