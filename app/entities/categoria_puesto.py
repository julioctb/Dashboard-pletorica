"""
Entidades de dominio para Categorías de Puesto.

Las categorías de puesto definen los tipos de personal que puede
tener cada tipo de servicio: Jardinero A, Jardinero B, Supervisor, etc.

Cada categoría pertenece a UN tipo de servicio específico.
La clave es única DENTRO del mismo tipo de servicio.

TODO: Completar esta entidad e integrar con FieldConfig para validación.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator, ConfigDict

from app.core.enums import Estatus
from app.core.validation import (
    CLAVE_TIPO_SERVICIO_PATTERN,
    CLAVE_TIPO_MIN,
    CLAVE_TIPO_MAX,
    NOMBRE_TIPO_MIN,
    NOMBRE_TIPO_MAX,
    DESCRIPCION_TIPO_MAX,
)


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

    TODO: Implementar validadores con FieldConfig cuando la entidad esté completa.
    """

    model_config = ConfigDict(
        use_enum_values=True,
        str_strip_whitespace=True,
        validate_assignment=True,
        from_attributes=True
    )

    # Identificación
    id: Optional[int] = None

    # Relación con tipo de servicio
    tipo_servicio_id: int = Field(
        description="ID del tipo de servicio al que pertenece"
    )

    # Información básica
    clave: str = Field(
        min_length=CLAVE_TIPO_MIN,
        max_length=CLAVE_TIPO_MAX,
        pattern=CLAVE_TIPO_SERVICIO_PATTERN,
        description="Clave única dentro del tipo (2-5 letras mayúsculas)"
    )
    nombre: str = Field(
        min_length=NOMBRE_TIPO_MIN,
        max_length=NOMBRE_TIPO_MAX,
        description="Nombre de la categoría de puesto"
    )
    descripcion: Optional[str] = Field(
        None,
        max_length=DESCRIPCION_TIPO_MAX,
        description="Descripción detallada de la categoría"
    )

    # Control de estado
    estatus: Estatus = Field(
        default=Estatus.ACTIVO,
        description="Estado actual de la categoría"
    )

    # Auditoría
    fecha_creacion: Optional[datetime] = Field(
        None,
        description="Fecha de registro en el sistema"
    )
    fecha_actualizacion: Optional[datetime] = None

    # TODO: Agregar validadores con FieldConfig
    # TODO: Agregar métodos de negocio

    def __str__(self) -> str:
        return f"{self.clave} - {self.nombre}"
