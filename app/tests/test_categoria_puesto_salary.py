"""Tests para sueldo base mensual en categorías de puesto."""

from decimal import Decimal

from app.domain.models.categoria_puesto import CategoriaPuestoCreate
from app.presentation.pages.backoffice.categorias_puesto.categorias_puesto_state import (
    CategoriasPuestoState,
)


def test_categoria_puesto_create_convierte_salario_base_mensual():
    categoria = CategoriaPuestoCreate(
        tipo_servicio_id=3,
        clave="SUP",
        nombre="SUPERVISOR",
        descripcion="",
        orden=1,
        salario_base_mensual="$ 12,500.00",
    )

    assert categoria.salario_base_mensual == Decimal("12500.00")


def test_serializar_categoria_state_formatea_salario_base():
    categoria = CategoriaPuestoCreate(
        tipo_servicio_id=3,
        clave="SUP",
        nombre="SUPERVISOR",
        descripcion="",
        orden=1,
        salario_base_mensual=Decimal("9800.50"),
    )

    data = CategoriasPuestoState._serializar_categoria_state(categoria)

    assert data["salario_base_mensual_fmt"] == "$ 9,800.50"
