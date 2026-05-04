"""
Entidades de dominio para la relación Contrato-Categoría de Puesto.

Esta es una tabla intermedia que especifica las cantidades mínimas y máximas
de personal requerido por categoría en cada contrato.

Ejemplo:
    Contrato MAN-JAR-25001 tiene:
        - Jardinero A (JARA): mínimo 50, máximo 70
        - Jardinero B (JARB): mínimo 10, máximo 15
        - Supervisor (SUP): mínimo 3, máximo 5
"""
from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict, field_validator, model_validator

from app.core.validation.decimal_converters import convertir_a_decimal_opcional
from app.domain.enums import TipoSueldo


class ContratoCategoria(BaseModel):
    """
    Entidad principal que relaciona un Contrato con una Categoría de Puesto.

    Define las cantidades mínimas y máximas de personal requerido
    por categoría en cada contrato.
    """

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        from_attributes=True
    )

    # Identificación
    id: Optional[int] = None
    contrato_id: int = Field(..., description="FK a contratos")
    categoria_puesto_id: int = Field(..., description="FK a categorias_puesto")

    # Cantidades de personal
    cantidad_minima: int = Field(
        ...,
        ge=0,
        description="Cantidad mínima de personal comprometida"
    )
    cantidad_maxima: int = Field(
        ...,
        ge=0,
        description="Cantidad máxima de personal autorizada"
    )

    # Costos (opcional)
    costo_unitario: Optional[Decimal] = Field(
        default=None,
        ge=0,
        decimal_places=2,
        description="Costo por persona/mes (bruto operativo). Uso legado/interno."
    )
    costo_contractual: Optional[Decimal] = Field(
        default=None,
        ge=0,
        decimal_places=2,
        description=(
            "Monto mensual que la empresa cobra al cliente por persona. "
            "Se usa para calcular el margen frente a costo empresa."
        ),
    )
    sueldo_base: Optional[Decimal] = Field(
        default=None,
        ge=0,
        decimal_places=2,
        description="Sueldo capturado por el usuario (bruto o neto segun tipo_sueldo)",
    )
    tipo_sueldo: TipoSueldo = Field(
        default=TipoSueldo.BRUTO,
        description="Indica si el sueldo_base fue capturado como bruto o neto",
    )
    nombre: Optional[str] = Field(
        default=None,
        max_length=120,
        description="Nombre visible de la categoria dentro del contrato",
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

    @model_validator(mode='after')
    def validar_cantidades(self) -> 'ContratoCategoria':
        """Valida min <= max. cantidad_maxima = 0 significa contrato abierto."""
        if self.cantidad_maxima > 0 and self.cantidad_maxima < self.cantidad_minima:
            raise ValueError(
                f"La cantidad máxima ({self.cantidad_maxima}) debe ser mayor o igual "
                f"a la cantidad mínima ({self.cantidad_minima})"
            )
        return self

    @field_validator('costo_unitario', mode='before')
    @classmethod
    def convertir_costo(cls, v):
        """Convierte el costo a Decimal si es necesario"""
        return convertir_a_decimal_opcional(v)

    @field_validator('costo_contractual', mode='before')
    @classmethod
    def convertir_costo_contractual(cls, v):
        return convertir_a_decimal_opcional(v)

    @field_validator('sueldo_base', mode='before')
    @classmethod
    def convertir_sueldo_base(cls, v):
        """Convierte el sueldo base a Decimal si es necesario."""
        return convertir_a_decimal_opcional(v)

    # =========================================================================
    # MÉTODOS DE NEGOCIO
    # =========================================================================

    def calcular_costo_minimo(self) -> Optional[Decimal]:
        """Calcula el costo mínimo mensual (cantidad_minima * costo_unitario)"""
        if self.costo_unitario is None:
            return None
        return self.cantidad_minima * self.costo_unitario

    def calcular_costo_maximo(self) -> Optional[Decimal]:
        """Calcula el costo máximo mensual (cantidad_maxima * costo_unitario)"""
        if self.costo_unitario is None:
            return None
        return self.cantidad_maxima * self.costo_unitario

    def __str__(self) -> str:
        return f"ContratoCategoria(contrato={self.contrato_id}, categoria={self.categoria_puesto_id}, min={self.cantidad_minima}, max={self.cantidad_maxima})"


class ContratoCategoriaCreate(BaseModel):
    """Modelo para crear una nueva asignación de categoría a contrato"""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True
    )

    contrato_id: int = Field(..., description="FK a contratos")
    categoria_puesto_id: int = Field(..., description="FK a categorias_puesto")
    cantidad_minima: int = Field(..., ge=0)
    cantidad_maxima: int = Field(..., ge=0)
    costo_unitario: Optional[Decimal] = Field(default=None, ge=0)
    costo_contractual: Optional[Decimal] = Field(default=None, ge=0)
    sueldo_base: Optional[Decimal] = Field(default=None, ge=0)
    tipo_sueldo: TipoSueldo = Field(default=TipoSueldo.BRUTO)
    nombre: Optional[str] = Field(default=None, max_length=120)
    notas: Optional[str] = Field(default=None, max_length=1000)

    @model_validator(mode='after')
    def validar_cantidades(self) -> 'ContratoCategoriaCreate':
        """Valida min <= max. cantidad_maxima = 0 significa contrato abierto."""
        if self.cantidad_maxima > 0 and self.cantidad_maxima < self.cantidad_minima:
            raise ValueError(
                f"La cantidad máxima ({self.cantidad_maxima}) debe ser mayor o igual "
                f"a la cantidad mínima ({self.cantidad_minima})"
            )
        return self

    @field_validator('costo_unitario', mode='before')
    @classmethod
    def convertir_costo(cls, v):
        """Convierte el costo a Decimal si es necesario"""
        return convertir_a_decimal_opcional(v)

    @field_validator('costo_contractual', mode='before')
    @classmethod
    def convertir_costo_contractual(cls, v):
        return convertir_a_decimal_opcional(v)

    @field_validator('sueldo_base', mode='before')
    @classmethod
    def convertir_sueldo_base(cls, v):
        """Convierte el sueldo base a Decimal si es necesario."""
        return convertir_a_decimal_opcional(v)


