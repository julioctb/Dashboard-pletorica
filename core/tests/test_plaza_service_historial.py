"""Tests de sincronización de historial laboral desde PlazaService."""

import asyncio
from datetime import date
from decimal import Decimal
from types import SimpleNamespace

import core.domain.services as services_module

from core.core.enums import EstatusPlaza
from core.domain.models.plaza import Plaza
from core.domain.services.plaza_service import PlazaService


def _build_plaza(
    *,
    plaza_id: int,
    empleado_id: int | None,
    estatus: EstatusPlaza,
    salario_mensual: Decimal = Decimal("12500.00"),
) -> Plaza:
    return Plaza(
        id=plaza_id,
        contrato_id=14,
        sede_id=3,
        categoria_puesto_id=7,
        numero_plaza=22,
        codigo="PLA-022",
        empleado_id=empleado_id,
        fecha_inicio=date(2026, 3, 1),
        fecha_fin=None,
        salario_mensual=salario_mensual,
        estatus=estatus,
        notas=None,
    )


class _FakePlazaRepository:
    def __init__(self, plaza: Plaza):
        self.plaza = plaza

    async def obtener_por_id(self, plaza_id: int) -> Plaza:
        assert plaza_id == self.plaza.id
        return self.plaza

    async def actualizar(self, plaza: Plaza) -> Plaza:
        self.plaza = plaza
        return plaza

    async def empleado_tiene_plaza_activa_con_categoria(
        self,
        empleado_id: int,
        *,
        excluir_plaza_id: int | None = None,
    ) -> bool:
        return False


class _FakePlazaRepositoryReasignacion:
    def __init__(self, plazas: list[Plaza]):
        self.plazas = {int(plaza.id or 0): plaza for plaza in plazas}

    async def obtener_por_id(self, plaza_id: int) -> Plaza:
        return self.plazas[plaza_id]

    async def actualizar(self, plaza: Plaza) -> Plaza:
        self.plazas[int(plaza.id or 0)] = plaza
        return plaza

    async def empleado_tiene_plaza_activa_con_categoria(
        self,
        empleado_id: int,
        *,
        excluir_plaza_id: int | None = None,
    ) -> bool:
        return any(
            int(plaza.empleado_id or 0) == empleado_id
            and int(plaza.id or 0) != int(excluir_plaza_id or 0)
            and plaza.categoria_puesto_id is not None
            and plaza.estatus == EstatusPlaza.OCUPADA
            for plaza in self.plazas.values()
        )


class _FakeEmpleadoService:
    def __init__(self):
        self.calls: list[tuple[int, bool]] = []

    async def sincronizar_estatus_por_plazas(
        self,
        empleado_id: int,
        *,
        tiene_plaza_activa: bool,
    ):
        self.calls.append((empleado_id, tiene_plaza_activa))
        return None


class _FakeHistorialLaboralService:
    def __init__(self, registro_activo=None):
        self.registro_activo = registro_activo
        self.calls: list[tuple] = []

    async def obtener_registro_activo(self, empleado_id: int):
        self.calls.append(("obtener", empleado_id))
        return self.registro_activo

    async def registrar_asignacion(self, *, empleado_id: int, plaza_id: int, fecha=None, notas=None):
        self.calls.append(("asignacion", empleado_id, plaza_id))
        return None

    async def registrar_cambio_plaza(
        self,
        *,
        empleado_id: int,
        nueva_plaza_id: int,
        fecha=None,
        notas=None,
    ):
        self.calls.append(("cambio", empleado_id, nueva_plaza_id))
        return None

    async def liberar_plaza_empleado(self, empleado_id: int, fecha=None):
        self.calls.append(("liberar", empleado_id))
        return None

    async def registrar_cambio_salario(
        self,
        *,
        empleado_id: int,
        plaza_id: int,
        salario_anterior: Decimal,
        salario_nuevo: Decimal,
        fecha=None,
        notas=None,
    ):
        self.calls.append(
            ("salario", empleado_id, plaza_id, salario_anterior, salario_nuevo),
        )
        return None


async def _noop_async(*args, **kwargs):
    return None


def test_asignar_empleado_registra_asignacion_en_historial(monkeypatch):
    repository = _FakePlazaRepository(
        _build_plaza(plaza_id=11, empleado_id=None, estatus=EstatusPlaza.VACANTE),
    )
    service = PlazaService(repository=repository)
    fake_empleado_service = _FakeEmpleadoService()
    fake_historial_service = _FakeHistorialLaboralService(
        registro_activo=SimpleNamespace(plaza_id=None),
    )

    monkeypatch.setattr(services_module, "empleado_service", fake_empleado_service)
    monkeypatch.setattr(services_module, "historial_laboral_service", fake_historial_service)

    plaza_actualizada = asyncio.run(service.asignar_empleado(11, 52))

    assert plaza_actualizada.empleado_id == 52
    assert plaza_actualizada.estatus == EstatusPlaza.OCUPADA
    assert ("asignacion", 52, 11) in fake_historial_service.calls
    assert fake_empleado_service.calls == [(52, True)]


