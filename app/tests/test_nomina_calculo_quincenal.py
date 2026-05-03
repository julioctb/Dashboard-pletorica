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
services_pkg = types.ModuleType("app.domain.services")
services_pkg.__path__ = [os.path.join(os.getcwd(), "app", "domain", "services")]
sys.modules.setdefault("app.domain.services", services_pkg)
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

from app.core.catalogs import (
    CatalogoISR,
    CatalogoSalarioMinimo,
    CatalogoUMA,
    PoliticaFiscalResolver,
)
from app.domain.enums import (
    PeriodicidadNomina,
    ReglaCalculoQuincenal,
    TipoJornadaPlaza,
)

nomina_calculo_module = importlib.import_module("app.domain.services.nomina_calculo_service")


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
        "AGUINALDO": 10,
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


def test_catalogos_fiscales_resuelven_por_fecha():
    assert CatalogoUMA.diario_vigente("2026-01-15") == Decimal("113.14")
    assert CatalogoUMA.diario_vigente("2026-02-15") == Decimal("117.31")
    assert CatalogoSalarioMinimo.diario_vigente(
        "2026-03-15",
        zona_frontera=False,
    ) == Decimal("315.04")
    assert CatalogoSalarioMinimo.diario_vigente(
        "2026-03-15",
        zona_frontera=True,
    ) == Decimal("440.87")
    assert CatalogoISR.calcular_subsidio(
        Decimal("10000"),
        "2026-01-15",
    ) == Decimal("536.21")
    assert CatalogoISR.calcular_subsidio(
        Decimal("10000"),
        "2026-03-15",
    ) == Decimal("535.65")
    assert CatalogoISR.calcular_subsidio_periodo(
        Decimal("10000"),
        Decimal("15"),
        "2026-03-15",
    ) == Decimal("264.30")


def test_catalogos_fiscales_hacen_fallback_a_ultima_vigencia_previa():
    assert CatalogoSalarioMinimo.obtener_vigencia("2027-01-15") is None

    vigencia_salario = CatalogoSalarioMinimo.obtener_vigencia(
        "2027-01-15",
        permitir_fallback=True,
    )
    politica_subsidio = CatalogoISR.obtener_politica_subsidio(
        "2027-01-15",
        permitir_fallback=True,
    )

    assert vigencia_salario is not None
    assert vigencia_salario.general == Decimal("315.04")
    assert politica_subsidio is not None
    assert politica_subsidio.subsidio_mensual == Decimal("535.65")


def test_politica_fiscal_resolver_marca_fallback_cuando_no_hay_vigencia_exacta():
    contexto = PoliticaFiscalResolver.resolver("2027-01-15")

    assert contexto.vigencia_soportada is False
    assert "fallback" in contexto.mensaje_vigencia.lower()
    assert contexto.salario_minimo_diario_aplicable == Decimal("315.04")
    assert contexto.subsidio_mensual == Decimal("535.65")


def test_calculo_isr_incluye_percepciones_manuales_gravables():
    bono_gravable = {
        "tipo": "PERCEPCION",
        "monto": 10000.0,
        "monto_gravable": 10000.0,
        "monto_exento": 0.0,
        "origen": "CONTABILIDAD",
    }
    fake_client = _FakeSupabaseClient({
        "nomina_movimientos": [
            _FakeResult([]),
            _FakeResult([bono_gravable]),
        ],
    })
    service = _build_service(fake_client)

    nomina = {
        "id": 701,
        "empleado_id": 30,
        "salario_diario": "1000.00",
        "salario_diario_integrado": "1000.00",
        "dias_trabajados": 15,
        "dias_faltas": 0,
        "dias_incapacidad": 0,
        "dias_periodo": 15,
        "horas_extra_dobles": 0,
        "horas_extra_triples": 0,
        "domingos_trabajados": 0,
        "tipo_jornada": TipoJornadaPlaza.COMPLETA.value,
        "factor_jornada": "1.0",
    }
    periodo = {
        "id": 70,
        "empresa_id": 7,
        "fecha_pago": "2026-03-15",
        "fecha_fin": "2026-03-15",
        "periodicidad": PeriodicidadNomina.QUINCENAL.value,
        "regla_calculo_quincenal": ReglaCalculoQuincenal.MIXTA.value,
        "zona_frontera": False,
        "aplicar_art_36": True,
    }

    result = asyncio.run(service._calcular_nomina_empleado(nomina, periodo))

    movimientos = fake_client.inserts["nomina_movimientos"][0]
    isr_mov = next(m for m in movimientos if m["concepto_id"] == 7)
    expected_isr = nomina_calculo_module._round2(
        CatalogoISR.calcular_isr_mensual(
            Decimal("50000.00"),
            "2026-03-15",
        ) / Decimal("2")
    )

    assert Decimal(str(isr_mov["monto"])) == expected_isr
    assert result["total_percepciones"] == Decimal("25000.00")
    assert result["total_deducciones"] == expected_isr


