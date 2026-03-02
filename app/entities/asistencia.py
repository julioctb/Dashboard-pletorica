"""
Entidades de dominio para el modulo de asistencias.
"""
from datetime import date, datetime, time
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.enums import (
    Estatus,
    EstatusJornada,
    OrigenIncidencia,
    TipoIncidencia,
    TipoRegistroAsistencia,
)


class Horario(BaseModel):
    """Horario contractual asociado a un contrato."""

    model_config = ConfigDict(
        use_enum_values=True,
        str_strip_whitespace=True,
        validate_assignment=True,
        from_attributes=True,
    )

    id: Optional[int] = None
    empresa_id: int
    contrato_id: int
    nombre: str = Field(..., max_length=100)
    descripcion: Optional[str] = None
    dias_laborales: dict
    tolerancia_entrada_min: int = Field(default=10, ge=0, le=60)
    tolerancia_salida_min: int = Field(default=0, ge=0, le=60)
    es_horario_activo: bool = True
    estatus: Estatus = Estatus.ACTIVO
    fecha_creacion: Optional[datetime] = None
    fecha_actualizacion: Optional[datetime] = None


class HorarioCreate(BaseModel):
    """DTO para crear o actualizar un horario contractual."""

    empresa_id: int
    contrato_id: int
    nombre: str = Field(..., max_length=100)
    descripcion: Optional[str] = None
    dias_laborales: dict
    tolerancia_entrada_min: int = Field(default=10, ge=0, le=60)
    tolerancia_salida_min: int = Field(default=0, ge=0, le=60)
    es_horario_activo: bool = True
    estatus: Estatus = Estatus.ACTIVO


class SupervisorSede(BaseModel):
    """Asignacion de supervisores a sedes."""

    model_config = ConfigDict(
        use_enum_values=True,
        str_strip_whitespace=True,
        validate_assignment=True,
        from_attributes=True,
    )

    id: Optional[int] = None
    supervisor_id: int
    sede_id: int
    empresa_id: int
    fecha_inicio: date = Field(default_factory=date.today)
    fecha_fin: Optional[date] = None
    activo: bool = True
    notas: Optional[str] = None
    fecha_creacion: Optional[datetime] = None
    fecha_actualizacion: Optional[datetime] = None


class SupervisorSedeCreate(BaseModel):
    """DTO para crear o actualizar una asignacion supervisor-sede."""

    empresa_id: int
    supervisor_id: int
    sede_id: int
    fecha_inicio: date = Field(default_factory=date.today)
    fecha_fin: Optional[date] = None
    activo: bool = True
    notas: Optional[str] = None


class JornadaAsistencia(BaseModel):
    """Sesion diaria de captura de asistencia."""

    model_config = ConfigDict(
        use_enum_values=True,
        str_strip_whitespace=True,
        validate_assignment=True,
        from_attributes=True,
    )

    id: Optional[int] = None
    empresa_id: int
    contrato_id: int
    horario_id: Optional[int] = None
    supervisor_id: Optional[int] = None
    fecha: date
    estatus: EstatusJornada = EstatusJornada.ABIERTA
    empleados_esperados: int = Field(default=0, ge=0)
    novedades_registradas: int = Field(default=0, ge=0)
    notas: Optional[str] = None
    abierta_por: Optional[UUID] = None
    cerrada_por: Optional[UUID] = None
    fecha_apertura: Optional[datetime] = None
    fecha_cierre: Optional[datetime] = None
    fecha_creacion: Optional[datetime] = None
    fecha_actualizacion: Optional[datetime] = None

    @property
    def esta_abierta(self) -> bool:
        return self.estatus == EstatusJornada.ABIERTA


class JornadaAsistenciaCreate(BaseModel):
    """DTO para abrir una jornada."""

    empresa_id: int
    contrato_id: int
    fecha: date = Field(default_factory=date.today)
    horario_id: Optional[int] = None
    supervisor_id: Optional[int] = None
    abierta_por: Optional[UUID] = None
    empleados_esperados: int = Field(default=0, ge=0)
    novedades_registradas: int = Field(default=0, ge=0)
    notas: Optional[str] = None


