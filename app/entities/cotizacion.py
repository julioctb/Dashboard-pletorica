"""
Entidades de dominio para Cotizaciones.

Una cotización representa una propuesta de servicios con múltiples partidas.
Código autogenerado: COT-[EMPRESA]-[AÑO][SEQ], ej: COT-MAN-26001.
"""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict

from app.core.enums import EstatusCotizacion, TipoCotizacion


def calcular_meses_periodo(fecha_inicio: date, fecha_fin: date) -> int:
    """Cuenta meses de servicio por frontera calendario, de forma inclusiva."""
    if fecha_fin <= fecha_inicio:
        return 0
    return (
        (fecha_fin.year - fecha_inicio.year) * 12
        + (fecha_fin.month - fecha_inicio.month)
        + 1
    )


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

    # Tipo de cotización
    tipo: str = TipoCotizacion.PERSONAL.value

    # Versionamiento
    version: int = Field(default=1, ge=1)
    cotizacion_origen_id: Optional[int] = None

    # Destinatario
    destinatario_nombre: Optional[str] = Field(default=None, max_length=200)
    destinatario_cargo: Optional[str] = Field(default=None, max_length=200)

    # Período (opcional — se usa al convertir a contrato)
    fecha_inicio_periodo: Optional[date] = None
    fecha_fin_periodo: Optional[date] = None

    # IVA y meses
    aplicar_iva: bool = False
    cantidad_meses: int = Field(default=1, ge=1)

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
        if self.fecha_inicio_periodo and self.fecha_fin_periodo:
            if self.fecha_fin_periodo <= self.fecha_inicio_periodo:
                raise ValueError("La fecha de fin debe ser posterior a la fecha de inicio")
        return self

    @property
    def meses_periodo(self) -> int:
        """Calcula meses de servicio considerando el rango mensual inclusivo."""
        if not self.fecha_inicio_periodo or not self.fecha_fin_periodo:
            return self.cantidad_meses
        return calcular_meses_periodo(
            self.fecha_inicio_periodo,
            self.fecha_fin_periodo,
        )

    @property
    def es_tipo_personal(self) -> bool:
        return self.tipo == TipoCotizacion.PERSONAL.value

    @property
    def es_tipo_productos(self) -> bool:
        return self.tipo == TipoCotizacion.PRODUCTOS_SERVICIOS.value

    @property
    def es_editable(self) -> bool:
        """Solo BORRADOR permite edición."""
        return self.estatus == EstatusCotizacion.BORRADOR


class CotizacionCreate(BaseModel):
    """DTO para crear una cotización."""

    model_config = ConfigDict(str_strip_whitespace=True)

    empresa_id: int
    tipo: str = TipoCotizacion.PERSONAL.value
    fecha_inicio_periodo: Optional[date] = None
    fecha_fin_periodo: Optional[date] = None
    aplicar_iva: bool = False
    cantidad_meses: int = Field(default=1, ge=1)
    destinatario_nombre: Optional[str] = Field(default=None, max_length=200)
    destinatario_cargo: Optional[str] = Field(default=None, max_length=200)
    mostrar_desglose: bool = False
    representante_legal: Optional[str] = Field(default=None, max_length=200)
    notas: Optional[str] = None

    @model_validator(mode='after')
    def validar_fechas(self) -> 'CotizacionCreate':
        if self.fecha_inicio_periodo and self.fecha_fin_periodo:
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
    aplicar_iva: Optional[bool] = None
    cantidad_meses: Optional[int] = Field(default=None, ge=1)
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
    tipo: str = TipoCotizacion.PERSONAL.value
    version: int = 1
    cotizacion_origen_id: Optional[int] = None
    destinatario_nombre: Optional[str] = None
    fecha_inicio_periodo: Optional[date] = None
    fecha_fin_periodo: Optional[date] = None
    aplicar_iva: bool = False
    cantidad_meses: int = 1
    mostrar_desglose: bool = False
    estatus: EstatusCotizacion = EstatusCotizacion.BORRADOR
    notas: Optional[str] = None
    cantidad_partidas: int = 0
    fecha_creacion: Optional[datetime] = None
    fecha_actualizacion: Optional[datetime] = None
