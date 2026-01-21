"""
Entidades de dominio para Plaza.

Una Plaza representa un puesto de trabajo específico dentro de un ContratoCategoría.
Por ejemplo, si un contrato tiene asignados 50-70 Jardineros A, existirán 50-70
plazas individuales que pueden ser ocupadas por empleados.

Ejemplo:
    Contrato MAN-JAR-25001 tiene:
        ContratoCategoria: Jardinero A (JARA), cantidad_maxima=70
        → 70 Plazas individuales (PZ-001 a PZ-070)
        → Cada plaza puede estar: VACANTE, OCUPADA, SUSPENDIDA, CANCELADA
"""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict, field_validator

from app.core.enums import EstatusPlaza


class Plaza(BaseModel):
    """
    Entidad principal que representa un puesto de trabajo dentro de un ContratoCategoría.

    Una plaza es una instancia individual de trabajo. Por ejemplo, si un contrato
    requiere 50 jardineros, habrá 50 plazas diferentes.
    """

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        from_attributes=True
    )

    # Identificación
    id: Optional[int] = None
    contrato_categoria_id: int = Field(..., description="FK a contrato_categorias")
    numero_plaza: int = Field(
        ...,
        ge=1,
        description="Número secuencial de la plaza dentro de la categoría (1, 2, 3...)"
    )
    codigo: str = Field(
        default="",
        max_length=50,
        description="Código único de la plaza (ej: PZ-001, JAR-001)"
    )

    # Relación con empleado (opcional - puede estar vacante)
    empleado_id: Optional[int] = Field(
        default=None,
        description="FK a empleados (null si está vacante)"
    )

    # Vigencia
    fecha_inicio: date = Field(..., description="Fecha de inicio de la plaza")
    fecha_fin: Optional[date] = Field(
        default=None,
        description="Fecha de fin (null si es indefinida)"
    )

    # Salario específico de esta plaza
    salario_mensual: Decimal = Field(
        ...,
        ge=0,
        decimal_places=2,
        description="Salario mensual de esta plaza"
    )

    # Estado
    estatus: EstatusPlaza = Field(
        default=EstatusPlaza.VACANTE,
        description="Estado de la plaza"
    )

    # Observaciones
    notas: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="Observaciones adicionales"
    )

    # Auditoría
    fecha_creacion: Optional[datetime] = None
    fecha_actualizacion: Optional[datetime] = None

    # =========================================================================
    # VALIDADORES
    # =========================================================================

    @field_validator('salario_mensual', mode='before')
    @classmethod
    def convertir_salario(cls, v):
        """Convierte el salario a Decimal si es necesario"""
        if v is None:
            return Decimal('0')
        if isinstance(v, str):
            v = v.replace(',', '').replace('$', '').strip()
            if not v:
                return Decimal('0')
        return Decimal(str(v))

    @field_validator('codigo', mode='before')
    @classmethod
    def normalizar_codigo(cls, v):
        """Normaliza el código a mayúsculas"""
        if v is None:
            return ""
        return v.strip().upper()

    # =========================================================================
    # MÉTODOS DE NEGOCIO
    # =========================================================================

    def esta_vacante(self) -> bool:
        """Verifica si la plaza está disponible para asignar"""
        return self.estatus == EstatusPlaza.VACANTE and self.empleado_id is None

    def esta_ocupada(self) -> bool:
        """Verifica si la plaza tiene un empleado asignado"""
        return self.estatus == EstatusPlaza.OCUPADA and self.empleado_id is not None

    def puede_asignar_empleado(self) -> bool:
        """Verifica si se puede asignar un empleado a esta plaza"""
        return self.estatus.es_asignable

    def esta_vigente(self, fecha_referencia: Optional[date] = None) -> bool:
        """Verifica si la plaza está vigente en una fecha"""
        fecha = fecha_referencia or date.today()
        if self.fecha_inicio > fecha:
            return False
        if self.fecha_fin and self.fecha_fin < fecha:
            return False
        return True

    def puede_ocupar(self) -> bool:
        """Verifica si la plaza puede pasar a estado OCUPADA"""
        return self.estatus == EstatusPlaza.VACANTE

    def puede_suspender(self) -> bool:
        """Verifica si la plaza puede ser suspendida"""
        return self.estatus in (EstatusPlaza.VACANTE, EstatusPlaza.OCUPADA)

    def puede_cancelar(self) -> bool:
        """Verifica si la plaza puede ser cancelada"""
        return self.estatus != EstatusPlaza.CANCELADA

    def puede_reactivar(self) -> bool:
        """Verifica si la plaza puede ser reactivada (a VACANTE)"""
        return self.estatus == EstatusPlaza.SUSPENDIDA

    def __str__(self) -> str:
        return f"Plaza({self.codigo or f'#{self.numero_plaza}'}, estatus={self.estatus.value})"


class PlazaCreate(BaseModel):
    """Modelo para crear una nueva plaza"""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True
    )

    contrato_categoria_id: int = Field(..., description="FK a contrato_categorias")
    numero_plaza: int = Field(..., ge=1)
    codigo: str = Field(default="", max_length=50)
    empleado_id: Optional[int] = Field(default=None)
    fecha_inicio: date = Field(...)
    fecha_fin: Optional[date] = Field(default=None)
    salario_mensual: Decimal = Field(..., ge=0)
    estatus: EstatusPlaza = Field(default=EstatusPlaza.VACANTE)
    notas: Optional[str] = Field(default=None, max_length=1000)

    @field_validator('salario_mensual', mode='before')
    @classmethod
    def convertir_salario(cls, v):
        """Convierte el salario a Decimal si es necesario"""
        if v is None:
            return Decimal('0')
        if isinstance(v, str):
            v = v.replace(',', '').replace('$', '').strip()
            if not v:
                return Decimal('0')
        return Decimal(str(v))

    @field_validator('codigo', mode='before')
    @classmethod
    def normalizar_codigo(cls, v):
        """Normaliza el código a mayúsculas"""
        if v is None:
            return ""
        return v.strip().upper()


