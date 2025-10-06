from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Optional, List, Dict
from pydantic import BaseModel, Field, ConfigDict

class TipoPeriodo(str, Enum):
    SEMANAL = 'SEMANAL'
    QUINCENAL = 'QUINCENAL'
    MENSUAL = 'MENSUAL'

class EstatusNomina(str, Enum):
    BORRADOR = 'BORRADOR'
    REVISION = 'REVISION'
    APROBADA = 'APROBADA'
    PAGADA = 'PAGADA'
    CANCELADA = 'CANCELADA'
    TIMBRADA = 'TIMBRADA'

class PeriodoNomina(BaseModel):
    """Modelo para períodos de nómina"""
    
    model_config = ConfigDict(
        use_enum_values=True,
        str_strip_whitespace=True,
        validate_assignment=True,
        from_attributes=True
    )
    
    id: Optional[int] = None
    empresa_id: int
    tipo_periodo: TipoPeriodo
    numero_periodo: int
    anio: int
    fecha_inicio: date
    fecha_fin: date
    fecha_pago: date
    
    # Control
    estatus: EstatusNomina = Field(default=EstatusNomina.BORRADOR)
    total_empleados: int = Field(default=0, ge=0)
    total_percepciones: Decimal = Field(default=Decimal('0'), decimal_places=2)
    total_deducciones: Decimal = Field(default=Decimal('0'), decimal_places=2)
    total_neto: Decimal = Field(default=Decimal('0'), decimal_places=2)
    
    # Proceso
    procesado_por: Optional[int] = None
    fecha_proceso: Optional[datetime] = None
    aprobado_por: Optional[int] = None
    fecha_aprobacion: Optional[datetime] = None
    
    # Timbrado
    timbrado: bool = Field(default=False)
    fecha_timbrado: Optional[datetime] = None
    folios_fiscales: List[str] = Field(default_factory=list)
    
    observaciones: Optional[str] = None


class NominaEmpleado(BaseModel):
    """Modelo para nómina individual por empleado"""
    
    model_config = ConfigDict(
        use_enum_values=True,
        str_strip_whitespace=True,
        validate_assignment=True,
        from_attributes=True,
        json_encoders={
            Decimal: lambda v: float(v)
        }
    )
    
    id: Optional[int] = None
    periodo_id: int
    empleado_id: int
    
    # Días y horas
    dias_trabajados: int = Field(ge=0)
    horas_normales: float = Field(ge=0)
    horas_extra_dobles: float = Field(default=0, ge=0)
    horas_extra_triples: float = Field(default=0, ge=0)
    
    # Percepciones
    sueldo_base: Decimal = Field(decimal_places=2)
    tiempo_extra: Decimal = Field(default=Decimal('0'), decimal_places=2)
    prima_dominical: Decimal = Field(default=Decimal('0'), decimal_places=2)
    prima_vacacional: Decimal = Field(default=Decimal('0'), decimal_places=2)
    aguinaldo: Decimal = Field(default=Decimal('0'), decimal_places=2)
    bonos: Decimal = Field(default=Decimal('0'), decimal_places=2)
    comisiones: Decimal = Field(default=Decimal('0'), decimal_places=2)
    otras_percepciones: Dict[str, Decimal] = Field(default_factory=dict)
    total_percepciones: Decimal = Field(decimal_places=2)
    
    # Deducciones
    imss: Decimal = Field(decimal_places=2)
    isr: Decimal = Field(decimal_places=2)
    prestamo: Decimal = Field(default=Decimal('0'), decimal_places=2)
    fonacot: Decimal = Field(default=Decimal('0'), decimal_places=2)
    infonavit: Decimal = Field(default=Decimal('0'), decimal_places=2)
    pension_alimenticia: Decimal = Field(default=Decimal('0'), decimal_places=2)
    otras_deducciones: Dict[str, Decimal] = Field(default_factory=dict)
    total_deducciones: Decimal = Field(decimal_places=2)
    
    # Neto
    neto_pagar: Decimal = Field(decimal_places=2)
    
    # Pago
    metodo_pago: str = Field(default="TRANSFERENCIA")
    banco: Optional[str] = None
    cuenta: Optional[str] = None
    
    # Timbrado
    uuid_fiscal: Optional[str] = Field(None, max_length=36)
    fecha_timbrado: Optional[datetime] = None
    xml_timbrado: Optional[str] = None
    
    # Control
    fecha_calculo: datetime
    observaciones: Optional[str] = None