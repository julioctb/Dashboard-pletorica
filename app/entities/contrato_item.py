"""
Entidades de dominio para Items de Contrato.

Los items de contrato representan bienes o servicios con precios definitivos,
a diferencia de los items de requisicion donde los precios son estimados/opcionales.

Se usan principalmente para contratos de ADQUISICION.
ContratoCategoria sigue siendo el modelo para contratos de SERVICIOS (personal).
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field, field_validator, ConfigDict


class ContratoItem(BaseModel):
    """Item de contrato con precio requerido."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        from_attributes=True,
    )

    id: Optional[int] = None
    contrato_id: Optional[int] = None
    requisicion_item_id: Optional[int] = Field(
        None,
        description="FK al item de requisicion origen. NULL si fue creado directamente."
    )
    numero_item: int = Field(default=1, ge=1)
    unidad_medida: str = Field(max_length=50, default="Pieza")
    cantidad: Decimal = Field(ge=0, decimal_places=4)
    descripcion: str
    precio_unitario: Decimal = Field(ge=0, decimal_places=2)
    subtotal: Decimal = Field(ge=0, decimal_places=2)
    especificaciones_tecnicas: Optional[str] = None
    notas: Optional[str] = None
    created_at: Optional[datetime] = None


class ContratoItemCreate(BaseModel):
    """Modelo para crear un item de contrato."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
    )

    requisicion_item_id: Optional[int] = None
    numero_item: int = Field(..., ge=1)
    unidad_medida: str = Field(..., max_length=50)
    cantidad: Decimal = Field(..., gt=0, decimal_places=4)
    descripcion: str
    precio_unitario: Decimal = Field(..., ge=0, decimal_places=2)
    especificaciones_tecnicas: Optional[str] = None
    notas: Optional[str] = None

    @field_validator('cantidad', 'precio_unitario', mode='before')
    @classmethod
    def convertir_a_decimal(cls, v):
        """Convierte strings a Decimal."""
        if v is None or v == '':
            return None
        if isinstance(v, str):
            return Decimal(v.replace(',', ''))
        return v
