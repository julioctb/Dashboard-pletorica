"""Tests del motor de periodos calculados y alta de nómina."""

import asyncio
import importlib
import os
import sys
import types
from datetime import date
from types import SimpleNamespace

import pytest


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

from app.core.catalogs.nomina.periodos import (
    calcular_fecha_pago_mensual,
    calcular_fecha_pago_quincena,
    calcular_fecha_pago_semanal,
    calcular_rango_quincena,
    detectar_periodo_actual,
    generar_catalogo_periodos,
    resolver_periodo_por_key,
    resolver_quincena_por_key,
)
from app.core.enums import PeriodicidadNomina, ReglaCalculoQuincenal
from app.core.exceptions import DuplicateError
from app.core.text_utils import formatear_fecha, formatear_fecha_hora
from app.entities.empleado_descuento_recurrente import EmpleadoDescuentoRecurrenteCreate

nomina_periodo_module = importlib.import_module("app.services.nomina_periodo_service")


class _FakeResult:
    def __init__(self, data=None, count: int | None = None):
        self.data = data or []
        self.count = count


class _FakeSupabaseTable:
    def __init__(self, client, table_name: str):
        self._client = client
        self._table_name = table_name

    def select(self, fields, **kwargs):
        self._client.calls.append((self._table_name, "select", fields, kwargs))
        return self

    def eq(self, field, value):
        self._client.calls.append((self._table_name, "eq", field, value))
        return self

    def gte(self, field, value):
        self._client.calls.append((self._table_name, "gte", field, value))
        return self

    def lte(self, field, value):
        self._client.calls.append((self._table_name, "lte", field, value))
        return self

    def in_(self, field, values):
        self._client.calls.append((self._table_name, "in", field, tuple(values)))
        return self

    def insert(self, payload):
        self._client.calls.append((self._table_name, "insert", payload))
        self._client.last_insert = payload
        return self

    def update(self, payload):
        self._client.calls.append((self._table_name, "update", payload))
        self._client.last_update = payload
        return self

    def order(self, field, **kwargs):
        self._client.calls.append((self._table_name, "order", field, kwargs))
        return self

    def limit(self, value):
        self._client.calls.append((self._table_name, "limit", value))
        return self

    def execute(self):
        self._client.calls.append((self._table_name, "execute"))
        return self._client.responses[self._table_name].pop(0)


class _FakeSupabaseClient:
    def __init__(self, responses: dict[str, list[_FakeResult]]):
        self.responses = responses
        self.calls: list[tuple] = []
        self.last_insert: dict | None = None
        self.last_update: dict | None = None

    def table(self, table_name: str) -> _FakeSupabaseTable:
        return _FakeSupabaseTable(self, table_name)


class _DuplicateInsertTable(_FakeSupabaseTable):
    def execute(self):
        raise Exception('duplicate key value violates unique constraint "uq_periodo_empresa_rango"')


class _DuplicateInsertClient(_FakeSupabaseClient):
    def table(self, table_name: str) -> _DuplicateInsertTable:
        return _DuplicateInsertTable(self, table_name)


class _DummyNominaRRHHState:
    def _obtener_periodo_disponible_por_key(self, periodo_key: str):
        for item in self.periodos_disponibles_catalogo:
            if item.get("key") == periodo_key:
                return item
        return None

    def set_form_periodo_key(self, v: str):
        self.form_periodo_key = v
        self.error_periodo = ""
        self.limpiar_mensajes()

        periodo = self._obtener_periodo_disponible_por_key(v)
        if periodo and periodo.get("fecha_pago_sugerida"):
            self.form_fecha_pago = str(periodo["fecha_pago_sugerida"])

    @staticmethod
    def _serializar_periodo_ui(periodo: dict) -> dict:
        data = dict(periodo or {})
        data["fecha_inicio_fmt"] = formatear_fecha(data.get("fecha_inicio"))
        data["fecha_fin_fmt"] = formatear_fecha(data.get("fecha_fin"))
        data["fecha_pago_fmt"] = formatear_fecha(
            data.get("fecha_pago"),
            valor_vacio="Sin dato",
        )
        data["fecha_creacion_fmt"] = formatear_fecha_hora(
            data.get("fecha_creacion"),
            valor_vacio="Sin dato",
        )
        data["creado_por_nombre_fmt"] = (
            str(data.get("creado_por_nombre") or "").strip() or "Sin dato"
        )
        return data

    def __init__(self):
        self.periodos_disponibles_catalogo = [
            {
                "key": "QUINCENAL:2026-03-1Q",
                "label": "1A Quincena Marzo: 1 - 15 Marzo",
                "nombre": "1A Quincena Marzo 2026",
                "fecha_inicio": "2026-03-01",
                "fecha_fin": "2026-03-15",
                "fecha_pago_sugerida": "2026-03-15",
            }
        ]
        self.form_periodo_key = ""
        self.form_fecha_pago = ""
        self.error_periodo = ""
        self.mensaje_info = ""
        self.tipo_mensaje = "info"

    def limpiar_mensajes(self):
        self.mensaje_info = ""
        self.tipo_mensaje = "info"