def test_salario_minimo_con_percepcion_extra_no_exenta_isr():
    fake_client = _FakeSupabaseClient({
        "nomina_movimientos": [
            _FakeResult([]),
            _FakeResult([]),
        ],
    })
    service = _build_service(fake_client)

    nomina = {
        "id": 702,
        "empleado_id": 31,
        "salario_diario": "315.04",
        "salario_diario_integrado": "315.04",
        "dias_trabajados": 15,
        "dias_faltas": 0,
        "dias_incapacidad": 0,
        "dias_periodo": 15,
        "horas_extra_dobles": 0,
        "horas_extra_triples": 1,
        "domingos_trabajados": 0,
        "tipo_jornada": TipoJornadaPlaza.COMPLETA.value,
        "factor_jornada": "1.0",
    }
    periodo = {
        "id": 71,
        "empresa_id": 7,
        "fecha_pago": "2026-03-15",
        "fecha_fin": "2026-03-15",
        "periodicidad": PeriodicidadNomina.QUINCENAL.value,
        "regla_calculo_quincenal": ReglaCalculoQuincenal.MIXTA.value,
        "zona_frontera": False,
        "aplicar_art_36": True,
    }

    asyncio.run(service._calcular_nomina_empleado(nomina, periodo))

    movimientos = fake_client.inserts["nomina_movimientos"][0]
    by_concepto = {mov["concepto_id"]: mov for mov in movimientos}
    monto_horas_triples = nomina_calculo_module._round2(
        Decimal("315.04") / Decimal("8") * Decimal("3")
    )
    base_mensual = nomina_calculo_module._round2(
        ((Decimal("315.04") * Decimal("15")) + monto_horas_triples) * Decimal("2")
    )
    isr_mensual = CatalogoISR.calcular_isr_mensual(base_mensual, "2026-03-15")
    isr_periodo = nomina_calculo_module._round2(isr_mensual / Decimal("2"))
    subsidio_periodo = min(
        CatalogoISR.calcular_subsidio_periodo(
            base_mensual,
            Decimal("15"),
            "2026-03-15",
        ),
        isr_periodo,
    )

    assert 7 in by_concepto
    assert 9 in by_concepto
    assert Decimal(str(by_concepto[7]["monto"])) == isr_periodo
    assert Decimal(str(by_concepto[9]["monto"])) == nomina_calculo_module._round2(
        subsidio_periodo
    )
    assert fake_client.updates["nominas_empleado"][0]["es_salario_minimo_art36"] is True


def test_calculo_aplica_art36_en_salario_minimo_jornada_completa(monkeypatch):
    _desactivar_isr_y_subsidio(monkeypatch)
    fake_client = _FakeSupabaseClient({"nomina_movimientos": [_FakeResult([])]})
    service = _build_service(fake_client)

    captured = {}

    def _fake_imss(**kwargs):
        captured.update(kwargs)
        return (
            {
                "excedente": 0.0,
                "prest_dinero": 0.0,
                "gastos_med": 0.0,
                "invalidez_vida": 0.0,
                "cesantia_vejez": 0.0,
            },
            45.67,
        )

    service.calculadora_imss = SimpleNamespace(calcular_obrero=_fake_imss)

    nomina = {
        "id": 801,
        "empleado_id": 40,
        "salario_diario": "315.04",
        "salario_diario_integrado": "315.04",
        "dias_trabajados": 15,
        "dias_faltas": 0,
        "dias_incapacidad": 0,
        "dias_periodo": 15,
        "horas_extra_dobles": 0,
        "horas_extra_triples": 0,
        "domingos_trabajados": 0,
        "tipo_jornada": TipoJornadaPlaza.COMPLETA.value,
        "factor_jornada": "1.0",
    }
    periodo = {
        "id": 77,
        "empresa_id": 7,
        "fecha_pago": "2026-03-15",
        "fecha_fin": "2026-03-15",
        "periodicidad": PeriodicidadNomina.QUINCENAL.value,
        "regla_calculo_quincenal": ReglaCalculoQuincenal.MIXTA.value,
        "zona_frontera": False,
        "aplicar_art_36": True,
    }

    result = asyncio.run(service._calcular_nomina_empleado(nomina, periodo))

    assert captured["es_salario_minimo"] is True
    assert captured["aplicar_art_36"] is True
    movimientos = fake_client.inserts["nomina_movimientos"][0]
    assert len(movimientos) == 1
    assert movimientos[0]["concepto_id"] == 1
    update = fake_client.updates["nominas_empleado"][0]
    assert update["es_salario_minimo_art36"] is True
    assert update["imss_obrero_absorbido"] == 45.67
    assert update["listo_para_timbrar"] is True
    assert result["listo_para_timbrar"] is True


