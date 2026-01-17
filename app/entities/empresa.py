"""
Entidades de dominio para Empresas.

Usa FieldConfig y helpers para mantener consistencia entre
validación frontend y backend con mínimo código duplicado.
"""
from decimal import Decimal
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator, ConfigDict

from app.core.enums import TipoEmpresa, EstatusEmpresa
from app.core.validation import (
    validar_rfc_detallado,
    formatear_registro_patronal,
    pydantic_field,
    campo_validador,
    # Configuraciones de campos
    CAMPO_NOMBRE_COMERCIAL,
    CAMPO_RAZON_SOCIAL,
    CAMPO_RFC,
    CAMPO_DIRECCION,
    CAMPO_CODIGO_POSTAL,
    CAMPO_TELEFONO,
    CAMPO_EMAIL,
    CAMPO_PAGINA_WEB,
    CAMPO_NOTAS,
    # Constantes para campos especiales
    CODIGO_CORTO_LEN,
    CODIGO_CORTO_PATTERN,
)
from app.core.catalogs import LimitesValidacion
from app.core.error_messages import (
    MSG_PRIMA_RIESGO_RANGO,
    msg_entidad_ya_estado,
)


class Empresa(BaseModel):
    """
    Entidad principal de Empresa con reglas de negocio.
    """

    model_config = ConfigDict(
        use_enum_values=True,
        str_strip_whitespace=True,
        validate_assignment=True,
        from_attributes=True
    )

    # Identificación
    id: Optional[int] = None

    # Información básica - usando pydantic_field()
    nombre_comercial: str = pydantic_field(CAMPO_NOMBRE_COMERCIAL)
    razon_social: str = pydantic_field(CAMPO_RAZON_SOCIAL)
    tipo_empresa: TipoEmpresa = Field(description="Tipo de empresa: nomina o mantenimiento")
    rfc: str = pydantic_field(CAMPO_RFC)

    # Información de contacto
    direccion: Optional[str] = pydantic_field(CAMPO_DIRECCION)
    codigo_postal: Optional[str] = pydantic_field(CAMPO_CODIGO_POSTAL)
    telefono: Optional[str] = pydantic_field(CAMPO_TELEFONO)
    email: Optional[str] = pydantic_field(CAMPO_EMAIL)
    pagina_web: Optional[str] = pydantic_field(CAMPO_PAGINA_WEB)

    # Datos IMSS (registro_patronal se formatea con guiones = 14 chars)
    registro_patronal: Optional[str] = Field(None, max_length=15)
    prima_riesgo: Optional[Decimal] = Field(
        None,
        ge=LimitesValidacion.PRIMA_RIESGO_MIN,
        le=LimitesValidacion.PRIMA_RIESGO_MAX,
        decimal_places=5,
        description="Prima de riesgo de trabajo (0.5% a 15%)"
    )

    # Código corto (autogenerado)
    codigo_corto: Optional[str] = Field(
        None,
        min_length=CODIGO_CORTO_LEN,
        max_length=CODIGO_CORTO_LEN,
        pattern=CODIGO_CORTO_PATTERN,
        description="Código único de 3 caracteres (autogenerado)"
    )

    # Control de estado
    estatus: EstatusEmpresa = Field(default=EstatusEmpresa.ACTIVO)
    notas: Optional[str] = pydantic_field(CAMPO_NOTAS)

    # Auditoría
    fecha_creacion: Optional[datetime] = None
    fecha_actualizacion: Optional[datetime] = None

    # =========================================================================
    # VALIDADORES - Generados desde FieldConfig
    # =========================================================================

    validar_nombre_comercial = campo_validador('nombre_comercial', CAMPO_NOMBRE_COMERCIAL)
    validar_razon_social = campo_validador('razon_social', CAMPO_RAZON_SOCIAL)
    validar_email = campo_validador('email', CAMPO_EMAIL)
    validar_telefono = campo_validador('telefono', CAMPO_TELEFONO)

    # =========================================================================
    # VALIDADORES ESPECIALES (lógica custom)
    # =========================================================================

    @field_validator('rfc', mode='before')
    @classmethod
    def validar_rfc(cls, v: str) -> str:
        """Valida RFC con validador detallado."""
        if v:
            v = v.upper().strip()
            error = validar_rfc_detallado(v, requerido=True)
            if error:
                raise ValueError(error)
        return v

    @field_validator('registro_patronal', mode='before')
    @classmethod
    def validar_registro_patronal(cls, v: Optional[str]) -> Optional[str]:
        """Formatea el registro patronal IMSS."""
        if v:
            return formatear_registro_patronal(v)
        return v

    @field_validator('prima_riesgo', mode='before')
    @classmethod
    def validar_prima_riesgo(cls, v) -> Optional[Decimal]:
        """Acepta porcentaje (2.598) o decimal (0.02598)."""
        if v is None:
            return None

        if isinstance(v, (int, float, str)):
            v = Decimal(str(v))

        # Si es mayor a 1, asumimos porcentaje
        if v > Decimal("1"):
            v = v / Decimal("100")

        min_val = LimitesValidacion.PRIMA_RIESGO_MIN
        max_val = LimitesValidacion.PRIMA_RIESGO_MAX

        if v < min_val or v > max_val:
            raise ValueError(MSG_PRIMA_RIESGO_RANGO)

        return v

    # =========================================================================
    # MÉTODOS DE CONSULTA
    # =========================================================================

    def es_empresa_nomina(self) -> bool:
        return self.tipo_empresa == TipoEmpresa.NOMINA

    def es_empresa_mantenimiento(self) -> bool:
        return self.tipo_empresa == TipoEmpresa.MANTENIMIENTO

    def esta_activa(self) -> bool:
        return self.estatus == EstatusEmpresa.ACTIVO

    def esta_suspendida(self) -> bool:
        return self.estatus == EstatusEmpresa.SUSPENDIDO

    def esta_inactiva(self) -> bool:
        return self.estatus == EstatusEmpresa.INACTIVO

    # =========================================================================
    # REGLAS DE NEGOCIO
    # =========================================================================

    def puede_facturar(self) -> bool:
        return self.estatus == EstatusEmpresa.ACTIVO

    def puede_tener_empleados(self) -> bool:
        return self.tipo_empresa == TipoEmpresa.NOMINA

    def puede_dar_mantenimiento(self) -> bool:
        return self.tipo_empresa == TipoEmpresa.MANTENIMIENTO

    # =========================================================================
    # MÉTODOS DE CAMBIO DE ESTADO
    # =========================================================================

    def activar(self):
        if self.estatus == EstatusEmpresa.ACTIVO:
            raise ValueError(msg_entidad_ya_estado("La empresa", "activa"))
        self.estatus = EstatusEmpresa.ACTIVO

    def suspender(self):
        if self.estatus == EstatusEmpresa.SUSPENDIDO:
            raise ValueError(msg_entidad_ya_estado("La empresa", "suspendida"))
        self.estatus = EstatusEmpresa.SUSPENDIDO

    def inactivar(self):
        if self.estatus == EstatusEmpresa.INACTIVO:
            raise ValueError(msg_entidad_ya_estado("La empresa", "inactiva"))
        self.estatus = EstatusEmpresa.INACTIVO

    def get_prima_riesgo_porcentaje(self) -> Optional[float]:
        if self.prima_riesgo:
            return float(self.prima_riesgo * 100)
        return None

    def tiene_datos_imss(self) -> bool:
        return bool(self.registro_patronal and self.prima_riesgo)

    def get_info_completa(self) -> str:
        return f"{self.nombre_comercial} ({self.razon_social}) - {self.tipo_empresa.value.title()}"

    def __str__(self) -> str:
        return f"{self.nombre_comercial} ({self.tipo_empresa.value})"


