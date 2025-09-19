"""
Modelos para el tracking completo del historial laboral de empleados
Crítico para auditoría y trazabilidad
"""

from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict

class TipoMovimiento(str, Enum):
    """Tipos de movimientos laborales"""
    # Altas y Bajas
    ALTA = 'ALTA'
    REINGRESO = 'REINGRESO'
    BAJA = 'BAJA'
    BAJA_VOLUNTARIA = 'BAJA_VOLUNTARIA'
    DESPIDO = 'DESPIDO'
    TERMINO_CONTRATO = 'TERMINO_CONTRATO'
    
    # Cambios organizacionales
    CAMBIO_EMPRESA = 'CAMBIO_EMPRESA'
    CAMBIO_SEDE = 'CAMBIO_SEDE'
    CAMBIO_DEPARTAMENTO = 'CAMBIO_DEPARTAMENTO'
    CAMBIO_PUESTO = 'CAMBIO_PUESTO'
    PROMOCION = 'PROMOCION'
    CAMBIO_JEFE = 'CAMBIO_JEFE'
    
    # Cambios salariales
    AUMENTO_SUELDO = 'AUMENTO_SUELDO'
    AJUSTE_SUELDO = 'AJUSTE_SUELDO'
    CAMBIO_SDI = 'CAMBIO_SDI'
    
    # Cambios contractuales
    CAMBIO_CONTRATO = 'CAMBIO_CONTRATO'
    RENOVACION_CONTRATO = 'RENOVACION_CONTRATO'
    CAMBIO_JORNADA = 'CAMBIO_JORNADA'
    
    # Suspensiones y permisos
    SUSPENSION = 'SUSPENSION'
    PERMISO_SIN_GOCE = 'PERMISO_SIN_GOCE'
    INCAPACIDAD = 'INCAPACIDAD'
    LICENCIA = 'LICENCIA'
    RETORNO_INCAPACIDAD = 'RETORNO_INCAPACIDAD'
    
    # Prestaciones
    CAMBIO_PRESTACIONES = 'CAMBIO_PRESTACIONES'
    ALTA_INFONAVIT = 'ALTA_INFONAVIT'
    BAJA_INFONAVIT = 'BAJA_INFONAVIT'
    ALTA_FONACOT = 'ALTA_FONACOT'
    BAJA_FONACOT = 'BAJA_FONACOT'
    PENSION_ALIMENTICIA = 'PENSION_ALIMENTICIA'


