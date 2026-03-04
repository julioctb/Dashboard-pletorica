"""
Entidades de dominio para Categorías por Partida de Cotización.

Cada registro representa una categoría de personal dentro de una partida,
con sus cantidades min/max y el precio unitario calculado.
"""
from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field, model_validator, ConfigDict


class CotizacionPartidaCategoria(BaseModel):
    """Categoría de personal dentro de una partida."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        from_attributes=True,
    )

    id: Optional[int] = None
    partida_id: int
    categoria_puesto_id: int

    cantidad_minima: int = Field(default=0, ge=0)
    cantidad_maxima: int = Field(default=0, ge=0)
    salario_base_mensual: Decimal = Field(gt=Decimal('0'))

    # Costo patronal
    costo_patronal_calculado: Decimal = Field(default=Decimal('0'), ge=Decimal('0'))
    costo_patronal_editado: Optional[Decimal] = None
    fue_editado_manualmente: bool = False

    # Precio unitario final (sin IVA)
    precio_unitario_final: Decimal = Field(default=Decimal('0'), ge=Decimal('0'))

    fecha_creacion: Optional[datetime] = None

    @model_validator(mode='after')
    def validar_cantidades(self) -> 'CotizacionPartidaCategoria':
        if self.cantidad_maxima < self.cantidad_minima:
            raise ValueError("La cantidad máxima debe ser mayor o igual a la mínima")
        return self

    @property
    def costo_patronal_efectivo(self) -> Decimal:
        """Retorna el costo patronal a usar (editado o calculado)."""
        if self.fue_editado_manualmente and self.costo_patronal_editado is not None:
            return self.costo_patronal_editado
        return self.costo_patronal_calculado


class CotizacionPartidaCategoriaCreate(BaseModel):
    """DTO para agregar una categoría a una partida."""

    model_config = ConfigDict(str_strip_whitespace=True)

    partida_id: int
    categoria_puesto_id: int
    cantidad_minima: int = Field(default=0, ge=0)
    cantidad_maxima: int = Field(default=0, ge=0)
    salario_base_mensual: Decimal = Field(gt=Decimal('0'))

    @model_validator(mode='after')
    def validar_cantidades(self) -> 'CotizacionPartidaCategoriaCreate':
        if self.cantidad_maxima < self.cantidad_minima:
            raise ValueError("La cantidad máxima debe ser mayor o igual a la mínima")
        return self


class CotizacionPartidaCategoriaResumen(BaseModel):
    """Vista enriquecida con datos de la categoría de puesto."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        from_attributes=True,
    )

    id: int
    partida_id: int
    categoria_puesto_id: int
    categoria_clave: str = ""
    categoria_nombre: str = ""

    cantidad_minima: int = 0
    cantidad_maxima: int = 0
    salario_base_mensual: Decimal = Decimal('0')
    costo_patronal_calculado: Decimal = Decimal('0')
    costo_patronal_editado: Optional[Decimal] = None
    fue_editado_manualmente: bool = False
    costo_patronal_efectivo: Decimal = Decimal('0')
    precio_unitario_final: Decimal = Decimal('0')

    fecha_creacion: Optional[datetime] = None
