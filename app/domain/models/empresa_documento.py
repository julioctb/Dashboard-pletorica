"""Entidades del expediente anual de documentación de empresas."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.domain.enums import TipoDocumentoEmpresa


class EmpresaDocumento(BaseModel):
    """Documento anual de una empresa."""

    model_config = ConfigDict(
        use_enum_values=True,
        str_strip_whitespace=True,
        from_attributes=True,
    )

    id: Optional[int] = None
    empresa_id: int
    anio: int = Field(ge=2000, le=2100)
    tipo_documento: TipoDocumentoEmpresa
    requisito_id: Optional[int] = None
    archivo_id: Optional[int] = None
    nombre_archivo: Optional[str] = Field(None, max_length=255)
    version: int = Field(default=1, ge=1)
    es_vigente: bool = True
    subido_por: Optional[UUID] = None
    fecha_creacion: Optional[datetime] = None
    fecha_actualizacion: Optional[datetime] = None


class EmpresaDocumentoCreate(BaseModel):
    """DTO para subir un documento anual de empresa."""

    model_config = ConfigDict(
        use_enum_values=True,
        str_strip_whitespace=True,
    )

    empresa_id: int
    anio: int = Field(ge=2000, le=2100)
    tipo_documento: TipoDocumentoEmpresa
    requisito_id: Optional[int] = None
    subido_por: Optional[UUID] = None


class EmpresaDocumentoResumen(BaseModel):
    """Resumen serializable para checklist de documentación."""

    model_config = ConfigDict(from_attributes=True)

    id: Optional[int] = None
    empresa_id: int
    anio: int
    numero: int
    tipo_documento: str
    requisito_id: Optional[int] = None
    tipo_documento_label: str
    ayuda: str = ""
    obligatorio: bool = True
    es_anual: bool = True
    es_personalizado: bool = False
    estatus: str = "Pendiente"
    subido: bool = False
    archivo_id: Optional[int] = None
    nombre_archivo: str = ""
    version: int = 0
    anio_documento: Optional[int] = None
    origen_documento_texto: str = ""
    fecha_creacion: Optional[datetime] = None


class EmpresaDocumentoRequisito(BaseModel):
    """Requisito configurable por empresa para documentos extra/complementarios."""

    model_config = ConfigDict(from_attributes=True, str_strip_whitespace=True)

    id: Optional[int] = None
    empresa_id: int
    codigo: str = Field(min_length=3, max_length=80)
    nombre: str = Field(min_length=3, max_length=160)
    ayuda: Optional[str] = Field(None, max_length=500)
    es_obligatorio: bool = False
    es_anual: bool = True
    orden: int = Field(default=100, ge=1, le=9999)
    activo: bool = True
    fecha_creacion: Optional[datetime] = None
    fecha_actualizacion: Optional[datetime] = None


class EmpresaDocumentoRequisitoCreate(BaseModel):
    """DTO para crear requisitos personalizados por empresa."""

    model_config = ConfigDict(str_strip_whitespace=True)

    empresa_id: int
    nombre: str = Field(min_length=3, max_length=160)
    ayuda: Optional[str] = Field(None, max_length=500)
    es_obligatorio: bool = False
    es_anual: bool = True


class EmpresaDocumentoShareLink(BaseModel):
    """Link compartible para un expediente anual."""

    model_config = ConfigDict(from_attributes=True)

    id: Optional[int] = None
    empresa_id: int
    anio: int
    token_hash: str
    expires_at: datetime
    created_by: Optional[UUID] = None
    revoked_at: Optional[datetime] = None
    revoked_by: Optional[UUID] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class EmpresaDocumentoShareLinkCreate(BaseModel):
    """DTO para crear un link compartible."""

    model_config = ConfigDict(str_strip_whitespace=True)

    empresa_id: int
    anio: int = Field(ge=2000, le=2100)
    expires_at: datetime
    created_by: Optional[UUID] = None
