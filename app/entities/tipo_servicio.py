"""
Entidades de dominio para Tipos de Servicio.

Los tipos de servicio son un catálogo global que define los tipos
de servicio que se pueden ofrecer: Jardinería, Limpieza, Mantenimiento, etc.

No dependen de empresa - todas las empresas usan el mismo catálogo.

Usa FieldConfig del módulo de validación para mantener
consistencia entre validación frontend y backend.
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator, ConfigDict

from app.core.enums import Estatus
from app.core.validation import (
    validar_con_config,
    # Configuraciones de campos
    CAMPO_CLAVE_TIPO_SERVICIO,
    CAMPO_NOMBRE_TIPO_SERVICIO,
    # Constantes para Field()
    CLAVE_TIPO_SERVICIO_PATTERN,
    CLAVE_TIPO_MIN,
    CLAVE_TIPO_MAX,
    NOMBRE_TIPO_MIN,
    NOMBRE_TIPO_MAX,
    DESCRIPCION_TIPO_MAX,
)
from app.core.error_messages import msg_entidad_ya_estado


class TipoServicio(BaseModel):
    """
    Entidad principal de Tipo de Servicio.

    Representa un tipo de servicio que las empresas pueden ofrecer.
    Es un catálogo global compartido por todas las empresas.

    Ejemplos:
        - JAR: Jardinería
        - LIM: Limpieza
        - MTO: Mantenimiento
        - ART: Personal Artístico
        - ADM: Administrativos
    """

    model_config = ConfigDict(
        use_enum_values=True,
        str_strip_whitespace=True,
        validate_assignment=True,
        from_attributes=True
    )

    # Identificación
    id: Optional[int] = None

    # Información básica
    clave: str = Field(
        min_length=CLAVE_TIPO_MIN,
        max_length=CLAVE_TIPO_MAX,
        pattern=CLAVE_TIPO_SERVICIO_PATTERN,
        description="Clave única del tipo (2-5 letras mayúsculas)"
    )
    nombre: str = Field(
        min_length=NOMBRE_TIPO_MIN,
        max_length=NOMBRE_TIPO_MAX,
        description="Nombre del tipo de servicio"
    )
    descripcion: Optional[str] = Field(
        None,
        max_length=DESCRIPCION_TIPO_MAX,
        description="Descripción detallada del tipo"
    )

    # Control de estado
    estatus: Estatus = Field(
        default=Estatus.ACTIVO,
        description="Estado actual del tipo"
    )

    # Auditoría
    fecha_creacion: Optional[datetime] = Field(
        None,
        description="Fecha de registro en el sistema"
    )
    fecha_actualizacion: Optional[datetime] = None

    # =========================================================================
    # VALIDADORES - Usan FieldConfig para consistencia con frontend
    # =========================================================================

    @field_validator('clave', mode='before')
    @classmethod
    def validar_clave(cls, v: str) -> str:
        """Valida y normaliza la clave usando FieldConfig."""
        if not v:
            return v
        v, error = validar_con_config(v, CAMPO_CLAVE_TIPO_SERVICIO)
        if error:
            raise ValueError(error)
        return v

    @field_validator('nombre', mode='before')
    @classmethod
    def validar_nombre(cls, v: str) -> str:
        """Valida y normaliza el nombre usando FieldConfig."""
        if not v:
            return v
        v, error = validar_con_config(v, CAMPO_NOMBRE_TIPO_SERVICIO)
        if error:
            raise ValueError(error)
        return v

    # Métodos de negocio
    def esta_activo(self) -> bool:
        """Verifica si el tipo está activo"""
        return self.estatus == Estatus.ACTIVO

    def puede_usarse_en_contratos(self) -> bool:
        """Verifica si el tipo puede usarse en nuevos contratos"""
        return self.esta_activo()

    def desactivar(self) -> None:
        """Desactiva el tipo de servicio"""
        if self.estatus == Estatus.INACTIVO:
            raise ValueError(msg_entidad_ya_estado("El tipo", "inactivo"))
        self.estatus = Estatus.INACTIVO

    def activar(self) -> None:
        """Activa el tipo de servicio"""
        if self.estatus == Estatus.ACTIVO:
            raise ValueError(msg_entidad_ya_estado("El tipo", "activo"))
        self.estatus = Estatus.ACTIVO

    def __str__(self) -> str:
        return f"{self.clave} - {self.nombre}"


class TipoServicioCreate(BaseModel):
    """Modelo para crear un nuevo tipo de servicio"""

    model_config = ConfigDict(
        use_enum_values=True,
        str_strip_whitespace=True,
        validate_assignment=True
    )

    clave: str = Field(min_length=CLAVE_TIPO_MIN, max_length=CLAVE_TIPO_MAX)
    nombre: str = Field(min_length=NOMBRE_TIPO_MIN, max_length=NOMBRE_TIPO_MAX)
    descripcion: Optional[str] = Field(None, max_length=DESCRIPCION_TIPO_MAX)
    estatus: Estatus = Field(default=Estatus.ACTIVO)

    @field_validator('clave', mode='before')
    @classmethod
    def validar_clave(cls, v: str) -> str:
        """Valida y normaliza la clave usando FieldConfig."""
        if not v:
            return v
        v, error = validar_con_config(v, CAMPO_CLAVE_TIPO_SERVICIO)
        if error:
            raise ValueError(error)
        return v

    @field_validator('nombre', mode='before')
    @classmethod
    def validar_nombre(cls, v: str) -> str:
        """Valida y normaliza el nombre usando FieldConfig."""
        if not v:
            return v
        v, error = validar_con_config(v, CAMPO_NOMBRE_TIPO_SERVICIO)
        if error:
            raise ValueError(error)
        return v


class TipoServicioUpdate(BaseModel):
    """Modelo para actualizar un tipo de servicio existente (campos opcionales)"""

    model_config = ConfigDict(
        use_enum_values=True,
        str_strip_whitespace=True,
        validate_assignment=True
    )

    clave: Optional[str] = Field(None, min_length=CLAVE_TIPO_MIN, max_length=CLAVE_TIPO_MAX)
    nombre: Optional[str] = Field(None, min_length=NOMBRE_TIPO_MIN, max_length=NOMBRE_TIPO_MAX)
    descripcion: Optional[str] = Field(None, max_length=DESCRIPCION_TIPO_MAX)
    estatus: Optional[Estatus] = None

    @field_validator('clave', mode='before')
    @classmethod
    def validar_clave(cls, v: Optional[str]) -> Optional[str]:
        """Valida y normaliza la clave usando FieldConfig si se proporciona."""
        if v:
            v, error = validar_con_config(v, CAMPO_CLAVE_TIPO_SERVICIO)
            if error:
                raise ValueError(error)
        return v

    @field_validator('nombre', mode='before')
    @classmethod
    def validar_nombre(cls, v: Optional[str]) -> Optional[str]:
        """Valida y normaliza el nombre usando FieldConfig si se proporciona."""
        if v:
            v, error = validar_con_config(v, CAMPO_NOMBRE_TIPO_SERVICIO)
            if error:
                raise ValueError(error)
        return v
