from datetime import date, time, datetime
from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict, field_validator

class TipoAsistencia(str, Enum):
    ENTRADA = 'ENTRADA'
    SALIDA = 'SALIDA'
    ENTRADA_COMIDA = 'ENTRADA_COMIDA'
    SALIDA_COMIDA = 'SALIDA_COMIDA'

class TipoJornada(str, Enum):
    NORMAL = 'NORMAL'
    EXTRA = 'EXTRA'
    FESTIVO = 'FESTIVO'
    DESCANSO = 'DESCANSO'
    DOMINICAL = 'DOMINICAL'

class EstatusAsistencia(str, Enum):
    REGISTRADO = 'REGISTRADO'
    VALIDADO = 'VALIDADO'
    RECHAZADO = 'RECHAZADO'
    CORREGIDO = 'CORREGIDO'

class Asistencia(BaseModel):
    """Modelo para registro de asistencias"""
    
    model_config = ConfigDict(
        use_enum_values=True,
        str_strip_whitespace=True,
        validate_assignment=True,
        from_attributes=True
    )
    
    id: Optional[int] = None
    empleado_id: int
    fecha: date
    
    # Registros de tiempo
    hora_entrada: Optional[time] = None
    hora_salida: Optional[time] = None
    hora_salida_comida: Optional[time] = None
    hora_entrada_comida: Optional[time] = None
    
    # Información adicional
    sede_id: int
    tipo_jornada: TipoJornada = Field(default=TipoJornada.NORMAL)
    horas_trabajadas: Optional[float] = Field(
        None,
        ge=0,
        le=24,
        description="Total de horas trabajadas"
    )
    horas_extra: Optional[float] = Field(
        None,
        ge=0,
        description="Horas extra trabajadas"
    )
    
    # Validación y control
    estatus: EstatusAsistencia = Field(default=EstatusAsistencia.REGISTRADO)
    validado_por: Optional[int] = None
    fecha_validacion: Optional[datetime] = None
    observaciones: Optional[str] = Field(None, max_length=500)
    
    # Metadata
    origen_registro: str = Field(
        default="MANUAL",
        description="MANUAL/RELOJ/IMPORT/APP"
    )
    ip_registro: Optional[str] = Field(None, max_length=45)
    dispositivo_id: Optional[str] = Field(None, max_length=50)
    fecha_creacion: Optional[datetime] = None
    
    @field_validator('hora_salida')
    @classmethod
    def validar_horarios(cls, v, info):
        """Valida que la salida sea después de la entrada"""
        if v and 'hora_entrada' in info.data:
            entrada = info.data['hora_entrada']
            if entrada and v < entrada:
                # Asumimos que es del día siguiente
                pass  # Permitir para turnos nocturnos
        return v
    
    def calcular_horas_trabajadas(self) -> float:
        """Calcula las horas trabajadas totales"""
        if not self.hora_entrada or not self.hora_salida:
            return 0.0
        
        from datetime import datetime, timedelta
        
        # Crear datetime para cálculos
        entrada = datetime.combine(self.fecha, self.hora_entrada)
        salida = datetime.combine(self.fecha, self.hora_salida)
        
        # Si salida es menor que entrada, asumimos día siguiente
        if salida < entrada:
            salida += timedelta(days=1)
        
        # Restar tiempo de comida si existe
        tiempo_comida = timedelta(0)
        if self.hora_salida_comida and self.hora_entrada_comida:
            salida_comida = datetime.combine(self.fecha, self.hora_salida_comida)
            entrada_comida = datetime.combine(self.fecha, self.hora_entrada_comida)
            tiempo_comida = entrada_comida - salida_comida
        
        tiempo_total = salida - entrada - tiempo_comida
        return tiempo_total.total_seconds() / 3600
