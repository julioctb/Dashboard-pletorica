"""
Entidades de dominio para el catálogo de conceptos de nómina.

Representan los registros en BD (configuración por empresa),
NO las reglas legales (esas viven en CatalogoConceptosNomina).
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict


class ConceptoNomina(BaseModel):
    """
    Concepto de nómina en BD (tabla conceptos_nomina).

    Sincronizado desde CatalogoConceptosNomina (Python).
    Los campos fiscales son de solo lectura — se actualizan
    solo por sincronización, no por el usuario.
    """
    model_config = ConfigDict(
        use_enum_values=True,
        str_strip_whitespace=True,
        from_attributes=True,
    )

    id: Optional[int] = None
    clave: str = Field(..., max_length=30, description="Clave interna única")
    nombre: str = Field(..., max_length=100, description="Nombre legal/oficial")
    descripcion: str = Field(default="", max_length=500)

    # Clasificación
    tipo: str = Field(..., description="PERCEPCION / DEDUCCION / OTRO_PAGO")
    clave_sat: str = Field(..., max_length=10, description="Clave del catálogo SAT")
    nombre_sat: str = Field(default="", max_length=150)
    categoria: str = Field(default="OTROS", max_length=30)

    # Fiscal
    tratamiento_isr: str = Field(default="GRAVABLE")
    integra_sbc: bool = Field(default=True)

    # Operación
    origen_captura: str = Field(default="SISTEMA")
    es_obligatorio: bool = Field(default=False)
    es_legal: bool = Field(default=True, description="True = viene de ley, False = custom empresa")
    orden_default: int = Field(default=0)
    activo: bool = Field(default=True)

    # Auditoría
    fecha_creacion: Optional[datetime] = None
    fecha_actualizacion: Optional[datetime] = None


class ConceptoNominaCreate(BaseModel):
    """DTO para crear un concepto (solo conceptos custom de empresa)."""
    model_config = ConfigDict(str_strip_whitespace=True)

    clave: str = Field(..., max_length=30)
    nombre: str = Field(..., max_length=100)
    descripcion: str = Field(default="", max_length=500)
    tipo: str
    clave_sat: str = Field(..., max_length=10)
    nombre_sat: str = Field(default="", max_length=150)
    categoria: str = Field(default="OTROS")
    tratamiento_isr: str = Field(default="GRAVABLE")
    integra_sbc: bool = Field(default=True)
    origen_captura: str = Field(default="RRHH")
    es_obligatorio: bool = Field(default=False)
    es_legal: bool = Field(default=False)
    orden_default: int = Field(default=99)


class ConceptoNominaResumen(BaseModel):
    """Resumen ligero para listados en UI."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    clave: str
    nombre: str
    tipo: str
    clave_sat: str
    categoria: str
    origen_captura: str
    es_obligatorio: bool
    es_legal: bool
    activo: bool


class ConceptoNominaEmpresa(BaseModel):
    """
    Configuración de un concepto para una empresa específica.

    Tabla conceptos_nomina_empresa: relación empresa - concepto.
    """
    model_config = ConfigDict(
        use_enum_values=True,
        str_strip_whitespace=True,
        from_attributes=True,
    )

    id: Optional[int] = None
    empresa_id: int
    concepto_id: int
    activo: bool = Field(default=True)
    nombre_personalizado: Optional[str] = Field(None, max_length=100)
    orden_recibo: int = Field(default=0)
    fecha_creacion: Optional[datetime] = None
    fecha_actualizacion: Optional[datetime] = None


class ConceptoNominaEmpresaCreate(BaseModel):
    """DTO para activar un concepto en una empresa."""
    model_config = ConfigDict(str_strip_whitespace=True)

    empresa_id: int
    concepto_id: int
    activo: bool = Field(default=True)
    nombre_personalizado: Optional[str] = Field(None, max_length=100)
    orden_recibo: int = Field(default=0)


class ConceptoNominaEmpresaResumen(BaseModel):
    """Resumen con datos del concepto para UI."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    empresa_id: int
    concepto_id: int
    activo: bool
    nombre_personalizado: Optional[str] = None
    orden_recibo: int

    # Datos del concepto (JOIN)
    concepto_clave: str = ""
    concepto_nombre: str = ""
    concepto_tipo: str = ""
    concepto_clave_sat: str = ""
    concepto_categoria: str = ""
    concepto_es_legal: bool = True
