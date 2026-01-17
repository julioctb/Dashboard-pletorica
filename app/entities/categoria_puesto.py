"""
Entidades de dominio para Categorías de Puesto.

Las categorías de puesto definen los tipos de personal que puede
tener cada tipo de servicio: Jardinero A, Jardinero B, Supervisor, etc.

Cada categoría pertenece a UN tipo de servicio específico.
La clave es única DENTRO del mismo tipo de servicio.

Reutiliza FieldConfigs de tipo_servicio para clave, nombre y descripción.
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict

from app.core.enums import Estatus
from app.core.validation import (
    CAMPO_CLAVE_CATALOGO,
    CAMPO_NOMBRE_CATALOGO,
    CAMPO_DESCRIPCION_CATALOGO,
    pydantic_field,
    campo_validador,
)
from app.core.error_messages import msg_entidad_ya_estado


class CategoriaPuesto(BaseModel):
    """
    Entidad principal de Categoría de Puesto.

    Representa una categoría de personal dentro de un tipo de servicio.
    Por ejemplo, Jardinería tiene: Jardinero A, Jardinero B, Oficial A, Supervisor.

    Ejemplos de claves:
        - JARA: Jardinero A
        - JARB: Jardinero B
        - OFIA: Oficial A
        - SUP: Supervisor
    """

    model_config = ConfigDict(
        use_enum_values=True,
        str_strip_whitespace=True,
        validate_assignment=True,
        from_attributes=True
    )

    # Identificación
    id: Optional[int] = None
    tipo_servicio_id: int = Field(..., description="FK a tipo_servicio")

    # Información básica - reutilizando FieldConfigs de tipo_servicio
    clave: str = pydantic_field(CAMPO_CLAVE_CATALOGO)
    nombre: str = pydantic_field(CAMPO_NOMBRE_CATALOGO)
    descripcion: Optional[str] = pydantic_field(CAMPO_DESCRIPCION_CATALOGO)

    # Ordenamiento
    orden: int = Field(default=0, ge=0, description="Orden de visualización")

    # Control de estado
    estatus: Estatus = Field(default=Estatus.ACTIVO)

    # Auditoría
    fecha_creacion: Optional[datetime] = None
    fecha_actualizacion: Optional[datetime] = None

    # =========================================================================
    # VALIDADORES - Generados desde FieldConfig
    # =========================================================================

    validar_clave = campo_validador('clave', CAMPO_CLAVE_CATALOGO)
    validar_nombre = campo_validador('nombre', CAMPO_NOMBRE_CATALOGO)

    # =========================================================================
    # MÉTODOS DE NEGOCIO
    # =========================================================================

    def esta_activo(self) -> bool:
        """Verifica si la categoría está activa"""
        return self.estatus == Estatus.ACTIVO

    def desactivar(self) -> None:
        """Desactiva la categoría de puesto"""
        if self.estatus == Estatus.INACTIVO:
            raise ValueError(msg_entidad_ya_estado("La categoría", "inactiva"))
        self.estatus = Estatus.INACTIVO

    def activar(self) -> None:
        """Activa la categoría de puesto"""
        if self.estatus == Estatus.ACTIVO:
            raise ValueError(msg_entidad_ya_estado("La categoría", "activa"))
        self.estatus = Estatus.ACTIVO

    def __str__(self) -> str:
        return f"{self.clave} - {self.nombre}"


class CategoriaPuestoCreate(BaseModel):
    """Modelo para crear una nueva categoría de puesto"""

    model_config = ConfigDict(
        use_enum_values=True,
        str_strip_whitespace=True,
        validate_assignment=True
    )

    tipo_servicio_id: int = Field(..., description="FK a tipo_servicio")
    clave: str = pydantic_field(CAMPO_CLAVE_CATALOGO)
    nombre: str = pydantic_field(CAMPO_NOMBRE_CATALOGO)
    descripcion: Optional[str] = pydantic_field(CAMPO_DESCRIPCION_CATALOGO)
    orden: int = Field(default=0, ge=0)
    estatus: Estatus = Field(default=Estatus.ACTIVO)

    # Validadores
    validar_clave = campo_validador('clave', CAMPO_CLAVE_CATALOGO)
    validar_nombre = campo_validador('nombre', CAMPO_NOMBRE_CATALOGO)


class CategoriaPuestoUpdate(BaseModel):
    """Modelo para actualizar una categoría existente (campos opcionales)"""

    model_config = ConfigDict(
        use_enum_values=True,
        str_strip_whitespace=True,
        validate_assignment=True
    )

    tipo_servicio_id: Optional[int] = None
    clave: Optional[str] = pydantic_field(CAMPO_CLAVE_CATALOGO, default=None)
    nombre: Optional[str] = pydantic_field(CAMPO_NOMBRE_CATALOGO, default=None)
    descripcion: Optional[str] = pydantic_field(CAMPO_DESCRIPCION_CATALOGO)
    orden: Optional[int] = Field(default=None, ge=0)
    estatus: Optional[Estatus] = None

    # Validadores
    validar_clave = campo_validador('clave', CAMPO_CLAVE_CATALOGO)
    validar_nombre = campo_validador('nombre', CAMPO_NOMBRE_CATALOGO)
