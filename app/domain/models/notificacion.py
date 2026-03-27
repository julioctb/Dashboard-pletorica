"""
Entidad de dominio para Notificaciones.

Sistema de notificaciones persistente para comunicar eventos del flujo
de facturacion y otros procesos del sistema a los usuarios.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class Notificacion(BaseModel):
    """Notificacion del sistema para un usuario o empresa."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        from_attributes=True,
    )

    id: Optional[int] = None
    usuario_id: Optional[str] = Field(None, description="UUID del usuario destinatario")
    empresa_id: Optional[int] = Field(None, description="ID de la empresa destinataria")
    titulo: str = Field(..., max_length=200)
    mensaje: str = Field(..., max_length=1000)
    tipo: str = Field(..., max_length=50, description="Tipo: entregable_aprobado, prefactura_rechazada, etc.")
    entidad_tipo: Optional[str] = Field(None, max_length=50, description="ENTREGABLE, PAGO, etc.")
    entidad_id: Optional[int] = None
    leida: bool = False
    fecha_creacion: Optional[datetime] = None


class NotificacionCreate(BaseModel):
    """DTO para crear una notificacion."""

    model_config = ConfigDict(str_strip_whitespace=True)

    usuario_id: Optional[str] = None
    empresa_id: Optional[int] = None
    titulo: str = Field(..., max_length=200)
    mensaje: str = Field(..., max_length=1000)
    tipo: str = Field(..., max_length=50)
    entidad_tipo: Optional[str] = Field(None, max_length=50)
    entidad_id: Optional[int] = None
