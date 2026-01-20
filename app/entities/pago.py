"""
Entidades de dominio para Pagos de Contratos.

Los pagos representan transacciones de pago asociadas a un contrato.
Permiten llevar el control de pagos parciales y totales sobre el monto
máximo autorizado del contrato.
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field, field_validator, ConfigDict

from app.core.validation.constants import (
    CONCEPTO_PAGO_MAX,
    NUMERO_FACTURA_MAX,
    COMPROBANTE_MAX,
    NOTAS_PAGO_MAX,
)


class Pago(BaseModel):
    """
    Entidad principal de Pago.

    Representa un pago realizado a un contrato.
    """

    model_config = ConfigDict(
        use_enum_values=True,
        str_strip_whitespace=True,
        validate_assignment=True,
        from_attributes=True
    )

    # Identificación
    id: Optional[int] = None
    contrato_id: int = Field(description="ID del contrato asociado")

    # Datos del pago
    fecha_pago: date = Field(description="Fecha en que se realizó el pago")
    monto: Decimal = Field(
        ge=0,
        decimal_places=2,
        description="Monto del pago"
    )
    concepto: str = Field(
        max_length=CONCEPTO_PAGO_MAX,
        description="Concepto o descripción del pago"
    )

    # Información de facturación (opcional)
    numero_factura: Optional[str] = Field(
        None,
        max_length=NUMERO_FACTURA_MAX,
        description="Número de factura asociada"
    )
    comprobante: Optional[str] = Field(
        None,
        max_length=COMPROBANTE_MAX,
        description="Referencia o URL del comprobante"
    )

    # Notas adicionales
    notas: Optional[str] = Field(
        None,
        max_length=NOTAS_PAGO_MAX,
        description="Notas u observaciones del pago"
    )

    # Auditoría
    fecha_creacion: Optional[datetime] = Field(
        None,
        description="Fecha de registro en el sistema"
    )
    fecha_actualizacion: Optional[datetime] = None

    # ==========================================
    # VALIDADORES
    # ==========================================

    @field_validator('concepto')
    @classmethod
    def validar_concepto(cls, v: str) -> str:
        """Valida que el concepto no esté vacío"""
        if not v or not v.strip():
            raise ValueError("El concepto del pago es obligatorio")
        return v.strip()

    @field_validator('numero_factura')
    @classmethod
    def validar_numero_factura(cls, v: Optional[str]) -> Optional[str]:
        """Normaliza el número de factura"""
        if v:
            return v.strip().upper()
        return v

    def __str__(self) -> str:
        return f"Pago {self.id}: ${self.monto} - {self.fecha_pago}"


class PagoCreate(BaseModel):
    """Modelo para crear un nuevo pago"""

    model_config = ConfigDict(
        use_enum_values=True,
        str_strip_whitespace=True,
        validate_assignment=True
    )

    contrato_id: int
    fecha_pago: date
    monto: Decimal = Field(ge=0)
    concepto: str = Field(min_length=1, max_length=CONCEPTO_PAGO_MAX)
    numero_factura: Optional[str] = Field(None, max_length=NUMERO_FACTURA_MAX)
    comprobante: Optional[str] = Field(None, max_length=COMPROBANTE_MAX)
    notas: Optional[str] = Field(None, max_length=NOTAS_PAGO_MAX)


class PagoUpdate(BaseModel):
    """Modelo para actualizar un pago existente"""

    model_config = ConfigDict(
        use_enum_values=True,
        str_strip_whitespace=True,
        validate_assignment=True
    )

    fecha_pago: Optional[date] = None
    monto: Optional[Decimal] = Field(None, ge=0)
    concepto: Optional[str] = Field(None, max_length=CONCEPTO_PAGO_MAX)
    numero_factura: Optional[str] = Field(None, max_length=NUMERO_FACTURA_MAX)
    comprobante: Optional[str] = Field(None, max_length=COMPROBANTE_MAX)
    notas: Optional[str] = Field(None, max_length=NOTAS_PAGO_MAX)


class PagoResumen(BaseModel):
    """Modelo resumido de pago para listados"""

    model_config = ConfigDict(
        use_enum_values=True,
        from_attributes=True
    )

    id: int
    contrato_id: int
    fecha_pago: date
    monto: Decimal
    concepto: str
    numero_factura: Optional[str]
    fecha_creacion: Optional[datetime]

    # Campos calculados (se llenan desde el servicio)
    codigo_contrato: Optional[str] = None

    @classmethod
    def from_pago(cls, pago: Pago) -> 'PagoResumen':
        """Factory method para crear desde un pago completo"""
        return cls(
            id=pago.id,
            contrato_id=pago.contrato_id,
            fecha_pago=pago.fecha_pago,
            monto=pago.monto,
            concepto=pago.concepto,
            numero_factura=pago.numero_factura,
            fecha_creacion=pago.fecha_creacion,
        )


class ResumenPagosContrato(BaseModel):
    """Resumen de pagos para un contrato específico"""

    model_config = ConfigDict(from_attributes=True)

    contrato_id: int
    codigo_contrato: str
    monto_maximo: Optional[Decimal] = None
    total_pagado: Decimal = Decimal("0")
    saldo_pendiente: Decimal = Decimal("0")
    porcentaje_pagado: Decimal = Decimal("0")
    cantidad_pagos: int = 0
    ultimo_pago: Optional[date] = None

    @property
    def esta_pagado(self) -> bool:
        """Indica si el contrato está completamente pagado"""
        if not self.monto_maximo:
            return False
        return self.total_pagado >= self.monto_maximo
