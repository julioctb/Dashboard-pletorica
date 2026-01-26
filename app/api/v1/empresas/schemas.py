"""
Schemas de request/response para el modulo Empresas.

Estos schemas son subconjuntos de las entidades de dominio,
adaptados para la API REST.
"""
from typing import Optional
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict


class EmpresaResponse(BaseModel):
    """Schema de respuesta para una empresa."""

    model_config = ConfigDict(from_attributes=True)

    id: Optional[int] = None
    codigo_corto: Optional[str] = None
    nombre_comercial: str
    razon_social: str
    rfc: str
    tipo_empresa: str
    estatus: str
    direccion: Optional[str] = None
    codigo_postal: Optional[str] = None
    telefono: Optional[str] = None
    email: Optional[str] = None
    pagina_web: Optional[str] = None
    registro_patronal: Optional[str] = None
    prima_riesgo: Optional[Decimal] = None
    notas: Optional[str] = None
    fecha_creacion: Optional[datetime] = None
    fecha_actualizacion: Optional[datetime] = None
