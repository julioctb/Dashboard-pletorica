"""Tests unitarios para `NotificacionService.marcar_leida`."""

import asyncio
import sys
import types
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

import pytest

from app.core.exceptions import DatabaseError


class _BootstrapDBManager:
    """Stub para evitar crear cliente real de Supabase al importar el módulo."""

    def get_client(self):
        return object()


class _SimpleNotificacion:
    """Modelo mínimo compatible con el uso del servicio en estas pruebas."""

    def __init__(self, **data):
        self.id = data.get("id")
        self.usuario_id = data.get("usuario_id")
        self.empresa_id = data.get("empresa_id")
        self.titulo = data.get("titulo", "")
        self.mensaje = data.get("mensaje", "")
        self.tipo = data.get("tipo", "")
        self.entidad_tipo = data.get("entidad_tipo")
        self.entidad_id = data.get("entidad_id")
        self.leida = data.get("leida", False)
        self.fecha_creacion = data.get("fecha_creacion")


class _SimpleNotificacionCreate:
    """Placeholder para resolver imports del módulo bajo prueba."""

    def __init__(self, **data):
        self._data = data

    def model_dump(self, **_kwargs):
        return dict(self._data)


class FakeResponse:
    """Respuesta mínima compatible con supabase-py para tests."""

    def __init__(self, data=None, count=None):
        self.data = data
        self.count = count


class FakeQuery:
    """Builder fake de query que registra la operación ejecutada."""

    def __init__(self, supabase, table_name: str):
        self._supabase = supabase
        self._table_name = table_name
        self._action = None
        self._payload = None
        self._filters = []
        self._limit = None
        self._select_fields = None

    def select(self, *fields, count=None):  # noqa: ARG002 - compat con supabase
        self._action = "select"
        self._select_fields = fields
        return self

    def update(self, payload):
        self._action = "update"
        self._payload = payload
        return self

    def eq(self, field, value):
        self._filters.append(("eq", field, value))
        return self

    def limit(self, value):
        self._limit = value
        return self

    def execute(self):
        self._supabase.executed.append(
            {
                "table": self._table_name,
                "action": self._action,
                "payload": self._payload,
                "filters": list(self._filters),
                "limit": self._limit,
                "select_fields": self._select_fields,
            }
        )
        if not self._supabase.results:
            raise AssertionError("No hay respuestas fake disponibles para execute()")
        result = self._supabase.results.pop(0)
        if isinstance(result, Exception):
            raise result
        return result


class FakeSupabase:
    """Cliente fake que devuelve respuestas preprogramadas por `execute()`."""

    def __init__(self, results):
        self.results = list(results)
        self.executed = []

    def table(self, table_name: str):
        return FakeQuery(self, table_name)


_MODULE_PATH = Path(__file__).resolve().parents[1] / "services" / "notificacion_service.py"
_SPEC = spec_from_file_location("test_notificacion_service_module", _MODULE_PATH)
_MOD = module_from_spec(_SPEC)
assert _SPEC and _SPEC.loader

_original_app_database = sys.modules.get("app.database")
_original_app_entities = sys.modules.get("app.entities")
_original_app_entities_notificacion = sys.modules.get("app.entities.notificacion")
_app_database_stub = types.ModuleType("app.database")
_app_database_stub.db_manager = _BootstrapDBManager()
_app_entities_stub = types.ModuleType("app.entities")
_app_entities_stub.__path__ = []
_app_entities_notif_stub = types.ModuleType("app.entities.notificacion")
_app_entities_notif_stub.Notificacion = _SimpleNotificacion
_app_entities_notif_stub.NotificacionCreate = _SimpleNotificacionCreate
sys.modules["app.database"] = _app_database_stub
sys.modules["app.entities"] = _app_entities_stub
sys.modules["app.entities.notificacion"] = _app_entities_notif_stub
try:
    _SPEC.loader.exec_module(_MOD)
finally:
    if _original_app_database is not None:
        sys.modules["app.database"] = _original_app_database
    else:
        sys.modules.pop("app.database", None)
    if _original_app_entities is not None:
        sys.modules["app.entities"] = _original_app_entities
    else:
        sys.modules.pop("app.entities", None)
    if _original_app_entities_notificacion is not None:
        sys.modules["app.entities.notificacion"] = _original_app_entities_notificacion
    else:
        sys.modules.pop("app.entities.notificacion", None)

