"""Entidades del módulo de incapacidades."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from core.core.enums import (
    EstatusIncapacidad,
    OrigenIncapacidad,
    TipoCertificado,
    TipoIncapacidad,
)


class CertificadoIncapacidad(BaseModel):
    """Certificado individual asociado a una incapacidad."""

    model_config = ConfigDict(
        use_enum_values=True,
        str_strip_whitespace=True,
        from_attributes=True,
    )

    id: Optional[int] = None
    incapacidad_id: int
    folio_imss: Optional[str] = Field(default=None, max_length=50)
    fecha_inicio: date
    fecha_fin: date
    dias_certificado: int = Field(ge=1)
    tipo_certificado: TipoCertificado = TipoCertificado.INICIAL
    archivo_id: Optional[int] = None
    fecha_creacion: Optional[datetime] = None
    fecha_actualizacion: Optional[datetime] = None


class CertificadoIncapacidadCreate(BaseModel):
    """DTO para registrar certificados de incapacidad."""

    model_config = ConfigDict(
        use_enum_values=True,
        str_strip_whitespace=True,
    )

    incapacidad_id: int
    folio_imss: Optional[str] = Field(default=None, max_length=50)
    fecha_inicio: date
    fecha_fin: date
    dias_certificado: int = Field(ge=1)
    tipo_certificado: TipoCertificado = TipoCertificado.SUBSECUENTE
    archivo_id: Optional[int] = None


class Incapacidad(BaseModel):
    """Entidad principal de incapacidad."""

    model_config = ConfigDict(
        use_enum_values=True,
        str_strip_whitespace=True,
        from_attributes=True,
    )

    id: Optional[int] = None
    empleado_id: int
    plaza_id: Optional[int] = None
    empresa_id: int
    origen: OrigenIncapacidad
    tipo: TipoIncapacidad
    fecha_inicio: date
    fecha_fin_estimada: Optional[date] = None
    fecha_fin_real: Optional[date] = None
    estatus: EstatusIncapacidad = EstatusIncapacidad.ACTIVA
    porcentaje_pago: Decimal = Field(default=Decimal("100.00"), ge=0, le=100, decimal_places=2)
    requiere_cobertura: bool = False
    notas: Optional[str] = None
    registrado_por: Optional[UUID] = None
    fecha_creacion: Optional[datetime] = None
    fecha_actualizacion: Optional[datetime] = None

    certificados: list[CertificadoIncapacidad] = Field(default_factory=list)
    empleado_nombre: Optional[str] = None
    plaza_categoria: Optional[str] = None
    plaza_sede: Optional[str] = None

    @property
    def dias_totales_certificados(self) -> int:
        return sum(int(cert.dias_certificado or 0) for cert in self.certificados)

    @property
    def ultimo_certificado(self) -> Optional[CertificadoIncapacidad]:
        if not self.certificados:
            return None
        return max(
            self.certificados,
            key=lambda cert: (cert.fecha_fin, cert.fecha_inicio),
        )

    @property
    def esta_vencida(self) -> bool:
        fecha_fin = self.fecha_fin_estimada
        if self.ultimo_certificado is not None:
            fecha_fin = self.ultimo_certificado.fecha_fin
        if fecha_fin is None:
            return False
        return fecha_fin < date.today() and self.estatus != EstatusIncapacidad.CERRADA

    @property
    def es_formal(self) -> bool:
        return self.origen == OrigenIncapacidad.FORMAL


class IncapacidadCreate(BaseModel):
    """DTO para registrar una incapacidad nueva."""

    model_config = ConfigDict(
        use_enum_values=True,
        str_strip_whitespace=True,
    )

    empleado_id: int
    plaza_id: Optional[int] = None
    contrato_id: Optional[int] = None
    empresa_id: int
    origen: OrigenIncapacidad
    tipo: TipoIncapacidad
    fecha_inicio: date
    fecha_fin_estimada: Optional[date] = None
    porcentaje_pago: Decimal = Field(default=Decimal("100.00"), ge=0, le=100, decimal_places=2)
    requiere_cobertura: bool = False
    notas: Optional[str] = None
    registrado_por: Optional[UUID] = None
    folio_imss: Optional[str] = Field(default=None, max_length=50)
    dias_certificado: Optional[int] = Field(default=None, ge=1)
    archivo_id: Optional[int] = None


class IncapacidadResumen(BaseModel):
    """Resumen serializable para listados y tarjetas."""

    model_config = ConfigDict(
        use_enum_values=True,
        str_strip_whitespace=True,
        from_attributes=True,
    )

    id: int
    empleado_id: int
    empleado_uuid: Optional[UUID] = None
    empleado_clave: str = ""
    empleado_nombre: str = ""
    tipo: TipoIncapacidad
    origen: OrigenIncapacidad
    fecha_inicio: date
    fecha_fin_estimada: Optional[date] = None
    estatus: EstatusIncapacidad
    dias_certificados: int = 0
    total_certificados: int = 0
    requiere_cobertura: bool = False
    plaza_id: Optional[int] = None
    contrato_id: Optional[int] = None
    ultimo_folio_imss: Optional[str] = None
    plaza_categoria: Optional[str] = None
    plaza_sede: Optional[str] = None
