"""
Entidades de dominio para el sistema de archivos.

Maneja archivos (imagenes y documentos) asociados a cualquier entidad
del sistema mediante relacion polimorfica (entidad_tipo + entidad_id).

Uso:
    from app.entities.archivo import (
        EntidadArchivo, TipoArchivo, OrigenArchivo,
        ArchivoSistema, ArchivoSistemaUpdate,
    )
"""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


# =============================================================================
# ENUMS
# =============================================================================


class EntidadArchivo(str, Enum):
    """Tipos de entidad que pueden tener archivos."""

    REQUISICION = "REQUISICION"
    REQUISICION_ITEM = "REQUISICION_ITEM"
    REPORTE = "REPORTE"
    REPORTE_ACTIVIDAD = "REPORTE_ACTIVIDAD"
    CONTRATO = "CONTRATO"
    EMPLEADO = "EMPLEADO"


class TipoArchivo(str, Enum):
    """Clasificacion del contenido del archivo."""

    IMAGEN = "IMAGEN"
    FICHA_TECNICA = "FICHA_TECNICA"
    DOCUMENTO = "DOCUMENTO"


class OrigenArchivo(str, Enum):
    """Origen desde donde se subio el archivo."""

    WEB = "WEB"
    MOVIL = "MOVIL"


# =============================================================================
# ENTIDAD PRINCIPAL
# =============================================================================


class ArchivoSistema(BaseModel):
    """Entidad completa de archivo del sistema."""

    model_config = ConfigDict(
        use_enum_values=True,
        str_strip_whitespace=True,
        from_attributes=True,
    )

    id: Optional[int] = None
    entidad_tipo: EntidadArchivo
    entidad_id: int

    nombre_original: str = Field(max_length=255)
    nombre_storage: str = Field(max_length=255)
    ruta_storage: str = Field(max_length=500)
    tipo_mime: str = Field(max_length=100)
    tamanio_bytes: int
    tipo_archivo: TipoArchivo

    descripcion: Optional[str] = Field(None, max_length=255)
    orden: int = 0

    tamanio_original_bytes: Optional[int] = None
    fue_comprimido: bool = False
    formato_original: Optional[str] = Field(None, max_length=20)
    origen: OrigenArchivo = OrigenArchivo.WEB

    created_at: Optional[datetime] = None
    created_by: Optional[int] = None

    @property
    def es_imagen(self) -> bool:
        return self.tipo_mime.startswith("image/")

    @property
    def es_pdf(self) -> bool:
        return self.tipo_mime == "application/pdf"

    @property
    def tamanio_mb(self) -> float:
        return round(self.tamanio_bytes / (1024 * 1024), 2)

    @property
    def reduccion_porcentaje(self) -> Optional[float]:
        if self.fue_comprimido and self.tamanio_original_bytes:
            return round(
                (1 - self.tamanio_bytes / self.tamanio_original_bytes) * 100, 1
            )
        return None


# =============================================================================
# MODELOS DE CREACION / ACTUALIZACION
# =============================================================================


class ArchivoSistemaUpdate(BaseModel):
    """Para actualizar metadata del archivo."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
    )

    tipo_archivo: Optional[TipoArchivo] = None
    descripcion: Optional[str] = Field(None, max_length=255)
    orden: Optional[int] = Field(None, ge=0)


# =============================================================================
# MODELOS DE RESUMEN Y RESPUESTA
# =============================================================================


class ArchivoUploadResponse(BaseModel):
    """Respuesta despues de subir un archivo."""

    model_config = ConfigDict(
        use_enum_values=True,
    )

    archivo: ArchivoSistema
    metadata_compresion: dict
