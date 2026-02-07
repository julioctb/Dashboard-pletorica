"""
Entidades de dominio para Contactos BUAP.

Los contactos BUAP son personas asociadas a una sede:
directores, coordinadores, administrativos, etc.
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict

from app.core.enums import Estatus, NivelContacto
from app.core.validation import (
    CAMPO_NOMBRE_CONTACTO,
    CAMPO_CARGO_CONTACTO,
    CAMPO_EXTENSION_CONTACTO,
    CAMPO_EMAIL,
    CAMPO_TELEFONO,
    pydantic_field,
    campo_validador,
    EMAIL_MAX,
    TELEFONO_DIGITOS,
)


class ContactoBuap(BaseModel):
    """
    Entidad principal de Contacto BUAP.

    Representa una persona de contacto dentro de una sede BUAP.
    """

    model_config = ConfigDict(
        use_enum_values=True,
        str_strip_whitespace=True,
        validate_assignment=True,
        from_attributes=True,
    )

    # Identificación
    id: Optional[int] = None
    sede_id: int = Field(...)

    # Datos personales
    nombre: str = pydantic_field(CAMPO_NOMBRE_CONTACTO)
    cargo: Optional[str] = pydantic_field(CAMPO_CARGO_CONTACTO)
    nivel: Optional[NivelContacto] = None

    # Contacto
    telefono: Optional[str] = Field(default=None, max_length=TELEFONO_DIGITOS)
    extension: Optional[str] = pydantic_field(CAMPO_EXTENSION_CONTACTO)
    email: Optional[str] = Field(default=None, max_length=EMAIL_MAX)
    es_principal: bool = Field(default=False)

    # Extra
    notas: Optional[str] = None
    estatus: Estatus = Field(default=Estatus.ACTIVO)

    # Auditoría
    fecha_creacion: Optional[datetime] = None
    fecha_actualizacion: Optional[datetime] = None

    # =========================================================================
    # VALIDADORES
    # =========================================================================

    validar_nombre = campo_validador('nombre', CAMPO_NOMBRE_CONTACTO)
    validar_email = campo_validador('email', CAMPO_EMAIL)
    validar_telefono = campo_validador('telefono', CAMPO_TELEFONO)

    # =========================================================================
    # MÉTODOS DE NEGOCIO
    # =========================================================================

    def esta_activo(self) -> bool:
        return self.estatus == Estatus.ACTIVO

    def nombre_con_cargo(self) -> str:
        if self.cargo:
            return f"{self.nombre} ({self.cargo})"
        return self.nombre

    def __str__(self) -> str:
        return self.nombre_con_cargo()


class ContactoBuapCreate(BaseModel):
    """Modelo para crear un nuevo contacto BUAP."""

    model_config = ConfigDict(
        use_enum_values=True,
        str_strip_whitespace=True,
        validate_assignment=True,
    )

    sede_id: int = Field(...)
    nombre: str = pydantic_field(CAMPO_NOMBRE_CONTACTO)
    cargo: Optional[str] = pydantic_field(CAMPO_CARGO_CONTACTO)
    nivel: Optional[NivelContacto] = None
    telefono: Optional[str] = Field(default=None, max_length=TELEFONO_DIGITOS)
    extension: Optional[str] = pydantic_field(CAMPO_EXTENSION_CONTACTO)
    email: Optional[str] = Field(default=None, max_length=EMAIL_MAX)
    es_principal: bool = Field(default=False)
    notas: Optional[str] = None
    estatus: Estatus = Field(default=Estatus.ACTIVO)

    # Validadores
    validar_nombre = campo_validador('nombre', CAMPO_NOMBRE_CONTACTO)
    validar_email = campo_validador('email', CAMPO_EMAIL)
    validar_telefono = campo_validador('telefono', CAMPO_TELEFONO)


class ContactoBuapUpdate(BaseModel):
    """Modelo para actualizar un contacto BUAP existente (campos opcionales)."""

    model_config = ConfigDict(
        use_enum_values=True,
        str_strip_whitespace=True,
        validate_assignment=True,
    )

    sede_id: Optional[int] = None
    nombre: Optional[str] = pydantic_field(CAMPO_NOMBRE_CONTACTO, default=None)
    cargo: Optional[str] = pydantic_field(CAMPO_CARGO_CONTACTO)
    nivel: Optional[NivelContacto] = None
    telefono: Optional[str] = Field(default=None, max_length=TELEFONO_DIGITOS)
    extension: Optional[str] = pydantic_field(CAMPO_EXTENSION_CONTACTO)
    email: Optional[str] = Field(default=None, max_length=EMAIL_MAX)
    es_principal: Optional[bool] = None
    notas: Optional[str] = None
    estatus: Optional[Estatus] = None

    # Validadores
    validar_nombre = campo_validador('nombre', CAMPO_NOMBRE_CONTACTO)
    validar_email = campo_validador('email', CAMPO_EMAIL)
    validar_telefono = campo_validador('telefono', CAMPO_TELEFONO)
