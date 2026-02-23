"""
Entidad de dominio para la configuración operativa de empresas.

Relación 1:1 con empresas. Controla parámetros de pago
y bloqueo de cuentas bancarias.
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class ConfiguracionOperativaEmpresa(BaseModel):
    """Configuración operativa de una empresa (1:1)."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        from_attributes=True,
    )

    id: Optional[int] = None
    empresa_id: int

    dias_bloqueo_cuenta_antes_pago: int = Field(
        default=3, ge=1, le=10,
        description="Días antes del pago en que se bloquean cambios bancarios"
    )
    dia_pago_primera_quincena: int = Field(
        default=15, ge=1, le=28,
        description="Día del mes para pago de primera quincena"
    )
    dia_pago_segunda_quincena: int = Field(
        default=0, ge=0, le=28,
        description="Día del mes para pago de segunda quincena (0=último día)"
    )

    # Auditoría
    fecha_creacion: Optional[datetime] = None
    fecha_actualizacion: Optional[datetime] = None


class ConfiguracionOperativaEmpresaCreate(BaseModel):
    """DTO para crear configuración operativa."""

    model_config = ConfigDict(str_strip_whitespace=True)

    empresa_id: int
    dias_bloqueo_cuenta_antes_pago: int = Field(default=3, ge=1, le=10)
    dia_pago_primera_quincena: int = Field(default=15, ge=1, le=28)
    dia_pago_segunda_quincena: int = Field(default=0, ge=0, le=28)


class ConfiguracionOperativaEmpresaUpdate(BaseModel):
    """DTO para actualizar configuración operativa (todos opcionales)."""

    model_config = ConfigDict(str_strip_whitespace=True)

    dias_bloqueo_cuenta_antes_pago: Optional[int] = Field(None, ge=1, le=10)
    dia_pago_primera_quincena: Optional[int] = Field(None, ge=1, le=28)
    dia_pago_segunda_quincena: Optional[int] = Field(None, ge=0, le=28)
