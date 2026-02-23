"""
Entidades de dominio para validación de CURP.

CurpValidacionResponse: resultado de validar formato + duplicados.
CurpRenapoResponse: stub para futura integración con RENAPO.
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class CurpValidacionResponse(BaseModel):
    """Resultado de validar un CURP en el sistema."""

    model_config = ConfigDict(from_attributes=True)

    curp: str
    formato_valido: bool
    duplicado: bool = False
    empleado_id: Optional[int] = None
    empleado_nombre: Optional[str] = None
    empresa_nombre: Optional[str] = None
    is_restricted: bool = False
    mensaje: str = ""


class CurpRenapoResponse(BaseModel):
    """Stub para futura validación contra RENAPO."""

    model_config = ConfigDict(from_attributes=True)

    curp: str
    valido: bool = False
    nombre: Optional[str] = None
    apellido_paterno: Optional[str] = None
    apellido_materno: Optional[str] = None
    fecha_nacimiento: Optional[str] = None
    sexo: Optional[str] = None
    entidad_nacimiento: Optional[str] = None
    fecha_consulta: Optional[datetime] = None
    mensaje: str = "Integración RENAPO no disponible"