def _config_quincenal() -> SimpleNamespace:
    return SimpleNamespace(
        tipo_nomina=PeriodicidadNomina.QUINCENAL.value,
        regla_calculo_quincenal=ReglaCalculoQuincenal.MIXTA.value,
        contrato_nomina_id=88,
        dia_pago_primera_quincena=15,
        dia_pago_segunda_quincena=0,
        dia_pago_semanal=5,
        dia_pago_mensual=0,
    )


@pytest.mark.parametrize(
    ("anio", "mes", "numero_quincena", "esperado_inicio", "esperado_fin"),
    [
        (2026, 3, 1, "2026-03-01", "2026-03-15"),
        (2026, 3, 2, "2026-03-16", "2026-03-31"),
        (2026, 4, 2, "2026-04-16", "2026-04-30"),
        (2025, 2, 2, "2025-02-16", "2025-02-28"),
        (2024, 2, 2, "2024-02-16", "2024-02-29"),
    ],
)
def test_calcular_rango_quincena_usa_calendario_real(
    anio: int,
    mes: int,
    numero_quincena: int,
    esperado_inicio: str,
    esperado_fin: str,
):
    inicio, fin = calcular_rango_quincena(anio, mes, numero_quincena)

    assert inicio.isoformat() == esperado_inicio
    assert fin.isoformat() == esperado_fin


def test_calcular_fecha_pago_segunda_quincena_usa_ultimo_dia_si_config_es_cero():
    fecha_pago = calcular_fecha_pago_quincena(
        anio=2026,
        mes=2,
        numero_quincena=2,
        dia_pago_primera_quincena=15,
        dia_pago_segunda_quincena=0,
    )

    assert fecha_pago.isoformat() == "2026-02-28"


def test_calcular_fecha_pago_segunda_quincena_puede_ir_al_mes_siguiente():
    fecha_pago = calcular_fecha_pago_quincena(
        anio=2026,
        mes=3,
        numero_quincena=2,
        dia_pago_primera_quincena=15,
        dia_pago_segunda_quincena=5,
    )

    assert fecha_pago.isoformat() == "2026-04-05"


def test_calcular_fecha_pago_semanal_usa_siguiente_ocurrencia_del_dia_configurado():
    fecha_pago = calcular_fecha_pago_semanal(date(2026, 3, 15), dia_pago_semanal=1)

    assert fecha_pago.isoformat() == "2026-03-16"


def test_calcular_fecha_pago_mensual_usa_mes_siguiente_si_el_dia_ya_pasara():
    fecha_pago = calcular_fecha_pago_mensual(2026, 3, dia_pago_mensual=15)

    assert fecha_pago.isoformat() == "2026-04-15"


def test_resolver_quincena_por_key_genera_nombre_compacto_y_label_largo():
    quincena = resolver_quincena_por_key("2026-03-2Q")

    assert quincena.nombre == "2A Quincena Marzo 2026"
    assert quincena.label == "2A Quincena Marzo: 16 - 31 Marzo"


def test_resolver_periodo_por_key_acepta_enum_como_periodicidad():
    periodo = resolver_periodo_por_key(
        "MENSUAL:2026-03",
        PeriodicidadNomina.MENSUAL,
        dia_pago_mensual=0,
    )

    assert periodo.nombre == "Nomina Marzo 2026"
    assert periodo.fecha_fin.isoformat() == "2026-03-31"