class HistorialLaboral(BaseModel):
    """Modelo para la tabla historial_laboral"""
    
    model_config = ConfigDict(
        use_enum_values=True,
        str_strip_whitespace=True,
        validate_assignment=True,
        from_attributes=True,
        json_encoders={
            Decimal: lambda v: float(v),
            date: lambda v: v.isoformat(),
            datetime: lambda v: v.isoformat()
        }
    )
    
    # Identificación
    id: Optional[int] = None
    empleado_id: int
    tipo_movimiento: TipoMovimiento
    fecha_movimiento: date
    fecha_efectiva: Optional[date] = Field(
        None,
        description="Fecha en que surte efecto el movimiento (si es diferente)"
    )
    
    # Datos anteriores (para comparación)
    empresa_anterior_id: Optional[int] = None
    sede_anterior_id: Optional[int] = None
    departamento_anterior_id: Optional[int] = None
    puesto_anterior_id: Optional[int] = None
    jefe_anterior_id: Optional[int] = None
    salario_anterior: Optional[Decimal] = Field(None, decimal_places=2)
    sdi_anterior: Optional[Decimal] = Field(None, decimal_places=2)
    contrato_anterior: Optional[str] = None
    
    # Datos nuevos (después del movimiento)
    empresa_id: Optional[int] = None
    sede_id: Optional[int] = None
    departamento_id: Optional[int] = None
    puesto_id: Optional[int] = None
    jefe_directo_id: Optional[int] = None
    salario_diario: Optional[Decimal] = Field(None, decimal_places=2)
    salario_diario_integrado: Optional[Decimal] = Field(None, decimal_places=2)
    tipo_contrato: Optional[str] = None
    
    # Detalles del movimiento
    motivo: str = Field(max_length=500)
    observaciones: Optional[str] = Field(None, max_length=1000)
    
    # Documentación
    documento_soporte: Optional[str] = Field(
        None,
        max_length=500,
        description="URL o referencia al documento"
    )
    folio_documento: Optional[str] = Field(None, max_length=50)
    
    # Para bajas específicamente
    motivo_baja_sat: Optional[str] = Field(
        None,
        max_length=2,
        description="Clave SAT del motivo de baja"
    )
    finiquito_pagado: Optional[bool] = None
    monto_finiquito: Optional[Decimal] = Field(None, decimal_places=2)
    fecha_pago_finiquito: Optional[date] = None
    
    # Para incapacidades
    folio_incapacidad: Optional[str] = Field(None, max_length=50)
    dias_incapacidad: Optional[int] = Field(None, gt=0)
    tipo_incapacidad: Optional[str] = Field(None, max_length=50)
    ramo_seguro: Optional[str] = Field(None, max_length=50)
    
    # Autorización y registro
    autorizado_por: Optional[int] = None
    nombre_autoriza: Optional[str] = Field(None, max_length=100)
    fecha_autorizacion: Optional[datetime] = None
    registrado_por: int
    fecha_registro: datetime = Field(default_factory=datetime.now)
    
    # Impacto en nómina
    afecta_nomina: bool = Field(default=True)
    periodo_aplicacion: Optional[str] = Field(
        None,
        description="Período de nómina donde aplica"
    )
    retroactivo: bool = Field(default=False)
    periodos_retroactivos: Optional[int] = Field(None, ge=0)
    
    # Metadata
    modificado_por: Optional[int] = None
    fecha_modificacion: Optional[datetime] = None
    activo: bool = Field(default=True)
    
    # Campos calculados
    @property
    def cambio_salarial(self) -> Optional[Decimal]:
        """Calcula el cambio salarial si aplica"""
        if self.salario_anterior and self.salario_diario:
            return self.salario_diario - self.salario_anterior
        return None
    
    @property
    def porcentaje_cambio_salarial(self) -> Optional[Decimal]:
        """Calcula el porcentaje de cambio salarial"""
        if self.salario_anterior and self.salario_diario and self.salario_anterior > 0:
            cambio = ((self.salario_diario - self.salario_anterior) / self.salario_anterior) * 100
            return Decimal(str(cambio)).quantize(Decimal('0.01'))
        return None
    
    def es_movimiento_salarial(self) -> bool:
        """Determina si el movimiento afecta el salario"""
        return self.tipo_movimiento in [
            TipoMovimiento.AUMENTO_SUELDO,
            TipoMovimiento.AJUSTE_SUELDO,
            TipoMovimiento.CAMBIO_SDI,
            TipoMovimiento.PROMOCION
        ]
    
    def es_movimiento_baja(self) -> bool:
        """Determina si es un movimiento de baja"""
        return self.tipo_movimiento in [
            TipoMovimiento.BAJA,
            TipoMovimiento.BAJA_VOLUNTARIA,
            TipoMovimiento.DESPIDO,
            TipoMovimiento.TERMINO_CONTRATO
        ]


class HistorialLaboralCreate(BaseModel):
    """Modelo para crear registro en historial laboral"""
    
    model_config = ConfigDict(
        use_enum_values=True,
        str_strip_whitespace=True
    )
    
    empleado_id: int
    tipo_movimiento: TipoMovimiento
    fecha_movimiento: date
    motivo: str
    
    # Campos opcionales según el tipo de movimiento
    empresa_id: Optional[int] = None
    sede_id: Optional[int] = None
    departamento_id: Optional[int] = None
    puesto_id: Optional[int] = None
    salario_diario: Optional[Decimal] = None
    salario_diario_integrado: Optional[Decimal] = None
    
    observaciones: Optional[str] = None
    documento_soporte: Optional[str] = None
    autorizado_por: Optional[int] = None
    registrado_por: int
    
    afecta_nomina: bool = True
    retroactivo: bool = False


class HistorialLaboralResumen(BaseModel):
    """Modelo para mostrar resumen del historial"""
    
    model_config = ConfigDict(
        from_attributes=True
    )
    
    id: int
    fecha_movimiento: date
    tipo_movimiento: str
    descripcion: str
    autorizado_por: Optional[str] = None
    documento: bool = False


