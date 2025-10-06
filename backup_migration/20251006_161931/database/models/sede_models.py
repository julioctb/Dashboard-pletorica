from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime
from enum import Enum

# Enums para SEDES
class TipoSede(str, Enum):
    MATRIZ = "matriz"
    SUCURSAL = "sucursal"
    OFICINA = "oficina"
    ALMACEN = "almacen"
    FABRICA = "fabrica"

class EstatusSede(str, Enum):
    ACTIVO = "activo"
    INACTIVO = "inactivo"
    CERRADO = "cerrado"
    EN_CONSTRUCCION = "en_construccion"

# Modelo base de Sede (para la BD)
class Sede(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: Optional[int] = None
    empresa_id: int = Field(..., description="ID de la empresa a la que pertenece")
    codigo: str = Field(..., min_length=2, max_length=20, description="Código único de la sede")
    nombre: str = Field(..., min_length=3, max_length=200, description="Nombre de la sede")
    tipo_sede: TipoSede = Field(default=TipoSede.SUCURSAL)
    
    # Información de contacto
    direccion: Optional[str] = Field(None, max_length=500, description="Dirección física")
    telefono: Optional[str] = Field(None, max_length=20)
    email: Optional[str] = Field(None, max_length=100)
    
    # Información geográfica
    ciudad: Optional[str] = Field(None, max_length=100)
    estado_provincia: Optional[str] = Field(None, max_length=100)
    codigo_postal: Optional[str] = Field(None, max_length=10)
    pais: Optional[str] = Field(None, max_length=50, default="México")
    
    # Información adicional
    capacidad_empleados: Optional[int] = Field(None, ge=0, description="Capacidad máxima de empleados")
    area_m2: Optional[float] = Field(None, ge=0, description="Área en metros cuadrados")
    
    # Control
    estatus: EstatusSede = Field(default=EstatusSede.ACTIVO)
    activo: bool = Field(default=True)
    
    # Timestamps
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

# Modelo para crear una nueva sede
class SedeCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    empresa_id: int = Field(..., description="ID de la empresa a la que pertenece")
    codigo: str = Field(..., min_length=2, max_length=20, description="Código único de la sede")
    nombre: str = Field(..., min_length=3, max_length=200, description="Nombre de la sede")
    tipo_sede: TipoSede = Field(default=TipoSede.SUCURSAL)
    
    # Información de contacto
    direccion: Optional[str] = Field(None, max_length=500)
    telefono: Optional[str] = Field(None, max_length=20)
    email: Optional[str] = Field(None, max_length=100)
    
    # Información geográfica
    ciudad: Optional[str] = Field(None, max_length=100)
    estado_provincia: Optional[str] = Field(None, max_length=100)
    codigo_postal: Optional[str] = Field(None, max_length=10)
    pais: str = Field(default="México", max_length=50)
    
    # Información adicional
    capacidad_empleados: Optional[int] = Field(None, ge=0)
    area_m2: Optional[float] = Field(None, ge=0)
    
    # Control
    estatus: EstatusSede = Field(default=EstatusSede.ACTIVO)
    activo: bool = Field(default=True)

# Modelo para actualizar una sede
class SedeUpdate(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    codigo: Optional[str] = Field(None, min_length=2, max_length=20)
    nombre: Optional[str] = Field(None, min_length=3, max_length=200)
    tipo_sede: Optional[TipoSede] = None
    
    # Información de contacto
    direccion: Optional[str] = Field(None, max_length=500)
    telefono: Optional[str] = Field(None, max_length=20)
    email: Optional[str] = Field(None, max_length=100)
    
    # Información geográfica
    ciudad: Optional[str] = Field(None, max_length=100)
    estado_provincia: Optional[str] = Field(None, max_length=100)
    codigo_postal: Optional[str] = Field(None, max_length=10)
    pais: Optional[str] = Field(None, max_length=50)
    
    # Información adicional
    capacidad_empleados: Optional[int] = Field(None, ge=0)
    area_m2: Optional[float] = Field(None, ge=0)
    
    # Control
    estatus: Optional[EstatusSede] = None
    activo: Optional[bool] = None

# Modelo para resumen/listado de sedes
class SedeResumen(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    empresa_id: int
    codigo: str
    nombre: str
    tipo_sede: TipoSede
    ciudad: Optional[str]
    estado_provincia: Optional[str]
    estatus: EstatusSede
    activo: bool
    created_at: Optional[datetime]

# Modelo extendido con información de la empresa
class SedeCompleta(Sede):
    model_config = ConfigDict(from_attributes=True)
    
    empresa_nombre: Optional[str] = None
    empresa_codigo: Optional[str] = None