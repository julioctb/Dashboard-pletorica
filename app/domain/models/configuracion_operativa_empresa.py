"""
Entidad de dominio para la configuración operativa de empresas.

Relación 1:1 con empresas. Controla parámetros de pago
y bloqueo de cuentas bancarias.
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict

from app.domain.enums import PeriodicidadNomina, ReglaCalculoQuincenal


class ConfiguracionOperativaEmpresa(BaseModel):
    """Configuración operativa de una empresa (1:1)."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        from_attributes=True,
    )

    id: Optional[int] = None
    empresa_id: int
    tipo_nomina: PeriodicidadNomina = Field(
        default=PeriodicidadNomina.QUINCENAL,
        description="Periodicidad configurada para la nomina de la empresa",
    )
    regla_calculo_quincenal: ReglaCalculoQuincenal = Field(
        default=ReglaCalculoQuincenal.MIXTA,
        description="Regla de calculo del sueldo base en nomina quincenal",
    )
    contrato_nomina_id: Optional[int] = Field(
        default=None,
        description="Contrato base que delimita la operacion de nomina",
    )

    dias_bloqueo_cuenta_antes_pago: int = Field(
        default=3, ge=1, le=10,
        description="Días antes del pago en que se bloquean cambios bancarios"
    )
    dia_pago_primera_quincena: int = Field(
        default=15, ge=1, le=31,
        description="Día del mes para pago de primera quincena"
    )
    dia_pago_segunda_quincena: int = Field(
        default=0, ge=0, le=31,
        description="Día del mes para pago de segunda quincena (0=último día)"
    )
    dia_pago_semanal: int = Field(
        default=5, ge=1, le=7,
        description="Dia de pago semanal usando base 1=Lunes ... 7=Domingo",
    )
    dia_pago_mensual: int = Field(
        default=0, ge=0, le=31,
        description="Dia de pago mensual (0=ultimo dia del mes)",
    )

    # Auditoría
    fecha_creacion: Optional[datetime] = None
    fecha_actualizacion: Optional[datetime] = None


class ConfiguracionOperativaEmpresaCreate(BaseModel):
    """DTO para crear configuración operativa."""

    model_config = ConfigDict(str_strip_whitespace=True)

    empresa_id: int
    tipo_nomina: PeriodicidadNomina = Field(default=PeriodicidadNomina.QUINCENAL)
    regla_calculo_quincenal: ReglaCalculoQuincenal = Field(
        default=ReglaCalculoQuincenal.MIXTA
    )
    contrato_nomina_id: Optional[int] = None
    dias_bloqueo_cuenta_antes_pago: int = Field(default=3, ge=1, le=10)
    dia_pago_primera_quincena: int = Field(default=15, ge=1, le=31)
    dia_pago_segunda_quincena: int = Field(default=0, ge=0, le=31)
    dia_pago_semanal: int = Field(default=5, ge=1, le=7)
    dia_pago_mensual: int = Field(default=0, ge=0, le=31)


class ConfiguracionOperativaEmpresaUpdate(BaseModel):
    """DTO para actualizar configuración operativa (todos opcionales)."""

    model_config = ConfigDict(str_strip_whitespace=True)

    dias_bloqueo_cuenta_antes_pago: Optional[int] = Field(None, ge=1, le=10)
    tipo_nomina: Optional[PeriodicidadNomina] = None
    regla_calculo_quincenal: Optional[ReglaCalculoQuincenal] = None
    contrato_nomina_id: Optional[int] = None
    dia_pago_primera_quincena: Optional[int] = Field(None, ge=1, le=31)
    dia_pago_segunda_quincena: Optional[int] = Field(None, ge=0, le=31)
    dia_pago_semanal: Optional[int] = Field(None, ge=1, le=7)
    dia_pago_mensual: Optional[int] = Field(None, ge=0, le=31)
