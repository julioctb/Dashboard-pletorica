"""
Entidades de dominio para nóminas individuales de empleado.

NominaEmpleado representa el recibo de nómina de un empleado
en un período específico. Contiene snapshots de salario y el
resumen de totales calculados desde los movimientos.
"""
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Optional

from pydantic import BaseModel, Field, ConfigDict

from app.domain.enums import ModoCalculoAguinaldo, TipoJornadaPlaza


class NominaEmpleado(BaseModel):
    """
    Nómina individual de empleado (tabla nominas_empleado).

    Representa el recibo de nómina de un empleado en un período.
    Los campos de salario son snapshots al momento de crear la nómina,
    independientes de cambios posteriores en el empleado.
    """
    model_config = ConfigDict(
        use_enum_values=True,
        str_strip_whitespace=True,
        from_attributes=True,
    )

    id: Optional[int] = None
    periodo_id: int
    empleado_id: int
    empresa_id: int

    estatus: str = Field(default='PENDIENTE')

    # Snapshot de salario al momento de crear la nómina
    salario_diario: Decimal = Field(..., gt=0, description="Salario diario (snapshot)")
    salario_diario_integrado: Optional[Decimal] = Field(
        None, ge=0, description="SDI = SBC (snapshot)"
    )

    # Asistencia del período
    dias_periodo: int = Field(default=0, ge=0)
    dias_trabajados: int = Field(default=0, ge=0)
    dias_faltas: int = Field(default=0, ge=0)
    dias_incapacidad: int = Field(default=0, ge=0)
    dias_vacaciones: int = Field(default=0, ge=0)
    horas_extra_dobles: Decimal = Field(default=Decimal('0'), ge=0)
    horas_extra_triples: Decimal = Field(default=Decimal('0'), ge=0)
    domingos_trabajados: int = Field(default=0, ge=0)
    tipo_jornada: TipoJornadaPlaza = Field(default=TipoJornadaPlaza.COMPLETA)
    factor_jornada: Decimal = Field(default=Decimal('1.0'), gt=0, le=1)
    salario_minimo_diario_aplicable: Decimal = Field(default=Decimal('0'), ge=0)
    es_salario_minimo_art36: bool = False
    imss_obrero_absorbido: Decimal = Field(default=Decimal('0'), ge=0)
    fecha_ingreso_vigente_aguinaldo: Optional[date] = None
    dias_aguinaldo_snapshot: Optional[int] = Field(default=None, ge=15)
    dias_laborados_aguinaldo: int = Field(default=0, ge=0)
    factor_proporcional_aguinaldo: Decimal = Field(default=Decimal('0'), ge=0)
    monto_aguinaldo_bruto: Decimal = Field(default=Decimal('0'), ge=0)
    modo_calculo_aguinaldo: ModoCalculoAguinaldo = Field(default=ModoCalculoAguinaldo.AUTO)
    monto_aguinaldo_override: Optional[Decimal] = Field(default=None, ge=0)
    notas_aguinaldo_override: Optional[str] = None
    listo_para_timbrar: bool = Field(default=False)
    observaciones_fiscales: list[dict[str, Any]] = Field(default_factory=list)

    # Totales (agregados desde nomina_movimientos)
    total_percepciones: Decimal = Field(default=Decimal('0'), ge=0)
    total_deducciones: Decimal = Field(default=Decimal('0'), ge=0)
    total_otros_pagos: Decimal = Field(default=Decimal('0'), ge=0)
    total_neto: Decimal = Field(default=Decimal('0'), ge=0)

    # Datos bancarios (snapshot)
    banco_destino: Optional[str] = Field(None, max_length=100)
    clabe_destino: Optional[str] = Field(None, max_length=18)

    notas: Optional[str] = None

    # Auditoría
    fecha_creacion: Optional[datetime] = None
    fecha_actualizacion: Optional[datetime] = None


