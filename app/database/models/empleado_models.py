from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict, field_validator, computed_field, EmailStr

class EstadoCivil(str, Enum):
    SOLTERO = 'SOLTERO'
    CASADO = 'CASADO'
    DIVORCIADO = 'DIVORCIADO'
    VIUDO = 'VIUDO'
    UNION_LIBRE = 'UNION_LIBRE'

class EstatusEmpleado(str, Enum):
    ACTIVO = 'ACTIVO'
    BAJA = 'BAJA'
    SUSPENDIDO = 'SUSPENDIDO'
    INCAPACIDAD = 'INCAPACIDAD'
    VACACIONES = 'VACACIONES'

class MetodoPago(str, Enum):
    TRANSFERENCIA = 'TRANSFERENCIA'
    DEPOSITO = 'DEPOSITO'
    EFECTIVO = 'EFECTIVO'
    

class Genero(str, Enum):
    MASCULINO = 'MASCULINO'
    FEMENINO = 'FEMENINO'
    

class Empleado(BaseModel):
    """
    Modelo de Empleado basado en tu estructura de FileMaker
    con campos calculados y relaciones
    """
    
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
    
    # ========================
    # CAMPOS PRIMARIOS
    # ========================
    id: Optional[int] = Field(
        None,
        description="ID autoincremental"
    )
    
    sede_id: int = Field(
        description="ID de la sede asignada"
    )
    
    empresa_id: int = Field(
        description="ID de la empresa (PLETORICA o MANTISER)"
    )
    
    # ========================
    # DATOS PERSONALES
    # ========================
    paterno: str = Field(
        min_length=1,
        max_length=50,
        description="Apellido paterno"
    )
    
    materno: Optional[str] = Field(
        None,
        max_length=50,
        description="Apellido materno"
    )
    
    nombres: str = Field(
        min_length=1,
        max_length=100,
        description="Nombre(s)"
    )
    
    # Campo calculado en FileMaker, pero lo podemos generar con computed_field
    @computed_field
    @property
    def nombre_completo(self) -> str:
        """Genera: nombres & " " & paterno & " " & materno"""
        partes = [self.nombres, self.paterno]
        if self.materno:
            partes.append(self.materno)
        return " ".join(partes)
    
    rfc: str = Field(
        min_length=12,
        max_length=13,
        pattern=r'^[A-Z&Ñ]{3,4}[0-9]{6}[A-V1-9][A-Z1-9][0-9A]$',
        description="RFC del empleado"
    )
    
    curp: str = Field(
        min_length=18,
        max_length=18,
        pattern=r'^[A-Z]{4}[0-9]{6}[HM][A-Z]{5}[0-9A-Z]{2}$',
        description="CURP único del empleado"
    )
    
    nss: str = Field(
        min_length=11,
        max_length=11,
        pattern=r'^[0-9]{11}$',
        description="Número de Seguro Social"
    )
    
    fecha_nacimiento: date = Field(
        description="Fecha de nacimiento"
    )
    
    genero: Genero = Field(
        description="Género M/F/O"
    )
    
    # ========================
    # CONTACTO
    # ========================
    telefono: str = Field(
        max_length=15,
        description="Teléfono principal"
    )
    
    email: Optional[EmailStr] = Field(
        None,
        description="Correo electrónico"
    )
    
    domicilio: str = Field(
        max_length=300,
        description="Dirección completa"
    )
    
    # ========================
    # CONTACTO DE EMERGENCIA
    # ========================
    contacto_emergencia_nombre: str = Field(
        max_length=100,
        description="Nombre del contacto de emergencia"
    )
    
    contacto_emergencia_parentesco: str = Field(
        max_length=50,
        description="Parentesco del contacto"
    )
    
    contacto_emergencia_telefono: str = Field(
        max_length=15,
        description="Teléfono de emergencia"
    )
    
    # ========================
    # DATOS LABORALES
    # ========================
    estatus: str = Field(
        default="ACTIVO",
        description="Estatus actual del empleado"
    )
    
    fecha_ingreso: date = Field(
        description="Fecha de ingreso a la empresa"
    )
    
    numero_reingresos: Optional[str] = Field(
        None,
        description="Número de veces que ha reingresado"
    )
    
    # Campos calculados que vienen del historial laboral
    # En FileMaker: Last(HISTORIAL_LABORAL::salario)
    @computed_field
    @property
    def salario_actual(self) -> Optional[Decimal]:
        """
        Campo calculado: obtiene el último salario del historial
        En producción, esto vendría de una consulta a historial_laboral
        """
        # Este sería calculado desde el último registro de historial_laboral
        # Por ahora retornamos el campo almacenado
        return self._salario_actual if hasattr(self, '_salario_actual') else None
    
    @computed_field
    @property
    def puesto_actual(self) -> Optional[str]:
        """
        Campo calculado: obtiene el último puesto del historial
        En FileMaker: Last(HISTORIAL_LABORAL::puesto)
        """
        # Este sería calculado desde el último registro de historial_laboral
        return self._puesto_actual if hasattr(self, '_puesto_actual') else None
    
    # Campos de respaldo para cuando no hay historial
    _salario_actual: Optional[Decimal] = Field(
        None,
        alias="salario_base",
        description="Salario base actual (respaldo)"
    )
    
    salario_imss_actual: Decimal = Field(
        description="Salario diario integrado para IMSS"
    )
    
    _puesto_actual: Optional[str] = Field(
        None,
        alias="puesto_id",
        description="ID o nombre del puesto actual"
    )
    
    # ========================
    # DATOS BANCARIOS
    # ========================
    banco: Optional[str] = Field(
        None,
        max_length=50,
        description="Nombre del banco"
    )
    
    cuenta_banco: Optional[str] = Field(
        None,
        max_length=20,
        description="Número de cuenta bancaria"
    )
    
    cuenta_banco_clabe: Optional[str] = Field(
        None,
        min_length=18,
        max_length=18,
        pattern=r'^[0-9]{18}$',
        description="CLABE interbancaria"
    )
    
    cuenta_banco_tarjeta: Optional[str] = Field(
        None,
        max_length=16,
        description="Número de tarjeta de débito"
    )
    
    metodo_pago_preferido: str = Field(
        default="TRANSFERENCIA",
        description="Método de pago preferido"
    )
    
    # ========================
    # RELACIÓN CON HISTORIAL
    # ========================
    historial_laboral: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Historial laboral relacionado"
    )
    
    # ========================
    # VALIDADORES
    # ========================
    @field_validator('curp')
    @classmethod
    def validar_curp(cls, v):
        """Valida formato CURP y convierte a mayúsculas"""
        if not v:
            raise ValueError('CURP es obligatorio')
        v = v.upper()
        if len(v) != 18:
            raise ValueError('CURP debe tener 18 caracteres')
        return v
    
    @field_validator('rfc')
    @classmethod
    def validar_rfc(cls, v):
        """Valida formato RFC y convierte a mayúsculas"""
        if not v:
            raise ValueError('RFC es obligatorio')
        v = v.upper()
        if len(v) not in [12, 13]:
            raise ValueError('RFC debe tener 12 o 13 caracteres')
        return v
    
    @field_validator('nss')
    @classmethod
    def validar_nss(cls, v):
        """Valida que NSS tenga 11 dígitos"""
        if not v:
            raise ValueError('NSS es obligatorio')
        if len(v) != 11 or not v.isdigit():
            raise ValueError('NSS debe tener exactamente 11 dígitos')
        return v
    
    @field_validator('cuenta_banco_clabe')
    @classmethod
    def validar_clabe(cls, v):
        """Valida formato de CLABE"""
        if v and (len(v) != 18 or not v.isdigit()):
            raise ValueError('CLABE debe tener exactamente 18 dígitos')
        return v
    
    # ========================
    # MÉTODOS ÚTILES
    # ========================
    def obtener_edad(self) -> int:
        """Calcula la edad actual del empleado"""
        hoy = date.today()
        return hoy.year - self.fecha_nacimiento.year - (
            (hoy.month, hoy.day) < (self.fecha_nacimiento.month, self.fecha_nacimiento.day)
        )
    
    def obtener_antiguedad_anos(self) -> float:
        """Calcula años de antigüedad"""
        hoy = date.today()
        delta = hoy - self.fecha_ingreso
        return delta.days / 365.25
    
    def obtener_antiguedad_formato(self) -> str:
        """Retorna antigüedad en formato legible"""
        anos = self.obtener_antiguedad_anos()
        anos_completos = int(anos)
        meses = int((anos - anos_completos) * 12)
        
        if anos_completos == 0:
            return f"{meses} meses"
        elif anos_completos == 1:
            return f"1 año, {meses} meses"
        else:
            return f"{anos_completos} años, {meses} meses"
    
    def esta_activo(self) -> bool:
        """Verifica si el empleado está activo"""
        return self.estatus == "ACTIVO"
    
    def puede_trabajar(self) -> bool:
        """Verifica si puede trabajar (no está de baja o incapacitado)"""
        return self.estatus in ["ACTIVO", "VACACIONES"]
    
    def requiere_renovacion_contrato(self, dias_anticipacion: int = 30) -> bool:
        """Verifica si el contrato está por vencer"""
        # Implementar lógica según tipo de contrato
        return False