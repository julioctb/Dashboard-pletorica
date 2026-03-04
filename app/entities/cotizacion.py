"""
Entidades de dominio para Cotizaciones.

Una cotización representa una propuesta de servicios con múltiples partidas.
Código autogenerado: COT-[EMPRESA]-[AÑO][SEQ], ej: COT-MAN-26001.
"""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict

from app.core.enums import EstatusCotizacion


class Cotizacion(BaseModel):
    """Entidad principal de Cotización."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        from_attributes=True,
        use_enum_values=True,
    )

    id: Optional[int] = None
    codigo: str = Field(max_length=30, description="Código único: COT-MAN-26001")
    empresa_id: int

    # Versionamiento
    version: int = Field(default=1, ge=1)
    cotizacion_origen_id: Optional[int] = None

    # Destinatario
    destinatario_nombre: Optional[str] = Field(default=None, max_length=200)
    destinatario_cargo: Optional[str] = Field(default=None, max_length=200)

    # Período
    fecha_inicio_periodo: date
    fecha_fin_periodo: date

    # Visualización
    mostrar_desglose: bool = False
    representante_legal: Optional[str] = Field(default=None, max_length=200)

    # Estado
    estatus: EstatusCotizacion = EstatusCotizacion.BORRADOR
    notas: Optional[str] = None

    # Auditoría
    created_by: Optional[str] = None
    fecha_creacion: Optional[datetime] = None
    fecha_actualizacion: Optional[datetime] = None

    @model_validator(mode='after')
    def validar_fechas(self) -> 'Cotizacion':
        if self.fecha_fin_periodo <= self.fecha_inicio_periodo:
            raise ValueError("La fecha de fin debe ser posterior a la fecha de inicio")
        return self

    @property
    def meses_periodo(self) -> int:
        """Calcula meses entre fecha_inicio y fecha_fin del período."""
        from dateutil.relativedelta import relativedelta
        delta = relativedelta(self.fecha_fin_periodo, self.fecha_inicio_periodo)
        return delta.months + (delta.years * 12)

    @property
    def es_editable(self) -> bool:
        """Solo BORRADOR permite edición."""
        return self.estatus == EstatusCotizacion.BORRADOR


class CotizacionCreate(BaseModel):
    """DTO para crear una cotización."""

    model_config = ConfigDict(str_strip_whitespace=True)

    empresa_id: int
    fecha_inicio_periodo: date
    fecha_fin_periodo: date
    destinatario_nombre: Optional[str] = Field(default=None, max_length=200)
    destinatario_cargo: Optional[str] = Field(default=None, max_length=200)
    mostrar_desglose: bool = False
    representante_legal: Optional[str] = Field(default=None, max_length=200)
    notas: Optional[str] = None

    @model_validator(mode='after')
    def validar_fechas(self) -> 'CotizacionCreate':
        if self.fecha_fin_periodo <= self.fecha_inicio_periodo:
            raise ValueError("La fecha de fin debe ser posterior a la fecha de inicio")
        return self


class CotizacionUpdate(BaseModel):
    """DTO para actualizar una cotización (todos opcionales)."""

    model_config = ConfigDict(str_strip_whitespace=True)

    destinatario_nombre: Optional[str] = Field(default=None, max_length=200)
    destinatario_cargo: Optional[str] = Field(default=None, max_length=200)
    fecha_inicio_periodo: Optional[date] = None
    fecha_fin_periodo: Optional[date] = None
    mostrar_desglose: Optional[bool] = None
    representante_legal: Optional[str] = Field(default=None, max_length=200)
    notas: Optional[str] = None


class CotizacionResumen(BaseModel):
    """Vista enriquecida de cotización para listados."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        from_attributes=True,
        use_enum_values=True,
    )

    id: int
    codigo: str
    empresa_id: int
    nombre_empresa: str = ""
    version: int = 1
    cotizacion_origen_id: Optional[int] = None
    destinatario_nombre: Optional[str] = None
    fecha_inicio_periodo: date
    fecha_fin_periodo: date
    mostrar_desglose: bool = False
    estatus: EstatusCotizacion = EstatusCotizacion.BORRADOR
    notas: Optional[str] = None
    cantidad_partidas: int = 0
    fecha_creacion: Optional[datetime] = None
    fecha_actualizacion: Optional[datetime] = None