def test_calculo_no_absorbe_imss_si_art36_esta_desactivado(monkeypatch):
    _desactivar_isr_y_subsidio(monkeypatch)
    fake_client = _FakeSupabaseClient({"nomina_movimientos": [_FakeResult([])]})
    service = _build_service(fake_client)

    def _fake_imss(**kwargs):
        return (
            {
                "excedente": 0.0,
                "prest_dinero": 10.0,
                "gastos_med": 5.0,
                "invalidez_vida": 4.0,
                "cesantia_vejez": 6.0,
            },
            0.0,
        )

    service.calculadora_imss = SimpleNamespace(calcular_obrero=_fake_imss)

    nomina = {
        "id": 802,
        "empleado_id": 41,
        "salario_diario": "315.04",
        "salario_diario_integrado": "315.04",
        "dias_trabajados": 15,
        "dias_faltas": 0,
        "dias_incapacidad": 0,
        "dias_periodo": 15,
        "horas_extra_dobles": 0,
        "horas_extra_triples": 0,
        "domingos_trabajados": 0,
        "tipo_jornada": TipoJornadaPlaza.COMPLETA.value,
        "factor_jornada": "1.0",
    }
    periodo = {
        "id": 78,
        "empresa_id": 7,
        "fecha_pago": "2026-03-15",
        "fecha_fin": "2026-03-15",
        "periodicidad": PeriodicidadNomina.QUINCENAL.value,
        "regla_calculo_quincenal": ReglaCalculoQuincenal.MIXTA.value,
        "zona_frontera": False,
        "aplicar_art_36": False,
    }

    asyncio.run(service._calcular_nomina_empleado(nomina, periodo))

    movimientos = fake_client.inserts["nomina_movimientos"][0]
    assert [mov["concepto_id"] for mov in movimientos] == [1, 8]
    update = fake_client.updates["nominas_empleado"][0]
    assert update["es_salario_minimo_art36"] is True
    assert update["imss_obrero_absorbido"] == 0.0


def test_calculo_future_catalog_marks_nomina_not_ready(monkeypatch):
    _desactivar_isr_y_subsidio(monkeypatch)
    fake_client = _FakeSupabaseClient({"nomina_movimientos": [_FakeResult([])]})
    service = _build_service(fake_client)

    nomina = {
        "id": 803,
        "empleado_id": 42,
        "salario_diario": "500.00",
        "salario_diario_integrado": "500.00",
        "dias_trabajados": 15,
        "dias_faltas": 0,
        "dias_incapacidad": 0,
        "dias_periodo": 15,
        "horas_extra_dobles": 0,
        "horas_extra_triples": 0,
        "domingos_trabajados": 0,
        "tipo_jornada": TipoJornadaPlaza.COMPLETA.value,
        "factor_jornada": "1.0",
    }
    periodo = {
        "id": 79,
        "empresa_id": 7,
        "fecha_pago": "2028-03-15",
        "fecha_fin": "2028-03-15",
        "periodicidad": PeriodicidadNomina.QUINCENAL.value,
        "regla_calculo_quincenal": ReglaCalculoQuincenal.MIXTA.value,
        "zona_frontera": False,
        "aplicar_art_36": True,
    }

    result = asyncio.run(service._calcular_nomina_empleado(nomina, periodo))

    update = fake_client.updates["nominas_empleado"][0]
    assert update["listo_para_timbrar"] is False
    assert any(
        item["codigo"] == "CATALOGO_FISCAL_NO_VIGENTE"
        for item in update["observaciones_fiscales"]
    )
    assert result["listo_para_timbrar"] is False


