"""
Entidades de dominio para la dispersión bancaria.

Modelos:
    ConfiguracionBancoEmpresa — Configuración de banco para pago de nómina
    DispersionLayout          — Registro de layout generado por período/banco
    ResultadoDispersion       — Resultado de la operación de generación
"""
from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


# =============================================================================
# CONFIGURACION DE BANCO
# =============================================================================

class ConfiguracionBancoEmpresa(BaseModel):
    """Configuración bancaria de una empresa para generación de layouts."""

    model_config = ConfigDict(from_attributes=True)

    id: Optional[int] = None
    empresa_id: int
    nombre_banco: str                          # 'BANREGIO', 'HSBC', 'FONDEADORA'
    formato: str                               # 'TXT_POSICIONES', 'CSV', 'TXT_CSV'
    cuenta_origen: Optional[str] = None
    clabe_origen: Optional[str] = None
    referencia_pago: Optional[str] = None
    activo: bool = True
    fecha_creacion: Optional[datetime] = None
    fecha_actualizacion: Optional[datetime] = None


class ConfiguracionBancoEmpresaCreate(BaseModel):
    empresa_id: int
    nombre_banco: str = Field(..., min_length=2, max_length=100)
    formato: str = Field(..., pattern=r'^(TXT_POSICIONES|CSV|TXT_CSV)$')
    cuenta_origen: Optional[str] = Field(default=None, max_length=30)
    clabe_origen: Optional[str] = Field(default=None, min_length=18, max_length=18)
    referencia_pago: Optional[str] = Field(default=None, max_length=50)
    activo: bool = True


# =============================================================================
# LAYOUT GENERADO
# =============================================================================

class DispersionLayout(BaseModel):
    """Registro de un archivo de dispersión generado."""

    model_config = ConfigDict(from_attributes=True)

    id: Optional[int] = None
    periodo_id: int
    empresa_id: int
    nombre_banco: str
    nombre_archivo: str
    storage_path: str
    total_empleados: int = 0
    total_monto: Decimal = Decimal('0')
    errores: list[str] = []
    generado_por: Optional[str] = None
    fecha_generacion: Optional[datetime] = None


# =============================================================================
# RESULTADO DE GENERACIÓN
# =============================================================================

class ResultadoDispersion(BaseModel):
    """Resultado de la operación de generación de layouts."""

    banco: str
    nombre_archivo: str
    storage_path: str
    total_empleados: int
    total_monto: float
    errores: list[str] = []

    @property
    def tiene_errores(self) -> bool:
        return len(self.errores) > 0
