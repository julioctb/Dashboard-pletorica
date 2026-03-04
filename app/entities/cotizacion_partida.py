"""
Entidades de dominio para Partidas de Cotización.

Una partida es un lote dentro de una cotización que puede convertirse
a contrato independiente cuando su estatus sea ACEPTADA.
"""
from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict

from app.core.enums import EstatusPartidaCotizacion


class CotizacionPartida(BaseModel):
    """Entidad principal de Partida de Cotización."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        from_attributes=True,
        use_enum_values=True,
    )

    id: Optional[int] = None
    cotizacion_id: int
    numero_partida: int = Field(ge=1)

    estatus_partida: EstatusPartidaCotizacion = EstatusPartidaCotizacion.PENDIENTE
    contrato_id: Optional[int] = None
    notas: Optional[str] = None

    fecha_creacion: Optional[datetime] = None

    @property
    def puede_convertir(self) -> bool:
        return self.estatus_partida == EstatusPartidaCotizacion.ACEPTADA

    @property
    def fue_convertida(self) -> bool:
        return self.estatus_partida == EstatusPartidaCotizacion.CONVERTIDA


class CotizacionPartidaCreate(BaseModel):
    """DTO para crear una partida."""

    model_config = ConfigDict(str_strip_whitespace=True)

    cotizacion_id: int
    notas: Optional[str] = None


class CotizacionPartidaResumen(BaseModel):
    """Vista enriquecida de partida con totales calculados."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        from_attributes=True,
        use_enum_values=True,
    )

    id: int
    cotizacion_id: int
    numero_partida: int
    estatus_partida: EstatusPartidaCotizacion = EstatusPartidaCotizacion.PENDIENTE
    contrato_id: Optional[int] = None
    notas: Optional[str] = None
    fecha_creacion: Optional[datetime] = None

    # Totales calculados (agregados en servicio)
    cantidad_categorias: int = 0
    cantidad_personal_minima: int = 0
    cantidad_personal_maxima: int = 0
    subtotal_minimo: Decimal = Decimal('0')
    subtotal_maximo: Decimal = Decimal('0')
    iva_minimo: Decimal = Decimal('0')
    iva_maximo: Decimal = Decimal('0')
    total_minimo: Decimal = Decimal('0')
    total_maximo: Decimal = Decimal('0')