# Tabla complementaria para tracking de cambios específicos
class CambiosSalariales(BaseModel):
    """Modelo para tracking detallado de cambios salariales"""
    
    model_config = ConfigDict(
        use_enum_values=True,
        str_strip_whitespace=True,
        validate_assignment=True,
        from_attributes=True
    )
    
    id: Optional[int] = None
    historial_id: int  # Referencia a historial_laboral
    empleado_id: int
    fecha_cambio: date
    
    # Salarios anteriores
    salario_diario_anterior: Decimal = Field(decimal_places=2)
    sdi_anterior: Decimal = Field(decimal_places=2)
    salario_mensual_anterior: Decimal = Field(decimal_places=2)
    
    # Salarios nuevos
    salario_diario_nuevo: Decimal = Field(decimal_places=2)
    sdi_nuevo: Decimal = Field(decimal_places=2)
    salario_mensual_nuevo: Decimal = Field(decimal_places=2)
    
    # Cálculos
    diferencia_diaria: Decimal = Field(decimal_places=2)
    porcentaje_aumento: Decimal = Field(decimal_places=2)
    
    # Detalles
    tipo_aumento: str  # MERITO, PROMOCION, AJUSTE_MERCADO, CONTRACTUAL
    motivo: str
    retroactivo_desde: Optional[date] = None
    monto_retroactivo: Optional[Decimal] = Field(None, decimal_places=2)
    
    # Autorización
    autorizado_por: int
    fecha_autorizacion: datetime
    aplicado_nomina: bool = Field(default=False)
    periodo_aplicacion: Optional[str] = None
    
    fecha_registro: datetime = Field(default_factory=datetime.now)


# Funciones auxiliares para el historial
class HistorialLaboralService:
    """Funciones auxiliares para gestión del historial"""
    
    @staticmethod
    def crear_registro_alta(empleado: Dict) -> HistorialLaboralCreate:
        """Crea registro de alta inicial"""
        return HistorialLaboralCreate(
            empleado_id=empleado['id'],
            tipo_movimiento=TipoMovimiento.ALTA,
            fecha_movimiento=empleado['fecha_ingreso'],
            motivo="Alta inicial en el sistema",
            empresa_id=empleado['empresa_id'],
            sede_id=empleado['sede_id'],
            departamento_id=empleado.get('departamento_id'),
            puesto_id=empleado['puesto_id'],
            salario_diario=empleado['salario_diario'],
            salario_diario_integrado=empleado['salario_diario_integrado'],
            registrado_por=empleado.get('registrado_por', 1),
            observaciones="Registro inicial del empleado en el sistema"
        )
    
    @staticmethod
    def crear_registro_cambio_sueldo(
        empleado_id: int,
        salario_anterior: Decimal,
        salario_nuevo: Decimal,
        sdi_anterior: Decimal,
        sdi_nuevo: Decimal,
        motivo: str,
        autorizado_por: int,
        retroactivo: bool = False
    ) -> HistorialLaboralCreate:
        """Crea registro de cambio de sueldo"""
        
        porcentaje = ((salario_nuevo - salario_anterior) / salario_anterior * 100)
        
        return HistorialLaboralCreate(
            empleado_id=empleado_id,
            tipo_movimiento=TipoMovimiento.AUMENTO_SUELDO,
            fecha_movimiento=date.today(),
            motivo=motivo,
            salario_diario=salario_nuevo,
            salario_diario_integrado=sdi_nuevo,
            observaciones=f"Aumento del {porcentaje:.2f}%. De ${salario_anterior} a ${salario_nuevo}",
            autorizado_por=autorizado_por,
            registrado_por=autorizado_por,
            retroactivo=retroactivo,
            afecta_nomina=True
        )
    
    @staticmethod
    def crear_registro_baja(
        empleado_id: int,
        tipo_baja: TipoMovimiento,
        fecha_baja: date,
        motivo: str,
        motivo_sat: str,
        finiquito: Optional[Decimal] = None,
        autorizado_por: int = 1
    ) -> HistorialLaboralCreate:
        """Crea registro de baja"""
        return HistorialLaboralCreate(
            empleado_id=empleado_id,
            tipo_movimiento=tipo_baja,
            fecha_movimiento=fecha_baja,
            motivo=motivo,
            observaciones=f"Motivo SAT: {motivo_sat}. Finiquito: ${finiquito or 0}",
            autorizado_por=autorizado_por,
            registrado_por=autorizado_por,
            afecta_nomina=True
        )

