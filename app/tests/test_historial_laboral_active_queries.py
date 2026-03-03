"""Tests unitarios para consultas que dependen del historial laboral vigente."""

import asyncio

from app.repositories.empleado_repository import SupabaseEmpleadoRepository
from app.services.nomina_periodo_service import NominaPeriodoService


class FakeResult:
    """Resultado mínimo compatible con el cliente de Supabase."""

    def __init__(self, data=None, count=None):
        self.data = data or []
        self.count = count


class FakeSupabaseTable:
    """Tabla fake encadenable que registra llamadas."""

    def __init__(self, client, table_name: str):
        self._client = client
        self._table_name = table_name

    def select(self, fields, **kwargs):
        self._client.calls.append((self._table_name, "select", fields, kwargs))
        return self

    def in_(self, field, values):
        self._client.calls.append((self._table_name, "in_", field, list(values)))
        return self

    def eq(self, field, value):
        self._client.calls.append((self._table_name, "eq", field, value))
        return self

    def is_(self, field, value):
        self._client.calls.append((self._table_name, "is_", field, value))
        return self

    def order(self, field, desc=False):
        self._client.calls.append((self._table_name, "order", field, desc))
        return self

    def limit(self, value):
        self._client.calls.append((self._table_name, "limit", value))
        return self

    def execute(self):
        self._client.calls.append((self._table_name, "execute"))
        responses = self._client.responses[self._table_name]
        return responses.pop(0)


class FakeSupabaseClient:
    """Cliente fake con respuestas por tabla."""

    def __init__(self, responses: dict[str, list[FakeResult]]):
        self.responses = responses
        self.calls: list[tuple] = []

    def table(self, table_name: str) -> FakeSupabaseTable:
        return FakeSupabaseTable(self, table_name)


class FakeDBManager:
    """DB manager fake para inyectar el cliente en repositorios."""

    def __init__(self, client):
        self._client = client

    def get_client(self):
        return self._client


def _historial_calls(client: FakeSupabaseClient) -> list[tuple]:
    return [call for call in client.calls if call[0] == "historial_laboral"]


class TestHistorialLaboralActiveQueries:
    """Protege el criterio de vigencia basado en `fecha_fin`."""

    def test_nomina_resuelve_salario_con_historial_vigente(self):
        client = FakeSupabaseClient(
            {
                "historial_laboral": [
                    FakeResult(
                        [
                            {"empleado_id": 1, "plaza_id": 10, "fecha_inicio": "2026-01-15"},
                            {"empleado_id": 2, "plaza_id": None, "fecha_inicio": "2026-01-20"},
                        ]
                    )
                ],
                "plazas": [FakeResult([{"id": 10, "salario_mensual": "9000"}])],
            }
        )
        service = object.__new__(NominaPeriodoService)
        service.supabase = client
        service.tabla = "periodos_nomina"
        service.tabla_nom_emp = "nominas_empleado"

        result = service._mapear_salario_diario_por_empleado([1, 2])

        assert result == {1: 300.0}
        historial_calls = _historial_calls(client)
        assert ("historial_laboral", "is_", "fecha_fin", "null") in historial_calls
        assert ("historial_laboral", "order", "fecha_inicio", True) in historial_calls
        assert not any(
            call[1] == "eq" and call[2] == "estatus"
            for call in historial_calls
        )

    def test_empleados_disponibles_ignora_historial_abierto_sin_plaza(self):
        client = FakeSupabaseClient(
            {
                "historial_laboral": [
                    FakeResult(
                        [
                            {"empleado_id": 1, "plaza_id": 25},
                            {"empleado_id": 2, "plaza_id": None},
                        ]
                    )
                ],
                "empleados": [
                    FakeResult(
                        [
                            {
                                "id": 1,
                                "clave": "B26-00001",
                                "curp": "AAAA010101HPLBBB01",
                                "nombre": "ANA",
                                "apellido_paterno": "UNO",
                                "apellido_materno": "A",
                                "empresa_id": 7,
                                "estatus": "ACTIVO",
                                "fecha_ingreso": "2026-01-01",
                                "empresas": {"nombre_comercial": "ACME"},
                            },
                            {
                                "id": 2,
                                "clave": "B26-00002",
                                "curp": "BBBB010101HPLBBB02",
                                "nombre": "BETO",
                                "apellido_paterno": "DOS",
                                "apellido_materno": "B",
                                "empresa_id": 7,
                                "estatus": "ACTIVO",
                                "fecha_ingreso": "2026-01-01",
                                "empresas": {"nombre_comercial": "ACME"},
                            },
                            {
                                "id": 3,
                                "clave": "B26-00003",
                                "curp": "CCCC010101HPLBBB03",
                                "nombre": "CARLA",
                                "apellido_paterno": "TRES",
                                "apellido_materno": "C",
                                "empresa_id": 7,
                                "estatus": "ACTIVO",
                                "fecha_ingreso": "2026-01-01",
                                "empresas": {"nombre_comercial": "ACME"},
                            },
                        ]
                    )
                ],
            }
        )
        repository = SupabaseEmpleadoRepository(db_manager=FakeDBManager(client))

        result = asyncio.run(repository.obtener_disponibles_para_asignacion())

        assert [item.id for item in result] == [2, 3]
        historial_calls = _historial_calls(client)
        assert ("historial_laboral", "is_", "fecha_fin", "null") in historial_calls
        assert not any(
            call[1] == "eq" and call[2] == "estatus"
            for call in historial_calls
        )