class EmpresaCreate(BaseModel):
    """Modelo para crear una nueva empresa."""

    model_config = ConfigDict(
        use_enum_values=True,
        str_strip_whitespace=True,
        validate_assignment=True
    )

    nombre_comercial: str = pydantic_field(CAMPO_NOMBRE_COMERCIAL)
    razon_social: str = pydantic_field(CAMPO_RAZON_SOCIAL)
    tipo_empresa: TipoEmpresa
    rfc: str = pydantic_field(CAMPO_RFC)
    direccion: Optional[str] = pydantic_field(CAMPO_DIRECCION)
    codigo_postal: Optional[str] = pydantic_field(CAMPO_CODIGO_POSTAL)
    telefono: Optional[str] = pydantic_field(CAMPO_TELEFONO)
    email: Optional[str] = pydantic_field(CAMPO_EMAIL)
    pagina_web: Optional[str] = pydantic_field(CAMPO_PAGINA_WEB)
    registro_patronal: Optional[str] = Field(None, max_length=15)
    prima_riesgo: Optional[Decimal] = None
    estatus: EstatusEmpresa = Field(default=EstatusEmpresa.ACTIVO)
    notas: Optional[str] = None


class EmpresaUpdate(BaseModel):
    """Modelo para actualizar una empresa existente (todos los campos opcionales)."""

    model_config = ConfigDict(
        use_enum_values=True,
        str_strip_whitespace=True,
        validate_assignment=True
    )

    nombre_comercial: Optional[str] = pydantic_field(CAMPO_NOMBRE_COMERCIAL, default=None)
    razon_social: Optional[str] = pydantic_field(CAMPO_RAZON_SOCIAL, default=None)
    tipo_empresa: Optional[TipoEmpresa] = None
    rfc: Optional[str] = pydantic_field(CAMPO_RFC, default=None)
    direccion: Optional[str] = pydantic_field(CAMPO_DIRECCION)
    codigo_postal: Optional[str] = pydantic_field(CAMPO_CODIGO_POSTAL)
    telefono: Optional[str] = pydantic_field(CAMPO_TELEFONO)
    email: Optional[str] = pydantic_field(CAMPO_EMAIL)
    pagina_web: Optional[str] = pydantic_field(CAMPO_PAGINA_WEB)
    registro_patronal: Optional[str] = Field(None, max_length=15)
    prima_riesgo: Optional[Decimal] = None
    estatus: Optional[EstatusEmpresa] = None
    notas: Optional[str] = None


class EmpresaResumen(BaseModel):
    """Modelo resumido de empresa para listados."""

    model_config = ConfigDict(
        use_enum_values=True,
        from_attributes=True
    )

    id: int
    codigo_corto: str
    nombre_comercial: str
    razon_social: str
    tipo_empresa: TipoEmpresa
    estatus: EstatusEmpresa
    contacto_principal: Optional[str]
    email: Optional[str]
    fecha_creacion: datetime
    registro_patronal: Optional[str]
    tiene_imss: bool

    @classmethod
    def from_empresa(cls, empresa: Empresa) -> 'EmpresaResumen':
        """Factory method para crear desde una empresa completa."""
        return cls(
            id=empresa.id,
            codigo_corto=empresa.codigo_corto or "---",
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