NotificacionService = _MOD.NotificacionService


def _run(coro):
    return asyncio.run(coro)


def _notif_row(
    *,
    notif_id=1,
    usuario_id=None,
    empresa_id=None,
    leida=False,
):
    return {
        "id": notif_id,
        "usuario_id": usuario_id,
        "empresa_id": empresa_id,
        "titulo": "Titulo",
        "mensaje": "Mensaje",
        "tipo": "entregable_aprobado",
        "entidad_tipo": "ENTREGABLE",
        "entidad_id": 10,
        "leida": leida,
        "fecha_creacion": "2026-02-01T10:00:00+00:00",
    }


def _service_with_results(*results):
    service = NotificacionService()
    fake_supabase = FakeSupabase(results)
    service.supabase = fake_supabase
    return service, fake_supabase


class TestNotificacionServiceMarcarLeida:
    """Cobertura de autorización y no-op para `marcar_leida`."""

    def test_marca_personal_propia(self):
        service, fake = _service_with_results(
            FakeResponse(data=[_notif_row(usuario_id="user-1", leida=False)]),
            FakeResponse(data=[{"id": 1}]),
        )

        result = _run(service.marcar_leida(1, usuario_id="user-1"))

        assert result is True
        assert [call["action"] for call in fake.executed] == ["select", "update"]
        assert ("eq", "leida", False) in fake.executed[1]["filters"]

    def test_rechaza_personal_ajena(self):
        service, fake = _service_with_results(
            FakeResponse(data=[_notif_row(usuario_id="user-owner")]),
        )

        result = _run(service.marcar_leida(1, usuario_id="user-other"))

        assert result is False
        assert [call["action"] for call in fake.executed] == ["select"]

    def test_marca_empresa_propia(self):
        service, _ = _service_with_results(
            FakeResponse(data=[_notif_row(empresa_id=123)]),
            FakeResponse(data=[{"id": 1}]),
        )

        result = _run(service.marcar_leida(1, empresa_id=123))

        assert result is True

    def test_rechaza_empresa_ajena(self):
        service, fake = _service_with_results(
            FakeResponse(data=[_notif_row(empresa_id=123)]),
        )

        result = _run(service.marcar_leida(1, empresa_id=999))

        assert result is False
        assert len(fake.executed) == 1

    def test_marca_global_admin_con_flag(self):
        service, _ = _service_with_results(
            FakeResponse(data=[_notif_row(usuario_id=None, empresa_id=None)]),
            FakeResponse(data=[{"id": 1}]),
        )

        result = _run(service.marcar_leida(1, usuario_id="admin-1", permitir_global_admin=True))

        assert result is True

    def test_rechaza_global_admin_sin_flag(self):
        service, fake = _service_with_results(
            FakeResponse(data=[_notif_row(usuario_id=None, empresa_id=None)]),
        )

        result = _run(service.marcar_leida(1, usuario_id="admin-1", permitir_global_admin=False))

        assert result is False
        assert len(fake.executed) == 1

    def test_retorna_false_si_no_existe(self):
        service, fake = _service_with_results(FakeResponse(data=[]))

        result = _run(service.marcar_leida(1, usuario_id="user-1"))

        assert result is False
        assert len(fake.executed) == 1

    def test_retorna_false_si_ya_estaba_leida(self):
        service, fake = _service_with_results(
            FakeResponse(data=[_notif_row(usuario_id="user-1", leida=True)]),
            FakeResponse(data=[]),
        )

        result = _run(service.marcar_leida(1, usuario_id="user-1"))

        assert result is False
        assert [call["action"] for call in fake.executed] == ["select", "update"]
        assert fake.executed[1]["payload"] == {"leida": True}

    def test_lanza_value_error_sin_contexto(self):
        service, fake = _service_with_results()

        with pytest.raises(ValueError):
            _run(service.marcar_leida(1))

        assert fake.executed == []

    def test_propaga_database_error_en_fallo_bd(self):
        service, fake = _service_with_results(
            FakeResponse(data=[_notif_row(usuario_id="user-1")]),
            RuntimeError("db down"),
        )

        with pytest.raises(DatabaseError) as raised:
            _run(service.marcar_leida(1, usuario_id="user-1"))

        assert "db down" in str(raised.value)
        assert [call["action"] for call in fake.executed] == ["select", "update"]
