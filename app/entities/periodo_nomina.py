"""
Entidades de dominio para períodos de nómina.

Un PeriodoNomina es el contenedor principal que agrupa los recibos
individuales de todos los empleados para un rango de fechas dado.
"""
from datetime import date, datetime
from decimal import Decimal
from typing import ClassVar, Optional

from pydantic import BaseModel, Field, ConfigDict, model_validator


class PeriodoNomina(BaseModel):
    """
    Período de nómina (tabla periodos_nomina).

    Contenedor principal que representa un ciclo de pago completo.
    Los totales se recalculan al cerrar/calcular el período.
    """
    model_config = ConfigDict(
        use_enum_values=True,
        str_strip_whitespace=True,
        from_attributes=True,
    )

    id: Optional[int] = None
    empresa_id: int
    contrato_id: Optional[int] = None

    nombre: str = Field(..., max_length=100, description="Nombre descriptivo del período")
    periodicidad: str = Field(default='QUINCENAL')
    fecha_inicio: date
    fecha_fin: date
    fecha_pago: Optional[date] = None

    estatus: str = Field(default='BORRADOR')

    # Totales (calculados/actualizados al cerrar)
    total_percepciones: Decimal = Field(default=Decimal('0'), ge=0)
    total_deducciones: Decimal = Field(default=Decimal('0'), ge=0)
    total_otros_pagos: Decimal = Field(default=Decimal('0'), ge=0)
    total_neto: Decimal = Field(default=Decimal('0'), ge=0)
    total_empleados: int = Field(default=0, ge=0)

    # Workflow — quién envió / cerró
    enviado_contabilidad_por: Optional[str] = None
    enviado_contabilidad_fecha: Optional[datetime] = None
    cerrado_por: Optional[str] = None
    fecha_cierre: Optional[datetime] = None

    notas: Optional[str] = None

    # Auditoría
    fecha_creacion: Optional[datetime] = None
    fecha_actualizacion: Optional[datetime] = None

    # =========================================================================
    # Mapa de transiciones válidas del workflow
    # =========================================================================
    TRANSICIONES_VALIDAS: ClassVar[dict[str, list[str]]] = {
        'BORRADOR': ['EN_PREPARACION_RRHH'],
        'EN_PREPARACION_RRHH': ['ENVIADO_A_CONTABILIDAD', 'BORRADOR'],
        'ENVIADO_A_CONTABILIDAD': ['EN_PROCESO_CONTABILIDAD', 'EN_PREPARACION_RRHH'],
        'EN_PROCESO_CONTABILIDAD': ['CALCULADO', 'ENVIADO_A_CONTABILIDAD'],
        'CALCULADO': ['CERRADO', 'EN_PROCESO_CONTABILIDAD'],
        'CERRADO': [],
    }

    @classmethod
    def es_transicion_valida(cls, actual: str, nuevo: str) -> bool:
        """Verifica si la transición de estatus es permitida."""
        return nuevo in cls.TRANSICIONES_VALIDAS.get(actual, [])


class PeriodoNominaCreate(BaseModel):
    """DTO para crear un período de nómina."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        use_enum_values=True,
    )

    empresa_id: int
    contrato_id: Optional[int] = None
    nombre: str = Field(..., max_length=100)
    periodicidad: str = Field(default='QUINCENAL')
    fecha_inicio: date
    fecha_fin: date
    fecha_pago: Optional[date] = None
    notas: Optional[str] = None

    @model_validator(mode='after')
    def validar_fechas(self) -> 'PeriodoNominaCreate':
        if self.fecha_fin < self.fecha_inicio:
            raise ValueError("fecha_fin debe ser mayor o igual a fecha_inicio")
        if self.fecha_pago is not None and self.fecha_pago < self.fecha_inicio:
            raise ValueError("fecha_pago debe ser mayor o igual a fecha_inicio")
        return self


class PeriodoNominaUpdate(BaseModel):
    """DTO para actualizar campos editables de un período."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        use_enum_values=True,
    )

    nombre: Optional[str] = Field(None, max_length=100)
    periodicidad: Optional[str] = None
    fecha_inicio: Optional[date] = None
    fecha_fin: Optional[date] = None
    fecha_pago: Optional[date] = None
    notas: Optional[str] = None


class PeriodoNominaResumen(BaseModel):
    """Resumen ligero para listados en UI."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    empresa_id: int
    contrato_id: Optional[int] = None
    nombre: str
    periodicidad: str
    fecha_inicio: date
    fecha_fin: date
    fecha_pago: Optional[date] = None
    estatus: str
    total_percepciones: Decimal = Decimal('0')
    total_deducciones: Decimal = Decimal('0')
    total_neto: Decimal = Decimal('0')
    total_empleados: int = 0
    fecha_creacion: Optional[datetime] = None
