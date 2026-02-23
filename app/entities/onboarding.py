"""
Entidades de dominio para el proceso de onboarding de empleados.

AltaEmpleadoBuap: datos mínimos para dar de alta un empleado desde BUAP.
CompletarDatosEmpleado: datos que el empleado llena en autoservicio.
ExpedienteStatus: value object con el estado del expediente documental.
"""
import re
from typing import Optional
from pydantic import BaseModel, Field, field_validator, ConfigDict

from app.core.validation.constants import (
    CURP_PATTERN,
    CURP_LEN,
    NOMBRE_EMPLEADO_MIN,
    NOMBRE_EMPLEADO_MAX,
    APELLIDO_MIN,
    APELLIDO_MAX,
    EMAIL_MAX,
    TELEFONO_DIGITOS,
    DIRECCION_MAX,
    CUENTA_BANCARIA_MAX,
    BANCO_MAX,
    CLABE_LEN,
    ENTIDAD_NACIMIENTO_MAX,
    CONTACTO_EMERGENCIA_MAX,
)


class AltaEmpleadoBuap(BaseModel):
    """
    Datos mínimos que BUAP proporciona para dar de alta un empleado.

    El CURP se valida con el mismo patrón que la entidad Empleado.
    """

    model_config = ConfigDict(
        str_strip_whitespace=True,
    )

    empresa_id: int
    curp: str = Field(min_length=CURP_LEN, max_length=CURP_LEN)
    nombre: str = Field(min_length=NOMBRE_EMPLEADO_MIN, max_length=NOMBRE_EMPLEADO_MAX)
    apellido_paterno: str = Field(min_length=APELLIDO_MIN, max_length=APELLIDO_MAX)
    apellido_materno: Optional[str] = Field(None, max_length=APELLIDO_MAX)
    email: Optional[str] = Field(None, max_length=EMAIL_MAX)
    sede_id: Optional[int] = None

    @field_validator('curp', mode='before')
    @classmethod
    def validar_curp(cls, v: str) -> str:
        """Valida formato de CURP (reutiliza patrón de Empleado)."""
        if v:
            v = v.upper().strip()
            if len(v) != CURP_LEN:
                raise ValueError(f'CURP debe tener {CURP_LEN} caracteres (tiene {len(v)})')
            if not re.match(CURP_PATTERN, v):
                raise ValueError('CURP con formato inválido')
        return v

    @field_validator('nombre', 'apellido_paterno', 'apellido_materno', mode='before')
    @classmethod
    def normalizar_nombre(cls, v: Optional[str]) -> Optional[str]:
        """Normaliza nombres a mayúsculas."""
        if v:
            return v.upper().strip()
        return v

    @field_validator('email', mode='before')
    @classmethod
    def validar_email(cls, v: Optional[str]) -> Optional[str]:
        """Valida formato de email."""
        if v:
            v = v.lower().strip()
            if '@' not in v or '.' not in v:
                raise ValueError('Email con formato inválido')
        return v


class CompletarDatosEmpleado(BaseModel):
    """
    Datos que el empleado completa en autoservicio.

    Se usa cuando el empleado accede por primera vez al portal
    y debe llenar su información personal y bancaria.
    """

    model_config = ConfigDict(
        str_strip_whitespace=True,
    )

    telefono: Optional[str] = Field(None, max_length=TELEFONO_DIGITOS)
    direccion: Optional[str] = Field(None, max_length=DIRECCION_MAX)
    contacto_emergencia: Optional[str] = Field(None, max_length=CONTACTO_EMERGENCIA_MAX)
    entidad_nacimiento: Optional[str] = Field(None, max_length=ENTIDAD_NACIMIENTO_MAX)

    # Datos bancarios
    cuenta_bancaria: Optional[str] = Field(None, max_length=CUENTA_BANCARIA_MAX)
    banco: Optional[str] = Field(None, max_length=BANCO_MAX)
    clabe_interbancaria: Optional[str] = Field(None, max_length=CLABE_LEN)

    @field_validator('telefono', mode='before')
    @classmethod
    def validar_telefono(cls, v: Optional[str]) -> Optional[str]:
        """Valida teléfono (solo 10 dígitos)."""
        if v:
            v = re.sub(r'[^0-9]', '', v)
            if len(v) != TELEFONO_DIGITOS:
                raise ValueError(f'Teléfono debe tener {TELEFONO_DIGITOS} dígitos')
        return v

    @field_validator('clabe_interbancaria', mode='before')
    @classmethod
    def validar_clabe(cls, v: Optional[str]) -> Optional[str]:
        """Valida CLABE interbancaria (18 dígitos)."""
        if v:
            v = v.strip()
            if not re.match(r'^\d{18}$', v):
                raise ValueError('CLABE interbancaria debe tener 18 dígitos numéricos')
        return v

    @field_validator('cuenta_bancaria', mode='before')
    @classmethod
    def validar_cuenta(cls, v: Optional[str]) -> Optional[str]:
        """Valida cuenta bancaria (10-18 dígitos)."""
        if v:
            v = v.strip()
            if not re.match(r'^\d{10,18}$', v):
                raise ValueError('Cuenta bancaria debe tener entre 10 y 18 dígitos numéricos')
        return v


class ExpedienteStatus(BaseModel):
    """
    Value object calculado con el estado del expediente documental.

    No se persiste: se calcula a partir de los documentos del empleado.
    """

    model_config = ConfigDict(from_attributes=True)

    documentos_requeridos: int = 0
    documentos_subidos: int = 0
    documentos_aprobados: int = 0
    documentos_rechazados: int = 0
    porcentaje_completado: float = 0.0

    @property
    def esta_completo(self) -> bool:
        """True si todos los documentos requeridos están aprobados."""
        return (
            self.documentos_requeridos > 0
            and self.documentos_aprobados >= self.documentos_requeridos
        )

    @property
    def tiene_rechazados(self) -> bool:
        """True si hay documentos rechazados que requieren corrección."""
        return self.documentos_rechazados > 0
