"""
Schemas Pydantic para los endpoints de onboarding.
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class AltaEmpleadoRequest(BaseModel):
    """Request para dar de alta un empleado."""
    empresa_id: int
    curp: str = Field(min_length=18, max_length=18)
    nombre: str = Field(min_length=2, max_length=100)
    apellido_paterno: str = Field(min_length=2, max_length=100)
    apellido_materno: Optional[str] = Field(None, max_length=100)
    email: Optional[str] = Field(None, max_length=200)
    sede_id: Optional[int] = None


class EmpleadoOnboardingResponse(BaseModel):
    """Respuesta con datos de empleado en onboarding."""
    id: int
    clave: str
    curp: str
    nombre_completo: str
    estatus_onboarding: Optional[str] = None
    email: Optional[str] = None
    fecha_creacion: Optional[datetime] = None


class ExpedienteStatusResponse(BaseModel):
    """Estado del expediente documental."""
    documentos_requeridos: int = 0
    documentos_subidos: int = 0
    documentos_aprobados: int = 0
    documentos_rechazados: int = 0
    porcentaje_completado: float = 0.0
    esta_completo: bool = False
    tiene_rechazados: bool = False


class DocumentoResponse(BaseModel):
    """Respuesta con datos de un documento."""
    id: int
    tipo_documento: str
    nombre_archivo: Optional[str] = None
    estatus: str
    observacion_rechazo: Optional[str] = None
    version: int = 1
    fecha_creacion: Optional[datetime] = None
    fecha_revision: Optional[datetime] = None


class RechazoDocumentoRequest(BaseModel):
    """Request para rechazar un documento."""
    observacion: str = Field(min_length=5, max_length=1000)
