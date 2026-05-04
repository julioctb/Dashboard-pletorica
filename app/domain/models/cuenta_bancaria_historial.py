"""
Entidad de dominio para el historial de cambios bancarios de empleados.

Tabla inmutable de auditoría (patrón de empleado_restricciones_log):
solo se insertan registros, nunca se modifican ni eliminan.
"""
from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict

from app.core.validation.constants import (
    CUENTA_BANCARIA_MAX,
    BANCO_MAX,
    CLABE_LEN,
)


class CuentaBancariaHistorial(BaseModel):
    """Registro inmutable de cambio de datos bancarios."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        from_attributes=True,
    )

    id: Optional[int] = None
    empleado_id: int

    # Datos bancarios capturados al momento del cambio
    cuenta_bancaria: Optional[str] = Field(None, max_length=CUENTA_BANCARIA_MAX)
    banco: Optional[str] = Field(None, max_length=BANCO_MAX)
    clabe_interbancaria: Optional[str] = Field(None, max_length=CLABE_LEN)

    # Auditoría
    cambiado_por: UUID
    ip_origen: Optional[str] = Field(None, max_length=45)
    fecha_cambio: datetime = Field(default_factory=datetime.now)

    # Documento soporte
    documento_id: Optional[int] = None

    # Timestamp
    fecha_creacion: Optional[datetime] = None


class CuentaBancariaHistorialCreate(BaseModel):
    """DTO para crear un registro de cambio bancario."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
    )

    empleado_id: int
    cuenta_bancaria: Optional[str] = Field(None, max_length=CUENTA_BANCARIA_MAX)
    banco: Optional[str] = Field(None, max_length=BANCO_MAX)
    clabe_interbancaria: Optional[str] = Field(None, max_length=CLABE_LEN)
    cambiado_por: UUID
    ip_origen: Optional[str] = Field(None, max_length=45)
    documento_id: Optional[int] = None
