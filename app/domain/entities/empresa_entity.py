"""
Entidad de dominio para Empresa usando Pydantic.
Combina validación de datos con lógica de negocio.
"""
from pydantic import BaseModel, Field, field_validator, ConfigDict
from datetime import datetime
from enum import Enum
from typing import Optional


class TipoEmpresa(str, Enum):
    """Tipos de empresa en el dominio"""
    NOMINA = 'NOMINA'
    MANTENIMIENTO = 'MANTENIMIENTO'


class EstatusEmpresa(str, Enum):
    """Estados posibles de una empresa"""
    ACTIVO = 'ACTIVO'
    INACTIVO = 'INACTIVO'
    SUSPENDIDO = 'SUSPENDIDO'


class EmpresaEntity(BaseModel):
    """
    Entidad de dominio Empresa.
    Extiende el modelo base con reglas de negocio.
    """
    
    model_config = ConfigDict(
        validate_assignment=True,
        str_strip_whitespace=True,
        from_attributes=True
    )
    
    # Identificación
    id: Optional[int] = None
    nombre_comercial: str = Field(min_length=1, max_length=100)
    razon_social: str = Field(min_length=1, max_length=100)
    tipo_empresa: TipoEmpresa
    rfc: str = Field(min_length=12, max_length=13)
    
    # Contacto
    direccion: Optional[str] = Field(None, max_length=200)
    codigo_postal: Optional[str] = Field(None, min_length=5, max_length=5)
    telefono: Optional[str] = Field(None, max_length=15)
    email: Optional[str] = Field(None, max_length=100)
    pagina_web: Optional[str] = Field(None, max_length=100)
    
    # Control
    estatus: EstatusEmpresa = Field(default=EstatusEmpresa.ACTIVO)
    notas: Optional[str] = None
    
    # Auditoría
    fecha_creacion: Optional[datetime] = None
    fecha_actualizacion: Optional[datetime] = None
    
    # Validadores
    @field_validator('rfc')
    @classmethod
    def validar_rfc(cls, v: str) -> str:
        """Valida y normaliza RFC"""
        if v:
            v = v.upper().strip()
            # Validación básica RFC mexicano
            if len(v) not in [12, 13]:
                raise ValueError(f"RFC debe tener 12 o 13 caracteres, tiene {len(v)}")
        return v
    
    @field_validator('email')
    @classmethod
    def validar_email(cls, v: Optional[str]) -> Optional[str]:
        """Normaliza email"""
        if v:
            v = v.lower().strip()
        return v
    
    # REGLAS DE NEGOCIO
    
    def puede_facturar(self) -> bool:
        """Una empresa solo puede facturar si está activa"""
        return self.estatus == EstatusEmpresa.ACTIVO
    
    def puede_tener_empleados(self) -> bool:
        """Solo empresas de nómina pueden tener empleados"""
        return self.tipo_empresa == TipoEmpresa.NOMINA
    
    def puede_dar_mantenimiento(self) -> bool:
        """Solo empresas de mantenimiento pueden dar este servicio"""
        return self.tipo_empresa == TipoEmpresa.MANTENIMIENTO
    
    def activar(self):
        """Activa la empresa"""
        if self.estatus == EstatusEmpresa.ACTIVO:
            raise ValueError("La empresa ya está activa")
        self.estatus = EstatusEmpresa.ACTIVO
    
    def suspender(self):
        """Suspende la empresa"""
        if self.estatus == EstatusEmpresa.SUSPENDIDO:
            raise ValueError("La empresa ya está suspendida")
        self.estatus = EstatusEmpresa.SUSPENDIDO
    
    def inactivar(self):
        """Inactiva la empresa"""
        if self.estatus == EstatusEmpresa.INACTIVO:
            raise ValueError("La empresa ya está inactiva")
        self.estatus = EstatusEmpresa.INACTIVO



class EmpresaResumenEntity(BaseModel):
    """Versión resumida de la empresa para listados"""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    nombre_comercial: str
    tipo_empresa: TipoEmpresa
    estatus: EstatusEmpresa
    contacto_principal: str
    fecha_creacion: Optional[datetime]
    
    @classmethod
    def from_empresa(cls, empresa: EmpresaEntity) -> 'EmpresaResumenEntity':
        """Factory method para crear desde una empresa completa"""
        contacto = empresa.email or empresa.telefono or "Sin contacto"
        return cls(
            id=empresa.id,
            nombre_comercial=empresa.nombre_comercial,
            tipo_empresa=empresa.tipo_empresa,
            estatus=empresa.estatus,
            contacto_principal=contacto,
            fecha_creacion=empresa.fecha_creacion
        )