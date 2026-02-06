"""
Entidades de dominio para Entregables.

Los entregables son los comprobantes del servicio contratado que las empresas
proveedoras deben entregar periódicamente a la BUAP para demostrar el
cumplimiento del contrato y habilitar el proceso de pago.

Flujo:
    1. Se configura el contrato con tipos de entregable requeridos
    2. Sistema genera períodos automáticamente (lazy, al consultar)
    3. Cliente sube archivos → estatus EN_REVISION
    4. BUAP revisa → APROBADO (crea pago) o RECHAZADO (con observaciones)
    5. Cliente sube factura → Pago EN_PROCESO → PAGADO
"""

from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict, field_validator, model_validator

# Usar ENUMs del módulo centralizado
from app.core.enums import (
    TipoEntregable,
    PeriodicidadEntregable,
    EstatusEntregable,
)

# Usar conversores existentes (NO duplicar)
from app.core.validation.decimal_converters import convertir_a_decimal_opcional

# Usar text_utils existentes para formateo
from app.core.text_utils import formatear_fecha


# =============================================================================
# CONSTANTES DE VALIDACIÓN
# =============================================================================

DESCRIPCION_TIPO_MAX = 200
INSTRUCCIONES_MAX = 1000
OBSERVACIONES_MAX = 2000


# =============================================================================
# ENTIDAD: ContratoTipoEntregable (Configuración)
# =============================================================================

class ContratoTipoEntregable(BaseModel):
    """
    Configuración de tipo de entregable para un contrato.
    
    Define qué tipos de entregable debe entregar la empresa proveedora
    y con qué periodicidad.
    """
    
    model_config = ConfigDict(
        use_enum_values=True,
        str_strip_whitespace=True,
        validate_assignment=True,
        from_attributes=True,
    )
    
    id: Optional[int] = None
    contrato_id: int = Field(..., description="FK al contrato")
    
    tipo_entregable: TipoEntregable = Field(
        ...,
        description="Tipo: FOTOGRAFICO, REPORTE, LISTADO, DOCUMENTAL"
    )
    periodicidad: PeriodicidadEntregable = Field(
        default=PeriodicidadEntregable.MENSUAL,
        description="Periodicidad de entrega"
    )
    
    requerido: bool = Field(
        default=True,
        description="Si es obligatorio para aprobar el período"
    )
    descripcion: Optional[str] = Field(
        None,
        max_length=DESCRIPCION_TIPO_MAX,
        description="Nombre personalizado (ej: 'Fotos de limpieza')"
    )
    instrucciones: Optional[str] = Field(
        None,
        max_length=INSTRUCCIONES_MAX,
        description="Instrucciones para el cliente"
    )
    
    fecha_creacion: Optional[datetime] = None
    fecha_actualizacion: Optional[datetime] = None


class ContratoTipoEntregableCreate(BaseModel):
    """DTO para crear configuración de tipo de entregable."""
    
    model_config = ConfigDict(str_strip_whitespace=True, use_enum_values=True)
    
    contrato_id: int
    tipo_entregable: TipoEntregable
    periodicidad: PeriodicidadEntregable = PeriodicidadEntregable.MENSUAL
    requerido: bool = True
    descripcion: Optional[str] = Field(None, max_length=DESCRIPCION_TIPO_MAX)
    instrucciones: Optional[str] = Field(None, max_length=INSTRUCCIONES_MAX)


class ContratoTipoEntregableUpdate(BaseModel):
    """DTO para actualizar configuración de tipo de entregable."""
    
    model_config = ConfigDict(str_strip_whitespace=True, use_enum_values=True)
    
    periodicidad: Optional[PeriodicidadEntregable] = None
    requerido: Optional[bool] = None
    descripcion: Optional[str] = Field(None, max_length=DESCRIPCION_TIPO_MAX)
    instrucciones: Optional[str] = Field(None, max_length=INSTRUCCIONES_MAX)


# =============================================================================
# ENTIDAD: Entregable (Operativa principal)
# =============================================================================

