from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Optional, Dict, List, Any
from pydantic import BaseModel, Field, ConfigDict, field_validator, EmailStr

class TipoContrato(str, Enum):
    INDETERMINADO = 'INDETERMINADO'
    DETERMINADO = 'DETERMINADO'
    OBRA_DETERMINADA = 'OBRA_DETERMINADA'
    CAPACITACION = 'CAPACITACION'
    PRUEBA = 'PRUEBA'

class EstatusEmpleado(str, Enum):
    ACTIVO = 'ACTIVO'
    BAJA = 'BAJA'
    SUSPENDIDO = 'SUSPENDIDO'
    INCAPACIDAD = 'INCAPACIDAD'
    VACACIONES = 'VACACIONES'
    PERMISO = 'PERMISO'

class EstadoCivil(str, Enum):
    SOLTERO = 'SOLTERO'
    CASADO = 'CASADO'
    DIVORCIADO = 'DIVORCIADO'
    VIUDO = 'VIUDO'
    UNION_LIBRE = 'UNION_LIBRE'

class TipoSangre(str, Enum):
    A_POSITIVO = 'A+'
    A_NEGATIVO = 'A-'
    B_POSITIVO = 'B+'
    B_NEGATIVO = 'B-'
    AB_POSITIVO = 'AB+'
    AB_NEGATIVO = 'AB-'
    O_POSITIVO = 'O+'
    O_NEGATIVO = 'O-'