class NominaEmpleadoCreate(BaseModel):
    """DTO para crear un registro de nómina individual."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        use_enum_values=True,
    )

    periodo_id: int
    empleado_id: int
    empresa_id: int
    salario_diario: Decimal = Field(..., gt=0)
    salario_diario_integrado: Optional[Decimal] = Field(None, ge=0)
    dias_periodo: int = Field(default=0, ge=0)
    dias_trabajados: int = Field(default=0, ge=0)
    dias_faltas: int = Field(default=0, ge=0)
    dias_incapacidad: int = Field(default=0, ge=0)
    dias_vacaciones: int = Field(default=0, ge=0)
    horas_extra_dobles: Decimal = Field(default=Decimal('0'), ge=0)
    horas_extra_triples: Decimal = Field(default=Decimal('0'), ge=0)
    domingos_trabajados: int = Field(default=0, ge=0)
    tipo_jornada: TipoJornadaPlaza = Field(default=TipoJornadaPlaza.COMPLETA)
    factor_jornada: Decimal = Field(default=Decimal('1.0'), gt=0, le=1)
    salario_minimo_diario_aplicable: Decimal = Field(default=Decimal('0'), ge=0)
    es_salario_minimo_art36: bool = False
    imss_obrero_absorbido: Decimal = Field(default=Decimal('0'), ge=0)
    fecha_ingreso_vigente_aguinaldo: Optional[date] = None
    dias_aguinaldo_snapshot: Optional[int] = Field(default=None, ge=15)
    dias_laborados_aguinaldo: int = Field(default=0, ge=0)
    factor_proporcional_aguinaldo: Decimal = Field(default=Decimal('0'), ge=0)
    monto_aguinaldo_bruto: Decimal = Field(default=Decimal('0'), ge=0)
    modo_calculo_aguinaldo: ModoCalculoAguinaldo = Field(default=ModoCalculoAguinaldo.AUTO)
    monto_aguinaldo_override: Optional[Decimal] = Field(default=None, ge=0)
    notas_aguinaldo_override: Optional[str] = None
    listo_para_timbrar: bool = False
    observaciones_fiscales: list[dict[str, Any]] = Field(default_factory=list)
    banco_destino: Optional[str] = Field(None, max_length=100)
    clabe_destino: Optional[str] = Field(None, max_length=18)
    notas: Optional[str] = None


class NominaEmpleadoUpdate(BaseModel):
    """DTO para actualizar campos editables de una nómina individual."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        use_enum_values=True,
    )

    estatus: Optional[str] = None
    dias_trabajados: Optional[int] = Field(None, ge=0)
    dias_faltas: Optional[int] = Field(None, ge=0)
    dias_incapacidad: Optional[int] = Field(None, ge=0)
    dias_vacaciones: Optional[int] = Field(None, ge=0)
    horas_extra_dobles: Optional[Decimal] = Field(None, ge=0)
    horas_extra_triples: Optional[Decimal] = Field(None, ge=0)
    domingos_trabajados: Optional[int] = Field(None, ge=0)
    tipo_jornada: Optional[TipoJornadaPlaza] = None
    factor_jornada: Optional[Decimal] = Field(None, gt=0, le=1)
    salario_minimo_diario_aplicable: Optional[Decimal] = Field(None, ge=0)
    es_salario_minimo_art36: Optional[bool] = None
    imss_obrero_absorbido: Optional[Decimal] = Field(None, ge=0)
    fecha_ingreso_vigente_aguinaldo: Optional[date] = None
    dias_aguinaldo_snapshot: Optional[int] = Field(default=None, ge=15)
    dias_laborados_aguinaldo: Optional[int] = Field(default=None, ge=0)
    factor_proporcional_aguinaldo: Optional[Decimal] = Field(default=None, ge=0)
    monto_aguinaldo_bruto: Optional[Decimal] = Field(default=None, ge=0)
    modo_calculo_aguinaldo: Optional[ModoCalculoAguinaldo] = None
    monto_aguinaldo_override: Optional[Decimal] = Field(default=None, ge=0)
    notas_aguinaldo_override: Optional[str] = None
    listo_para_timbrar: Optional[bool] = None
    observaciones_fiscales: Optional[list[dict[str, Any]]] = None
    notas: Optional[str] = None


class NominaEmpleadoResumen(BaseModel):
    """Resumen con datos JOIN para listados en UI."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    periodo_id: int
    empleado_id: int
    empresa_id: int
    estatus: str
    salario_diario: Decimal
    dias_trabajados: int = 0
    dias_faltas: int = 0
    tipo_jornada: TipoJornadaPlaza = TipoJornadaPlaza.COMPLETA
    factor_jornada: Decimal = Decimal('1.0')
    fecha_ingreso_vigente_aguinaldo: Optional[date] = None
    dias_aguinaldo_snapshot: Optional[int] = None
    dias_laborados_aguinaldo: int = 0
    factor_proporcional_aguinaldo: Decimal = Decimal('0')
    monto_aguinaldo_bruto: Decimal = Decimal('0')
    modo_calculo_aguinaldo: ModoCalculoAguinaldo = ModoCalculoAguinaldo.AUTO
    monto_aguinaldo_override: Optional[Decimal] = None
    total_percepciones: Decimal = Decimal('0')
    total_deducciones: Decimal = Decimal('0')
    total_neto: Decimal = Decimal('0')
    listo_para_timbrar: bool = False
    observaciones_fiscales: list[dict[str, Any]] = Field(default_factory=list)

    # Campos JOIN (empleado)
    nombre_empleado: str = ""
    clave_empleado: str = ""
