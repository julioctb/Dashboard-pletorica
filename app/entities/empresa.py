"""
Entidades de dominio para Empresas.
Consolidadas desde múltiples ubicaciones legacy.
"""
import re
from decimal import Decimal
from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field, field_validator, ConfigDict

# Constantes de validación
RFC_PATTERN = r'^[A-Z&Ñ]{3,4}[0-9]{6}[A-V1-9][A-Z1-9][0-9A]$'
EMAIL_PATTERN = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
REGISTRO_PATRONAL_PATTERN = r'^[A-Z][0-9]{2}-[0-9]{5}-[0-9]{2}-[0-9]$'


class TipoEmpresa(str, Enum):
    """Tipos de empresa en el sistema"""
    NOMINA = 'NOMINA'
    MANTENIMIENTO = 'MANTENIMIENTO'


class EstatusEmpresa(str, Enum):
    """Estados posibles de una empresa"""
    ACTIVO = 'ACTIVO'
    INACTIVO = 'INACTIVO'
    SUSPENDIDO = 'SUSPENDIDO'

def formatear_registro_patronal(valor: str) -> str:
    """
    Formatea el registro patronal al formato estándar: Y12-34567-10-1
    
    Acepta:
        - Y1234567101 (sin guiones)
        - Y12-34567-10-1 (con guiones)
    """
    # Limpiar: solo letras y números
    limpio = re.sub(r'[^A-Z0-9]', '', valor.upper())
    
    if len(limpio) != 11:
        raise ValueError(
            f'Registro patronal debe tener 11 caracteres (tiene {len(limpio)})'
        )
    
    if not re.match(r'^[A-Z][0-9]{10}$', limpio):
        raise ValueError(
            'Registro patronal inválido. Debe iniciar con letra seguida de 10 dígitos'
        )
    
    # Formatear: Y12-34567-10-1
    return f"{limpio[0:3]}-{limpio[3:8]}-{limpio[8:10]}-{limpio[10]}"


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
        min_length=2,
        max_length=100,
        description="Nombre comercial de la empresa"
    )
    razon_social: str = Field(
        min_length=2,
        max_length=100,
        description="Razón social completa"
    )
    tipo_empresa: TipoEmpresa = Field(
        description="Tipo de empresa: nomina o mantenimiento"
    )
    rfc: str = Field(
        min_length=12,
        max_length=13,
        pattern=RFC_PATTERN,
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

    # Datos IMSS (opcionales)
    registro_patronal: Optional[str] = Field(
        None,
        max_length=15,
        description="Registro patronal IMSS. Formato: Y12-34567-10-1"
    )
    prima_riesgo: Optional[Decimal] = Field(
        None,
        ge=Decimal("0.00500"),
        le=Decimal("0.15000"),
        decimal_places=5,
        description="Prima de riesgo de trabajo (0.5% a 15%)"
    )

    codigo_corto: Optional[str] = Field(
    None,
    min_length=3,
    max_length=3,
    pattern=r'^[A-Z0-9]{3}$',
    description="Código único de 3 caracteres (autogenerado)"
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
        if v:
            v = v.upper().strip()
            # Validar formato específico con mensaje claro usando constante global
            if not re.match(RFC_PATTERN, v):
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
        """Valida formato y normaliza email a minúsculas"""
        if v:
            v = v.lower().strip()
            # Validar formato usando constante global (mismo patrón que frontend)
            if not re.match(EMAIL_PATTERN, v):
                raise ValueError('Formato de email inválido (ejemplo: usuario@dominio.com)')
        return v

    @field_validator('telefono')
    @classmethod
    def validar_telefono(cls, v: Optional[str]) -> Optional[str]:
        """Valida que el teléfono tenga 10 dígitos (mexicano)"""
        if v:
            v = v.strip()
            # Remover separadores permitidos (misma lógica que frontend)
            tel_solo_digitos = (
                v.replace(" ", "")
                .replace("-", "")
                .replace("(", "")
                .replace(")", "")
                .replace("+", "")
            )

            if not tel_solo_digitos.isdigit():
                raise ValueError('Teléfono: Solo números (puede usar espacios, guiones o paréntesis)')

            if len(tel_solo_digitos) != 10:
                raise ValueError(f'Teléfono debe tener 10 dígitos (tiene {len(tel_solo_digitos)})')

        return v
    
    @field_validator('registro_patronal')
    @classmethod
    def validar_registro_patronal(cls, v: Optional[str]) -> Optional[str]:
        """Valida y formatea el registro patronal IMSS"""
        if v:
            return formatear_registro_patronal(v)
        return v

    @field_validator('prima_riesgo', mode='before')
    @classmethod
    def validar_prima_riesgo(cls, v) -> Optional[Decimal]:
        """
        Acepta porcentaje (2.598) o decimal (0.02598)
        """
        if v is None:
            return None
        
        if isinstance(v, (int, float, str)):
            v = Decimal(str(v))
        
        # Si es mayor a 1, asumimos porcentaje
        if v > Decimal("1"):
            v = v / Decimal("100")
        
        if v < Decimal("0.00500") or v > Decimal("0.15000"):
            raise ValueError(
                f'Prima de riesgo debe estar entre 0.5% y 15%'
            )
        
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

    def get_prima_riesgo_porcentaje(self) -> Optional[float]:
        """Retorna la prima de riesgo como porcentaje (ej: 2.598)"""
        if self.prima_riesgo:
            return float(self.prima_riesgo * 100)
        return None

    def tiene_datos_imss(self) -> bool:
        """Verifica si tiene datos IMSS completos"""
        return bool(self.registro_patronal and self.prima_riesgo)

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

    nombre_comercial: str = Field(min_length=2, max_length=100)
    razon_social: str = Field(min_length=2, max_length=100)
    tipo_empresa: TipoEmpresa
    rfc: str = Field(min_length=12, max_length=13)
    direccion: Optional[str] = Field(None, max_length=200)
    codigo_postal: Optional[str] = Field(None, min_length=5, max_length=5)
    telefono: Optional[str] = Field(None, max_length=15)
    email: Optional[str] = Field(None, max_length=100)
    pagina_web: Optional[str] = Field(None, max_length=100)
    registro_patronal: Optional[str] = Field(None, max_length=15)
    prima_riesgo: Optional[Decimal] = Field(None)
    estatus: EstatusEmpresa = Field(default=EstatusEmpresa.ACTIVO)
    notas: Optional[str] = None


class EmpresaUpdate(BaseModel):
    """Modelo para actualizar una empresa existente (todos los campos opcionales)"""

    model_config = ConfigDict(
        use_enum_values=True,
        str_strip_whitespace=True,
        validate_assignment=True
    )

    nombre_comercial: Optional[str] = Field(None, min_length=2, max_length=100)
    razon_social: Optional[str] = Field(None, min_length=2, max_length=100)
    tipo_empresa: Optional[TipoEmpresa] = None
    rfc: Optional[str] = Field(None, min_length=12, max_length=13)
    direccion: Optional[str] = Field(None, max_length=200)
    codigo_postal: Optional[str] = Field(None, min_length=5, max_length=5)
    telefono: Optional[str] = Field(None, max_length=15)
    email: Optional[str] = Field(None, max_length=100)
    pagina_web: Optional[str] = Field(None, max_length=100)
    registro_patronal: Optional[str] = Field(None, max_length=15)
    prima_riesgo: Optional[Decimal] = Field(None)
    estatus: Optional[EstatusEmpresa] = None
    notas: Optional[str] = None


class EmpresaResumen(BaseModel):
    """Modelo resumido de empresa para listados con datos clave para UI mejorada"""

    model_config = ConfigDict(
        use_enum_values=True,
        from_attributes=True
    )

    id: int
    nombre_comercial: str
    razon_social: str  # Agregado para mostrar en subtítulo
    tipo_empresa: TipoEmpresa
    estatus: EstatusEmpresa
    contacto_principal: Optional[str]  # Teléfono
    email: Optional[str]  # Agregado para mostrar en tarjeta
    fecha_creacion: datetime
    registro_patronal: Optional[str]  # Nuevo
    tiene_imss: bool  # Nuevo

    @classmethod
    def from_empresa(cls, empresa: Empresa) -> 'EmpresaResumen':
        """Factory method para crear desde una empresa completa"""
        return cls(
            id=empresa.id,
            nombre_comercial=empresa.nombre_comercial,
            razon_social=empresa.razon_social,
            tipo_empresa=empresa.tipo_empresa,
            estatus=empresa.estatus,
            contacto_principal=empresa.telefono,  # Teléfono directo
            email=empresa.email,  # Email directo
            fecha_creacion=empresa.fecha_creacion,
            registro_patronal=empresa.registro_patronal,
            tiene_imss=empresa.tiene_datos_imss(),
        )