def test_liberar_plaza_registra_desasignacion_en_historial(monkeypatch):
    repository = _FakePlazaRepository(
        _build_plaza(plaza_id=11, empleado_id=52, estatus=EstatusPlaza.OCUPADA),
    )
    service = PlazaService(repository=repository)
    fake_empleado_service = _FakeEmpleadoService()
    fake_historial_service = _FakeHistorialLaboralService(
        registro_activo=SimpleNamespace(plaza_id=11),
    )

    monkeypatch.setattr(services_module, "empleado_service", fake_empleado_service)
    monkeypatch.setattr(services_module, "historial_laboral_service", fake_historial_service)

    plaza_actualizada = asyncio.run(service.liberar_plaza(11))

    assert plaza_actualizada.empleado_id is None
    assert plaza_actualizada.estatus == EstatusPlaza.VACANTE
    assert ("liberar", 52) in fake_historial_service.calls
    assert fake_empleado_service.calls == [(52, False)]


def test_reasignar_empleado_a_plaza_registra_cambio_en_historial(monkeypatch):
    plaza_origen = _build_plaza(
        plaza_id=11,
        empleado_id=52,
        estatus=EstatusPlaza.OCUPADA,
    )
    plaza_destino = _build_plaza(
        plaza_id=12,
        empleado_id=None,
        estatus=EstatusPlaza.VACANTE,
    )
    repository = _FakePlazaRepositoryReasignacion([plaza_origen, plaza_destino])
    service = PlazaService(repository=repository)
    fake_empleado_service = _FakeEmpleadoService()
    fake_historial_service = _FakeHistorialLaboralService(
        registro_activo=SimpleNamespace(plaza_id=11),
    )

    monkeypatch.setattr(services_module, "empleado_service", fake_empleado_service)
    monkeypatch.setattr(services_module, "historial_laboral_service", fake_historial_service)

    plaza_actualizada = asyncio.run(
        service.reasignar_empleado_a_plaza(
            plaza_origen_id=11,
            plaza_destino_id=12,
        )
    )

    assert repository.plazas[11].empleado_id is None
    assert repository.plazas[11].estatus == EstatusPlaza.VACANTE
    assert plaza_actualizada.empleado_id == 52
    assert plaza_actualizada.estatus == EstatusPlaza.OCUPADA
    assert ("cambio", 52, 12) in fake_historial_service.calls
    assert fake_empleado_service.calls == [(52, True)]


def test_actualizar_salario_plaza_ocupada_registra_cambio_salarial(monkeypatch):
    repository = _FakePlazaRepository(
        _build_plaza(
            plaza_id=11,
            empleado_id=52,
            estatus=EstatusPlaza.OCUPADA,
            salario_mensual=Decimal("12500.00"),
        ),
    )
    service = PlazaService(repository=repository)
    fake_historial_service = _FakeHistorialLaboralService(
        registro_activo=SimpleNamespace(plaza_id=11),
    )

    monkeypatch.setattr(services_module, "historial_laboral_service", fake_historial_service)
    monkeypatch.setattr(service, "_validar_sede_activa", _noop_async)
    monkeypatch.setattr(service, "_validar_categoria_activa", _noop_async)

    plaza_actualizada = asyncio.run(
        service.actualizar(
            11,
            SimpleNamespace(
                model_dump=lambda exclude_unset=True: {
                    "salario_mensual": Decimal("13900.00"),
                }
            ),
        )
    )

    assert plaza_actualizada.salario_mensual == Decimal("13900.00")
    assert ("salario", 52, 11, Decimal("12500.00"), Decimal("13900.00")) in fake_historial_service.calls


def test_actualizar_salario_plaza_vacante_no_registra_historial(monkeypatch):
    repository = _FakePlazaRepository(
        _build_plaza(
            plaza_id=11,
            empleado_id=None,
            estatus=EstatusPlaza.VACANTE,
            salario_mensual=Decimal("9800.00"),
        ),
    )
    service = PlazaService(repository=repository)
    fake_historial_service = _FakeHistorialLaboralService()

    monkeypatch.setattr(services_module, "historial_laboral_service", fake_historial_service)
    monkeypatch.setattr(service, "_validar_sede_activa", _noop_async)
    monkeypatch.setattr(service, "_validar_categoria_activa", _noop_async)

    plaza_actualizada = asyncio.run(
        service.actualizar(
            11,
            SimpleNamespace(
                model_dump=lambda exclude_unset=True: {
                    "salario_mensual": Decimal("10200.00"),
                }
            ),
        )
    )

    assert plaza_actualizada.salario_mensual == Decimal("10200.00")
    assert not any(call[0] == "salario" for call in fake_historial_service.calls)


def test_actualizar_salario_sin_cambio_no_registra_historial(monkeypatch):
    repository = _FakePlazaRepository(
        _build_plaza(
            plaza_id=11,
            empleado_id=52,
            estatus=EstatusPlaza.OCUPADA,
            salario_mensual=Decimal("12500.00"),
        ),
    )
    service = PlazaService(repository=repository)
    fake_historial_service = _FakeHistorialLaboralService(
        registro_activo=SimpleNamespace(plaza_id=11),
    )

    monkeypatch.setattr(services_module, "historial_laboral_service", fake_historial_service)
    monkeypatch.setattr(service, "_validar_sede_activa", _noop_async)
    monkeypatch.setattr(service, "_validar_categoria_activa", _noop_async)

    plaza_actualizada = asyncio.run(
        service.actualizar(
            11,
            SimpleNamespace(
                model_dump=lambda exclude_unset=True: {
                    "salario_mensual": Decimal("12500.00"),
                }
            ),
        )
    )

    assert plaza_actualizada.salario_mensual == Decimal("12500.00")
    assert not any(call[0] == "salario" for call in fake_historial_service.calls)
