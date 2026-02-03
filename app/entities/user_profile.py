"""
Entidades de dominio para Perfiles de Usuario.

Los perfiles de usuario extienden la tabla auth.users de Supabase
con datos específicos de la aplicación: rol, nombre, teléfono, etc.

El ID es un UUID que viene directamente de Supabase Auth, estableciendo
una relación 1:1 entre auth.users y user_profiles.

Roles:
    - admin: Personal de BUAP con acceso completo al sistema
    - client: Usuario de empresa proveedora con acceso limitado a sus empresas
"""
from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field, field_validator, ConfigDict

import re

from app.core.enums import RolUsuario
from app.core.validation.constants import (
    TELEFONO_DIGITOS,
    EMAIL_PATTERN,
    NOMBRE_COMPLETO_MIN,
    NOMBRE_COMPLETO_MAX,
    PASSWORD_MIN,
)


# =============================================================================
# ENTIDAD PRINCIPAL
# =============================================================================

class UserProfile(BaseModel):
    """
    Entidad principal de Perfil de Usuario.

    Extiende auth.users de Supabase con datos específicos de la aplicación.
    El ID es el mismo UUID de auth.users (relación 1:1).

    Atributos:
        id: UUID del usuario en Supabase Auth
        rol: Rol del usuario (admin o client)
        nombre_completo: Nombre para mostrar
        telefono: Teléfono de contacto (10 dígitos, formato mexicano)
        activo: Si el usuario puede acceder al sistema
        ultimo_acceso: Timestamp del último login exitoso
    """

    model_config = ConfigDict(
        use_enum_values=True,
        str_strip_whitespace=True,
        validate_assignment=True,
        from_attributes=True,
    )

    # Identificación (UUID de Supabase Auth)
    id: UUID

    # Rol en el sistema
    rol: RolUsuario = Field(default=RolUsuario.CLIENT)

    # Datos personales
    nombre_completo: str = Field(
        ...,
        min_length=NOMBRE_COMPLETO_MIN,
        max_length=NOMBRE_COMPLETO_MAX,
        description="Nombre completo del usuario"
    )

    telefono: Optional[str] = Field(
        default=None,
        min_length=TELEFONO_DIGITOS,
        max_length=TELEFONO_DIGITOS,
        pattern=r'^\d{10}$',
        description="Teléfono a 10 dígitos"
    )

    # Estado
    activo: bool = Field(default=True)
    ultimo_acceso: Optional[datetime] = None

    # Auditoría
    fecha_creacion: Optional[datetime] = None
    fecha_actualizacion: Optional[datetime] = None

    # =========================================================================
    # VALIDADORES
    # =========================================================================

    @field_validator('nombre_completo')
    @classmethod
    def validar_nombre_completo(cls, v: str) -> str:
        """Normaliza el nombre: strip y título"""
        if v:
            # Capitalizar cada palabra respetando preposiciones comunes
            return v.strip().title()
        return v

    @field_validator('telefono')
    @classmethod
    def validar_telefono(cls, v: Optional[str]) -> Optional[str]:
        """Valida que el teléfono tenga exactamente 10 dígitos"""
        if v is None:
            return None
        # Eliminar cualquier caracter no numérico
        digitos = ''.join(c for c in v if c.isdigit())
        if len(digitos) != TELEFONO_DIGITOS:
            raise ValueError(f'El teléfono debe tener exactamente {TELEFONO_DIGITOS} dígitos')
        return digitos

    # =========================================================================
    # MÉTODOS DE NEGOCIO
    # =========================================================================

    def esta_activo(self) -> bool:
        """Verifica si el usuario está activo en el sistema."""
        return self.activo

    def es_admin(self) -> bool:
        """Verifica si el usuario tiene rol de administrador."""
        return self.rol == RolUsuario.ADMIN or (
            isinstance(self.rol, str) and self.rol == 'admin'
        )

    def puede_iniciar_sesion(self) -> bool:
        """Verifica si el usuario puede iniciar sesión."""
        return self.activo

    def registrar_acceso(self) -> None:
        """Actualiza el timestamp de último acceso."""
        self.ultimo_acceso = datetime.now()

    def desactivar(self) -> None:
        """Desactiva el usuario (soft delete)."""
        if not self.activo:
            raise ValueError("El usuario ya está desactivado")
        self.activo = False

    def activar(self) -> None:
        """Reactiva un usuario desactivado."""
        if self.activo:
            raise ValueError("El usuario ya está activo")
        self.activo = True

    def __str__(self) -> str:
        estado = "activo" if self.activo else "inactivo"
        return f"{self.nombre_completo} ({self.rol}) - {estado}"


# =============================================================================
# MODELO PARA CREACIÓN
# =============================================================================

