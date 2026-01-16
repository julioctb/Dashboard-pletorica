"""
Entidades de dominio para Empresas.
Consolidadas desde múltiples ubicaciones legacy.
"""
import re
from decimal import Decimal
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator, ConfigDict

from app.core.enums import TipoEmpresa, EstatusEmpresa
from app.core.validation_patterns import (
    RFC_PATTERN,
    RFC_PREFIX_PATTERN,
    EMAIL_PATTERN,
    REGISTRO_PATRONAL_PATTERN,
    REGISTRO_PATRONAL_LIMPIO_PATTERN,
    CODIGO_POSTAL_PATTERN,
    CODIGO_CORTO_PATTERN,
    # Constantes de longitud
    NOMBRE_COMERCIAL_MIN,
    NOMBRE_COMERCIAL_MAX,
    RAZON_SOCIAL_MIN,
    RAZON_SOCIAL_MAX,
    RFC_MIN,
    RFC_MAX,
    DIRECCION_MAX,
    CODIGO_POSTAL_LEN,
    TELEFONO_MAX,
    EMAIL_MAX,
    PAGINA_WEB_MAX,
    REGISTRO_PATRONAL_MAX,
    CODIGO_CORTO_LEN,
)
from app.core.error_messages import (
    msg_rfc_longitud,
    MSG_RFC_LETRAS_INVALIDAS,
    MSG_RFC_FECHA_INVALIDA,
    msg_rfc_homoclave_invalida,
    MSG_EMAIL_FORMATO_INVALIDO,
    MSG_TELEFONO_SOLO_NUMEROS,
    msg_telefono_digitos,
    msg_registro_patronal_longitud,
    MSG_REGISTRO_PATRONAL_INVALIDO,
    MSG_PRIMA_RIESGO_RANGO,
    msg_entidad_ya_estado,
)

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
        raise ValueError(msg_registro_patronal_longitud(11, len(limpio)))

    if not re.match(REGISTRO_PATRONAL_LIMPIO_PATTERN, limpio):
        raise ValueError(MSG_REGISTRO_PATRONAL_INVALIDO)
    
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
        min_length=NOMBRE_COMERCIAL_MIN,
        max_length=NOMBRE_COMERCIAL_MAX,
        description="Nombre comercial de la empresa"
    )
    razon_social: str = Field(
        min_length=RAZON_SOCIAL_MIN,
        max_length=RAZON_SOCIAL_MAX,
        description="Razón social completa"
    )
    tipo_empresa: TipoEmpresa = Field(
        description="Tipo de empresa: nomina o mantenimiento"
    )
    rfc: str = Field(
        min_length=RFC_MIN,
        max_length=RFC_MAX,
        pattern=RFC_PATTERN,
        description="RFC válido de la empresa"
    )

    # Información de contacto
    direccion: Optional[str] = Field(
        None,
        max_length=DIRECCION_MAX,
        description="Dirección física completa"
    )
    codigo_postal: Optional[str] = Field(
        None,
        min_length=CODIGO_POSTAL_LEN,
        max_length=CODIGO_POSTAL_LEN,
        pattern=CODIGO_POSTAL_PATTERN,
        description="Código postal de 5 dígitos"
    )
    telefono: Optional[str] = Field(
        None,
        max_length=TELEFONO_MAX,
        description="Número de teléfono principal"
    )
    email: Optional[str] = Field(
        None,
        max_length=EMAIL_MAX,
        description="Correo electrónico de contacto"
    )
    pagina_web: Optional[str] = Field(
        None,
        max_length=PAGINA_WEB_MAX,
        description="Sitio web de la empresa"
    )

    # Datos IMSS (opcionales)
    registro_patronal: Optional[str] = Field(
        None,
        max_length=REGISTRO_PATRONAL_MAX,
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
        min_length=CODIGO_CORTO_LEN,
        max_length=CODIGO_CORTO_LEN,
        pattern=CODIGO_CORTO_PATTERN,
        description="Código único de 3 caracteres (autogenerado, inmutable)"
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
                    raise ValueError(msg_rfc_longitud(len(v)))
                if not re.match(RFC_PREFIX_PATTERN, v[:4]):
                    raise ValueError(MSG_RFC_LETRAS_INVALIDAS)
                if not re.match(r'^[0-9]{6}', v[4:10] if len(v) == 13 else v[3:9]):
                    raise ValueError(MSG_RFC_FECHA_INVALIDA)
                # Si llegamos aquí, es la homoclave
                raise ValueError(msg_rfc_homoclave_invalida(v[-3:]))
        return v

    @field_validator('email')
    @classmethod
    def validar_email(cls, v: Optional[str]) -> Optional[str]:
        """Valida formato y normaliza email a minúsculas"""
        if v:
            v = v.lower().strip()
            # Validar formato usando constante global (mismo patrón que frontend)
            if not re.match(EMAIL_PATTERN, v):
                raise ValueError(MSG_EMAIL_FORMATO_INVALIDO)
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
                raise ValueError(MSG_TELEFONO_SOLO_NUMEROS)

            if len(tel_solo_digitos) != 10:
                raise ValueError(msg_telefono_digitos(10, len(tel_solo_digitos)))

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
            raise ValueError(MSG_PRIMA_RIESGO_RANGO)
        
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
            raise ValueError(msg_entidad_ya_estado("La empresa", "activa"))
        self.estatus = EstatusEmpresa.ACTIVO

    def suspender(self):
        """Suspende la empresa"""
        if self.estatus == EstatusEmpresa.SUSPENDIDO:
            raise ValueError(msg_entidad_ya_estado("La empresa", "suspendida"))
        self.estatus = EstatusEmpresa.SUSPENDIDO

    def inactivar(self):
        """Inactiva la empresa"""
        if self.estatus == EstatusEmpresa.INACTIVO:
            raise ValueError(msg_entidad_ya_estado("La empresa", "inactiva"))
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

    nombre_comercial: str = Field(min_length=NOMBRE_COMERCIAL_MIN, max_length=NOMBRE_COMERCIAL_MAX)
    razon_social: str = Field(min_length=RAZON_SOCIAL_MIN, max_length=RAZON_SOCIAL_MAX)
    tipo_empresa: TipoEmpresa
    rfc: str = Field(min_length=RFC_MIN, max_length=RFC_MAX)
    direccion: Optional[str] = Field(None, max_length=DIRECCION_MAX)
    codigo_postal: Optional[str] = Field(None, min_length=CODIGO_POSTAL_LEN, max_length=CODIGO_POSTAL_LEN)
    telefono: Optional[str] = Field(None, max_length=TELEFONO_MAX)
    email: Optional[str] = Field(None, max_length=EMAIL_MAX)
    pagina_web: Optional[str] = Field(None, max_length=PAGINA_WEB_MAX)
    registro_patronal: Optional[str] = Field(None, max_length=REGISTRO_PATRONAL_MAX)
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

    nombre_comercial: Optional[str] = Field(None, min_length=NOMBRE_COMERCIAL_MIN, max_length=NOMBRE_COMERCIAL_MAX)
    razon_social: Optional[str] = Field(None, min_length=RAZON_SOCIAL_MIN, max_length=RAZON_SOCIAL_MAX)
    tipo_empresa: Optional[TipoEmpresa] = None
    rfc: Optional[str] = Field(None, min_length=RFC_MIN, max_length=RFC_MAX)
    direccion: Optional[str] = Field(None, max_length=DIRECCION_MAX)
    codigo_postal: Optional[str] = Field(None, min_length=CODIGO_POSTAL_LEN, max_length=CODIGO_POSTAL_LEN)
    telefono: Optional[str] = Field(None, max_length=TELEFONO_MAX)
    email: Optional[str] = Field(None, max_length=EMAIL_MAX)
    pagina_web: Optional[str] = Field(None, max_length=PAGINA_WEB_MAX)
    registro_patronal: Optional[str] = Field(None, max_length=REGISTRO_PATRONAL_MAX)
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
    codigo_corto: str  # Código único de 3 caracteres
    nombre_comercial: str
    razon_social: str  # Agregado para mostrar en subtítulo
    tipo_empresa: TipoEmpresa
    estatus: EstatusEmpresa
    contacto_principal: Optional[str]  # Teléfono
    email: Optional[str]  # Agregado para mostrar en tarjeta
    fecha_creacion: datetime
    registro_patronal: Optional[str]
    tiene_imss: bool

    @classmethod
    def from_empresa(cls, empresa: Empresa) -> 'EmpresaResumen':
        """Factory method para crear desde una empresa completa"""
        return cls(
            id=empresa.id,
            codigo_corto=empresa.codigo_corto or "---",  # Fallback para empresas sin código
            nombre_comercial=empresa.nombre_comercial,
            razon_social=empresa.razon_social,
            tipo_empresa=empresa.tipo_empresa,
            estatus=empresa.estatus,
            contacto_principal=empresa.telefono,
            email=empresa.email,
            fecha_creacion=empresa.fecha_creacion,
            registro_patronal=empresa.registro_patronal,
            tiene_imss=empresa.tiene_datos_imss(),
        )
