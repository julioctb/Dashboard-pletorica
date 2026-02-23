"""
Entidades de dominio para la relación Usuario-Empresa.

Esta entidad representa la relación muchos-a-muchos entre usuarios
y empresas. Un usuario puede tener acceso a múltiples empresas,
y una empresa puede tener múltiples usuarios con acceso.

El campo es_principal indica cuál empresa se muestra por defecto
al usuario cuando inicia sesión (solo una puede ser principal).
"""
from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict

from app.core.enums import RolEmpresa


# =============================================================================
# ENTIDAD PRINCIPAL
# =============================================================================

class UserCompany(BaseModel):
    """
    Entidad que representa la relación entre un usuario y una empresa.

    Esta relación permite:
    - Que un usuario (ej: admin BUAP) acceda a múltiples empresas
    - Que una empresa tenga múltiples usuarios con acceso
    - Definir una empresa "principal" que se carga por defecto al login

    Atributos:
        id: Identificador único de la relación
        user_id: UUID del usuario (FK a user_profiles)
        empresa_id: ID de la empresa (FK a empresas)
        es_principal: Si es la empresa por defecto del usuario
        fecha_creacion: Cuándo se creó esta asociación
    """

    model_config = ConfigDict(
        use_enum_values=True,
        str_strip_whitespace=True,
        validate_assignment=True,
        from_attributes=True,
    )

    # Identificación
    id: Optional[int] = None

    # Relaciones
    user_id: UUID = Field(..., description="UUID del usuario")
    empresa_id: int = Field(..., description="ID de la empresa")

    # Configuración
    es_principal: bool = Field(
        default=False,
        description="Si es la empresa por defecto al iniciar sesión"
    )

    # Rol en esta empresa
    rol_empresa: RolEmpresa = Field(
        default=RolEmpresa.LECTURA,
        description="Rol del usuario en esta empresa específica"
    )

    # Auditoría
    fecha_creacion: Optional[datetime] = None

    # =========================================================================
    # MÉTODOS DE NEGOCIO
    # =========================================================================

    def marcar_como_principal(self) -> None:
        """Marca esta relación como la empresa principal del usuario."""
        self.es_principal = True

    def quitar_principal(self) -> None:
        """Quita la marca de empresa principal."""
        self.es_principal = False

    def __str__(self) -> str:
        principal = " (principal)" if self.es_principal else ""
        return f"Usuario {self.user_id} → Empresa {self.empresa_id}{principal}"


# =============================================================================
# MODELO PARA CREACIÓN
# =============================================================================

class UserCompanyCreate(BaseModel):
    """
    Modelo para asignar una empresa a un usuario.

    Se usa cuando un admin quiere dar acceso a un usuario
    para ver/gestionar datos de una empresa específica.

    Ejemplo:
        asignacion = UserCompanyCreate(
            user_id=uuid_del_usuario,
            empresa_id=1,
            es_principal=True
        )
    """

    model_config = ConfigDict(
        use_enum_values=True,
        str_strip_whitespace=True,
        validate_assignment=True,
    )

    user_id: UUID = Field(..., description="UUID del usuario a asignar")
    empresa_id: int = Field(..., gt=0, description="ID de la empresa")
    es_principal: bool = Field(
        default=False,
        description="Marcar como empresa principal del usuario"
    )
    rol_empresa: RolEmpresa = Field(
        default=RolEmpresa.LECTURA,
        description="Rol del usuario en esta empresa"
    )


# =============================================================================
# MODELO RESUMIDO CON DATOS ENRIQUECIDOS
# =============================================================================

class UserCompanyResumen(BaseModel):
    """
    Modelo con datos enriquecidos de la relación usuario-empresa.

    Incluye datos de la empresa para mostrar en listados sin
    necesidad de queries adicionales.
    """

    model_config = ConfigDict(
        use_enum_values=True,
        from_attributes=True,
    )

    id: int
    user_id: UUID
    empresa_id: int
    es_principal: bool
    rol_empresa: RolEmpresa = Field(default=RolEmpresa.LECTURA)
    fecha_creacion: Optional[datetime] = None

    # Datos enriquecidos de la empresa
    empresa_nombre: Optional[str] = None
    empresa_rfc: Optional[str] = None
    empresa_tipo: Optional[str] = None
    empresa_activa: bool = True

    def __str__(self) -> str:
        nombre = self.empresa_nombre or f"Empresa {self.empresa_id}"
        principal = " ★" if self.es_principal else ""
        return f"{nombre}{principal}"
