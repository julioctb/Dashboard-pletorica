from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field,ConfigDict


class TipoEmpresa(str, Enum):
    NOMINA = 'NOMINA'
    MANTENIMIENTO = 'MANTENIMIENTO'

class EstatusEmpresa (str, Enum):
    ACTIVO = 'ACTIVO'
    INACTIVO = 'INACTIVO'
    SUSPENDIDO = 'SUSPENDIDO'

#Se define el modelo de la empresa

class Empresa(BaseModel):
    '''Entidad con reglas de negocio BUAP'''
    """Modelo principal para la tabla empresas"""
    
    # Pydantic v2 - Nueva sintaxis para configuración
    model_config = ConfigDict(
        use_enum_values=True,
        str_strip_whitespace=True,  # Elimina espacios automáticamente
        validate_assignment=True,   # Valida al asignar valores
        from_attributes=True       # Permite crear desde atributos de objeto
    )
    
    # Campo ID
    id: Optional[int] = None
    
    # Información básica de la empresa
    nombre_comercial: str = Field(
        min_length=1, 
        max_length=100,
        description="Nombre comercial de la empresa"
    )
    razon_social: str = Field(
        min_length=1, 
        max_length=100,
        description="Razón social completa"
    )
    tipo_empresa: TipoEmpresa = Field(
        description="Tipo de empresa: nomina o mantenimiento"
    )
    rfc: str = Field(
        min_length=12, 
        max_length=13,
        pattern=r'^[A-Z&Ñ]{3,4}[0-9]{6}[A-V1-9][A-Z1-9][0-9A]$',
        description="RFC válido de la empresa"
    )
    
    # Información de contacto
    direccion: Optional[str] = Field(
        None, 
        max_length=200,
        description="Dirección física completa"
    )
    codigo_postal: Optional[str] = Field(
        None, 
        min_length=5, 
        max_length=5, 
        pattern=r'^[0-9]{5}$',
        description="Código postal de 5 dígitos"
    )
    telefono: Optional[str] = Field(
        None, 
        max_length=15,
        description="Número de teléfono principal"
    )
    email: Optional[str] = Field(
        None, 
        max_length=100,
        description="Correo electrónico de contacto"
    )
    pagina_web: Optional[str] = Field(
        None, 
        max_length=100,
        description="Sitio web de la empresa"
    )
    
    # Control de estado
    estatus: EstatusEmpresa = Field(
        default=EstatusEmpresa.ACTIVO,
        description="Estado actual de la empresa"
    )
    fecha_creacion: Optional[datetime] = Field(
        None,
        description="Fecha de registro en el sistema"
    )
    notas: Optional[str] = Field(
        None,
        description="Observaciones y notas adicionales"
    )
    
    # Métodos utilitarios
    def es_empresa_nomina(self) -> bool:
        return self.tipo_empresa == TipoEmpresa.NOMINA
    
    def es_empresa_mantenimiento(self) -> bool:
        return self.tipo_empresa == TipoEmpresa.MANTENIMIENTO
    
    def esta_activa(self) -> bool:
        return self.estatus == EstatusEmpresa.ACTIVO
    
    def get_info_completa(self) -> str:
        return f"{self.nombre_comercial} ({self.razon_social}) - {self.tipo_empresa.value.title()}"
    
    def __str__(self) -> str:
        return f"{self.nombre_comercial} ({self.tipo_empresa.value})"

#clase para crear una empresa
class EmpresaCreate(BaseModel):
     
    model_config = ConfigDict(
        use_enum_values=True,
        str_strip_whitespace=True,
        validate_assignment=True
    )
    
    nombre_comercial: str = Field(min_length=1, max_length=100)
    razon_social: str = Field(min_length=1, max_length=100)
    tipo_empresa: TipoEmpresa
    rfc: str = Field(min_length=12, max_length=13)
    direccion: Optional[str] = Field(None, max_length=200)
    codigo_postal: Optional[str] = Field(None, min_length=5, max_length=5)
    telefono: Optional[str] = Field(None, max_length=15)
    email: Optional[str] = Field(None, max_length=100)
    pagina_web: Optional[str] = Field(None, max_length=100)
    estatus: EstatusEmpresa = Field(default=EstatusEmpresa.ACTIVO)
    notas: Optional[str] = None

class EmpresaUpdate(BaseModel):
 
    
    model_config = ConfigDict(
        use_enum_values=True,
        str_strip_whitespace=True,
        validate_assignment=True
    )
    
    nombre_comercial: Optional[str] = Field(None, min_length=1, max_length=100)
    razon_social: Optional[str] = Field(None, min_length=1, max_length=100)
    tipo_empresa: Optional[TipoEmpresa] = None
    rfc: Optional[str] = Field(None, min_length=12, max_length=13)
    direccion: Optional[str] = Field(None, max_length=200)
    codigo_postal: Optional[str] = Field(None, min_length=5, max_length=5)
    telefono: Optional[str] = Field(None, max_length=15)
    email: Optional[str] = Field(None, max_length=100)
    pagina_web: Optional[str] = Field(None, max_length=100)
    estatus: Optional[EstatusEmpresa] = None
    notas: Optional[str] = None

class EmpresaResumen(BaseModel):
    """Modelo para mostrar resumen de empresa"""
    
    model_config = ConfigDict(
        use_enum_values=True,
        from_attributes=True
    )
    
    id: int
    nombre_comercial: str
    tipo_empresa: TipoEmpresa
    estatus: EstatusEmpresa
    contacto_principal: str
    fecha_creacion: datetime