class IncidenciaAsistencia(BaseModel):
    """Incidencia registrada por excepcion."""

    model_config = ConfigDict(
        use_enum_values=True,
        str_strip_whitespace=True,
        validate_assignment=True,
        from_attributes=True,
    )

    id: Optional[int] = None
    jornada_id: Optional[int] = None
    empleado_id: int
    empresa_id: int
    fecha: date
    tipo_incidencia: TipoIncidencia
    minutos_retardo: int = Field(default=0, ge=0)
    horas_extra: Decimal = Field(default=Decimal("0"), ge=0, decimal_places=2)
    motivo: Optional[str] = None
    documento_soporte_id: Optional[int] = None
    origen: OrigenIncidencia = OrigenIncidencia.SUPERVISOR
    registrado_por: Optional[UUID] = None
    sede_real_id: Optional[int] = None
    fecha_creacion: Optional[datetime] = None
    fecha_actualizacion: Optional[datetime] = None

    @field_validator("horas_extra", mode="before")
    @classmethod
    def convertir_horas_extra(cls, value):
        if value in ("", None):
            return Decimal("0")
        return Decimal(str(value))


class IncidenciaAsistenciaCreate(BaseModel):
    """DTO para crear o actualizar una incidencia."""

    empleado_id: int
    empresa_id: int
    fecha: date = Field(default_factory=date.today)
    tipo_incidencia: TipoIncidencia
    minutos_retardo: int = Field(default=0, ge=0)
    horas_extra: Decimal = Field(default=Decimal("0"), ge=0, decimal_places=2)
    motivo: Optional[str] = None
    origen: OrigenIncidencia = OrigenIncidencia.SUPERVISOR
    registrado_por: Optional[UUID] = None
    sede_real_id: Optional[int] = None

    @field_validator("horas_extra", mode="before")
    @classmethod
    def convertir_horas_extra(cls, value):
        if value in ("", None):
            return Decimal("0")
        return Decimal(str(value))


class RegistroAsistencia(BaseModel):
    """Registro consolidado por empleado y fecha."""

    model_config = ConfigDict(
        use_enum_values=True,
        str_strip_whitespace=True,
        validate_assignment=True,
        from_attributes=True,
    )

    id: Optional[int] = None
    empleado_id: int
    empresa_id: int
    contrato_id: int
    jornada_id: Optional[int] = None
    incidencia_id: Optional[int] = None
    fecha: date
    tipo_registro: TipoRegistroAsistencia
    hora_entrada: Optional[time] = None
    hora_salida: Optional[time] = None
    horas_trabajadas: Optional[Decimal] = Field(default=None, ge=0, decimal_places=2)
    horas_extra: Decimal = Field(default=Decimal("0"), ge=0, decimal_places=2)
    minutos_retardo: int = Field(default=0, ge=0)
    sede_real_id: Optional[int] = None
    es_consolidado: bool = False
    fecha_creacion: Optional[datetime] = None
    fecha_actualizacion: Optional[datetime] = None

    @field_validator("horas_trabajadas", "horas_extra", mode="before")
    @classmethod
    def convertir_decimal(cls, value):
        if value in ("", None):
            return None if value is None else Decimal("0")
        return Decimal(str(value))


class EmpleadoAsistenciaEsperado(BaseModel):
    """Fila enriquecida para la jornada del dia."""

    model_config = ConfigDict(from_attributes=True)

    empleado_id: int
    clave: str = ""
    nombre_completo: str = ""
    curp: str = ""
    sede_id: Optional[int] = None
    sede_nombre: str = ""
    plaza_id: Optional[int] = None
    plaza_codigo: str = ""
    categoria_nombre: str = ""
    estatus_empleado: str = ""
    incidencia_id: Optional[int] = None
    tipo_incidencia: str = ""
    resultado_dia: str = "PENDIENTE"
    minutos_retardo: int = 0
    horas_extra: float = 0.0
    motivo: str = ""
    origen: str = ""
    registro_id: Optional[int] = None
    es_consolidado: bool = False