class ContratoCategoriaUpdate(BaseModel):
    """Modelo para actualizar una asignación existente (campos opcionales)"""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True
    )

    cantidad_minima: Optional[int] = Field(default=None, ge=0)
    cantidad_maxima: Optional[int] = Field(default=None, ge=0)
    costo_unitario: Optional[Decimal] = Field(default=None, ge=0)
    costo_contractual: Optional[Decimal] = Field(default=None, ge=0)
    sueldo_base: Optional[Decimal] = Field(default=None, ge=0)
    tipo_sueldo: Optional[TipoSueldo] = Field(default=None)
    nombre: Optional[str] = Field(default=None, max_length=120)
    notas: Optional[str] = Field(default=None, max_length=1000)

    @field_validator('costo_unitario', mode='before')
    @classmethod
    def convertir_costo(cls, v):
        """Convierte el costo a Decimal si es necesario"""
        return convertir_a_decimal_opcional(v)

    @field_validator('costo_contractual', mode='before')
    @classmethod
    def convertir_costo_contractual(cls, v):
        return convertir_a_decimal_opcional(v)

    @field_validator('sueldo_base', mode='before')
    @classmethod
    def convertir_sueldo_base(cls, v):
        """Convierte el sueldo base a Decimal si es necesario."""
        return convertir_a_decimal_opcional(v)


class ContratoCategoriaResumen(BaseModel):
    """
    Modelo para listados con datos enriquecidos de la categoría.

    Incluye información de la categoría de puesto para evitar
    múltiples consultas al mostrar listados.
    """

    model_config = ConfigDict(
        str_strip_whitespace=True,
        from_attributes=True
    )

    # Datos de la relación
    id: int
    contrato_id: int
    categoria_puesto_id: int
    cantidad_minima: int
    cantidad_maxima: int
    costo_unitario: Optional[Decimal] = None
    costo_contractual: Optional[Decimal] = None
    sueldo_base: Optional[Decimal] = None
    tipo_sueldo: TipoSueldo = TipoSueldo.BRUTO
    nombre: Optional[str] = None
    notas: Optional[str] = None

    # Datos de la categoría (enriquecidos)
    categoria_clave: str = ""
    categoria_nombre: str = ""

    # Calculados
    costo_minimo: Optional[Decimal] = None
    costo_maximo: Optional[Decimal] = None

    @classmethod
    def from_contrato_categoria(
        cls,
        cc: ContratoCategoria,
        categoria_clave: str = "",
        categoria_nombre: str = ""
    ) -> 'ContratoCategoriaResumen':
        """Crea un resumen desde una entidad ContratoCategoria"""
        return cls(
            id=cc.id,
            contrato_id=cc.contrato_id,
            categoria_puesto_id=cc.categoria_puesto_id,
            cantidad_minima=cc.cantidad_minima,
            cantidad_maxima=cc.cantidad_maxima,
            costo_unitario=cc.costo_unitario,
            costo_contractual=cc.costo_contractual,
            sueldo_base=cc.sueldo_base,
            tipo_sueldo=cc.tipo_sueldo,
            nombre=cc.nombre,
            notas=cc.notas,
            categoria_clave=categoria_clave,
            categoria_nombre=categoria_nombre,
            costo_minimo=cc.calcular_costo_minimo(),
            costo_maximo=cc.calcular_costo_maximo(),
        )


class ResumenPersonalContrato(BaseModel):
    """Resumen de totales de personal para un contrato"""

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

    contrato_id: int
    cantidad_categorias: int = 0
    total_minimo: int = 0
    total_maximo: int = 0
    costo_minimo_total: Optional[Decimal] = None
    costo_maximo_total: Optional[Decimal] = None
