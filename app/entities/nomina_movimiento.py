"""
Entidades de dominio para movimientos de nómina.

NominaMovimiento representa cada concepto aplicado en el recibo
de un empleado (una fila del desglose: sueldo, ISR, IMSS, etc.).
"""
from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


class NominaMovimiento(BaseModel):
    """
    Movimiento de nómina — un concepto aplicado (tabla nomina_movimientos).

    Cada registro es un concepto del catálogo aplicado al recibo de un empleado.
    El monto siempre es positivo; el tipo (PERCEPCION/DEDUCCION/OTRO_PAGO)
    define si suma o resta al neto.
    """
    model_config = ConfigDict(
        use_enum_values=True,
        str_strip_whitespace=True,
        from_attributes=True,
    )

    id: Optional[int] = None
    nomina_empleado_id: int
    concepto_id: int

    tipo: str = Field(..., description="PERCEPCION / DEDUCCION / OTRO_PAGO (redundante, para performance)")
    origen: str = Field(default='SISTEMA')

    monto: Decimal = Field(..., ge=0, description="Monto del movimiento (siempre positivo)")
    monto_gravable: Decimal = Field(default=Decimal('0'), ge=0)
    monto_exento: Decimal = Field(default=Decimal('0'), ge=0)

    es_automatico: bool = Field(
        default=True,
        description="True = calculado por sistema; False = capturado manualmente"
    )
    notas: Optional[str] = Field(None, max_length=255)
    registrado_por: Optional[str] = None

    # Auditoría
    fecha_creacion: Optional[datetime] = None
    fecha_actualizacion: Optional[datetime] = None


class NominaMovimientoCreate(BaseModel):
    """DTO para registrar un movimiento en la nómina."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        use_enum_values=True,
    )

    nomina_empleado_id: int
    concepto_id: int
    tipo: str = Field(..., description="PERCEPCION / DEDUCCION / OTRO_PAGO")
    origen: str = Field(default='SISTEMA')
    monto: Decimal = Field(..., ge=0)
    monto_gravable: Decimal = Field(default=Decimal('0'), ge=0)
    monto_exento: Decimal = Field(default=Decimal('0'), ge=0)
    es_automatico: bool = Field(default=True)
    notas: Optional[str] = Field(None, max_length=255)
    registrado_por: Optional[str] = None


class NominaMovimientoResumen(BaseModel):
    """Resumen con datos JOIN del concepto para la UI del recibo."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    nomina_empleado_id: int
    concepto_id: int
    tipo: str
    origen: str
    monto: Decimal
    monto_gravable: Decimal = Decimal('0')
    monto_exento: Decimal = Decimal('0')
    es_automatico: bool

    # Campos JOIN (concepto)
    concepto_clave: str = ""
    concepto_nombre: str = ""
