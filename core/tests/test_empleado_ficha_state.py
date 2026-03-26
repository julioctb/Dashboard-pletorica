"""Tests puntuales para fallback de plaza en EmpleadoFichaState."""

import asyncio
from datetime import date
from decimal import Decimal
from types import SimpleNamespace

from core.core.enums import EstatusPlaza, TipoJornadaPlaza
from core.domain.models.plaza import Plaza, PlazaResumen
import core.presentation.pages.portal.empleado_ficha.state as ficha_state_module
from core.presentation.pages.portal.empleado_ficha.state import EmpleadoFichaState


class _DummyFichaState:
    _resolver_plaza_activa_por_ocupacion = EmpleadoFichaState._resolver_plaza_activa_por_ocupacion
    _cargar_plaza_actual = EmpleadoFichaState._cargar_plaza_actual

    def __init__(self):
        self.id_empresa_actual = 9
        self.plaza_actual = {}
        self.tiene_plaza = False


class _FakeHistorialService:
    async def obtener_registro_activo(self, empleado_id: int):
        return None


class _FakePlazaService:
    async def obtener_resumen_ocupadas_por_empresa(self, empresa_id: int):
        assert empresa_id == 9
        return [
            PlazaResumen(
                id=17,
                contrato_id=4,
                sede_id=3,
                categoria_puesto_id=8,
                numero_plaza=12,
                codigo="PLA-012",
                empleado_id=88,
                fecha_inicio=date(2026, 1, 1),
                salario_mensual=Decimal("10000.00"),
                tipo_jornada=TipoJornadaPlaza.COMPLETA,
                factor_jornada=Decimal("1.0"),
                estatus=EstatusPlaza.OCUPADA,
                contrato_codigo="CT-04",
                categoria_nombre="AUXILIAR",
                sede_codigo="CC",
                sede_nombre="CAMPUS CENTRO",
                empleado_nombre="ANA PEREZ",
            )
        ]

    async def obtener_por_id(self, plaza_id: int):
        assert plaza_id == 17
        return Plaza(
            id=17,
            contrato_id=4,
            sede_id=3,
            categoria_puesto_id=8,
            numero_plaza=12,
            codigo="PLA-012",
            empleado_id=88,
            fecha_inicio=date(2026, 1, 1),
            fecha_fin=None,
            salario_mensual=Decimal("10000.00"),
            tipo_jornada=TipoJornadaPlaza.COMPLETA,
            factor_jornada=Decimal("1.0"),
            estatus=EstatusPlaza.OCUPADA,
            notas=None,
        )


class _FakeContratoService:
    async def obtener_por_id(self, contrato_id: int):
        assert contrato_id == 4
        return SimpleNamespace(
            codigo="CT-04",
            fecha_inicio=date(2026, 1, 1),
            fecha_fin=None,
        )


class _FakeCategoriaService:
    async def obtener_por_id(self, categoria_id: int):
        assert categoria_id == 8
        return SimpleNamespace(nombre="Auxiliar")


class _FakeSedeService:
    async def obtener_por_id(self, sede_id: int):
        assert sede_id == 3
        return SimpleNamespace(nombre="Campus Centro", codigo="CC")


def test_cargar_plaza_actual_usa_fallback_por_ocupacion_si_historial_esta_vacio(monkeypatch):
    dummy = _DummyFichaState()

    monkeypatch.setattr(ficha_state_module, "historial_laboral_service", _FakeHistorialService())
    monkeypatch.setattr(ficha_state_module, "plaza_service", _FakePlazaService())
    monkeypatch.setattr(ficha_state_module, "contrato_service", _FakeContratoService())
    monkeypatch.setattr(ficha_state_module, "categoria_puesto_service", _FakeCategoriaService())
    monkeypatch.setattr(ficha_state_module, "sede_service", _FakeSedeService())

    asyncio.run(dummy._cargar_plaza_actual(88))

    assert dummy.tiene_plaza is True
    assert dummy.plaza_actual["plaza_id"] == 17
    assert dummy.plaza_actual["numero_contrato"] == "CT-04"
    assert dummy.plaza_actual["categoria_nombre"] == "Auxiliar"
    assert dummy.plaza_actual["sede_nombre"].upper() == "CAMPUS CENTRO"