def test_generar_catalogo_periodos_generico_funciona_con_enum():
    catalogo = generar_catalogo_periodos(
        PeriodicidadNomina.SEMANAL,
        fecha_inicio_catalogo=date(2026, 3, 1),
        fecha_fin_catalogo=date(2026, 3, 15),
        dia_pago_semanal=5,
    )

    assert [item.fecha_inicio.isoformat() for item in catalogo] == [
        "2026-02-23",
        "2026-03-02",
        "2026-03-09",
    ]


def test_detectar_periodo_actual_mensual_usa_mes_natural():
    periodo = detectar_periodo_actual(
        PeriodicidadNomina.MENSUAL,
        fecha_referencia=date(2026, 3, 9),
        dia_pago_mensual=0,
    )

    assert periodo.titulo_actual == "Marzo"
    assert periodo.rango_actual_label == "1 - 31 Marzo"


def test_listar_periodos_disponibles_excluye_rangos_ya_creados(monkeypatch):
    fake_client = _FakeSupabaseClient(
        {
            "periodos_nomina": [
                _FakeResult(
                    [
                        {
                            "fecha_inicio": "2026-03-01",
                            "fecha_fin": "2026-03-15",
                        }
                    ]
                )
            ]
        }
    )
    service = object.__new__(nomina_periodo_module.NominaPeriodoService)
    service.supabase = fake_client
    service.tabla = "periodos_nomina"
    service.tabla_nom_emp = "nominas_empleado"

    async def _fake_config(_empresa_id: int):
        return _config_quincenal()

    monkeypatch.setattr(service, "_obtener_configuracion_nomina", _fake_config)
    monkeypatch.setattr(
        service,
        "_rango_catalogo_periodos",
        lambda: (
            nomina_periodo_module.date(2026, 3, 1),
            nomina_periodo_module.date(2026, 3, 31),
        ),
    )

    result = asyncio.run(service.listar_periodos_disponibles(7))

    assert [item["key"] for item in result] == ["QUINCENAL:2026-03-2Q"]
    assert result[0]["label"] == "2A Quincena Marzo: 16 - 31 Marzo"


def test_crear_periodo_configurado_persiste_auditoria_y_puebla_empleados(monkeypatch):
    fake_client = _FakeSupabaseClient(
        {
            "periodos_nomina": [
                _FakeResult(
                    [
                        {
                            "id": 44,
                            "empresa_id": 7,
                            "nombre": "1A Quincena Marzo 2026",
                            "periodicidad": "QUINCENAL",
                            "fecha_inicio": "2026-03-01",
                            "fecha_fin": "2026-03-15",
                            "fecha_pago": "2026-03-15",
                        }
                    ]
                )
            ]
        }
    )
    service = object.__new__(nomina_periodo_module.NominaPeriodoService)
    service.supabase = fake_client
    service.tabla = "periodos_nomina"
    service.tabla_nom_emp = "nominas_empleado"

    async def _fake_config(_empresa_id: int):
        return _config_quincenal()

    async def _fake_resolver_contrato(_empresa_id: int, contrato_id: int | None):
        assert contrato_id == 88
        return 88

    async def _fake_sync_contrato(_empresa_id: int, contrato_id: int | None):
        assert contrato_id == 88

    async def _fake_poblar_empleados(periodo_id: int) -> int:
        assert periodo_id == 44
        return 12

    monkeypatch.setattr(service, "_obtener_configuracion_nomina", _fake_config)
    monkeypatch.setattr(service, "_resolver_contrato_nomina_id_periodo", _fake_resolver_contrato)
    monkeypatch.setattr(service, "_sincronizar_contrato_nomina_configurado", _fake_sync_contrato)
    monkeypatch.setattr(service, "poblar_empleados", _fake_poblar_empleados)

    result = asyncio.run(
        service.crear_periodo_configurado(
            empresa_id=7,
            periodo_key="QUINCENAL:2026-03-1Q",
            contrato_id=88,
            fecha_pago_override=None,
            usuario_id="user-123",
            usuario_nombre="Ana RRHH",
        )
    )

    assert fake_client.last_insert == {
        "empresa_id": 7,
        "nombre": "1A Quincena Marzo 2026",
        "periodicidad": "QUINCENAL",
        "regla_calculo_quincenal": "MIXTA",
        "fecha_inicio": "2026-03-01",
        "fecha_fin": "2026-03-15",
        "estatus": "BORRADOR",
        "contrato_id": 88,
        "fecha_pago": "2026-03-15",
        "creado_por": "user-123",
        "creado_por_nombre": "Ana RRHH",
    }
    assert result["total_empleados_poblados"] == 12


