"""Tests unitarios del repositorio de incapacidades."""

import asyncio

from core.domain.repositories import SupabaseIncapacidadRepository as InitIncapacidadRepository
from core.domain.repositories.incapacidad_repository import SupabaseIncapacidadRepository


class _FakeResult:
    def __init__(self, data=None, count=None):
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

    def neq(self, field, value):
        self._client.calls.append((self._table_name, "neq", field, value))
        return self

    def is_(self, field, value):
        self._client.calls.append((self._table_name, "is_", field, value))
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

    def table(self, table_name: str) -> _FakeSupabaseTable:
        return _FakeSupabaseTable(self, table_name)


class _FakeDBManager:
    def __init__(self, client):
        self._client = client

    def get_client(self):
        return self._client


def test_app_repositories_expone_repositorio_canonico():
    assert InitIncapacidadRepository is SupabaseIncapacidadRepository


def test_listar_por_empleado_retorna_datos_y_ordena_por_fecha_inicio():
    client = _FakeSupabaseClient(
        {
            "incapacidades": [
                _FakeResult(
                    data=[
                        {
                            "id": 10,
                            "empleado_id": 8,
                            "tipo": "ENF_GENERAL",
                            "estatus": "ACTIVA",
                        }
                    ]
                )
            ]
        }
    )
    repository = SupabaseIncapacidadRepository(db_manager=_FakeDBManager(client))

    result = asyncio.run(repository.listar_por_empleado(8))

    assert result == [
        {
            "id": 10,
            "empleado_id": 8,
            "tipo": "ENF_GENERAL",
            "estatus": "ACTIVA",
        }
    ]
    assert ("incapacidades", "eq", "empleado_id", 8) in client.calls
    assert (
        "incapacidades",
        "order",
        "fecha_inicio",
        {"desc": True},
    ) in client.calls


def test_obtener_activa_por_plaza_retorna_primera_incapacidad_activa():
    client = _FakeSupabaseClient(
        {
            "incapacidades": [
                _FakeResult(
                    data=[
                        {"id": 21, "plaza_id": 5, "estatus": "ACTIVA"},
                        {"id": 22, "plaza_id": 5, "estatus": "ACTIVA"},
                    ]
                )
            ]
        }
    )
    repository = SupabaseIncapacidadRepository(db_manager=_FakeDBManager(client))

    result = asyncio.run(repository.obtener_activa_por_plaza(5))

    assert result == {"id": 21, "plaza_id": 5, "estatus": "ACTIVA"}
    assert ("incapacidades", "eq", "plaza_id", 5) in client.calls
    assert ("incapacidades", "eq", "estatus", "ACTIVA") in client.calls
    assert ("incapacidades", "limit", 1) in client.calls


def test_obtener_abierta_por_empleado_filtra_estatus_cerrada():
    client = _FakeSupabaseClient(
        {
            "incapacidades": [
                _FakeResult(
                    data=[
                        {"id": 31, "empleado_id": 9, "estatus": "VENCIDA"},
                    ]
                )
            ]
        }
    )
    repository = SupabaseIncapacidadRepository(db_manager=_FakeDBManager(client))

    result = asyncio.run(repository.obtener_abierta_por_empleado(9))

    assert result == {"id": 31, "empleado_id": 9, "estatus": "VENCIDA"}
    assert ("incapacidades", "eq", "empleado_id", 9) in client.calls
    assert ("incapacidades", "neq", "estatus", "CERRADA") in client.calls
    assert ("incapacidades", "limit", 1) in client.calls


def test_contar_por_empresa_usa_counts_exactos():
    client = _FakeSupabaseClient(
        {
            "incapacidades": [
                _FakeResult(count=4),
                _FakeResult(count=1),
                _FakeResult(count=6),
            ]
        }
    )
    repository = SupabaseIncapacidadRepository(db_manager=_FakeDBManager(client))

    result = asyncio.run(repository.contar_por_empresa(19))

    assert result == {"activas": 4, "vencidas": 1, "total": 6}
    assert (
        "incapacidades",
        "select",
        "id",
        {"count": "exact"},
    ) in client.calls
    assert ("incapacidades", "eq", "empresa_id", 19) in client.calls