class PlazaUpdate(BaseModel):
    """Modelo para actualizar una plaza existente (campos opcionales)"""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True
    )

    codigo: Optional[str] = Field(default=None, max_length=50)
    empleado_id: Optional[int] = Field(default=None)
    fecha_inicio: Optional[date] = Field(default=None)
    fecha_fin: Optional[date] = Field(default=None)
    salario_mensual: Optional[Decimal] = Field(default=None, ge=0)
    estatus: Optional[EstatusPlaza] = Field(default=None)
    notas: Optional[str] = Field(default=None, max_length=1000)

    @field_validator('salario_mensual', mode='before')
    @classmethod
    def convertir_salario(cls, v):
        """Convierte el salario a Decimal si es necesario"""
        if v is None:
            return None
        if isinstance(v, str):
            v = v.replace(',', '').replace('$', '').strip()
            if not v:
                return None
        return Decimal(str(v))

    @field_validator('codigo', mode='before')
    @classmethod
    def normalizar_codigo(cls, v):
        """Normaliza el código a mayúsculas"""
        if v is None:
            return None
        return v.strip().upper()


class PlazaResumen(BaseModel):
    """
    Modelo para listados con datos enriquecidos.

    Incluye información del contrato y categoría para evitar
    múltiples consultas al mostrar listados.
    """

    model_config = ConfigDict(
        str_strip_whitespace=True,
        from_attributes=True
    )

    # Datos de la plaza
    id: int
    contrato_categoria_id: int
    numero_plaza: int
    codigo: str = ""
    empleado_id: Optional[int] = None
    fecha_inicio: date
    fecha_fin: Optional[date] = None
    salario_mensual: Decimal
    estatus: EstatusPlaza
    notas: Optional[str] = None

    # Datos enriquecidos del contrato
    contrato_id: int = 0
    contrato_codigo: str = ""

    # Datos enriquecidos de la categoría
    categoria_puesto_id: int = 0
    categoria_clave: str = ""
    categoria_nombre: str = ""

    # Datos enriquecidos del empleado (si está ocupada)
    empleado_nombre: str = ""
    empleado_curp: str = ""

    @classmethod
    def from_plaza(
        cls,
        plaza: Plaza,
        contrato_id: int = 0,
        contrato_codigo: str = "",
        categoria_puesto_id: int = 0,
        categoria_clave: str = "",
        categoria_nombre: str = "",
        empleado_nombre: str = "",
        empleado_curp: str = ""
    ) -> 'PlazaResumen':
        """Crea un resumen desde una entidad Plaza"""
        return cls(
            id=plaza.id,
            contrato_categoria_id=plaza.contrato_categoria_id,
            numero_plaza=plaza.numero_plaza,
            codigo=plaza.codigo,
            empleado_id=plaza.empleado_id,
            fecha_inicio=plaza.fecha_inicio,
            fecha_fin=plaza.fecha_fin,
            salario_mensual=plaza.salario_mensual,
            estatus=plaza.estatus,
            notas=plaza.notas,
            contrato_id=contrato_id,
            contrato_codigo=contrato_codigo,
            categoria_puesto_id=categoria_puesto_id,
            categoria_clave=categoria_clave,
            categoria_nombre=categoria_nombre,
            empleado_nombre=empleado_nombre,
            empleado_curp=empleado_curp,
        )


class ResumenPlazasContrato(BaseModel):
    """Resumen de totales de plazas para un contrato"""

    model_config = ConfigDict(from_attributes=True)

    contrato_id: int
    total_plazas: int = 0
    plazas_vacantes: int = 0
    plazas_ocupadas: int = 0
    plazas_suspendidas: int = 0
    plazas_canceladas: int = 0
    costo_total_mensual: Decimal = Decimal('0')

    @property
    def porcentaje_ocupacion(self) -> float:
        """Calcula el porcentaje de plazas ocupadas"""
        plazas_activas = self.total_plazas - self.plazas_canceladas
        if plazas_activas == 0:
            return 0.0
        return (self.plazas_ocupadas / plazas_activas) * 100


class ResumenPlazasCategoria(BaseModel):
    """Resumen de totales de plazas para una ContratoCategoria"""

    model_config = ConfigDict(from_attributes=True)

    contrato_categoria_id: int
    categoria_clave: str = ""
    categoria_nombre: str = ""
    cantidad_minima: int = 0
    cantidad_maxima: int = 0
    total_plazas: int = 0
    plazas_vacantes: int = 0
    plazas_ocupadas: int = 0
    plazas_suspendidas: int = 0
    costo_total_mensual: Decimal = Decimal('0')

    @property
    def cumple_minimo(self) -> bool:
        """Verifica si se cumple el mínimo de plazas ocupadas"""
        return self.plazas_ocupadas >= self.cantidad_minima

    @property
    def plazas_faltantes(self) -> int:
        """Calcula cuántas plazas faltan para el mínimo"""
        faltantes = self.cantidad_minima - self.plazas_ocupadas
        return max(0, faltantes)
