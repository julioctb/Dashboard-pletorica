"""
Entidades de dominio para Conceptos de Cotización.

Los conceptos son las filas de la matriz de costos.
- PATRONAL: autogenerados por el motor (sueldo, IMSS, INFONAVIT, etc.)
- INDIRECTO: gastos adicionales definidos por el usuario
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict

from app.core.enums import TipoConceptoCotizacion, TipoValorConcepto


class CotizacionConcepto(BaseModel):
    """Fila de la matriz de costos de una partida."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        from_attributes=True,
        use_enum_values=True,
    )

    id: Optional[int] = None
    partida_id: int

    nombre: str = Field(max_length=200)
    tipo_concepto: TipoConceptoCotizacion = TipoConceptoCotizacion.INDIRECTO
    tipo_valor: TipoValorConcepto = TipoValorConcepto.FIJO
    orden: int = Field(default=0, ge=0)
    es_autogenerado: bool = False

    fecha_creacion: Optional[datetime] = None

    @property
    def es_patronal(self) -> bool:
        return self.tipo_concepto == TipoConceptoCotizacion.PATRONAL

    @property
    def es_editable(self) -> bool:
        """Los conceptos autogenerados no se editan manualmente."""
        return not self.es_autogenerado


class CotizacionConceptoCreate(BaseModel):
    """DTO para agregar un concepto a una partida."""

    model_config = ConfigDict(str_strip_whitespace=True)

    partida_id: int
    nombre: str = Field(max_length=200)
    tipo_concepto: TipoConceptoCotizacion = TipoConceptoCotizacion.INDIRECTO
    tipo_valor: TipoValorConcepto = TipoValorConcepto.FIJO
    es_autogenerado: bool = False
