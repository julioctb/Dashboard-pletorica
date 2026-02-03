"""
Entidad de dominio para el historial de restricciones de empleados.

Registra cada evento de restriccion y liberacion para auditoria.
Esta tabla es INMUTABLE: solo se insertan registros, nunca se modifican.
"""
from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict

from app.core.enums import AccionRestriccion


class EmpleadoRestriccionLog(BaseModel):
    """
    Registro de historial de restriccion/liberacion.

    Cada vez que un admin restringe o libera un empleado,
    se crea un registro en esta tabla para auditoria.
    """

    model_config = ConfigDict(
        use_enum_values=True,
        from_attributes=True,
    )

    id: Optional[int] = None
    empleado_id: int
    accion: AccionRestriccion
    motivo: str = Field(..., min_length=10, max_length=500)
    fecha: datetime = Field(default_factory=datetime.now)
    ejecutado_por: UUID
    notas: Optional[str] = Field(None, max_length=1000)
    fecha_creacion: Optional[datetime] = None


class EmpleadoRestriccionLogCreate(BaseModel):
    """DTO para crear un registro de restriccion/liberacion."""

    model_config = ConfigDict(
        use_enum_values=True,
        str_strip_whitespace=True,
    )

    empleado_id: int
    accion: AccionRestriccion
    motivo: str = Field(..., min_length=10, max_length=500)
    ejecutado_por: UUID
    notas: Optional[str] = Field(None, max_length=1000)


class EmpleadoRestriccionLogResumen(BaseModel):
    """Resumen para mostrar en UI (incluye nombre del admin)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    empleado_id: int
    accion: str
    motivo: str
    fecha: datetime
    ejecutado_por_nombre: str  # JOIN con user_profiles
    notas: Optional[str] = None
