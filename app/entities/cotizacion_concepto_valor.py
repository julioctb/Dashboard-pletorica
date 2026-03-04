"""
Entidades de dominio para Valores de Conceptos de Cotización.

Cada registro es la intersección de la matriz:
concepto (fila) × categoría (columna) = valor en pesos.
"""
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class CotizacionConceptoValor(BaseModel):
    """Valor de una celda de la matriz de costos."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        from_attributes=True,
    )

    id: Optional[int] = None
    concepto_id: int
    partida_categoria_id: int
    valor_pesos: Decimal = Field(default=Decimal('0'), ge=Decimal('0'))


class CotizacionConceptoValorCreate(BaseModel):
    """DTO para crear/actualizar un valor en la matriz."""

    model_config = ConfigDict(str_strip_whitespace=True)

    concepto_id: int
    partida_categoria_id: int
    valor_pesos: Decimal = Field(default=Decimal('0'), ge=Decimal('0'))
