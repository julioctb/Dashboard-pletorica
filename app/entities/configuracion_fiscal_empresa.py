"""
Entidad de dominio para la configuración fiscal/patronal de empresas.

Relación 1:1 con empresas. Almacena los parámetros que alimentan al motor
CalculadoraCostoPatronal para el cálculo de cotizaciones.
"""
from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class ConfiguracionFiscalEmpresa(BaseModel):
    """Configuración fiscal/patronal de una empresa (1:1)."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        from_attributes=True,
    )

    id: Optional[int] = None
    empresa_id: int

    # Parámetros para CalculadoraCostoPatronal
    prima_riesgo: Decimal = Field(
        default=Decimal('0.005'),
        ge=Decimal('0.005'),
        le=Decimal('0.15'),
        description="Prima de riesgo de trabajo IMSS. Rango legal: 0.5%-15%",
    )
    factor_integracion: Optional[Decimal] = Field(
        default=None,
        ge=Decimal('1.0'),
        le=Decimal('2.0'),
        description="Factor de integración IMSS. None = cálculo automático",
    )
    dias_aguinaldo: int = Field(
        default=15,
        ge=15,
        description="Días de aguinaldo (mínimo legal: 15)",
    )
    prima_vacacional: Decimal = Field(
        default=Decimal('0.25'),
        ge=Decimal('0.25'),
        description="Prima vacacional (mínimo legal: 0.25 = 25%)",
    )
    aplicar_art_36: bool = Field(
        default=True,
        description="Si true, patrón absorbe cuota obrera IMSS (Art. 36 LSS)",
    )
    zona_frontera: bool = Field(
        default=False,
        description="True para zona fronteriza norte",
    )
    estado_isn: str = Field(
        default='Puebla',
        max_length=50,
        description="Estado para tasa ISN. Ej: 'Puebla'",
    )

    # Representante legal
    representante_legal_nombre: Optional[str] = Field(
        default=None,
        max_length=200,
    )
    representante_legal_cargo: str = Field(
        default='Representante Legal',
        max_length=100,
    )

    # Auditoría
    fecha_creacion: Optional[datetime] = None
    fecha_actualizacion: Optional[datetime] = None

    def to_config_empresa(
        self, nombre_empresa: str, estado: Optional[str] = None
    ):
        """
        Convierte a ConfiguracionEmpresa para el motor de cálculo.

        Args:
            nombre_empresa: Nombre de la empresa (requerido por ConfiguracionEmpresa).
            estado: Estado para ISN. Si None, usa self.estado_isn.

        Returns:
            ConfiguracionEmpresa lista para CalculadoraCostoPatronal.
        """
        from app.entities.costo_patronal import ConfiguracionEmpresa
        return ConfiguracionEmpresa(
            nombre=nombre_empresa,
            estado=estado or self.estado_isn,
            prima_riesgo=float(self.prima_riesgo),
            factor_integracion_fijo=(
                float(self.factor_integracion)
                if self.factor_integracion is not None
                else None
            ),
            dias_aguinaldo=self.dias_aguinaldo,
            prima_vacacional=float(self.prima_vacacional),
            zona_frontera=self.zona_frontera,
            aplicar_art_36_lss=self.aplicar_art_36,
        )


class ConfiguracionFiscalEmpresaCreate(BaseModel):
    """DTO para crear configuración fiscal."""

    model_config = ConfigDict(str_strip_whitespace=True)

    empresa_id: int
    prima_riesgo: Decimal = Field(
        default=Decimal('0.005'),
        ge=Decimal('0.005'),
        le=Decimal('0.15'),
    )
    factor_integracion: Optional[Decimal] = Field(
        default=None,
        ge=Decimal('1.0'),
        le=Decimal('2.0'),
    )
    dias_aguinaldo: int = Field(default=15, ge=15)
    prima_vacacional: Decimal = Field(default=Decimal('0.25'), ge=Decimal('0.25'))
    aplicar_art_36: bool = Field(default=True)
    zona_frontera: bool = Field(default=False)
    estado_isn: str = Field(default='Puebla', max_length=50)
    representante_legal_nombre: Optional[str] = Field(default=None, max_length=200)
    representante_legal_cargo: str = Field(default='Representante Legal', max_length=100)


class ConfiguracionFiscalEmpresaUpdate(BaseModel):
    """DTO para actualizar configuración fiscal (todos opcionales)."""

    model_config = ConfigDict(str_strip_whitespace=True)

    prima_riesgo: Optional[Decimal] = Field(
        default=None,
        ge=Decimal('0.005'),
        le=Decimal('0.15'),
    )
    factor_integracion: Optional[Decimal] = Field(
        default=None,
        ge=Decimal('1.0'),
        le=Decimal('2.0'),
    )
    dias_aguinaldo: Optional[int] = Field(default=None, ge=15)
    prima_vacacional: Optional[Decimal] = Field(default=None, ge=Decimal('0.25'))
    aplicar_art_36: Optional[bool] = None
    zona_frontera: Optional[bool] = None
    estado_isn: Optional[str] = Field(default=None, max_length=50)
    representante_legal_nombre: Optional[str] = Field(default=None, max_length=200)
    representante_legal_cargo: Optional[str] = Field(default=None, max_length=100)
