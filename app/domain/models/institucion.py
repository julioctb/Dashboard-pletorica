"""
Entidades de dominio para Instituciones.

Las instituciones representan clientes institucionales (BUAP, Gobierno, etc.)
que supervisan a una o más empresas proveedoras.

Modelo de acceso:
    - Usuarios con rol='institucion' tienen user_profiles.institucion_id
    - La tabla instituciones_empresas define qué empresas supervisa cada institución
    - Los usuarios institucionales NO usan user_companies
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


# =============================================================================
# ENTIDAD PRINCIPAL
# =============================================================================

class Institucion(BaseModel):
    """
    Entidad principal de Institución.

    Representa una organización cliente que supervisa empresas proveedoras.
    Ejemplo: BUAP supervisa todas las empresas que le proveen servicios.
    """

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        from_attributes=True,
    )

    id: int
    nombre: str = Field(
        ...,
        min_length=2,
        max_length=200,
        description="Nombre completo de la institución"
    )
    codigo: str = Field(
        ...,
        min_length=2,
        max_length=20,
        description="Código corto único (ej: BUAP, GOB-PUE)"
    )
    activo: bool = Field(default=True)

    # Auditoría
    fecha_creacion: Optional[datetime] = None
    fecha_actualizacion: Optional[datetime] = None

    def esta_activa(self) -> bool:
        """Verifica si la institución está activa."""
        return self.activo

    def __str__(self) -> str:
        estado = "activa" if self.activo else "inactiva"
        return f"{self.nombre} ({self.codigo}) - {estado}"


# =============================================================================
# MODELO PARA CREACIÓN
# =============================================================================

class InstitucionCreate(BaseModel):
    """Modelo para crear una nueva institución."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
    )

    nombre: str = Field(
        ...,
        min_length=2,
        max_length=200,
    )
    codigo: str = Field(
        ...,
        min_length=2,
        max_length=20,
    )


class InstitucionUpdate(BaseModel):
    """Modelo para actualizar una institución existente."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
    )

    nombre: Optional[str] = Field(
        default=None,
        min_length=2,
        max_length=200,
    )
    codigo: Optional[str] = Field(
        default=None,
        min_length=2,
        max_length=20,
    )


# =============================================================================
# MODELO RESUMIDO PARA LISTADOS
# =============================================================================

class InstitucionResumen(BaseModel):
    """Modelo resumido con cantidad de empresas supervisadas."""

    model_config = ConfigDict(
        from_attributes=True,
    )

    id: int
    nombre: str
    codigo: str
    activo: bool
    cantidad_empresas: int = 0

    def __str__(self) -> str:
        return f"{self.nombre} ({self.codigo}) - {self.cantidad_empresas} empresas"


# =============================================================================
# ENTIDAD JOIN: INSTITUCIÓN-EMPRESA
# =============================================================================

class InstitucionEmpresa(BaseModel):
    """
    Relación entre una institución y una empresa que supervisa.

    Este modelo se usa para:
    - Asignar empresas a una institución
    - Listar qué empresas supervisa una institución
    - Determinar el acceso de usuarios institucionales
    """

    model_config = ConfigDict(
        str_strip_whitespace=True,
        from_attributes=True,
    )

    id: Optional[int] = None
    institucion_id: int = Field(..., description="ID de la institución")
    empresa_id: int = Field(..., description="ID de la empresa supervisada")
    fecha_creacion: Optional[datetime] = None

    # Datos enriquecidos (se llenan con JOIN)
    empresa_nombre: Optional[str] = None
    empresa_rfc: Optional[str] = None
    institucion_nombre: Optional[str] = None

    def __str__(self) -> str:
        nombre = self.empresa_nombre or f"Empresa {self.empresa_id}"
        return f"Institución {self.institucion_id} → {nombre}"
