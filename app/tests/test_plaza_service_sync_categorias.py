"""Tests unitarios para sincronizar categorías contractuales hacia plazas."""

import asyncio
from datetime import date
from decimal import Decimal

import app.domain.services as services_module
from app.domain.models.contrato_categoria import ContratoCategoria
from app.domain.models.plaza import Plaza
from app.domain.services.plaza_service import PlazaService
from app.domain.enums import EstatusPlaza


def _build_plaza(plaza_id: int, numero: int, salario: str) -> Plaza:
    return Plaza(
        id=plaza_id,
        contrato_id=26,
        sede_id=None,
        categoria_puesto_id=None,
        numero_plaza=numero,
        codigo="",
        empleado_id=None,
        fecha_inicio=date(2026, 3, 1),
        fecha_fin=None,
        salario_mensual=Decimal(salario),
        estatus=EstatusPlaza.VACANTE,
        notas=None,
    )


class _FakePlazaRepository:
    def __init__(self, plazas: list[Plaza]):
        self.plazas = {plaza.id: plaza for plaza in plazas}
        self.updated: list[tuple[int, int | None, Decimal]] = []

    async def obtener_por_contrato(self, contrato_id: int, incluir_canceladas: bool = False) -> list[Plaza]:
        return [self.plazas[plaza_id] for plaza_id in sorted(self.plazas)]

    async def actualizar(self, plaza: Plaza) -> Plaza:
        self.plazas[plaza.id] = plaza
        self.updated.append((plaza.id, plaza.categoria_puesto_id, plaza.salario_mensual))
        return plaza


class _FakeContratoCategoriaService:
    def __init__(self, categorias: list[ContratoCategoria]):
        self.categorias = categorias

    async def obtener_categorias_de_contrato(self, contrato_id: int) -> list[ContratoCategoria]:
        return self.categorias


def test_sincronizar_categorias_desde_contrato_asigna_categoria_sin_tocar_salario(monkeypatch):
    plazas = [_build_plaza(plaza_id=i, numero=i, salario=str(i * 100)) for i in range(1, 23)]
    repository = _FakePlazaRepository(plazas)
    service = PlazaService(repository=repository)
    categorias = [
        ContratoCategoria(
            id=1,
            contrato_id=26,
            categoria_puesto_id=10,
            cantidad_minima=10,
            cantidad_maxima=15,
            costo_unitario=Decimal("12345.67"),
        ),
        ContratoCategoria(
            id=2,
            contrato_id=26,
            categoria_puesto_id=20,
            cantidad_minima=5,
            cantidad_maxima=7,
            costo_unitario=Decimal("9800"),
        ),
    ]

    monkeypatch.setattr(
        services_module,
        "contrato_categoria_service",
        _FakeContratoCategoriaService(categorias),
    )

    actualizadas = asyncio.run(service.sincronizar_categorias_desde_contrato(26))

    assert actualizadas == 22
    assert [repository.plazas[i].categoria_puesto_id for i in range(1, 16)] == [10] * 15
    assert [repository.plazas[i].categoria_puesto_id for i in range(16, 23)] == [20] * 7
    assert [repository.plazas[i].salario_mensual for i in range(1, 23)] == [
        Decimal(str(i * 100)) for i in range(1, 23)
    ]
