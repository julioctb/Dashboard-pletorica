"""
Entidades de dominio para documentos del expediente de empleados.

Soporta flujo de validación (pendiente → aprobado/rechazado)
y versionamiento (un documento vigente por tipo por empleado).
"""
from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict

from app.core.enums import TipoDocumentoEmpleado, EstatusDocumento
from app.core.validation.constants import OBSERVACION_RECHAZO_MAX


class EmpleadoDocumento(BaseModel):
    """Documento del expediente de un empleado."""

    model_config = ConfigDict(
        use_enum_values=True,
        str_strip_whitespace=True,
        from_attributes=True,
    )

    id: Optional[int] = None
    empleado_id: int
    tipo_documento: TipoDocumentoEmpleado
    archivo_id: Optional[int] = None
    nombre_archivo: Optional[str] = Field(None, max_length=255)

    # Flujo de validación
    estatus: EstatusDocumento = Field(default=EstatusDocumento.PENDIENTE_REVISION)
    observacion_rechazo: Optional[str] = Field(None, max_length=OBSERVACION_RECHAZO_MAX)
    revisado_por: Optional[UUID] = None
    fecha_revision: Optional[datetime] = None

    # Versionamiento
    version: int = Field(default=1, ge=1)
    es_vigente: bool = True

    # Auditoría
    subido_por: Optional[UUID] = None
    fecha_creacion: Optional[datetime] = None
    fecha_actualizacion: Optional[datetime] = None

    def esta_pendiente(self) -> bool:
        """Retorna True si el documento está pendiente de revisión."""
        return self.estatus == EstatusDocumento.PENDIENTE_REVISION

    def esta_aprobado(self) -> bool:
        """Retorna True si el documento está aprobado."""
        return self.estatus == EstatusDocumento.APROBADO

    def esta_rechazado(self) -> bool:
        """Retorna True si el documento fue rechazado."""
        return self.estatus == EstatusDocumento.RECHAZADO


class EmpleadoDocumentoCreate(BaseModel):
    """DTO para crear un documento de empleado."""

    model_config = ConfigDict(
        use_enum_values=True,
        str_strip_whitespace=True,
    )

    empleado_id: int
    tipo_documento: TipoDocumentoEmpleado
    archivo_id: Optional[int] = None
    nombre_archivo: Optional[str] = Field(None, max_length=255)
    subido_por: Optional[UUID] = None


class EmpleadoDocumentoResumen(BaseModel):
    """Resumen de documento para listados (incluye datos JOIN)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    empleado_id: int
    tipo_documento: str
    nombre_archivo: Optional[str] = None
    estatus: str
    observacion_rechazo: Optional[str] = None
    version: int = 1
    es_vigente: bool = True
    fecha_creacion: Optional[datetime] = None
    fecha_revision: Optional[datetime] = None

    # Campos JOIN
    empleado_nombre: Optional[str] = None
    revisado_por_nombre: Optional[str] = None