class Empleado(BaseModel):
    """Modelo completo para la tabla empleados"""
    
    model_config = ConfigDict(
        use_enum_values=True,
        str_strip_whitespace=True,
        validate_assignment=True,
        from_attributes=True,
        json_encoders={
            Decimal: lambda v: float(v),
            date: lambda v: v.isoformat(),
            datetime: lambda v: v.isoformat()
        }
    )
    
    # Identificación
    id: Optional[int] = None
    numero_empleado: str = Field(
        min_length=1,
        max_length=20,
        description="Número único de empleado"
    )
    
    # Datos personales básicos
    nombre: str = Field(min_length=1, max_length=50)
    apellido_paterno: str = Field(min_length=1, max_length=50)
    apellido_materno: Optional[str] = Field(None, max_length=50)
    fecha_nacimiento: date
    lugar_nacimiento: Optional[str] = Field(None, max_length=100)
    genero: str = Field(pattern=r'^[MFO]$', description="M/F/O")
    estado_civil: EstadoCivil
    
    # Documentos oficiales
    rfc: str = Field(
        min_length=12,
        max_length=13,
        pattern=r'^[A-Z&Ñ]{4}[0-9]{6}[A-V1-9][A-Z1-9][0-9A]$'
    )
    curp: str = Field(
        min_length=18,
        max_length=18,
        pattern=r'^[A-Z]{4}[0-9]{6}[HM][A-Z]{5}[0-9A-Z]{2}$'
    )
    nss: str = Field(
        min_length=11,
        max_length=11,
        pattern=r'^[0-9]{11}$',
        description="Número de Seguridad Social"
    )
    
    # Contacto
    direccion: str = Field(max_length=200)
    colonia: str = Field(max_length=100)
    ciudad: str = Field(max_length=100)
    estado: str = Field(max_length=50)
    codigo_postal: str = Field(
        min_length=5,
        max_length=5,
        pattern=r'^[0-9]{5}$'
    )
    telefono: str = Field(max_length=15)
    telefono_emergencia: str = Field(max_length=15)
    contacto_emergencia: str = Field(max_length=100)
    email_personal: Optional[EmailStr] = None
    email_corporativo: Optional[EmailStr] = None
    
    # Información laboral
    empresa_id: int
    sede_id: int
    departamento_id: Optional[int] = None
    puesto_id: int
    jefe_directo_id: Optional[int] = None
    fecha_ingreso: date
    fecha_baja: Optional[date] = None
    motivo_baja: Optional[str] = Field(None, max_length=200)
    tipo_contrato: TipoContrato
    fecha_fin_contrato: Optional[date] = None
    
    # Información salarial
    salario_diario: Decimal = Field(
        gt=0,
        decimal_places=2,
        description="Salario diario real"
    )
    salario_diario_integrado: Decimal = Field(
        gt=0,
        decimal_places=2,
        description="SDI para IMSS"
    )
    salario_mensual: Decimal = Field(
        gt=0,
        decimal_places=2,
        description="Salario mensual nominal"
    )
    
    # Información médica
    tipo_sangre: Optional[TipoSangre] = None
    alergias: Optional[str] = Field(None, max_length=500)
    padecimientos_cronicos: Optional[str] = Field(None, max_length=500)
    
    # Información bancaria
    banco: Optional[str] = Field(None, max_length=50)
    numero_cuenta: Optional[str] = Field(None, max_length=20)
    clabe_interbancaria: Optional[str] = Field(
        None,
        min_length=18,
        max_length=18,
        pattern=r'^[0-9]{18}$'
    )
    
    # Beneficiarios
    beneficiarios: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Lista de beneficiarios con porcentajes"
    )
    
    # Documentos
    documentos_entregados: List[str] = Field(
        default_factory=list,
        description="Lista de documentos entregados"
    )
    documentos_urls: Dict[str, str] = Field(
        default_factory=dict,
        description="URLs de documentos digitalizados"
    )
    
    # Control
    estatus: EstatusEmpleado = Field(default=EstatusEmpleado.ACTIVO)
    fecha_creacion: Optional[datetime] = None
    fecha_actualizacion: Optional[datetime] = None
    actualizado_por: Optional[int] = None
    notas: Optional[str] = None
    
    # Campos calculados y métodos
    @property
    def nombre_completo(self) -> str:
        """Retorna el nombre completo del empleado"""
        parts = [self.nombre, self.apellido_paterno]
        if self.apellido_materno:
            parts.append(self.apellido_materno)
        return " ".join(parts)
    
    @property
    def edad(self) -> int:
        """Calcula la edad del empleado"""
        from datetime import date
        today = date.today()
        return today.year - self.fecha_nacimiento.year - (
            (today.month, today.day) < (self.fecha_nacimiento.month, self.fecha_nacimiento.day)
        )
    
    @property
    def antiguedad_anos(self) -> float:
        """Calcula años de antigüedad"""
        from datetime import date
        fecha_calculo = self.fecha_baja or date.today()
        delta = fecha_calculo - self.fecha_ingreso
        return delta.days / 365.25
    
    @field_validator('curp')
    @classmethod
    def validar_curp(cls, v):
        """Valida que el CURP sea correcto"""
        if not v or len(v) != 18:
            raise ValueError('CURP debe tener 18 caracteres')
        return v.upper()
    
    @field_validator('rfc')
    @classmethod
    def validar_rfc(cls, v):
        """Valida formato de RFC"""
        if not v or len(v) not in [12, 13]:
            raise ValueError('RFC debe tener 12 o 13 caracteres')
        return v.upper()
    
    @field_validator('nss')
    @classmethod
    def validar_nss(cls, v):
        """Valida que el NSS tenga 11 dígitos"""
        if not v or len(v) != 11 or not v.isdigit():
            raise ValueError('NSS debe tener 11 dígitos')
        return v
    
    def calcular_vacaciones(self) -> int:
        """Calcula días de vacaciones según antigüedad"""
        anos = int(self.antiguedad_anos)
        
        # Tabla LFT Art. 76
        tabla_vacaciones = {
            1: 12, 2: 14, 3: 16, 4: 18, 5: 20,
            10: 22, 15: 24, 20: 26, 25: 28, 30: 30
        }
        
        for anos_limite in sorted(tabla_vacaciones.keys(), reverse=True):
            if anos >= anos_limite:
                return tabla_vacaciones[anos_limite]
        
        return 12 if anos >= 1 else 0
    
    def calcular_prima_vacacional(self) -> Decimal:
        """Calcula prima vacacional (25% mínimo)"""
        dias_vacaciones = self.calcular_vacaciones()
        return Decimal(dias_vacaciones * float(self.salario_diario) * 0.25)
    
    def calcular_aguinaldo(self) -> Decimal:
        """Calcula aguinaldo proporcional (15 días mínimo)"""
        from datetime import date
        
        # Calcular días trabajados en el año
        ano_actual = date.today().year
        fecha_inicio = max(self.fecha_ingreso, date(ano_actual, 1, 1))
        fecha_fin = min(self.fecha_baja or date.today(), date(ano_actual, 12, 31))
        
        dias_trabajados = (fecha_fin - fecha_inicio).days + 1
        dias_aguinaldo = max(15, 15)  # Mínimo legal, ajustar según empresa
        
        aguinaldo_proporcional = (Decimal(dias_aguinaldo) * self.salario_diario * Decimal(dias_trabajados)) / Decimal(365)
        return aguinaldo_proporcional.quantize(Decimal('0.01'))


