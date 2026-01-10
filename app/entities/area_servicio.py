"""
Entidades de dominio para Áreas de Servicio.

Las áreas de servicio son un catálogo global que define los tipos
de servicio que se pueden ofrecer: Jardinería, Limpieza, Mantenimiento, etc.

No dependen de empresa - todas las empresas usan el mismo catálogo.
"""
import re
from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field, field_validator, ConfigDict


# Constantes de validación
CLAVE_PATTERN = r'^[A-Z]{2,5}$'


class EstatusAreaServicio(str, Enum):
    """Estados posibles de un área de servicio"""
    ACTIVO = 'ACTIVO'
    INACTIVO = 'INACTIVO'


class AreaServicio(BaseModel):
    """
    Entidad principal de Área de Servicio.
    
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
        min_length=2,
        max_length=5,
        pattern=CLAVE_PATTERN,
        description="Clave única del área (2-5 letras mayúsculas)"
    )
    nombre: str = Field(
        min_length=2,
        max_length=50,
        description="Nombre del área de servicio"
    )
    descripcion: Optional[str] = Field(
        None,
        max_length=500,
        description="Descripción detallada del área"
    )

    # Control de estado
    estatus: EstatusAreaServicio = Field(
        default=EstatusAreaServicio.ACTIVO,
        description="Estado actual del área"
    )

    # Auditoría
    fecha_creacion: Optional[datetime] = Field(
        None,
        description="Fecha de registro en el sistema"
    )
    fecha_actualizacion: Optional[datetime] = None

    # Validadores
    @field_validator('clave')
    @classmethod
    def validar_clave(cls, v: str) -> str:
        """Valida y normaliza la clave del área"""
        if v:
            v = v.upper().strip()
            if not re.match(CLAVE_PATTERN, v):
                if len(v) < 2 or len(v) > 5:
                    raise ValueError(f'La clave debe tener entre 2 y 5 caracteres (tiene {len(v)})')
                if not v.isalpha():
                    raise ValueError('La clave solo puede contener letras')
                raise ValueError('La clave solo puede contener letras mayúsculas')
        return v

    @field_validator('nombre')
    @classmethod
    def validar_nombre(cls, v: str) -> str:
        """Valida y normaliza el nombre"""
        if v:
            v = v.strip()
            # Convertir a formato título
            v = v.upper()
        return v

    # Métodos de negocio
    def esta_activo(self) -> bool:
        """Verifica si el área está activa"""
        return self.estatus == EstatusAreaServicio.ACTIVO

    def puede_usarse_en_contratos(self) -> bool:
        """Verifica si el área puede usarse en nuevos contratos"""
        return self.esta_activo()

    def desactivar(self) -> None:
        """Desactiva el área de servicio"""
        if self.estatus == EstatusAreaServicio.INACTIVO:
            raise ValueError("El área ya está inactiva")
        self.estatus = EstatusAreaServicio.INACTIVO

    def activar(self) -> None:
        """Activa el área de servicio"""
        if self.estatus == EstatusAreaServicio.ACTIVO:
            raise ValueError("El área ya está activa")
        self.estatus = EstatusAreaServicio.ACTIVO

    def __str__(self) -> str:
        return f"{self.clave} - {self.nombre}"


class AreaServicioCreate(BaseModel):
    """Modelo para crear una nueva área de servicio"""

    model_config = ConfigDict(
        use_enum_values=True,
        str_strip_whitespace=True,
        validate_assignment=True
    )

    clave: str = Field(min_length=2, max_length=5)
    nombre: str = Field(min_length=2, max_length=50)
    descripcion: Optional[str] = Field(None, max_length=500)
    estatus: EstatusAreaServicio = Field(default=EstatusAreaServicio.ACTIVO)

    @field_validator('clave')
    @classmethod
    def validar_clave(cls, v: str) -> str:
        """Valida y normaliza la clave"""
        if v:
            v = v.upper().strip()
            if not re.match(CLAVE_PATTERN, v):
                raise ValueError('La clave debe tener entre 2 y 5 letras mayúsculas')
        return v

    @field_validator('nombre')
    @classmethod
    def validar_nombre(cls, v: str) -> str:
        """Normaliza el nombre a mayúsculas"""
        if v:
            v = v.strip().upper()
        return v


class AreaServicioUpdate(BaseModel):
    """Modelo para actualizar un área de servicio existente (campos opcionales)"""

    model_config = ConfigDict(
        use_enum_values=True,
        str_strip_whitespace=True,
        validate_assignment=True
    )

    clave: Optional[str] = Field(None, min_length=2, max_length=5)
    nombre: Optional[str] = Field(None, min_length=2, max_length=50)
    descripcion: Optional[str] = Field(None, max_length=500)
    estatus: Optional[EstatusAreaServicio] = None

    @field_validator('clave')
    @classmethod
    def validar_clave(cls, v: Optional[str]) -> Optional[str]:
        """Valida y normaliza la clave si se proporciona"""
        if v:
            v = v.upper().strip()
            if not re.match(CLAVE_PATTERN, v):
                raise ValueError('La clave debe tener entre 2 y 5 letras mayúsculas')
        return v

    @field_validator('nombre')
    @classmethod
    def validar_nombre(cls, v: Optional[str]) -> Optional[str]:
        """Normaliza el nombre a mayúsculas si se proporciona"""
        if v:
            v = v.strip().upper()
        return v