class Entregable(BaseModel):
    """
    Entregable de un período específico.
    
    Representa el "paquete" de entrega que incluye todos los tipos
    configurados para el contrato (fotos, reportes, listados, etc.)
    """
    
    model_config = ConfigDict(
        use_enum_values=True,
        str_strip_whitespace=True,
        validate_assignment=True,
        from_attributes=True,
    )
    
    id: Optional[int] = None
    contrato_id: int = Field(..., description="FK al contrato")
    
    periodo_inicio: date = Field(..., description="Inicio del período")
    periodo_fin: date = Field(..., description="Fin del período")
    numero_periodo: int = Field(..., gt=0, description="Consecutivo: 1, 2, 3...")
    
    estatus: EstatusEntregable = Field(
        default=EstatusEntregable.PENDIENTE,
        description="Estado actual del entregable"
    )
    
    fecha_entrega: Optional[datetime] = Field(
        None, description="Cuándo el cliente subió los archivos"
    )
    fecha_revision: Optional[datetime] = Field(
        None, description="Cuándo BUAP revisó"
    )
    revisado_por: Optional[UUID] = Field(
        None, description="UUID del usuario que revisó"
    )
    
    observaciones_rechazo: Optional[str] = Field(
        None, max_length=OBSERVACIONES_MAX, description="Motivo del rechazo"
    )
    
    monto_calculado: Optional[Decimal] = Field(
        None, ge=0, decimal_places=2, description="Calculado según detalle de personal"
    )
    monto_aprobado: Optional[Decimal] = Field(
        None, ge=0, decimal_places=2, description="Aprobado por BUAP"
    )
    
    pago_id: Optional[int] = Field(
        None, description="FK al pago creado al aprobar"
    )
    
    fecha_creacion: Optional[datetime] = None
    fecha_actualizacion: Optional[datetime] = None
    
    # =========================================================================
    # VALIDADORES (usando helpers existentes)
    # =========================================================================
    
    @model_validator(mode='after')
    def validar_periodo(self) -> 'Entregable':
        """Valida que periodo_fin >= periodo_inicio"""
        if self.periodo_fin < self.periodo_inicio:
            raise ValueError(
                f"El fin del período ({self.periodo_fin}) no puede ser "
                f"anterior al inicio ({self.periodo_inicio})"
            )
        return self
    
    @field_validator('monto_calculado', 'monto_aprobado', mode='before')
    @classmethod
    def convertir_montos(cls, v):
        """Usa conversor existente de app.core.validation"""
        return convertir_a_decimal_opcional(v)
    
    # =========================================================================
    # PROPIEDADES DE NEGOCIO
    # =========================================================================
    
    @property
    def puede_editar_cliente(self) -> bool:
        """El cliente puede editar si está PENDIENTE o RECHAZADO"""
        return self.estatus in (
            EstatusEntregable.PENDIENTE,
            EstatusEntregable.RECHAZADO,
        )
    
    @property
    def puede_revisar_admin(self) -> bool:
        """El admin puede revisar si está EN_REVISION"""
        return self.estatus == EstatusEntregable.EN_REVISION
    
    @property
    def esta_aprobado(self) -> bool:
        return self.estatus == EstatusEntregable.APROBADO
    
    @property
    def tiene_pago(self) -> bool:
        return self.pago_id is not None
    
    @property
    def periodo_texto(self) -> str:
        """Retorna el período en formato legible usando formatear_fecha existente"""
        inicio = formatear_fecha(self.periodo_inicio, formato="%d/%m/%Y")
        fin = formatear_fecha(self.periodo_fin, formato="%d/%m/%Y")
        return f"{inicio} - {fin}"


class EntregableCreate(BaseModel):
    """DTO para crear un entregable (normalmente se genera automáticamente)."""
    
    model_config = ConfigDict(str_strip_whitespace=True, use_enum_values=True)
    
    contrato_id: int
    periodo_inicio: date
    periodo_fin: date
    numero_periodo: int = Field(..., gt=0)
    estatus: EstatusEntregable = EstatusEntregable.PENDIENTE


class EntregableUpdate(BaseModel):
    """DTO para actualizar un entregable."""
    
    model_config = ConfigDict(str_strip_whitespace=True, use_enum_values=True)
    
    estatus: Optional[EstatusEntregable] = None
    fecha_entrega: Optional[datetime] = None
    fecha_revision: Optional[datetime] = None
    revisado_por: Optional[UUID] = None
    observaciones_rechazo: Optional[str] = Field(None, max_length=OBSERVACIONES_MAX)
    monto_calculado: Optional[Decimal] = Field(None, ge=0)
    monto_aprobado: Optional[Decimal] = Field(None, ge=0)
    pago_id: Optional[int] = None


