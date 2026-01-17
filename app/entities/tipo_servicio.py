"""
Entidades de dominio para Tipos de Servicio.

Los tipos de servicio son un catálogo global que define los tipos
de servicio que se pueden ofrecer: Jardinería, Limpieza, Mantenimiento, etc.

No dependen de empresa - todas las empresas usan el mismo catálogo.

Usa FieldConfig y helpers para mantener consistencia entre validación
frontend y backend con mínimo código duplicado.
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

    # Información básica - usando pydantic_field()
    clave: str = pydantic_field(CAMPO_CLAVE_CATALOGO)
    nombre: str = pydantic_field(CAMPO_NOMBRE_CATALOGO)
    descripcion: Optional[str] = pydantic_field(CAMPO_DESCRIPCION_CATALOGO)

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

    clave: str = pydantic_field(CAMPO_CLAVE_CATALOGO)
    nombre: str = pydantic_field(CAMPO_NOMBRE_CATALOGO)
    descripcion: Optional[str] = pydantic_field(CAMPO_DESCRIPCION_CATALOGO)
    estatus: Estatus = Field(default=Estatus.ACTIVO)

    # Validadores
    validar_clave = campo_validador('clave', CAMPO_CLAVE_CATALOGO)
    validar_nombre = campo_validador('nombre', CAMPO_NOMBRE_CATALOGO)


class TipoServicioUpdate(BaseModel):
    """Modelo para actualizar un tipo de servicio existente (campos opcionales)"""

    model_config = ConfigDict(
        use_enum_values=True,
        str_strip_whitespace=True,
        validate_assignment=True
    )

    clave: Optional[str] = pydantic_field(CAMPO_CLAVE_CATALOGO, default=None)
    nombre: Optional[str] = pydantic_field(CAMPO_NOMBRE_CATALOGO, default=None)
    descripcion: Optional[str] = pydantic_field(CAMPO_DESCRIPCION_CATALOGO)
    estatus: Optional[Estatus] = None

    # Validadores
    validar_clave = campo_validador('clave', CAMPO_CLAVE_CATALOGO)
    validar_nombre = campo_validador('nombre', CAMPO_NOMBRE_CATALOGO)