def test_crear_periodo_configurado_rechaza_duplicados_por_rango(monkeypatch):
    service = object.__new__(nomina_periodo_module.NominaPeriodoService)
    service.supabase = _DuplicateInsertClient({"periodos_nomina": []})
    service.tabla = "periodos_nomina"
    service.tabla_nom_emp = "nominas_empleado"

    async def _fake_config(_empresa_id: int):
        return _config_quincenal()

    async def _fake_resolver_contrato(_empresa_id: int, contrato_id: int | None):
        assert contrato_id is None
        return 88

    async def _fake_sync_contrato(_empresa_id: int, contrato_id: int | None):
        assert contrato_id == 88

    monkeypatch.setattr(service, "_obtener_configuracion_nomina", _fake_config)
    monkeypatch.setattr(service, "_resolver_contrato_nomina_id_periodo", _fake_resolver_contrato)
    monkeypatch.setattr(service, "_sincronizar_contrato_nomina_configurado", _fake_sync_contrato)

    with pytest.raises(DuplicateError):
        asyncio.run(
            service.crear_periodo_configurado(
                empresa_id=7,
                periodo_key="QUINCENAL:2026-03-1Q",
                usuario_id="user-123",
                usuario_nombre="Ana RRHH",
            )
        )


def test_transicionar_a_preparacion_materializa_descuentos_recurrentes_rrhh(monkeypatch):
    fake_client = _FakeSupabaseClient(
        {
            "conceptos_nomina": [
                _FakeResult(
                    [
                        {"id": 201, "clave": "DESCUENTO_INFONAVIT"},
                        {"id": 202, "clave": "PENSION_ALIMENTICIA"},
                    ]
                )
            ],
            "nomina_movimientos": [
                _FakeResult(
                    [
                        {"nomina_empleado_id": 501, "concepto_id": 201},
                    ]
                ),
                _FakeResult([{"id": 901}]),
            ],
            "periodos_nomina": [
                _FakeResult(
                    [
                        {
                            "id": 44,
                            "estatus": "EN_PREPARACION_RRHH",
                        }
                    ]
                )
            ],
        }
    )
    service = object.__new__(nomina_periodo_module.NominaPeriodoService)
    service.supabase = fake_client
    service.tabla = "periodos_nomina"
    service.tabla_nom_emp = "nominas_empleado"

    async def _fake_obtener_periodo(_periodo_id: int):
        return {
            "id": 44,
            "estatus": "BORRADOR",
            "fecha_inicio": "2026-03-01",
            "fecha_fin": "2026-03-15",
        }

    async def _fake_descuentos_vigentes(_empleado_ids, fecha_inicio, fecha_fin):
        assert fecha_inicio.isoformat() == "2026-03-01"
        assert fecha_fin.isoformat() == "2026-03-15"
        return {
            9: [
                EmpleadoDescuentoRecurrenteCreate(
                    empleado_id=9,
                    concepto_clave="DESCUENTO_INFONAVIT",
                    monto_periodico="1500.00",
                    fecha_inicio=date(2026, 1, 1),
                ),
                EmpleadoDescuentoRecurrenteCreate(
                    empleado_id=9,
                    concepto_clave="PENSION_ALIMENTICIA",
                    monto_periodico="900.00",
                    fecha_inicio=date(2026, 2, 1),
                    notas="Expediente 55/2026",
                ),
            ]
        }

    monkeypatch.setattr(service, "obtener_periodo", _fake_obtener_periodo)
    monkeypatch.setattr(
        service,
        "_consultar_empleados_periodo",
        lambda _periodo_id: [{"id": 501, "empleado_id": 9}],
    )
    sys.modules["app.services.empleado_descuento_recurrente_service"] = types.SimpleNamespace(
        empleado_descuento_recurrente_service=types.SimpleNamespace(
            obtener_vigentes_en_rango=_fake_descuentos_vigentes,
        )
    )

    result = asyncio.run(
        service.transicionar_estatus(44, "EN_PREPARACION_RRHH", "user-123")
    )

    assert fake_client.last_insert == [
        {
            "nomina_empleado_id": 501,
            "concepto_id": 202,
            "tipo": "DEDUCCION",
            "origen": "RRHH",
            "monto": 900.0,
            "monto_gravable": 0.0,
            "monto_exento": 0.0,
            "es_automatico": True,
            "notas": "Expediente 55/2026",
        }
    ]
    assert fake_client.last_update == {"estatus": "EN_PREPARACION_RRHH"}
    assert result["estatus"] == "EN_PREPARACION_RRHH"