class EntregableResumen(BaseModel):
    """Resumen de entregable para listados con datos enriquecidos."""
    
    model_config = ConfigDict(use_enum_values=True, from_attributes=True)
    
    id: int
    contrato_id: int
    numero_periodo: int
    periodo_inicio: date
    periodo_fin: date
    estatus: str
    fecha_entrega: Optional[datetime] = None
    monto_aprobado: Optional[Decimal] = None
    
    contrato_codigo: Optional[str] = None
    empresa_id: Optional[int] = None
    empresa_nombre: Optional[str] = None
    observaciones_rechazo: Optional[str] = None

    @property
    def periodo_texto(self) -> str:
        inicio = formatear_fecha(self.periodo_inicio, formato="%d/%m/%Y")
        fin = formatear_fecha(self.periodo_fin, formato="%d/%m/%Y")
        return f"{inicio} - {fin}"
    
    @property
    def estatus_descripcion(self) -> str:
        """Usa el ENUM para obtener descripción"""
        try:
            return EstatusEntregable(self.estatus).descripcion
        except ValueError:
            return self.estatus


# =============================================================================
# ENTIDAD: EntregableDetallePersonal
# =============================================================================

class EntregableDetallePersonal(BaseModel):
    """
    Detalle de personal reportado por categoría en un entregable.
    Se genera al parsear el archivo LISTADO (CSV/XLS).
    """
    
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        from_attributes=True,
    )
    
    id: Optional[int] = None
    entregable_id: int = Field(..., description="FK al entregable")
    contrato_categoria_id: int = Field(..., description="FK a contrato_categorias")
    
    cantidad_reportada: int = Field(default=0, ge=0)
    cantidad_validada: int = Field(default=0, ge=0)
    
    tarifa_unitaria: Decimal = Field(..., ge=0, decimal_places=2)
    subtotal: Decimal = Field(..., ge=0, decimal_places=2)
    
    fecha_creacion: Optional[datetime] = None
    
    @field_validator('tarifa_unitaria', 'subtotal', mode='before')
    @classmethod
    def convertir_montos(cls, v):
        if v is None:
            return Decimal("0")
        return convertir_a_decimal_opcional(v) or Decimal("0")
    
    def calcular_subtotal(self) -> Decimal:
        return Decimal(str(self.cantidad_validada)) * self.tarifa_unitaria
    
    @property
    def tiene_diferencia(self) -> bool:
        return self.cantidad_reportada != self.cantidad_validada


class EntregableDetallePersonalCreate(BaseModel):
    """DTO para crear detalle de personal."""
    
    model_config = ConfigDict(str_strip_whitespace=True)
    
    entregable_id: int
    contrato_categoria_id: int
    cantidad_reportada: int = Field(default=0, ge=0)
    cantidad_validada: int = Field(default=0, ge=0)
    tarifa_unitaria: Decimal = Field(..., ge=0)
    subtotal: Decimal = Field(..., ge=0)


class EntregableDetallePersonalResumen(BaseModel):
    """Resumen con datos de la categoría para UI."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    entregable_id: int
    contrato_categoria_id: int
    cantidad_reportada: int
    cantidad_validada: int
    tarifa_unitaria: Decimal
    subtotal: Decimal
    
    categoria_clave: str = ""
    categoria_nombre: str = ""
    cantidad_minima: int = 0
    cantidad_maxima: int = 0
    
    @property
    def cumple_minimo(self) -> bool:
        return self.cantidad_validada >= self.cantidad_minima
    
    @property
    def excede_maximo(self) -> bool:
        return self.cantidad_validada > self.cantidad_maxima


# =============================================================================
# MODELOS DE ESTADÍSTICAS Y ALERTAS
# =============================================================================

class ResumenEntregablesContrato(BaseModel):
    """Resumen de entregables para un contrato específico."""
    
    model_config = ConfigDict(from_attributes=True)
    
    contrato_id: int
    codigo_contrato: str = ""
    
    total_periodos: int = 0
    pendientes: int = 0
    en_revision: int = 0
    aprobados: int = 0
    rechazados: int = 0
    
    monto_total_aprobado: Decimal = Decimal("0")
    monto_total_pagado: Decimal = Decimal("0")
    
    @property
    def porcentaje_cumplimiento(self) -> Decimal:
        if self.total_periodos == 0:
            return Decimal("0")
        return (Decimal(str(self.aprobados)) / Decimal(str(self.total_periodos))) * 100


class AlertaEntregables(BaseModel):
    """Alertas de entregables para el dashboard del admin."""
    
    model_config = ConfigDict(from_attributes=True)
    
    total_en_revision: int = 0
    entregables: List[EntregableResumen] = []
    
    @property
    def tiene_alertas(self) -> bool:
        return self.total_en_revision > 0
    
    @property
    def mensaje(self) -> str:
        if self.total_en_revision == 0:
            return "No hay entregables pendientes de revisión"
        elif self.total_en_revision == 1:
            return "Tienes 1 entregable en revisión"
        else:
            return f"Tienes {self.total_en_revision} entregables en revisión"