class UserProfileCreate(BaseModel):
    """
    Modelo para crear un nuevo usuario.

    Este modelo se usa para preparar los datos que se enviarán a
    Supabase Auth al crear el usuario. Los campos se pasarán como
    user_metadata y el trigger en la BD creará el profile automáticamente.

    Ejemplo de uso:
        datos = UserProfileCreate(
            email="juan@ejemplo.com",
            password="contraseña_segura",
            nombre_completo="Juan Pérez García",
            rol=RolUsuario.CLIENT,
            telefono="5512345678"
        )
        # Luego se envía a supabase.auth.admin.create_user()
    """

    model_config = ConfigDict(
        use_enum_values=True,
        str_strip_whitespace=True,
        validate_assignment=True,
    )

    # Credenciales (para Supabase Auth)
    email: str = Field(..., description="Email del usuario (será su login)")
    password: str = Field(
        ...,
        min_length=8,
        description="Contraseña (mínimo 8 caracteres)"
    )

    # Datos del perfil (irán en user_metadata)
    nombre_completo: str = Field(
        ...,
        min_length=NOMBRE_COMPLETO_MIN,
        max_length=NOMBRE_COMPLETO_MAX,
    )
    rol: RolUsuario = Field(default=RolUsuario.CLIENT)
    telefono: Optional[str] = Field(
        default=None,
        min_length=TELEFONO_DIGITOS,
        max_length=TELEFONO_DIGITOS,
        pattern=r'^\d{10}$',
    )

    # =========================================================================
    # VALIDADORES
    # =========================================================================

    @field_validator('email')
    @classmethod
    def validar_email(cls, v: str) -> str:
        """Normaliza y valida el formato de email."""
        v = v.strip().lower()
        if not re.match(EMAIL_PATTERN, v):
            raise ValueError('Formato de email invalido')
        return v

    @field_validator('nombre_completo')
    @classmethod
    def validar_nombre(cls, v: str) -> str:
        """Normaliza el nombre."""
        return v.strip().title() if v else v

    @field_validator('telefono')
    @classmethod
    def validar_telefono(cls, v: Optional[str]) -> Optional[str]:
        """Extrae solo dígitos del teléfono."""
        if v is None:
            return None
        digitos = ''.join(c for c in v if c.isdigit())
        if len(digitos) != TELEFONO_DIGITOS:
            raise ValueError(f'El teléfono debe tener {TELEFONO_DIGITOS} dígitos')
        return digitos

    # =========================================================================
    # MÉTODOS HELPER
    # =========================================================================

    def to_auth_metadata(self) -> dict:
        """
        Convierte a formato de metadata para Supabase Auth.

        Returns:
            dict con los campos que el trigger leerá para crear el profile
        """
        metadata = {
            'nombre_completo': self.nombre_completo,
            'rol': self.rol if isinstance(self.rol, str) else self.rol.value,
        }
        if self.telefono:
            metadata['telefono'] = self.telefono
        return metadata


# =============================================================================
# MODELO PARA ACTUALIZACIÓN
# =============================================================================

class UserProfileUpdate(BaseModel):
    """
    Modelo para actualizar un perfil existente.

    Todos los campos son opcionales. Solo se actualizan los campos
    que se proporcionen (no-None).

    Nota: El rol solo puede ser modificado por un admin.
    """

    model_config = ConfigDict(
        use_enum_values=True,
        str_strip_whitespace=True,
        validate_assignment=True,
    )

    nombre_completo: Optional[str] = Field(
        default=None,
        min_length=NOMBRE_COMPLETO_MIN,
        max_length=NOMBRE_COMPLETO_MAX,
    )
    telefono: Optional[str] = Field(
        default=None,
        min_length=TELEFONO_DIGITOS,
        max_length=TELEFONO_DIGITOS,
        pattern=r'^\d{10}$',
    )
    rol: Optional[RolUsuario] = None
    activo: Optional[bool] = None

    # =========================================================================
    # VALIDADORES
    # =========================================================================

    @field_validator('nombre_completo')
    @classmethod
    def validar_nombre(cls, v: Optional[str]) -> Optional[str]:
        """Normaliza el nombre si se proporciona."""
        if v:
            return v.strip().title()
        return v

    @field_validator('telefono')
    @classmethod
    def validar_telefono(cls, v: Optional[str]) -> Optional[str]:
        """Valida teléfono si se proporciona."""
        if v is None:
            return None
        digitos = ''.join(c for c in v if c.isdigit())
        if len(digitos) != TELEFONO_DIGITOS:
            raise ValueError(f'El teléfono debe tener {TELEFONO_DIGITOS} dígitos')
        return digitos


# =============================================================================
# MODELO RESUMIDO PARA LISTADOS
# =============================================================================

class UserProfileResumen(BaseModel):
    """
    Modelo resumido de perfil para listados y selects.

    Incluye información básica del usuario más las empresas a las que
    tiene acceso (para contexto en interfaces de administración).
    """

    model_config = ConfigDict(
        use_enum_values=True,
        from_attributes=True,
    )

    id: UUID
    nombre_completo: str
    rol: str
    activo: bool
    ultimo_acceso: Optional[datetime] = None

    # Datos enriquecidos (se llenan desde el servicio)
    email: Optional[str] = None  # Viene de auth.users
    cantidad_empresas: int = 0   # Cantidad de empresas asignadas
    empresa_principal: Optional[str] = None  # Nombre de la empresa principal

    @property
    def esta_activo(self) -> bool:
        return self.activo

    @property
    def es_admin(self) -> bool:
        return self.rol == 'admin'

    def __str__(self) -> str:
        return f"{self.nombre_completo} ({self.rol})"