def test_calculo_aguinaldo_manual_usa_override_y_no_depende_de_periodicidad(monkeypatch):
    _desactivar_isr_y_subsidio(monkeypatch)
    fake_client = _FakeSupabaseClient({"nomina_movimientos": [_FakeResult([])]})
    service = _build_service(fake_client)

    nomina = {
        "id": 901,
        "empleado_id": 51,
        "salario_diario": "300.00",
        "salario_diario_integrado": "300.00",
        "monto_aguinaldo_bruto": "4500.00",
        "monto_aguinaldo_override": "5200.00",
        "modo_calculo_aguinaldo": "MANUAL",
        "tipo_jornada": TipoJornadaPlaza.COMPLETA.value,
        "factor_jornada": "1.0",
    }
    periodo = {
        "id": 81,
        "empresa_id": 7,
        "tipo_periodo": "AGUINALDO",
        "periodicidad": PeriodicidadNomina.SEMANAL.value,
        "fecha_pago": "2026-12-20",
        "fecha_fin": "2026-12-31",
        "zona_frontera": False,
        "aplicar_art_36": True,
    }

    result = asyncio.run(service._calcular_nomina_empleado(nomina, periodo))

    movimientos = fake_client.inserts["nomina_movimientos"][0]
    assert [mov["concepto_id"] for mov in movimientos] == [10]
    assert movimientos[0]["monto"] == 5200.0
    update = fake_client.updates["nominas_empleado"][0]
    assert update["modo_calculo_aguinaldo"] == "MANUAL"
    assert update["monto_aguinaldo_bruto"] == 4500.0
    assert update["imss_obrero_absorbido"] == 0.0
    assert result["total_percepciones"] == Decimal("5200.00")
    assert result["total_deducciones"] == Decimal("0.00")


def test_calculo_aguinaldo_no_aplica_subsidio_empleo():
    fake_client = _FakeSupabaseClient({"nomina_movimientos": [_FakeResult([])]})
    service = _build_service(fake_client)

    nomina = {
        "id": 902,
        "empleado_id": 52,
        "salario_diario": "315.04",
        "salario_diario_integrado": "315.04",
        "monto_aguinaldo_bruto": "4000.00",
        "modo_calculo_aguinaldo": "AUTO",
        "tipo_jornada": TipoJornadaPlaza.COMPLETA.value,
        "factor_jornada": "1.0",
    }
    periodo = {
        "id": 82,
        "empresa_id": 7,
        "tipo_periodo": "AGUINALDO",
        "periodicidad": PeriodicidadNomina.QUINCENAL.value,
        "regla_calculo_quincenal": ReglaCalculoQuincenal.MIXTA.value,
        "fecha_pago": "2026-12-20",
        "fecha_fin": "2026-12-31",
        "zona_frontera": False,
        "aplicar_art_36": True,
    }

    asyncio.run(service._calcular_nomina_empleado(nomina, periodo))

    movimientos = fake_client.inserts["nomina_movimientos"][0]
    concepto_ids = [mov["concepto_id"] for mov in movimientos]

    assert 10 in concepto_ids
    assert 7 in concepto_ids
    assert 9 not in concepto_ids


def test_guardar_override_aguinaldo_persiste_manual_y_recalcula(monkeypatch):
    fake_client = _FakeSupabaseClient()
    service = _build_service(fake_client)

    async def _fake_nomina(_nomina_id: int):
        return {"id": 777, "periodo_id": 81}

    async def _fake_periodo(_periodo_id: int):
        return {"id": 81, "tipo_periodo": "AGUINALDO"}

    async def _fake_recalculo(_nomina_id: int):
        return {"ok": True}

    monkeypatch.setattr(service, "_obtener_nomina_empleado", _fake_nomina)
    monkeypatch.setattr(service, "_obtener_periodo", _fake_periodo)
    monkeypatch.setattr(service, "recalcular_empleado", _fake_recalculo)

    result = asyncio.run(
        service.guardar_override_aguinaldo(
            777,
            monto_bruto=Decimal("6123.45"),
            notas="Ajuste autorizado",
        )
    )

    assert fake_client.updates["nominas_empleado"] == [
        {
            "modo_calculo_aguinaldo": "MANUAL",
            "monto_aguinaldo_override": "6123.45",
            "notas_aguinaldo_override": "Ajuste autorizado",
        }
    ]
    assert result == {"ok": True}