# Modelos para crear y actualizar
class EmpleadoCreate(BaseModel):
    """Modelo para crear un nuevo empleado"""
    
    model_config = ConfigDict(
        use_enum_values=True,
        str_strip_whitespace=True
    )
    
    # Datos mínimos requeridos para crear
    numero_empleado: str
    nombre: str
    apellido_paterno: str
    apellido_materno: Optional[str] = None
    fecha_nacimiento: date
    genero: str
    estado_civil: EstadoCivil
    
    rfc: str
    curp: str
    nss: str
    
    direccion: str
    colonia: str
    ciudad: str
    estado: str
    codigo_postal: str
    telefono: str
    telefono_emergencia: str
    contacto_emergencia: str
    
    empresa_id: int
    sede_id: int
    puesto_id: int
    fecha_ingreso: date
    tipo_contrato: TipoContrato
    
    salario_diario: Decimal
    salario_diario_integrado: Decimal
    salario_mensual: Decimal
    
    # Opcionales
    email_personal: Optional[EmailStr] = None
    departamento_id: Optional[int] = None
    jefe_directo_id: Optional[int] = None
    banco: Optional[str] = None
    numero_cuenta: Optional[str] = None
    clabe_interbancaria: Optional[str] = None


class EmpleadoUpdate(BaseModel):
    """Modelo para actualizar empleado"""
    
    model_config = ConfigDict(
        use_enum_values=True,
        str_strip_whitespace=True
    )
    
    # Todos los campos son opcionales para actualización parcial
    nombre: Optional[str] = None
    apellido_paterno: Optional[str] = None
    apellido_materno: Optional[str] = None
    estado_civil: Optional[EstadoCivil] = None
    
    direccion: Optional[str] = None
    colonia: Optional[str] = None
    ciudad: Optional[str] = None
    estado: Optional[str] = None
    codigo_postal: Optional[str] = None
    telefono: Optional[str] = None
    email_personal: Optional[EmailStr] = None
    email_corporativo: Optional[EmailStr] = None
    
    sede_id: Optional[int] = None
    departamento_id: Optional[int] = None
    puesto_id: Optional[int] = None
    jefe_directo_id: Optional[int] = None
    
    salario_diario: Optional[Decimal] = None
    salario_diario_integrado: Optional[Decimal] = None
    salario_mensual: Optional[Decimal] = None
    
    banco: Optional[str] = None
    numero_cuenta: Optional[str] = None
    clabe_interbancaria: Optional[str] = None
    
    estatus: Optional[EstatusEmpleado] = None
    notas: Optional[str] = None


class EmpleadoResumen(BaseModel):
    """Modelo para mostrar resumen de empleado en listas"""
    
    model_config = ConfigDict(
        from_attributes=True
    )
    
    id: int
    numero_empleado: str
    nombre_completo: str
    puesto: str
    sede: str
    empresa: str
    estatus: EstatusEmpleado
    telefono: str
    fecha_ingreso: date