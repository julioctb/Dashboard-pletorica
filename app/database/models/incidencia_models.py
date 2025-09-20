from datetime import date, datetime
from enum import Enum
from typing import Optional
from decimal import Decimal
from pydantic import BaseModel, Field, ConfigDict, field_validator


class TipoIncidencia(str, Enum):
    FALTA = 'FALTA'
    FALTA_JUSTIFICADA = 'FALTA_JUSTIFICADA'
    RETARDO = 'RETARDO'
    PERMISO = 'PERMISO'
    PERMISO_SIN_GOCE = 'PERMISO_SIN_GOCE'
    INCAPACIDAD_ENFERMEDAD = 'INCAPACIDAD_ENFERMEDAD'
    INCAPACIDAD_MATERNIDAD = 'INCAPACIDAD_MATERNIDAD'
    INCAPACIDAD_RIESGO = 'INCAPACIDAD_RIESGO'
    VACACIONES = 'VACACIONES'
    DIA_FESTIVO = 'DIA_FESTIVO'
    SUSPENSION = 'SUSPENSION'
    LICENCIA = 'LICENCIA'

class EstatusIncidencia(str, Enum):
    PENDIENTE = 'PENDIENTE'
    AUTORIZADA = 'AUTORIZADA'
    RECHAZADA = 'RECHAZADA'
    CANCELADA = 'CANCELADA'

class Incidencia(BaseModel):
    """Modelo para gestión de incidencias"""
    
    model_config = ConfigDict(
        use_enum_values=True,
        str_strip_whitespace=True,
        validate_assignment=True,
        from_attributes=True
    )
    
    id: Optional[int] = None
    empleado_id: int
    tipo: TipoIncidencia
    fecha_inicio: date
    fecha_fin: date
    dias_totales: Optional[int] = Field(None, gt=0)
    
    # Detalles
    motivo: str = Field(max_length=500)
    folio_incapacidad: Optional[str] = Field(None, max_length=50)
    institucion_medica: Optional[str] = Field(None, max_length=100)
    documento_url: Optional[str] = Field(None, max_length=500)
    
    # Autorización
    estatus: EstatusIncidencia = Field(default=EstatusIncidencia.PENDIENTE)
    solicitado_por: int
    autorizado_por: Optional[int] = None
    fecha_autorizacion: Optional[datetime] = None
    comentarios_autorizacion: Optional[str] = Field(None, max_length=500)
    
    # Afectación en nómina
    afecta_nomina: bool = Field(default=True)
    descuento_aplicado: Optional[Decimal] = Field(None, decimal_places=2)
    
    # Control
    fecha_creacion: Optional[datetime] = None
    fecha_actualizacion: Optional[datetime] = None
    
    @field_validator('fecha_fin')
    @classmethod
    def validar_fechas(cls, v, info):
        """Valida que fecha_fin sea mayor o igual a fecha_inicio"""
        if 'fecha_inicio' in info.data:
            if v < info.data['fecha_inicio']:
                raise ValueError('La fecha fin debe ser posterior a la fecha inicio')
        return v
    
    def calcular_dias(self) -> int:
        """Calcula los días totales de la incidencia"""
        return (self.fecha_fin - self.fecha_inicio).days + 1