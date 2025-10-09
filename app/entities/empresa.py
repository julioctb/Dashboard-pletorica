"""
Entidades de dominio para Empresas.
Consolidadas desde múltiples ubicaciones legacy.
"""
from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field, field_validator, ConfigDict


class TipoEmpresa(str, Enum):
    """Tipos de empresa en el sistema"""
    NOMINA = 'NOMINA'
    MANTENIMIENTO = 'MANTENIMIENTO'


class EstatusEmpresa(str, Enum):
    """Estados posibles de una empresa"""
    ACTIVO = 'ACTIVO'
    INACTIVO = 'INACTIVO'
    SUSPENDIDO = 'SUSPENDIDO'


class Empresa(BaseModel):
    """
    Entidad principal de Empresa con reglas de negocio.
    Consolida funcionalidad de app/database/models, app/domain/entities, y app/modules/empresas/domain.
    """

    model_config = ConfigDict(
        use_enum_values=True,
        str_strip_whitespace=True,
        validate_assignment=True,
        from_attributes=True
    )

    # Identificación
    id: Optional[int] = None

    # Información básica
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
    notas: Optional[str] = Field(
        None,
        description="Observaciones y notas adicionales"
    )

    # Auditoría
    fecha_creacion: Optional[datetime] = Field(
        None,
        description="Fecha de registro en el sistema"
    )
    fecha_actualizacion: Optional[datetime] = None

    # Validadores adicionales
    @field_validator('rfc')
    @classmethod
    def validar_rfc(cls, v: str) -> str:
        """Valida y normaliza RFC"""
        import re
        if v:
            v = v.upper().strip()
            # Validar formato específico con mensaje claro
            patron = r'^[A-Z&Ñ]{3,4}[0-9]{6}[A-V1-9][A-Z1-9][0-9A]$'
            if not re.match(patron, v):
                # Identificar qué parte está mal
                if len(v) < 12 or len(v) > 13:
                    raise ValueError(f'RFC debe tener 12 o 13 caracteres (tiene {len(v)})')
                if not re.match(r'^[A-Z&Ñ]{3,4}', v[:4]):
                    raise ValueError('RFC: Las primeras 3-4 letras son inválidas')
                if not re.match(r'^[0-9]{6}', v[4:10] if len(v) == 13 else v[3:9]):
                    raise ValueError('RFC: La fecha (6 dígitos) es inválida')
                # Si llegamos aquí, es la homoclave
                raise ValueError(f'RFC: La homoclave "{v[-3:]}" es inválida. Debe seguir el formato del SAT')
        return v

    @field_validator('email')
    @classmethod
    def validar_email(cls, v: Optional[str]) -> Optional[str]:
        """Normaliza email a minúsculas"""
        if v:
            v = v.lower().strip()
        return v

    # Métodos de consulta de tipo
    def es_empresa_nomina(self) -> bool:
        """Verifica si es empresa de nómina"""
        return self.tipo_empresa == TipoEmpresa.NOMINA

    def es_empresa_mantenimiento(self) -> bool:
        """Verifica si es empresa de mantenimiento"""
        return self.tipo_empresa == TipoEmpresa.MANTENIMIENTO

    # Métodos de consulta de estado
    def esta_activa(self) -> bool:
        """Verifica si la empresa está activa"""
        return self.estatus == EstatusEmpresa.ACTIVO

    def esta_suspendida(self) -> bool:
        """Verifica si la empresa está suspendida"""
        return self.estatus == EstatusEmpresa.SUSPENDIDO

    def esta_inactiva(self) -> bool:
        """Verifica si la empresa está inactiva"""
        return self.estatus == EstatusEmpresa.INACTIVO

    # Reglas de negocio
    def puede_facturar(self) -> bool:
        """Solo empresas activas pueden facturar"""
        return self.estatus == EstatusEmpresa.ACTIVO

    def puede_tener_empleados(self) -> bool:
        """Solo empresas de nómina pueden tener empleados"""
        return self.tipo_empresa == TipoEmpresa.NOMINA

    def puede_dar_mantenimiento(self) -> bool:
        """Solo empresas de mantenimiento pueden dar este servicio"""
        return self.tipo_empresa == TipoEmpresa.MANTENIMIENTO

    # Métodos de cambio de estado
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

    # Métodos de representación
    def get_info_completa(self) -> str:
        """Retorna información completa de la empresa"""
        return f"{self.nombre_comercial} ({self.razon_social}) - {self.tipo_empresa.value.title()}"

    def __str__(self) -> str:
        return f"{self.nombre_comercial} ({self.tipo_empresa.value})"


class EmpresaCreate(BaseModel):
    """Modelo para crear una nueva empresa"""

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
    """Modelo para actualizar una empresa existente (todos los campos opcionales)"""

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
    """Modelo resumido de empresa para listados"""

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

    @classmethod
    def from_empresa(cls, empresa: Empresa) -> 'EmpresaResumen':
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