def test_state_autorrellena_fecha_pago_al_seleccionar_periodo():
    dummy = _DummyNominaRRHHState()

    dummy.set_form_periodo_key("QUINCENAL:2026-03-1Q")

    assert dummy.form_periodo_key == "QUINCENAL:2026-03-1Q"
    assert dummy.form_fecha_pago == "2026-03-15"
    assert dummy.error_periodo == ""


def test_state_serializa_periodo_viejo_con_fallback_de_auditoria():
    data = _DummyNominaRRHHState._serializar_periodo_ui(
        {
            "nombre": "1A Quincena Marzo 2025",
            "fecha_inicio": "2025-03-01",
            "fecha_fin": "2025-03-15",
            "fecha_pago": None,
            "fecha_creacion": None,
            "creado_por_nombre": None,
        }
    )

    assert data["fecha_pago_fmt"] == "Sin dato"
    assert data["fecha_creacion_fmt"] == "Sin dato"
    assert data["creado_por_nombre_fmt"] == "Sin dato"


def test_dias_trabajados_ui_quincenal_mixta_tiene_tope_15():
    service = object.__new__(nomina_periodo_module.NominaPeriodoService)

    assert service._dias_trabajados_ui_periodo(
        PeriodicidadNomina.QUINCENAL.value,
        ReglaCalculoQuincenal.MIXTA.value,
        16,
    ) == 15


def test_dias_trabajados_ui_quincenal_real_conserva_dias_reales():
    service = object.__new__(nomina_periodo_module.NominaPeriodoService)

    assert service._dias_trabajados_ui_periodo(
        PeriodicidadNomina.QUINCENAL.value,
        ReglaCalculoQuincenal.REAL.value,
        16,
    ) == 16


def test_resumen_operativo_cuenta_permiso_sin_goce_como_inasistencia(monkeypatch):
    fake_client = _FakeSupabaseClient(
        {
            "registros_asistencia": [
                _FakeResult([], count=4),
                _FakeResult([], count=1),
            ]
        }
    )
    service = object.__new__(nomina_periodo_module.NominaPeriodoService)
    service.supabase = fake_client
    service.tabla = "periodos_nomina"
    service.tabla_nom_emp = "nominas_empleado"

    async def _fake_config(_empresa_id: int):
        return _config_quincenal()

    async def _fake_validar_contrato(_empresa_id: int, _contrato_id: int):
        return None

    async def _fake_totales_contrato(_contrato_id: int):
        return SimpleNamespace(total_plazas=10, plazas_ocupadas=7)

    monkeypatch.setattr(service, "_obtener_configuracion_nomina", _fake_config)
    monkeypatch.setattr(
        nomina_periodo_module.configuracion_operativa_service,
        "validar_contrato_nomina",
        _fake_validar_contrato,
    )
    sys.modules["app.services"].plaza_service = types.SimpleNamespace(
        calcular_totales_contrato=_fake_totales_contrato,
    )

    resumen = asyncio.run(
        service.obtener_resumen_operativo_actual(
            7,
            fecha_referencia=date(2026, 3, 9),
        )
    )

    assert resumen["inasistencias"] == 4
    assert (
        "registros_asistencia",
        "in",
        "tipo_registro",
        ("FALTA", "PERMISO_SIN_GOCE"),
    ) in fake_client.calls
