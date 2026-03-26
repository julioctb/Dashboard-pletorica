"""
Entidades de dominio para Items de Cotización.

Un item representa un concepto extra (line item) que puede pertenecer a:
- Un perfil (partida_categoria_id NOT NULL) → nivel perfil
- Una partida (partida_id NOT NULL, partida_categoria_id NULL) → nivel partida
- La cotización (ambos NULL) → nivel global
"""
from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class CotizacionItem(BaseModel):
    """Item de cotización en cualquier nivel."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        from_attributes=True,
    )

    id: Optional[int] = None
    cotizacion_id: int
    partida_id: Optional[int] = None
    partida_categoria_id: Optional[int] = None
    numero: int = Field(ge=1)
    cantidad: Decimal = Field(default=Decimal('1'))
    descripcion: str = Field(max_length=500)
    precio_unitario: Decimal = Field(default=Decimal('0'))
    importe: Decimal = Field(default=Decimal('0'))
    es_autogenerado: bool = False
    fecha_creacion: Optional[datetime] = None

    @property
    def nivel(self) -> str:
        """Determina el nivel/scope del item."""
        if self.partida_categoria_id is not None:
            return "perfil"
        if self.partida_id is not None:
            return "partida"
        return "global"


class CotizacionItemCreate(BaseModel):
    """DTO para crear un item de cotización."""

    model_config = ConfigDict(str_strip_whitespace=True)

    cotizacion_id: int
    partida_id: Optional[int] = None
    partida_categoria_id: Optional[int] = None
    cantidad: Decimal = Field(default=Decimal('1'))
    descripcion: str = Field(max_length=500)
    precio_unitario: Decimal = Field(default=Decimal('0'))
