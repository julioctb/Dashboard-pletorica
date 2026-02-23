"""
Schemas de request/response para el modulo CURP.

Subconjunto de CurpValidacionResponse adaptado para la API REST.
"""
from typing import Optional
from pydantic import BaseModel, ConfigDict


class CurpValidacionSchema(BaseModel):
    """Schema de respuesta para validacion de CURP."""

    model_config = ConfigDict(from_attributes=True)

    curp: str
    formato_valido: bool
    duplicado: bool = False
    empleado_id: Optional[int] = None
    empleado_nombre: Optional[str] = None
    empresa_nombre: Optional[str] = None
    is_restricted: bool = False
    mensaje: str = ""
